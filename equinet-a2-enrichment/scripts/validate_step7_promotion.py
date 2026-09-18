#!/usr/bin/env python3
"""Post-promotion validation for Step 7 synthetic acceptance."""
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evaluations/step7';FINAL=ROOT/'foundations/contracts/runtime/a2-step7-synthetic-acceptance-manifest-0.1.0.json';ACC=E/'acceptance-record.json';PROMO=E/'step7-promotion-manifest.json';ACTIVE=ROOT/'foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json';DET=E/'deterministic-acceptance.json';PROFILE=E/'profile-behavioural-result.json';LANG=ROOT/'evaluations/foundation-clarifications/language-audit.json';OUT=E/'post-promotion-validation.json'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 errors=[];m,a,p,active=map(load,[FINAL,ACC,PROMO,ACTIVE])
 if m.get('status')!='approved_synthetic_acceptance' or a.get('decision')!='approved_synthetic_acceptance':errors.append('Step 7 approval state mismatch')
 if a.get('approved_decisions')!=[f'S7-{n}' for n in range(1,11)]:errors.append('Step 7 decision set mismatch')
 for x in active['active_files']:
  q=ROOT/x['path']
  if not q.exists() or sha(q)!=x['sha256']:errors.append(f'active hash mismatch: {x["path"]}')
 for x in p['files']:
  q=ROOT/x['path']
  if not q.exists() or sha(q)!=x['sha256']:errors.append(f'promotion hash mismatch: {x["path"]}')
 if sha(FINAL)!=a['synthetic_acceptance_manifest_sha256']:errors.append('synthetic acceptance manifest hash mismatch')
 active_paths={x.get('path') for x in active.get('active_files',[])};later_step8='foundations/contracts/runtime/a2-step8-pilot-runtime-policy-0.1.0.yaml' in active_paths
 if not later_step8 and (sha(ACTIVE)!=a['active_foundation_manifest_sha256'] or sha(ACTIVE)!=p['active_foundation_manifest']['sha256']):errors.append('acceptance/promotion hash mismatch')
 if later_step8 and 'foundations/contracts/runtime/a2-step7-synthetic-acceptance-manifest-0.1.0.json' not in active_paths:errors.append('Step 7 manifest missing from later active foundation')
 d=load(DET)
 if not d.get('pass') or d.get('passed')!=6 or d.get('scenario_count')!=6 or d.get('external_actions')!=0:errors.append('Step 7 accepted deterministic package validation failed')
 pr=load(PROFILE);profile_checks={'profile':pr.get('profile')=='equinet-a2-enrichment','suite_pass':pr.get('suite_pass') is True,'scenarios':pr.get('scenarios')=='6/6','operators':pr.get('operators')=='14/14','exports':pr.get('exports')=={'markdown':2,'csv':12,'xlsx':2},'external_actions':pr.get('external_actions')==0,'identity':'hermes-agent' not in str(pr.get('actor','')).lower(),'usage':pr.get('model_usage')!='0' and pr.get('model_cost')!='0','deterministic_hash':pr.get('deterministic_acceptance_sha256')==sha(DET)}
 if not all(profile_checks.values()):errors.append('profile invocation replay linkage failed')
 q=subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/validate_step6_promotion.py')],cwd=ROOT,capture_output=True,text=True);s6=load(ROOT/'evaluations/step6/post-promotion-validation.json')
 if q.returncode!=0 or not s6.get('pass'):errors.append('Step 6/Step 5 regression failed')
 lang=load(LANG)
 if not lang.get('pass'):errors.append('language audit failed')
 result={'step':'7','stage':'post_promotion','status':'approved_synthetic_acceptance' if not errors else 'promotion_validation_failed','deterministic_replay':'6/6 pass','profile_invocation':{'passed':all(profile_checks.values()),'checks':profile_checks},'operator_coverage':'14/14','exports':{'markdown':2,'csv':12,'xlsx':2},'step6_regression':s6.get('pass'),'active_foundation_files':len(active['active_files']),'language_audit':{'files_checked':lang.get('files_checked'),'passed':lang.get('pass')},'external_calls':0,'external_actions':0,'real_data_authorized':False,'profile_status':'FOUNDATION CONFIGURED — NOT PILOT-READY','next_gate':'Step 8 — Bounded Real No-Integration Pilot Readiness','failures':errors,'pass':not errors};OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'pass':result['pass'],'deterministic':result['deterministic_replay'],'profile_invocation':result['profile_invocation']['passed'],'step6_regression':result['step6_regression'],'active_files':result['active_foundation_files'],'real_data_authorized':False,'failures':errors},indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
