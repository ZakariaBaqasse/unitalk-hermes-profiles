# Decision Review — Step 3H Twenty Review Layer

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
| `valid_approved` | valid | PASS |
| `valid_needs_changes` | valid | PASS |
| `valid_held` | valid | PASS |
| `valid_rejected` | valid | PASS |
| `missing-reviewer` | invalid | PASS |
| `hubspot-write` | invalid | PASS |
| `wrong-hash` | invalid | PASS |
| `approved-pending-field` | invalid | PASS |
| `approval-scope` | invalid | PASS |
| `changed-without-revision` | invalid | PASS |
| `duplicate-field-id` | invalid | PASS |
| `missing-twenty-id` | invalid | PASS |

This approval establishes the Unitalk working baseline and authorises preparation of the final specialist SOUL in draft form. Exact Twenty workspace mapping and runtime activation remain pending.
