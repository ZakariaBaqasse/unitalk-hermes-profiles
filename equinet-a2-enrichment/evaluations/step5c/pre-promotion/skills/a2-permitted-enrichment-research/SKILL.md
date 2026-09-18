---
name: a2-permitted-enrichment-research
description: Use when Equinet A2 must preflight a named source action.
---

# A2 Permitted Enrichment Research

## Delivery status

**Version:** `0.1.0-draft.1`  
**Status:** `WAVE 2 DRAFT — NOT APPROVED`

## Mission

Preflight one named, field-bounded source action against the active Source Register, Business Field Catalogue and Provider/Cost Policy. Step 5C may process local synthetic fixtures but performs no live source call.

## Authoritative dependencies

Resolve current files through `foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json`. Use the active Source Register and Provider/Cost Policy rather than prompt-supplied permissions.

## Inputs

A JSON request with candidate ID, operating scope, source ID, field key, named need and execution mode. Source-specific inputs include the official-site check state, synthetic fixture reference, named role gap, selected profile match and bounded limits.

## Command

```bash
/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python \
  /opt/data/profiles/equinet-a2-enrichment/scripts/preflight_a2_source_action.py \
  <request.json> --output <source-preflight.json>
```

## Source order

1. reuse the approved A1 handoff and evidence;
2. read HubSpot only when a permitted connection exists;
3. use authorised Equinet first-party data;
4. inspect the prospect-owned official site for a named gap;
5. consider the exact approved provider action only after the official-site gap and every rights, vendor, account, build, retention, budget and audit gate;
6. use search only to locate an official destination, never as retained field evidence.

## Official-site controls

A future bounded check may inspect at most five relevant public pages and one targeted retry per failed URL. It stops on terms/robots denial, login/paywall, CAPTCHA, HTTP 403/429, unexpected personal data or scope/budget limits. Explicit professional social links may be retained and attributed from the official page, but the linked social profile is not opened or extracted.

## Provider controls

`harvestapi/linkedin-profile-search` remains blocked. Prefer an exact company LinkedIn URL explicitly published on the official site, otherwise a verified company name plus target role. An individual profile URL follows a separate manual or separately approved profile-scraper route. Email search is a distinct action; it retains professional email only by default and never creates consent.

## Boundaries

- No second discovery crawl.
- No arbitrary approval token can activate a source.
- No live Web, Apify, HubSpot or other external call during Step 5C.
- No automatic query segmentation, provider fallback, social-profile opening, outreach or CRM write.
- A search snippet is discovery-only.
- Every result reports zero external calls/actions and preserves audit requirements.

## Outputs

A hashed preflight with source policy, field gate, runtime status, limits, stop conditions, missing provider gates, blocks, warnings, the required audit envelope and an explicit false external-call authorisation. A provider fixture may validate downstream handling while all live provider gates remain visible and blocked.

## Handoff

Only `allowed_local_fixture` or `allowed_local_reuse` data may enter the Step 5C field-verification fixtures. Future live execution requires Step 6 runtime controls and the applicable integration gate.
