# Step 2E Independent Adversarial Review Resolution

**Status:** CLOSED  
**Resolution scope:** Step 2E validator hardening plus two corrective foundation clarifications  
**Approval:** Covered by Séverine's approval of E1–E13 on `2026-08-26T10:00:06Z`

| Finding | Resolution |
|---|---|
| Requalification lifecycle conflicted with append-only history | Signal and return creation-revision IDs remain immutable. Existing artifacts may advance only through approved lifecycle transitions; immutable payload mutation is rejected. |
| Embedded A1 handoff received incomplete validation | The canonical validator now invokes the complete pinned A1 handoff cross-field validator. |
| Synthetic records could claim external writes | Synthetic CRM/provider authority, external-system references and active field applications are rejected. Canonical authority cannot exceed immutable handoff authority. |
| Later revisions could omit their predecessor or reuse a revision ID | Revisions after 1 require a previous record, exact sequence, a new revision ID and matching supersession reference. The prior record also receives cross-field validation. |
| Score revisions were not bound to their referenced return | Source signal IDs must be present in the referenced accepted return. Prior scoring must match the immutable A1 handoff or a retained prior A1 score revision. Step 2C arithmetic checks are reused. |
| Review and application claims were insufficiently derived | Field-decision completeness is recomputed. Blocked workflow/review alignment, failed attempts, application receipts and reconciliation evidence are checked. |
| Protected state could be downgraded | A protected baseline cannot be relabelled unprotected. External application requires explicit field approval and an approval-matrix version. Both clear-request value fields must be null. |
| Field Catalogue validation checked labels but not values | When supplied, the catalogue controls version, field key, segment applicability, declared type, normalised values and minimum-package required keys. |
| Evidence-reference coverage was incomplete | External-match, relationship, correction-chain, field and requalification evidence links are checked, including reciprocal support and source-policy state. |
| Relationship-scoped assessments were structurally impossible | Canonical schema `1.0.0-draft.2` permits `A2-REL-*` targets only for relationship scope. |
| Source-specific synthetic-domain logic was embedded in the validator | Removed. Source/content policy remains external and versioned. |
| Deployment-language verification was outside the suite | Retained as a separate package-level language audit; latest full regression requires it to pass. |

Post-resolution deterministic result: `59/59 PASS` for Step 2E before Step 2F expansion. No external action was performed.
