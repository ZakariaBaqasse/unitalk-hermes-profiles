# A2 Website-First Enrichment and Facebook Contact Fallback — Implementation Plan

**Plan version:** `0.1.0-draft.2`  
**Updated:** `2026-09-18T13:17:09Z`  
**Profile:** `equinet-a2-enrichment`  
**Current active foundation:** `1.4.4` / `integration_validation_in_progress`  
**Plan status:** design only — not implemented or activated  
**Requested architecture:** Twenty → official website → conditional Facebook/Apify → FullEnrich → Twenty

## 1. Purpose

Upgrade the A2 workflow so that an organisation's verified official website is always checked before FullEnrich when a website URL is available. The website supplies first-party company contact details, explicit company social URLs and up to two named people. The Facebook Page Contact Info Scraper is a company-contact fallback only when a required company email or phone remains missing after combining A1/Twenty and official-site evidence. FullEnrich remains the person-contact provider and the existing fallback when no website or no usable website person exists.

This plan does not activate web access, Apify, new provider spending or new Twenty writes. Those actions remain gated until the contracts, connectors, tests and live acceptance below are completed.

## 2. Confirmed business decisions

1. Preserve the existing A1/Twenty primary company email and phone. Append distinct official-website values to the corresponding Twenty composite field. If the baseline is empty, the official-site value becomes primary.
2. Inspect at most five public same-domain pages: homepage/footer, Contact, About, Team and Staff or their closest equivalents.
3. Retain up to two people presented by the official website regardless of role. Preserve an explicit role/title when present; role is optional for collection.
4. If the official website verifies a person's name, current company and role, skip FullEnrich Lookup and use Contact Enrichment when email or phone is missing. If identity/current-company context is uncertain, resolve it before contact enrichment.
5. Run `apify/facebook-page-contact-information` only against a Facebook URL explicitly linked by the verified official website and only when a company channel remains missing across both A1/Twenty and the website.
6. Append Facebook-published email and phone directly to the Company composite fields after normalisation and deduplication.
7. Use the live Twenty Company social mappings already created.
8. Apify controls: one Actor call per eligible Company, no automatic retry, no Company-count maximum per chat-triggered run, and no use of a Facebook page that was not explicitly linked by the official website.
9. Generic company contacts never populate Person fields. A Person field receives a website value only when the page explicitly attributes the value to that named person.
10. A missing, unavailable or blocked website immediately returns the Company to the existing FullEnrich flow after recording the exact website state.

## 3. Target workflow

### 3.1 Intake and baseline

1. Pull the explicitly scoped Twenty Companies and all linked People.
2. Preserve A1/Twenty values and source context.
3. Validate the Company website URL from `domainName.primaryLinkUrl` or approved A1 evidence.
4. If no usable URL exists, record `website_not_found` and continue to the current linked-Person Lookup / staged FullEnrich flow.

### 3.2 Official website stage

For a usable website:

1. Perform scheme, DNS, redirect, content-type, robots and scope preflight.
2. Fetch the homepage and inspect its full DOM, including header and footer.
3. Discover same-site Contact, About, Team and Staff links using deterministic link-text/path aliases.
4. Fetch no more than five pages total, with one targeted retry per failed URL as already allowed by the Source Register.
5. Extract only visible/public business evidence:
   - company emails from visible text and `mailto:` links;
   - company phones from visible text and `tel:` links;
   - explicit outbound Facebook, Instagram, YouTube, LinkedIn, TikTok and X/Twitter URLs;
   - up to two named people in company/team/staff/contact context;
   - exact displayed role/title when present;
   - person-attributed email/phone only when the DOM context clearly associates the channel with that person.
6. Preserve page URL, extraction method, observed text, timestamp and content hash for every accepted observation.
7. Create an LLM decision packet. The LLM decides company/person attribution, person-name boundaries, credential suffixes, current-company context and role classification. A deterministic validator enforces source URLs, page limits, real extracted strings and no inferred values.

### 3.3 Company merge after website

