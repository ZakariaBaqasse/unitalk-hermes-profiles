# Location-scoped directory adapters

Use this checklist when converting a pilot-bound directory adapter to canonical geography while retaining each source's real coverage limits.

## Request normalization

- Normalize geography once in the orchestrator; adapters validate and consume it but do not invent defaults.
- Require `city`, `country`, two-letter `country_code`, and canonical `location_key`. Use country-neutral `region`/`region_code`, with `state`/`state_code` only as compatibility aliases.
- Use supplied `city_slug`, `region_slug`, and `country_slug` only when the provider's route pattern is verified. Opaque provider IDs and uncertain routes belong in explicit `source_location_config`, never in guessed slug or ordinal logic.
- Build a canonical location key from every pagination-relevant dimension, for example `US|TX|fort-worth` or `GB|ENG|newmarket`; use `*` when region does not apply.
- Validate an incoming cursor's `source_id`, `segment`, `location_key`, and provider mode/scope before reading its offset or URL. Compare canonical keys consistently; tolerate case only when deliberately migrating an older equivalent key.
- Keep policy approval separate from technical normalization: country-neutral data structures do not authorize production discovery outside the versioned source policy.

## Dynamic versus fixed-location sources

For genuinely geographic sources, derive the provider URL from normalized location fields and keep host/path allowlists fixed. A location word inside a provider hostname or source ID is source identity, not necessarily a hardcoded request assumption.

For a source that is intrinsically tied to one place:

1. Keep its fixed URL and place-specific parser.
2. Add an applicability branch before the network request.
3. For other locations, return a successful empty result with `source_exhausted: true`, an explicit terminal cursor or documented empty terminal cursor, and an explicit `skipped_not_applicable` summary/warning.
4. Do not throw and do not perform the remote fetch merely to discover it is inapplicable.

For a source whose routing depends on opaque IDs or not-yet-verified path conventions, require explicit provider route configuration. If it is absent, use the same no-network exhausted-skip path. Validate continuation URLs against the exact configured provider ID/path, not merely a broad hostname prefix.

## Provider-pattern examples

Treat these as patterns to verify against the active source policy and a bounded live fixture, not as permission to crawl a new geography:

- **Mad Barn:** location pages use a city/full-state slug such as `/service/farrier/location/miami-florida/`; build it only from canonical `city_slug` and `state_slug` and keep the host/path allowlist fixed.
- **FarrierIQ:** state directories use full-state slugs such as `/directory/texas`; parse both the supplied state name and two-letter code, then paginate the exact-city subset.
- **Best of Lexington:** intrinsically Lexington/Kentucky-specific; keep its URL fixed and skip it elsewhere.
- **NewHorse:** geographic selectors are opaque IDs such as `g.17`; maintain an explicit verified location-to-ID map and skip unmapped locations. Never infer an ID from a region name or ordinal. Validate every current/next-page URL against the same configured `g.*` path before fetching.
- **HorseProFinder:** mode and geography are path segments. Use `farriers` only for the Farrier branch and `stables` for the Horse Owner commercial-operation proxy. Require explicitly verified country/region/city path slugs, and validate every profile URL against the selected mode and exact configured route. Never label a Stable as an individual horse owner.
- **Google Maps dataset adapters:** construct the provider location query from canonical display fields, filter returned city/state/country against canonical aliases, and carry `location_key` in provider and dataset cursors.

A source-capability plan should filter inapplicable adapters before invocation while preserving the approved source order. If provider-specific configuration must survive a database progress node, explicitly select it in that node's SQL output; passthrough fields from the original source-plan item otherwise disappear.

## Record geography

- Do not relabel nearby/statewide records as exact-city matches merely because they came from a city landing page.
- Parse or test the published location, assign `location_match`, and paginate only the eligible exact-location set.
- If address text cannot be safely decomposed, retain the raw address but populate city/state only when the requested city/state is explicitly evidenced.
- Keep parser summaries explicit: `raw_records`, `eligible_records`, `filtered_out_by_location`, and `exact_city_records`.
- A state-wide page with records but no exact-city matches is a valid exhausted empty result, not a parser failure.

## Cursor and failure invariants

- Build every successful partial or terminal cursor with the dynamic canonical `location_key`, source ID, segment, scope key, and provider mode; never leave the pilot key hardcoded.
- Preserve a terminal cursor with the final offset/page/provider state when traceability matters. A deliberately empty terminal cursor is acceptable only when the parent contract explicitly treats exhaustion as the complete terminal state.
- On fetch or parser failure, keep `source_exhausted: false` and return the prior cursor unchanged so the same page can be retried.
- Only advance the offset against the eligible record collection, not against raw out-of-scope records. Dataset providers are different: their raw dataset offset advances by every fetched raw row, including filtered or duplicate rows.
- An intentional fixed-source applicability or unconfigured-route skip is different from failure: it is exhausted, does no remote work, and carries an explicit skip reason.

## Detail-enrichment child workflows

When an adapter calls a detail enricher, verify that the child carries forward `location`, `location_key`, `source_scope_key`, `source_exhausted`, and `next_cursor`. The child must not recompute pagination from enriched records.

Preserve listing-only records that have no profile URL. Route them around remote detail fetching, annotate them as skipped for detail enrichment, and include them unchanged in the final records array. This is especially important for directory category pages that publish useful contact fields but no dedicated profile links.

A child detail failure must not be hidden by an exhausted listing page: if any item-level detail fails, the child and outer source result remain `partial` while preserving the adapter's exhausted flag and terminal cursor. For the full boundary, evidence checks, failure semantics, and verification matrix, read `directory-detail-enrichment-boundaries.md`.

## Audit procedure

1. Parse the workflow export and enumerate every node before recommending edits.
2. Search node parameters and code for pilot city/state names, state codes, country literals, URL slugs, `location_key`, cursor, exhaustion, and profile handling.
3. Separate legitimate provider identity/allowlist strings from request-dependent geography.
4. Trace success, valid-empty, non-applicable, fetch-failure, parse-failure, and no-profile paths through the actual connections.
5. Give node-by-node manual edits and explicitly list nodes needing no change.
6. Validate JSON structure, unique node names, connection targets, and Code-node JavaScript syntax without modifying the source artifacts.
