#!/usr/bin/env python3
"""Build the non-active Step 10 implementation manifest."""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 include=[]
 fixed=['deliverables/A2-TWENTY-FULLENRICH-IMPLEMENTATION-PLAN.md','deliverables/A2-STEP10-IMPLEMENTATION-REPORT.md','evaluations/step10/synthetic-acceptance.json','evaluations/step10/acceptance-summary.json','evaluations/step10/contract-validation.json','evaluations/step10/live-read/twenty-mapping-validation.json','evaluations/step10/live-fullenrich/account-preflight.json','foundations/decisions/A2-FULLENRICH-CREDIT-CAPS-20260915.json','foundations/decisions/A2-ROLE-STATUS-SEMANTICS-20260915.json','foundations/decisions/A2-STAGED-PEOPLE-SEARCH-20260917.json','foundations/decisions/A2-LINKED-SECONDARY-FALLBACK-20260917.json','foundations/contracts/governance/a2-provider-and-cost-policy-0.4.0.json','foundations/contracts/integrations/schemas/a2-fullenrich-search-batch-0.1.1.schema.json','foundations/contracts/integrations/schemas/a2-person-selection-decisions-0.1.2.schema.json','foundations/contracts/integrations/schemas/a2-write-proposal-0.1.2.schema.json','scripts/run_step10_staged_search_tests.py','scripts/a2_fullenrich_budget.py','scripts/fullenrich_credit_status.py']
 include.extend(ROOT/x for x in fixed)
 for folder,patterns in [('foundations/contracts',['**/*0.4.0-rc.1.json','integrations/a2-fullenrich-direct-integration-0.1.2.json','twenty/a2-twenty-operational-mapping-0.1.1.json','runtime/a2-twenty-fullenrich-state-model-0.1.3.json','integrations/schemas/a2-*.json']),('scripts',['*step10*.py','*twenty*fullenrich*.py','pull_twenty_companies.py','push_twenty_enrichment.py','fullenrich_*.py','classify_a2_target_role_v2.py','build_fullenrich_action_requests.py','build_lookup_decision_packet.py','validate_lookup_decisions.py','build_search_candidate_packet.py','build_linked_secondary_fallback_packet.py','validate_person_selection_decisions.py','build_selected_contact_batch.py','build_twenty_enrichment_write_plan.py','validate_twenty_reconciliation.py','manage_a2_enrichment_run.py','validate_a2_integration_artifact.py','validate_twenty_operational_mapping.py'])]:
  for pat in patterns:include.extend((ROOT/folder).glob(pat))
 
 for skill_dir in (ROOT/'skills/equinet-a2').glob('a2-*'):
  if skill_dir.name in {'a2-twenty-fullenrich-enrichment','a2-twenty-fullenrich-workflow','a2-twenty-connector','a2-fullenrich-connector','a2-contact-resolution-and-selection','a2-twenty-write-governance'}:
   include.extend(p for p in skill_dir.rglob('*') if p.is_file())
 paths=sorted({p.resolve() for p in include if p.is_file() and p.name!='a2-step10-implementation-manifest-0.1.0.json'})
 artifacts=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths]
 active=json.loads((ROOT/'foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json').read_text());drift=[]
 for item in active.get('active_files',[]):
  p=ROOT/item['path']
  if p.is_file() and sha(p)!=item.get('sha256'):drift.append({'path':item['path'],'expected':item.get('sha256'),'actual':sha(p)})
 acceptance=json.loads((ROOT/'evaluations/step10/acceptance-summary.json').read_text())
 result={'manifest_id':'equinet-a2-step10-twenty-fullenrich-implementation','version':'0.1.0','status':'implemented_local_and_twenty_read_validated_fullenrich_live_pending','generated_at':datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z'),'activation':False,'active_foundation_observed_version':active.get('version'),'artifacts':artifacts,'artifact_count':len(artifacts),'acceptance':{'status':acceptance.get('status'),'twenty_live_read_validated':acceptance.get('twenty_live_read_validated'),'twenty_live_writes_executed':0,'fullenrich_live_calls_executed':0,'fullenrich_api_key_available':acceptance.get('fullenrich_api_key_available')},'active_manifest_hash_drift':drift,'remaining_gates':acceptance.get('remaining_gates'),'external_writes':0,'hubspot_actions':0,'outreach_actions':0}
 out=ROOT/'foundations/contracts/runtime/a2-step10-implementation-manifest-0.1.0.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'artifact_count':len(artifacts),'active_manifest_drift':len(drift),'output':str(out)},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
