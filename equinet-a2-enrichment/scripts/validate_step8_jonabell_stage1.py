#!/usr/bin/env python3
"""Validate the Jonabell Step 8 Stage 1 profile outputs."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'evaluations/step8/pilot/A1-DARLEY-JONABELL-001';OUT=B/'stage1-validation.json'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def can(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
 a=load(B/'stage1-analysis.reviewed.json' if (B/'stage1-analysis.reviewed.json').exists() else B/'stage1-analysis.json');u=load(B/'stage1-audit.reviewed.json' if (B/'stage1-audit.reviewed.json').exists() else B/'stage1-audit.json');batch=load(B/'observation-batch.json');v=load(B/'validated-observations.json');checks={};findings=[]
 checks['candidate']=a.get('candidate_id')==u.get('candidate_id')==batch.get('candidate_id')==v.get('candidate_id')=='A1-DARLEY-JONABELL-001'
 checks['validated_batch']=v.get('accepted_count')==3 and v.get('rejected_count')==1 and v.get('batch_status')=='completed_with_rejections'
 checks['no_final_confidence']=v.get('final_confidence_assigned') is False
 checks['no_canonical_mutation']=v.get('canonical_record_mutated') is False
 checks['zero_external_actions']=v.get('external_actions')==u.get('external_actions')==0
 receipt_ok=True
 for p in (B/'receipts').glob('*.json'):
  r=load(p);receipt_ok &= r['preflight_sha256']==can({k:x for k,x in r.items() if k!='preflight_sha256'})
 checks['receipt_hashes']=receipt_ok
 source_ok=True
 for x in batch['observations'][:3]:
  r=x['source_preflight'];p=ROOT/r['audit']['output_reference'];source_ok &= p.exists() and sha(p)==r['source_content_sha256']
 checks['source_content_hashes']=source_ok
 checks['analysis_self_hash']=a.get('sha256')==can({k:x for k,x in a.items() if k!='sha256'})
 checks['audit_self_hash']=u.get('sha256')==can({k:x for k,x in u.items() if k!='sha256'})
 actual_ids={x['field_key']:x['field_assessment_candidate']['field_assessment_id'] for x in v['observations'][:3]};checks['analysis_assessment_ids']=all(x.get('field_assessment_id')==actual_ids.get(x['field_key']) for x in a.get('field_dispositions',[]))
 checks['analysis_state_language']=all(x.get('validation_action')=='accept_for_wave3_evidence_assessment' and x.get('validation_state')=='present_unverified' for x in a.get('field_dispositions',[]))
 checks['gateway_name']=a.get('unitalk_gateway')=='litellm-unitalk' and u.get('entity',{}).get('unitalk_gateway')=='litellm-unitalk'
 checks['model_usage_not_zeroed']=u.get('usage_and_cost',{}).get('model_calls')==1 and u.get('usage_and_cost',{}).get('cost_status')=='unavailable'
 files={'handoff_json':'evaluations/step8/handoffs/A1-DARLEY-JONABELL-001.handoff.json','initial_record_json':'evaluations/step8/intake/A1-DARLEY-JONABELL-001/initial-record.json','reuse_snapshot_json':'evaluations/step8/planning/A1-DARLEY-JONABELL-001.reuse-snapshot.json','gap_plan_json':'evaluations/step8/planning/A1-DARLEY-JONABELL-001.gap-plan.json','collection_manifest_json':'evaluations/step8/collection/collection-manifest.json','page_01_md':'evaluations/step8/collection/A1-DARLEY-JONABELL-001/page-01.md','page_02_md':'evaluations/step8/collection/A1-DARLEY-JONABELL-001/page-02.md'};mismatches=[]
 for key,rel in files.items():
  actual=sha(ROOT/rel)
  if u.get('source_file_hashes',{}).get(key)!=actual:mismatches.append({'key':key,'path':rel,'declared':u.get('source_file_hashes',{}).get(key),'actual':actual})
 checks['audit_file_hashes']=not mismatches
 checks['role_priority_recommendation']=a.get('target_role_priority_recommendation',{}).get('recommendation')=='secondary' and a['target_role_priority_recommendation'].get('human_review_required') is True and a['target_role_priority_recommendation'].get('not_a_sourced_fact') is True
 if not checks['analysis_assessment_ids']:findings.append('Replace null field_assessment_id values with the deterministic IDs from validated-observations.json.')
 if not checks['analysis_state_language']:findings.append('Do not describe Stage 1 fields as verified or propose_keep; they are present_unverified and accepted for evidence assessment only.')
 if not checks['gateway_name']:findings.append('Replace hermes_tui with litellm-unitalk / Unitalk AI Gateway in deployment artifacts.')
 if not checks['model_usage_not_zeroed']:findings.append('Record one model call; tokens and cost may remain unavailable but must not be zero.')
 if mismatches:findings.append('Replace canonical object hashes mislabeled as source_file_hashes with actual SHA-256 file hashes.')
 result={'record_type':'step8_jonabell_stage1_validation','status':'accepted_pending_relationship_review' if all(checks.values()) else 'changes_required','checks':checks,'checks_passed':sum(checks.values()),'checks_total':len(checks),'accepted_observations':['organisation.stable_type','person.role_title','person.business_email'],'accepted_observation_state':'present_unverified_ready_for_evidence_assessment','rejected_observation':'relationship.target_role_priority','review_decision_required':{'field_key':'relationship.target_role_priority','recommendation':'secondary','recommended_decision':'approve_as_reviewed_classification_not_sourced_fact'},'audit_hash_mismatches':mismatches,'required_corrections':findings,'canonical_revision_authorized':False,'rood_and_riddle_authorized':False,'external_actions':0};OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps(result,indent=2,ensure_ascii=False));return 0 if result['status'].startswith('accepted') else 2
if __name__=='__main__':raise SystemExit(main())
