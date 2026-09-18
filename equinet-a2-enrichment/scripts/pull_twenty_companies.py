#!/usr/bin/env python3
"""Pull and optionally claim a bounded, filtered batch of A2-eligible Twenty Companies."""
from __future__ import annotations
import argparse,json,re,urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any
from a2_twenty_fullenrich_common import IntegrationError,http_json,make_envelope,normalise_twenty_company,response_records,sha256_json,twenty_env,utc_now,write_json_atomic
ORDER_FIELDS={'createdAt','updatedAt','name'};ORDER_DIRECTIONS={'AscNullsFirst','AscNullsLast','DescNullsFirst','DescNullsLast'}
def quote(value:str)->str:return json.dumps(value,ensure_ascii=False,separators=(',',':'))
def one(field:str,operator:str,value:str,*,quoted:bool=False)->str:return f"{field}[{operator}]:{quote(value) if quoted else value}"
def any_of(predicates:list[str])->str:
 if not predicates:return ''
 return predicates[0] if len(predicates)==1 else 'or('+','.join(predicates)+')'
def parse_order(value:str)->list[tuple[str,str]]:
 out=[]
 for item in value.split(','):
  match=re.fullmatch(r'([A-Za-z][A-Za-z0-9]*)(?:\[([A-Za-z]+)\])?',item.strip())
  if not match or match.group(1) not in ORDER_FIELDS:raise ValueError(f'unsupported order_by item: {item}')
  direction=match.group(2) or 'AscNullsLast'
  if direction not in ORDER_DIRECTIONS:raise ValueError(f'unsupported order direction: {direction}')
  out.append((match.group(1),direction))
 return out
def build_filter(args)->str|None:
 parts=[]
 if not args.allow_any_status:
  status=[one('a2EnrichmentStatus','eq',x) for x in args.statuses]
  if args.include_null:status.append(one('a2EnrichmentStatus','is','NULL'))
  parts.append(any_of(status))
 if args.company_id:parts.append(any_of([one('id','eq',x) for x in args.company_id]))
 if args.company_name:parts.append(any_of([one('name','eq',x,quoted=True) for x in args.company_name]))
 if args.segment:parts.append(any_of([one('segment','eq',x) for x in args.segment]))
 if args.city:parts.append(any_of([one('city','eq',x) for x in args.city]))
 if args.state:parts.append(any_of([one('state','eq',x) for x in args.state]))
 if args.country:parts.append(any_of([one('country','eq',x) for x in args.country]))
 for field,low,high in [('createdAt',args.created_after,args.created_before),('updatedAt',args.updated_after,args.updated_before)]:
  if low:parts.append(one(field,'gte',low,quoted=True))
  if high:parts.append(one(field,'lte',high,quoted=True))
 return ','.join(x for x in parts if x) or None
def parse_dt(value:Any):
 if not isinstance(value,str):return None
 try:return datetime.fromisoformat(value.replace('Z','+00:00'))
 except ValueError:return None
def values(record:dict,key:str)->str|None:
 value=record.get(key)
 if value is None and key in {'city','state','country'}:
  address=record.get('address') if isinstance(record.get('address'),dict) else {};mapping={'city':'addressCity','state':'addressState','country':'addressCountry'};value=address.get(mapping[key])
 return str(value).casefold() if value is not None else None
def local_match(record:dict,args)->bool:
 if not args.allow_any_status and not (record.get('a2EnrichmentStatus') in set(args.statuses) or (args.include_null and record.get('a2EnrichmentStatus') is None)):return False
 checks=[('id',args.company_id),('name',args.company_name),('segment',args.segment),('city',args.city),('state',args.state),('country',args.country)]
 for key,wanted in checks:
  if wanted and values(record,key) not in {str(x).casefold() for x in wanted}:return False
 for key,low,high in [('createdAt',args.created_after,args.created_before),('updatedAt',args.updated_after,args.updated_before)]:
  actual=parse_dt(record.get(key));lo=parse_dt(low);hi=parse_dt(high)
  if low and (actual is None or lo is None or actual<lo):return False
  if high and (actual is None or hi is None or actual>hi):return False
 return True
def sort_local(records:list[dict],specs:list[tuple[str,str]])->list[dict]:
 result=list(records)
 for field,direction in reversed(specs):
  desc=direction.startswith('Desc');null_first=direction.endswith('NullsFirst')
  result.sort(key=lambda r:'' if r.get(field) is None else str(r.get(field)).casefold(),reverse=desc)
  result.sort(key=lambda r:0 if (r.get(field) is None)==null_first else 1)
 return result
