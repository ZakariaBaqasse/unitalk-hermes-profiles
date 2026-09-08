# Twenty Company enrichment and scoring fields

## Status

Live Twenty Company metadata verified on 2026-09-02. The compact machine-readable contract is `configurations/crm/twenty-company-field-manifest-v1.json`.

## Dedicated enrichment/scoring fields

| Label | Live API name | Live type | Exact Select values / rule |
|---|---|---|---|
| Qualification status | `qualificationStatus` | `SELECT` | `ELIGIBLE`, `EXCLUDED`, `NEEDS_REVIEW`, `NOT_CHECKED` |
| ICP Score Status | `icpScoreStatus` | `SELECT` | `NOT_SCORED`, `SCORED`, `BLOCKED` |
| ICP Score | `icpScore` | `NUMBER` | Nullable whole number, 0–100 |
| ICP Band | `icpBand` | `SELECT` | `HIGH`, `MEDIUM`, `LOW`, `UNQUALIFIED` |
| ICP Outcome | `icpOutcome` | `TEXT` | Nullable deterministic outcome |
| Evidence Confidence Score | `evidenceConfidenceScore` | `NUMBER` | Nullable whole number, 0–100 |
| Evidence Confidence Level | `evidenceConfidenceLevel` | `SELECT` | `HIGH`, `MEDIUM`, `LOW` |

Use the final post-cap ICP band. Keep ICP score and evidence confidence separate. Never use score zero to mean not scored.

## Existing Company fields retained

- `name` (`TEXT`)
- `domainName` (`LINKS`, maximum one value)
- `address` (`ADDRESS`; live label is **Address**)
- `phone` (`PHONES`), used only when no Person is expected
- `email` (`EMAILS`, maximum ten values), used only when no Person is expected
- `country` (`SELECT`: `US`, `AUSTRALIA`, `NEW_ZEALAND`)
- `city` (`SELECT`: currently `LEXINGTON`)
- `state` (`SELECT`: currently `KENTUCKY`)
- `sourceUrl` (`LINKS`, maximum ten values). Its primary URL is the discovery/acquisition directory source retained from n8n; it must never be replaced by the verified official website. Its label is the normalized source hostname.
- `segment` (`SELECT`: `FARRIER`, `HORSE_OWNER`)
- `discoveryStatus` (`SELECT`: `ELIGIBLE`, `DISCOVERED`, `HELD`, `REJECTED`)
- `discoverySourceNotes` (`TEXT`)
- `discoveryFingerprint` (`TEXT`)

`createdAt`, `updatedAt`, and `deletedAt` are system-managed and must not be sent in create/update payloads.

## Fields deliberately stored in Discovery Source Notes

The final Company field set has no dedicated columns for website-verification status, enrichment status/time, prospect type, model/config versions, missing information, limitations, block reason, or artifact references. Store those as compact JSON in `discoverySourceNotes`. Public phone/email are dedicated contact fields but their owner is conditional: Person when `name` is present, otherwise Company.

Dedicated score, band, outcome, qualification, and confidence fields are authoritative for filtering and reporting. Do not store full pages, complete evidence excerpts, raw API responses, private contact data, or the canonical Prospect Candidate in notes.

## Null semantics

No website or terminal enrichment fallback:

```text
qualificationStatus = NOT_CHECKED
icpScoreStatus = NOT_SCORED
icpScore = null
icpBand = null
icpOutcome = null
evidenceConfidenceScore = null
evidenceConfidenceLevel = null
```

Successfully scored:

```text
qualificationStatus = ELIGIBLE | EXCLUDED | NEEDS_REVIEW
icpScoreStatus = SCORED
icpScore = <0..100>
icpBand = HIGH | MEDIUM | LOW | UNQUALIFIED
icpOutcome = <deterministic outcome>
evidenceConfidenceScore = <0..100>
evidenceConfidenceLevel = HIGH | MEDIUM | LOW
```

Scoring blocked after valid enrichment:

```text
icpScoreStatus = BLOCKED
icpScore = null
icpBand = null
icpOutcome = <block outcome>
```

## Stager requirements

- Load and validate the live field manifest before writes.
- Merge enrichment/scoring overlays by exact `lead_fingerprint` only.
- Validate numeric ranges and exact Select API values before dispatch.
- Populate `domainName` only from a verified official website.
- Preserve reviewer-controlled `discoveryStatus` on updates.
- Do not clear an existing valid score when an incoming overlay is absent or unscored.
- Read back and reconcile every dedicated field written.
- Keep scoring and qualification Company-level; linked-Person availability is non-scoring metadata.
- Apply duplicate/soft-delete preflight and read-back reconciliation to both expected entities.
