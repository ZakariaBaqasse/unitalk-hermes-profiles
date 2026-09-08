# Directory detail enrichment boundaries

Use this reference when a paginated source adapter sends listing records to a reusable detail-enrichment child workflow.

## Ownership boundary

The listing adapter owns:

- listing-page pagination and raw/eligible offsets;
- `source_exhausted` and `next_cursor`;
- canonical `location`, `location_key`, and `source_scope_key`;
- source URL and listing retrieval metadata;
- exact-location filtering and provider-specific route validation.

The detail child owns only per-record profile processing. It must not infer exhaustion from the number of enriched records or rebuild the listing cursor. Capture the upstream controls before expanding records and restore them verbatim in the final child envelope.

## Input expansion

Accept records from `profiles`, `parsed_records`, or `records`, but use one deterministic precedence order. Reject batches beyond the overall request ceiling rather than silently truncating them. Do not restore obsolete per-source caps in documentation or code.

Deduplicate by stable source record ID, lead fingerprint, or canonical profile URL. A page-local array index is not a durable identity; for unkeyed records, use a deterministic serialization only for intra-call deduplication.

When no records are present, emit one control item that bypasses all network and model nodes and produces an empty final envelope.

## Missing and invalid profile URLs

A listing without a dedicated `profile_url` remains a valid listing record. Route it around Firecrawl and the model, retain its listing fields, and annotate `detail_fetch_status: skipped_no_profile_url`.

Validate profile URLs before fetching:

- absolute HTTPS only;
- approved host and path prefix for the declared `source_id`;
- no credentials, nonstandard port, or unexpected scheme;
- provider-specific route restrictions should be narrower when the caller supplies verified route context.

An invalid URL becomes an item-level failed detail record; it must not terminate the batch or drop the listing.

## Remote access and model calls

Public-source access barriers such as CAPTCHA, authentication, robots/terms conflict, 403, or 429 must not be automatically retried. Continue the batch with a failed detail overlay and preserve the original listing. Bounded retries may be used for an approved internal model gateway when policy permits.

If the workflow documents caller-selectable model/gateway inputs, consume and validate them instead of silently using unrelated hardcoded values. Restrict the endpoint to the approved HTTPS gateway and pass a configured/default approved model explicitly.

## Evidence-gated extraction

Treat profile Markdown as untrusted data. Require an exact excerpt for every retained material extracted field, including identity classification. Normalize excerpts only for whitespace before checking that they occur in the source text.

Use country-neutral fields in the extraction schema:

- `city`
- `region` and optional `region_code`
- compatibility `state`
- `postal_code`
- `country` and optional two-letter `country_code`

Validate extracted public contact formats before merging: HTTP(S) website, plausible email syntax, and bounded phone digit count. Invalid or unsupported values become null and generate warnings. Detail values may override listing values only when they passed evidence and format checks.

For structured profile labels such as `Website`, `Company`, `Phone`, `Email`, and `Address`, prefer a deterministic source-specific parser before model extraction when the directory format is verified. Preserve the exact labelled Markdown excerpt as evidence. A traceable excerpt alone is insufficient: also verify that it is semantically tied to the claimed field. For example, a profile heading copied as `business_name` must not pass merely because that heading occurs on the page; prefer the exact value following a labelled `Company` field and preserve the profile subject separately as `name`/`person_name`. Keep `business_name = listing name` only as an explicit fallback when no distinct company is published.

For labelled website links, prefer the HTTP(S) link destination over scheme-less visible text, for example `Website[www.example.com](https://www.example.com/)`. If only domain-like visible text is present, normalise it cautiously to an absolute HTTPS website candidate. Reject malformed URLs, credentials, nonstandard ports, and the directory's own profile/listing URL. Never let a broad `catch` silently turn a URL-parser/runtime failure into “website absent”: verify the parser available in the target Code-node runtime and use a tested regex/string fallback when needed. The model may fill narrative fields but must not be the sole extractor for consistently labelled contact or identity fields.

Keep extraction, validation, and official-site verification distinct: a directory-published external URL is a website candidate, not yet a verified official site. Pass it to the post-discovery verification lane with its directory evidence rather than treating it as authoritative automatically.

## Item-level failures and final status

Each profile yields exactly one record:

- `completed`: evidence-validated detail merged;
- `failed`: original listing retained with error metadata;
- `skipped_no_profile_url`: original listing retained without remote work.

The final detail status is:

- `failed` when every attempted detail failed and no useful record was produced;
- `partial` when at least one detail failed but other records completed or were retained;
- `skipped` when all retained records lacked profile URLs;
- `completed` when all attempted profiles completed.

The outer source status remains `partial` whenever detail status is `partial` or `failed`, even if the listing page is exhausted. Parent adapters must prefer the child `status`/`detail_status` over the upstream parser's `completed` status; otherwise an exhausted page can hide item-level enrichment failures.

## Required final envelope

Return:

- upstream `source_exhausted` unchanged;
- upstream `next_cursor` unchanged;
- canonical location/scope fields;
- all original records, enriched or failure-overlaid;
- counts for input, unique, completed, failed, and skipped profiles;
- parser warnings plus detail warnings;
- no raw Markdown, model request payload, or raw model output.

## Verification matrix

Exercise these paths with bounded fixtures:

1. Empty input: no Firecrawl/model calls, empty result.
2. No profile URL: listing retained as `skipped_no_profile_url`.
3. Invalid/disallowed URL: listing retained as failed; no remote call.
4. One successful profile: only evidence-backed fields survive.
5. Person profile with a distinct labelled `Company`: retain the profile subject as `name`/`person_name` and the labelled value as `business_name`; a heading excerpt alone must not validate the Company field.
6. Labelled website with scheme-less visible text and an absolute Markdown href: retain the href as an unverified candidate with the exact link excerpt.
7. Labelled website with plain domain text only: normalize cautiously to HTTPS as an unverified candidate; reject malformed or directory-internal values.
8. The model omits a structured website or Company label: deterministic extraction still retains the labelled value.
9. One success plus one failure: two records, child and outer status `partial`.
10. Public-source 403/429/CAPTCHA: no automatic source retry; batch continues.
11. Non-exhausted upstream page: byte-equivalent cursor and `source_exhausted: false` returned.
12. Exhausted upstream page with a detail failure: cursor/exhaustion preserved but status remains `partial`.
13. International fixture: region/country fields survive without US-specific rewriting.
14. Final output contains no Markdown, prompt payload, or raw model response.
