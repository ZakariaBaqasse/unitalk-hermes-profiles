# Foundation Clarification — Official-Site Social Profile URL Capture

**Profile:** `equinet-a2-enrichment`  
**Status:** `APPROVED AND APPLIED`  
**Approved by:** Séverine, Unitalk Operations  
**Approved at:** `2026-08-27T11:40:17Z`  
**Decisions:** `SOC-1` through `SOC-8`  
**Active configuration version:** `0.1.1-draft.1`

## Purpose

This clarification makes explicit how A2 retains professional social-profile links published on a prospect's official website and how those links may support a later, separately authorised role-search workflow.

It does not activate social-platform extraction, Apify, HubSpot, Twenty, n8n, outreach or any external action.

## Approved decisions

| ID | Decision |
|---|---|
| SOC-1 | Retain professional social-profile URLs explicitly published on the official website. |
| SOC-2 | Keep person and organisation profile URLs separate and hold ambiguous attribution for review. |
| SOC-3 | Keep both URL fields optional for Farrier and Horse Owner. |
| SOC-4 | Do not open or extract linked social profiles automatically during the official-site check. |
| SOC-5 | Prefer an exact LinkedIn company URL for the future profile-search Actor; use verified company name plus target role as fallback. |
| SOC-6 | Route an individual LinkedIn profile URL to human review or a separately approved profile-scraper action. |
| SOC-7 | Keep broad social signals, followers, posts, connections and personal interests out of scope. |
| SOC-8 | Do not infer consent, outreach eligibility or buying influence from a social-profile URL. |

## Resulting operating rule

```text
Approved A1 handoff and evidence
→ authorised baseline systems when available
→ bounded official-site check
→ retain explicit professional social-profile URLs only
→ identify a remaining named role/contact gap
→ prefer an exact LinkedIn company URL for a future approved profile-search action
→ otherwise use verified company name plus target role
→ human review
```

An individual LinkedIn profile URL is not passed to the selected `harvestapi/linkedin-profile-search` route. It is retained for authorised human review or a separately approved `harvestapi/linkedin-profile-scraper` action.

## Canonical fields

- `person.public_profile_urls` — optional for both segments.
- `organisation.public_profile_urls` — optional for both segments; added by this clarification.
- `person.social_signals` — remains `do_not_collect` for both segments.

The canonical JSON Schema remains `1.0.0`. The generic field-assessment architecture already supports the added business-catalogue key.

## Updated active artifacts

- Business Field Catalogue `0.1.1-draft.1`.
- Minimum Data Packages `0.1.1-draft.1`; package requirements unchanged.
- A2 Source Register `0.1.1-draft.1`.
- Evidence, Verification, Confidence and Freshness Policy `0.1.1-draft.1`.
- Protected Fields and Conflict Policy `0.1.1-draft.1`; dependency refresh only.
- Provider and Cost Policy `0.1.1-draft.1`.
- Preliminary A2-to-HubSpot Mapping `0.1.1-draft.1`.
- Active `SOUL.md`.
- Delivery Status and Ordered Roadmap `1.1.1`.

The accepted `0.1.0-draft.1` artifacts and Step 3 acceptance records remain unchanged. Pre-amendment copies of active mutable documents are retained in this clarification package.

## Unchanged controls

- Apify runtime remains blocked.
- LinkedIn automated extraction remains blocked.
- Other social-platform automation remains blocked.
- Public profile URLs do not establish consent or outreach eligibility.
- Public profile URLs do not establish buying influence or alter the A1 score.
- HubSpot write remains blocked.
- No Minimum Data Package requirement changed.
- No external action occurred.

## Validation

The deterministic clarification suite executes the real URL classifier and checks:

- person and organisation URL separation;
- optional priority for both segments;
- official-site URL-only collection;
- ambiguous attribution hold;
- exact LinkedIn company URL input preference;
- company-name-plus-role fallback;
- individual profile URL routing;
- broad social-signal prohibition;
- no consent, outreach or buying-influence inference;
- continued Apify runtime block;
- dependency hashes and CSV fidelity;
- historical Step 3A and Step 3C acceptance integrity;
- English-only stored profile artifacts.

See `technical-validation.json`, `fixtures.json`, `manifest.json` and `acceptance-record.json` in this directory.

## Next gate

`Step 5A — Operational Skill Architecture and Runtime Manifest`, followed by Wave 1 — Intake and Identity.
