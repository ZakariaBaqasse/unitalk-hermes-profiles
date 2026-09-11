---
name: n8n-stateful-orchestration
description: Use when auditing stateful n8n loops and cursors.
version: 1.5.0
author: Unitalk AI Collaborator
license: MIT
platforms: [linux]
status: active
metadata:
  hermes:
    tags: [n8n, pagination, cursor, deduplication, orchestration, policy]
    related_skills: [equinet-n8n-discovery-control, mcp-server-connectivity-testing]
---

# Stateful n8n Orchestration

Use this skill for multi-source or paginated n8n workflows that must resume across executions, stop at a target, prevent duplicate outputs, or enforce a versioned source policy.

## Operating sequence

1. Inspect the current workflow export or live workflow; do not infer wiring from names.
2. Identify the application run key, durable scope key, cursor owner, global identity store, and caller-facing result limit.
3. Trace one item through every parent and child workflow. Record where control fields are replaced rather than merged.
4. Separate policy changes from workflow implementation. Version and validate policy first, then edit workflows, then run a bounded live test.
5. If the user requests analysis or edit instructions only, do not generate, import, publish, or modify workflow artifacts.

## State model

Keep these concerns separate:

- **Per-run audit state:** status, counts and errors for one execution.
- **Cross-run continuation state:** cursor keyed by the complete search scope and source, never by application run ID alone.
- **Global identity state:** canonical fingerprints and all stable aliases.
- **Consumed source records:** durable source record IDs independent of run ID.

A scope key should include every input that changes pagination semantics, such as policy version, segment, canonical geography, normalized focus and source ID. Normalize geography once in the parent, pass the canonical location through every child, and reject a cursor whose `location_key` differs from the request. Normalize accepted policy-version aliases to one stored value as well; otherwise two labels for the same policy create separate cursor namespaces. Keep intrinsically local sources fixed and skip them outside their supported location instead of fabricating a dynamic URL.

Keep the orchestrator-owned external source scope distinct from any provider-internal job scope. A child may append source, actor, query-plan or build dimensions to an internal `provider_scope_key`, but its top-level `source_scope_key` and returned cursor `scope_key` must match the parent scope exactly. Do not weaken strict parent validation to accept arbitrary provider suffixes; fix the child contract and store the internal provider scope separately.

Treat a caller-supplied application run ID as immutable once persisted. Before resuming it, compare the stored segment, location key, source scope, requested count and policy with the normalized request; reject mismatches rather than moving an existing run and contaminating its audit and lead rows.

Advance a cursor only after a validated successful or partial response. Preserve the prior cursor on blocked or failed responses. Record exhaustion separately from request completion. A later parent-stage failure may occur after a successful source cursor was already committed; inspect preceding failed executions before diagnosing an apparently premature resume or exhaustion.

## Global-new admission

A ledger upsert alone does not exclude old records. Resolve all available identity aliases first, atomically claim unseen canonical fingerprints, and insert into the current run only records claimed by that run. Allow later sources in the same run to enrich an already-claimed record.

Use stable source IDs, Place IDs, domains, normalized phones and name/address keys. Never use a page-local array index as durable identity.

## Loop and target semantics

`Loop Over Items` drains its queue unless an explicit branch leaves the loop. A skip node is not a break. Enforce a one-input/one-feedback invariant: each candidate may send exactly one item back to the loop. In particular, do not combine `alwaysOutputData: true`, `continueErrorOutput`, and connections from both regular and error outputs to the same downstream normalizer; on failure this can emit both an empty regular placeholder and an error item, doubling persistence and repeatedly firing the loop completion output. Prefer one normalized success/error output path or explicitly suppress the companion placeholder.

When a Code node rebuilds an item, preserve envelope identifiers such as `run_id` and `lead_fingerprint` from the top-level input unless the validated contract explicitly nests them. Inside split-batch loops, use paired-item context (`.item`) or an explicit context merge rather than `.first()`, which can bind delayed or parallel branch output to the wrong candidate. Treat a persistence node returning a generic success marker as insufficient proof: assert that `UPDATE ... RETURNING` affected exactly one expected row before feeding the loop back.

After persisting each source result:

1. Recalculate newly claimed records.
2. Compare them with the discovery target.
3. Route target-reached directly to post-loop processing.
4. Otherwise continue to the next non-exhausted source.
5. Apply the caller-facing result limit after downstream duplicate screening.

When persistence uses PostgreSQL data-modifying CTEs, do not recalculate the current count by querying the modified base table inside a sibling CTE and assume it sees the new rows. Derive the immediate count from the pre-statement persisted count plus the current claim/`RETURNING` CTE, taking care not to count conflict updates as new inserts. Otherwise target progress can lag one source and trigger unnecessary downstream adapters.

Distinguish `requested_count` from `discovery_target`. An overfetch factor of two means a request for 40 seeks 80 discovered records unless the request or default uses factor one.

## Child-workflow contract

Child enrichment must preserve the parent adapter's cursor, exhausted flag, status, warnings, errors, source URL and retrieval metadata. Empty batches must bypass remote fetches and must not produce synthetic blank records. Validate relative next-page URLs after resolving them against the current page.

Build source plans from an explicit capability matrix based on the deployed children. Filter unsupported sources without changing the relative policy order of retained sources, and fail clearly if no active child supports the requested scope. Do not infer broad geographic support from a statewide directory URL or a provider's theoretical coverage.

