# Equinet A1-to-A2 Boundary and Handoff Contract

**Contract version:** `1.0.1`  
**Profiles:** `equinet-a1-icp-discovery` → `equinet-a2-enrichment`  
**Status:** `APPROVED BY UNITALK OPERATIONS FOR A2 FOUNDATION`  
**Parent contract:** `A2-IMPLEMENTATION-CONTRACT.md` version `0.1.1`  
**A1 candidate dependency:** `Equinet A1 Prospect Candidate` version `1.0.0`

**Decision:** `APPROVED AS DRAFTED`  
**Approver:** Séverine, Unitalk Operations  
**Decision timestamp:** `2026-08-16T15:56:49Z`  
**Approved scope:** Boundary decisions H1–H6 and permission to build the canonical A2 Enrichment Record. This is not Equinet client sign-off, pilot approval, production approval or contractual acceptance.

**Clarification record:** Séverine, Unitalk Operations, `2026-08-16T16:10:17Z`  
**Clarification:** A1 owns scoring. A2 may trigger requalification with verified new evidence. Any changed score is a new A1-generated, human-approved revision; the original handoff score remains immutable.

## 1. Purpose

This contract defines the exact boundary between A1 ICP Discovery and A2 Enrichment. It specifies:

- what A1 owns and must preserve;
- what A2 may add without changing A1 decisions;
- the approval and eligibility gates required before A2 can accept work;
- the structured handoff envelope;
- lifecycle state ownership;
- rejection, hold, retry and audit behaviour;
- the difference between a no-integration package and a delivered production event.

It does not define the complete canonical A2 Enrichment Record. That record is the next foundation deliverable.

## 2. Confirmed foundation

The following are already approved by Séverine in the A2 Implementation Contract:

1. the primary trigger is a recorded human A1 decision leading to `approved_for_a2`;
2. A2 preserves the A1 score and returns material new evidence for requalification instead of recalculating silently;
3. every enriched record requires human review during the pilot;
4. A2 cannot write to HubSpot or deliver a record to A3/A14 during the no-integration pilot.

A1 currently has no durable A2, HubSpot, Twenty or n8n integration. A1 may prepare a handoff package but must not claim delivery or acceptance by A2.

## 3. Responsibility boundary

| Information or decision | A1 ownership | A2 rights and duties |
|---|---|---|
| Candidate identity at A1 approval | Authoritative A1 snapshot | Preserve unchanged; create separate proposed corrections if new evidence appears |
| Segment and prospect type | A1 | Preserve; request requalification if material evidence conflicts |
| A1 evidence | A1 | Reuse without recollection when still applicable; never alter evidence text or IDs |
| ICP criteria and exclusion assessment | A1 | Read-only |
| ICP score, band, components and rationale | A1 deterministic scoring | Read-only; no silent recalculation |
| A1 confidence assessment | A1 deterministic method | Read-only; A2 later calculates separate enrichment confidence |
| A1 duplicate checks | A1 for the checks actually performed | Preserve statuses; A2 may run additional checks and record separate results |
| A1 human approval | A1/review layer | Validate before accepting the handoff |
| A1 recommendation | A1 | Must be `pass_to_a2` for an eligible handoff |
| Public professional contacts already found | A1 | Reuse and verify when needed; do not pay to recollect valid data by default |
| Broader role-relevant stakeholders | Outside normal A1 scope | A2 may enrich under the approved field, source and minimisation policies |
| New contact, role, service-area or equine information | Outside A1 snapshot | A2 records in its own canonical record with field-level evidence |
| Material evidence affecting ICP fit | A1 requalification and deterministic rescoring responsibility | A2 creates a requalification signal with evidence; it does not award points or mutate A1 fields |
| HubSpot patch | Outside A1 | A2 may prepare it later; guarded write remains approval-gated |
| Outreach eligibility and downstream routing | Outside A1 handoff approval | A2 must not infer it; future authoritative checks and human approval are required |

The A1 snapshot inside the handoff is immutable. A2 must never rewrite it to make later enrichment appear to have existed at A1 approval time.

## 4. Handoff operating scopes

