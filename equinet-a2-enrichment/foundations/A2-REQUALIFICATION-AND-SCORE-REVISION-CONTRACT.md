# Equinet A2 Requalification and Score-Revision Data Contract

**Current contract version:** `0.1.1`  
**Approved baseline:** `0.1.0`  
**Step:** `2C — Requalification and Score-Revision Data Contract`  
**Status:** `APPROVED BY UNITALK OPERATIONS WITH 0.1.1 LIFECYCLE CLARIFICATION`  
**Profile:** `equinet-a2-enrichment`

**Decision:** `APPROVED AS DRAFTED`  
**Approver:** Séverine, Unitalk Operations  
**Decision timestamp:** `2026-08-26T08:37:46Z`  
**Approved scope:** Requalification and score-revision decisions C1–C10. This is not approval of integration, source access, CRM write, outreach, pilot, production or contractual acceptance.

## 1. Purpose

This contract defines how verified evidence discovered by A2 may trigger a new A1 qualification and score revision without allowing A2 to calculate, overwrite or approve the A1 score.

It defines four structured artifacts:

1. `requalification_signal` — created by A2;
2. `requalification_return` — approved evidence payload sent to A1;
3. `a1_score_revision_reference` — deterministic result created by A1 and stored by A2;
4. `requalification_package` — relationship wrapper used for validation and audit.

This contract does not activate an A1/A2 integration, source, provider, CRM write, outreach workflow or production action.

## 2. Approved dependencies

The contract pins and verifies:

| A1 dependency | Version | SHA-256 |
|---|---:|---|
| Prospect Candidate schema | `1.0.0` | `cf4ea0b3729ecaa2b28fa5330917e32f5d911d5894c9c8d396095d6dcc3eb8de` |
| ICP configuration | `1.0.0` | `4d28bc35d11a458015f08903b30f0560f204476016508135fe2d126014f16169` |
| Evidence and confidence rules | `1.0.0` | `5cf2377814ccf3ee635bb279b512778924d2eb42bf1a0a58ec684d90c69c8f80` |
| ICP scoring model | `1.0.0` | `2bb426d73971509b7638ccfe55decb428b3fa11d5ce4b8d3bcc05418b6c75841` |

A changed A1 configuration requires compatibility review and a new Step 2C contract version before it is used.

## 3. Ownership boundary

| Information or action | Owner |
|---|---|
| New enrichment observation and evidence | A2 under an approved A2 source/evidence policy |
| Requalification signal | A2 |
| Signal review before return | Authorised A2 business reviewer |
| Evidence admissibility for ICP | A1 evidence rules |
| Criterion-state acceptance | A1 qualification workflow |
| Numeric points, score components, score and band | A1 deterministic scoring only |
| Score-revision approval | Authorised A1 business reviewer |
| Operational current-score pointer | Authorised A1/workflow layer after approval |
| Original score history | Immutable A1 handoff and revision history |

A2 may describe a potential score direction (`increase`, `decrease`, `unchanged` or `unknown`) but this is advisory. It must not calculate points, a replacement score or a replacement band.

## 4. Requalification trigger

A2 may create a signal only when permitted evidence materially affects an A1 criterion, for example:

- a previously unknown criterion becomes directly supported;
- previously accepted evidence is contradicted;
- a mandatory gate changes;
- an exclusion risk is discovered;
- a role, activity, scale or purchasing-influence fact materially changes;
- a stale fact is replaced by verified current evidence.

A2 must not create a signal merely because a profile contains more descriptive detail. The evidence must relate to a real A1 criterion ID.

## 5. `requalification_signal`

Each signal preserves:

- signal schema version and stable signal ID;
- A2 record and revision IDs;
- A1 candidate and handoff IDs;
- immutable A1 candidate snapshot hash;
- affected A1 criterion ID;
- prior criterion status;
- proposed evidence status;
- A1 evidence references reused from the handoff;
- new A2 evidence IDs;
- source field-assessment IDs;
- materiality;
- potential score direction;
- evidence-led reason and limitations;
- creator, timestamp and audit correlation ID;
- synthetic/production marker;
- signal review state and human decision.

### Signal states

```text
draft
→ pending_review
→ approved_for_return | rejected
→ sent_to_a1
→ accepted_by_a1 | rejected_by_a1
→ rescored
```

`error` is a controlled technical-failure state.

