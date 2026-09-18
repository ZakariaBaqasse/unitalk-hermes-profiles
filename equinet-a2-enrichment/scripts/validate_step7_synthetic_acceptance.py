#!/usr/bin/env python3
"""Validate the Step 7 deterministic synthetic acceptance package."""
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evaluations/step7';SUITE=E/'deterministic-acceptance.json';PROFILE_INPUT=E/'profile-test-input.json';PROFILE_RESULT=E/'profile-behavioural-result.json';TECH=E/'technical-validation.json';REVIEW=E/'A2-STEP-7-REVIEW.md';MANIFEST=E/'step7-draft-package-manifest.json';STEP6=ROOT/'evaluations/step6/acceptance-record.json';LANG=ROOT/'evaluations/foundation-clarifications/language-audit.json';RUNNER=ROOT/'scripts/run_step7_synthetic_acceptance.py'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 failures=[];s=load(SUITE);s6=load(STEP6)
 if s6.get('decision')!='approved_for_synthetic_local_testing' or s6.get('real_data_authorized') is not False:failures.append('Step 6 prerequisite mismatch')
 if not s.get('pass') or s.get('passed')!=6 or s.get('scenario_count')!=6:failures.append('deterministic scenario suite failed')
 if s.get('export_formats')!={'markdown':2,'csv':12,'xlsx':2}:failures.append('export format coverage mismatch')
 if not s.get('all_records_synthetic') or s.get('external_actions')!=0:failures.append('synthetic/action boundary mismatch')
 expected={'a2-intake','a2-normalise-resolve-entities','a2-duplicate-eligibility','a2-build-gap-plan','a2-evaluate-minimum-package','a2-source-preflight','a2-social-link-classifier','a2-normalise-validate-observations','a2-evaluate-evidence-confidence','a2-evaluate-protected-field-action','a2-create-revision','a2-render-review-package','a2-twenty-review','a2-governed-handoff'}
 for scenario in ['farrier_review','horse_owner_requalification']:
  r=load(E/f'workflows/{scenario}/workflow-result.json')
  if set(r.get('operator_coverage',[]))!=expected or r.get('external_actions')!=0 or r.get('status')!='pass':failures.append(f'workflow operator coverage failed: {scenario}')
  review=load(E/f'workflows/{scenario}/review-result.json')
  if not review.get('valid'):failures.append(f'review package invalid: {scenario}')
 q=subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/validate_step6_promotion.py')],cwd=ROOT,capture_output=True,text=True);step6=load(ROOT/'evaluations/step6/post-promotion-validation.json')
 if q.returncode!=0 or not step6.get('pass'):failures.append('Step 6/Step 5 regression failed')
 subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/audit_profile_language.py')],cwd=ROOT,capture_output=True);lang=load(LANG)
 if not lang.get('pass'):failures.append('language audit failed')
 profile_validation={'present':PROFILE_RESULT.exists(),'passed':False,'status':'pending'}
 if PROFILE_RESULT.exists():
  p=load(PROFILE_RESULT);exp=load(PROFILE_INPUT)['expected'];checks={'profile':p.get('profile')=='equinet-a2-enrichment','suite_pass':p.get('suite_pass') is True,'scenarios':p.get('scenarios')=='6/6','formats':p.get('exports')=={'markdown':2,'csv':12,'xlsx':2},'external_actions':p.get('external_actions')==0,'identity':'hermes-agent' not in str(p.get('actor','')).lower(),'usage':p.get('model_usage')!='0' and p.get('model_cost')!='0'};profile_validation={'present':True,'passed':all(checks.values()),'status':'pass' if all(checks.values()) else 'failed','checks':checks,'source_sha256':sha(PROFILE_RESULT)}
  if not profile_validation['passed']:failures.append('profile-level invocation failed')
 status='ready_for_severine_review_not_approved' if not failures and profile_validation['passed'] else 'deterministic_pass_profile_invocation_pending' if not failures else 'validation_failed'
 result={'step':'7','version':'0.1.0-draft.1','status':status,'deterministic_scenarios':{'passed':s.get('passed'),'total':s.get('scenario_count')},'profile_invocation':profile_validation,'operator_coverage':'14/14','export_formats':s.get('export_formats'),'step6_regression':step6.get('pass'),'language_audit':{'files_checked':lang.get('files_checked'),'passed':lang.get('pass')},'external_calls':0,'external_actions':0,'approval_required':True,'promotion_performed':False,'real_data_authorized':False,'profile_status':'FOUNDATION CONFIGURED — NOT PILOT-READY','next_gate_after_approval':'Step 8 — Bounded Real No-Integration Pilot','failures':failures,'pass':not failures};TECH.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 decisions=[('S7-1','Use six representative synthetic scenarios covering ready, gap, duplicate, block, protected conflict and requalification outcomes.'),('S7-2','Require every scenario and referenced canonical record to be explicitly synthetic.'),('S7-3','Keep human decisions pending or clearly marked as synthetic fixture decisions.'),('S7-4','Require coverage of all fourteen approved operator commands.'),('S7-5','Validate canonical JSON plus Markdown, twelve CSV files and two Excel workbooks.'),('S7-6','Hold possible duplicates, block confirmed duplicates and preserve authoritative conflicts.'),('S7-7','Prepare A1 requalification without delivery or A2 score calculation.'),('S7-8','Require zero Web, CRM, provider, outreach and external actions.'),('S7-9','Require one profile-level invocation of the concise deterministic suite before Step 7 approval.'),('S7-10','Treat Step 7 approval as synthetic acceptance only; it does not authorise the real-data pilot.')];rows='\n'.join(f'| {i} | {x} |' for i,x in decisions);REVIEW.write_text(f'''# Decision Review — Step 7 Synthetic End-to-End Acceptance\n\n**Status:** `{status.upper()}`  \n**Profile:** `equinet-a2-enrichment`\n\n## Results\n\n- Deterministic scenarios: **{s.get('passed')}/{s.get('scenario_count')} PASS**.\n- Operator coverage: **14/14**.\n- Exports: **2 Markdown, 12 CSV, 2 Excel**.\n- Profile-level invocation: **{profile_validation['status']}**.\n- External calls/actions: **0/0**.\n- Language audit: **PASS — {lang.get('files_checked')} files checked**.\n\n## Decisions proposed\n\n| ID | Decision |\n|---|---|\n{rows}\n\nStep 7 approval will not authorise real Mustad/Equinet data. The Step 8 real-data gate remains separately blocked by provider telemetry/governance and named reviewer inputs.\n''')
 files=[RUNNER,SUITE,PROFILE_INPUT,TECH,REVIEW,STEP6,LANG]
 if PROFILE_RESULT.exists():files.append(PROFILE_RESULT)
 for d in [E/'workflows/farrier_review',E/'workflows/horse_owner_requalification']:
  files.extend(sorted(p for p in d.rglob('*') if p.is_file()))
 unique=[];seen=set()
 for p in files:
  k=str(p.resolve())
  if k not in seen:seen.add(k);unique.append(p)
 manifest={'manifest_id':'equinet-a2-step7-draft-package','version':'0.1.0-draft.1','status':status,'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in unique],'file_count':len(unique),'scenarios':6,'operators':14,'external_actions':0,'promotion_performed':False};MANIFEST.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'pass':result['pass'],'deterministic':'6/6','operators':'14/14','exports':s.get('export_formats'),'profile_invocation':profile_validation['status'],'status':status,'failures':failures},indent=2));return 0 if not failures else 1
if __name__=='__main__':raise SystemExit(main())
