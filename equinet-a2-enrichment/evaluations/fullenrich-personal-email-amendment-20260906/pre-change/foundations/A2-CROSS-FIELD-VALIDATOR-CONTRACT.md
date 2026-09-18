# Equinet A2 Deterministic Cross-Field Validator Contract

**Validator version:** `0.1.0`  
**Profile:** `equinet-a2-enrichment`  
**Step:** `2E — Deterministic Cross-Field Validator`  
**Status:** `APPROVED BY UNITALK OPERATIONS FOR STEP 2F`  
**Deployment language:** English

**Decision:** `APPROVED AS DRAFTED`  
**Approver:** Séverine, Unitalk Operations  
**Decision timestamp:** `2026-08-26T10:00:06Z`  
**Approved scope:** Step 2E decisions E1–E13, including corrective A2 schema `1.0.0-draft.2` and Step 2C lifecycle clarification `0.1.1`.

## 1. Purpose

This contract defines the deterministic validation layer applied after JSON Schema validation to an Equinet A2 canonical enrichment record.

The validator does not research, infer missing facts, calculate an A1 score, approve records, perform external actions or replace source-system permissions. It checks whether a record is internally consistent with the approved A1-to-A2 boundary, A2 state model, requalification contract and action controls.

## 2. Runtime interface

```text
validate_a2_enrichment_record.py RECORD
  [--previous-record PREVIOUS_RECORD]
  [--field-catalogue FIELD_CATALOGUE]
  [--output RESULT_JSON]
```

Validation order:

1. validate the record against `a2-enrichment-record.schema.json`;
2. stop cross-field evaluation if structural validation fails;
3. validate current-record invariants;
4. validate revision lineage and append-only history when a previous revision is supplied;
5. validate field keys and declared value types when an external Field Catalogue is supplied;
6. return machine-readable `valid` and `errors` fields;
7. exit with status `0` for valid and `1` for invalid.

The optional Field Catalogue remains an external configuration. The validator can consume it but does not embed it in the schema or source code.

## 3. Authoritative dependencies

- Canonical A2 JSON Schema `1.0.0`, promoted in Step 2I from the approved `1.0.0-draft.2` corrective proposal;
- A2 Canonical Record Design `0.1.0`;
- A2 Field Dictionary `0.1.0`;
- A2 State Model `0.1.0`;
- A1-to-A2 Handoff Contract and schema `1.0.1`;
- A2 Requalification and Score-Revision Data Contract approved baseline `0.1.0`, with corrective lifecycle clarification `0.1.1` included in this review;
- A1 Prospect Candidate schema `1.0.0`.

The validator uses only local pinned artifacts and performs no network or external-system action.

## 4. Handoff and identity integrity

The validator requires agreement between:

- the source-handoff wrapper and embedded handoff version, ID, idempotency key, scope, eligibility and candidate hash;
- the embedded candidate content and its SHA-256 hash;
- the canonical system references and authoritative A1 candidate/handoff IDs;
- the canonical audit correlation ID and the handoff correlation ID;
- the record kind, operating scope, candidate kind and handoff synthetic marker.

A canonical A2 record requires an eligible handoff. Synthetic or connected records require an accepted A2 receipt. The manual no-integration route may initialise only from an eligible handoff that is ready for delivery or accepted under a controlled process.

## 5. Entity and relationship integrity

The validator rejects:

- duplicate entity IDs;
- duplicate relationship IDs;
- relationships referencing unknown entities;
- field assessments referencing an unknown entity or relationship;
- a person or organisation assessment whose scope conflicts with the target entity type;
- record-level assessments carrying an entity ID.

## 6. Field-assessment integrity

The validator checks:

- unique field-assessment IDs;
- one assessment per scope, target and field key in a revision;
- unique observation IDs;
- evidence references for baselines, observations and proposals;
- a usable value when presence is `known`;
- no observations when availability is `not_checked`, `unavailable` or `not_found`;
- values and evidence for `add` or `update` proposals;
- a baseline for `retain` or `no_change` proposals;
- no replacement value in a `clear_request`;
- evidence for verified observations and proposals;
- an existing proposal before a reviewer can approve it.

When a Field Catalogue is supplied, the validator checks its version, approved key and declared value type without copying the catalogue into the canonical schema.

## 7. Evidence integrity

The validator maintains separate A1 and A2 evidence sets:

- A1 evidence IDs come from the immutable A1 candidate snapshot;
- A2 evidence IDs come from the A2 evidence registry;
- every field, relationship and requalification evidence reference must resolve to one of those sets;
- A2 evidence IDs must be unique;
- an `a1_reference` evidence entry must identify evidence present in the immutable handoff;
- evidence may support only field-assessment and requalification-signal IDs that exist in the same record.

The validator checks reference integrity. Field-specific source admissibility, corroboration, freshness and confidence calculations remain separate policies implemented later.

## 8. Data-quality and eligibility integrity

- Data-quality field lists must reference fields assessed in the record.
- Missing field keys must be a subset of required field keys.
- Duplicate-check IDs must be unique.
- A confirmed duplicate requires blocked A2 eligibility.
- A possible duplicate requires hold or blocked eligibility.
- `not_checked` and `unavailable` checks cannot claim a check timestamp.
- Completed duplicate results require a check timestamp.

