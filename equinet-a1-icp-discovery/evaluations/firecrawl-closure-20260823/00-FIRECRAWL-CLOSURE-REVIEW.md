# Firecrawl Closure Review — Equinet A1 Bounded No-Integration Pilot

**Status:** `firecrawl_scope_closed_for_bounded_no-integration_pilot`
**Closure ID:** FCR-20260823-469CA5
**Approved by:** Séverine (Unitalk Operations)
**Decision recorded at:** 2026-08-23T19:40:55Z
**Pilot run:** LIVE-20260823T170816Z-469CA5

---

## 1. Scope

This closure reconciles the complete twelve-source directory pathway set that was approved under Source Register V1.4.3 and Runtime Policy V1.7.3. It documents every pathway's tested state, limitations and integration requirement. It does **not** authorise production use, candidate acceptance, outreach, CRM writes or A2 handoff.

## 2. Twelve-Source Smoke-Test Totals

| Category | Count |
|---|---|
| Completed | 6 |
| Partial | 5 |
| Blocked | 1 |
| **Total** | **12** |

### Adapter readiness

| Category | Count |
|---|---|
| Validated adapters (Wave 1 & 2) | 6 |
| Sources without an adapter | 6 |
| **Total** | **12** |

### Validated adapters (6) — tested, approved and frozen

| Source | Adapter | Version | Wave | Adapter coverage | Runtime readiness |
|---|---|---|---|---|---|
| FarrierIQ | `farrieriq` | 1.1.0 | 1 | partial | `validated_for_bounded_pilot_with_data_quality_controls` |
| HAST Farrier Directory | `hast_farriers` | 1.1.0 | 1 | partial | `validated_for_bounded_pilot_with_freshness_warning` |
| Best of Lexington | `best_of_lexington_farriers` | 1.1.0 | 1 | complete_snapshot | `validated_for_bounded_pilot_low_volume` |
| HorseProFinder | `horseprofinder` | 1.0.0 | 2 | partial | `validated_for_bounded_pilot_no_profile_contact_and_freshness_warning` |
| NewHorse | `newhorse` | 1.0.0 | 2 | partial | `validated_for_bounded_pilot_with_self_submitted_content_controls` |
| Mad Barn | `mad_barn_directory` | 1.0.0 | 2 | partial | `validated_for_bounded_pilot_with_identity_reconciliation` |

### No-adapter sources (6) — smoke-tested, no adapter implemented

| Source | Smoke status | Runtime readiness |
|---|---|---|
| American Farrier's Association | partial | `technical_access_preflight_required_no_adapter` |
| Professional Farriers Directory | partial | `partial_context_only_no_public_directory_adapter` |
| Farrier Industry Association | blocked | `member_search_blocked_recaptcha_public_context_pages_only_no_adapter` |
| EDSS Farrier Search | partial | `partial_kentucky_form_submission_unsupported_no_adapter` |
| BWFA Kentucky | partial | `partial_landing_only_low_volume_no_adapter` |
| EquineNow Kentucky Farms | partial | `partial_landing_only_horse_owner_use_only_no_adapter` |

## 3. Wider Source Register Categories (outside the twelve-source set)

| Category | Count |
|---|---|
| Blocked commercial sources (Yellow Pages, Yelp, EquineProFinder, O Horse) | 4 |
| Conditional manual-only (IAPF Member Directory, The Majestic Horses, Horse Council) | 3 |
| Integration-pending (Apify Google Maps) | 1 |
| Needs verification (Google Places API) | 1 |
| Unavailable / no licence (Clay, Apollo) | 2 |
| Unavailable integrations (HubSpot, Twenty) | 2 |

## 4. End-to-End Pilot Summary

The staged pilot ran through all four gates (research, qualification, scoring, review_export). Three Farrier candidates were produced: **J.T. Holub** (James Holub Equine Services, Lexington KY), **Bobby Menker** (Bobby Menker Horseshoeing, Lexington KY), **Kentucky Legend Horseshoeing** (Richmond KY). All candidates have `needs_research` recommendation. All human decisions remain pending.

### Candidate decisions — all pending

| Decision | Count |
|---|---|
| Accept | 0 |
| Reject | 0 |
| Needs Research | 3 |

## 5. Integration Status

| Integration | Status |
|---|---|
| HubSpot duplicate/exclusion/consent checks | unavailable |
| Twenty staging/review | unavailable |
| A2 enrichment | not triggered, not authorised |
| Apify Google Maps | integration_pending |
| Google Places API | needs_verification |
| Clay / Apollo | unavailable (no licence) |

## 6. Tests Executed

| Test suite | Status | Pass | Fail |
|---|---|---|---|
| Source Register validation | passed | 38 sources validated | 0 |
| Source Register tests | passed | 26 tests | 0 |
| Runtime policy validation | passed | all checks | 0 |
| Foundation validation (offline fixture) | passed | 43 tests | 0 |
| Wave 1 adapter offline tests | passed | 26 tests | 0 |
| Wave 2 adapter offline tests | passed | 45 tests | 0 |
| Recovery tests | passed | 23 tests | 0 |
| **Total** | — | **passed** | **0** |

All tests used saved live payloads or synthetic fixtures. No network requests were made during closure validation.

## 7. Final Active Versions

| Component | Version |
|---|---|
| Source Register | 1.4.3 |
| Runtime Policy | 1.7.3 |
| Directory Runtime Profiles | 1.6.1 |
| Public Prospect Research skill | 2.0.0 |
| Wave 1 adapters (FarrierIQ, HAST, Best of Lexington) | 1.1.0 |
| Wave 2 adapters (HorseProFinder, NewHorse, Mad Barn) | 1.0.0 |

## 8. Evidence Files

- `01-source-matrix.json` — 12-source reconciliation: 6 completed, 5 partial, 1 blocked; 6 validated adapters, 6 no adapter
- `02-frozen-component-register.json` — 48 files with SHA-256 verification; all hashes match
- `03-deferred-unsupported-pathway-register.json` — blocked, manual-only, integration-pending, unavailable and deferred pathways
- `04-closure-acceptance-record.json` — a prepared acceptance record awaiting Séverine's final decision
- `05-hash-manifest.json` — non-recursive SHA-256 manifest of the five other closure artifacts

## 9. Limitations

- All three pilot candidates remain at `needs_research` — no accept/reject decisions recorded
- HubSpot and Twenty unavailable for duplicate/exclusion checks
- Apify Google Maps integration pending (credential test, Actor runtime, billing controls, audit capture)
- Google Places API needs verification (account, scopes, costs, attribution, storage)
- Kentucky Legend Horseshoeing cross-source duplicate group unresolved
- Bobby Menker and Kentucky Legend Horseshoeing lack verified standalone official websites
- No Horse Owner segment candidates were produced in this all-Farrier pilot
- Provider cost is unknown for several tested sources
- Candidate approval, outreach, CRM writes and A2 handoff are prohibited and have not occurred

## 10. Final Closure Decision

Séverine approved the Firecrawl scope closure for the bounded no-integration pilot on 23 August 2026. This decision does **not** authorise production acceptance, candidate acceptance, outreach, CRM writes or A2 handoff — those remain separate gates.