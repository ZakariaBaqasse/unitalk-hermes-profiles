#!/usr/bin/env python3
"""Validate the Step 3F provider and cost policy draft."""

from __future__ import annotations
import copy, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'foundations/contracts/governance/a2-provider-and-cost-policy-0.1.0-draft.1.json'
CONTRACT=ROOT/'foundations/A2-PROVIDER-AND-COST-POLICY.md'
EVAL=ROOT/'evaluations/step3f'; REVIEW=EVAL/'A2-PROVIDER-COST-POLICY-REVIEW.md'; OUTPUT=EVAL/'technical-validation.json'; MANIFEST=EVAL/'step3f-draft-package-manifest.json'
LANGUAGE=ROOT/'evaluations/foundation-clarifications/language-audit.json'
BUILDER=ROOT/'scripts/build_step3f_provider_cost_policy.py'; VALIDATOR=Path(__file__).resolve()

def load(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def validate(p):
 e=[]
 if p.get('status')!='approved_by_unitalk_as_working_baseline_runtime_activation_pending': e.append('policy status must be the approved Unitalk working baseline with runtime pending')
 approval=p.get('unitalk_approval',{})
 if approval.get('approver')!='Séverine, Unitalk Operations' or approval.get('scope')!='decisions_3F_1_through_3F_10': e.append('Unitalk approval metadata is invalid')
 for d in p.get('dependencies',[]):
  q=ROOT/d['path']
  if not q.exists() or sha(q)!=d['sha256']: e.append(f"dependency hash mismatch: {d['path']}")
 c=p.get('contractual_budget_boundary',{})
 if c.get('advance_token_credit_currency')!='USD' or c.get('advance_token_credit_initial_amount')!=5000 or c.get('negative_balance_permitted') is not False: e.append('contractual prepaid-credit boundary mismatch')
 b=p.get('budget_controls',{})
 if any(b.get(k) is not None for k in ['test_cap_usd','daily_cap_usd','pilot_cap_usd','spend_approver','consumption_owner']): e.append('pending budget values were invented')
 if b.get('hard_stop_percent')!=100 or b.get('never_exceed_remaining_prepaid_balance') is not True or b.get('run_blocked_when_any_required_cap_is_null') is not True: e.append('hard budget stop is missing')
 providers=p.get('providers',{})
 if set(providers)!={'apify_linkedin_profile_search','apify_independent_email_search','apollo','clay'}: e.append('provider inventory mismatch')
 if providers['apollo']['runtime_enabled'] or providers['clay']['runtime_enabled']: e.append('unselected provider enabled')
 for name in ['apify_linkedin_profile_search','apify_independent_email_search']:
  if providers[name]['runtime_status']!='blocked_pending_rights_vendor_account_budget_retention_and_connector': e.append(f'{name} runtime status overstated')
 email=providers['apify_independent_email_search']
 if email.get('personal_email')!='held_for_human_privacy_review' or email.get('personal_email_contactability_before_review') is not False or email.get('crm_write_before_review') is not False or email.get('outreach_before_authoritative_checks') is not False: e.append('personal-email review boundary mismatch')
 if email.get('provenance')!='independent_HarvestAPI_email_search_not_LinkedIn': e.append('email provenance incorrectly attributed')
 x=p.get('execution_controls',{})
 if x.get('retry_on_not_found')!=0 or x.get('retry_on_policy_or_budget_block')!=0 or x.get('max_retry_on_transient_technical_failure')!=1 or x.get('no_automatic_provider_fallback') is not True: e.append('retry or fallback controls mismatch')
 g=p.get('data_governance',{})
 if g.get('raw_dataset_retention_days') is not None or g.get('retention_policy_status')!='pending': e.append('retention was invented')
 gate=p.get('runtime_activation_gate',{})
 if gate.get('current_status')!='blocked' or gate.get('external_calls_authorized') is not False: e.append('runtime activation gate was weakened')
 if p.get('benchmark',{}).get('candidate_count')!=10: e.append('benchmark candidate count mismatch')
 return e

def authorize(policy, request):
 missing=[g for g in policy['runtime_activation_gate']['all_required'] if not request.get('gates',{}).get(g)]
 caps=policy['budget_controls']; requested=request.get('estimated_cost_usd',0); remaining=request.get('remaining_prepaid_balance_usd',0)
 if request.get('idempotent_result_exists'): return {'decision':'reuse_existing_result','charge_authorized':False,'missing_gates':missing,'reason':'successful prior result exists'}
 if missing: return {'decision':'blocked','charge_authorized':False,'missing_gates':missing,'reason':'activation gates incomplete'}
 limits=request.get('approved_caps',{})
 if any(limits.get(k) is None for k in ['test_cap_usd','daily_cap_usd','pilot_cap_usd']): return {'decision':'blocked','charge_authorized':False,'missing_gates':[],'reason':'required cost cap missing'}
 if requested>min(limits['test_cap_usd'],limits['daily_cap_usd'],limits['pilot_cap_usd'],remaining): return {'decision':'blocked','charge_authorized':False,'missing_gates':[],'reason':'cost or prepaid balance cap exceeded'}
 return {'decision':'approved_for_bounded_test','charge_authorized':True,'missing_gates':[],'reason':'all gates and caps pass'}

def negatives(p):
 out=[]
 def run(n,x,fn):
  q=copy.deepcopy(p);fn(q);es=validate(q);out.append({'name':n,'expected_error':x,'errors':es,'passed':any(x in z for z in es)})
 run('currency_changed','prepaid-credit boundary',lambda q:q['contractual_budget_boundary'].update(advance_token_credit_currency='EUR'))
 run('negative_balance','prepaid-credit boundary',lambda q:q['contractual_budget_boundary'].update(negative_balance_permitted=True))
 run('invented_budget','pending budget values were invented',lambda q:q['budget_controls'].update(test_cap_usd=25))
 run('hard_stop_removed','hard budget stop is missing',lambda q:q['budget_controls'].update(hard_stop_percent=110))
 run('apollo_enabled','unselected provider enabled',lambda q:q['providers']['apollo'].update(runtime_enabled=True))
 run('apify_enabled','runtime status overstated',lambda q:q['providers']['apify_linkedin_profile_search'].update(runtime_status='active'))
 run('personal_email_operational','personal-email review boundary mismatch',lambda q:q['providers']['apify_independent_email_search'].update(personal_email_contactability_before_review=True))
 run('email_misattributed','email provenance incorrectly attributed',lambda q:q['providers']['apify_independent_email_search'].update(provenance='LinkedIn'))
 run('retry_not_found','retry or fallback controls mismatch',lambda q:q['execution_controls'].update(retry_on_not_found=2))
 run('retention_invented','retention was invented',lambda q:q['data_governance'].update(raw_dataset_retention_days=30))
 run('gate_enabled','runtime activation gate was weakened',lambda q:q['runtime_activation_gate'].update(current_status='active',external_calls_authorized=True))
 run('approval_removed','Unitalk approval metadata is invalid',lambda q:q['unitalk_approval'].update(scope='draft_only'))
 return out

def render(p):
 c="""# Equinet A2 Provider and Cost Policy

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED UNITALK WORKING BASELINE — RUNTIME ACTIVATION PENDING`  
**Decision timestamp:** `2026-08-26T20:26:01Z`  
**Step:** `3F — Provider and Cost Policy`

## Current provider scope

- Apify `harvestapi/linkedin-profile-search` for bounded role/company matching after an official-site gap.
- The same Actor's independent email-search mode as a separately governed action.
- Apollo and Clay remain under Equinet evaluation and are not selected.

## Personal email review

A personal email returned by the independent search may be retained only as `held_for_human_privacy_review`. Before review it cannot satisfy professional contactability, be written to CRM, be used for outreach or be represented as LinkedIn-sourced. Review may approve recorded business use, reject and delete it, or hold it for more evidence. Retention remains pending.

## Cost controls

The contractual USD 5,000 Advance Token Credit is a hard aggregate ceiling and may never become negative. A2-specific test, daily and pilot caps, spend approver and consumption owner remain unset; therefore provider execution remains blocked. Warnings occur at 50%, escalation at 80% and hard stop at 100% of an approved cap.

## Execution controls

- Reuse a successful idempotent result.
- No retry for `not_found`, policy block or budget block.
- Maximum one retry for a transient technical failure.
- No automatic fallback to Apollo, Clay or another provider.
- Record provider action, candidate, field, run, usage, cost, result and approval.

## Benchmark

Use ten approved candidates across Farrier and Horse Owner. Measure identity and role/company precision, professional-email precision, segment coverage, false positives, provenance, latency and cost per usable verified field. Acceptance thresholds are set only after reviewing the first bounded output.

## Remaining activation inputs

1. Apify workspace/account, runtime owner and credential route.
2. Pinned Actor build.
3. Rights or documented exception.
4. HarvestAPI vendor/privacy review.
5. Raw-result retention period.
6. Test, daily and pilot USD caps.
7. Spend approver and consumption owner.
8. Personal-email review owner and final outcomes.

Séverine approved decisions 3F-1 through 3F-10 as the Unitalk working baseline. No provider execution or spend is authorised.
"""
 CONTRACT.write_text(c,encoding='utf-8')
 r="""# Decision Review — Step 3F Provider and Cost Policy

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED AS UNITALK WORKING BASELINE — RUNTIME BLOCKED`  
**Decision timestamp:** `2026-08-26T20:26:01Z`

| ID | Proposed decision |
|---|---|
| 3F-1 | Limit current provider scope to Apify profile search and its separately governed email-search action. |
| 3F-2 | Keep Apollo, Clay and other providers unselected pending Equinet tests. |
| 3F-3 | Keep all monetary caps and approvers pending; block runtime while any required value is missing. |
| 3F-4 | Use a ten-candidate benchmark with the existing per-candidate source limits. |
| 3F-5 | Reuse successful idempotent results, use no retry for not-found or blocked outcomes, and allow one transient technical retry. |
| 3F-6 | Prohibit automatic fallback to another provider. |
| 3F-7 | Hold personal emails for human privacy review; do not use them operationally before approval. |
| 3F-8 | Attribute provider email to the independent HarvestAPI search, not LinkedIn. |
| 3F-9 | Require daily visibility, monthly statements and a hard stop before any approved cap or prepaid balance is exceeded. |
| 3F-10 | Keep runtime blocked until account, rights, vendor, retention, budget, audit and connector gates pass. |

This approval establishes the Unitalk working baseline and authorises Step 3G draft preparation. It does not authorise provider execution or spend.
"""
 REVIEW.write_text(r,encoding='utf-8')

def main():
 p=load(POLICY); errs=validate(p); neg=negatives(p)
 if any(not x['passed'] for x in neg): errs.append('negative regression failed')
 all_gates={k:True for k in p['runtime_activation_gate']['all_required']}
 cases=[
  ('current_policy_blocked',authorize(p,{'gates':{},'estimated_cost_usd':1,'remaining_prepaid_balance_usd':5000}), 'blocked'),
  ('fully_gated_under_cap',authorize(p,{'gates':all_gates,'approved_caps':{'test_cap_usd':25,'daily_cap_usd':10,'pilot_cap_usd':100},'estimated_cost_usd':5,'remaining_prepaid_balance_usd':5000}), 'approved_for_bounded_test'),
  ('over_daily_cap',authorize(p,{'gates':all_gates,'approved_caps':{'test_cap_usd':25,'daily_cap_usd':10,'pilot_cap_usd':100},'estimated_cost_usd':11,'remaining_prepaid_balance_usd':5000}), 'blocked'),
  ('over_remaining_balance',authorize(p,{'gates':all_gates,'approved_caps':{'test_cap_usd':25,'daily_cap_usd':10,'pilot_cap_usd':100},'estimated_cost_usd':5,'remaining_prepaid_balance_usd':4}), 'blocked'),
  ('idempotent_reuse',authorize(p,{'gates':all_gates,'approved_caps':{'test_cap_usd':25,'daily_cap_usd':10,'pilot_cap_usd':100},'estimated_cost_usd':5,'remaining_prepaid_balance_usd':5000,'idempotent_result_exists':True}), 'reuse_existing_result'),
 ]
 case_results=[{'name':n,'result':res,'expected':exp,'passed':res['decision']==exp} for n,res,exp in cases]
 if any(not x['passed'] for x in case_results): errs.append('authorization scenario failed')
 EVAL.mkdir(parents=True,exist_ok=True)
 render(p)
 docs={'contract':CONTRACT.exists(),'review':REVIEW.exists(),'decisions':all(f'| 3F-{n} |' in REVIEW.read_text() for n in range(1,11)),'runtime_block':'No provider execution or spend is authorised' in CONTRACT.read_text()}
 if not all(docs.values()): errs.append('documentation check failed')
 lang=load(LANGUAGE)
 if not lang.get('pass'): errs.append('language audit failed')
 result={'step':'3F','version':p['version'],'approval_state':'approved_unitalk_working_baseline_runtime_activation_pending','policy':{'path':str(POLICY.relative_to(ROOT)),'sha256':sha(POLICY)},'policy_validation':{'errors':validate(p),'passed':not validate(p)},'authorization_cases':{'total':len(case_results),'passed':sum(x['passed'] for x in case_results),'cases':case_results},'negative_regressions':{'total':len(neg),'passed':sum(x['passed'] for x in neg),'cases':neg},'documentation_checks':docs,'language_audit':{'files_checked':lang.get('files_checked'),'findings':len(lang.get('findings',[])),'passed':lang.get('pass') is True},'runtime_activation':False,'provider_spend_authorized':False,'external_actions':0,'next_gate_after_approval':'Step 3G — Preliminary A2-to-HubSpot Mapping','failures':errs,'pass':not errs}
 EVAL.mkdir(parents=True,exist_ok=True);OUTPUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 paths=[POLICY,BUILDER,VALIDATOR,CONTRACT,REVIEW,OUTPUT]
 manifest={'manifest_id':'equinet-a2-step3f-draft-package','version':p['version'],'status':'approved_unitalk_working_baseline_runtime_activation_pending','files':[{'path':str(x.relative_to(ROOT)),'bytes':x.stat().st_size,'sha256':sha(x)} for x in paths],'file_count':len(paths),'provider_spend':0,'external_actions':0}
 MANIFEST.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({'pass':result['pass'],'authorization_cases':f"{result['authorization_cases']['passed']}/{result['authorization_cases']['total']}",'negative':f"{result['negative_regressions']['passed']}/{result['negative_regressions']['total']}",'runtime_activation':False,'review':str(REVIEW),'failures':errs},indent=2))
 return 0 if not errs else 1
if __name__=='__main__': raise SystemExit(main())
