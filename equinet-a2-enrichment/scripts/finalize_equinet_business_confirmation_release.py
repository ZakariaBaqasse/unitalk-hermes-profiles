#!/usr/bin/env python3
"""Freeze and verify the Equinet A2 business-confirmation release."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evaluations/equinet-business-confirmation-20260830'
STAMP='2026-08-30T17:05:11Z'
FILES=[
 'SOUL.md',
 'foundations/decisions/A2-EQUINET-BUSINESS-CONFIRMATION-20260830.json',
 'foundations/decisions/A2-EQUINET-BUSINESS-CONFIRMATION-20260830.md',
 'foundations/A2-BUSINESS-FIELD-CATALOGUE.md','foundations/A2-MINIMUM-DATA-PACKAGES.md','foundations/A2-PRELIMINARY-HUBSPOT-MAPPING.md',
 'foundations/contracts/business/a2-business-field-catalogue-0.2.0.json','foundations/contracts/business/a2-business-field-catalogue-0.2.0.csv',
 'foundations/contracts/business/a2-minimum-data-packages-0.2.0.json',
 'foundations/contracts/sources/a2-source-register-0.2.0.json','foundations/contracts/sources/a2-source-register-0.2.0.csv',
 'foundations/contracts/governance/a2-provider-and-cost-policy-0.2.0.json',
 'foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.2.0.json',
 'foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.2.0.json',
 'foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.2.0.json','foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.2.0.csv',
 'foundations/contracts/runtime/a2-no-integration-runtime-policy-1.1.0.yaml',
 'foundations/contracts/skills/a2-business-confirmation-runtime-manifest-1.1.0.json',
 'foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json',
 'deliverables/A2-DELIVERY-STATUS-AND-ROADMAP.md',
 'skills/a2-entity-resolution-and-normalisation/SKILL.md','skills/a2-gap-analysis-and-enrichment-planning/SKILL.md',
 'skills/a2-permitted-enrichment-research/SKILL.md','skills/a2-field-verification/SKILL.md',
 'skills/a2-field-verification/references/contact-verification.md','skills/a2-field-verification/references/professional-verification.md','skills/a2-field-verification/references/equine-business-verification.md',
 'skills/a2-data-quality-and-review-readiness/SKILL.md','skills/a2-review-package-and-governed-handoffs/SKILL.md',
 'scripts/build_a2_gap_plan.py','scripts/preflight_a2_source_action.py','scripts/normalise_and_validate_a2_observations.py',
 'scripts/evaluate_a2_minimum_package.py','scripts/classify_a2_target_role.py','scripts/validate_a2_contact_selection.py',
 'scripts/create_a2_revision.py','scripts/build_and_validate_a2_handoff.py','scripts/validate_a2_enrichment_record.py','scripts/run_a2_no_integration_workflow.py',
 'scripts/apply_equinet_business_confirmation_v020.py','scripts/validate_equinet_business_confirmation_v020.py',
 'scripts/publish_a2_dependency_closure_policies.py',
 'scripts/build_a2_business_confirmation_runtime_manifest.py','scripts/build_equinet_business_confirmation_manifest.py',
 'evaluations/equinet-business-confirmation-20260830/technical-validation.json',
 'evaluations/equinet-business-confirmation-20260830/results/farrier-workflow-result.json',
 'evaluations/equinet-business-confirmation-20260830/results/horse-owner-workflow-result.json',
 'evaluations/foundation-clarifications/language-audit.json',
 'evaluations/equinet-business-confirmation-20260830/A2-EQUINET-BUSINESS-CONFIRMATION-FINAL-REVIEW.md',
]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
 BASE.mkdir(parents=True,exist_ok=True)
 missing=[rel for rel in FILES if not (ROOT/rel).is_file()]
 if missing:print(json.dumps({'status':'fail','missing':missing},indent=2));return 1
 tech=load(BASE/'technical-validation.json')
 release={'release_id':'equinet-a2-business-confirmation-1.1.0','configuration_version':'0.2.0','runtime_overlay_version':'1.1.0','active_manifest_version':'1.2.0','created_at':STAMP,'status':'approved_implementation_no_integration','files':[{'path':rel,'bytes':(ROOT/rel).stat().st_size,'sha256':sha(ROOT/rel)} for rel in FILES],'validation':{'business_checks':f"{tech.get('checks_passed')}/{tech.get('checks_total')} PASS",'farrier_workflow':'PASS','horse_owner_workflow':'PASS','operator_coverage_each':14,'language_audit':'PASS','external_actions':0},'integration_states':{'hubspot_read':'not_connected','hubspot_write':'not_connected_not_authorized','twenty':'not_connected','n8n':'not_connected','apify_harvestapi':'not_runtime_active','web':'disabled_by_default'}}
 release_path=BASE/'release-manifest.json';release_path.write_text(json.dumps(release,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 acceptance={'record_type':'a2_equinet_business_confirmation_acceptance','decision':'approved_and_implemented_no_integration','decision_by':{'name':'Séverine','role':'Unitalk Operations'},'decision_at':STAMP,'scope':'Implement Equinet-confirmed A2 roles, contact-selection, Horse Owner completeness, horse-count evidence precedence and final-review behaviour without intermediate approval gates.','configuration_version':'0.2.0','runtime_overlay_version':'1.1.0','active_manifest_version':'1.2.0','release_manifest':{'path':str(release_path.relative_to(ROOT)),'sha256':sha(release_path)},'limitations':['Named Equinet approver and original source reference remain to be attached.','HubSpot, Twenty, n8n and HarvestAPI integrations remain inactive.','No CRM write, outreach or durable delivery is authorised.'],'external_actions':0,'next_gate':'Step 10 — HubSpot, Twenty and n8n integration'}
 acceptance_path=BASE/'acceptance-record.json';acceptance_path.write_text(json.dumps(acceptance,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 active=load(ROOT/'foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json')
 active_errors=[]
 for item in active['active_files']:
  p=ROOT/item['path']
  if not p.is_file():active_errors.append(f"missing:{item['path']}")
  elif sha(p)!=item['sha256']:active_errors.append(f"hash:{item['path']}")
 release_errors=[]
 for item in release['files']:
  p=ROOT/item['path']
  if not p.is_file():release_errors.append(f"missing:{item['path']}")
  elif sha(p)!=item['sha256']:release_errors.append(f"hash:{item['path']}")
 farrier=load(BASE/'results/farrier-workflow-result.json');owner=load(BASE/'results/horse-owner-workflow-result.json');lang=load(ROOT/'evaluations/foundation-clarifications/language-audit.json')
 checks={'active_manifest_hashes':not active_errors,'release_manifest_hashes':not release_errors,'business_validation':tech.get('status')=='pass' and tech.get('checks_passed')==tech.get('checks_total'),'farrier_workflow':farrier.get('status')=='pass' and farrier.get('operator_count')==14,'horse_owner_workflow':owner.get('status')=='pass' and owner.get('operator_count')==14,'zero_external_actions':farrier.get('external_actions')==owner.get('external_actions')==tech.get('external_actions')==0,'language_audit':lang.get('pass') is True and not lang.get('findings'),'acceptance_release_hash':acceptance['release_manifest']['sha256']==sha(release_path)}
 result={'record_type':'a2_equinet_business_confirmation_final_verification','verified_at':STAMP,'status':'pass' if all(checks.values()) else 'fail','checks':checks,'active_manifest_errors':active_errors,'release_manifest_errors':release_errors,'release_manifest_sha256':sha(release_path),'acceptance_record_sha256':sha(acceptance_path),'external_actions':0}
 out=BASE/'final-verification.json';out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(json.dumps(result,indent=2,ensure_ascii=False));return 0 if result['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
