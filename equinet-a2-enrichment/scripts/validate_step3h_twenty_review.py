#!/usr/bin/env python3
"""Validate Step 3H Twenty review-layer contract and fixtures."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker
R=Path(__file__).resolve().parents[1];O=R/'foundations/contracts/twenty';CONTRACT=O/'a2-twenty-review-layer-contract-0.1.0-draft.1.json';SCHEMA=O/'a2-twenty-review-receipt.schema.json';FIX=R/'evaluations/step3h/fixtures';ROOT=R/'evaluations/step3h';DOC=R/'foundations/A2-TWENTY-REVIEW-LAYER-CONTRACT.md';REVIEW=ROOT/'A2-TWENTY-REVIEW-LAYER-REVIEW.md';OUT=ROOT/'technical-validation.json';MANIFEST=ROOT/'step3h-draft-package-manifest.json';LANG=R/'evaluations/foundation-clarifications/language-audit.json';B=R/'scripts/build_step3h_twenty_review.py';V=Path(__file__).resolve()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def errors(x,s):
 es=[f"schema:/{'/'.join(map(str,e.absolute_path))}: {e.message}" for e in Draft202012Validator(s,format_checker=FormatChecker()).iter_errors(x)]
 status=x.get('review_status');final=status in {'approved','needs_changes','held','rejected'}
 if final and (x.get('reviewer') is None or x.get('decided_at') is None):es.append('final decision requires reviewer and decided_at')
 ids=[d.get('field_assessment_id') for d in x.get('field_decisions',[])]
 if len(ids)!=len(set(ids)):es.append('duplicate field decision')
 if status=='approved':
  if any(d.get('decision')!='approved' for d in x.get('field_decisions',[])):es.append('approved receipt cannot contain unresolved field decision')
  if x.get('approval_scope')!='prepare_proposed_hubspot_patch' or x.get('proposed_hubspot_patch_authorized') is not True:es.append('approved review requires proposed patch scope')
 if status!='approved' and x.get('proposed_hubspot_patch_authorized'):es.append('non-approved review cannot authorize proposed patch')
 if status=='needs_changes' and any(d.get('corrected_value') is not None for d in x.get('field_decisions',[])) and not x.get('corrected_values_create_new_revision'):es.append('needs_changes with correction requires new revision')
 if x.get('hubspot_write_authorized') is not False:es.append('hubspot_write_authorized must remain false')
 return sorted(es)
def render(c,results):
 rows='\n'.join(f"| `{x['name']}` | {'valid' if x['expected'] else 'invalid'} | {'PASS' if x['passed'] else 'FAIL'} |" for x in results)
 DOC.write_text("""# Equinet A2 Twenty Review Layer Contract and Mapping

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED UNITALK WORKING BASELINE — TWENTY WORKSPACE VERIFICATION PENDING`  
**Decision timestamp:** `2026-08-27T10:19:34Z`  
**Step:** `3H — Twenty Review Layer Contract and Mapping`

## Operating model

A1 keeps the main prospect record in Twenty. A2 creates a linked, versioned enrichment-review record and field-level decisions or an equivalent workspace-supported structure. Canonical A2 JSON remains the only lossless source of truth. Twenty is the staging and human-review layer; HubSpot remains the final CRM system of record.

## Review states

`pending → in_review → approved | needs_changes | held | rejected`

`needs_changes → pending` after A2 creates a new canonical revision. `held → in_review` after the named dependency is resolved. Approved and rejected decisions are terminal for that review revision.

## Review capabilities

The reviewer may approve, reject, hold or request changes per field, provide corrected values and comments, then take a record-level decision. Final decisions require reviewer identity, role, timestamp, reason and an idempotent review receipt.

## Approval effect

Twenty approval authorises preparation of a proposed HubSpot patch only. It never authorises HubSpot write or outreach. Corrections create a new A2 revision and retain the prior revision.

## Proposed Twenty model

- Existing A1 prospect record: retained.
- Linked `A2 Enrichment Review` logical object: proposed.
- Linked `A2 Field Decision` logical object or safe structured equivalent: proposed.
- Exact object names, fields and relations: pending workspace metadata.

## API and workflow boundary

Twenty provides workspace-generated REST/GraphQL APIs and webhooks, but the Equinet workspace schema, API key, role scopes and event configuration are not connected. n8n must filter, deduplicate and reconcile events. No integration is activated by this contract.
""",encoding='utf-8')
 REVIEW.write_text(f"""# Decision Review — Step 3H Twenty Review Layer

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED AS UNITALK WORKING BASELINE — INTEGRATION PENDING`  
**Decision timestamp:** `2026-08-27T10:19:34Z`

