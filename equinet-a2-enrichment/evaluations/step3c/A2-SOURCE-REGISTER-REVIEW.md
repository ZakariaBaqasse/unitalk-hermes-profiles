# Decision Review — Step 3C A2 Source Register

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED AS UNITALK WORKING BASELINE — RUNTIME ACTIVATION PENDING`
**Decision timestamp:** `2026-08-26T17:58:25Z`

## Decisions already captured

- Every retained Farrier and Horse Owner should have its official website checked when one exists.
- Equinet has approved the business use of `harvestapi/linkedin-profile-search` for A2.
- The Actor runs only after an official-site role/contact gap.
- Independent professional-email search through the Actor is included as a separately governed provider action.
- Search-engine discovery is permitted only to locate the official website.
- No additional A2 registry or association is selected beyond A1 evidence reuse.
- Apollo, Clay and other paid enrichment providers are not selected.

## Unitalk safeguards proposed

1. Reuse A1 evidence before new access.
2. Use the official website before LinkedIn.
3. Trigger the Apify Actor only for a named role/contact gap.
4. Start with name, current title, current company, location and profile URL, then review a bounded output before expanding the allowlist.
5. Treat email search as a separate provider action; retain professional email only by default and never label it as LinkedIn-sourced.
6. Limit each candidate to one search page, five returned profiles, three retained contacts and at most three email searches.
7. Keep concurrency at one and automatic query segmentation disabled.
8. Keep runtime blocked until rights, vendor, account, build, budget, retention and audit gates pass.
9. Keep Apollo, Clay and other enrichment providers unselected and unconnected.

## Decision scope

This approval establishes the Unitalk working baseline, not runtime activation. Rights, vendor, account, budget, retention and integration gates remain mandatory.
