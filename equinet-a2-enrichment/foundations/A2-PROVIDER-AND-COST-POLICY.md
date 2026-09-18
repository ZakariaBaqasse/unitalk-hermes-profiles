# Equinet A2 Provider and Cost Policy

**Version:** `0.1.1-draft.1`  
**Status:** `APPROVED UNITALK WORKING BASELINE — RUNTIME ACTIVATION PENDING`  
**Decision timestamp:** `2026-08-26T20:26:01Z`  
**Step:** `3F — Provider and Cost Policy`

## Current provider scope

- Apify `harvestapi/linkedin-profile-search` for bounded role/company matching after an official-site gap. Prefer an exact LinkedIn company URL explicitly published on the official website; use verified company name plus target role only as fallback.
- An individual LinkedIn profile URL is reserved for authorised human review or a separately approved `harvestapi/linkedin-profile-scraper` action; it is not an input to the selected profile-search route.
- The same Actor's independent email-search mode as a separately governed action.
- Apollo and Clay remain under Equinet evaluation and are not selected.

## Personal email review

A personal email returned by the independent search may be retained only as `held_for_human_privacy_review`. Before review it cannot satisfy professional contactability, be written to CRM, be used for outreach or be represented as LinkedIn-sourced. Review may approve recorded business use, reject and delete it, or hold it for more evidence. Retention remains pending.

## Cost controls

The contractual USD 5,000 Advance Token Credit is a hard aggregate ceiling and may never become negative. A2-specific test, daily and pilot caps, spend approver and consumption owner remain unset; therefore provider execution remains blocked. Warnings occur at 50%, escalation at 80% and hard stop at 100% of an approved cap.

## Execution controls

- Reuse a successful idempotent result.
- No retry for `not_found`, policy block or budget block.
- Maximum one retry for a transient technical failure.
- No automatic fallback to Apollo, Clay or another provider.
- Record provider action, candidate, field, run, usage, cost, result and approval.

## Benchmark

Use ten approved candidates across Farrier and Horse Owner. Measure identity and role/company precision, professional-email precision, segment coverage, false positives, provenance, latency and cost per usable verified field. Acceptance thresholds are set only after reviewing the first bounded output.

## Remaining activation inputs

1. Apify workspace/account, runtime owner and credential route.
2. Pinned Actor build.
3. Rights or documented exception.
4. HarvestAPI vendor/privacy review.
5. Raw-result retention period.
6. Test, daily and pilot USD caps.
7. Spend approver and consumption owner.
8. Personal-email review owner and final outcomes.

Séverine approved decisions 3F-1 through 3F-10 as the Unitalk working baseline. No provider execution or spend is authorised.
