# HubSpot Company-name fallback in n8n

Use this pattern when an n8n workflow currently checks HubSpot Companies only by domain and many candidates lack websites.

## Boundary

- Keep the existing exact domain lookup as the primary path.
- On the no-domain branch, search the HubSpot **Company `name` property** using distinct non-empty candidate `business_name` and `name` values.
- This is not a Contact-name check. Do not imply that a personal-name lookup searched Contacts unless a separate Contact branch actually ran.
- A Company-name-only result is a `possible_duplicate` requiring human review, never an automatic clear duplicate. Names can collide across locations and businesses.
- A candidate with neither domain nor usable name must remain explicit and review-held rather than silently becoming eligible.

## Node pattern

Wire in this order:

```text
Prepare lookup
→ Has company domain?
  true  → native HubSpot Company searchByDomain → summarize → classify domain
  false → Has company name?
            true  → HTTP Request Company search → summarize → classify name
            false → build no-lookup-key review decision
→ persist one terminal HubSpot decision
→ throttle/wait
→ continue candidate loop
```

The native n8n HubSpot Company node exposes `searchByDomain` but no Company-name search. Use an authenticated HTTP Request node for the name branch:

```text
POST https://api.hubapi.com/crm/v3/objects/companies/search
```

Use the same predefined HubSpot app-token/service-key credential as the existing HubSpot node; never embed a token in headers or JSON.

For one or more exact alternatives, use the Company `name` property with `IN`. HubSpot requires lowercase search values for string properties used with `IN`:

```javascript
={{ {
  filterGroups: [{
    filters: [{
      propertyName: 'name',
      operator: 'IN',
      values: $json.hubspot_names_lower
    }]
  }],
  properties: ['name', 'domain', 'website', 'phone', 'city', 'state', 'zip', 'country'],
  limit: 5
} }}
```

Prepare names with NFKC normalization, trimmed/collapsed whitespace, de-duplication, and a lowercase API copy. Preserve the original-cased checked values for audit evidence.

## Response handling

The HTTP Search API returns one envelope such as `{ total, results }`, unlike the native HubSpot node which may emit one item per match. The summarizer must therefore flatten `row.results`, restore candidate context from the upstream preparation node, and merge both the normal and error outputs.

Recommended classifications:

- API error: `lead_status = hubspot_check_failed`, nested `status = check_failed`.
- One or more exact Company-name results: `lead_status = possible_duplicate`, nested `status = possible_match`, `match_strength = exact_name_only`, and `requires_human_review = true`.
- No result: `lead_status = eligible`, nested `status = no_match`.
- No domain and no name: use the workflow's review-held status, with nested `status = not_checked_no_lookup_key`; do not call this a completed check.

Retain all returned object IDs, matched Company names, match count, whether multiple records matched, checked values, search method, and any API error. Do not assign an invented numeric match-confidence score.

## Result-contract and SQL consistency

After introducing the fallback, a count based on `hubspot_match.status = not_checked_no_domain` no longer measures website absence. Count no-domain candidates from the immutable candidate payload instead, and track separately:

- candidates without a website/domain;
- candidates checked by exact Company name;
- candidates without any usable HubSpot lookup key;
- failed HubSpot checks;
- possible duplicates.

Remove obsolete warnings that every no-domain lead received only a partial check. Warn only for no lookup key, API failure, or a possible match.

If the final-result CTE selects only `eligible` and `possible_duplicate`, `hubspot_check_failed` rows disappear even though the summary reports them. For workflows whose policy requires failures to be review-held, include failed rows in the returned review set and order them after eligible and possible-duplicate rows.

## Contact-name fallback when explicitly required

If the approved requirement is to search HubSpot **Contacts** rather than Companies, keep the domain lookup primary and place a native HubSpot `contact` / `search` node only on the no-domain branch. HubSpot Contacts use `firstname` and `lastname`; there is no standard Contact `name` property equivalent to Company `name`.

Use the lead's explicitly selected person-name field as the search query, request only the minimum disambiguation properties, and then post-filter returned rows by an exact case-insensitive NFKC-normalized `firstname + lastname` comparison. The API query is candidate generation, not duplicate proof, because Contact text search also searches email, phone and company fields. A name-only Contact result is always `possible_duplicate` / `possible_match` with human review, never an automatic clear duplicate. Preserve all exact-match Contact IDs, the checked name, result count and API errors; do not persist unrelated returned contact details.

A no-domain candidate with no usable person name must receive an explicit no-lookup-key review outcome. Update final-result counts and warnings so a successful Contact-name check is not still reported as `not_checked_no_domain`, and ensure failed checks remain visible in the review result when policy requires it.

### Persistence and loop-integrity traps

Keep orchestration identifiers from the candidate envelope, not the nested source payload. If `Load Candidates` emits top-level `run_id` and `lead_fingerprint`, the preparation node must preserve them as `$json.run_id` and `$json.lead_fingerprint`; `payload.run_id` is usually absent. A PostgreSQL `UPDATE ... RETURNING` that matches zero rows may still surface as a technically successful node result, so return an explicit `persisted` boolean and fail the workflow when it is false. Otherwise every lead can remain `discovered` while the final query legitimately returns no rows because it selects only terminal screening statuses.

Avoid connecting both outputs of a CRM search node to the same downstream summarizer when `Always Output Data` and `Continue using error output` are both enabled. On one failed request, n8n can emit an empty main-output placeholder plus the real error-output item, producing two decisions, two loop returns and repeated finalization. Prefer one terminal path per candidate: continue errors on the regular output and connect only that output, or explicitly deduplicate the branches before persistence.

Inside item loops, restore candidate context with item linkage (`$('Prepare Lookup').item.json`) rather than `.first()`. Delayed placeholder/error branches can make `.first()` reuse the wrong candidate, often the final item in the batch.

For Contact search, verify the credential has the read scope required for Contacts before enabling the branch. Preserve the proper URL-to-hostname parser in the shared lookup-preparation node; do not replace domain canonicalization with lowercasing the raw URL.

Use these invariants in bounded tests:

- `N` loaded candidates produce exactly `N` classified decisions and `N` successful persistence updates;
- every persistence result reports that one row was matched;
- the candidate loop's done output fires once;
- the final-result node executes once;
- `discovered_count` equals the sum of terminal statuses plus any intentionally pending rows;
- if `discovered_unique > 0` but `returned = 0`, inspect persisted row statuses and update-match counts before blaming final aggregation.

## Verification matrix

Pin or fixture at least these cases before publishing:

1. Existing domain → unchanged clear domain duplicate.
2. No domain + matching `business_name` → possible duplicate.
3. No domain + matching `name` only → possible duplicate.
4. Distinct business/name values; either one matches → possible duplicate.
5. No domain + no name match → eligible/no match.
6. No domain + no usable name → explicit review-held no-key result.
7. HTTP 401, 429, and 5xx → failed check preserved in final review output.
8. Multiple HubSpot Companies with the same name → all IDs preserved and human review required.

Syntax-check replacement Code-node JavaScript independently, then run a bounded n8n test. Do not claim the production path is validated until a real execution proves both the new branch and final persisted/result contract.