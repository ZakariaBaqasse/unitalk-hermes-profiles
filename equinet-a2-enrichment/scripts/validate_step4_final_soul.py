#!/usr/bin/env python3
"""Validate the proposed final Equinet A2 specialist SOUL."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]; ROOT=R/'evaluations/step4'; SOUL=ROOT/'SOUL.proposed.md'; OUT=ROOT/'technical-validation.json'; REVIEW=ROOT/'A2-FINAL-SOUL-REVIEW.md'; MANIFEST=ROOT/'step4-draft-package-manifest.json'; LANGUAGE=R/'evaluations/foundation-clarifications/language-audit.json'; V=Path(__file__).resolve()
DEPS=[R/'foundations/A2-IMPLEMENTATION-CONTRACT.md',R/'foundations/contracts/a1-to-a2-handoff.schema.json',R/'foundations/contracts/canonical/a2-enrichment-record.schema.json',R/'foundations/contracts/business/a2-business-field-catalogue-0.1.0-draft.1.json',R/'foundations/contracts/business/a2-minimum-data-packages-0.1.0-draft.1.json',R/'foundations/contracts/sources/a2-source-register-0.1.0-draft.1.json',R/'foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.1.0-draft.1.json',R/'foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.1.0-draft.1.json',R/'foundations/contracts/governance/a2-provider-and-cost-policy-0.1.0-draft.1.json',R/'foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.1.0-draft.1.json',R/'foundations/contracts/twenty/a2-twenty-review-layer-contract-0.1.0-draft.1.json']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(text):
 e=[]
 headings=['## Deployment status','## Mission','## Authoritative contracts','## Intended users and approval ownership','## Normal operating workflow','## A1 and scoring boundary','## Minimum package and missing-data behaviour','## Source sequence and access rules','## Evidence, confidence and freshness','## Protected fields and conflict handling','## Twenty review layer','## HubSpot mapping and action boundary','## Provider and cost controls','## Outputs','## Action permissions','## Error and escalation behaviour','## Communication behaviour','## Audit requirements','## Current integration status','## Current next gate']
 for h in headings:
  if h not in text:e.append(f'missing heading: {h}')
 required=['FOUNDATION CONFIGURED — NOT PILOT-READY','A1 alone calculates any score revision','A1 durable handoff: not connected','Twenty: selected review layer; workspace schema, API key, permissions and webhooks not connected or verified','HubSpot write: not connected and not authorised','n8n: not connected','rights, vendor, account, build, budget, retention and connector gates pending','A personal email candidate remains `held_for_human_privacy_review`','inventing or guessing a value','The next delivery gate is Step 5 — Operational Skills and Scripts','Never simulate access, success or delivery']
 for x in required:
  if x not in text:e.append(f'missing required boundary: {x}')
 forbidden=['Twenty or alternative review staging: not selected','HubSpot read: connected','HubSpot write: connected','Apify/HarvestAPI: runtime-active','PILOT_READY','PRODUCTION READY','send outreach','autonomously write to HubSpot']
 for x in forbidden:
  if x in text:e.append(f'forbidden or stale claim: {x}')
 if text.count('Twenty Review Layer Contract `0.1.0-draft.1`')!=1:e.append('Step 3H foundation reference missing or duplicated')
 if 'Provider and Cost Policy `0.1.0-draft.1`' not in text or 'Preliminary A2-to-HubSpot Mapping `0.1.0-draft.1`' not in text:e.append('Step 3F/3G references missing')
 return e
def main():
 text=SOUL.read_text(encoding='utf-8');fails=validate(text);deps=[]
 for p in DEPS:
  ok=p.exists();deps.append({'path':str(p.relative_to(R)),'sha256':sha(p) if ok else None,'passed':ok})
  if not ok:fails.append(f'missing dependency: {p}')
 # adversarial removals/unsafe replacements
 mutations=[('remove_no_score','A1 alone calculates any score revision','A1 may calculate a score revision'),('activate_hubspot','HubSpot write: not connected and not authorised','HubSpot write: connected'),('stale_twenty','Twenty: selected review layer; workspace schema, API key, permissions and webhooks not connected or verified','Twenty or alternative review staging: not selected'),('remove_no_invent','inventing or guessing a value','approximating a value'),('provider_active','Apify/HarvestAPI: business-approved scope defined; rights, vendor, account, build, budget, retention and connector gates pending','Apify/HarvestAPI: runtime-active'),('remove_next_gate','The next delivery gate is Step 5 — Operational Skills and Scripts','The next delivery gate is unknown')]
 negative=[]
 for n,old,new in mutations:
  es=validate(text.replace(old,new));negative.append({'name':n,'passed':bool(es),'errors':es})
  if not es:fails.append(f'negative regression failed: {n}')
 language=json.loads(LANGUAGE.read_text())
 if not language.get('pass'):fails.append('language audit failed')
 result={'step':'4','stage':'final_soul_draft','approval_state':'ready_for_severine_review_not_active','proposed_soul':{'path':str(SOUL.relative_to(R)),'sha256':sha(SOUL)},'dependency_checks':deps,'static_errors':validate(text),'negative_regressions':{'total':len(negative),'passed':sum(x['passed'] for x in negative),'cases':negative},'active_soul_replaced':False,'profile_status':'FOUNDATION CONFIGURED — NOT PILOT-READY','language_audit':{'files_checked':language.get('files_checked'),'findings':len(language.get('findings',[])),'passed':language.get('pass') is True},'external_actions':0,'next_gate_after_approval':'Step 5 — Operational Skills and Scripts','failures':fails,'pass':not fails}
 ROOT.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 review="""# Decision Review — Step 4 Final Specialist SOUL

