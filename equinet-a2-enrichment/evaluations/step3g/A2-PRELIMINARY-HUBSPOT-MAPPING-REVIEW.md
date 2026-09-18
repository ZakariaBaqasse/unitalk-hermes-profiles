# Decision Review — Step 3G Preliminary HubSpot Mapping

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED AS UNITALK WORKING BASELINE — LIVE VERIFICATION PENDING`  
**Decision timestamp:** `2026-08-27T09:09:39Z`

| ID | Proposed decision |
|---|---|
| 3G-1 | Use the supplied HubSpot property export as the preliminary metadata authority. |
| 3G-2 | Keep all directions read-and-propose only; approve no writes. |
| 3G-3 | Preserve populated manual CRM values and apply Step 3E conflict rules. |
| 3G-4 | Prefer `work_email` for professional email and treat primary `email` as a reviewed fallback. |
| 3G-5 | Keep personal-email candidates canonical review-only with no HubSpot mapping. |
| 3G-6 | Block `horse_count_range` mapping until overlapping options are resolved. |
| 3G-7 | Block `stable_type` mapping until the enum mismatch is resolved. |
| 3G-8 | Use segment-specific discipline candidates and require explicit enum conversion. |
| 3G-9 | Keep every mapped field at `workflow_dependency_unverified`. |
| 3G-10 | Require live read-only verification of values, associations, permissions and fill rates before final mapping approval. |

This approval establishes the Unitalk working baseline and authorises preparation of the final specialist SOUL in draft form. It does not connect HubSpot or authorise a write.
