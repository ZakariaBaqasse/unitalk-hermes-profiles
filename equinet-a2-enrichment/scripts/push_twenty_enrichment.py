#!/usr/bin/env python3
"""Validate, apply and reconcile an explicit Twenty enrichment write plan."""
from __future__ import annotations
import argparse,json
from datetime import datetime
from pathlib import Path
from a2_twenty_fullenrich_common import IntegrationError,http_json,load_json,sha256_json,twenty_env,utc_now,write_json_atomic
ALLOWED={'create_person','update_person','associate_person_company','update_company_fields','update_company_status'}
A1_PROTECTED={'discoveryStatus','discoverySourceNotes','discoveryFingerprint','qualificationStatus','icpScoreStatus','icpScore','icpBand','icpOutcome','evidenceConfidenceScore','evidenceConfidenceLevel'}
def validate_plan(plan):
 errors=[];ops=plan.get('operations')
 if not isinstance(ops,list):return ['operations must be an array']
 ids=[]
 for i,op in enumerate(ops):
  if not isinstance(op,dict):errors.append(f'operations[{i}] must be an object');continue
  oid=op.get('operation_id');ids.append(oid)
  if not oid:errors.append(f'operations[{i}] requires operation_id')
  if op.get('operation_type') not in ALLOWED:errors.append(f'operations[{i}] unsupported operation_type')
  fields=op.get('fields') or {}
  bad=A1_PROTECTED.intersection(fields)
  if bad:errors.append(f'operations[{i}] attempts protected A1 fields: {sorted(bad)}')
  if 'personalEmailCandidate' in fields:errors.append(f'operations[{i}] cannot auto-write personal email')
 if len(ids)!=len(set(ids)):errors.append('operation IDs must be unique')
 merge_positions=[i for i,o in enumerate(ops) if isinstance(o,dict) and o.get('operation_type')=='update_company_fields']
 if len(merge_positions)>1:errors.append('at most one Company business-field merge operation is allowed')
 if merge_positions:
  op=ops[merge_positions[0]]
  if merge_positions[0]!=0:errors.append('Company business-field merge must be the first operation')
  if not op.get('baseline_sha256') or not isinstance(op.get('baseline_fields'),dict):errors.append('Company business-field merge requires baseline hash and fields')
  allowed_company={'email','phone','linkedinLink','facebook','instagram','youtube','tiktok','xTwitter'}
  bad=set((op.get('fields') or {}))-allowed_company
  if bad:errors.append(f'Company business-field merge has unsupported fields: {sorted(bad)}')
 status_positions=[i for i,o in enumerate(ops) if isinstance(o,dict) and o.get('operation_type')=='update_company_status']
 if status_positions and status_positions[-1]!=len(ops)-1:errors.append('final Company status operation must be last')
 return errors
def unwrap(payload,singular):
 data=payload.get('data',payload) if isinstance(payload,dict) else {}
 return data.get(singular,data) if isinstance(data,dict) else {}
def equivalent(expected,observed):
 if expected==observed:return True
 if isinstance(expected,str) and isinstance(observed,str):
  try:return datetime.fromisoformat(expected.replace('Z','+00:00'))==datetime.fromisoformat(observed.replace('Z','+00:00'))
  except ValueError:return False
 return False
def apply(plan,do_apply):
 errors=validate_plan(plan)
 if errors:return {'status':'invalid','errors':errors,'external_writes':0}
 if not do_apply:return {'status':'dry_run','write_plan_sha256':sha256_json(plan),'operation_count':len(plan['operations']),'operations':plan['operations'],'external_writes':0}
 base,key=twenty_env();temp={};receipts=[]
 for op in plan['operations']:
  typ=op['operation_type'];fields=dict(op.get('fields') or {})
  if typ=='create_person':
   payload,receipt=http_json('POST',base+'/rest/people?depth=1',token=key,body=fields,retries=0);record=unwrap(payload,'person');temp[op.get('temporary_person_key')]=record.get('id');target=record.get('id')
  elif typ=='update_person':
   target=op['twenty_person_id'];payload,receipt=http_json('PATCH',f'{base}/rest/people/{target}?depth=1',token=key,body=fields,retries=0)
  elif typ=='associate_person_company':
   target=op.get('twenty_person_id') or temp.get(op.get('temporary_person_key'))
   if not target:raise IntegrationError('association has no resolved Person ID',code='unresolved_person_reference')
   payload,receipt=http_json('PATCH',f'{base}/rest/people/{target}?depth=1',token=key,body={'companyId':op['twenty_company_id']},retries=0)
  elif typ=='update_company_fields':
   target=op['twenty_company_id'];current_payload,baseline_receipt=http_json('GET',f'{base}/rest/companies/{target}?depth=0',token=key,retries=1);current=unwrap(current_payload,'company');baseline=op.get('baseline_fields') or {};observed={k:current.get(k) for k in baseline}
   if sha256_json(observed)!=op.get('baseline_sha256'):raise IntegrationError('Company baseline changed before composite merge',code='company_baseline_conflict',payload={'expected_sha256':op.get('baseline_sha256'),'observed_sha256':sha256_json(observed)})
   payload,receipt=http_json('PATCH',f'{base}/rest/companies/{target}?depth=1',token=key,body=fields,retries=0);receipt={**receipt,'baseline_read_receipt':baseline_receipt}
  else:
   target=op['twenty_company_id'];payload,receipt=http_json('PATCH',f'{base}/rest/companies/{target}?depth=1',token=key,body=fields,retries=0)
  receipts.append({'operation_id':op['operation_id'],'operation_type':typ,'target_id':target,'receipt':receipt})
 company_id=plan['company_id'];read,read_receipt=http_json('GET',f'{base}/rest/companies/{company_id}?depth=1',token=key,retries=1);company=unwrap(read,'company')
 expected=plan.get('expected_read_back') or {};mismatches=[]
 for field,value in (expected.get('company_fields') or {}).items():
  if not equivalent(value,company.get(field)):mismatches.append({'entity':'company','field':field,'expected':value,'observed':company.get(field)})
 linked={p.get('id'):p for p in (company.get('people') or []) if isinstance(p,dict)}
 for person in expected.get('people') or []:
  pid=person.get('twenty_person_id') or temp.get(person.get('temporary_person_key'));actual=linked.get(pid)
  if not actual:mismatches.append({'entity':'person','person_id':pid,'field':'association','expected':'linked','observed':'missing'});continue
  for field,value in (person.get('fields') or {}).items():
   if not equivalent(value,actual.get(field)):mismatches.append({'entity':'person','person_id':pid,'field':field,'expected':value,'observed':actual.get(field)})
 return {'status':'reconciled' if not mismatches else 'reconciliation_failed','write_plan_sha256':sha256_json(plan),'receipts':receipts,'temporary_person_ids':temp,'read_receipt':read_receipt,'mismatches':mismatches,'external_writes':len(receipts)}
def main()->int:
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('plan',type=Path);ap.add_argument('--apply',action='store_true');ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 try:result=apply(load_json(args.plan),args.apply)
 except (IntegrationError,OSError,ValueError,json.JSONDecodeError) as exc:result={'status':'error','error':str(exc),'code':getattr(exc,'code',None),'external_writes':0}
 result['completed_at']=utc_now();write_json_atomic(args.output,result);print(json.dumps({'status':result['status'],'external_writes':result.get('external_writes',0),'mismatch_count':len(result.get('mismatches',[])),'output':str(args.output)},indent=2));return 0 if result['status'] in {'dry_run','reconciled'} else 1
if __name__=='__main__':raise SystemExit(main())