| Scope | Purpose | Maximum permitted delivery state | Integration requirements |
|---|---|---|---|
| `synthetic_test` | Deterministic contract and behavioural fixtures | `accepted_by_a2` in an explicitly synthetic test harness | None; no live data or external action |
| `manual_no_integration_pilot` | Controlled file-based pilot with approved real records | `ready_for_delivery` | No delivery claim; no CRM write, outreach or paid provider unless separately approved |
| `integrated_pilot` | Event-driven pilot with durable shared state | `accepted_by_a2` | Approved staging, audit, n8n and required source-system checks |
| `production` | Approved operational workflow | `accepted_by_a2` and later A2 states | Full permissions, monitoring, approval, idempotency, cost and audit gates |

For `manual_no_integration_pilot`, unavailable HubSpot or Twenty checks do not automatically prohibit research-only A2 enrichment, but they must remain visible and they block CRM write, outreach eligibility and downstream production routing.

## 5. Handoff envelope

The handoff is a strict JSON envelope containing:

1. `handoff_schema_version`;
2. stable `handoff_id` and `idempotency_key`;
3. `source_profile` and `target_profile`;
4. `operating_scope` and `delivery_state`;
5. trigger event and recorded human approval;
6. eligibility result with deterministic gate outcomes;
7. requested enrichment scope;
8. an immutable full A1 Prospect Candidate snapshot;
9. snapshot integrity metadata;
10. integration-availability states;
11. enforced action constraints;
12. nullable A2 receipt;
13. audit provenance.

The full A1 candidate is carried so A2 receives a lossless, version-pinned snapshot. The handoff does not replace the A1 canonical record.

## 6. Primary trigger

The primary business trigger is:

```text
A1 reviewer records approval for enrichment
→ A1 candidate workflow.stage = approved_for_a2
→ A1 candidate workflow.review_decision = approved
→ A1 recommendation.next_action = pass_to_a2
→ handoff eligibility gates run
→ eligible envelope becomes ready_for_delivery
```

The future technical trigger must be a durable event or work-item state change. Free-form profile-to-profile conversation is not a production handoff.

A manual trigger for existing HubSpot or staging records remains outside this contract and disabled until separately approved.

## 7. Required approval event

The handoff approval event must include:

- decision `approved_for_enrichment`;
- reviewer actor ID and role;
- decision timestamp;
- source layer where the decision was recorded;
- optional source record ID;
- explicit scope `a2_enrichment`.

The reviewer, decision and timestamp must match the approval recorded inside the A1 candidate snapshot. A role-based reviewer is acceptable while the named Equinet approval matrix remains pending.

## 8. Eligibility decisions

The envelope has one of three eligibility results:

- `eligible`: all hard gates pass for the declared operating scope;
- `hold`: a human or authoritative-system check can resolve the issue without changing the candidate identity fundamentally;
- `blocked`: the candidate or action is prohibited, invalid or cannot safely progress.

### 8.1 Required gates

| Gate ID | `eligible` requirement | Hold or block behaviour |
|---|---|---|
| `candidate_schema` | A1 snapshot validates against candidate schema `1.0.0` and cross-field rules | Invalid → `blocked` |
| `human_approval` | stage `approved_for_a2`, decision `approved`, reviewer and timestamp present | Missing or inconsistent → `blocked` |
| `recommendation` | `recommendation.next_action = pass_to_a2` | Other action → `blocked` |
| `exclusion` | not `excluded` | `excluded` → `blocked`; unresolved review may be `hold` |
| `minimum_data` | `pass`, or an approved review pathway explicitly accepted by the reviewer | `fail` → `blocked`; unresolved `needs_review` → `hold` |
| `identity_quality` | data quality is not `invalid`; identity is sufficiently resolved under A1 rules | Invalid identity → `blocked`; unresolved material conflict → `hold` |
| `duplicate_batch` | no confirmed or possible duplicate in the current batch | Confirmed → `blocked`; possible → `hold` |
| `duplicate_exclusion_file` | no confirmed or possible match when the file check exists | Confirmed → `blocked`; possible → `hold`; unavailable remains visible |
| `source_policy` | no blocked source supports the candidate | Blocked-source dependency → `blocked` |
| `scoring_state` | A1 scoring is completed and not `blocked` | Blocked/not scored → `blocked` unless a later approved pathway says otherwise |
| `audit_identity` | A1 audit correlation ID exists | Missing → `blocked` |
| `scope_permissions` | requested scope does not require a prohibited source, action or unapproved spend | Violation → `blocked` |
| `hubspot_duplicate` | For integrated/production scope: authoritative result is acceptable | Possible → `hold`; confirmed → `blocked`; unavailable blocks only integrated/production delivery |
| `hubspot_eligibility` | For integrated/production scope: customer, Deal, partner, distributor, consent and suppression checks pass | Unavailable/uncertain → `hold`; prohibited class → `blocked` |