For Execute Sub-workflow nodes, inspect the child trigger before prescribing field mappings. A child trigger configured with `inputSource: passthrough` receives the whole incoming item even when the parent's exported `workflowInputs.value` is empty. In that case, preserve the parent item and add canonical contract aliases such as `maximum_results` and `previous_position` before the call; do not add redundant mappings that can accidentally omit `location`, `location_key`, or `source_scope_key`.

For asynchronous dataset providers, keep provider execution status separate from adapter/job status. Persist the provider run ID, dataset ID, raw dataset offset and exhausted flag; fetch from that raw offset and calculate provider record indexes from it. Never use an offset over filtered records as the provider cursor, overwrite a provider `SUCCEEDED` status with an adapter `COMPLETED` label, automatically restart terminal failures, or start another paid run after a successful dataset is exhausted. Active-run concurrency checks must not stop at a calendar-day boundary.

A source contract failure must not admit the child records. In the parent normalizer, clear records, preserve the previously committed cursor and prior exhaustion state, and retain the structured error. Add a second guard in persistence SQL so only normalized successful statuses such as `partial` and `exhausted` can update the global ledger, aliases, source provenance, or consumed-source-record table. This prevents a failed response from silently consuming records or advancing durable state.

## Manual workflow-edit guidance

When the user asks for manual edits rather than regenerated workflow JSON, inspect the latest export and give instructions in node execution order. Lead with defects still present, provide complete replacement bodies for intertwined Code/SQL changes, state exact UI settings and wiring, list nodes that need no changes, and finish with stale-string searches plus bounded test data. Do not regenerate, import, publish, or activate the workflow unless explicitly requested.

For adding a safe HubSpot Company-name fallback behind an existing domain check—including HTTP Search API setup, name-only review classification, result-SQL consistency and bounded fixtures—read `references/hubspot-company-name-fallback.md`.

For the complete country-neutral location contract, source-capability pattern, parser/detail boundary, async provider-state design and verification checklist, read `references/location-scoped-adapters-and-provider-state.md`.

For reusable directory detail enrichment—listing/detail state ownership, no-profile preservation, evidence-gated field merging, item-level failure status, source access barriers and bounded tests—read `references/directory-detail-enrichment-boundaries.md`.

## Policy changes

When source order or volume rules change:

1. Update the authoritative source register and runtime policy as a documented versioned amendment.
2. Keep historical acceptance records unchanged.
3. Update every workflow enforcement point: orchestrator plan, SQL remaining-target calculation, adapter request caps, parser defaults, child batch guards, provider planning and dataset retrieval.
4. Preserve unrelated safety controls unless explicitly changed, especially concurrency, cost visibility, access/robots/CAPTCHA/rate-limit stops, no-outreach and CRM boundaries.
5. Mark implementation and live validation pending until workflows are actually updated and exercised.

## Compact-result forensic triage

When production controls permit retrieval only of the compact final-result node, diagnose a zero-lead run without broad execution-data retrieval:

1. Separate engine status from business status. A technically successful execution with `discovery_failed` means the finalizer found zero persisted candidates; it does not prove source availability, HubSpot screening, or a transport failure.
2. Compare the compact result's `source_scope_key`, policy version, `sources[]`, candidate totals, and elapsed duration with earlier persisted results for the same scope. An empty `sources[]` plus a very short run can indicate that planned sources were skipped before adapter persistence.
3. Inspect the **live workflow definition** (not stale notes) for the source-policy normalization and source-skip code. A hard-coded or overwritten policy version inside `source_scope_key` can silently reuse an obsolete cursor namespace. If `completed`/`exhausted` cursor statuses bypass adapter calls, that is a strong, but not database-proven, explanation for an empty source list.
4. State the evidence level precisely. Do not claim the exact cursor rows without a permitted read. Call it a high-confidence inference only when the static skip path, matching historic scope, historic exhausted source results, empty current sources, and elapsed duration all agree.
5. Hold the run rather than rerun it. Repair the policy normalization, scope construction, and any location comparisons; publish and run a bounded validation before resuming discovery.

A source-policy version must be validated against the active register rather than unconditionally replaced in workflow code. The canonical accepted policy label must flow unchanged into the durable source scope; otherwise old cursors and consumed-record state may contaminate a new policy run.

## Verification

- Parse all JSON/YAML artifacts.
- Verify unique node names/IDs and valid connection targets.
- Compile Code-node JavaScript without executing n8n globals.
- Check SQL placeholder counts against query replacements.
- Compare the n8n engine status with the workflow's business-result status; a technically successful execution may intentionally return a controlled failure envelope.
- Compare the parent scope with both the child top-level scope and returned cursor scope.
- Simulate two independent run IDs to verify cursor continuation, globally new counting, early exit and non-overlapping outputs.
- Verify failed or blocked adapter results cannot mutate lead, alias, source-provenance, consumed-record, or forward-cursor state.
- Run a bounded live test before claiming operational readiness.

For the Equinet-specific node map and policy-update pattern, read `references/equinet-discovery-cursor-and-policy.md`.

For converting or auditing legacy location-bound adapters for canonical geography, fixed-location applicability, exact-city filtering, cursor scope and no-profile detail behavior, read `references/location-scoped-directory-adapters.md`.

For the PostgreSQL data-modifying CTE counting trap and the execution-history method for diagnosing cursors advanced by failed parent runs, read `references/postgres-cte-and-failed-run-cursor-diagnostics.md`.

For diagnosing provider-success/parent-failure cursor mismatches, separating external and provider scopes, blocking failed-batch persistence, and recovering paid provider datasets without restart, read `references/cursor-contract-failure-and-failed-batch-persistence.md`.
