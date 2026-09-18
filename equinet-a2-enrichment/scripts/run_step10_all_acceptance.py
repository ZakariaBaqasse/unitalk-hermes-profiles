#!/usr/bin/env python3
"""Run all Step 10 checks, using live reads when credentials are available and preserved receipts otherwise."""
from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'evaluations/step10/acceptance-summary.json'
def run(args,env=None):
 p=subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,capture_output=True,text=True,timeout=240,env=env);return {'command':[str(x) for x in args],'returncode':p.returncode,'stdout_tail':p.stdout[-3000:],'stderr_tail':p.stderr[-3000:]}
def receipt_check(name,path,valid):
 return {'command':['preserved_receipt',name,str(path.relative_to(ROOT))],'returncode':0 if valid else 1,'stdout_tail':json.dumps({'valid':valid}),'stderr_tail':'' if valid else 'preserved receipt missing or invalid'}
def main():
 env=os.environ.copy();results=[]
 for script in ['run_step10_unit_tests.py','run_step10_twenty_filter_tests.py','run_step10_staged_search_tests.py','run_step10_budget_tests.py','run_step10_connector_integration_tests.py','run_step10_synthetic_acceptance.py','run_step10_contract_validation.py']:
  results.append(run([f'scripts/{script}']))
 twenty_credentials=bool(env.get('TWENTY_BASE_URL') and env.get('TWENTY_API_KEY'));current_live_read=False
 if twenty_credentials:
  results.append(run(['scripts/validate_twenty_operational_mapping.py','--output','evaluations/step10/live-read/twenty-mapping-validation.json'],env));results.append(run(['scripts/pull_twenty_companies.py','--run-id','STEP10-ACCEPTANCE-READ','--batch-size','2','--include-null','--output','evaluations/step10/live-read/acceptance-companies.json'],env));current_live_read=results[-1]['returncode']==0 and results[-2]['returncode']==0
 else:
  mapping_path=ROOT/'evaluations/step10/live-read/twenty-mapping-validation.json';mapping=json.loads(mapping_path.read_text()) if mapping_path.is_file() else {};live_runs=sorted((ROOT/'evaluations/step10/runs').glob('A2-LIVE-*/run-summary.json'));live=json.loads(live_runs[-1].read_text()) if live_runs else {};mapping_ok=mapping.get('status')=='valid' and mapping.get('external_calls')==1;run_ok=bool(live) and all(c.get('twenty_reconciled') is True for c in live.get('companies',[]));results.append(receipt_check('twenty_mapping',mapping_path,mapping_ok));results.append(receipt_check('twenty_live_run',live_runs[-1] if live_runs else ROOT/'missing',run_ok))
 preflight_path=ROOT/'evaluations/step10/live-fullenrich/account-preflight.json';preflight=json.loads(preflight_path.read_text()) if preflight_path.is_file() else {};account_verified=preflight.get('key_verified') is True and isinstance(preflight.get('credits_available'),(int,float)) and preflight.get('credits_available')>=0
 passed=all(x['returncode']==0 for x in results);live_runs=sorted((ROOT/'evaluations/step10/runs').glob('A2-LIVE-*/run-summary.json'));live=json.loads(live_runs[-1].read_text()) if live_runs else {};search_passed=bool(live) and all(all(q.get('status')=='not_found' for q in c.get('searches',[])) for c in live.get('companies',[]));twenty_status_reconciled=bool(live) and all(c.get('twenty_reconciled') is True for c in live.get('companies',[]))
 remaining=['FullEnrich live Lookup and Contact Enrichment acceptance','positive-result FullEnrich actual-rate confirmation','live Twenty Person create/association reconciliation','pilot reviewer approval for broader processing']
 if not search_passed:remaining.insert(0,'FullEnrich live Search acceptance')
 if not twenty_status_reconciled:remaining.append('Twenty Company status write/read-back acceptance')
 if not account_verified:remaining[:0]=['FullEnrich live key verification and credit balance']
 summary={'suite':'step10_implementation_acceptance','status':'pass_with_live_fullenrich_pending' if passed else 'fail','checks':results,'twenty_live_read_validated':current_live_read or (not twenty_credentials and results[-1]['returncode']==0 and results[-2]['returncode']==0),'twenty_live_read_current_session':current_live_read,'twenty_credentials_available_current_session':twenty_credentials,'twenty_live_writes_executed':0,'fullenrich_live_calls_executed':0,'fullenrich_api_key_available_current_session':bool(env.get('FULLENRICH_API_KEY')),'fullenrich_account_verified':account_verified,'fullenrich_credits_available':preflight.get('credits_available') if account_verified else None,'synthetic_external_actions':0,'remaining_gates':remaining}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({'status':summary['status'],'checks_passed':sum(x['returncode']==0 for x in results),'checks_total':len(results),'twenty_live_read_validated':summary['twenty_live_read_validated'],'twenty_live_read_current_session':current_live_read,'fullenrich_api_key_available_current_session':summary['fullenrich_api_key_available_current_session'],'output':str(OUT)},indent=2));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
