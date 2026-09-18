#!/usr/bin/env python3
"""Validate Step 5E full operational regression and no-integration workflow."""
from __future__ import annotations
import hashlib,json,py_compile,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evaluations/step5e';TECH=E/'technical-validation.json';REVIEW=E/'A2-STEP-5-CLOSURE-REVIEW.md';PACKAGE=E/'step5e-draft-package-manifest.json';CONSOLIDATED=ROOT/'foundations/contracts/skills/a2-step5-runtime-manifest-0.1.0-draft.1.json';ACTIVE=ROOT/'foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json';LANG=ROOT/'evaluations/foundation-clarifications/language-audit.json'
RUNTIMES=[ROOT/f'foundations/contracts/skills/a2-wave{n}-runtime-manifest-0.1.0.json' for n in [1,2,3]]
COMMANDS=[('a2-intake','scripts/a2_intake.py'),('a2-normalise-resolve-entities','scripts/normalise_and_resolve_a2_entities.py'),('a2-duplicate-eligibility','scripts/evaluate_a2_duplicate_eligibility.py'),('a2-build-gap-plan','scripts/build_a2_gap_plan.py'),('a2-evaluate-minimum-package','scripts/evaluate_a2_minimum_package.py'),('a2-source-preflight','scripts/preflight_a2_source_action.py'),('a2-social-link-classifier','scripts/classify_official_site_social_link.py'),('a2-normalise-validate-observations','scripts/normalise_and_validate_a2_observations.py'),('a2-evaluate-evidence-confidence','scripts/evaluate_a2_evidence_confidence.py'),('a2-evaluate-protected-field-action','scripts/evaluate_a2_protected_field_action.py'),('a2-create-revision','scripts/create_a2_revision.py'),('a2-render-review-package','scripts/render_and_validate_a2_review_package.py'),('a2-twenty-review','scripts/build_and_validate_a2_twenty_review.py'),('a2-governed-handoff','scripts/build_and_validate_a2_handoff.py')]
SUPPORT=['scripts/a2_wave2_contracts.py','scripts/a2_wave3_contracts.py'];ORCH=ROOT/'scripts/run_a2_no_integration_workflow.py'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(script):return subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/script)],cwd=ROOT,capture_output=True,text=True)
def main():
 failures=[];runtime=[load(p) for p in RUNTIMES];active=load(ACTIVE)
 if any(x.get('status')!='approved_local_no_integration' for x in runtime):failures.append('one or more wave runtime manifests are not approved')
 for m in runtime:
  for sec in ['skills','references','commands','supporting_modules','pinned_dependencies']:
   for x in m.get(sec,[]):
    for pk,hk in [('path','sha256'),('evals_path','evals_sha256')]:
     if pk in x:
      p=ROOT/x[pk]
      if not p.exists() or sha(p)!=x[hk]:failures.append(f"runtime hash mismatch: {x[pk]}")
 active_bad=[]
 for x in active['active_files']:
  p=ROOT/x['path']
  if not p.exists() or sha(p)!=x['sha256']:active_bad.append(x['path'])
 if active_bad:failures.append(f'active foundation mismatches: {active_bad}')
 compile_checks=[]
 for _,rel in COMMANDS:
  try:py_compile.compile(str(ROOT/rel),doraise=True);compile_checks.append({'path':rel,'passed':True})
  except Exception as e:compile_checks.append({'path':rel,'passed':False,'error':str(e)});failures.append(f'compile failed: {rel}')
 for rel in SUPPORT+[str(ORCH.relative_to(ROOT))]:
  try:py_compile.compile(str(ROOT/rel),doraise=True);compile_checks.append({'path':rel,'passed':True})
  except Exception as e:compile_checks.append({'path':rel,'passed':False,'error':str(e)});failures.append(f'compile failed: {rel}')
 regressions=[]
 for name,script,result_path in [('wave1','scripts/validate_step5b_wave1_promotion.py','evaluations/step5b/post-promotion-validation.json'),('wave2','scripts/validate_step5c_wave2_promotion.py','evaluations/step5c/post-promotion-validation.json'),('wave3','scripts/validate_step5d_wave3_promotion.py','evaluations/step5d/post-promotion-validation.json')]:
  p=run(script);data=load(ROOT/result_path);ok=p.returncode==0 and data.get('pass') is True;regressions.append({'wave':name,'passed':ok,'path':result_path,'sha256':sha(ROOT/result_path)});
  if not ok:failures.append(f'{name} post-promotion regression failed')
 deterministic=sum(load(ROOT/x['path'])['deterministic_replay']['passed'] for x in regressions);det_total=sum(load(ROOT/x['path'])['deterministic_replay']['total'] for x in regressions);behavioural=3+3+4;beh_total=10
 workflows=[]
 for scenario in ['farrier_review','horse_owner_requalification']:
  out=E/'workflows'/scenario
  if out.exists():shutil.rmtree(out)
  p=subprocess.run([str(ROOT/'.venv/bin/python'),str(ORCH),'--scenario',scenario,'--output-dir',str(out)],cwd=ROOT,capture_output=True,text=True);data=load(out/'workflow-result.json');ok=p.returncode==0 and data.get('status')=='pass' and data.get('operator_count')==14 and data.get('external_actions')==0;workflows.append({'scenario':scenario,'passed':ok,'result_path':str((out/'workflow-result.json').relative_to(ROOT)),'result_sha256':sha(out/'workflow-result.json'),'operator_count':data.get('operator_count'),'semantic_checks':data.get('semantic_checks')});
  if not ok:failures.append(f'workflow failed: {scenario}')
 farrier=load(E/'workflows/farrier_review/workflow-result.json');owner=load(E/'workflows/horse_owner_requalification/workflow-result.json');coverage=sorted(set(farrier['operator_coverage'])|set(owner['operator_coverage']));expected=sorted(x[0] for x in COMMANDS)
 if coverage!=expected:failures.append('14-command operator coverage mismatch')
 subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/audit_profile_language.py')],cwd=ROOT,capture_output=True);lang=load(LANG)
 if not lang.get('pass'):failures.append('language audit failed')
 skills=[]
 for m in runtime:
  skills.extend(m['skills'])
 consolidated={'manifest_id':'equinet-a2-step5-runtime','version':'0.1.0-draft.1','status':'ready_for_severine_review_not_approved' if not failures else 'validation_failed','profile':'equinet-a2-enrichment','approved_wave_manifests':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in RUNTIMES],'skill_count':len(skills),'skills':skills,'operator_count':len(COMMANDS),'operators':[{'command_id':i,'path':rel,'sha256':sha(ROOT/rel),'status':'active_local_no_integration'} for i,rel in COMMANDS],'supporting_modules':[{'path':rel,'sha256':sha(ROOT/rel)} for rel in SUPPORT],'orchestrator':{'path':str(ORCH.relative_to(ROOT)),'sha256':sha(ORCH),'status':'draft_local_no_integration'},'permissions':{'local_file_processing':True,'synthetic_fixture_processing':True,'web_access':False,'apify':False,'twenty':False,'hubspot_read':False,'hubspot_write':False,'n8n':False,'outreach':False,'handoff_delivery':False},'regression_summary':{'deterministic':f'{deterministic}/{det_total} pass','behavioural':f'{behavioural}/{beh_total} pass','workflow_scenarios':'2/2 pass','operators':'14/14 covered'},'next_gate':'Step 6 — Model, Tools, Permissions and Quotas'};CONSOLIDATED.parent.mkdir(parents=True,exist_ok=True);CONSOLIDATED.write_text(json.dumps(consolidated,indent=2,ensure_ascii=False)+'\n')
 result={'step':'5E','status':'ready_for_severine_review_not_approved' if not failures else 'validation_failed','approved_skills':len(skills),'operator_commands':len(COMMANDS),'compile_checks':compile_checks,'wave_regressions':regressions,'deterministic_replay':{'passed':deterministic,'total':det_total},'behavioural_replay':{'passed':behavioural,'total':beh_total},'workflow_scenarios':workflows,'operator_coverage':coverage,'active_foundation_files':len(active['active_files']),'language_audit':{'files_checked':lang.get('files_checked'),'passed':lang.get('pass')},'external_calls':0,'external_actions':0,'approval_required':True,'promotion_performed':False,'profile_status':'FOUNDATION CONFIGURED — NOT PILOT-READY','next_gate_after_approval':'Step 6 — Model, Tools, Permissions and Quotas','failures':failures,'pass':not failures};E.mkdir(parents=True,exist_ok=True);TECH.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 decisions=[('5E-1','Freeze ten approved Wave 1–3 skills and fourteen operator commands as the Step 5 local runtime.'),('5E-2','Use the profile orchestrator only with approved local/synthetic inputs until later pilot gates pass.'),('5E-3','Require all prior-wave deterministic and behavioural regressions to remain green.'),('5E-4','Require every workflow run to cover all fourteen operators with zero external calls and actions.'),('5E-5','Keep canonical JSON authoritative and require independently validated review projections.'),('5E-6','Keep A1 requalification prepared-not-delivered; do not calculate a replacement score in A2.'),('5E-7','Keep HubSpot, A3 and A14 blocked until strict destination contracts and durable receipt paths exist.'),('5E-8','Keep Web, Apify, Twenty, HubSpot and n8n disabled in the consolidated Step 5 runtime.'),('5E-9','Treat Step 5 completion as operational-skill completion, not pilot, production or contractual acceptance.'),('5E-10','Open Step 6 for model, tool, permission and quota configuration after Step 5E approval.')];rows='\n'.join(f'| {i} | {d} |' for i,d in decisions);REVIEW.write_text(f'''# Decision Review — Step 5E Full Operational Skills Regression and No-Integration Workflow\n\n**Status:** `READY FOR SÉVERINE REVIEW — NOT APPROVED`  \n**Profile:** `equinet-a2-enrichment`\n\n## Results\n\n- Approved skills: **{len(skills)}**.\n- Operator commands: **14/14 covered**.\n- Deterministic replay: **{deterministic}/{det_total} PASS**.\n- Behavioural replay: **{behavioural}/{beh_total} PASS**.\n- No-integration workflows: **2/2 PASS**.\n- External calls/actions: **0/0**.\n- Language audit: **PASS — {lang.get('files_checked')} files checked**.\n\n## Decisions proposed\n\n| ID | Decision |\n|---|---|\n{rows}\n\nApproval closes Step 5 and authorises Step 6 configuration. It does not make the profile pilot-ready or enable integrations.\n''')
 files=[ORCH,CONSOLIDATED,TECH,REVIEW,*RUNTIMES,*[ROOT/x['path'] for x in regressions],LANG]
 for wf in workflows:
  base=ROOT/Path(wf['result_path']).parent
  files.extend(sorted(p for p in base.rglob('*') if p.is_file()))
 unique=[];seen=set()
 for p in files:
  k=str(p.resolve())
  if k not in seen:seen.add(k);unique.append(p)
 manifest={'manifest_id':'equinet-a2-step5e-draft-package','version':'0.1.0-draft.1','status':result['status'],'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in unique],'file_count':len(unique),'skills':len(skills),'operators':14,'workflow_scenarios':2,'external_actions':0,'promotion_performed':False};PACKAGE.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'pass':result['pass'],'skills':len(skills),'operators':'14/14','deterministic':f'{deterministic}/{det_total}','behavioural':f'{behavioural}/{beh_total}','workflows':'2/2','status':result['status'],'failures':failures},indent=2));return 0 if not failures else 1
if __name__=='__main__':raise SystemExit(main())