The deterministic validator must evaluate the gates from the snapshot and envelope. It must not accept narrative claims in place of the required states.

## 9. Delivery states and ownership

| State | Owner | Meaning |
|---|---|---|
| `prepared` | A1/manual builder | Envelope exists but eligibility has not passed |
| `ready_for_delivery` | A1/manual builder | Eligible for the declared scope; no delivery claim yet |
| `delivered` | Workflow/integration layer | Durable state accepted the event; A2 receipt not yet confirmed |
| `accepted_by_a2` | A2 | A2 validated and accepted the exact envelope |
| `rejected_by_a2` | A2 | A2 refused the envelope with structured reasons |
| `delivery_failed` | Workflow/integration layer | Technical delivery failed after bounded retries |
| `expired` | Workflow/integration layer | Envelope exceeded the approved validity window before acceptance |

State rules:

- `eligible` is required for `ready_for_delivery`, `delivered` and `accepted_by_a2`;
- `manual_no_integration_pilot` cannot progress beyond `ready_for_delivery`;
- `delivered` requires a durable external event reference;
- `accepted_by_a2` or `rejected_by_a2` requires an A2 receipt;
- `prepared`, `ready_for_delivery` and `delivered` require `a2_receipt = null`;
- a retry must reuse the same idempotency key and immutable snapshot;
- a changed snapshot requires a new handoff ID and idempotency key.

## 10. Hold, block and rejection behaviour

### Hold

A `hold` preserves the envelope for human or system resolution. Typical reasons include:

- possible duplicate;
- unresolved material identity conflict;
- minimum data requiring review without a matching approval pathway;
- unavailable authoritative HubSpot check in an integrated scope;
- uncertain customer, Deal, partner, distributor, consent or suppression state.

### Block

A `blocked` envelope must not be delivered. Typical reasons include:

- invalid A1 candidate;
- no valid human approval;
- confirmed exclusion or duplicate;
- failed minimum data without approved exception;
- blocked-source dependency;
- prohibited requested action;
- missing audit identity;
- A1 scoring blocked;
- unapproved provider or spend required.

### A2 rejection

A2 may reject a technically delivered envelope only with structured reason codes, timestamp and receiver identity. Rejection does not alter the A1 snapshot. A corrected resubmission requires either:

- the same envelope and idempotency key when only the transient delivery failed; or
- a new handoff ID and snapshot hash when candidate content, approval or requested scope changed.

## 11. Immutable A1 snapshot and new A2 evidence

A2 must preserve:

- A1 candidate ID and run ID;
- schema, ICP, confidence and scoring versions;
- evidence IDs, URLs, excerpts and retrieval dates;
- score, band, components and rationale;
- approval actor, decision and timestamp;
- duplicate and exclusion states;
- audit correlation ID.

A2 records all new facts and corrections in its own future canonical record. If new evidence materially affects A1 identity, segment, exclusion, qualification or scoring, A2 creates a structured `requalification_signal`. A later workflow packages the approved signal and evidence as a `requalification_return` to A1. A2 does not modify the embedded A1 snapshot.

### 11.1 Score revision lifecycle

```text
A2 verifies material new evidence
→ A2 creates a requalification_signal
→ A1 validates the evidence under A1 rules
→ A1 deterministic scoring creates a proposed new revision
→ human reviewer approves or rejects the revision
→ latest approved revision may become operationally current
```

The original A1 score, components, evidence and approval carried in the handoff remain immutable. A new approved score must have a distinct revision ID and preserve its relationship to the original candidate and prior score revision. A2 may initiate this process but does not calculate or approve the score revision.

## 12. Requested enrichment scope

The handoff may request:

- `default_minimum_package`; or
- `targeted_fields` with explicit field paths and a reason.

The final field catalogue and Horse Owner/Farrier minimum packages are not approved in this step. Requested fields are therefore strings validated for structure, not proof that a provider, source or CRM field is authorised.

The handoff cannot request:

- outreach or sequence enrolment;
- CRM write or deletion;
- A1 score change;
- owner or territory assignment without approved rules;
- restricted-source access;
- unapproved paid enrichment.

## 13. Integration visibility

The envelope must explicitly record the availability of:

- HubSpot read;
- Twenty or alternative staging;
- n8n/durable workflow;
- enrichment provider;
- email verification provider;
- phone verification provider.

