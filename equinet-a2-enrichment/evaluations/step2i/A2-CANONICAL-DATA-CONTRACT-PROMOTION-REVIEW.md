# Step 2I — Canonical Data Contract Review and Promotion

**Profile:** `equinet-a2-enrichment`  
**Review status:** `READY FOR SÉVERINE REVIEW — NOT PROMOTED`  
**Current schema:** `1.0.0-draft.2`  
**Proposed schema:** `1.0.0`  
**Profile status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`  

## 1. Decision requested

Approve or request changes to decisions I1–I10. No active schema, runtime artifact, integration or profile status has been promoted by preparing this package.

## 2. Verified prerequisite chain

| Gate | Result | Validation SHA-256 |
|---|---:|---|
| Step 1B | PASS | `e8c5594194eedb5825a91b96f30022f53338c25668037a1b52001d7dee42e363` |
| Step 2A | PASS | `81c5bb97408afede488681a61745ef4d6c819160b7ce0292be15a66d91fba76c` |
| Step 2B | PASS | `e056dc4aa12399a75a0e5f9d3cab277d8bca248ea53283cce5aa723968d13d36` |
| Step 2C | PASS | `9185fb1acfe21a25727657c8ef637fba0ac9cb267d36c84001a77634821d33fd` |
| Step 2D | PASS | `09fff71efb20647f60b65d7357b4360e4099c7814b40b9a77d12ea9f2c70e8d7` |
| Step 2E | PASS | `a9ad2cdcb9900502b8799285a4f86b09516e5ea74611db3837f511d2192e8773` |
| Step 2F | PASS | `30dc4e5142afe7a519ac42f6e79965a5703a3d7875cb97b1225d10c86e6890ba` |
| Step 2G | PASS | `65c23102652b72a4a149dc7a9ac0045c9287c150e839c3a51aa1dc4452a69cd7` |
| Step 2H | PASS | `b8e277b89c1e9076617774d201ef6a179fd8db5b6484b6369b35460db566ff6d` |

All approved foundation gates from Step 1B through Step 2H were rerun before this review. All passed. Step 2H explicitly authorises review at Step 2I.

## 3. Proposed promotion

The proposed `1.0.0` schema changes only four metadata paths from the approved `1.0.0-draft.2` schema:

- `$id`;
- schema description, removing the word `draft`;
- `record_metadata.schema_version.const`;
- `x-unitalk-contract.status`.

No canonical section, field, type, required rule, state vocabulary, external schema reference, no-integration ceiling or conditional rule changes.

## 4. Representative synthetic records

| Record | Segment | Workflow | Data quality | A2 eligibility | Review | Fields / evidence | Signals / returns / score refs | Proposed 1.0.0 validation |
|---|---|---|---|---|---|---:|---:|---:|
| `farrier_review_required` | farrier | review_required | review_ready | not_checked | pending | 6 / 2 | 0 / 0 / 0 | PASS |
| `farrier_conflict_held` | farrier | held | conflict | not_checked | held | 6 / 3 | 0 / 0 / 0 | PASS |
| `horse_owner_gap_held` | horse_owner | held | incomplete | not_checked | held | 3 / 0 | 0 / 0 / 0 | PASS |
| `horse_owner_requalification` | horse_owner | enrichment_planned | needs_review | not_checked | pending | 1 / 1 | 1 / 1 / 1 | PASS |
| `farrier_protected_update` | farrier | review_required | review_ready | not_checked | pending | 6 / 3 | 0 / 0 / 0 | PASS |
| `farrier_confirmed_duplicate` | farrier | blocked | incomplete | blocked | blocked | 6 / 0 | 0 / 0 / 0 | PASS |

The review set covers normal human review, conflict hold, gap hold, complete requalification, protected update and confirmed duplicate blocking. Each proposed copy differs from its approved synthetic source only at `record_metadata.schema_version`. Recorded external actions across the set: **0**.

## 5. Stable contract being promoted

- Fourteen required canonical sections.
- Immutable A1 handoff and immutable A2 revision lineage.
- Field flow: baseline → observations → proposal → human decision → application state.
- Separate A1 and A2 evidence namespaces.
- A1-only numeric scoring; A2 can only initiate evidence-backed requalification.
- Canonical JSON as the only lossless record.
- Read-only Markdown, CSV and Excel projections.
- Strict no-integration, approval, provider, CRM-write and outreach ceilings.

## 6. Configuration deliberately not promoted into the schema

The Business Field Catalogue, minimum data packages, source/provider policy, confidence/freshness rules, protected-field catalogue, approval matrix, CRM mapping, retention policy and operating quotas remain separate versioned configurations. They continue in Step 3 and later gates.

## 7. Atomic promotion plan after approval

1. Create a hashed pre-promotion evidence snapshot.
2. Promote the schema and active dependency manifest to `1.0.0`.
3. Update active validator, initialiser, review-view compatibility and synthetic fixtures together.
4. Regenerate all active manifests and review projections.
5. Run all Step 2D–2H deterministic suites plus the language audit.
6. Search active artifacts for stale draft references and unresolved pending-promotion markers.
7. Create the final Step 2I acceptance and promotion records with hashes.
8. Update the temporary SOUL and roadmap to Step 3A.

Files containing the draft identifier before promotion: **150**. Historical acceptance and review evidence will be preserved in the pre-promotion snapshot rather than silently reinterpreted.

## 8. Decisions for Séverine

| ID | Proposed decision |
|---|---|
| I1 | Promote the unchanged approved canonical structure from 1.0.0-draft.2 to 1.0.0. |
| I2 | Keep exactly fourteen required top-level sections and strict locally defined objects. |
| I3 | Keep the Field Catalogue, minimum packages, source/provider policy, confidence/freshness rules, protected-field catalogue, approval matrix, CRM mapping and retention policy outside the stable schema. |
| I4 | Preserve the complete A1 handoff and A1-only numeric scoring boundary; A2 may create evidence-backed requalification signals but cannot calculate scores. |
| I5 | Keep canonical JSON as the sole lossless record and Markdown, CSV and Excel as read-only derived views. |
| I6 | Promote dependent active tooling and synthetic test assets together, while preserving a hashed pre-promotion evidence snapshot. |
| I7 | Require all Step 2D–2H regression suites and the deployment-language audit to pass after promotion. |
| I8 | Keep all external integrations and actions disabled; schema promotion does not authorise enrichment, provider use, CRM access, writeback, outreach or pilot use. |
| I9 | Create a Step 2I acceptance record that pins the final schema, dependency manifest, validation and promotion evidence hashes. |
| I10 | After successful promotion, advance the next foundation gate to Step 3A — Business Field Catalogue. |

## 9. What this approval does not approve

- live prospect enrichment;
- source activation or paid-provider use;
- A1/A2 production delivery;
- HubSpot, Twenty or n8n access;
- CRM writeback;
- outreach;
- pilot readiness;
- production readiness;
- contractual acceptance.

## 10. Current technical conclusion

**PASS — ready for Séverine's Step 2I decision.** The active schema remains `1.0.0-draft.2` until explicit approval is recorded.
