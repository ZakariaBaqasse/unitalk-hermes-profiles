# Decision Review — Step 2G Handoff-to-Record Initialisation

**Version:** `0.1.0`  
**Status:** `APPROVED BY UNITALK OPERATIONS FOR STEP 2H`  
**Profile status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`  
**Technical validation:** PASS  
**Human decision:** APPROVED AS DRAFTED  
**Approver:** Séverine, Unitalk Operations  
**Decision timestamp:** `2026-08-26T12:32:41Z`

## 1. Technical result

| Check | Result |
|---|---:|
| Valid handoffs | 3/3 PASS |
| Invalid handoffs | 8/8 PASS |
| Fixture total | 11/11 PASS |
| Deterministic/idempotency controls | 15/15 PASS |
| Farrier and Horse Owner | PASS |
| Targeted-field request | PASS |
| Lossless source handoff | PASS |
| Empty A2 working containers | PASS |
| Different-content overwrite protection | PASS |
| External actions | 0 |
| Package manifest files | 25 |
| Independent post-fix review | PASS |

## 2. Output behaviour

A valid handoff creates one deterministic first revision containing the full immutable A1 input, resolved entities, pending review, unavailable integrations and no A2 evidence or assessments.

An identical retry produces canonical byte-identical output and returns `unchanged`. A local ledger rejects changed payloads reusing a handoff ID or idempotency key. Atomic file creation prevents concurrent different-content overwrite.

## 3. Rejected inputs

The suite rejects:

- unknown handoff properties;
- candidate snapshot hash mismatch;
- wrong target profile;
- synthetic handoff not accepted by A2;
- non-eligible handoff;
- recommendation other than `pass_to_a2`;
- provider authority during synthetic initialisation;
- synthetic data relabelled as manual no-integration production data.
- duplicate JSON keys and non-finite JSON numbers.

## 4. Limitation

The positive manual no-integration path remains untested until an approved real production handoff is supplied. No synthetic fixture is relabelled as production merely to make the test pass.

## 5. Decisions confirmed by Séverine

| ID | Decision |
|---|---|
| G1 | Validate the complete A1 handoff before initialisation. |
| G2 | Derive lineage from the handoff hash and revision/run IDs from the handoff plus contract versions. |
| G3 | Preserve the complete A1 handoff and candidate snapshot. |
| G4 | Create only A1-supported entities; do not assign ambiguous aliases or an unproven relationship. |
| G5 | Initialise empty A2 evidence, assessment and requalification containers. |
| G6 | Keep review pending and every external action/reference disabled. |
| G7 | Preserve targeted requests until the planning stage creates assessments. |
| G8 | Enforce strict JSON, ledger-backed idempotency, canonical bytes and atomic collision protection. |
| G9 | Defer the positive manual no-integration case until approved real input exists. |
| G10 | Proceed to Step 2H review-view specification after approval. |
| G11 | Approve the Step 2E and Step 2F compatibility corrections required by protected-review and targeted initialisation states. |

## 6. Recorded decision

**Approved as drafted.** G1–G11 are approved and Step 2H may begin.

This approval is limited to deterministic initialisation and the compatibility corrections in G11. It does not approve live sources, integrations, providers, CRM writes, outreach, pilot, production or contractual acceptance.