For Company email and phone:

1. Normalise email case and syntax; normalise phone numbers to E.164 when country context permits while retaining the source display value in evidence.
2. Deduplicate exact canonical values.
3. Preserve the existing primary A1/Twenty value.
4. Append each distinct official-website value to `additionalEmails` or `additionalPhones`.
5. If the existing primary is empty, use the first official-site value as primary and append further unique values.
6. Different A1 and website values are not automatically a conflict because Twenty supports multiple values. Both remain visible with field-level provenance in canonical A2 JSON.
7. Never move a generic Company email or phone into a Person.

For social URLs:

1. Accept only explicit outbound links found on the official website.
2. Canonicalise tracking parameters, mobile host variants and trailing path noise without changing the account/page identity.
3. Preserve existing primary values and append distinct URLs when the Twenty field supports secondary links.
4. Do not open or extract LinkedIn, Instagram, YouTube, TikTok or X profiles.
5. The only linked social destination eligible for subsequent automated extraction is the official Facebook page under the separate Apify gate.

### 3.4 Conditional Facebook/Apify stage

Compute channel gaps after the A1/Twenty + website merge:

- `company_email_missing = no usable email across baseline and website`
- `company_phone_missing = no usable phone across baseline and website`

The Actor is eligible only when at least one gap is true and an official website page explicitly linked a Company Facebook URL.

Execution:

1. Validate that the Actor input URL exactly matches the canonical Facebook URL captured from the official website.
2. Reserve one Actor call for that Company. No automatic retry is permitted.
3. Submit one URL to `apify~facebook-page-contact-information` using a pinned Actor build/version.
4. Use the asynchronous Actor run API and deterministic polling so runs can resume safely. Retrieve only the run's default dataset after terminal success.
5. Allowlist output fields: `facebookUrl`, `pageUrl`, `pageName`, `title`, `email`, `phone`, `website`, `error`, and `errorDescription`.
6. Ignore likes, followers, ratings, photos, posts, descriptions, personal-profile data and every non-required field.
7. Verify the returned page URL against the submitted official URL.
8. Append a returned email or phone directly to the Company composite field if syntactically valid and not already present.
9. Do not overwrite any existing value and do not populate a Person.
10. On `not_found`, Actor failure, output mismatch or unexpected personal data, retain partial website evidence and continue to FullEnrich. Do not retry or use another Facebook actor automatically.

No hard Company-count limit is introduced. The run still requires an explicit user-scoped Company batch. A financial hard stop remains mandatory; activation is blocked until Equinet confirms an Apify account and USD run/day/pilot caps or explicitly approves another bounded spend control.

### 3.5 Website people and FullEnrich

Collection and selection are separate:

1. Collect up to two unique people that the official website presents in organisation, team, staff, About or Contact context, regardless of role.
2. Exclude testimonial authors, customers, event attendees, quoted third parties and names that are not represented as part of the organisation.
3. If more than two valid people are present, rank deterministically:
   - explicit target-role evidence first;
   - explicit Owner/founder/manager/current staff context next;
   - unknown-role current staff last;
   - source page priority and DOM order break ties.
   This ranking does not reject non-target roles; it only resolves the two-person limit.
4. Preserve exact displayed name and title. For a value such as `Corey Baxter, CJF`, retain `source_full_name = Corey Baxter, CJF`; when `CJF` is recognised or explicitly presented as a credential, store it separately and use `Corey Baxter` as the provider comparison name. Never delete the source form.
5. Set `a2RoleStatus = CURRENT_AT_COMPANY` only when the official page context presents the person as current. Set role priority from explicit title evidence; use `UNKNOWN` when no role is shown.
6. A website person may be retained even with `UNKNOWN` or unrelated role priority, per the confirmed business decision. Such a person does not automatically satisfy the target-role requirement or establish buying influence.
7. Generic page contact details remain Company values. Only person-card/profile-attributed details become Person values.

FullEnrich routing for each retained website person:

