# Cursor-Exhaustion Zero-Lead Diagnosis (Live Case: Lexington KY Horse Owner, 2026-09-10)

Concrete worked example of the `discovery_failed`-with-zero-leads triage pattern. Use it to recognise and report an exhausted-source-cursor run without over-claiming or re-running.

## Live execution evidence

- Workflow: `A1 - Equinet Discovery Orchestrator - Directories and Google Maps-v2` (`3tBw9IHcr4knwM4H`), active, MCP-exposed.
- Execution `1345`, mode `webhook`, engine status `success`, started `2026-09-10T19:32:26.173Z`, stopped `19:32:27.367Z` — **~1.2s total**.
- Compact `Build Final Discovery Result` (retrieved once, `includeData: true`, `nodeNames: ["Build Final Discovery Result"]`, `truncateData: 1`):
  - `contract_version: a1.discovery-result.v1`
  - `run_id: A1-20260910193226-DUP9WC`
  - `status: discovery_failed`
  - `request.source_scope_key: "2.0.0|horse_owner|US|KY|lexington|focus:"`
  - `source_policy.registry_version: 2.0.0`
  - `summary`: `eligible 0, returned 0, discovered_unique 0, possible_duplicates 0, hubspot_* all 0`
  - `leads: []`, `sources: []`, `warnings: []`

## Why zero leads — both planned sources skipped on exhausted cursors

The execution `contextData."node:Loop Over Sources".processedItems` showed each planned source item with `should_run: false`, `skipped: true`, `source_status: "exhausted"`, `source_exhausted: true`, and a cursor `updated_at` from the **previous day (2026-09-09)** for the identical scope key:

1. `integration.apify_google_maps_scraper` ("Google Maps via Apify", order 1) — cursor `mode: apify_dataset`, `state.dataset_exhausted: true`, `actor_status: SUCCEEDED`, `dataset_offset: 80`, `dataset_id: fE3Cg05fYPkPbF4tD`. `source_exhausted: true`.
2. `pdf.horseprofinder` ("HorseProFinder", order 2) — cursor `mode: not_configured`, `state: {offset: 0, source_mode: stables}`, `source_exhausted: true`, `last_successful_record_id: null`.

`noItemsLeft: true`, `done: true` on the source loop. The HubSpot loop received only a `control_only` placeholder with `lead_fingerprint: null` — nothing to screen.

Interpretation: this was **not a live scrape that found nothing**. The stateful cursor store already marked every approved source for `horse_owner|US|KY|lexington` as exhausted from a prior run, so the orchestrator skipped all adapters and finalized as `discovery_failed` with zero candidates in ~1 second.

## Recognition signature (report this shape precisely)

A zero-lead run is a cursor-exhaustion skip, not a genuine "no inventory" result, when ALL of these agree:

- engine `status: success` but business `status: discovery_failed`;
- `summary` all zeros AND `sources: []` AND `warnings: []`;
- elapsed time ~1–2s (far too short for any real adapter fetch);
- `contextData` source-loop items show `should_run: false` / `skipped: true` / `source_exhausted: true` with a cursor `updated_at` predating the run for the same `source_scope_key`.

State it as: "the run resumed against existing exhausted source cursors; no approved source was queried." Do NOT say "Lexington has no horse farms" and do NOT claim the exact DB cursor rows were read — the evidence is the execution context and timing, which is a high-confidence inference, not a direct cursor-table read.

## Operator handling

- Do not re-fire the same scope expecting different output; the cursors are durable and will skip again.
- Do not fabricate leads, do not create a zero-coverage staging index, do not consume a ticket on it.
- Cursor reset / adding a new approved source / widening geography is an **operator action on the n8n cursor store** — the AI Collaborator cannot reset cursors from MCP.
- Valid user-facing paths: (1) expand geography to adjacent in-scope counties with unexhausted cursors, (2) request an operator cursor reset for the exhausted scope, (3) switch segment if that segment's cursors differ.
- A `mode: not_configured` cursor that is simultaneously `source_exhausted: true` (as on `pdf.horseprofinder`) is worth flagging to the operator — it suggests the source was marked exhausted without a real configured fetch, which may be a stale or over-broad exhaustion flag rather than genuine inventory depletion.
