#!/usr/bin/env python3
"""Run Step 11 local website-first acceptance without live provider or CRM writes."""
from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from a2_twenty_fullenrich_common import env_value
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'evaluations/step11/acceptance-summary.json'
def run(script):
 p=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,capture_output=True,text=True,timeout=300);return {'script':script,'returncode':p.returncode,'stdout_tail':p.stdout[-3000:],'stderr_tail':p.stderr[-3000:]}
def main():
 scripts=['scripts/run_step11_preflight_tests.py','scripts/run_step11_firecrawl_tests.py','scripts/run_step11_apify_facebook_tests.py','scripts/run_step11_company_merge_tests.py','scripts/run_step11_website_people_tests.py','scripts/run_step11_quillin_extraction_acceptance.py','scripts/run_step11_synthetic_acceptance.py','scripts/run_step11_contract_tests.py','scripts/run_step10_unit_tests.py','scripts/run_step10_connector_integration_tests.py','scripts/run_step10_synthetic_acceptance.py','scripts/run_step10_contract_validation.py','scripts/run_step10_staged_search_tests.py']
 results=[]
 for script in scripts:
  if not (ROOT/script).is_file():results.append({'script':script,'returncode':1,'stderr_tail':'missing test script','stdout_tail':''})
  else:results.append(run(script))
 mapping_path=ROOT/'evaluations/step11/live-read/twenty-website-mapping.json';mapping=json.loads(mapping_path.read_text()) if mapping_path.is_file() else {};mapping_valid=mapping.get('status')=='valid' and mapping.get('external_writes')==0
 passed=all(x['returncode']==0 for x in results) and mapping_valid
 summary={'suite':'step11_website_first_local_acceptance','status':'pass' if passed else 'fail','checks':results,'checks_passed':sum(x['returncode']==0 for x in results),'checks_total':len(results),'twenty_mapping_validated':mapping_valid,'firecrawl_key_resolved':bool(env_value('FIRECRAWL_API_KEY')),'apify_key_resolved':bool(env_value('APIFY_API_KEY') or env_value('APIFY_TOKEN')),'live_firecrawl_calls':0,'live_apify_calls':0,'live_twenty_writes':0,'activation_ready':False,'remaining_gates':['Firecrawl live authentication and positive-result acceptance','Apify live authentication, account/build/rights/financial controls and positive-result acceptance','Twenty Company composite write/readback live acceptance','website Person FullEnrich positive-result acceptance','full end-to-end human review']};OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({'status':summary['status'],'checks_passed':summary['checks_passed'],'checks_total':summary['checks_total'],'twenty_mapping_validated':mapping_valid,'credentials_resolved':summary['firecrawl_key_resolved'] and summary['apify_key_resolved'],'output':str(OUT)},indent=2));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