- Both person email and phone available on the official site: no Contact Enrichment call.
- Either channel missing: run one Contact Enrichment call requesting exactly `contact.work_emails` and `contact.phones`; merge only valid new values.
- Name/current Company/role verified by official-site context: skip People Lookup.
- Current-company identity uncertain: run supported Lookup when identifiers permit. If Lookup is unsupported, use a constrained name + exact Company Search packet and require LLM match validation before Contact Enrichment.
- Personal email returned incidentally remains isolated as `personal_email_candidate`; it never fills work email automatically.

After website people are retained:

- If fewer than two People are retained and the target-role gap remains, the existing FullEnrich staged Search may use the remaining slot.
- If two website People are already retained, do not create a third automatically. Preserve any unresolved target-role gap for review.
- Existing A1-linked People remain preserved and deduplicated against website people by FullEnrich ID, professional URL, work email, normalised name + Company, then Twenty Person ID.

### 3.6 Website failure path

Use explicit states:

- `website_not_found`: no stored/approved URL;
- `website_unavailable`: timeout, DNS/TLS failure or unsupported content;
- `website_blocked`: terms/robots denial, login, CAPTCHA, HTTP 403/429 or policy stop;
- `website_no_relevant_data`: pages read but no accepted observations;
- `website_succeeded`: at least one validated observation.

All five states continue to the current FullEnrich flow. Only valid partial evidence is retained. There is no automatic search-engine discovery in this upgrade when the Company lacks a stored website.

## 4. Tooling

### 4.1 Website content tools

The operational workflow must use a bounded skill-owned Firecrawl connector script. The agent orchestrates validated stages but must not call Hermes `web_extract` freely for prospect enrichment.

**Bounded Firecrawl path**

1. `build_official_site_plan.py` validates the Company, approved official URL, page limit and requested page classes.
2. `firecrawl_official_site_fetch.py` reads `FIRECRAWL_API_KEY` from the environment, never from an artifact. The operator has confirmed that this environment variable is available; every run still performs a boolean credential preflight without logging the value.
3. The script calls Firecrawl `/v2/scrape` for the homepage with:

   ```json
   {
     "formats": ["markdown", "html", "links"],
     "onlyMainContent": false
   }
   ```

   `onlyMainContent: false` is mandatory so header/footer email, phone and social links are not discarded.
4. The script deterministically selects same-domain Contact, About, Team and Staff links from the homepage result.
5. It calls Firecrawl `/v2/batch/scrape` for no more than four selected URLs using the same formats. Combined with the homepage, the hard maximum remains five pages.
6. It persists request metadata, returned page URLs, Firecrawl response IDs when available, page hashes, errors and a minimised result artifact.
7. `extract_official_site_observations.py` uses pinned `selectolax` over returned HTML plus deterministic Markdown/link processing for contacts, social URLs and Person candidates.

The script retains local URL/robots/scope controls:

- Python `urllib.robotparser` and explicit terms/robots preflight;
- `tldextract` or an equivalently pinned public-suffix-aware domain normaliser;
- private/link-local/loopback/metadata-service destination blocking before submitting any URL;
- same-domain and five-page enforcement before and after Firecrawl returns data;
- deterministic email, phone and social URL normalisers.

Firecrawl handles normal HTTP fetching, redirects, JavaScript rendering, HTML cleaning and link extraction. Routine Browser Use/Chromium fallback is removed. A Firecrawl blocked/failed page does not trigger another scraping provider; valid partial evidence is preserved and the Company continues to FullEnrich.

Hermes `web_extract` remains available only for provider documentation, development diagnostics and manual investigation of synthetic failures. It is not an authorised normal-runtime path for prospect websites because it does not enforce the skill's complete page plan, artifact and idempotency contract.

**Firecrawl usage decision**

No Firecrawl credit policy, credit reservation, run/day/pilot cap, spend approval or credit settlement is required. The technical controls are the five-page maximum per Company, explicit chat-triggered Company scope, concurrency one per Company and idempotent reuse within a run. Page counts, request IDs and errors are recorded for operational audit only.

