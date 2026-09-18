#!/usr/bin/env python3
"""Run the deterministic Twenty–FullEnrich workflow acceptance suite."""
from __future__ import annotations
import json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];F=ROOT/'evaluations/step10/fixtures';W=ROOT/'evaluations/step10/work';PY=sys.executable
def run(*args,expect=0):
 p=subprocess.run([PY,*map(str,args)],cwd=ROOT,capture_output=True,text=True)
 if p.returncode!=expect:raise RuntimeError(f"command failed {args}: rc={p.returncode}\nstdout={p.stdout}\nstderr={p.stderr}")
 return p
def load(name):return json.loads((W/name).read_text(encoding='utf-8'))
def main():
 if W.exists():shutil.rmtree(W)
 W.mkdir(parents=True)
 checks=[]
 def step(name,*args,expect=0):
  run(*args,expect=expect);checks.append(name)
 step('ledger_start','scripts/manage_a2_enrichment_run.py','start','--run-id','STEP10-SYN-001','--ledger',W/'run.json','--company-ids','11111111-1111-4111-8111-111111111111')
 step('pull_fixture','scripts/pull_twenty_companies.py','--run-id','STEP10-SYN-001','--batch-size','1','--include-null','--claim','--fixture',F/'twenty-companies.json','--output',W/'companies.json')
 step('company_schema','scripts/validate_a2_integration_artifact.py','foundations/contracts/integrations/schemas/a2-company-batch.schema.json',W/'companies.json')
 step('lookup_fixture','scripts/fullenrich_people_lookup.py',F/'lookup-requests.json','--fixture',F/'lookup-provider.json','--output',W/'lookups.json')
 step('lookup_packet','scripts/build_lookup_decision_packet.py',W/'companies.json',W/'lookups.json','--output',W/'lookup-packet.json')
 step('lookup_decisions','scripts/validate_lookup_decisions.py',W/'lookup-packet.json',F/'lookup-decisions.json','--output',W/'lookup-validation.json')
 step('search_fixture','scripts/fullenrich_people_search.py',F/'search-requests.json','--fixture',F/'search-provider.json','--output',W/'search.json')
 step('search_packet','scripts/build_search_candidate_packet.py',W/'companies.json',W/'search.json','--output',W/'search-packet.json')
 step('selection_decisions','scripts/validate_person_selection_decisions.py',W/'search-packet.json',F/'selection-decisions.json','--output',W/'selection-validation.json')
 step('contact_fixture','scripts/fullenrich_contact_enrichment.py',F/'selected-people.json','--fixture',F/'contact-provider.json','--output',W/'contacts.json')
 step('write_plan','scripts/build_twenty_enrichment_write_plan.py',F/'write-proposal.json','--output',W/'write-plan.json')
 step('write_plan_schema','scripts/validate_a2_integration_artifact.py','foundations/contracts/integrations/schemas/a2-twenty-write-plan.schema.json',W/'write-plan.json')
 step('write_dry_run','scripts/push_twenty_enrichment.py',W/'write-plan.json','--output',W/'write-dry-run.json')
 step('ledger_advance','scripts/manage_a2_enrichment_run.py','advance','--ledger',W/'run.json','--stage','write_plan_validated','--artifact',W/'write-plan.json')
 step('ledger_schema','scripts/validate_a2_integration_artifact.py','foundations/contracts/integrations/schemas/a2-run-ledger.schema.json',W/'run.json')
 companies=load('companies.json');lookups=load('lookups.json');search=load('search.json');contacts=load('contacts.json');plan=load('write-plan.json');dry=load('write-dry-run.json') if (W/'write-dry-run.json').exists() else {}
 assertions={
  'one_company':companies.get('company_count')==1,
  'zero_external_twenty_writes':companies.get('external_writes')==0,
  'lookup_secondary_found':lookups['results'][0]['person']['exact_current_role']=='Trainer',
  'two_search_candidates':len(search['results'][0]['candidates'])==2,
  'two_contacts':len(contacts.get('results',[]))==2,
  'personal_email_not_requested':contacts.get('personal_email_requested') is False,
  'five_write_operations':len(plan.get('operations',[]))==5,
  'final_company_status_last':plan['operations'][-1]['operation_type']=='update_company_status',
  'dry_run_no_writes':dry.get('external_writes')==0 and dry.get('status')=='dry_run'
 }
 result={'suite':'step10_twenty_fullenrich_synthetic_acceptance','status':'pass' if all(assertions.values()) else 'fail','checks_run':checks,'assertions':assertions,'external_calls':0,'external_writes':0,'failures':[k for k,v in assertions.items() if not v]}
 (ROOT/'evaluations/step10/synthetic-acceptance.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2));return 0 if result['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
