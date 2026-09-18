#!/usr/bin/env python3
"""Publish A2 Evidence and Protected Fields policies 0.2.0."""
from __future__ import annotations
import hashlib,json
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STAMP='2026-08-30T17:05:11Z'
def load(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(rel,obj):
 p=ROOT/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');return p
def main():
 decision=ROOT/'foundations/decisions/A2-EQUINET-BUSINESS-CONFIRMATION-20260830.json'
 cat=ROOT/'foundations/contracts/business/a2-business-field-catalogue-0.2.0.json'
 source=ROOT/'foundations/contracts/sources/a2-source-register-0.2.0.json'
 state=ROOT/'foundations/contracts/a2-state-model-0.1.0.json'
 evidence=deepcopy(load('foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.1.1-draft.1.json'))
 evidence['version']='0.2.0'
 evidence['status']='approved_unitalk_with_equinet_business_confirmation_freshness_windows_pending'
 evidence['unitalk_approval']={'approver':'Séverine, Unitalk Operations','approved_at':STAMP,'scope':'Equinet-confirmed roles, contact handling, Horse Owner priorities, horse-count evidence precedence and final-review routing'}
 evidence['dependencies']=[{'path':str(source.relative_to(ROOT)),'sha256':sha(source)},{'path':str(cat.relative_to(ROOT)),'sha256':sha(cat)},{'path':str(state.relative_to(ROOT)),'sha256':sha(state)},{'path':str(decision.relative_to(ROOT)),'sha256':sha(decision)}]
 evidence['principles'].update({'existing_hubspot_owner_horse_count_is_authoritative':True,'net_new_horse_count_requires_explicit_approved_evidence':True,'horse_count_range_is_ignored':True,'horse_count_band_new_values_prohibited':True,'missing_required_business_data_still_reaches_final_human_review':True})
 evidence['source_rules']['hubspot_authoritative_records']['horse_count_rule']='Contact.owner_horse_count is authoritative for an existing matched record.'
 evidence['source_rules']['prospect_official_website']['horse_count_rule']='An explicit exact count may support a net-new prospect or an empty HubSpot value; inference is prohibited.'
 evidence['field_specific_rules']={
  'organisation.horse_count':{'existing_match_authority':'Contact.owner_horse_count','net_new_sources':['a1_approved_handoff','equinet_authorized_first_party_data','equinet_representative_confirmation','prospect_official_website'],'exact_positive_integer_required':True,'inference_prohibited':True,'conflict_action':'preserve_hubspot_and_hold_for_human_review'},
  'organisation.horse_count_band':{'new_values_prohibited':True,'historical_values_preserved':True},
  'organisation.breeds':{'at_least_one_verified_value_for_completeness':True,'mixed_or_other_preserved_when_verified':True},
  'organisation.public_business_location':{'minimum_verified_components':['state_region','country_code'],'complete_address_preferred_when_available':True},
  'person.contact_channels':{'attempt_both':['person.business_email','person.business_phone'],'at_least_one_required_when_other_unavailable':True},
 }
 evidence['outcomes']['required_field_unsatisfied'].update({'workflow_after_research_exhausted':'review_required','human_dispositions':['needs_changes','held','approved_collect_during_discovery','rejected_for_explicit_business_reason']})
 evidence_path=dump('foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.2.0.json',evidence)
 protected=deepcopy(load('foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.1.1-draft.1.json'))
 protected['version']='0.2.0'
 protected['status']='approved_unitalk_with_equinet_business_confirmation_integration_pending'
 protected['unitalk_approval']={'approver':'Séverine, Unitalk Operations','approved_at':STAMP,'scope':'Dependency refresh and owner_horse_count authority/write boundary'}
 protected['dependencies']=[{'path':str(cat.relative_to(ROOT)),'sha256':sha(cat)},{'path':str(evidence_path.relative_to(ROOT)),'sha256':sha(evidence_path)},*[d for d in protected['dependencies'] if d['path'].startswith('/opt/data/profiles/equinet/attachments/')]]
 if not any(x.get('property')=='owner_horse_count' for x in protected['hubspot_protected_fields']):
  protected['hubspot_protected_fields'].append({'object':'Contact','property':'owner_horse_count','class':'a2_enrichment_candidate','reason':'authoritative existing horse-count value; reviewed proposal permitted only when empty or through an approved field exception'})
 protected['owner_horse_count_rule']={'existing_populated_value':'preserve_as_authoritative','same_verified_value':'no_change','empty_baseline_verified_net_new_proposal':'propose_add_for_human_review','different_verified_proposal':'preserve_and_hold_for_human_review','write_requires_final_review':True,'workflow_dependency_and_readback_required':True,'horse_count_range':'ignored'}
 protected_path=dump('foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.2.0.json',protected)
 print(json.dumps({'status':'pass','evidence_policy':str(evidence_path.relative_to(ROOT)),'protected_policy':str(protected_path.relative_to(ROOT)),'evidence_sha256':sha(evidence_path),'protected_sha256':sha(protected_path)},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
