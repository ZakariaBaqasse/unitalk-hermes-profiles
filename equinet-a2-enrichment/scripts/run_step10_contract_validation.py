#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];W=ROOT/'evaluations/step10/work';F=ROOT/'evaluations/step10/fixtures';S=ROOT/'foundations/contracts/integrations/schemas'
pairs=[('a2-company-batch.schema.json',W/'companies.json'),('a2-fullenrich-lookup-batch.schema.json',F/'lookup-requests.json'),('a2-lookup-decisions-0.1.2.schema.json',F/'lookup-decisions.json'),('a2-fullenrich-search-batch-0.1.1.schema.json',F/'search-requests.json'),('a2-person-selection-decisions-0.1.2.schema.json',F/'selection-decisions.json'),('a2-selected-contact-batch.schema.json',W/'generated-selected.json'),('a2-fullenrich-contact-results.schema.json',W/'contacts.json'),('a2-write-proposal-0.1.2.schema.json',F/'write-proposal.json'),('a2-twenty-write-plan.schema.json',W/'write-plan.json'),('a2-run-ledger.schema.json',W/'run.json'),('a2-twenty-mapping-validation.schema.json',ROOT/'evaluations/step10/live-read/twenty-mapping-validation.json')]
def main():
 # generated-selected may have been cleared by workflow; rebuild deterministically
 if not (W/'generated-selected.json').exists():
  p=subprocess.run([sys.executable,'scripts/build_selected_contact_batch.py','--lookup-packet',str(W/'lookup-packet.json'),'--lookup-decisions',str(W/'lookup-validation.json'),'--search-packet',str(W/'search-packet.json'),'--selection-decisions',str(W/'selection-validation.json'),'--run-id','STEP10-SYN-001','--output',str(W/'generated-selected.json')],cwd=ROOT,capture_output=True,text=True)
  if p.returncode:print(p.stdout,p.stderr);return 1
 results=[]
 for schema,artifact in pairs:
  p=subprocess.run([sys.executable,'scripts/validate_a2_integration_artifact.py',str(S/schema),str(artifact)],cwd=ROOT,capture_output=True,text=True)
  results.append({'schema':schema,'artifact':str(artifact.relative_to(ROOT)),'passed':p.returncode==0,'output':p.stdout[-500:]})
 out={'suite':'step10_contract_validation','status':'pass' if all(x['passed'] for x in results) else 'fail','passed':sum(x['passed'] for x in results),'total':len(results),'results':results};(ROOT/'evaluations/step10/contract-validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'passed':out['passed'],'total':out['total']},indent=2));return 0 if out['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
