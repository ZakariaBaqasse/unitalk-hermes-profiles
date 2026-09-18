# Decision Review — Step 2A Canonical Record Design and Field Ownership

**Design version:** `0.1.0`  
**Status:** `APPROVED BY UNITALK OPERATIONS FOR STEP 2B`  
**Profile status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`  
**Technical validation:** PASS  
**Human decision:** APPROVED AS DRAFTED  
**Approver:** Séverine, Unitalk Operations  
**Decision date:** `2026-08-16T16:37:04Z`

## Technical validation summary

| Check group | Result |
|---|---:|
| Required design sections | 24/24 PASS |
| Canonical top-level sections | 14/14 PASS |
| Ownership and safety boundaries | 10/10 PASS |
| Decisions R1–R9 present | 9/9 PASS |
| Forbidden readiness or ownership claims | 0 found |

## Proposed canonical structure

The future A2 canonical record will contain:

- record and immutable revision metadata;
- the complete accepted A1-to-A2 source handoff;
- A2-resolved people, organisations and relationships;
- enrichment scope;
- generic field assessments;
- A2 evidence registry;
- enrichment data quality;
- duplicate and eligibility checks;
- requalification signals, returns and A1 score-revision references;
- field-level and record-level human review;
- workflow state;
- nullable external-system references;
- governance references;
- append-only audit and consumption metadata.

## Core ownership model

| Information or action | Owner |
|---|---|
| Original A1 candidate, evidence and score | Immutable accepted A1 handoff |
| A2 observations and evidence | A2 under approved policies |
| Proposed field resolution | A2 |
| Field and record decision | Authorised human reviewer |
| Requalification signal | A2 |
| Evidence acceptance and deterministic rescoring | A1 |
| New score-revision approval | Authorised human reviewer |
| HubSpot/Twenty IDs and applied actions | Authorised connector or workflow |
| Audit and consumption events | Runtime/workflow/connectors |

## Field-assessment structure

Each business field will use the same stable structure:

```text
field identity
→ baseline
→ zero or more observations
→ at most one proposed resolution
→ human decision
→ separate application/sync state
```

This avoids hard-coding HubSpot properties or a fixed enrichment-provider model into the canonical schema.

## Decisions requested

| ID | Unitalk proposal | Main consequence |
|---|---|---|
| R1 | One A2 record lineage per accepted A1 handoff version. | A materially changed A1 handoff creates a new linked A2 lineage. |
| R2 | Every released A2 JSON revision is immutable. | Corrections and approvals create new revisions instead of overwriting history. |
| R3 | Embed the complete accepted A1-to-A2 handoff. | The A2 record remains lossless and usable without live integrations. |
| R4 | Use generic `field_assessments[]` plus a separate business field catalogue. | The schema remains stable when business fields or CRM mappings change. |
| R5 | Use baseline + observations + one proposed resolution + human decision + application state. | Conflicts and approval remain visible and auditable. |
| R6 | Give A2 evidence its own namespace and reference reused A1 evidence. | New A2 evidence cannot be confused with evidence collected by A1. |
| R7 | Support field-level and record-level review. | Protected fields require explicit field-level approval. |
| R8 | Store requalification signals/returns and A1 score-revision references. | A2 can trigger score evolution while A1 remains the scoring owner. |
| R9 | Keep external IDs nullable and connector-controlled. | Null never means checked, absent or eligible. |

## Deferred items

Approval of Step 2A does not approve:

- the detailed field dictionary or exact enums;
- the canonical JSON Schema;
- the business field catalogue;
- Horse Owner or Farrier minimum data packages;
- confidence, freshness or conflict calculations;
- source/provider policies;
- HubSpot or Twenty mapping;
- live enrichment, CRM writes, outreach, pilot or production use.

## Recorded decision

**Approved as drafted.** R1–R9 are approved and Step 2B may begin.

This is not approval of the JSON Schema, business field catalogue, integrations, pilot, production or contractual acceptance.
