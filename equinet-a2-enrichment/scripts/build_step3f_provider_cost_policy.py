#!/usr/bin/env python3
"""Build the Step 3F provider and cost-policy draft."""

from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'foundations/contracts/governance/a2-provider-and-cost-policy-0.1.0-draft.1.json'
SOURCE=ROOT/'foundations/contracts/sources/a2-source-register-0.1.0-draft.1.json'
CLARIFICATION=ROOT/'evaluations/foundation-clarifications/step3f-personal-email-review-clarification.json'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def main():
 p={
  'policy_id':'equinet-a2-provider-and-cost-policy','version':'0.1.0-draft.1','status':'approved_by_unitalk_as_working_baseline_runtime_activation_pending','profile':'equinet-a2-enrichment',
  'unitalk_approval':{'approver':'Séverine, Unitalk Operations','approved_at':'2026-08-26T20:26:01Z','scope':'decisions_3F_1_through_3F_10'},
  'dependencies':[{'path':str(SOURCE.relative_to(ROOT)),'sha256':sha(SOURCE)},{'path':str(CLARIFICATION.relative_to(ROOT)),'sha256':sha(CLARIFICATION)}],
  'contractual_budget_boundary':{'advance_token_credit_currency':'USD','advance_token_credit_initial_amount':5000,'negative_balance_permitted':False,'a2_provider_allocation_usd':None,'daily_visibility_required':True,'monthly_statement_required':True},
  'providers':{
   'apify_linkedin_profile_search':{'actor_id':'harvestapi/linkedin-profile-search','purpose':'role_and_company_match_after_official_site_gap','business_approval':'approved','runtime_status':'blocked_pending_rights_vendor_account_budget_retention_and_connector','billing_model':'pay_per_event_verify_in_live_console','limits':{'take_pages':1,'max_items_per_candidate':5,'max_retained_contacts':3,'concurrency':1,'automatic_query_segmentation':False},'allowed_fields':['name','current_title','current_company','professional_location','profile_url'],'prohibited_fields':['full_career_history','education','skills','posts','followers','connections','photos','personal_interests']},
   'apify_independent_email_search':{'actor_id':'harvestapi/linkedin-profile-search','mode':'full_plus_email_search','purpose':'professional_email_search_for_selected_matched_profile','business_approval':'approved','runtime_status':'blocked_pending_rights_vendor_account_budget_retention_and_connector','max_searches_per_candidate':3,'professional_email':'eligible_for_verification','personal_email':'held_for_human_privacy_review','personal_email_contactability_before_review':False,'crm_write_before_review':False,'outreach_before_authoritative_checks':False,'provenance':'independent_HarvestAPI_email_search_not_LinkedIn'},
   'apollo':{'status':'equinet_test_pending_not_selected','runtime_enabled':False},
   'clay':{'status':'equinet_test_pending_not_selected','runtime_enabled':False}
  },
  'benchmark':{'candidate_count':10,'segments':['farrier','horse_owner'],'dataset':'approved_fixed_dataset','live_crm_write':False,'outreach':False,'success_metrics':['identity_match_precision','role_company_match_precision','professional_email_precision','coverage_by_segment','false_positive_rate','cost_per_usable_verified_field','provenance_completeness','latency'],'acceptance_thresholds':'pending_after_first_bounded_output_review'},
  'budget_controls':{'test_cap_usd':None,'daily_cap_usd':None,'pilot_cap_usd':None,'spend_approver':None,'consumption_owner':None,'warning_percent':50,'escalation_percent':80,'hard_stop_percent':100,'run_blocked_when_any_required_cap_is_null':True,'never_exceed_remaining_prepaid_balance':True},
  'execution_controls':{'idempotency_key_components':['candidate_id','provider_action','field_key','policy_version'],'successful_lookup_reuse_required':True,'retry_on_not_found':0,'retry_on_policy_or_budget_block':0,'max_retry_on_transient_technical_failure':1,'no_automatic_provider_fallback':True,'provider_result_requires_audit_record':True},
  'data_governance':{'raw_dataset_retention_days':None,'retention_policy_status':'pending','minimum_normalised_evidence_only':True,'credentials_in_secret_store_only':True,'provider_output_not_authoritative_without_validation':True,'deliverability_is_not_consent':True,'personal_email_review_state':'held_for_human_privacy_review'},
  'runtime_activation_gate':{'all_required':['approved_account','pinned_actor_build','rights_or_exception','vendor_due_diligence','retention_rule','test_cap','daily_cap','pilot_cap','spend_approver','consumption_owner','audit_logging','connector_test'],'current_status':'blocked','external_calls_authorized':False},
  'open_inputs':['authorised Apify workspace/account and runtime owner','pinned Actor build','rights or documented exception','HarvestAPI vendor/privacy review','raw dataset retention period','test, daily and pilot USD caps','spend approver and consumption owner','benchmark acceptance thresholds after the first bounded output review','Equinet decision on personal-email review outcomes'],
 }
 write(OUT,p)
 print(json.dumps({'policy':str(OUT),'version':p['version'],'providers':len(p['providers']),'benchmark_candidates':p['benchmark']['candidate_count']},indent=2))
if __name__=='__main__': main()
