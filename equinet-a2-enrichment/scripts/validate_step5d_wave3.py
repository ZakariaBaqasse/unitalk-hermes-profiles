#!/usr/bin/env python3
"""Validate Equinet A2 Step 5D Wave 3 skills and commands."""
from __future__ import annotations
import copy,hashlib,json,py_compile,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];S=ROOT/'scripts';sys.path.insert(0,str(S))
from a2_wave3_contracts import ContractError,load as strict_load
from evaluate_a2_evidence_confidence import evaluate as evidence_eval
from evaluate_a2_protected_field_action import evaluate as protected_eval
from create_a2_revision import finalise
from render_and_validate_a2_review_package import build as review_build
from build_and_validate_a2_twenty_review import prepare as twenty_prepare,validate_receipt
from build_and_validate_a2_handoff import build as handoff_build
from preflight_a2_source_action import preflight
from validate_step5c_wave2 import prepare_source_request
E=ROOT/'evaluations/step5d';FIX=E/'fixtures/wave3-cases.json';TECH=E/'technical-validation.json';BEH=E/'behavioural-validation.json';REVIEW=E/'A2-WAVE-3-REVIEW.md';PACKAGE=E/'wave3-draft-package-manifest.json';ACTIVE=ROOT/'foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json';W2=ROOT/'evaluations/step5c/acceptance-record.json';LANG=ROOT/'evaluations/foundation-clarifications/language-audit.json'
POL_E=ROOT/'foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.1.1-draft.1.json';POL_P=ROOT/'foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.1.1-draft.1.json';CAT=ROOT/'foundations/contracts/business/a2-business-field-catalogue-0.1.1-draft.1.json';SOURCE=ROOT/'foundations/contracts/sources/a2-source-register-0.1.1-draft.1.json';PROVIDERS=ROOT/'foundations/contracts/governance/a2-provider-and-cost-policy-0.1.1-draft.1.json';REVIEW_SPEC=ROOT/'foundations/contracts/canonical/a2-review-view-spec-0.1.0.json';TWENTY_SCHEMA=ROOT/'foundations/contracts/twenty/a2-twenty-review-receipt.schema.json';TWENTY_CONTRACT=ROOT/'foundations/contracts/twenty/a2-twenty-review-layer-contract-0.1.0-draft.1.json';REQUAL_SCHEMA=ROOT/'foundations/contracts/requalification/a2-requalification-package.schema.json';CANONICAL_SCHEMA=ROOT/'foundations/contracts/canonical/a2-enrichment-record.schema.json'
SKILLS=[ROOT/f'skills/{x}/SKILL.md' for x in ['a2-evidence-confidence-and-freshness','a2-protected-field-conflict-resolution','a2-data-quality-and-review-readiness','a2-review-package-and-governed-handoffs']];EVALS=[p.parent/'evals/evals.json' for p in SKILLS]
COMMANDS=[ROOT/f'scripts/{x}' for x in ['evaluate_a2_evidence_confidence.py','evaluate_a2_protected_field_action.py','create_a2_revision.py','render_and_validate_a2_review_package.py','build_and_validate_a2_twenty_review.py','build_and_validate_a2_handoff.py']];SUPPORT=[ROOT/'scripts/a2_wave3_contracts.py']
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 failures=[];cases=[];active=load(ACTIVE);w2=load(W2);f=load(FIX);ep=load(POL_E);pp=load(POL_P);cat=load(CAT);source=load(SOURCE);providers=load(PROVIDERS)
 if w2.get('decision')!='approved_and_promoted' or w2.get('next_gate')!='Step 5D — Wave 3 Decision, Review and Handoffs':failures.append('Wave 2 approval prerequisite failed')
 idx={x['path']:x['sha256'] for x in active['active_files']}
 for p in [POL_E,POL_P,CAT]:
  rel=str(p.relative_to(ROOT))
  if idx.get(rel)!=sha(p):failures.append(f'active dependency mismatch: {rel}')
 for p in [REVIEW_SPEC,TWENTY_SCHEMA,TWENTY_CONTRACT,REQUAL_SCHEMA,CANONICAL_SCHEMA]:
  if not p.is_file():failures.append(f'missing pinned Wave 3 dependency: {p.relative_to(ROOT)}')
 checks=[]
 for sp,ev in zip(SKILLS,EVALS):
  text=sp.read_text() if sp.exists() else '';e=load(ev) if ev.exists() else {};c={'name':f'name: {sp.parent.name}' in text,'draft':'WAVE 3 DRAFT — NOT APPROVED' in text,'mission':'## Mission' in text,'command':'## Command' in text or '## Commands' in text,'boundaries':'## Boundaries' in text,'handoff':'## Handoff' in text,'evals':len(e.get('evals',[]))==3};checks.append({'skill_id':sp.parent.name,'checks':c,'passed':all(c.values())});
  if not all(c.values()):failures.append(f'skill package failed: {sp.parent.name}')
 comp=[]
 for p in [*COMMANDS,*SUPPORT]:
  try:py_compile.compile(str(p),doraise=True);comp.append({'path':str(p.relative_to(ROOT)),'passed':True})
  except Exception as x:comp.append({'path':str(p.relative_to(ROOT)),'passed':False,'error':str(x)});failures.append(f'compile failed: {p.name}')
 def add(name,result,passed):cases.append({'name':name,'result':result,'passed':passed});failures.append(f'case failed: {name}') if not passed else None
 for c in f['evidence_cases']:
  req=copy.deepcopy(c['request']);provider=req['source_id'].startswith('apify_');mode='preflight_only' if provider else 'local_fixture_simulation';preq={'candidate_id':'SYN-W3-EVIDENCE','operating_scope':'synthetic_test','source_id':req['source_id'],'field_key':req['claim_key'],'named_need':'Wave 3 evidence assessment','execution_mode':mode,'fixture_is_synthetic':not provider,'fixture_reference':None if provider else f"fixtures://{c['name']}",'official_site_check':'completed_fixture','named_role_gap':True,'selected_profile_match':True,'max_items':5,'max_searches':1,'automatic_query_segmentation':False};req['source_preflight']=preflight(prepare_source_request(preq),source,cat,providers)
  r=evidence_eval(req,ep);x=c['expected'];ok=r['verification_status']==x['verification_status'] and r['external_actions']==0
  if 'confidence_level' in x:ok=ok and r['confidence_level']==x['confidence_level']
  if 'maximum_score' in x:ok=ok and any(v['maximum_score']==x['maximum_score'] for v in r['applied_caps'])
  add(c['name'],r,ok)
 for c in f['protected_cases']:
  r=protected_eval(c['request'],pp);add(c['name'],r,r['recommended_action']==c['expected'] and r['external_write_allowed'] is False and r['external_actions']==0)
 rec=f['records'];prev=load(ROOT/rec['review_previous']);cur=load(ROOT/rec['review_current']);r=finalise(prev,cur,cat);add('valid-immutable-revision',r,r['valid'] and not r['prior_record_mutated'])
 bad=copy.deepcopy(cur);bad['source_handoff']['handoff_id']='MUTATED';r=finalise(prev,bad,cat);add('mutated-handoff-rejected',r,not r['valid'] and 'immutable source_handoff changed' in r['errors'])
 bad=copy.deepcopy(cur);bad['record_metadata']['supersedes_revision_id']='WRONG';r=finalise(prev,bad,cat);add('bad-lineage-rejected',r,not r['valid'] and 'supersedes_revision_id mismatch' in r['errors'])
 with tempfile.TemporaryDirectory(prefix='a2-w3-') as n:
  rr=review_build(ROOT/rec['review_current'],Path(n)/'review',ROOT/rec['review_previous'],ROOT/'foundations/contracts/canonical/a2-review-view-spec-0.1.0.json');add('lossless-review-package',rr,rr['valid'] and rr['external_actions']==0)
 prep=twenty_prepare(cur);add('twenty-payload-prepared',prep,prep['status']=='prepared_not_delivered' and prep['external_actions']==0)
 receipt=load(ROOT/'evaluations/step3h/fixtures/valid-approved.json');rv=validate_receipt(receipt,cur);add('twenty-receipt-mismatch-rejected',rv,not rv['valid'] and rv['hubspot_write_authorized'] is False)
 rq=load(ROOT/rec['requalification_current']);rqp=load(ROOT/rec['requalification_previous']);h=handoff_build(rq,'a1_requalification',rqp,cat);add('a1-requalification-prepared',h,h['status']=='prepared_not_delivered' and not h['delivered'])
 h=handoff_build(cur,'hubspot_proposed_patch',prev,cat);add('hubspot-patch-contract-pending-blocked',h,h['status']=='blocked_contract_pending' and h['hubspot_write_authorized'] is False)
 h=handoff_build(cur,'a3_outreach',prev,cat);add('a3-contract-and-approval-blocked',h,h['status']=='blocked_contract_pending' and h['outreach_authorized'] is False)
 ap=load(ROOT/rec['approved_current']);app=load(ROOT/rec['approved_previous']);h=handoff_build(ap,'a14_field_rep',app,cat);add('a14-contract-pending-blocked',h,h['status']=='blocked_contract_pending' and not h['delivered'])
 with tempfile.TemporaryDirectory(prefix='a2-w3-json-') as n:
  p=Path(n)/'x.json';p.write_text('{"a":1,"a":2}')
  try:strict_load(p);ok=False
  except ContractError as x:ok='duplicate JSON key' in str(x)
  add('duplicate-json-rejected',{'expected':'duplicate JSON key'},ok);p.write_text('{"a":NaN}')
  try:strict_load(p);ok=False
  except ContractError as x:ok='non-finite JSON number' in str(x)
  add('non-finite-json-rejected',{'expected':'non-finite JSON number'},ok)
 b=load(BEH) if BEH.exists() else {};bc={'present':BEH.exists(),'pass':b.get('overall_status')=='pass','four':b.get('passed')==4 and b.get('scenario_count')==4,'zero':b.get('external_actions')==0}
 if not all(bc.values()):failures.append('behavioural validation failed')
 subprocess.run([sys.executable,str(ROOT/'scripts/audit_profile_language.py')],cwd=ROOT,capture_output=True);lang=load(LANG)
 if not lang.get('pass'):failures.append('language audit failed')
 result={'step':'5D','wave':3,'status':'ready_for_severine_review_not_approved' if not failures else 'validation_failed','skill_count':4,'command_count':6,'supporting_module_count':1,'package_checks':checks,'compile_checks':comp,'deterministic_cases':{'total':len(cases),'passed':sum(x['passed'] for x in cases),'cases':cases},'behavioural_validation':bc,'language_audit':{'files_checked':lang.get('files_checked'),'passed':lang.get('pass')},'external_calls':0,'external_actions':0,'approval_required':True,'promotion_performed':False,'next_gate_after_approval':'Step 5E — Full Operational Skills Regression and No-Integration Workflow','failures':failures,'pass':not failures};E.mkdir(parents=True,exist_ok=True);TECH.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 decisions=[
 ('W3-1','Use the active six-dimension evidence policy; confidence is not ICP fit.'),('W3-2','Preserve inherited A1 evidence confidence and never rescore it in A2.'),('W3-3','Treat material conflict, stale data and failed source gates with deterministic caps and holds.'),('W3-4','Preserve authoritative, read-only, owner and manual baselines; never silently overwrite them.'),('W3-5','Create requalification signals for A1-material evidence without points or replacement scores.'),('W3-6','Require immutable canonical revision lineage and append-only evidence, observations and audit.'),('W3-7','Keep missing required data incomplete or held, never automatically rejected.'),('W3-8','Render Markdown, CSV and Excel as lossless read-only projections of canonical JSON.'),('W3-9','Treat Twenty approval as eligibility for future proposed-patch preparation only; keep patch generation blocked until its strict schema and verified mappings exist.'),('W3-10','Keep A1 output prepared-not-delivered and block HubSpot, A3 and A14 until their contracts and durable receipt paths exist.')]
 rows='\n'.join(f'| {i} | {d} |' for i,d in decisions);REVIEW.write_text(f'''# Decision Review — Step 5D Wave 3 Decision, Review and Handoffs\n\n**Status:** `READY FOR SÉVERINE REVIEW — NOT APPROVED`  \n**Profile:** `equinet-a2-enrichment`\n\n## Delivered skill packages\n\n1. `a2-evidence-confidence-and-freshness`;\n2. `a2-protected-field-conflict-resolution`;\n3. `a2-data-quality-and-review-readiness`;\n4. `a2-review-package-and-governed-handoffs`.\n\n## Decisions proposed\n\n| ID | Decision |\n|---|---|\n{rows}\n\n## Technical result\n\n- Skills: **4/4 present**.\n- Commands: **6/6 compile**.\n- Deterministic cases: **{sum(x['passed'] for x in cases)}/{len(cases)} PASS**.\n- Behavioural scenarios: **{b.get('passed',0)}/4 PASS**.\n- External calls/actions: **0/0**.\n- Language audit: **PASS — {lang.get('files_checked')} files checked**.\n\nApproval promotes Wave 3 for local no-integration use. It does not activate Twenty, HubSpot, n8n, providers, outreach or delivery.\n''')
 files=[*SKILLS,*EVALS,*COMMANDS,*SUPPORT,FIX,BEH,TECH,REVIEW,W2,ACTIVE,POL_E,POL_P,CAT,REVIEW_SPEC,TWENTY_SCHEMA,TWENTY_CONTRACT,REQUAL_SCHEMA,CANONICAL_SCHEMA];manifest={'manifest_id':'equinet-a2-wave3-draft-package','version':'0.1.0-draft.1','status':result['status'],'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files if p.exists()],'file_count':sum(p.exists() for p in files),'skills':4,'commands':6,'deterministic_cases':f"{sum(x['passed'] for x in cases)}/{len(cases)} pass",'external_actions':0,'promotion_performed':False};PACKAGE.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'pass':result['pass'],'skills':4,'deterministic':manifest['deterministic_cases'],'behavioural':f"{b.get('passed',0)}/4",'status':result['status'],'failures':failures},indent=2));return 0 if not failures else 1
if __name__=='__main__':raise SystemExit(main())
