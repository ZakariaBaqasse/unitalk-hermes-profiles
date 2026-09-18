#!/usr/bin/env python3
"""Prepare or validate a gated Twenty A2 review payload without integration access."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_wave3_contracts import ROOT,canonical_hash,load
from validate_step3h_twenty_review import errors as receipt_errors
SCHEMA=ROOT/'foundations/contracts/twenty/a2-twenty-review-receipt.schema.json'
def prepare(record:dict)->dict:
 m=record['record_metadata'];candidate=record['source_handoff']['handoff_snapshot']['candidate_snapshot']['candidate_id'];digest=canonical_hash(record)
 return {'command':'a2-twenty-review','mode':'prepare','version':'0.1.0-draft.1','status':'prepared_not_delivered','review_payload_id':'A2-TWENTY-PREP-'+digest[:16].upper(),'a1_candidate_id':candidate,'a2_record_id':m['a2_record_id'],'record_revision_id':m['record_revision_id'],'canonical_record_sha256':digest,'field_assessment_ids':[x['field_assessment_id'] for x in record['field_assessments']],'twenty_candidate_id':None,'twenty_review_id':None,'workspace_mapping_status':'pending_metadata_snapshot','hubspot_write_authorized':False,'outreach_authorized':False,'external_actions':0,'errors':[]}
def validate_receipt(receipt:dict,record:dict)->dict:
 es=receipt_errors(receipt,load(SCHEMA));m=record['record_metadata'];candidate=record['source_handoff']['handoff_snapshot']['candidate_snapshot']['candidate_id'];digest=canonical_hash(record)
 checks={'candidate':receipt.get('a1_candidate_id')==candidate,'record':receipt.get('a2_record_id')==m.get('a2_record_id'),'revision':receipt.get('record_revision_id')==m.get('record_revision_id'),'hash':receipt.get('canonical_record_sha256')==digest,'no_hubspot_write':receipt.get('hubspot_write_authorized') is False}
 for k,v in checks.items():
  if not v:es.append(f'receipt {k} mismatch')
 return {'command':'a2-twenty-review','mode':'validate_receipt','version':'0.1.0-draft.1','valid':not es,'review_receipt_id':receipt.get('review_receipt_id'),'review_status':receipt.get('review_status'),'checks':checks,'proposed_patch_preparation_authorized':receipt.get('review_status')=='approved' and not es,'hubspot_write_authorized':False,'outreach_authorized':False,'external_actions':0,'errors':sorted(set(es))}
def main()->int:
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True);a=sub.add_parser('prepare');a.add_argument('record',type=Path);a.add_argument('--output',type=Path);b=sub.add_parser('validate-receipt');b.add_argument('receipt',type=Path);b.add_argument('record',type=Path);b.add_argument('--output',type=Path);x=p.parse_args();r=prepare(load(x.record)) if x.mode=='prepare' else validate_receipt(load(x.receipt),load(x.record));text=json.dumps(r,indent=2,ensure_ascii=False)+'\n'
 if x.output:x.output.parent.mkdir(parents=True,exist_ok=True);x.output.write_text(text,encoding='utf-8')
 print(text,end='');return 1 if r.get('errors') else 0
if __name__=='__main__':raise SystemExit(main())
