# Decision Review — Step 3D Evidence Policy

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED AS UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING`  
**Decision timestamp:** `2026-08-26T18:53:52Z`

## Decisions approved as the Unitalk working baseline

| ID | Proposed decision |
|---|---|
| 3D-1 | Use the six weighted dimensions `20/20/20/20/10/10`. |
| 3D-2 | Use High `80–100`, Medium `60–79`, Low `0–59`. |
| 3D-3 | Cap unresolved identity and material conflicts at `39`. |
| 3D-4 | Cap Required claims supported only by inference and stale time-sensitive claims at `59`. |
| 3D-5 | Give evidence from a source with an unmet rights/runtime gate a score of `0`. |
| 3D-6 | Let a current official website verify explicit self-controlled facts without a visible date. |
| 3D-7 | Keep search snippets discovery-only and preserve inherited A1 evidence confidence. |
| 3D-8 | Treat Apify email search as independent provider evidence; require identity/company match and never infer consent. |
| 3D-9 | Apply the proposed field freshness windows, subject to Equinet confirmation. |
| 3D-10 | Let verified material evidence trigger an A1 requalification signal without A2 calculating a score. |

## Deterministic cases

| Case | Source | Score | Confidence | Verification | Test |
|---|---|---:|---|---|---:|
| `official_site_current_role` | prospect_official_website | 96 | high | verified | PASS |
| `official_site_business_email` | prospect_official_website | 98 | high | verified | PASS |
| `apify_profile_runtime_blocked` | apify_harvestapi_linkedin_profile_search | 0 | low | unverified | PASS |
| `apify_email_verified_after_future_gate` | apify_harvestapi_email_search | 87 | high | verified | PASS |
| `undated_secondary_role` | a1_directory_evidence_reuse | 63 | medium | partially_verified | PASS |
| `inference_only_required` | prospect_official_website | 59 | low | unverified | PASS |
| `material_role_conflict` | prospect_official_website | 39 | low | contradicted | PASS |
| `stale_professional_status` | prospect_official_website | 59 | low | unverified | PASS |
| `search_snippet_discovery_only` | search_engine_discovery | 0 | low | unverified | PASS |
| `unresolved_identity` | prospect_official_website | 39 | low | unverified | PASS |

## Approval scope

This approval establishes the Unitalk working baseline and authorises preparation of Step 3E in draft form. It does not activate a source, provider, CRM action, outreach, pilot or production workflow.
