# Step 2G Independent Adversarial Review Resolution

**Status:** PASS AFTER CORRECTION  
**Scope:** Deterministic A1-handoff-to-A2-record initialisation

| Review finding | Resolution |
|---|---|
| Same revision IDs could represent different outputs | Lineage remains bound to the complete handoff hash; revision and run IDs also include schema and initialiser versions. The free Field Catalogue parameter was removed. |
| Handoff idempotency identifiers were not enforced | Added a locked local ledger binding both `handoff_id` and `idempotency_key` to the complete handoff digest and output IDs. Changed payload reuse is rejected. |
| Local writes were race-unsafe | Added canonical temporary-file creation and atomic exclusive linking. Concurrent different-content writes permit one winner only. |
| Duplicate JSON keys and non-finite values were accepted | Added strict parsing and `allow_nan=False`; invalid inputs create no output. |
| Byte determinism was not proven | Added sorted canonical output serialization and independent key-order byte-equality tests. |
| Runner could pass an incomplete case matrix | Added exact required valid/invalid case names, declared-count checks and CLI no-output checks for every invalid handoff. |
| Candidate aliases and evidence were assigned to unproven entities/relationships | Candidate-level aliases remain unassigned and no relationship is created without explicit relationship evidence. |

Post-fix verification:

- fixtures: `11/11 PASS`;
- deterministic/idempotency controls: `15/15 PASS`;
- canonical byte output: PASS;
- concurrent write and ledger tests: PASS;
- strict JSON tests: PASS;
- independent post-fix verdict: `PASS`;
- remaining critical/high findings: none.

No external service or action was used.