### 4.2 Apify tools

- Direct Apify REST API, actor identifier `apify~facebook-page-contact-information` / current Store actor ID `oJ48ceKNY7ueGPGL0`;
- asynchronous `POST /v2/actors/{actorId}/runs`, bounded polling of `GET /v2/actor-runs/{runId}`, then dataset retrieval;
- API key from `APIFY_API_KEY` (`APIFY_TOKEN` accepted only as a legacy alias), never stored in artifacts;
- pinned Actor build/version and stored input/output schema hashes;
- one run per eligible Company, zero automatic retries;
- idempotency key from Company ID + canonical Facebook URL + requested channel gaps + Actor build;
- output minimiser before data enters the canonical record.

Provider documentation observed for this plan reports output fields including email and phone and advertises result pricing from $6.60/1,000 on discounted tiers, with $13/1,000 on free/no-discount pricing plus a $0.001 Actor-start event. These values must be re-read and accepted against the actual Equinet account before activation.

## 5. Twenty mappings

Live metadata read during plan preparation verified these Company fields:

| Business value | Twenty internal field | Type |
|---|---|---|
| Official website | `domainName` | `LINKS` |
| Email | `email` | `EMAILS` |
| Phone | `phone` | `PHONES` |
| LinkedIn | `linkedinLink` | `LINKS` |
| Facebook | `facebook` | `LINKS` |
| Instagram | `instagram` | `LINKS` |
| YouTube | `youtube` | `LINKS` |
| TikTok | `tiktok` | `LINKS` |
| X/Twitter | `xTwitter` | `LINKS` |

Composite write behaviour:

- `EMAILS`: `primaryEmail`, `additionalEmails`;
- `PHONES`: `primaryPhoneNumber`, country/calling-code fields, `additionalPhones`;
- `LINKS`: `primaryLinkUrl`, `primaryLinkLabel`, `secondaryLinks`.

The operational mapping contract must add these Company business fields. Every merge plan reads the latest Company baseline, hashes it, builds the complete composite value explicitly, applies one guarded PATCH and reads the exact Company back. The final Company enrichment status remains the last write.

Per-value provenance cannot be represented losslessly inside the Twenty composite itself. Canonical A2 JSON must retain source type, source URL, page/Actor receipt, observation timestamp, original display value, canonical value and merge action for every contact and social URL.

## 6. State and decision model

Add canonical runtime states without overloading `a2EnrichmentStatus`:

### Website

`NOT_CHECKED`, `NOT_FOUND`, `PREFLIGHT_BLOCKED`, `FETCHING`, `PARTIAL`, `SUCCEEDED`, `NO_RELEVANT_DATA`, `UNAVAILABLE`, `ERROR`.

### Facebook fallback

`NOT_REQUIRED`, `ELIGIBLE`, `BUDGET_BLOCKED`, `SUBMITTED`, `RUNNING`, `SUCCEEDED`, `NOT_FOUND`, `OUTPUT_MISMATCH`, `FAILED`, `POLICY_BLOCKED`.

### Website Person

- `website_observed = true`;
- exact source name and provider comparison name;
- current-company evidence state;
- role title and priority independently;
- selection status: `RETAINED`, `NOT_RETAINED_LIMIT`, `REJECTED_NOT_ORGANISATION_PERSON`, `HELD_AMBIGUOUS`;
- contact state: `COMPLETE_FROM_WEBSITE`, `CONTACT_ENRICHMENT_REQUIRED`, `CONTACT_ENRICHED`, `CONTACT_NOT_FOUND`, `CONTACT_ERROR`.

The LLM decides attribution, name boundaries, role classification and retention. Scripts validate page evidence, IDs, limits, allowed transitions, merge safety and external write plans.

## 7. Profile artifacts to create

### Contracts and decisions

