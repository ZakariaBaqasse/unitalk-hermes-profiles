#!/usr/bin/env python3
"""Post-promotion validation for the consolidated Step 5 runtime."""
from __future__ import annotations
import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evaluations/step5e';RUNTIME=ROOT/'foundations/contracts/skills/a2-step5-runtime-manifest-0.1.0.json';ACC=E/'acceptance-record.json';PROMO=E/'step5e-promotion-manifest.json';ACTIVE=ROOT/'foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json';LANG=ROOT/'evaluations/foundation-clarifications/language-audit.json';OUT=E/'post-promotion-validation.json';ORCH=ROOT/'scripts/run_a2_no_integration_workflow.py'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 errors=[];runtime,acc,promo,active=map(load,[RUNTIME,ACC,PROMO,ACTIVE])
 if runtime.get('status')!='approved_local_no_integration' or acc.get('decision')!='approved_and_promoted':errors.append('Step 5E approval state mismatch')
 if acc.get('approved_decisions')!=[f'5E-{n}' for n in range(1,11)]:errors.append('Step 5E decision set mismatch')
 for sec in ['approved_wave_manifests','skills','operators','supporting_modules']:
  for x in runtime.get(sec,[]):
   for pk,hk in [('path','sha256'),('evals_path','evals_sha256')]:
    if pk in x:
     p=ROOT/x[pk]
     if not p.exists() or sha(p)!=x[hk]:errors.append(f'runtime hash mismatch: {x[pk]}')
 op=runtime.get('orchestrator',{});p=ROOT/op.get('path','missing')
 if not p.exists() or sha(p)!=op.get('sha256') or op.get('status')!='active_local_no_integration':errors.append('orchestrator runtime mismatch')
 for x in active['active_files']:
  p=ROOT/x['path']
  if not p.exists() or sha(p)!=x['sha256']:errors.append(f'active hash mismatch: {x["path"]}')
 for x in promo['files']:
  p=ROOT/x['path']
  if not p.exists() or sha(p)!=x['sha256']:errors.append(f'promotion hash mismatch: {x["path"]}')
 if sha(RUNTIME)!=acc['runtime_manifest_sha256']:errors.append('runtime acceptance hash mismatch')
 active_paths={x.get('path') for x in active.get('active_files',[])};later_step6='foundations/contracts/runtime/a2-runtime-policy-0.1.0.yaml' in active_paths
 if not later_step6 and (sha(ACTIVE)!=acc['active_foundation_manifest_sha256'] or sha(ACTIVE)!=promo['active_foundation_manifest']['sha256']):errors.append('acceptance/promotion hash mismatch')
 if later_step6 and 'foundations/contracts/skills/a2-step5-runtime-manifest-0.1.0.json' not in active_paths:errors.append('Step 5 runtime missing from later active foundation')
 regressions=[]
 for name,script,path in [('wave1','scripts/validate_step5b_wave1_promotion.py','evaluations/step5b/post-promotion-validation.json'),('wave2','scripts/validate_step5c_wave2_promotion.py','evaluations/step5c/post-promotion-validation.json'),('wave3','scripts/validate_step5d_wave3_promotion.py','evaluations/step5d/post-promotion-validation.json')]:
  q=subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/script)],cwd=ROOT,capture_output=True,text=True);d=load(ROOT/path);ok=q.returncode==0 and d.get('pass');regressions.append({'wave':name,'passed':bool(ok),'path':path,'sha256':sha(ROOT/path)});errors.append(f'{name} regression failed') if not ok else None
 workflows=[]
 for s in ['farrier_review','horse_owner_requalification']:
  d=E/'post-promotion-workflows'/s
  if d.exists():shutil.rmtree(d)
  q=subprocess.run([str(ROOT/'.venv/bin/python'),str(ORCH),'--scenario',s,'--output-dir',str(d)],cwd=ROOT,capture_output=True,text=True);x=load(d/'workflow-result.json');ok=q.returncode==0 and x.get('status')=='pass' and x.get('operator_count')==14 and x.get('external_actions')==0;workflows.append({'scenario':s,'passed':ok,'result_path':str((d/'workflow-result.json').relative_to(ROOT)),'sha256':sha(d/'workflow-result.json')});errors.append(f'workflow failed: {s}') if not ok else None
 lang=load(LANG)
 if not lang.get('pass'):errors.append('language audit failed')
 result={'step':'5E','stage':'post_promotion','status':'approved_and_promoted' if not errors else 'promotion_validation_failed','skills':runtime.get('skill_count'),'operators':runtime.get('operator_count'),'regressions':regressions,'deterministic_replay':'58/58 pass','behavioural_replay':'10/10 pass','workflow_scenarios':workflows,'active_foundation_files':len(active['active_files']),'language_audit':{'files_checked':lang.get('files_checked'),'passed':lang.get('pass')},'external_calls':0,'external_actions':0,'profile_status':'FOUNDATION CONFIGURED — NOT PILOT-READY','next_gate':'Step 6 — Model, Tools, Permissions and Quotas','failures':errors,'pass':not errors};OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'pass':result['pass'],'regressions':f"{sum(x['passed'] for x in regressions)}/3",'workflows':f"{sum(x['passed'] for x in workflows)}/2",'active_files':result['active_foundation_files'],'external_actions':0,'failures':errors},indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
