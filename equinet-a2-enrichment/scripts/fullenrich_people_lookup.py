#!/usr/bin/env python3
"""Run bounded FullEnrich People Lookup requests and minimise results."""
from __future__ import annotations
import argparse,json
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from a2_twenty_fullenrich_common import domain_name,fullenrich_env,fullenrich_preflight,http_json,load_json,make_envelope,normalise_fullenrich_person,sha256_json,write_json_atomic
from a2_fullenrich_budget import estimate_credits,reserve_credits,settle_credits

def build_payload(item):
 if item.get('person_professional_network_url'):return {'person_professional_network_url':item['person_professional_network_url']}
 if item.get('person_professional_network_id'):return {'person_professional_network_id':item['person_professional_network_id']}
 payload={}
 if item.get('person_name'):payload['person_name']=item['person_name']
 if item.get('company_domain'):payload['company_domain']=domain_name(item['company_domain'])
 elif item.get('company_professional_network_url'):payload['company_professional_network_url']=item['company_professional_network_url']
 elif item.get('company_professional_network_id'):payload['company_professional_network_id']=item['company_professional_network_id']
 if 'person_name' not in payload or len(payload)<2:raise ValueError('Lookup requires person professional-network identifier or person_name plus Company domain/network identifier')
 return payload

def execute(item,fixture,base,key):
 rid=item.get('request_id') or item.get('twenty_person_id');payload=build_payload(item)
 if fixture is not None:raw=fixture.get(rid,{}) ; receipt={'fixture':True,'http_status':200}
 else:raw,receipt=http_json('POST',base+'/people/lookup',token=key,body=payload,retries=1)
 people=raw.get('people') if isinstance(raw,dict) else None
 if not isinstance(people,list) or len(people)>1:raise ValueError('FullEnrich Lookup response must contain a people array of at most one')
 return {'request_id':rid,'company_id':item.get('company_id'),'twenty_person_id':item.get('twenty_person_id'),'terminal_status':'succeeded' if people else 'not_found','request_payload':payload,'person':normalise_fullenrich_person(people[0]) if people else None,'metadata':raw.get('metadata') or {},'provider_payload_sha256':sha256_json(raw),'receipt':receipt}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('request',type=Path);ap.add_argument('--fixture',type=Path);ap.add_argument('--workers',type=int,default=4);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();req=load_json(a.request);items=req.get('requests') or [];run_id=req.get('run_id','unknown')
 if len(items)>25:raise SystemExit('maximum 25 requests per script run to preserve retry headroom under the documented 60 calls/minute limit')
 fixture=load_json(a.fixture) if a.fixture else None
 if not items:
  result=make_envelope('a2-fullenrich-lookup-results',run_id,{'result_count':0,'results':[],'budget':{'no_action':True},'external_calls':0});write_json_atomic(a.output,result);print(json.dumps({'status':'valid','results':0,'output':str(a.output)},indent=2));return 0
 reservation=None;estimated=estimate_credits('people_lookup',items)
 try:
  base,key=(None,None) if fixture is not None else fullenrich_env();preflight={'fixture':True} if fixture is not None else fullenrich_preflight(base,key,estimated)
  if fixture is None:reservation=reserve_credits(run_id=run_id,action='people_lookup',maximum_credits=estimated,request=req)
  if reservation and reservation.get('reused'):
   raise IntegrationError('An existing credit reservation/result exists for this exact run and request; reuse the prior result artifact instead of repeating a paid call',code='idempotent_reuse_required')
  results=[]
  with ThreadPoolExecutor(max_workers=max(1,min(a.workers,10))) as pool:
   futures={pool.submit(execute,x,fixture,base,key):x for x in items}
   for f in as_completed(futures):
    item=futures[f]
    try:results.append(f.result())
    except Exception as e:results.append({'request_id':item.get('request_id'),'company_id':item.get('company_id'),'twenty_person_id':item.get('twenty_person_id'),'terminal_status':'insufficient_match' if isinstance(e,ValueError) else 'failed','error':str(e)})
  failed=any(x['terminal_status']=='failed' for x in results);actual=sum(float((x.get('metadata') or {}).get('credits') or 0) for x in results);settlement=None
  if reservation:settlement=settle_credits(reservation['reservation_id'],estimated if failed else actual,status='settled_conservative' if failed else 'settled')
  result=make_envelope('a2-fullenrich-lookup-results',run_id,{'result_count':len(results),'results':sorted(results,key=lambda x:str(x.get('request_id'))),'preflight':preflight,'budget':{'estimated_max_credits':estimated,'reservation':reservation,'settlement':settlement},'external_calls':0 if fixture is not None else len(items)+2})
  write_json_atomic(a.output,result);print(json.dumps({'status':'valid','results':len(results),'failed':sum(x['terminal_status']=='failed' for x in results),'output':str(a.output)},indent=2));return 0 if not failed else 1
 except Exception as e:
  if reservation:
   try:settle_credits(reservation['reservation_id'],estimated,status='settled_conservative')
   except Exception:pass
  result={'status':'error','error':str(e),'code':getattr(e,'code',None),'budget':{'estimated_max_credits':estimated,'reservation':reservation}};write_json_atomic(a.output,result);print(json.dumps(result,indent=2));return 1
if __name__=='__main__':raise SystemExit(main())
