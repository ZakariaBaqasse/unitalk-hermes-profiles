# Step 9 Pre-Freeze Review

**Profile:** `equinet-a2-enrichment`  
**Release candidate:** `equinet-a2-no-integration-1.0.0-rc.1`  
**Status:** `STARTED — PREFLIGHT CORRECTIONS REQUIRED`

## Baseline

- Step 8 acceptance: PASS and approved for Step 9.
- Skills: **10**, all with version `0.1.0`.
- Operators: **14** plus the local orchestrator.
- Active-foundation inventory: **70 files**; **5 hash mismatches**.
- Release-candidate inventory: **130 files**; missing **0**; unversioned **0**.

## Required correction propagation

| ID | Finding | Required action |
|---|---|---|
| S9-C1 | The active foundation manifest has stale hashes for SOUL.md and config.yaml after approved Step 8 closure changes. | Build a release-candidate active-foundation manifest with current hashes; do not overwrite the Step 8 historical snapshot. |
| S9-C2 | The active Step 6 runtime policy still describes synthetic-only real-data gates and a configured fallback, while the accepted Step 8 route used a named two-candidate policy with fallback disabled. | Create a consolidated no-integration runtime policy for the release; preserve the historical Step 6 and Step 8 policies. |
| S9-C3 | The Step 8 receipt helper omitted person.business_phone from its allowlist despite the authoritative catalogue permitting that field. | Retain the tested correction and verify the generic runtime preflight already permits the field; keep the Step 8 helper as pilot evidence rather than a core operator. |
| S9-C4 | The live pilot clarified that selected named contact and target-role priority are separate concepts. | Propagate unambiguous terminology to the runbook and review guidance; do not change the canonical field model. |
| S9-C5 | Normal A2 operation uses one consolidated final human review; intermediate pilot checks were implementation-test checkpoints only. | Verify SOUL, review skill and runbook consistently implement the single-final-review model. |
| S9-C6 | The Rood & Riddle replay used 234,533 tokens and 9 model API calls; cost remained unknown. | Record this as an optimisation baseline, reduce redundant path discovery and context loading, and do not treat unknown cost as zero. |
| S9-C7 | The Rood & Riddle accepted outcome proves that a High A1 score can coexist with an A2 held state when minimum-package evidence is incomplete. | Preserve held-gap behaviour and add it to the frozen acceptance tests and runbook. |
| S9-C8 | The non-interactive profile initially opened outside the requested relative workspace and performed two path-search recovery calls. | Use exact absolute profile paths in the frozen runbook and replay controller. |

## Freeze blockers

- Release-candidate active-foundation manifest not yet built.
- Consolidated no-integration runtime policy not yet built.
- Offline regression and exact accepted-record replay not yet run.
- Delivery documents and safe archive not yet built.
- Step 9 human approval not yet recorded.

## Boundary

No promotion has occurred. The profile remains **FOUNDATION CONFIGURED — NOT PILOT-READY**. No external action was performed.
