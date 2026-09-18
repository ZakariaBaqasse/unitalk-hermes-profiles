#!/usr/bin/env python3
"""Atomic FullEnrich credit reservations and settlements for A2."""
from __future__ import annotations
import fcntl,json,os,tempfile
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
from pathlib import Path
from typing import Any
from a2_twenty_fullenrich_common import IntegrationError,load_json,sha256_json,utc_now
ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'foundations/contracts/governance/a2-provider-and-cost-policy-0.4.0.json'
DEFAULT_LEDGER=ROOT/'evaluations/step10/consumption/fullenrich-credit-ledger.json'

def dec(value:Any)->Decimal:
 try:return Decimal(str(value))
 except (InvalidOperation,ValueError,TypeError):raise IntegrationError(f'invalid credit value: {value}',code='budget_value_invalid')
def number(value:Decimal)->int|float:
 return int(value) if value==value.to_integral() else float(value)
def ledger_path()->Path:return Path(os.getenv('A2_FULLENRICH_CREDIT_LEDGER',str(DEFAULT_LEDGER)))
def _write(path:Path,value:dict)->None:
 path.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as h:json.dump(value,h,indent=2);h.write('\n');tmp=Path(h.name)
 tmp.replace(path)
def _caps()->dict[str,Decimal]:
 c=load_json(POLICY).get('controls',{});raw={'run':c.get('per_run_cap_credits'),'day':c.get('daily_cap_credits'),'pilot':c.get('pilot_cap_credits')}
 if any(v is None for v in raw.values()):raise IntegrationError('FullEnrich credit caps are not configured',code='budget_block')
 return {k:dec(v) for k,v in raw.items()}
def _usage(entry:dict)->Decimal:
 if entry.get('status')=='released':return Decimal('0')
 return dec(entry.get('actual_credits')) if entry.get('actual_credits') is not None else dec(entry.get('reserved_credits',0))
def _locked_update(fn):
 path=ledger_path();path.parent.mkdir(parents=True,exist_ok=True);lock=path.with_suffix(path.suffix+'.lock')
 with lock.open('a+',encoding='utf-8') as h:
  fcntl.flock(h.fileno(),fcntl.LOCK_EX)
  ledger=load_json(path) if path.is_file() else {'schema_id':'a2-fullenrich-credit-ledger','version':'0.1.0','pilot_id':'equinet-a2-step10-controlled-pilot','created_at':utc_now(),'entries':[]}
  result=fn(ledger);ledger['updated_at']=utc_now();_write(path,ledger);return result

def reserve_credits(*,run_id:str,action:str,maximum_credits:float|int,request:Any)->dict:
 maximum=dec(maximum_credits)
 if maximum<0:raise IntegrationError('maximum credits cannot be negative',code='budget_value_invalid')
 caps=_caps();request_hash=sha256_json(request);today=datetime.now(timezone.utc).date().isoformat()
 def update(ledger):
  for e in ledger['entries']:
   if e.get('run_id')==run_id and e.get('action')==action and e.get('request_sha256')==request_hash and e.get('status')!='released':return {**e,'reused':True}
  run_used=sum((_usage(e) for e in ledger['entries'] if e.get('run_id')==run_id),Decimal('0'))
  day_used=sum((_usage(e) for e in ledger['entries'] if str(e.get('created_at',''))[:10]==today),Decimal('0'))
  pilot_used=sum((_usage(e) for e in ledger['entries']),Decimal('0'))
  projected={'run':run_used+maximum,'day':day_used+maximum,'pilot':pilot_used+maximum};violations=[k for k in projected if projected[k]>caps[k]]
  if violations:raise IntegrationError('FullEnrich credit cap would be exceeded: '+','.join(violations),code='budget_block',payload={'caps':{k:number(v) for k,v in caps.items()},'projected':{k:number(v) for k,v in projected.items()}})
  rid='FE-RES-'+sha256_json({'run_id':run_id,'action':action,'request_sha256':request_hash})[:16].upper();entry={'reservation_id':rid,'run_id':run_id,'action':action,'request_sha256':request_hash,'reserved_credits':number(maximum),'actual_credits':None,'status':'reserved','created_at':utc_now(),'utc_day':today};ledger['entries'].append(entry)
  return {**entry,'reused':False,'usage_before':{'run':number(run_used),'day':number(day_used),'pilot':number(pilot_used)},'caps':{k:number(v) for k,v in caps.items()}}
 return _locked_update(update)
def settle_credits(reservation_id:str,actual_credits:float|int,*,status:str='settled')->dict:
 actual=dec(actual_credits)
 if actual<0:raise IntegrationError('actual credits cannot be negative',code='budget_value_invalid')
 def update(ledger):
  entry=next((e for e in ledger['entries'] if e.get('reservation_id')==reservation_id),None)
  if not entry:raise IntegrationError('credit reservation not found',code='budget_reservation_missing')
  if entry.get('status') in {'settled','settled_conservative'}:
   if dec(entry.get('actual_credits',0))!=actual:raise IntegrationError('credit reservation already settled with a different amount',code='budget_settlement_conflict')
   return {**entry,'reused':True}
  entry.update(actual_credits=number(actual),status=status,settled_at=utc_now(),over_reservation=actual>dec(entry.get('reserved_credits',0)))
  return {**entry,'reused':False}
 return _locked_update(update)
def usage_summary()->dict:
 caps=_caps();today=datetime.now(timezone.utc).date().isoformat()
 def read(ledger):
  entries=ledger['entries'];run={}
  for e in entries:run[e['run_id']]=run.get(e['run_id'],Decimal('0'))+_usage(e)
  return {'caps':{k:number(v) for k,v in caps.items()},'pilot_used':number(sum((_usage(e) for e in entries),Decimal('0'))),'today_used':number(sum((_usage(e) for e in entries if str(e.get('created_at',''))[:10]==today),Decimal('0'))),'run_used':{k:number(v) for k,v in run.items()},'entry_count':len(entries)}
 return _locked_update(read)


def estimate_credits(action:str,items:list[dict[str,Any]])->float|int:
 policy=load_json(POLICY);rates=policy.get('documented_reference_rates',{});profile=dec(rates.get('people_search_or_lookup_per_returned_person_credits'));email=dec(rates.get('work_email_if_found_credits'));mobile=dec(rates.get('mobile_if_found_credits'))
 if action=='people_lookup':value=profile*len(items)
 elif action=='people_search':value=profile*sum(dec(item.get('limit',2)) for item in items)
 elif action=='contact_enrichment':value=(email+mobile)*len(items)
 else:raise IntegrationError(f'unknown FullEnrich action: {action}',code='budget_action_invalid')
 return number(value)
