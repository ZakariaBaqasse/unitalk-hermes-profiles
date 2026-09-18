# Decision Review — Step 2C Requalification and Score-Revision Data Contract

**Version:** `0.1.0`  
**Status:** `APPROVED BY UNITALK OPERATIONS FOR STEP 2D`  
**Profile status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`  
**Technical validation:** PASS  
**Human decision:** APPROVED AS DRAFTED  
**Approver:** Séverine, Unitalk Operations  
**Decision date:** `2026-08-26T08:37:46Z`

## 1. Technical result

| Check | Result |
|---|---:|
| Pinned A1 dependencies | 4/4 hash matches |
| A1 criteria recognised | 26 |
| Weighted A1 criteria recognised | 21 |
| Strict schemas | 4/4 PASS |
| Valid fixtures | 5/5 PASS |
| Negative fixtures | 10/10 PASS |
| Total cases | 15/15 PASS |
| Language audit | PASS |

## 2. Contracts created

- A2 requalification signal;
- A2-to-A1 requalification return;
- A1 score-revision reference stored by A2;
- relationship package linking original score, signals, return and revision.

## 3. Approved ownership model proposed

```text
A2 discovers and verifies new evidence
→ A2 creates a requalification signal
→ A2 reviewer approves or rejects the signal
→ approved return is sent to A1
→ A1 validates evidence
→ A1 deterministic scoring creates a new revision
→ A1 reviewer approves or rejects the revision
→ approved revision may become operationally current
```

The original score remains immutable.

## 4. Hard controls

- A2 cannot include `points_awarded` in a signal.
- A2 cannot calculate a replacement score or band.
- The signal criterion must exist in A1.
- At least one traceable evidence reference is required.
- An approved return requires A2 human approval.
- A manual no-integration return cannot exceed `prepared`.
- A1 is the only permitted score-revision producer.
- Score components must use configured weights.
- Component total must equal score.
- Score delta must equal accepted criterion-change weight delta.
- An approved/rejected score revision requires matching A1 human review.
- Rejected signals cannot create a score revision.
- Package, signal, return and revision IDs/hashes must reconcile.

## 5. Synthetic example

```text
Original A1 score: 68 / medium
Horse-count criterion: unknown
A2 finds direct permitted evidence
A2 potential direction: increase
A2 numeric points: prohibited
A1 accepts evidence and applies weight: 20
A1 proposed revised score: 88 / high
A1 human review: required
```

The example proves that A2 can cause the score to evolve without becoming a second scoring authority.

## 6. No-integration boundary

For `manual_no_integration_pilot`:

- return status remains `prepared`;
- no external event reference;
- no A1 receipt;
- no claim that A1 processed the evidence;
- no score revision until a real A1 process or controlled synthetic test exists.

## 7. Decisions confirmed

| ID | Approved decision |
|---|---|
| C1 | Signal only for a real A1 criterion and with traceable evidence. |
| C2 | A2 may propose evidence status/direction only; no points, score or band. |
| C3 | A2 human approval before return to A1. |
| C4 | Manual no-integration return stops at `prepared`. |
| C5 | A1 alone validates evidence and produces the numeric revision. |
| C6 | Criterion changes, configured weights and score delta must reconcile. |
| C7 | A1 human review before a revision becomes approved/current. |
| C8 | Rejected signals do not change score and remain auditable. |
| C9 | Original and later score revisions remain immutable; supersession is operational only. |
| C10 | Idempotent retries and matching IDs/hashes/receipts. |

## 8. Deferred work

Approval of Step 2C does not approve:

- A1/A2 integration;
- A2 sources or providers;
- live requalification;
- HubSpot mapping or write;
- outreach;
- pilot or production use;
- contractual acceptance.

## 9. Recorded decision

**Approved as drafted.** C1–C10 are approved and Step 2D may begin.

This is not approval of integration, source access, CRM write, outreach, pilot, production or contractual acceptance.
