# Decision Review — Step 3F Provider and Cost Policy

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED AS UNITALK WORKING BASELINE — RUNTIME BLOCKED`  
**Decision timestamp:** `2026-08-26T20:26:01Z`

| ID | Proposed decision |
|---|---|
| 3F-1 | Limit current provider scope to Apify profile search and its separately governed email-search action. |
| 3F-2 | Keep Apollo, Clay and other providers unselected pending Equinet tests. |
| 3F-3 | Keep all monetary caps and approvers pending; block runtime while any required value is missing. |
| 3F-4 | Use a ten-candidate benchmark with the existing per-candidate source limits. |
| 3F-5 | Reuse successful idempotent results, use no retry for not-found or blocked outcomes, and allow one transient technical retry. |
| 3F-6 | Prohibit automatic fallback to another provider. |
| 3F-7 | Hold personal emails for human privacy review; do not use them operationally before approval. |
| 3F-8 | Attribute provider email to the independent HarvestAPI search, not LinkedIn. |
| 3F-9 | Require daily visibility, monthly statements and a hard stop before any approved cap or prepaid balance is exceeded. |
| 3F-10 | Keep runtime blocked until account, rights, vendor, retention, budget, audit and connector gates pass. |

This approval establishes the Unitalk working baseline and authorises Step 3G draft preparation. It does not authorise provider execution or spend.
