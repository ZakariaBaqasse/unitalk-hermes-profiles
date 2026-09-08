# Location-scoped source adapters and durable provider state

Use this reference when generalising a stateful multi-source n8n discovery workflow from one hard-coded location to caller-supplied geography, especially when the user wants manual node-by-node edits rather than regenerated exports.

## Manual-edit delivery format

When the user requests manual changes:

1. Inspect the exact current export; do not answer from an older version.
2. Lead with the defects still present in that export.
3. Walk nodes in execution order.
4. For each changed Code or SQL node, provide a complete replacement body when intertwined edits would be ambiguous.
5. For UI-only changes, state the exact setting and value.
6. Name nodes that need no change and give the final wiring.
7. Finish with stale-string searches, bounded pin data, and expected cursor/result fields.
8. Do not regenerate, import, publish, or activate workflows unless explicitly requested.

## Canonical geography contract

Normalise geography once in the orchestrator. A country-neutral structure should carry:

```json
{
  "city": "Newmarket",
  "city_slug": "newmarket",
  "city_aliases": [],
  "region": "England",
  "region_code": "ENG",
  "region_slug": "england",
  "state": "England",
  "state_code": "ENG",
  "country": "United Kingdom",
  "country_code": "GB",
  "country_slug": "united-kingdom",
  "location_display": "Newmarket, England, United Kingdom"
}
```

Use `region` as the country-neutral field and retain `state` aliases only for compatibility. Require ISO alpha-2 `country_code`; do not guess country codes. Build a stable location key such as `GB|ENG|newmarket`, using `*` only when a region genuinely does not apply.

The durable source scope must include policy version, segment, canonical location, and any focus/query input that changes pagination.

## Orchestrator responsibilities

- Validate and canonicalise geography before creating run state.
- Keep policy permission separate from technical source capability.
- Filter unsupported sources in the ordered source plan rather than forcing local directories to arbitrary countries.
- Pass `location`, `location_key`, `source_scope_key`, `source_location_config`, remaining target, cursor, segment, and policy version through each child call.
- Validate that successful/partial child responses and non-empty cursors return the expected `location_key`.
- Persist cursors by complete source scope plus source ID.

A local brand such as a city-specific directory should remain locally constrained. An opaque provider geography such as a numeric state ID must use an explicit verified map; never derive or guess it.

## Adapter request validation

Every adapter should:

- remove silent city/state/country defaults;
- require canonical location fields needed by that source;
- validate source ID, segment, location key, and cursor type before reading the cursor;
- reject a cursor whose source, segment, or location differs;
- build and re-validate URLs against an approved host/path;
- make source job IDs geography-specific;
- preserve the orchestrator's policy version rather than reverting to a stale adapter default.

Source-specific country restrictions belong in the source capability map and defensive adapter validation, not in shared global normalisation.

## Parser and detail-enrichment boundary

The listing parser owns selected records, source exhaustion, next cursor, listing summary/warnings, and requested-location classification. The detail child may enrich records but must not replace pagination control. In the final adapter result, explicitly merge the upstream parser envelope over the detail result for `source_exhausted`, `next_cursor`, `location`, `location_key`, and scope. Prefer the child `summary` when it already merges listing and detail counts, otherwise retain the parser summary.

Do not assign the requested city to every listing. Preserve published location text and distinguish `exact_city` from weaker labels such as `source_location_page` or `region_directory`.

Return a terminal cursor with its final offset and `source_exhausted: true`; do not erase it merely because no continuation remains. Preserve the previous cursor on fetch/parse failure.

## Async dataset providers

Keep provider execution status separate from adapter/dataset status:

- provider status: `READY`, `RUNNING`, `SUCCEEDED`, `FAILED`, `TIMED-OUT`, `ABORTED`;
- job status: `RUNNING`, `PARTIAL`, `COMPLETED`, `DATASET_FAILED`, `FAILED`.

Persist raw `dataset_offset` and `dataset_exhausted`. Fetch dataset pages from the stored raw offset, and calculate raw item indexes as `dataset_offset + page index`. Do not use an offset over already-filtered records as the provider cursor.

A successful exhausted dataset must return a terminal source result without starting another paid provider run. Terminal provider failures must require explicit restart. Active-run concurrency checks must not stop at a calendar-day boundary.

## Failure handling

When a fetch node's downstream code converts provider errors into a controlled result envelope, configure the node to continue through its regular output. Do not automatically retry CAPTCHA, login, robots, 403, or 429 responses. On failure, preserve the previous cursor and mark the source non-exhausted unless evidence proves exhaustion.

## Verification checklist

- Parse the export and compile every Code-node body.
- Validate SQL punctuation, migration column types/defaults, and placeholder/replacement counts.
- Search for stale hard-coded geography, policy versions, old cursor fields, and misleading sticky-note text.
- Test one original location and one new location.
- Test cursor mismatch rejection.
- Run the same location twice and confirm non-overlapping source records.
- Confirm different locations create different source scopes.
- Confirm an unsupported source is skipped before network access.
- Confirm an exhausted provider dataset does not start a new paid run.
- Keep the workflow inactive until bounded behavioural tests pass and do not treat technical geography support as policy approval.
