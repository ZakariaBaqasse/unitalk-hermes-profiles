# Overlay-aware Twenty REST staging implementation

Use this blueprint when adding enrichment/scoring overlays to the deterministic Company stager. It supplements `two-lane-enrichment-staging.md` and the live field manifest; it does not authorize non-Company writes.

## Pre-write contract gate

Before creating the output directory or making any Twenty request:

1. Load `configurations/crm/twenty-company-field-manifest-v1.json` (derive the profile root from the script path; allow an explicit `--field-manifest` override for isolated tests).
2. Validate the manifest schema/object identity and every field used by staging: expected type, writable/nullable flags, whole-number metadata, and exact Select options. Reject unknown, missing, system-managed, or incompatible fields.
3. Load optional `--overlays <json>`. If supplied, require the overlay envelope's run ID and discovery-input SHA-256 to match the source and require exact one-to-one fingerprint coverage: no duplicate, missing, or unknown fingerprints.
4. Reject duplicate discovery fingerprints before plan construction.
5. Validate every overlay and its cross-field semantics. Do not silently coerce enums or treat a malformed overlay as an unscored fallback.

The normal runtime currently has no guaranteed `jsonschema` dependency, so either keep the production validator stdlib-only or add and deploy that dependency explicitly. A schema file remains useful as documentation and for development tests.

## Overlay boundary and mapping

Use the versioned `a1.twenty-company-overlays.v2` envelope, containing one overlay per exact `lead_fingerprint`. Version 2 permits a cited verified official URL to be retained when assessment fields remain explicitly unscored. The item should carry the approved boundary fields: website verification/enrichment status, verified official URL, classified segment/prospect type, qualification status, scoring status/score/band/outcome/model version, confidence score/level/method version, enrichment time, missing information, limitations, and artifact references.

Map only validated values:

| Overlay | Twenty Company |
|---|---|
| `qualification_status` | `qualificationStatus` |
| `scoring.status` | `icpScoreStatus` |
| `scoring.score` | `icpScore` |
| `scoring.band` | `icpBand` |
| `scoring.outcome` | `icpOutcome` |
| `confidence.score` | `evidenceConfidenceScore` |
| `confidence.level` | `evidenceConfidenceLevel` |

Semantic rules:

- `SCORED`: score and confidence are whole integers from 0 through 100; band, outcome, qualification, model version, confidence level, and method version are present. Zero is valid only as a real scored value.
- `NOT_SCORED`: qualification is `NOT_CHECKED`; score, band, outcome, and confidence values are null.
- `BLOCKED`: score and band are null and a non-empty deterministic block outcome is present; confidence is either a complete pair or entirely null.
- Only `website_verification_status == VERIFIED` with a valid HTTP(S) official URL may populate `domainName`. Raw n8n website/domain values remain discovery candidates and must never be promoted by the stager itself.
- For creates without an overlay, emit the explicit `NOT_CHECKED`/`NOT_SCORED` nullable tuple. Omit `domainName`.

Validate the exact action payload after create/update materialization and before recording a write attempt. Keep `position` as an MCP-only directive and strip it from REST creates.

## Safe update materialization

Duplicate lookups must select `deletedAt`, `discoveryStatus`, `discoverySourceNotes`, and all seven assessment fields in addition to identity fields. Continue using exact fingerprint first, verified domain second, and conservative name/location review holds.

For updates:

- Always omit `position` and reviewer-owned `discoveryStatus` from PATCH.
- If the incoming overlay is absent or `NOT_SCORED` and the existing Company has a complete, internally valid `SCORED` assessment tuple, omit all seven assessment fields so the prior score is preserved.
- If an existing assessment is partially populated or inconsistent, stop before write rather than destructively clearing it.
- A valid incoming `SCORED` or explicit `BLOCKED` overlay may replace the tuple.
- If no newly verified URL exists, omit `domainName` so an existing domain is preserved.
- If an exact fingerprint match and verified-domain match resolve to different active Companies, block as an identity conflict.

Put `fields_written`, `fields_preserved`, and `expected_readback` in `decision.json`. Keep the batch-level soft-deleted scan and exact fingerprint/domain hold unchanged.

## Discovery Source Notes v2

Write canonical compact JSON with `schema_version: a1.discovery-source-notes.v2`. Store run/candidate identity, public business email, website verification/enrichment state and time, prospect type and versions, qualification/scoring/confidence versions, missing-information summaries, limitations, artifact references, and whether an existing assessment was preserved.

Dedicated Company fields are authoritative. Do not duplicate numeric score, band, outcome, or confidence values in notes. Never store full pages, evidence excerpts, raw API responses, private contact data, or the canonical Prospect Candidate.

For updates, parse existing notes before replacement. Merge valid v2 metadata deterministically. Preserve compatible legacy JSON under a clearly labelled legacy member when migration is lossless; if existing notes cannot be safely parsed or retained, stop pre-write rather than silently destroying them.

## Read-back and audit

Reconcile against `decision.expected_readback`, not the original plan. Verify every field written and every field explicitly preserved. Compare Notes v2 by parsed JSON semantics. Retain the tested phone calling-code reconstruction and narrow trailing-slash URL equivalence. A mismatch remains item-scoped `sync_failed`; never retry a create.

Persist overlay and manifest hashes in batch/plan/reconciliation artifacts and a safe manifest-validation summary. Version the plan/batch/reconciliation schemas when their shapes change. Also reconcile `staging-index.schema.json` with the worker's actual disposition keys rather than silently extending the v1 schema.

## Regression suite

Cover at minimum:

- raw website candidate does not populate `domainName`;
- scored, blocked, no-site, and failed-enrichment mappings;
- score zero versus unscored null semantics;
- invalid enums, ranges, fractional numbers, URLs, tuple combinations, and manifest drift;
- overlay run/hash mismatch plus duplicate/missing/unknown fingerprints;
- canonical Notes v2 and prohibited-content exclusion;
- preservation of reviewer status, valid existing score/confidence, domain, and assessment metadata;
- malformed existing assessment blocks pre-write;
- reconciliation failure for each dedicated or preserved field;
- fingerprint/domain identity conflict;
- overlay-derived soft-deleted-domain hold;
- invalid overlays/manifests perform zero HTTP requests;
- local payload/preparation failures report `write_attempted: false`;
- all requests remain under `/rest/companies`, with existing duplicate and soft-delete tests retained.
