#!/usr/bin/env python3
"""Start and poll FullEnrich Contact Enrichment for selected People."""
from __future__ import annotations
import argparse,json,time,urllib.parse
from pathlib import Path
from a2_twenty_fullenrich_common import domain_name,IntegrationError,fullenrich_env,fullenrich_preflight,http_json,load_json,make_envelope,normalise_fullenrich_person,select_mobile,select_work_email,sha256_json,split_name,write_json_atomic
from a2_fullenrich_budget import estimate_credits,reserve_credits,settle_credits
TERMINAL={'CANCELED','CREDITS_INSUFFICIENT','FINISHED'};INDETERMINATE={'RATE_LIMIT','UNKNOWN'}
def build_contact(x):
 first,last=x.get('first_name'),x.get('last_name')
 if not first or not last:first,last=split_name(x.get('full_name'))
 item={'enrich_fields':['contact.work_emails','contact.phones'],'custom':{'request_id':str(x.get('request_id')),'company_id':str(x.get('company_id')),'provider_person_id':str(x.get('provider_person_id') or '')}}
 if x.get('professional_network_url'):item['linkedin_url']=x['professional_network_url']
 else:
  if not first or not last:raise ValueError('Contact Enrichment requires LinkedIn URL or splittable first and last name')
  item['first_name']=first;item['last_name']=last
  if x.get('company_domain'):item['domain']=domain_name(x['company_domain'])
  elif x.get('company_name'):item['company_name']=x['company_name']
  else:raise ValueError('name-based Contact Enrichment requires Company domain or name')
 return item
def minimise(raw):
 out=[]
 for row in raw.get('data') or []:
  if not isinstance(row,dict):continue
  contact=row.get('contact_info') if isinstance(row.get('contact_info'),dict) else {};profile=row.get('profile') if isinstance(row.get('profile'),dict) else {};inp=row.get('input') if isinstance(row.get('input'),dict) else {};custom=row.get('custom') if isinstance(row.get('custom'),dict) else {}
  personal=contact.get('most_probable_personal_email') or ((contact.get('personal_emails') or [None])[0])
  out.append({'request_id':custom.get('request_id'),'company_id':custom.get('company_id'),'provider_person_id':custom.get('provider_person_id') or profile.get('id'),'input':{'full_name':inp.get('full_name') or ' '.join(filter(None,[inp.get('first_name'),inp.get('last_name')])),'company_name':inp.get('company_name'),'company_domain':inp.get('company_domain'),'professional_network_url':inp.get('professional_network_url')},'profile':normalise_fullenrich_person(profile) if profile else None,'work_email':select_work_email(contact),'mobile_phone':select_mobile(contact),'personal_email_candidate':personal if isinstance(personal,dict) else None,'personal_email_requested':False})
 return out
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('request',type=Path);ap.add_argument('--fixture',type=Path);ap.add_argument('--poll-seconds',type=int,default=300);ap.add_argument('--max-polls',type=int,default=10);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();req=load_json(a.request);people=req.get('selected_people') or [];run_id=req.get('run_id','unknown')
 if not people or len(people)>100:raise SystemExit('selected_people must contain 1..100 items')
 reservation=None;estimated=estimate_credits('contact_enrichment',people)
 try:
  payload={'name':f"A2 {run_id}",'data':[build_contact(x) for x in people]}
  if any('contact.personal_emails' in (x.get('enrich_fields') or []) for x in payload['data']):raise ValueError('personal email request is prohibited')
  polls=[]
  if a.fixture:raw=load_json(a.fixture);enrichment_id=raw.get('id','fixture');external_calls=0;preflight={'fixture':True}
  else:
   base,key=fullenrich_env();preflight=fullenrich_preflight(base,key,estimated);reservation=reserve_credits(run_id=run_id,action='contact_enrichment',maximum_credits=estimated,request=req)
   if reservation.get('reused'):raise IntegrationError('An existing credit reservation/result exists for this exact run and request; reuse the prior result artifact instead of repeating a paid call',code='idempotent_reuse_required')
   start,receipt=http_json('POST',base+'/contact/enrich/bulk?'+urllib.parse.urlencode({'silentFail':'true'}),token=key,body=payload,retries=1);enrichment_id=start.get('enrichment_id')
   if not enrichment_id:raise ValueError('FullEnrich start response missing enrichment_id')
   raw=None;external_calls=1
   for poll in range(1,a.max_polls+1):
    try:
     candidate,pr=http_json('GET',base+f'/contact/enrich/bulk/{enrichment_id}',token=key,retries=1);external_calls+=1;polls.append({'poll':poll,'http_status':pr['http_status'],'status':candidate.get('status')})
     if candidate.get('status') in TERMINAL|INDETERMINATE:raw=candidate;break
    except IntegrationError as e:
     external_calls+=1
     if e.status==400 and e.code=='error.enrichment.in_progress':polls.append({'poll':poll,'http_status':400,'status':'IN_PROGRESS'})
     elif e.status==402 and isinstance(e.payload,dict):raw=e.payload;break
     else:raise
    if poll<a.max_polls:time.sleep(max(1,a.poll_seconds))
   if raw is None:raise IntegrationError('Contact Enrichment polling timed out',code='timed_out')
  status=raw.get('status');results=minimise(raw) if status=='FINISHED' else []
  requested={str(x.get('request_id')):x for x in people}
  for result_row in results:
   source=requested.get(str(result_row.get('request_id'))) or {}
   result_row.update({'twenty_person_id':source.get('twenty_person_id'),'website_person_id':source.get('website_person_id'),'source_kind':source.get('source_kind'),'selection_stage':source.get('selection_stage'),'selected_target_priority':source.get('selected_target_priority'),'identity_status':source.get('identity_status'),'company_match_status':source.get('company_match_status'),'role_status':source.get('role_status'),'source_full_name':source.get('source_full_name'),'exact_current_role':source.get('exact_current_role'),'website_work_email':source.get('website_work_email'),'website_phone':source.get('website_phone'),'website_evidence_refs':source.get('evidence_refs') or []})
  actual=(raw.get('cost') or {}).get('credits');actual=float(actual) if isinstance(actual,(int,float)) else estimated;settlement=None
  if reservation:settlement=settle_credits(reservation['reservation_id'],actual,status='settled' if isinstance((raw.get('cost') or {}).get('credits'),(int,float)) else 'settled_conservative')
  result=make_envelope('a2-fullenrich-contact-results',run_id,{'enrichment_id':enrichment_id,'terminal_status':status,'results':results,'cost':raw.get('cost') or {},'polls':polls,'request_fields':['contact.work_emails','contact.phones'],'personal_email_requested':False,'preflight':preflight,'budget':{'estimated_max_credits':estimated,'reservation':reservation,'settlement':settlement},'provider_payload_sha256':sha256_json(raw),'external_calls':external_calls+(0 if a.fixture else 2)})
  write_json_atomic(a.output,result);print(json.dumps({'status':'valid','terminal_status':status,'results':len(results),'output':str(a.output)},indent=2));return 0 if status=='FINISHED' else 1
 except Exception as e:
  if reservation:
   try:settle_credits(reservation['reservation_id'],estimated,status='settled_conservative')
   except Exception:pass
  result={'status':'error','error':str(e),'code':getattr(e,'code',None),'personal_email_requested':False,'budget':{'estimated_max_credits':estimated,'reservation':reservation}};write_json_atomic(a.output,result);print(json.dumps(result,indent=2));return 1
if __name__=='__main__':raise SystemExit(main())