1. `foundations/decisions/A2-WEBSITE-FIRST-ENRICHMENT-<date>.json` — business decisions in this plan.
2. `foundations/contracts/integrations/a2-official-website-firecrawl-integration-0.1.0.json` — bounded Firecrawl scrape/batch-scrape methods, environment credential, pages, fields, safety, extraction, idempotency and receipts.
3. `foundations/contracts/integrations/a2-apify-facebook-contact-integration-0.1.0.json` — Actor/build, API, input/output allowlists, polling and idempotency.
4. `foundations/contracts/sources/a2-source-register-0.3.2.json/.csv` — activate bounded official-site runtime and add the specific Facebook Actor as a distinct source; do not repurpose the blocked generic social-automation entry.
5. `foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.3.2.json` — official-site and official-Facebook-page evidence semantics.
6. `foundations/contracts/governance/a2-provider-and-cost-policy-0.5.0.json` — preserve FullEnrich credits and add only Apify USD/event controls. Firecrawl has no credit policy or cap enforcement.
7. `foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.3.2.json` — multi-value append and baseline-preservation rules.
8. `foundations/contracts/twenty/a2-twenty-operational-mapping-0.1.2.json` — Company email, phone and social fields.
9. `foundations/contracts/runtime/a2-twenty-fullenrich-state-model-0.1.4.json` — website and Facebook stages before FullEnrich.
10. JSON Schemas for website fetch plans/results, extraction observations, LLM decisions, Facebook requests/results, company merge plans and updated write proposals.
11. A successor Active Foundation Manifest only after synthetic and live acceptance pass.

### Scripts to create

1. `scripts/build_official_site_plan.py` — URL, robots and deterministic page-plan validation.
2. `scripts/firecrawl_official_site_fetch.py` — bounded homepage scrape plus selected-page batch scrape with persisted receipts.
3. `scripts/extract_official_site_observations.py` — candidate company contacts/social URLs/people; no business decisions.
4. `scripts/build_website_decision_packet.py` — includes cleaned, bounded person evidence blocks.
5. `scripts/validate_website_person_observation_proposals.py` — exact block/span validation and controlled name derivations.
6. `scripts/validate_website_decisions.py`.
7. `scripts/build_company_contact_merge_plan.py` — explicit composite merge and provenance.
8. `scripts/build_apify_facebook_requests.py` — exact official URL and gap-only gating.
9. `scripts/apify_facebook_page_contact.py` — account preflight, submit, poll, minimise, settle cost.
10. `scripts/validate_apify_facebook_results.py`.
11. `scripts/build_website_people_contact_batch.py` — dedupe and FullEnrich routing.
12. Extend `build_twenty_enrichment_write_plan.py` and `push_twenty_enrichment.py` for guarded Company composite fields and website-observed People.
13. Extend `manage_a2_enrichment_run.py` for resumable website, Firecrawl and Actor stages.

### Scripts to modify

- `pull_twenty_companies.py`: include Company email, phone and all social composites.
- `a2_twenty_fullenrich_common.py`: canonical URL/contact normalisers and new contract pointers.
- `build_fullenrich_action_requests.py`: website-person routes and remaining-slot logic.
- `build_selected_contact_batch.py`: website Person source kind and exact Company/domain evidence.
- `fullenrich_contact_enrichment.py`: preserve website source metadata and existing channels.
- `validate_person_selection_decisions.py`: website-observed retention separate from role suitability.
- `build_step10_implementation_manifest.py` and acceptance runners.

### Skills and runbook

Create an `a2-official-site-and-facebook-enrichment` skill and update:

- `a2-twenty-fullenrich-workflow`;
- `a2-permitted-enrichment-research`;
- `a2-gap-analysis-and-enrichment-planning`;
- `a2-evidence-confidence-and-freshness`;
- `a2-protected-field-conflict-resolution`;
- `a2-twenty-connector`;
- `a2-fullenrich-connector`;
- the chat-controlled runbook.

## 8. Connector safeguards

### Website / Firecrawl

