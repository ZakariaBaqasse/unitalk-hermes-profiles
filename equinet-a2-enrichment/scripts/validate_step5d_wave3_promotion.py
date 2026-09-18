#!/usr/bin/env python3
"""Post-promotion validation for Equinet A2 Step 5D Wave 3."""
from __future__ import annotations
import copy,hashlib,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from a2_wave3_contracts import ContractError,load as strict_load
from evaluate_a2_evidence_confidence import evaluate as evidence_eval
from evaluate_a2_protected_field_action import evaluate as protected_eval
from create_a2_revision import finalise
from render_and_validate_a2_review_package import build as review_build
from build_and_validate_a2_twenty_review import prepare as twenty_prepare,validate_receipt
from build_and_validate_a2_handoff import build as handoff_build
from preflight_a2_source_action import preflight
from validate_step5c_wave2 import prepare_source_request
E=ROOT/'evaluations/step5d';RUNTIME=ROOT/'foundations/contracts/skills/a2-wave3-runtime-manifest-0.1.0.json';ACC=E/'acceptance-record.json';PROMO=E/'wave3-promotion-manifest.json';ACTIVE=ROOT/'foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json';FIX=E/'fixtures/wave3-cases.json';TECH=E/'technical-validation.json';BEH=E/'behavioural-validation.json';LANG=ROOT/'evaluations/foundation-clarifications/language-audit.json';OUT=E/'post-promotion-validation.json';EP=ROOT/'foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.1.1-draft.1.json';PP=ROOT/'foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.1.1-draft.1.json';CAT=ROOT/'foundations/contracts/business/a2-business-field-catalogue-0.1.1-draft.1.json';SOURCE=ROOT/'foundations/contracts/sources/a2-source-register-0.1.1-draft.1.json';PROVIDERS=ROOT/'foundations/contracts/governance/a2-provider-and-cost-policy-0.1.1-draft.1.json'
SKILLS=[ROOT/f'skills/{x}/SKILL.md' for x in ['a2-evidence-confidence-and-freshness','a2-protected-field-conflict-resolution','a2-data-quality-and-review-readiness','a2-review-package-and-governed-handoffs']]
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 errors=[];cases=[];runtime,acc,promo,active=map(load,[RUNTIME,ACC,PROMO,ACTIVE]);f=load(FIX);ep=load(EP);pp=load(PP);cat=load(CAT);source=load(SOURCE);providers=load(PROVIDERS);beh=load(BEH)
 if runtime.get('status')!='approved_local_no_integration' or acc.get('decision')!='approved_and_promoted':errors.append('Wave 3 approval state mismatch')
 if acc.get('approved_decisions')!=[f'W3-{n}' for n in range(1,11)]:errors.append('Wave 3 decision set mismatch')
 for p in SKILLS:
  t=p.read_text()
  if '**Version:** `0.1.0`' not in t or '**Status:** `WAVE 3 APPROVED — LOCAL NO-INTEGRATION MODE`' not in t:errors.append(f'skill not promoted: {p.parent.name}')
 for sec in ['skills','commands','supporting_modules','pinned_dependencies']:
  for x in runtime.get(sec,[]):
   for pk,hk in [('path','sha256'),('evals_path','evals_sha256')]:
    if pk in x:
     p=ROOT/x[pk]
     if not p.exists() or sha(p)!=x[hk]:errors.append(f'runtime hash mismatch: {x[pk]}')
 for x in active['active_files']:
  p=ROOT/x['path']
  if not p.exists() or sha(p)!=x['sha256']:errors.append(f'active hash mismatch: {x["path"]}')
 for x in promo['files']:
  p=ROOT/x['path']
  if not p.exists() or sha(p)!=x['sha256']:errors.append(f'promotion hash mismatch: {x["path"]}')
 if sha(RUNTIME)!=acc['runtime_manifest_sha256']:errors.append('runtime acceptance hash mismatch')
 active_paths={x.get('path') for x in active.get('active_files',[])};later_step5='foundations/contracts/skills/a2-step5-runtime-manifest-0.1.0.json' in active_paths
 if not later_step5 and (sha(ACTIVE)!=acc['active_foundation_manifest_sha256'] or sha(ACTIVE)!=promo['active_foundation_manifest']['sha256']):errors.append('acceptance/promotion manifest hash mismatch')
 if later_step5 and 'foundations/contracts/skills/a2-wave3-runtime-manifest-0.1.0.json' not in active_paths:errors.append('Wave 3 runtime missing from consolidated active foundation')
 def add(n,ok):cases.append({'name':n,'passed':ok});errors.append(f'post case failed: {n}') if not ok else None
 for c in f['evidence_cases']:
  q=copy.deepcopy(c['request']);provider=q['source_id'].startswith('apify_');preq={'candidate_id':'SYN-W3-POST','operating_scope':'synthetic_test','source_id':q['source_id'],'field_key':q['claim_key'],'named_need':'post promotion evidence','execution_mode':'preflight_only' if provider else 'local_fixture_simulation','fixture_is_synthetic':not provider,'fixture_reference':None if provider else f"fixtures://{c['name']}",'official_site_check':'completed_fixture','named_role_gap':True,'selected_profile_match':True,'max_items':5,'max_searches':1,'automatic_query_segmentation':False};q['source_preflight']=preflight(prepare_source_request(preq),source,cat,providers);r=evidence_eval(q,ep);x=c['expected'];ok=r['verification_status']==x['verification_status'] and r['external_actions']==0
  if 'confidence_level' in x:ok=ok and r['confidence_level']==x['confidence_level']
  if 'maximum_score' in x:ok=ok and any(z['maximum_score']==x['maximum_score'] for z in r['applied_caps'])
  add(c['name'],ok)
 for c in f['protected_cases']:
  r=protected_eval(c['request'],pp);add(c['name'],r['recommended_action']==c['expected'] and r['external_write_allowed'] is False)
 rec=f['records'];prev=load(ROOT/rec['review_previous']);cur=load(ROOT/rec['review_current']);r=finalise(prev,cur,cat);add('valid-immutable-revision',r['valid'])
 bad=copy.deepcopy(cur);bad['source_handoff']['handoff_id']='MUTATED';r=finalise(prev,bad,cat);add('mutated-handoff-rejected',not r['valid'])
 bad=copy.deepcopy(cur);bad['record_metadata']['supersedes_revision_id']='WRONG';r=finalise(prev,bad,cat);add('bad-lineage-rejected',not r['valid'])
 with tempfile.TemporaryDirectory(prefix='a2-w3-post-') as n:r=review_build(ROOT/rec['review_current'],Path(n)/'review',ROOT/rec['review_previous'],ROOT/'foundations/contracts/canonical/a2-review-view-spec-0.1.0.json');add('lossless-review-package',r['valid'])
 add('twenty-payload-prepared',twenty_prepare(cur)['status']=='prepared_not_delivered');rv=validate_receipt(load(ROOT/'evaluations/step3h/fixtures/valid-approved.json'),cur);add('twenty-mismatch-rejected',not rv['valid'])
 rq=load(ROOT/rec['requalification_current']);rqp=load(ROOT/rec['requalification_previous']);add('a1-requalification-prepared',handoff_build(rq,'a1_requalification',rqp,cat)['status']=='prepared_not_delivered');add('hubspot-contract-pending',handoff_build(cur,'hubspot_proposed_patch',prev,cat)['status']=='blocked_contract_pending');add('a3-contract-pending',handoff_build(cur,'a3_outreach',prev,cat)['status']=='blocked_contract_pending');ap=load(ROOT/rec['approved_current']);app=load(ROOT/rec['approved_previous']);add('a14-contract-pending',handoff_build(ap,'a14_field_rep',app,cat)['status']=='blocked_contract_pending')
 with tempfile.TemporaryDirectory(prefix='a2-w3-post-json-') as n:
  p=Path(n)/'x';p.write_text('{"a":1,"a":2}')
  try:strict_load(p);ok=False
  except ContractError:ok=True
  add('duplicate-json-rejected',ok);p.write_text('{"a":NaN}')
  try:strict_load(p);ok=False
  except ContractError:ok=True
  add('non-finite-json-rejected',ok)
 lang=load(LANG)
 if not lang.get('pass'):errors.append('language audit failed')
 result={'step':'5D','stage':'post_promotion','status':'approved_and_promoted' if not errors else 'promotion_validation_failed','skills':4,'deterministic_replay':{'total':len(cases),'passed':sum(x['passed'] for x in cases),'cases':cases},'behavioural_replay':{'total':beh.get('scenario_count'),'passed':beh.get('passed'),'status':beh.get('overall_status')},'active_foundation_files':len(active['active_files']),'language_audit':{'files_checked':lang.get('files_checked'),'passed':lang.get('pass')},'external_calls':0,'external_actions':0,'next_gate':'Step 5E — Full Operational Skills Regression and No-Integration Workflow','failures':errors,'pass':not errors};OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'pass':result['pass'],'replay':f"{result['deterministic_replay']['passed']}/{result['deterministic_replay']['total']}",'behavioural':f"{result['behavioural_replay']['passed']}/{result['behavioural_replay']['total']}",'active_files':result['active_foundation_files'],'external_actions':0,'failures':errors},indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