Allowed states are `connected`, `unavailable`, `not_checked` and `error`. `connected` is not evidence that the current user has the required scope; permission checks remain separate.

For the current foundation and no-integration path, every integration is `unavailable` or `not_checked`.

## 14. Action constraints carried in every envelope

Every handoff must state and enforce:

- the A1 score inside the handoff is immutable in A2; any change requires a separate A1-generated, human-approved score revision;
- human review is required before use of enriched data;
- no outreach is authorised;
- no CRM write is authorised in `synthetic_test` or `manual_no_integration_pilot`;
- no downstream A3/A14 delivery is authorised in the no-integration pilot;
- no paid provider is authorised unless a separate approval reference exists;
- public information does not establish consent.

These constraints are machine-validated, not narrative guidance only.

## 15. Idempotency and integrity

- `handoff_id` identifies one immutable handoff version.
- `idempotency_key` prevents duplicate delivery or paid processing.
- `candidate_snapshot_sha256` is calculated from the canonical sorted UTF-8 JSON representation defined by the validator.
- the snapshot hash must match before A2 accepts the work;
- retries use the same handoff ID, idempotency key and hash;
- any changed approval, candidate snapshot or requested scope creates a new handoff version;
- acceptance records the accepted handoff ID and hash.

## 16. Audit and provenance

The handoff records:

- source and target profiles;
- builder/trigger actor;
- reviewer and approval time;
- candidate and A1 run IDs;
- handoff and idempotency IDs;
- audit correlation ID;
- operating scope and delivery state;
- all gate results and reasons;
- integration states;
- snapshot hash and schema version;
- requested enrichment scope;
- A2 receipt when applicable;
- external event reference for real delivery;
- failure, retry or expiry state.

No field may imply delivery or A2 acceptance without the required durable reference or receipt.

## 17. No-integration behaviour

During the no-integration pilot:

1. an approved A1 fixture or candidate snapshot may be packaged manually;
2. the envelope is validated deterministically;
3. the maximum state is `ready_for_delivery`;
4. A2 may later consume the file only in a separately controlled manual test;
5. the source package cannot claim `delivered` or `accepted_by_a2`;
6. no HubSpot/Twenty status is inferred;
7. no outreach, CRM write, downstream delivery or paid call occurs;
8. all unresolved authoritative checks remain visible in the package and review.

Synthetic contract fixtures may use `accepted_by_a2` only to test receipt-state validation and must remain explicitly synthetic.

## 18. Acceptance criteria for Step 1C

Step 1C is technically valid when:

- the pinned A1 candidate schema copy matches the A1 authoritative schema hash;
- the handoff JSON Schema compiles;
- valid Farrier and Horse Owner envelopes pass;
- invalid or inconsistent approval, recommendation, duplicate, exclusion, hash, scope and delivery states fail for the expected reason;
- no-integration fixtures cannot claim delivery or CRM/outreach permission;
- candidate snapshot IDs and approval metadata remain consistent with the envelope;
- the human-readable contract, schema, validator and fixtures use the same approved version.

Step 1C was approved by Séverine after technical validation of the decisions below.

## 19. Decisions confirmed by Séverine

| ID | Approved decision |
|---|---|
| H1 | Carry the full immutable A1 Prospect Candidate snapshot inside the handoff envelope, with a deterministic SHA-256 integrity value. |
| H2 | Allow unavailable HubSpot/Twenty checks for `manual_no_integration_pilot`, while blocking CRM write, outreach eligibility and production routing. |
| H3 | Require `approved_for_a2`, human decision `approved`, reviewer, timestamp and A1 recommendation `pass_to_a2` before eligibility. |
| H4 | Treat confirmed exclusions/duplicates and invalid candidates as `blocked`; treat possible duplicates and unresolved material conflicts as `hold`. |
| H5 | Keep the original A1 score, evidence and approval immutable. A2 may trigger requalification with verified new evidence; A1 alone creates a new deterministic score revision, subject to human approval. |
| H6 | Cap the manual no-integration handoff at `ready_for_delivery`; only a durable integration may claim `delivered`, and only A2 may claim `accepted_by_a2`. |

H1–H6 were approved as drafted by Séverine on `2026-08-16T15:56:49Z`. This authorises progression to the canonical A2 Enrichment Record. It does not authorise live enrichment, integrations, pilot use, CRM writes, outreach, provider spend, production or contractual acceptance.