- `FIRECRAWL_API_KEY` is required from the environment; never display or persist it.
- Use Firecrawl scrape for the homepage and batch scrape for up to four selected pages; do not use unrestricted crawl.
- Request only `markdown`, `html` and `links` with `onlyMainContent: false`; do not request Firecrawl JSON, question, highlights, PDF, audio or video modes.
- HTTP(S) only; block credentials in URLs.
- Reject private, loopback, link-local and metadata-service destinations before submission and reject unexpected returned URLs.
- Maximum five pages and same-domain pages only; external social URLs may be recorded as observations but are never submitted to Firecrawl.
- HTML/text content only; no document downloads or media extraction.
- Concurrency one per Company.
- Reuse identical successful Firecrawl page results within the same enrichment run.
- One targeted retry remains allowed only if the website Source Register permits it; no fallback scraper is invoked after a policy/block response.
- Preserve partial results when later pages fail.
- Record page count, request/response IDs when available, hashes and errors for audit. Do not implement Firecrawl credit caps or settlement.

### Apify

- `APIFY_API_KEY` required from environment/secret store (`APIFY_TOKEN` is a legacy alias).
- Verify Actor identity, owner (`Apify`), build, account and pricing before a run.
- One URL and one Actor run per eligible Company.
- No retry, resurrection, fallback Actor or automatic Facebook search.
- Poll terminal status with bounded duration.
- Record run ID, dataset ID, Actor/build, input hash, output hash, status and final cost.
- Reject a dataset with multiple/mismatched Facebook pages, unexpected personal-profile output or missing provenance.
- Financial reservation before submit and actual-cost settlement after finalized run accounting.

### Twenty

- Read the latest baseline immediately before planning.
- Preserve primary values unless empty.
- Append only normalised unique values.
- Never clear a composite field through omission.
- Reject write plans whose baseline hash no longer matches.
- Read back the exact Company and Person composites.
- Write final Company status last.

## 9. Test plan

### Unit tests

- URL canonicalisation and social-platform classification.
- robots, redirect and SSRF controls.
- Contact/About/Team/Staff link discovery.
- email/phone extraction from text, `mailto:` and `tel:`.
- Company versus Person attribution boundaries.
- credential suffix preservation and provider comparison names.
- email/phone/social composite deduplication.
- A1 primary preservation and website append.
- website-as-primary when baseline is empty.
- two-person limit and deterministic ranking regardless of role.
- page and retry limits.

### Synthetic website scenarios

1. Homepage/footer contains all social URLs, email and phone.
2. A1 and website have different valid contacts; both remain.
3. Duplicate values use one canonical value and multiple evidence references.
4. Contact page has two named people with roles.
5. About page has names without roles; both remain with `UNKNOWN` priority.
6. More than two names; deterministic ranking selects two.
7. Testimonial/customer names are rejected.
8. Person-specific and generic Company contacts are kept separate.
9. JavaScript page triggers bounded browser fallback.
10. robots denial, CAPTCHA, 403 and 429 stop correctly and continue to FullEnrich.

### Synthetic Facebook scenarios

1. No call when A1 or website already supplies the channel.
2. No call without a Facebook URL explicitly linked by the official site.
3. One call when a channel is missing.
4. Both email and phone append when both were missing.
5. Duplicate result produces `no_change`.
6. Mismatched page output is rejected.
7. Personal-profile output is rejected.
8. Actor failure produces no retry and continues to FullEnrich.
9. Cost reservation and settlement are correct.

### Full workflow scenarios

- Website has complete Company contacts and two people; no Facebook Actor, no People Search.
- Website has Company contacts but no people; existing FullEnrich Search runs.
- Website has a named person with one missing channel; one Contact Enrichment call.
- Website has Facebook but no Company contact channels; one Actor call, Company append, then person flow.
- No website; current FullEnrich workflow is unchanged.
- Two website people consume the contact limit; target-role gap remains visible without creating a third Person.
- All intended Twenty Company/Person writes reconcile exactly.

## 10. Live acceptance sequence

Each acceptance action must be separately chat-triggered and bounded:

