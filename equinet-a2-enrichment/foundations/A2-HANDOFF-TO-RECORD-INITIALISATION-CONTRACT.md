# Equinet A2 Handoff-to-Record Initialisation Contract

**Initialiser version:** `0.1.0`  
**Profile:** `equinet-a2-enrichment`  
**Step:** `2G — Handoff-to-Record Initialisation`  
**Status:** `APPROVED BY UNITALK OPERATIONS FOR STEP 2H`  
**Canonical schema:** `1.0.0` — promoted in Step 2I  
**A1-to-A2 handoff schema:** `1.0.1`

**Decision:** `APPROVED AS DRAFTED`  
**Approver:** Séverine, Unitalk Operations  
**Decision timestamp:** `2026-08-26T12:32:41Z`

## 1. Purpose

This contract defines the deterministic creation of the first canonical A2 record revision from an approved A1-to-A2 handoff.

The initialiser performs no research, model call, provider call, CRM access, outreach or downstream delivery. It writes only the requested local canonical JSON artifact.

## 2. Input gate

Before initialisation, the complete pinned A1-to-A2 handoff validator must pass, including:

- JSON Schema and A1 candidate validation;
- candidate snapshot SHA-256;
- A1 approval and `pass_to_a2` recommendation;
- all eligibility gates;
- target profile;
- action constraints;
- delivery state and receipt;
- audit correlation and synthetic/production consistency.

Synthetic, integrated and production handoffs require `accepted_by_a2`. The manual no-integration pathway requires `ready_for_delivery` and a real production candidate. A positive manual fixture remains pending until an approved real handoff exists.

## 3. Deterministic identity

The initialiser calculates a canonical SHA-256 of the complete handoff. The first twenty uppercase hexadecimal characters create:

- the stable A2 lineage ID;
- the first revision ID;
- the initialisation run ID.

The same handoff always produces the same IDs and byte-equivalent canonical record. A materially different handoff produces a different lineage ID.

## 4. Lossless source preservation

The output stores the complete handoff unchanged in `source_handoff.handoff_snapshot`. The A1 candidate snapshot, approval, score, evidence, duplicate checks, constraints, receipt and provenance therefore remain available without a live integration.

A person and organisation present in the A1 identity become separate A2 entities. Candidate-level aliases are not assigned to either entity, and no relationship is created without explicit relationship evidence. The complete original identity remains available in the immutable handoff.

## 5. Initial record state

The first revision is initialised with:

- `revision_number: 1`;
- no superseded revision;
- workflow `initialised` and no previous state;
- empty A2 evidence and field-assessment arrays;
- empty requalification arrays;
- record review `pending`;
- data quality `unassessed`;
- A2 eligibility `not_checked`;
- outreach eligibility `unavailable`;
- owner routing `needs_owner_review`;
- all HubSpot, Twenty, n8n, provider and downstream references null;
- outreach, CRM write and provider permissions false;
- one deterministic audit event and zero external-call consumption.

Requested targeted field keys may be preserved while assessments remain empty only in the `initialised` state. The later planning stage must create the corresponding assessments.

## 6. Idempotent local write

- First write to a new path returns `created`.
- An identical retry returns `unchanged`.
- Different content at an existing path is never overwritten.
- An atomic local ledger binds both `handoff_id` and `idempotency_key` to the complete handoff digest and output IDs.
- Reuse of either identifier with changed payload content is rejected.
- Concurrent different-content writers cannot both succeed.
- Input JSON with duplicate keys, `NaN` or infinite values is rejected before output creation.
- Canonical sorted serialization makes output bytes independent of input key order.
- Invalid input produces no output artifact.
- The CLI returns exit code `0` for a valid created/unchanged result and `1` for failure.

## 7. Technical result

| Check | Result |
|---|---:|
| Valid handoff cases | 3/3 PASS |
| Invalid handoff cases | 8/8 PASS |
| Total fixture cases | 11/11 PASS |
| Deterministic/idempotency controls | 15/15 PASS |
| Farrier output | PASS |
| Horse Owner output | PASS |
| Targeted-field output | PASS |
| Lossless handoff preservation | PASS |
| Empty A2 working containers | PASS |
| External actions | 0 |
| Package manifest files | 25 |
| Independent post-fix review | PASS |

## 8. Known limitation

The `manual_no_integration_pilot` positive pathway is implemented but not positively exercised because no approved real production handoff is available. The suite explicitly rejects relabelling a synthetic candidate as manual/production data.

## 9. Decisions confirmed by Séverine

| ID | Approved decision |
|---|---|
| G1 | Require the complete pinned A1 handoff validator to pass before initialisation. |
| G2 | Derive the A2 lineage ID from the complete handoff hash and derive revision/run IDs from the handoff hash plus schema and initialiser versions. |
| G3 | Preserve the complete handoff and A1 candidate snapshot without modification. |
| G4 | Create person and organisation entities only from identities present in A1; do not assign ambiguous aliases or create an unproven relationship. |
| G5 | Initialise empty A2 evidence, assessment and requalification containers. |
| G6 | Keep review pending, data quality unassessed and all external permissions/references unavailable or false. |
| G7 | Preserve targeted field requests while deferring assessment creation to the planning stage. |
| G8 | Use a locked idempotency ledger and atomic local writes; reject identifier reuse, concurrent different content and invalid JSON. |
| G9 | Keep the manual no-integration positive pathway pending until an approved real handoff exists. |
| G10 | Proceed next to Step 2H review-view specification after approval. |
| G11 | Approve the Step 2E and Step 2F compatibility corrections required by pending protected proposals and targeted fields in the `initialised` state. |

G1–G11 were approved as drafted by Séverine on `2026-08-26T12:32:41Z`. This authorises Step 2H. It does not approve live data access, integrations, providers, CRM writes, outreach, pilot, production or contractual acceptance.
