# Decision Review — Step 1C A1-to-A2 Boundary and Handoff Contract

**Current contract version:** `1.0.1`  
**Original approval version:** `1.0.0`  
**Status:** `APPROVED BY UNITALK OPERATIONS FOR A2 FOUNDATION`  
**Decision:** APPROVED AS DRAFTED  
**Approver:** Séverine, Unitalk Operations  
**Original decision date:** `2026-08-16T15:56:49Z`  
**Clarification date:** `2026-08-16T16:10:17Z`  
**Profile status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`

## Technical result

| Check | Result |
|---|---:|
| Pinned A1 schema compared with source | PASS |
| Pinned A1 validator compared with source | PASS |
| Valid Farrier fixture | PASS |
| Valid Horse Owner fixture | PASS |
| Expected negative cases | 9/9 PASS |
| Total | 11/11 PASS |

The tests correctly reject:

- missing A1 human approval;
- a recommendation other than `pass_to_a2`;
- a possible duplicate incorrectly declared eligible;
- a modified snapshot or incorrect hash;
- a delivery claim during the no-integration pilot;
- CRM-write permission in a synthetic/no-integration context;
- an A2 receipt linked to the wrong handoff;
- duplicated or missing eligibility gates;
- an excluded candidate handed to A2.

## Approved responsibility boundary

### A1 remains the owner of

- identity and segment at the time of approval;
- A1 evidence;
- ICP qualification;
- scoring model and deterministic score calculation;
- original score, band, components and rationale;
- A1 confidence;
- recommendation and A1 approval.

### A2 may

- receive an immutable copy of the A1 candidate;
- reuse still-valid A1 data and evidence;
- add its enrichment to a separate A2 record;
- trigger requalification when verified new evidence materially affects an A1 criterion;
- receive the resulting approved A1 score-revision reference.

A2 does not retroactively modify the A1 snapshot and does not calculate the revised score.

## Approved decisions

| ID | Approved decision | Consequence |
|---|---|---|
| H1 | Include the complete immutable A1 Prospect Candidate in the handoff with deterministic SHA-256 integrity. | A2 receives a lossless copy and any modification is detectable. |
| H2 | Allow HubSpot/Twenty checks to remain unavailable for the manual no-integration pilot. | A2 can be tested while CRM write, outreach eligibility and production routing remain blocked. |
| H3 | Require `approved_for_a2`, decision `approved`, reviewer, timestamp and recommendation `pass_to_a2`. | A simple HubSpot creation or pending recommendation cannot trigger A2. |
| H4 | Treat confirmed exclusions/duplicates and invalid candidates as `blocked`; treat possible duplicates and unresolved material conflicts as `hold`. | Ambiguous cases cannot be accepted silently. |
| H5 | Keep the original A1 score, evidence and approval immutable. A2 may trigger requalification with verified new evidence; A1 alone creates a new deterministic score revision, subject to human approval. | The score can evolve without dual scoring ownership or silent overwrite. |
| H6 | Limit the manual no-integration pilot to `ready_for_delivery`. Only a durable integration may declare `delivered`, and only A2 may declare `accepted_by_a2`. | A prepared file cannot be presented as delivered or accepted. |

## Approved states

```text
prepared
→ ready_for_delivery
→ delivered
→ accepted_by_a2

Alternative outcomes:
rejected_by_a2 | delivery_failed | expired
```

For `manual_no_integration_pilot`, the maximum state is `ready_for_delivery`.

## Score revision lifecycle clarification

```text
A2 verifies material new evidence
→ A2 creates a requalification signal
→ A1 validates the evidence under A1 rules
→ A1 deterministic scoring creates a proposed new revision
→ a human reviewer approves or rejects the revision
→ the latest approved revision may become operationally current
```

The original A1 score and its approval history remain immutable.

## Limits of this approval

This decision does not approve:

- the canonical A2 Enrichment Record;
- final enrichment fields;
- minimum data packages;
- sources or providers;
- HubSpot, Twenty or n8n integrations;
- A2 confidence rules;
- a live pilot;
- CRM writes, outreach or production use.

## Recorded decision

**Approved as drafted**, with the later score-revision clarification recorded in version `1.0.1`.

This is not Equinet client sign-off, pilot approval, production approval or contractual acceptance.
