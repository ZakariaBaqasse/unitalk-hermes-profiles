#!/usr/bin/env python3
"""Validate and finalise one immutable A2 canonical revision without external actions."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_wave3_contracts import ROOT,canonical_hash,load,load_active
from validate_a2_enrichment_record import validate
CAT_REL='foundations/contracts/business/a2-business-field-catalogue-0.3.0.json';CAT=ROOT/CAT_REL

def finalise(previous:dict,proposed:dict,catalogue:dict)->dict:
 errors=[]
 nv=validate(proposed,previous=previous,field_catalogue=catalogue if proposed.get('enrichment_scope',{}).get('field_catalogue_version')==catalogue.get('version') else None)
 if not nv['valid']:errors.extend('proposed: '+e for e in nv['errors'])
 prior_catalogue=previous.get('enrichment_scope',{}).get('field_catalogue_version');next_catalogue=proposed.get('enrichment_scope',{}).get('field_catalogue_version')
 if prior_catalogue!=next_catalogue:errors.append('field catalogue version changed inside revision lineage')
 if next_catalogue not in {'0.1.0-draft.1','0.1.1-draft.1','0.2.0'}:
  if not (str(next_catalogue).startswith('synthetic-') and proposed.get('record_metadata',{}).get('record_kind')=='synthetic_test'):
   errors.append('unsupported field catalogue compatibility version')
 pm=previous.get('record_metadata',{});nm=proposed.get('record_metadata',{})
 if proposed.get('source_handoff')!=previous.get('source_handoff'):errors.append('immutable source_handoff changed')
 if nm.get('revision_number')!=pm.get('revision_number',0)+1:errors.append('revision_number must increment by one')
 if nm.get('supersedes_revision_id')!=pm.get('record_revision_id'):errors.append('supersedes_revision_id mismatch')
 if nm.get('record_revision_id')==pm.get('record_revision_id'):errors.append('revision ID must change')
 result={'command':'a2-create-revision','version':'0.1.0-draft.1','valid':not errors,'a2_record_id':nm.get('a2_record_id'),'prior_revision_id':pm.get('record_revision_id'),'record_revision_id':nm.get('record_revision_id'),'revision_number':nm.get('revision_number'),'previous_record_sha256':canonical_hash(previous),'record_sha256':canonical_hash(proposed) if not errors else None,'record':proposed if not errors else None,'prior_record_mutated':False,'automatic_rejection':False,'automatic_a1_score_change':False,'external_actions':0,'errors':errors}
 return result

def main()->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('previous_record',type=Path);p.add_argument('proposed_record',type=Path);p.add_argument('--catalogue',type=Path,default=CAT);p.add_argument('--output',type=Path);a=p.parse_args();catalogue=load_active(CAT_REL) if a.catalogue==CAT else load(a.catalogue);r=finalise(load(a.previous_record),load(a.proposed_record),catalogue);text=json.dumps(r,indent=2,ensure_ascii=False)+'\n'
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text,encoding='utf-8')
 print(json.dumps({k:r[k] for k in ['command','valid','a2_record_id','prior_revision_id','record_revision_id','revision_number','previous_record_sha256','record_sha256','external_actions','errors']},indent=2,ensure_ascii=False));return 0 if r['valid'] else 1
if __name__=='__main__':raise SystemExit(main())