## 9. Requalification integrity and A1-only scoring

For every A2 signal, the validator checks record, revision, candidate, handoff, candidate hash, audit correlation and synthetic markers against the canonical record.

Signal evidence and field-assessment references must resolve.

For every return, the validator checks:

- record and handoff identifiers;
- exact signal snapshots against canonical signals;
- deterministic signal-snapshot hash;
- unique return IDs.

For every A1 score-revision reference, the validator checks:

- candidate and correlation identity;
- referenced return and signal existence;
- A1 acceptance state for source signals;
- unique score-revision IDs;
- synthetic marker consistency.

JSON Schema and the Step 2C validator remain responsible for the detailed A1 scoring arithmetic. A2 cannot create points, a replacement score or a replacement band.

## 10. Review, protected-field and application integrity

An application in `pending`, `applied` or `reconciled` state requires:

- an approved field review;
- an approved record review;
- explicit CRM-write authorisation.

A protected update or clear request requires explicit field approval and a recorded approval-matrix version.

Successful external audit actions require both an approval reference and an external result reference.

## 11. Workflow and immutable revision integrity

Within a record, the validator checks the declared `previous_state → state` pair against the approved state model.

When the prior revision is provided, the validator also requires:

- the same `a2_record_id`;
- revision number incremented by exactly one;
- a new `record_revision_id`;
- `supersedes_revision_id` matching the prior revision;
- an unchanged complete `source_handoff`;
- `workflow.previous_state` matching the prior recorded state;
- evidence and audit collections to remain append-only;
- requalification payload fields to remain immutable while lifecycle states advance through approved transitions;
- prior observations not to be deleted or mutated.

The validator does not update an operational current-revision pointer.

## 12. No-integration ceiling

For `manual_no_integration_pilot`, the validator rejects:

- sync workflow states;
- active or completed field applications;
- delivered or processed requalification returns;
- A1 score-revision results;
- provider references, provider costs or provider calls;
- audit events claiming pending, successful or failed external actions.

The JSON Schema separately requires external connector references and action-authorisation flags to remain null or false in that scope.

## 13. Audit and consumption integrity

- Audit event IDs must be unique.
- Successful external actions require approval and action references.
- Aggregate token, call, credit and cost values must equal event totals when the underlying event values are fully available.
- Unknown cost remains unknown; it is not interpreted as zero-cost usage.

## 14. Error behaviour

- Validation errors are explicit and deterministic.
- No invalid record is automatically repaired.
- No failed validation triggers a retry, write, send or provider call.
- The caller decides whether to correct, hold, reject or escalate the record.
- Multiple errors may be returned for one record so the reviewer can correct the full set.

## 15. Technical test result

Initial deterministic suite:

| Test class | Result |
|---|---:|
| Valid cases | 7/7 PASS |
| Negative cases | 52/52 PASS |
| Total cases | 59/59 PASS |
| Pinned validator dependencies | 15/15 PASS |

The suite covers schema-first validation, embedded handoff gates, identifiers, hashes, entity and relationship graphs, bidirectional evidence references, source-policy eligibility, actual Field Catalogue value types, field proposals, protected fields, application and outreach gates, workflow transitions, human-review completeness, duplicate handling, data-quality summaries, complete requalification lifecycle/linkage and A1 score arithmetic, usage totals and append-only revision history.

The complete Farrier/Horse Owner business fixture matrix remains Step 2F.

An independent adversarial review identified and prompted correction of the draft.1 relationship-target constraint and additional hardening for embedded handoff validation, synthetic action ceilings, revision-chain requirements, lifecycle transitions, evidence references, provider authority, protected baselines, review completeness and A1 score-return linkage. These corrections are included in the reported test result.

## 16. Decisions confirmed by Séverine

| ID | Approved decision |
|---|---|
| E1 | Run strict JSON Schema validation before any cross-field checks. |
| E2 | Require handoff wrappers, hashes, candidate IDs, system references and audit correlation IDs to match their authoritative embedded values. |
| E3 | Require unique entity, relationship, field-assessment, observation, evidence, check, signal, return, score-revision and audit-event IDs where applicable. |
| E4 | Require all entity, relationship, field, evidence and requalification references to resolve inside the record or immutable A1 handoff. |
| E5 | Enforce baseline/observation/proposal/review/application consistency without inventing missing values. |
| E6 | Validate Field Catalogue version, key and declared value type only when the separate external catalogue is supplied. |
| E7 | Enforce data-quality list consistency and duplicate-to-eligibility gates. |
| E8 | Validate requalification signal/return/revision linkage while retaining A1 as the only numeric scoring authority. |
| E9 | Require recorded human decisions and CRM-write authority before an application can become active or complete. |
| E10 | Validate workflow transitions and immutable append-only history against a supplied prior revision. |
| E11 | Enforce synthetic/real separation and the manual no-integration action ceiling. |
| E12 | Reconcile audit usage where values are available and fail closed without repairing or executing actions. |
| E13 | Approve the corrective schema `1.0.0-draft.2` relationship target and Step 2C lifecycle clarification `0.1.1`. |

E1–E13 were approved as drafted by Séverine on `2026-08-26T10:00:06Z`. This authorises Step 2F fixture and regression expansion. It does not approve sources, providers, integrations, CRM writes, outreach, pilot, production or contractual acceptance.
