#!/usr/bin/env python3
"""Calculate A2 evidence confidence, verification and freshness deterministically."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_wave3_contracts import ROOT,canonical_hash,load,load_active
POLICY_REL='foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.3.0.json'
DEFAULT_POLICY=ROOT/POLICY_REL

def evaluate(item:dict,policy:dict)->dict:
 errors=[];dims=policy['confidence_dimensions'];source=policy['source_rules'].get(item.get('source_id'));inherited=None
 receipt=item.get('source_preflight');source_gate_passed=False
 if item.get('source_id') in {'a1_approved_handoff','a1_directory_evidence_reuse'}:
  source_gate_passed=True
 elif not isinstance(receipt,dict):
  errors.append('matching hashed source_preflight receipt is required')
 else:
  supplied=receipt.get('preflight_sha256');calculated=canonical_hash({k:v for k,v in receipt.items() if k!='preflight_sha256'})
  if supplied!=calculated:errors.append('source_preflight receipt hash mismatch')
  if receipt.get('source_id')!=item.get('source_id') or receipt.get('field_key')!=item.get('claim_key'):errors.append('source_preflight receipt scope mismatch')
  source_gate_passed=receipt.get('preflight_status') in {'allowed_local_fixture','allowed_local_reuse','completed','completed_fixture'} and receipt.get('external_actions')==0
 if source is None:
  errors.append(f"unknown source_id {item.get('source_id')!r}");authority='blocked_or_unverified'
 else:
  authority=source['authority']
  if authority=='preserve_inherited':
   inherited=item.get('inherited_confidence')
   if not isinstance(inherited,dict):errors.append('A1 inherited evidence requires inherited_confidence')
   authority='blocked_or_unverified'
 inputs={'identity_match':item.get('identity_match'),'source_authority':authority,'claim_directness':item.get('claim_directness'),'freshness':item.get('freshness'),'corroboration':item.get('corroboration'),'consistency':item.get('consistency')}
 components={}
 for dimension,level in inputs.items():
  values=dims[dimension]['levels']
  if level not in values:errors.append(f'unknown {dimension} level {level!r}');components[dimension]=0
  else:components[dimension]=values[level]
 raw=sum(components.values());caps=[]
 if item.get('identity_match')=='unresolved':caps.append(('identity_match_unresolved',39))
 if item.get('consistency')=='material_conflict':caps.append(('material_conflict',39))
 if item.get('required_claim') is True and item.get('claim_directness')=='reasonable_inference':caps.append(('required_claim_supported_only_by_reasonable_inference',59))
 if item.get('freshness')=='stale':caps.append(('time_sensitive_claim_is_stale',59))
 if not source_gate_passed or authority in {'search_discovery','blocked_or_unverified'}:caps.append(('source_rights_or_runtime_gate_not_passed',0))
 score=min([raw,*[v for _,v in caps]]) if caps else raw
 level='high' if score>=80 else 'medium' if score>=60 else 'low'
 if inherited is not None and not errors:
  score=inherited.get('score');level=inherited.get('level');verification=inherited.get('verification_status');components={};caps=[]
 elif errors:verification='error'
 elif item.get('consistency')=='material_conflict':verification='contradicted'
 elif score>=80 and item.get('identity_match')=='exact' and item.get('claim_directness')=='direct_fact' and source_gate_passed and item.get('freshness') not in {'stale','error'}:verification='verified'
 elif score>=60:verification='partially_verified'
 else:verification='unverified'
 evidence_id=item.get('evidence_id') or 'A2-EV-'+canonical_hash({'field':item.get('field_assessment_id'),'source':item.get('source_id'),'value':item.get('normalised_value'),'refs':item.get('source_references',[])})[:16].upper()
 return {'command':'a2-evaluate-evidence-confidence','version':'0.1.0-draft.1','evidence_id':evidence_id,'field_assessment_id':item.get('field_assessment_id'),'source_id':item.get('source_id'),'claim_key':item.get('claim_key'),'normalised_value':item.get('normalised_value'),'components':components,'raw_score':raw,'applied_caps':[{'condition':n,'maximum_score':v} for n,v in caps],'confidence_score':score,'confidence_level':level,'verification_status':verification,'freshness_status':item.get('freshness'),'source_references':item.get('source_references',[]),'source_preflight_sha256':receipt.get('preflight_sha256') if isinstance(receipt,dict) else None,'source_gate_passed':source_gate_passed,'a1_confidence_preserved':inherited is not None,'a1_score_changed':False,'canonical_record_mutated':False,'outreach_authorized':False,'external_actions':0,'errors':errors}

def main()->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('evidence',type=Path);p.add_argument('--policy',type=Path,default=DEFAULT_POLICY);p.add_argument('--output',type=Path);a=p.parse_args()
 policy=load_active(POLICY_REL) if a.policy==DEFAULT_POLICY else load(a.policy);r=evaluate(load(a.evidence),policy);text=json.dumps(r,indent=2,ensure_ascii=False)+'\n'
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text,encoding='utf-8')
 print(text,end='');return 1 if r['errors'] else 0
if __name__=='__main__':raise SystemExit(main())