### Hard signal restrictions

- The criterion ID must exist in the pinned A1 ICP/scoring configurations.
- At least one A1 or A2 evidence reference is required.
- An approved/sent signal requires recorded human approval.
- A rejected signal cannot generate a score revision.
- The strict schema rejects `points_awarded`, replacement score, replacement band and other unapproved fields.

## 6. `requalification_return`

The return is the durable A2-to-A1 payload. It preserves:

- return schema version, ID and idempotency key;
- source/target profile;
- operating scope;
- A2 record/revision IDs;
- A1 candidate/handoff IDs and snapshot hash;
- target ICP, evidence and scoring versions;
- complete immutable approved signal snapshots;
- deterministic signal-snapshot hash;
- human approval;
- delivery state, attempt count and external event reference;
- A1 receipt or rejection reasons;
- constraints prohibiting A2 points and replacement scores;
- audit correlation and synthetic marker.

### Return states

```text
prepared
→ delivered
→ accepted_by_a1 | rejected_by_a1
```

Alternative technical outcomes:

```text
delivery_failed | error
```

### No-integration boundary

For `manual_no_integration_pilot`:

- the maximum state is `prepared`;
- there is no external event reference;
- delivery attempt count remains zero;
- A1 receipt remains null;
- A2 may export the validated payload for review but cannot claim A1 received it.

## 7. A1 evidence and criterion processing

When A1 receives an approved return, A1 must:

1. verify package integrity and idempotency;
2. verify candidate/handoff identity and snapshot hash;
3. verify the signal criterion exists;
4. validate new evidence under A1 evidence/source rules;
5. preserve rejected or inadmissible evidence with reasons;
6. calculate accepted criterion changes;
7. run the pinned deterministic A1 scorer;
8. produce a new score revision ID;
9. request the required human review;
10. return the revision result or rejection.

A1 may accept evidence without changing numeric score when the evidence affects a non-scoring pathway, routing or confidence only.

## 8. `a1_score_revision_reference`

A2 may store the authoritative A1 result containing:

- score-revision schema and revision ID;
- A1 candidate ID and prior revision ID;
- source return and signal IDs;
- A1 producer identity;
- deterministic calculation method;
- ICP, evidence and scoring versions;
- A1-validated evidence IDs;
- criterion changes before and after;
- prior and revised scoring snapshots;
- calculation timestamp;
- revision status;
- A1 reviewer, decision and timestamp;
- verifiable result reference and SHA-256;
- audit correlation and synthetic marker.

A2 does not edit this result. A correction requires a new A1 score revision.

### Lifecycle clarification proposed during Step 2E

`a2_record_revision_id` identifies the immutable A2 revision in which a signal or return was created. It is not rewritten when that artifact is retained in a later A2 revision. The later revision may advance only the approved lifecycle fields under deterministic transition controls. New signals and returns must identify the current creation revision. The Step 2C schemas remain `0.1.0` because their field shapes do not change.

This clarification was approved by Séverine, Unitalk Operations, through Step 2E decision E13 on `2026-08-26T10:00:06Z`.

### Revision states

```text
proposed_by_a1
→ approved | rejected
→ superseded
```

`error` records a technical failure.

An `approved` or `rejected` revision requires the matching A1 human-review decision.

## 9. Deterministic score checks

The Step 2C validator enforces:

- A1 is the producer;
- calculation method is deterministic A1 scoring;
- scoring/ICP/evidence versions match the pinned dependencies;
- every component criterion exists;
- component `max_points` equals the configured A1 weight;
- awarded points do not exceed configured weight;
- component total equals numeric score;
- raw score band matches the A1 model;
- score delta equals the accepted criterion-change weight delta;
- after-evidence is included in A1-validated evidence;
- revision signals match the package signals;
- result hash matches the revised scoring snapshot.

## 10. Synthetic example

Initial A1 state:

```text
horse_owner.more_than_three_horses = unknown
A1 score = 68
A1 band = medium
```

A2 finds a permitted direct statement that the synthetic operation manages more than three horses:

```text
A2 signal:
criterion = horse_owner.more_than_three_horses
prior status = unknown
proposed evidence status = confirmed
potential direction = increase
numeric points = prohibited
```

A1 accepts the evidence and applies the configured weight of 20:

```text
A1 revised score = 88
A1 revised band = high
```

