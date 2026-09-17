# Supplemental public business-page enrichment

Use this pattern when an n8n source adapter or detail enricher optionally searches a public social platform for missing professional business data.

## Placement and ownership

- Run supplemental enrichment only after the primary source record has been normalized and any first-party/detail-page enrichment has completed.
- For a reusable detail enricher, call the supplemental batch workflow after the final detail envelope is built, not inside the per-profile loop.
- For an asynchronous provider adapter, call it after the provider job has been persisted and the common source envelope has been built.
- The supplemental child must preserve the caller's `status`, `source_exhausted`, `next_cursor`, location and scope fields byte-for-byte. It never owns primary-source pagination.
- A supplemental failure retains the original record and adds an item-level status/warning; it does not turn a successful primary source into a failed source.

## Cost-aware eligibility

Default to searching only when at least two of public phone, professional email and non-social external website are missing. Missing email alone is not normally sufficient because many legitimate businesses do not publish email.

Make the threshold configurable, but bound:

- missing-field threshold: 1..3, default 2;
- maximum candidates per envelope;
- maximum results per candidate and per Actor run;
- maximum total charge;
- one active Actor run unless a versioned policy allows more.

Batch records that share one canonical location when the Actor supports multiple search terms plus one location. Avoid one paid Actor run per record.

## Search and identity rules

- Search by exact `business_name` plus canonical city/region/country.
- Accept public business Pages only; reject personal profiles, groups, events, posts and login-only content.
- Do not merge a result based on search rank, follower count, photos or similar name alone.
- Require exact normalized business-name agreement plus matching geography, or exact name plus a strong existing contact signal such as phone/domain/email.
- If more than one candidate passes within a small score margin, mark `possible_match` and merge nothing.
- Do not strip semantic horse-business words such as `farm`, `farms`, `stable` or `stables` during name normalization; doing so can collapse distinct businesses. Legal suffixes such as LLC/Inc may be normalized conservatively.

## Field semantics

- Fill only fields that are absent; never silently overwrite stronger primary-source data.
- Keep a Facebook Page URL in `facebook_page_url`, not `website` or Twenty `domainName`.
- An external website published by a social Page is a `website` candidate that still requires official-site verification downstream.
- A business Page title populates `business_name` only. Never infer `name` or `person_name` from a Page title.
- Retain exact Page URL, public field value/excerpt, retrieval time, Actor ID/run ID/dataset ID and match basis.
- Conflicts are review evidence, not overwrite permission.

## Durable provider state

Persist optional Actor jobs under a separate job table or generic enrichment-job table keyed by application run, source job and deterministic request key. On retry, reuse active/succeeded jobs rather than starting another paid run. Keep provider job state separate from primary source state.

When choosing between a current-run provider row and a cross-run cursor, select one complete state owner first. Never mix individual fields from both. In SQL, do not `COALESCE(job.dataset_offset, 0)` or `COALESCE(job.dataset_exhausted, false)` when absence must fall back to a cursor: fabricated zero/false values mask real cursor state. Return null for a missing job, use `existing_job_found`, then select actor ID, dataset ID, status, offset and exhausted flag from the same owner.

## Facebook Search Scraper contract

For `apify/facebook-search-scraper` (Actor ID `Us34x9p7VgjCz99H6`), the verified input fields are:

```json
{
  "categories": ["Exact Business Name"],
  "locations": ["City, Region, Country"],
  "resultsLimit": 3
}
```

Observed output fields include `facebookUrl`, `pageUrl`, `pageId`, `facebookId`, `pageName`, `title`, `categories`, `info`, `address`, `phone`, `email` and `website`. Treat output as untrusted public data and validate every retained value.

## Verification matrix

1. No material gaps: no Actor starts.
2. Missing email only under threshold 2: no Actor starts.
3. Exact business name plus exact location: eligible for merge.
4. Same name, wrong location: no merge.
5. Two close matches: `possible_match`, no merge.
6. Page title never fills person fields.
7. External website remains an unverified candidate.
8. Actor failure retains original records and primary cursor.
9. Repeated envelope reuses the durable Actor job.
10. Primary source cursor and exhaustion fields are unchanged after enrichment.
