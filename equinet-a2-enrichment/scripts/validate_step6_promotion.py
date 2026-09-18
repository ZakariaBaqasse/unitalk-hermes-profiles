#!/usr/bin/env python3
"""Post-promotion validation for Step 6 synthetic-local runtime configuration."""
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evaluations/step6';CONFIG=ROOT/'config.yaml';POLICY=ROOT/'foundations/contracts/runtime/a2-runtime-policy-0.1.0.yaml';ACC=E/'acceptance-record.json';PROMO=E/'step6-promotion-manifest.json';ACTIVE=ROOT/'foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json';PRIMARY=E/'gateway-smoke/primary-validation.json';LANG=ROOT/'evaluations/foundation-clarifications/language-audit.json';OUT=E/'post-promotion-validation.json'
def j(p):return json.loads(p.read_text(encoding='utf-8'))
def y(p):return yaml.safe_load(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 errors=[];c=y(CONFIG);p=y(POLICY);a=j(ACC);pr=j(PROMO);active=j(ACTIVE);pv=j(PRIMARY);active_paths={x.get('path') for x in active.get('active_files',[])};later_step8='foundations/contracts/runtime/a2-step8-pilot-runtime-policy-0.1.0.yaml' in active_paths
 if p.get('status')!='approved_for_synthetic_local_testing_gateway_telemetry_pending' or a.get('decision')!='approved_for_synthetic_local_testing':errors.append('Step 6 approval state mismatch')
 if a.get('approved_decisions')!=[*[f'S6-{n}' for n in range(1,10)],'S6-10-revised']:errors.append('Step 6 decision set mismatch')
 if c.get('model',{}).get('default')!='deepseek-v4-flash':errors.append('primary model configuration mismatch')
 if later_step8:
  if c.get('fallback_providers')!=[] or c.get('web')!={'search_backend':'exa','extract_backend':'firecrawl'}:errors.append('Step 8 pilot config mismatch')
 elif c.get('fallback_providers')!=[{'provider':'openai-api','model':'Gemini 3.7 Flash'}]:errors.append('Step 6 fallback configuration mismatch')
 if p['real_data_activation_gate']['current_status']!='blocked_pending_gateway_telemetry_fallback_and_governance' or p['real_data_activation_gate']['synthetic_local_testing_authorized'] is not True:errors.append('real-data gate mismatch')
 if p['model_routing']['primary']['real_mustad_data_authorized'] or p['model_routing']['fallback']['real_mustad_data_authorized']:errors.append('real-data model use is not blocked')
 if not (pv.get('routing_configuration_pass') and pv.get('session_response_observed') and pv.get('external_safety_pass') and pv.get('v2_validation',{}).get('business_contract_pass') and pv.get('v2_validation',{}).get('audit_pass')):errors.append('primary functional smoke evidence mismatch')
 if pv.get('gateway_route_verified') or pv.get('primary_smoke_accepted'):errors.append('unverified upstream route overstated')
 for x in active['active_files']:
  q=ROOT/x['path']
  if not q.exists() or sha(q)!=x['sha256']:errors.append(f'active hash mismatch: {x["path"]}')
 for x in pr['files']:
  q=ROOT/x['path']
  if later_step8 and x['path']=='config.yaml':continue
  if not q.exists() or sha(q)!=x['sha256']:errors.append(f'promotion hash mismatch: {x["path"]}')
 historical_config=E/'pre-promotion/config.yaml'
 if later_step8:
  if not historical_config.exists() or sha(historical_config)!=a['config_sha256'] or sha(POLICY)!=a['runtime_policy_sha256']:errors.append('historical Step 6 config/policy acceptance hash mismatch')
 elif sha(CONFIG)!=a['config_sha256'] or sha(POLICY)!=a['runtime_policy_sha256']:errors.append('config/policy acceptance hash mismatch')
 active_paths={x.get('path') for x in active.get('active_files',[])};later_step7='foundations/contracts/runtime/a2-step7-synthetic-acceptance-manifest-0.1.0.json' in active_paths
 if not later_step7 and (sha(ACTIVE)!=a['active_foundation_manifest_sha256'] or sha(ACTIVE)!=pr['active_foundation_manifest']['sha256']):errors.append('acceptance/promotion hash mismatch')
 if later_step7 and 'foundations/contracts/runtime/a2-runtime-policy-0.1.0.yaml' not in active_paths:errors.append('Step 6 runtime policy missing from later active foundation')
 q=subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/validate_step5e_promotion.py')],cwd=ROOT,capture_output=True,text=True);step5=j(ROOT/'evaluations/step5e/post-promotion-validation.json')
 if q.returncode!=0 or not step5.get('pass'):errors.append('Step 5 regression failed')
 lang=j(LANG)
 if not lang.get('pass'):errors.append('language audit failed')
 result={'step':'6','stage':'post_promotion','status':'approved_for_synthetic_local_testing' if not errors else 'promotion_validation_failed','primary_functional_smoke':'passed','primary_upstream_route':'telemetry_pending','fallback_route':'configured_not_tested','real_data_authorized':False,'step5_regression':step5.get('pass'),'active_foundation_files':len(active['active_files']),'language_audit':{'files_checked':lang.get('files_checked'),'passed':lang.get('pass')},'external_calls':0,'external_actions':0,'profile_status':'FOUNDATION CONFIGURED — NOT PILOT-READY','next_gate':'Step 7 — Synthetic End-to-End Acceptance','failures':errors,'pass':not errors};OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'pass':result['pass'],'primary_functional_smoke':result['primary_functional_smoke'],'primary_upstream_route':result['primary_upstream_route'],'fallback_route':result['fallback_route'],'real_data_authorized':False,'step5_regression':result['step5_regression'],'active_files':result['active_foundation_files'],'failures':errors},indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
