#!/usr/bin/env python3
"""Prepare and validate governed A2 handoffs without delivering them."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_wave3_contracts import ROOT,canonical_hash,load,load_active
from validate_a2_enrichment_record import validate
CAT_REL='foundations/contracts/business/a2-business-field-catalogue-0.1.1-draft.1.json'
DESTINATIONS={'a1_requalification','hubspot_proposed_patch','a3_outreach','a14_field_rep'}
def build(record:dict,destination:str,previous:dict|None,catalogue:dict,review_receipt:dict|None=None)->dict:
 errors=[];v=validate(record,previous=previous)
 if not v['valid']:errors.extend(v['errors'])
 if destination not in DESTINATIONS:errors.append('unsupported destination')
 m=record.get('record_metadata',{});digest=canonical_hash(record);payload={};status='blocked'
 if destination=='a1_requalification':
  signals=record.get('requalification',{}).get('signals',[])
  if not signals:errors.append('no requalification signals')
  if any('score' in json.dumps(s).lower() and any(k in s for k in ['score','points','band']) for s in signals):errors.append('A2 signal cannot contain replacement score')
  payload={'signals':signals,'source_profile':'equinet-a2-enrichment','target_profile':'equinet-a1-icp-discovery','delivery_authorized':False};status='prepared_not_delivered' if signals and not errors else 'blocked'
 elif destination=='hubspot_proposed_patch':
  if not review_receipt or review_receipt.get('review_status')!='approved':errors.append('approved Twenty review receipt required')
  patches=[]
  for x in record.get('field_assessments',[]):
   p=x.get('proposed_resolution') or {}
   if x.get('field_review',{}).get('decision')=='approved' and p.get('action') in {'add','update'}:patches.append({'field_assessment_id':x['field_assessment_id'],'field_key':x['field_key'],'value':p.get('normalised_value'),'evidence_ids':p.get('evidence_ids',[])})
  if not patches:errors.append('no approved field proposals')
  errors.append('HubSpot proposed-patch schema and verified mapped destinations are pending')
  payload={'patches':patches,'hubspot_write_authorized':False,'delivery_authorized':False};status='blocked_contract_pending'
 elif destination in {'a3_outreach','a14_field_rep'}:
  if record.get('review',{}).get('record_decision')!='approved':errors.append('approved canonical review required')
  if destination=='a3_outreach' and record.get('duplicate_and_eligibility',{}).get('outreach_eligibility_status')!='eligible':errors.append('authoritative outreach eligibility required')
  errors.append('destination handoff contract and durable delivery receipt are pending')
  payload={'record_reference':m.get('record_revision_id'),'review_decision':record.get('review',{}).get('record_decision'),'delivery_authorized':False};status='blocked_contract_pending'
 hid='A2-HANDOFF-'+canonical_hash({'record':digest,'destination':destination,'payload':payload})[:16].upper()
 return {'command':'a2-governed-handoff','version':'0.1.0-draft.1','handoff_id':hid,'destination':destination,'status':status,'a2_record_id':m.get('a2_record_id'),'record_revision_id':m.get('record_revision_id'),'canonical_record_sha256':digest,'payload':payload,'delivery_receipt':None,'delivered':False,'hubspot_write_authorized':False,'outreach_authorized':False,'external_actions':0,'errors':sorted(set(errors))}
def main()->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('record',type=Path);p.add_argument('--destination',required=True);p.add_argument('--previous-record',type=Path);p.add_argument('--review-receipt',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();cat=load_active(CAT_REL);r=build(load(a.record),a.destination,load(a.previous_record) if a.previous_record else None,cat,load(a.review_receipt) if a.review_receipt else None);text=json.dumps(r,indent=2,ensure_ascii=False)+'\n'
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text,encoding='utf-8')
 print(text,end='');return 1 if r['errors'] else 0
if __name__=='__main__':raise SystemExit(main())