def main()->int:
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run-id',required=True);ap.add_argument('--batch-size',type=int,default=10);ap.add_argument('--order-by',default='createdAt[DescNullsLast]');ap.add_argument('--status',action='append',dest='statuses');ap.add_argument('--include-null',action='store_true');ap.add_argument('--allow-any-status',action='store_true');ap.add_argument('--company-id',action='append');ap.add_argument('--company-name',action='append');ap.add_argument('--segment',action='append',choices=['FARRIER','HORSE_OWNER']);ap.add_argument('--city',action='append');ap.add_argument('--state',action='append');ap.add_argument('--country',action='append');ap.add_argument('--created-after');ap.add_argument('--created-before');ap.add_argument('--updated-after');ap.add_argument('--updated-before');ap.add_argument('--claim',action='store_true');ap.add_argument('--enrichment-version',default='0.1.0');ap.add_argument('--fixture',type=Path);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();args.statuses=args.statuses or ['NOT_ENRICHED']
 if not 1<=args.batch_size<=200:raise SystemExit('batch-size must be 1..200')
 if args.allow_any_status and (args.include_null or args.statuses!=['NOT_ENRICHED']):raise SystemExit('--allow-any-status cannot be combined with --status or --include-null')
 if args.company_id and len(set(args.company_id))>args.batch_size:raise SystemExit('batch-size must cover every requested company-id')
 if args.company_name and len(set(args.company_name))>args.batch_size:raise SystemExit('batch-size must cover every requested company-name')
 try:
  order=parse_order(args.order_by);filter_value=build_filter(args);fetch_limit=200 if args.company_name and len(args.company_name)==1 and not args.company_id else args.batch_size;params={'limit':str(fetch_limit),'depth':'1','order_by':args.order_by}
  if filter_value:params['filter']=filter_value
  if args.fixture:
   raw=json.loads(args.fixture.read_text(encoding='utf-8'));records=raw.get('companies',raw if isinstance(raw,list) else []);records=sort_local(records,order);receipt={'fixture':True}
  else:
   base,key=twenty_env();payload,receipt=http_json('GET',base+'/rest/companies?'+urllib.parse.urlencode(params),token=key,retries=1);records=response_records(payload,'companies')
  matched=[record for record in records if local_match(record,args)]
  if args.company_name and len(args.company_name)==1 and not args.company_id and len(matched)>1:raise ValueError('company name is ambiguous; use --company-id')
  eligible=matched[:args.batch_size];claims=[];normalised=[]
  for record in eligible:
   cid=record.get('id')
   if args.claim and not args.fixture:
    body={'a2EnrichmentStatus':'PROCESSING','a2EnrichmentRunId':args.run_id,'a2ProcessingStartedAt':utc_now(),'a2LastAttemptedAt':utc_now(),'a2EnrichmentVersion':args.enrichment_version,'a2EnrichmentErrorCode':None}
    patched,write_receipt=http_json('PATCH',f'{base}/rest/companies/{cid}?depth=1',token=key,body=body,retries=0);verify,read_receipt=http_json('GET',f'{base}/rest/companies/{cid}?depth=1',token=key,retries=1);data=verify.get('data',verify);company=data.get('company',data) if isinstance(data,dict) else {};ok=company.get('a2EnrichmentStatus')=='PROCESSING' and company.get('a2EnrichmentRunId')==args.run_id;claims.append({'company_id':cid,'claimed':ok,'write_receipt':write_receipt,'read_receipt':read_receipt})
    if not ok:continue
    record=company
   elif args.claim and args.fixture:record={**record,'a2EnrichmentStatus':'PROCESSING','a2EnrichmentRunId':args.run_id,'a2ProcessingStartedAt':utc_now()};claims.append({'company_id':cid,'claimed':True,'fixture':True})
   normalised.append(normalise_twenty_company(record))
  applied={'statuses':None if args.allow_any_status else args.statuses,'include_null':args.include_null,'allow_any_status':args.allow_any_status,'company_ids':args.company_id or [],'company_names':args.company_name or [],'segments':args.segment or [],'cities':args.city or [],'states':args.state or [],'countries':args.country or [],'created_after':args.created_after,'created_before':args.created_before,'updated_after':args.updated_after,'updated_before':args.updated_before,'order_by':args.order_by}
  result=make_envelope('a2-twenty-company-batch',args.run_id,{'input_snapshot_sha256':sha256_json(eligible),'requested_batch_size':args.batch_size,'company_count':len(normalised),'companies':normalised,'claims':claims,'applied_filters':applied,'twenty_query':{'path':'/rest/companies','params':params,'receipt':receipt},'external_writes':sum(1 for x in claims if not x.get('fixture'))})
  write_json_atomic(args.output,result);print(json.dumps({'status':'valid','company_count':len(normalised),'claimed':sum(x.get('claimed') is True for x in claims),'filters':applied,'output':str(args.output),'external_writes':result['external_writes']},indent=2));return 0
 except (IntegrationError,OSError,ValueError,json.JSONDecodeError) as exc:
  result={'status':'error','error':str(exc),'code':getattr(exc,'code',None),'external_writes':0};write_json_atomic(args.output,result);print(json.dumps(result,indent=2));return 1
if __name__=='__main__':raise SystemExit(main())