1. **Official-site read-only acceptance:** one approved Company with a simple site; verify page limits, contacts, socials, names and evidence receipts.
2. **Firecrawl JavaScript acceptance:** one approved JS-rendered site; verify rendered content, footer preservation, page limit, same-domain enforcement and stop controls.
3. **Twenty Company merge acceptance:** one approved Company with an empty additional slot; append one website email/phone/social URL, then read back.
4. **Apify account preflight:** token verification, Actor identity/build, account and effective pricing; no Actor run.
5. **Apify positive-result acceptance:** one approved official Facebook page with a missing channel; one run, no retry, cost/read-back receipt.
6. **Website Person + FullEnrich acceptance:** one approved official-site person missing a channel; Contact Enrich and verify cost.
7. **Full end-to-end acceptance:** website → optional Facebook → selected website Person → FullEnrich → Twenty write/read-back.

Production or broad pilot activation remains blocked until every positive-result path has a verified receipt.

## 11. Rollout

### Phase A — contracts and fixtures

Create versioned contracts, schemas, fixture pages and mocked Actor/FullEnrich/Twenty responses. No external actions.

### Phase B — deterministic connectors

Implement the bounded Firecrawl website connector, extraction, decision validators, merges, Facebook connector and resume state. Run all unit and synthetic acceptance suites.

### Phase C — read-only official-site validation

Activate website access for explicitly selected Companies only. No Apify or Twenty business-field writes.

### Phase D — guarded writes and Apify validation

After metadata/write-plan validation, test one Company merge and one Actor call independently with read-back/cost reconciliation.

### Phase E — bounded integrated validation

Run the complete workflow on a user-selected batch. Do not remove the chat trigger or human review requirement.

## 12. Open activation dependencies

The business flow is sufficiently specified for implementation planning, but these gates remain before live activation:

1. Apify account/token availability and least-privilege access.
2. Actor owner/build pin and live input/output contract verification.
3. Facebook/platform rights, vendor, retention and privacy review for the specific Actor.
4. Apify USD run/day/pilot caps or another explicit bounded financial control. The absence of a Company-count limit does not remove the financial hard-stop requirement.
5. Firecrawl endpoint/account connectivity, rate limits, timeout/response-size values and a successful boolean `FIRECRAWL_API_KEY` preflight in the connector execution environment. No Firecrawl credit policy is required.
6. Confirmation that existing Company contact/social composite writes do not trigger unintended Twenty workflows.
7. Live acceptance of website-observed People with `UNKNOWN` or unrelated role priority, including their review label and downstream target-gap behavior.

## 13. Definition of done

The upgrade is complete only when:

- every Company with a website receives a bounded official-site check before FullEnrich;
- page/robots/security controls pass;
- Company contacts and social URLs are extracted with evidence and merged without overwrite;
- Facebook Actor runs only under the exact approved missing-channel trigger and official-URL rule;
- zero retries and one call per eligible Company are enforced;
- up to two website People are retained regardless of role without confusing role priority, target suitability or outreach authority;
- missing Person channels route to FullEnrich correctly;
- no website or blocked website continues to the current FullEnrich flow;
- Company and Person writes are validated and reconciled;
- FullEnrich/Apify costs, retries, Firecrawl page usage, source evidence and external actions are audited;
- synthetic, connector, positive-result and full end-to-end acceptance pass;
- a successor active foundation manifest is published with zero hash drift.

## 14. Current action state

This document is an implementation plan only. During plan preparation:

- live Twenty metadata was read to verify the existing Company fields;
- Apify public documentation was read to identify the Actor, API model, output fields and advertised pricing;
- the operator confirmed that `FIRECRAWL_API_KEY` is configured, but this plan update did not display or test the secret and made no Firecrawl call;
- no official prospect website was visited;
- no Apify Actor was run;
- no FullEnrich enrichment call was made;
- no Twenty record or metadata was changed;
- no active contract, runtime policy, skill or foundation manifest was changed.