**Status:** `READY FOR SÉVERINE REVIEW — NOT ACTIVE`  
**Proposed profile status:** `FOUNDATION CONFIGURED — NOT PILOT-READY`

## Decisions proposed

| ID | Decision |
|---|---|
| S1 | Replace the temporary safety scaffold with the proposed operational A2 identity. |
| S2 | Use the workflow A1 → Twenty → A2 → Twenty review → proposed HubSpot patch. |
| S3 | Preserve A1-only score ownership and the requalification revision pathway. |
| S4 | Apply the approved minimum-package, source, evidence, freshness and conflict policies by reference. |
| S5 | Keep personal-email candidates in human privacy review before operational use. |
| S6 | Keep Twenty, HubSpot, n8n and Apify actions unavailable until their individual integration gates pass. |
| S7 | Keep every HubSpot mapping read-and-propose only and every write blocked. |
| S8 | Require verified receipts for Twenty submissions, reviews, provider actions and CRM writes. |
| S9 | Keep the profile `NOT PILOT-READY` until skills, runtime and end-to-end acceptance pass. |
| S10 | Proceed next to Step 5 — Operational Skills and Scripts. |

## Approval effect

Approval will replace the active temporary `SOUL.md` with the proposed final specialist identity. It will not activate integrations, source calls, provider spend, HubSpot writes, outreach, pilot status or production status.
"""
 REVIEW.write_text(review,encoding='utf-8');paths=[SOUL,V,OUT,REVIEW,*DEPS];manifest={'manifest_id':'equinet-a2-step4-final-soul-draft','status':'ready_for_severine_review_not_active','files':[{'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths],'file_count':len(paths),'active_soul_replaced':False,'external_actions':0};MANIFEST.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({'pass':result['pass'],'static_errors':len(result['static_errors']),'negative':f"{result['negative_regressions']['passed']}/{result['negative_regressions']['total']}",'dependency_count':len(deps),'active_soul_replaced':False,'review':str(REVIEW),'failures':fails},indent=2));return 0 if not fails else 1
if __name__=='__main__':raise SystemExit(main())
