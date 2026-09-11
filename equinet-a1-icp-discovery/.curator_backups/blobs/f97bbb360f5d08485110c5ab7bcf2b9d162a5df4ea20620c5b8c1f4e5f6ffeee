# Equinet discovery cursor and source-policy reference

Use this reference when the Equinet directory and Google Maps orchestrator repeats leads, visits unnecessary sources, loses cursors, or needs a source-order/volume policy change.

## Relevant workflow nodes

### Main orchestrator

- `Normalize and Validate Request`: distinguishes requested count from overfetch discovery target and builds the stable source scope.
- `Build Ordered Source Plan`: defines segment-specific source order; do not derive Horse Owner sources with an order-dependent array slice.
- `Load Run Progress`: must load cross-run cursor state by source scope, not `run_id`.
- `Decide Whether to Run Source`: applies target, exhaustion and retained controls.
- `Discovery Target Reached?`: must route directly to post-loop processing.
- `Normalize Adapter Response`: validates cursor/exhaustion contract and emits all identity aliases.
- `Persist Source Results`: must atomically claim globally new leads, persist source record IDs and advance the global cursor.
- `Build Final Discovery Result`: caps the caller-facing array to `requested_count` after the HubSpot screen.

### Directory adapters

The request-building and parser nodes must use the orchestrator-provided remaining target rather than a duplicated fixed cap. The reusable Detail Enricher must preserve upstream pagination fields. Records without a dedicated profile URL should retain listing fields without scraping the category page repeatedly.

Mad Barn offsets must accept any non-negative integer. NewHorse next links may be relative and must be normalized and host/path validated.

### Google Maps via Apify

Check all independent controls:

- request `maximumResults`;
- query-plan product (`searchStrings × max per search`);
- daily-use policy branch;
- dataset retrieval `limit` and `offset`;
- normalized-result slicing and continuation cursor;
- terminal Actor status before deciding to resume.

Removing a policy cap from only one of these leaves an effective cap elsewhere.

## Equinet policy update pattern

A source volume/order change updates both:

- `configurations/sources/approved-source-register-v1.yaml`
- `configurations/operations/a1-runtime-policy-v1.yaml`

Record an amendment with effective time, authorization basis, changed rules, retained controls and explicit implementation status. Keep historical acceptance records unchanged.

For the 2026-09-02 change, the active policy versions became source register `1.5.0` and runtime policy `3.2.0`. Fixed per-source run/day candidate caps were removed in favor of `remaining_discovery_target`; total requested candidates remained capped at 200 and concurrency remained one. The Farrier priority became Mad Barn, Google Maps, FarrierIQ, NewHorse, Best of Lexington, then HorseProFinder. Horse Owner remained Google Maps then HorseProFinder because the Mad Barn adapter was Farrier-only.

This reference records the policy shape, not operational proof. Do not claim the change is live until the corresponding n8n nodes are updated and an end-to-end run succeeds.

## V2 canonical-location orchestrator audit

The September 2026 V2 export exposed several location-specific implementation lessons:

- `Normalize and Validate Request` accepted an empty city, canonicalized only Kentucky aliases, retained the raw location object, and defaulted to stale `approved-source-register-v2`. Require city for city-scoped adapters, normalize US country aliases and all supported state name/code aliases, persist one canonical location object, and normalize accepted policy labels to the single stored register version `1.5.0`.
- Preserve the existing key convention when migrating: the parent generated lowercase city keys such as `US|KY|lexington`. Changing only capitalization creates a new durable cursor namespace.
- `Build Ordered Source Plan` had the correct policy order, but no geographic capability filter and used `horseOwnerSources.slice(-2)`. Select the explicit segment list, filter it through a capability matrix, preserve relative policy order, and throw if no adapter supports the request.
- Capability must reflect the current child code, not desired future coverage. In the audited exports, Mad Barn, Google Maps and Best of Lexington were Lexington/Kentucky-only; FarrierIQ, NewHorse and HorseProFinder used Kentucky pages with requested-city filtering. Outside the US remains policy-blocked. Widen these entries only after child URL construction, geographic filtering and cursors are made dynamic and tested.
- `Decide Whether to Run Source` should expose canonical child aliases `maximum_results = remaining_target` and `previous_position = cursor`, while retaining `location`, `location_key`, `source_scope_key` and policy fields.
- The six Execute Sub-workflow nodes required no field-map edit because every child trigger used `inputSource: passthrough`; the complete item already crossed the boundary despite exported `workflowInputs.value: {}`. Verify this trigger setting before prescribing mappings.
- `Normalize Adapter Response` should reject a non-empty cursor whose canonical location key differs from the parent and stamp accepted cursor metadata from the parent scope. Case-insensitive comparison may be used only to migrate an equivalent legacy key.
- `Persist Source Results` already keyed durable cursors by `(source_scope_key, source_id)`. Do not replace this with run-scoped state. To retain terminal diagnostics, store a successful/exhausted child cursor instead of replacing it with `{}`, while preserving the previous cursor on failed or blocked responses.
- `Create or Resume Run`, `Load Run Progress`, the Switch routes, six child call nodes and post-discovery/HubSpot nodes required no location SQL or wiring change. Add a run-scope consistency check before source execution so a reused caller-provided run ID cannot silently attach a different location to old audit/lead rows.

Verification should compare equivalent aliases (`US`/`United States`, full state name/postal code, city whitespace/case), assert identical scope keys for equivalents and different keys for distinct cities, inspect the child input item, and test the source-plan matrix for both segments before a bounded live run.

## Common hidden defects found in this workflow class

- A detail child hard-codes `source_exhausted: true` and `next_cursor: {}`, erasing the listing cursor.
- A global ledger is updated but not used to gate current-run insertion.
- A single preferred fingerprint loses alternate identity aliases across sources.
- A no-profile sentinel is still sent to a remote scraper and becomes a blank synthetic lead.
- A source adapter enforces a small default cap even after the orchestrator cap is removed.
- A dataset adapter always reads offset zero, truncates, and marks the source exhausted.
- A lookup branch replaces candidate context; an incorrectly wired one-input Merge does not restore it.
- A stale Switch route has no adapter and feeds unadapted input into normalization.

## Validation pattern

Use a dependency-free validator when possible. Assert policy versions, null per-source caps, exact priority arrays, remaining-target semantics, total request ceiling, concurrency and implementation status. For workflows, validate graph references and compile every Code-node JavaScript body. Then simulate two application run IDs and verify that the second run starts at persisted cursors and returns no prior fingerprints.
