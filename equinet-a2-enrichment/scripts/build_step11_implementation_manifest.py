#!/usr/bin/env python3
"""Build the Step 11 website-first implementation manifest."""
from __future__ import annotations
import hashlib,json,py_compile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'foundations/contracts/runtime/a2-step11-implementation-manifest-0.1.0.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 fixed=[
 'deliverables/A2-WEBSITE-FIRST-ENRICHMENT-IMPLEMENTATION-PLAN.md','deliverables/A2-STEP11-WEBSITE-FIRST-IMPLEMENTATION-REPORT.md',
 'foundations/decisions/A2-WEBSITE-FIRST-FIRECRAWL-FACEBOOK-20260918.json','foundations/contracts/integrations/a2-official-website-firecrawl-integration-0.1.0.json','foundations/contracts/integrations/a2-apify-facebook-page-contact-integration-0.1.0.json','foundations/contracts/sources/a2-source-register-0.3.2.json','foundations/contracts/sources/a2-source-register-0.3.2.csv','foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.3.2.json','foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.3.2.json','foundations/contracts/governance/a2-provider-and-cost-policy-0.5.0.json','foundations/contracts/twenty/a2-twenty-operational-mapping-0.1.2.json','foundations/contracts/runtime/a2-twenty-fullenrich-state-model-0.1.4.json','foundations/contracts/runtime/a2-step11-runtime-policy-0.1.0-rc.1.json',
 'scripts/build_official_site_plan.py','scripts/firecrawl_official_site_fetch.py','scripts/extract_official_site_observations.py','scripts/build_website_decision_packet.py','scripts/validate_website_person_observation_proposals.py','scripts/validate_website_decisions.py','scripts/assemble_company_contact_merge_request.py','scripts/build_company_contact_merge_plan.py','scripts/build_apify_facebook_requests.py','scripts/apify_facebook_page_contact.py','scripts/validate_apify_facebook_results.py','scripts/build_website_people_contact_batch.py','scripts/preflight_step11_source_action.py','scripts/validate_step11_twenty_mapping.py','scripts/run_step11_firecrawl_tests.py','scripts/run_step11_apify_facebook_tests.py','scripts/run_step11_company_merge_tests.py','scripts/run_step11_website_people_tests.py','scripts/run_step11_preflight_tests.py','scripts/run_step11_contract_tests.py','scripts/run_step11_quillin_extraction_acceptance.py','scripts/run_step11_synthetic_acceptance.py','scripts/run_step11_all_acceptance.py',
 'skills/equinet-a2/a2-official-site-and-facebook-enrichment/SKILL.md','skills/equinet-a2/a2-official-site-and-facebook-enrichment/references/runbook.md','evaluations/step11/fixtures/firecrawl/quillin-about-fetch.json','evaluations/step11/quillin-person-extraction-acceptance.json','evaluations/step11/synthetic-acceptance.json','evaluations/step11/acceptance-summary.json','evaluations/step11/live-read/twenty-website-mapping.json','evaluations/step11/live-read/provider-credential-validation.json']
 fixed += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'foundations/contracts/integrations/schemas').glob('a2-*0.1.*.schema.json')) if any(x in p.name for x in ['official-site','firecrawl','website','company-contact','apify-facebook','write-proposal-0.1.3'])]
 fixed += ['scripts/a2_twenty_fullenrich_common.py','scripts/pull_twenty_companies.py','scripts/build_twenty_enrichment_write_plan.py','scripts/push_twenty_enrichment.py','scripts/fullenrich_contact_enrichment.py','scripts/manage_a2_enrichment_run.py']
 paths=[]
 for rel in fixed:
  if rel not in paths:paths.append(rel)
 missing=[x for x in paths if not (ROOT/x).is_file()];artifacts=[];compile_errors=[]
 for rel in paths:
  p=ROOT/rel
  if not p.is_file():continue
  artifacts.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p)})
  if p.suffix=='.py':
   try:py_compile.compile(str(p),doraise=True)
   except Exception as e:compile_errors.append(f'{rel}: {e}')
 active=json.loads((ROOT/'foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json').read_text());drift=[]
 for x in active.get('active_files',[]):
  p=ROOT/x['path']
  if not p.is_file() or sha(p)!=x['sha256']:drift.append(x['path'])
 acceptance_path=ROOT/'evaluations/step11/acceptance-summary.json';acceptance=json.loads(acceptance_path.read_text()) if acceptance_path.is_file() else {}
 status='implemented_local_live_acceptance_pending' if not missing and not compile_errors and acceptance.get('status')=='pass' else 'implementation_incomplete'
 out={'manifest_id':'equinet-a2-step11-implementation','version':'0.1.0','status':status,'generated_at':datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z'),'artifact_count':len(artifacts),'artifacts':artifacts,'missing':missing,'compile_errors':compile_errors,'acceptance':acceptance,'active_manifest_version':active.get('version'),'active_manifest_hash_drift':drift,'activation_ready':False,'activation_blocks':['Firecrawl positive-result candidate acceptance','Apify pinned build/rights/financial controls','Apify positive-result live acceptance','Twenty Company composite write/readback live acceptance','website Person FullEnrich live acceptance','full end-to-end review and approval']};OUT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':status,'artifact_count':len(artifacts),'missing':len(missing),'compile_errors':len(compile_errors),'active_manifest_drift':len(drift),'output':str(OUT)},indent=2));return 0 if status!='implementation_incomplete' else 1
if __name__=='__main__':raise SystemExit(main())
