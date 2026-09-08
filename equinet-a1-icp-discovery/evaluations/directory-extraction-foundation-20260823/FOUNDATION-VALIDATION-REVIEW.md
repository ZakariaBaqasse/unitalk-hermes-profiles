# Shared Directory Extraction Foundation — Validation Review

## Decision requested

Approve Step 1 as **FOUNDATION VALIDATED — LIVE SOURCE ADAPTERS NOT ENABLED** and authorise progression to Wave 1 adapter implementation.

## Scope delivered

The shared foundation now provides:

- a provider-neutral bounded directory runner;
- a lazy Firecrawl transport that performs no network access on import;
- a fixture transport for deterministic testing;
- Source Register, active-source, segment, host, per-run, daily and implementation-readiness gates;
- safe run identifiers and US geography enforcement;
- configurable pacing and one-retry transient-error handling;
- immediate stop handling for HTTP 403, HTTP 429, CAPTCHA, login, paywall, robots and terms conflicts;
- canonical URL cleanup, stable listing IDs and deterministic listing normalisation;
- JSON Schema validation for directory listings, source runtime profiles, coverage and audit records;
- atomic JSON writes and locks for per-source execution and shared state;
- deduplication through a durable listing index;
- partial-scan cursor persistence and fresh-complete-coverage reuse;
- immutable raw-page artifacts per run;
- an A1 Research Seed handoff that remains `needs_research` until official-site verification;
- hash-linked append-only audit events that explicitly prohibit outreach, CRM writes and A2 handoffs;
- deterministic replay with an injected clock;
- rejection of direct Google Maps collection when the approved Apify integration is still pending.

## Configured source profiles

Six source runtime profiles are present. They are configuration records only; no live adapter is enabled.

| Wave | Source | Foundation status |
|---|---|---|
| 1 | FarrierIQ | Pending targeted profile test |
| 1 | HAST | Foundation only |
| 1 | Best of Lexington | Foundation only |
| 2 | HorseProFinder | Pending targeted profile test |
| 2 | NewHorse | Pending targeted profile test |
| 2 | Mad Barn | Pending targeted profile test |

## Deterministic validation result

- Foundation tests: **43 passed, 0 failed**
- Foundation validator: **passed**
- Python compilation: **passed**
- Source Register validator and regression suite: **passed**
- Runtime policy validator: **passed**
- Existing Wave 1 skill regression suite: **passed**
- Recovery and runtime blocklist suite: **passed**
- Network requests during this foundation evaluation: **0**
- Live source adapters enabled at foundation validation: **0**; current post-Wave-2 state: **6 validated adapters**

The synthetic suite verified:

- valid two-page extraction;
- deterministic normalisation;
- duplicate detection;
- complete and partial coverage states;
- next-cursor preservation;
- fresh-coverage fetch suppression;
- HTTP 429 stop without retry;
- one controlled retry for HTTP 503;
- per-run and daily limits;
- host restrictions;
- live-mode rejection before adapter acceptance;
- unsafe run-ID rejection;
- non-US rejection;
- concurrency locking;
- hash-linked append-only audit verification;
- byte-identical replay with fixed time and identical fixtures;
- direct Google Maps bypass prevention;
- on-disk audit validation;
- compatibility with the existing A1 Research Seed contract;
- zero external actions.

## Storage locations

- Reusable code: `skills/public-prospect-research/scripts/directory_extraction/`
- Schemas and usage reference: `skills/public-prospect-research/references/directory-extraction/`
- Equinet configuration: `configurations/directory-extraction/`
- Mutable pilot state: `runtime/directory-extraction/`
- Test evidence: `evaluations/directory-extraction-foundation-20260823/`

## Limitations and next gate

This step does not prove that any of the six source-specific adapters works live. It intentionally made no Firecrawl request. Runtime profiles remain non-live until their adapter implementation and bounded acceptance tests pass.

The next proposed gate is **Wave 1 — FarrierIQ, HAST and Best of Lexington**. It requires explicit approval before live bounded requests are made.