The revision is not operationally current until the A1 reviewer approves it. The original score of 68 remains immutable history.

## 11. Rejected evidence behaviour

If A2 evidence is rejected because it is inadmissible, ambiguous, stale, identity-mismatched or source-blocked:

- the signal is marked rejected or rejected_by_a1;
- no new numeric score is recorded;
- the original A1 score remains current;
- reasons and evidence references remain in audit history;
- retry requires new or corrected evidence and a new immutable signal/revision path where applicable.

## 12. Idempotency and integrity

- Signal IDs are unique within a package.
- Return retries reuse the same return ID and idempotency key when payload content is unchanged.
- Changed signals require a new return version/ID and hash.
- Signal snapshot hash must match the exact ordered signal snapshots.
- Score result hash must match the exact revised scoring snapshot.
- Duplicate delivery must not duplicate A1 score revisions.
- A1 receipt must match return ID and signal hash.

## 13. Audit requirements

Record where applicable:

- A2 actor/profile/run/revision;
- A1 candidate/handoff/snapshot hash;
- signal IDs, field-assessment IDs and evidence IDs;
- A2 reviewer and decision;
- return ID, idempotency key, delivery and receipt;
- A1 evidence decision and rejected-evidence reasons;
- A1 scoring method/configuration versions;
- prior and new score revision IDs;
- A1 reviewer and decision;
- timestamps, model/tools, cost and external action references;
- success, failure, retry, hold, rejection and error states.

## 14. Schemas and fixtures

Schemas:

- `a2-requalification-signal.schema.json`;
- `a2-requalification-return.schema.json`;
- `a1-score-revision-reference.schema.json`;
- `a2-requalification-package.schema.json`.

Valid fixtures:

- Horse Owner signal;
- Farrier signal;
- manual no-integration prepared return;
- complete synthetic A2→A1→A2 score revision package;
- rejected-signal package with no revision.

Negative fixtures reject:

- A2 points;
- unknown criterion;
- missing evidence;
- false no-integration delivery;
- signal hash mismatch;
- A2 score production;
- score/component mismatch;
- approved revision without review;
- package/signal mismatch;
- rejected signal with score revision.

## 15. Open items

- Durable A2→A1 workflow and A1 receipt integration are not connected.
- A1 score-revision storage and operational-current pointer are not implemented.
- Named A2 reviewer and backup remain unconfirmed.
- A1 reviewer role exists but production approval assignment remains to be confirmed.
- A2 source register and field-specific evidence rules are not approved.
- Canonical A2 JSON Schema Step 2D is not yet created.
- No HubSpot field mapping or write is authorised.

## 16. Step 2C acceptance criteria

Step 2C is ready for approval when:

- all four schemas compile;
- dependencies match their pinned source hashes;
- valid signals, returns and packages pass;
- all negative cases fail for the expected reason;
- A2 cannot add points, score or band;
- A1-only deterministic scoring is enforced;
- no-integration return cannot claim delivery;
- rejected signals cannot change the score;
- original score and prior revisions remain traceable;
- all artifacts are in English;
- Séverine approves decisions C1–C10.

## 17. Decisions confirmed by Séverine

| ID | Approved decision |
|---|---|
| C1 | A2 may create a signal only for an existing A1 criterion and with at least one traceable A1/A2 evidence reference. |
| C2 | A2 may propose evidence status and potential direction only; points, replacement score and replacement band are prohibited. |
| C3 | An A2 reviewer must approve a signal before it can be included in a return to A1. |
| C4 | A manual no-integration return stops at `prepared` and cannot claim A1 delivery or receipt. |
| C5 | A1 validates evidence and is the only producer of numeric score revisions under the pinned scoring model. |
| C6 | A1 criterion changes and score delta must reconcile deterministically with configured weights and accepted evidence. |
| C7 | An A1 human review is required before a score revision becomes approved/operationally current. |
| C8 | Rejected signals/evidence do not change the current score and remain auditable. |
| C9 | Original score and all later revisions remain immutable; a later approved revision may supersede only operationally. |
| C10 | Return and score-revision retries are idempotent and require matching hashes, IDs and receipts. |

C1–C10 were approved as drafted by Séverine on `2026-08-26T08:37:46Z`. This authorises Step 2D Canonical A2 JSON Schema work. It does not activate A1/A2 integration, source access, provider use, CRM write, outreach, pilot, production or contractual acceptance.
