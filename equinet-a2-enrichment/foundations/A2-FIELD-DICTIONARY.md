# Equinet A2 Canonical Field Dictionary

**Version:** `0.1.0`  
**Status:** `APPROVED BY UNITALK OPERATIONS FOR STEP 2C`  
**Decision:** `APPROVED AS DRAFTED`  
**Approver:** Séverine, Unitalk Operations  
**Decision timestamp:** `2026-08-25T22:20:22Z`  
**Detailed machine-readable dictionary:** `contracts/a2-field-dictionary-0.1.0.csv`

## 1. Purpose

This dictionary defines the stable structural fields of the canonical A2 Enrichment Record before JSON Schema is authored. It does not define the business field catalogue such as email, service area, certifications or horse count; those fields are referenced generically through `field_assessments[].field_key`.

## 2. Dictionary columns

- `section` — approved canonical section.
- `field_path` — unique future JSON path.
- `data_type` — intended canonical type before final JSON Schema syntax.
- `required` — yes, no or conditional.
- `nullable` — whether explicit null is valid.
- `cardinality` — one, zero-or-one, zero-or-more or one-or-more.
- `producer` — actor, script, reviewer or connector that creates the value.
- `authority` — source that controls the business meaning or final result.
- `mutability` — immutable, append-only, derived, human-controlled, external-authoritative or connector-controlled.
- `state_vocabulary` — exact vocabulary defined in the State Model where applicable.

## 3. Section inventory

| Section | Field paths | Purpose |
|---|---:|---|
| `record_metadata` | 12 | Stable record/revision identity, run and audit correlation. |
| `source_handoff` | 9 | Immutable accepted A1-to-A2 envelope and source snapshot. |
| `subject` | 16 | A2-resolved people, organisations and relationships. |
| `enrichment_scope` | 7 | Requested field package, policy versions, scope and run limits. |
| `field_assessments` | 52 | Generic baseline, observations, proposal, field review and application state. |
| `evidence_registry` | 21 | A2-native evidence and references to reused A1 evidence. |
| `data_quality` | 10 | Deterministic completeness, gap, conflict, stale and invalid-field summary. |
| `duplicate_and_eligibility` | 14 | Separate duplicate, CRM eligibility, outreach and owner-routing visibility. |
| `requalification` | 22 | A2 signals/returns and authoritative A1 score-revision references. |
| `review` | 6 | Record-level human decision and requested changes. |
| `workflow` | 7 | Controlled A2 lifecycle state and transition evidence. |
| `system_references` | 15 | Connector-controlled A1, HubSpot, Twenty, n8n, provider and downstream IDs. |
| `governance` | 12 | Purpose, personal-data, source, consent, retention, approval and action guards. |
| `audit_and_consumption` | 13 | Append-only run, tool, model, usage, cost, error and external-action events. |

**Total field paths:** 216

## 4. Core ownership rules

- `source_handoff.*` is immutable and remains owned by the accepted A1 handoff.
- `field_assessments[].baseline` mirrors the authoritative value known before the current proposal.
- `observations[]` is append-only and preserves every permitted material observation, including contradictions.
- A2 may create at most one `proposed_resolution` per field assessment and revision.
- The authorised human controls `field_review` and `review.record_decision`.
- Approval is separate from `application`; only an authorised connector can record an applied external action.
- Every future external-system ID is nullable except the A1 candidate and handoff IDs; null never means checked or absent.
- A2 creates requalification signals, but only A1 may produce a numeric score revision.
- Source, minimum-package, confidence, freshness, retention and HubSpot mapping rules remain separate versioned configurations.

## 5. Baseline, observation, proposal, decision and application

```text
baseline = value known before the current A2 proposal
observations = permitted values collected or reused during enrichment
proposed_resolution = one evidence-led recommendation
field_review = human decision
application = separate verified external action state
```

A baseline is never silently overwritten. A reviewer correction or approved external result creates a new immutable record revision.

## 6. Required A1 and external references

- `system_references.a1_candidate_id` and `system_references.a1_handoff_id` are required and non-nullable.
- HubSpot, Twenty, n8n, provider, A3, A14 and sync references remain nullable until a connector verifies them.
- The exact HubSpot property mapping is not part of this dictionary.

## 7. Open items

- Business field keys and Required/Optional/Do Not Collect decisions.
- Farrier and Horse Owner minimum packages.
- Evidence, verification, confidence and freshness calculations.
- Protected-field catalogue and field-specific conflict rules.
- A2 source register and provider approvals.
- HubSpot/Twenty mappings and workflow dependency register.
- Named A2 reviewer and backup.

## 8. Step 2B approval boundary

Approval of this dictionary authorises Step 2C and later JSON Schema authoring. It does not approve business fields, sources, integrations, live enrichment, CRM writes, outreach, pilot or production use.