| ID | Proposed decision |
|---|---|
| 3H-1 | Keep the A1 prospect as the main Twenty record and use a linked versioned A2 review record. |
| 3H-2 | Use pending, in_review, needs_changes, held, approved and rejected review states. |
| 3H-3 | Support field-level decisions, corrected values, comments and a record-level decision. |
| 3H-4 | Require reviewer identity, role, timestamp, reason and an idempotent receipt. |
| 3H-5 | Let Twenty approval authorize proposed HubSpot patch preparation only. |
| 3H-6 | Require corrected values to create a new canonical A2 revision. |
| 3H-7 | Keep canonical JSON as the lossless source and Twenty as a review projection/input layer. |
| 3H-8 | Use role-scoped Twenty API access and n8n filtering/deduplication after integration approval. |
| 3H-9 | Reject duplicate or mismatched Twenty candidate/review events. |
| 3H-10 | Keep HubSpot write and outreach authorization false in every Twenty review receipt. |

## Fixture result

| Case | Expected | Test |
|---|---|---:|
{rows}

This approval establishes the Unitalk working baseline and authorises preparation of the final specialist SOUL in draft form. Exact Twenty workspace mapping and runtime activation remain pending.
""",encoding='utf-8')
def main():
 c=load(CONTRACT);s=load(SCHEMA);Draft202012Validator.check_schema(s);fails=[]
 if c.get('status')!='approved_by_unitalk_as_working_baseline_twenty_integration_pending':fails.append('contract status must be the approved Unitalk working baseline')
 approval=c.get('unitalk_approval',{})
 if approval.get('approver')!='Séverine, Unitalk Operations' or approval.get('scope')!='decisions_3H_1_through_3H_10':fails.append('Unitalk approval metadata is invalid')
 if c['integration_status']['runtime_active'] or c['integration_status']['workspace_metadata_received']:fails.append('integration status overstated')
 if c['approval_effects']['any_decision']!='never authorizes HubSpot write or outreach':fails.append('approval effect unsafe')
 if c['review_states']!=['pending','in_review','needs_changes','held','approved','rejected']:fails.append('review states mismatch')
 results=[]
 for k in load(FIX/'manifest.json')['cases']:
  es=errors(load(FIX/k['fixture']),s);actual=not es;passed=actual==k['valid'] and (k['valid'] or k['expected'] in '\n'.join(es));results.append({'name':k['name'],'expected':k['valid'],'actual':actual,'errors':es,'passed':passed})
  if not passed:fails.append(f"fixture failed: {k['name']}")
 render(c,results);lang=load(LANG)
 if not lang.get('pass'):fails.append('language audit failed')
 result={'step':'3H','version':c['version'],'approval_state':'approved_unitalk_working_baseline_twenty_integration_pending','contract':{'path':str(CONTRACT.relative_to(R)),'sha256':sha(CONTRACT)},'schema':{'path':str(SCHEMA.relative_to(R)),'sha256':sha(SCHEMA)},'fixtures':{'total':len(results),'passed':sum(x['passed'] for x in results),'cases':results},'language_audit':{'files_checked':lang.get('files_checked'),'findings':len(lang.get('findings',[])),'passed':lang.get('pass') is True},'twenty_connection':False,'hubspot_write_authorized':False,'external_actions':0,'open_inputs':c['open_inputs'],'failures':fails,'pass':not fails}
 ROOT.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');paths=[CONTRACT,SCHEMA,FIX/'manifest.json',B,V,DOC,REVIEW,OUT];manifest={'manifest_id':'equinet-a2-step3h-draft-package','version':c['version'],'status':'approved_unitalk_working_baseline_twenty_integration_pending','files':[{'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths],'file_count':len(paths),'external_actions':0};MANIFEST.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({'pass':result['pass'],'fixtures':f"{result['fixtures']['passed']}/{result['fixtures']['total']}",'twenty_connection':False,'review':str(REVIEW),'failures':fails},indent=2));return 0 if not fails else 1
if __name__=='__main__':raise SystemExit(main())
