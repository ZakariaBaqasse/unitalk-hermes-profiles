# A2 Step 11 Website-First Enrichment — Implementation Report

**Version:** `0.1.0`  
**Generated:** `2026-09-18T14:06:13Z`  
**Status:** `IMPLEMENTED LOCALLY — LIVE ACCEPTANCE AND ACTIVATION BLOCKED`

## Scope

This release candidate adds bounded Firecrawl official-site research before FullEnrich, conditional official-Facebook Company contact fallback through Apify, multi-value Twenty Company contact/social merges, and website-observed People regardless of role.

## Confirmed controls

- Firecrawl is invoked only by a bounded skill script, never by free agent `web_extract` during prospect runtime.
- Five pages maximum per Company: homepage plus up to four Contact/About/Team/Staff equivalents.
- `onlyMainContent: false`; formats are Markdown, HTML and links.
- No Firecrawl credit policy or credit caps.
- One Apify Actor call per eligible Company; no retry; no Company-count maximum.
- Facebook URL must be explicitly linked by the official website.
- Existing A1/Twenty Company primary email/phone is preserved; distinct official-site/Facebook values append.
- Generic Company channels never populate Person fields.
- Up to two official-site People may be retained regardless of role; role priority remains independent.
- Missing/unavailable/blocked websites continue to the existing FullEnrich flow.

## Implemented components

- bounded Firecrawl official-site plan, fetch, extraction, decision-packet and decision-validation scripts;
- cleaned semantic Person evidence blocks, prose-aware shared-name extraction and exact-span LLM proposal validation;
- same-domain/SSRF/robots/page-limit controls;
- official-Facebook Apify request, async polling and result-validation scripts;
- Company multi-value email/phone/social merge planning;
- guarded Twenty Company business-field PATCH and baseline/read-back controls;
- website People retention regardless of role and FullEnrich Contact Enrichment routing;
- successor draft Source Register, evidence, conflict, provider, Twenty mapping and state contracts;
- Step 11 runtime policy, schemas, fixtures, runbook and local acceptance.

## Validation results

- focused Step 11 unit tests: **67/67 passed**;
- Firecrawl and Person-extraction tests: **29/29 passed**;
- Apify Facebook tests: **12/12 passed**;
- Company merge/write tests: **11/11 passed**;
- website People tests: **4/4 passed**;
- source-preflight tests: **5/5 passed**;
- contract tests: **6/6 passed**;
- complete website → Contact Enrichment fixture → Company merge → Apify fallback → Twenty dry-run acceptance: **passed**;
- Quillin real-page regression: **passed** with Ralph Quillin, Donna Quillin, Rob Windels and Vince Grupposo recovered and zero product-name false positives;
- consolidated Step 11 groups, including Step 10 regressions: **13/13 passed**;
- live Twenty Company contact/social metadata validation: **passed, zero writes**.

## Live metadata validation

Twenty Company fields `domainName`, `email`, `phone`, `linkedinLink`, `facebook`, `instagram`, `youtube`, `tiktok`, and `xTwitter` were read and validated. No metadata or records were changed.

## Credential resolution

- `FIRECRAWL_API_KEY`: resolved from the profile environment and authenticated through the read-only Firecrawl team endpoint; no credential value was exposed or persisted.
- `APIFY_API_KEY`: resolved from the process/profile environment and authenticated through the read-only Apify current-user endpoint; no credential value was exposed or persisted. `APIFY_TOKEN` remains a legacy alias only.
- These checks sent no prospect data, started no provider jobs, incurred no provider action cost and made no CRM write.

## Activation boundary

Official-site, Firecrawl, Apify and new Twenty Company business-field writes remain disabled until positive-result live acceptance and read-back. Current Step 10 Twenty–FullEnrich permissions are unchanged.
