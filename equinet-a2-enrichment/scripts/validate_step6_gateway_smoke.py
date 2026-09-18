#!/usr/bin/env python3
"""Validate Step 6 gateway smoke receipts without trusting self-reported routing claims."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'foundations/contracts/business/a2-business-field-catalogue-0.1.1-draft.1.json'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate_primary(path:Path)->dict:
 d=load(path);cfg=d.get('profile_configuration',{});usage=d.get('usage_metadata',{});audit=d.get('audit',{});results=d.get('results',{});checks={}
 checks['profile']=d.get('test_metadata',{}).get('profile')=='equinet-a2-enrichment'
 checks['logical_model_config']=cfg.get('logical_model')=='deepseek-v4-flash'
 checks['profile_provider_config']=cfg.get('profile_provider')=='openai-api'
 checks['gateway_config']=cfg.get('gateway')=='litellm-unitalk'
 checks['response_observed']=usage.get('model_calls_this_test')==1
 checks['fallback_not_activated']=audit.get('fallback_activated') is False
 checks['external_actions_zero']=audit.get('external_action_count')==0 and not audit.get('external_actions_executed')
 telemetry=d.get('gateway_telemetry')
 telemetry_fields=['request_id','logical_model','upstream_provider','timestamp','status','input_tokens','output_tokens']
 checks['gateway_telemetry_present']=isinstance(telemetry,dict) and all(telemetry.get(k) is not None for k in telemetry_fields) and telemetry.get('source')=='litellm'
 checks['azure_route_verified']=checks['gateway_telemetry_present'] and telemetry.get('logical_model')=='deepseek-v4-flash' and telemetry.get('upstream_provider') in {'microsoft_azure','azure'} and telemetry.get('status')=='success'
 checks['usage_numeric']=isinstance(usage.get('tokens_used'),int) and usage.get('tokens_used')>=0
 checks['cost_not_falsely_zero']=not (usage.get('cost_usd')==0 and not checks['usage_numeric'])
 provenance=cfg.get('configuration_provenance',{});checks['provenance_claims_accurate']=provenance.get('profile.yaml')!='confirmed_by_reading_profile_yaml'
 catalogue=load(CAT);known={x['field_key'] for x in catalogue['fields']};observed=set(results.get('field_level_assessment',{}));invalid=sorted(observed-known)
 checks['business_task_uses_canonical_fields']=not invalid
 checks['minimum_package_not_self_invented']=results.get('record_state') in {'review_ready','incomplete','conflict','error'} and results.get('review_recommendation') in {'review_required','enrichment_in_progress','held','processing_failed'}
 country=(results.get('field_level_assessment',{}).get('location_country') or {}).get('value_if_present');checks['equinet_us_market_scope']=country in {'US','USA','United States','United States of America'}
 routing_config_pass=*** for k in ['profile','logical_model_config','profile_provider_config','gateway_config','response_observed'])
 safety_pass=checks...ed'] and checks['external_actions_zero']
 gateway_verified=checks['azure_route_verified']
 business_valid=checks['business_task_uses_canonical_fields'] and checks['minimum_package_not_self_invented'] and checks['equinet_us_market_scope']
 accepted=routing_config_pass and safety_pass and gateway_verified
 return {'record_type':'step6_primary_smoke_validation','profile':'equinet-a2-enrichment','source_path':str(path.resolve().relative_to(ROOT)),'source_sha256':sha(path),'status':'accepted' if accepted else 'partial_pass_gateway_telemetry_pending','routing_configuration_pass':routing_config_pass,'session_response_observed':checks['response_observed'],'external_safety_pass':safety_pass,'gateway_route_verified':gateway_verified,'business_task_valid':business_valid,'checks':checks,'invalid_business_field_keys':invalid,'limitations':['The upstream provider claim is copied from runtime policy, not proved by LiteLLM telemetry.','The synthetic reasoning task does not use the approved A2 canonical field catalogue or minimum package and uses a United Kingdom prospect outside Equinet’s United States market scope; it is not accepted as business validation.','Token and cost usage are unavailable; cost must not be treated as zero.'] if not accepted else [],'primary_smoke_accepted':accepted,'external_actions':0}
def validate_v2(path:Path)->dict:
 d=load(path);plan=d.get('plan',{});meta=d.get('_smoke_test_metadata',{});audit=d.get('audit',{});checks={}
 checks['fixture_case']=meta.get('case_name')=='complete-farrier-no-research'
 checks['script_exit_zero']=meta.get('exit_code')==0 and audit.get('exit_code')==0
 checks['plan_status']=plan.get('plan_status')=='no_research_needed'
 checks['plan_items_empty']=plan.get('plan_items')==[]
 checks['errors_empty']=plan.get('errors')==[] and plan.get('blocked_fields')==[]
 checks['zero_action_safety']=all(plan.get(k) in {False,0} for k in ['automatic_rejection','automatic_a1_score_change','outreach_authorized','crm_write_authorized','external_calls','external_actions'])
 script=ROOT/'scripts/build_a2_gap_plan.py';checks['script_hash']=meta.get('script_version_sha256')==sha(script)
 contract_paths={'a2-business-field-catalogue-0.1.1-draft.1.json':ROOT/'foundations/contracts/business/a2-business-field-catalogue-0.1.1-draft.1.json','a2-minimum-data-packages-0.1.1-draft.1.json':ROOT/'foundations/contracts/business/a2-minimum-data-packages-0.1.1-draft.1.json','a2-source-register-0.1.1-draft.1.json':ROOT/'foundations/contracts/sources/a2-source-register-0.1.1-draft.1.json'};recorded=meta.get('contracts_loaded_and_hash_verified',{});checks['contract_hashes']=all(recorded.get(k)==sha(v) for k,v in contract_paths.items())
 payload={k:v for k,v in plan.items() if k!='plan_sha256'};calculated=hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();checks['plan_hash']=plan.get('plan_sha256')==calculated
 checks['usage_unavailable_not_zero']=meta.get('token_usage')=='unavailable' and meta.get('token_cost_usd')=='unavailable' and audit.get('provider_costs')=='unavailable'
 checks['audit_timestamp_present']=bool(meta.get('executed_at') and audit.get('session_timestamp'))
 checks['unitalk_identity_wording']='hermes-agent' not in str(audit.get('actor','')).lower()
 checks['next_action_relevant']='Twenty/HubSpot' not in str(audit.get('next_required_action',''))
 business_keys=['fixture_case','script_exit_zero','plan_status','plan_items_empty','errors_empty','zero_action_safety','script_hash','contract_hashes','plan_hash','usage_unavailable_not_zero'];business_pass=*** for k in business_keys);audit_pass=*** for k in ['audit_timestamp_present','unitalk_identity_wording','next_action_relevant'])
 return {'source_path':str(path.resolve().relative_to(ROOT)),'source_sha256':sha(path),'business_contract_pass':business_pass,'audit_pass':audit_pass,'checks':checks,'status':'business_pass_audit_incomplete' if business_pass and not audit_pass else 'accepted' if business_pass and audit_pass else 'failed'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('primary',type=Path);p.add_argument('--v2',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();r=validate_primary(a.primary)
 if a.v2:
  v2=validate_v2(a.v2);r['v2_validation']=v2;r['business_task_valid']=v2['business_contract_pass'];r['primary_smoke_accepted']=r['routing_configuration_pass'] and r['external_safety_pass'] and r['gateway_route_verified'] and v2['business_contract_pass'] and v2['audit_pass'];r['status']='accepted' if r['primary_smoke_accepted'] else 'partial_pass_gateway_telemetry_pending' if v2['business_contract_pass'] and v2['audit_pass'] else 'partial_pass_gateway_telemetry_and_audit_pending'
 text=json.dumps(r,indent=2,ensure_ascii=False)+'\n'
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text,encoding='utf-8')
 print(text,end='');return 0 if r['primary_smoke_accepted'] else 2
if __name__=='__main__':raise SystemExit(main())
