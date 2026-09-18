---
name: a2-permitted-enrichment-research
description: Use when Equinet A2 must preflight a named source action.
---

# A2 Permitted Enrichment Research

## Delivery status

**Version:** `0.3.2`  
**Status:** `IMPLEMENTED LOCALLY — STEP 11 LIVE ACTIVATION PENDING`

## Mission

Preflight one named, field-bounded source action against the active Source Register, Business Field Catalogue, provider contracts and Provider/Cost Policy. The current runtime permits bounded Twenty–FullEnrich integration validation; the Step 11 Firecrawl and official-Facebook Apify paths remain live-acceptance gated.

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
3. inspect the prospect-owned official site through the bounded Firecrawl skill for Company contacts, social URLs and named People;
4. use the separately gated official-Facebook Apify Actor only for Company email/phone still missing after A1/Twenty plus website evidence;
5. use FullEnrich People Search when no suitable named contact exists, or People Lookup when a known contact still needs identity/current-role verification;
6. use FullEnrich Contact Enrichment only for selected contacts and request work email plus mobile, never personal email;
7. use search only to locate an official destination, never as retained field evidence.

Equinet has no separate first-party enrichment dataset.

For horse count, preserve this precedence: an existing matched HubSpot `Contact.owner_horse_count` is authoritative; a net-new prospect or empty HubSpot value may use only an explicit count from the approved A1 handoff, recorded Equinet confirmation or the prospect-owned official website. Equinet has no separate first-party enrichment dataset. Never infer the count, use `horse_count_range` or create a new `horse_count_band`.

## Official-site controls

The bounded connector may inspect at most five relevant public pages and stops on terms/robots denial, login/paywall, CAPTCHA, HTTP 403/429, unexpected personal data or scope limits. It uses Firecrawl with `onlyMainContent=false`, same-domain page selection and environment-only credentials. Explicit professional social links may be retained and attributed from the official page, but linked profiles are not opened except the separately gated official-Facebook Company-contact action.

## Provider controls

FullEnrich is active only for bounded integration validation under the 50/run, 100/day and 250/pilot caps. Search/Lookup/Contact Enrichment remain separate validated actions. Contact Enrichment requests work email and phones for selected contacts only and does not request personal email. The official-Facebook Apify Actor remains fixture-only until account, build, rights, financial and positive-result live gates pass.

Retain one selected named contact by default and at most two when the second is justified by a large organisation or shared purchasing or operational responsibility.

## Boundaries

- No second discovery crawl.
- No arbitrary approval token can activate a source.
- Firecrawl and Apify live calls remain blocked until their Step 11 runtime gates pass; FullEnrich is limited to the active integration-validation policy.
- No automatic query segmentation, provider fallback, social-profile opening, outreach or CRM write.
- A search snippet is discovery-only.
- Every result reports zero external calls/actions and preserves audit requirements.

## Outputs

A hashed preflight with source policy, field gate, runtime status, limits, stop conditions, missing provider gates, blocks, warnings, the required audit envelope and an explicit false external-call authorisation. A provider fixture may validate downstream handling while all live provider gates remain visible and blocked.

## Handoff

Only `allowed_local_fixture` or `allowed_local_reuse` data may enter the Step 5C field-verification fixtures. Future live execution requires Step 6 runtime controls and the applicable integration gate.
