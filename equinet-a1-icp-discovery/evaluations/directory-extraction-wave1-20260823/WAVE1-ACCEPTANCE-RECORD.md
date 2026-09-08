# Wave 1 Directory Adapter Acceptance Record

## Decision

**Accepted for bounded pilot use**

## Approver

- Approver: Séverine
- Role: Unitalk Operations
- Approved at: 2026-08-23T15:34:39Z
- Approval source: explicit selection in the Unitalk implementation conversation

## Accepted components

| Source | Adapter | Version | Operational status |
|---|---|---:|---|
| FarrierIQ | `farrieriq` | 1.1.0 | `validated_for_bounded_pilot` |
| HAST | `hast_farriers` | 1.1.0 | `validated_for_bounded_pilot` |
| Best of Lexington | `best_of_lexington_farriers` | 1.1.0 | `validated_for_bounded_pilot` |

The bounded live extraction evidence was generated with adapter V1.0.0. V1.1.0 is a post-review hardening release that adds deterministic five-record cursors for FarrierIQ and HAST and a five-record runtime cap for all three sources. It was replayed offline against the same saved live payloads before promotion.

## Approval scope

The approval covers bounded public-directory discovery under the Source Register limits:

- maximum 20 candidates per source per run;
- maximum 50 candidates per source per day;
- concurrency 1;
- immediate stop on 403, 429, CAPTCHA, login, paywall, robots/terms conflict or unexpected sensitive data;
- no outreach, CRM write or A2 handoff;
- material claims require verification through the prospect's official business website or another permitted source when directory evidence is insufficient.

## Accepted limitations

### FarrierIQ

Séverine approved the adapter despite the identified data-quality risk. Two sampled individual profiles exposed `555` phone numbers and appeared to contain placeholder or synthetic directory data.

Mandatory controls:

- discard all `555` telephone contacts;
- treat extracted listings as discovery-only;
- do not present a FarrierIQ listing as review-ready without independent official-site verification;
- preserve uncertainty and hold unsupported identity or contact claims.

### HAST

- Legacy static HTTP source.
- The source states that its list is not complete.
- Public names and professional contacts may be retained with provenance.
- Current activity and material claims require secure-source corroboration.

### Best of Lexington

- Five visible Kentucky Farrier results in the tested snapshot.
- Low-volume source rather than broad market coverage.
- Claim links, message forms and reCAPTCHA content are excluded.
- Material directory claims require corroboration.

## Evidence

- `WAVE1-VALIDATION-REVIEW.md`
- `wave1-validation.json`
- `offline-adapter-test-results.json`
- `farrieriq-target-profile.json`
- `farrieriq-second-profile-check.json`
- runtime runs `W1-FARRIERIQ-20260823`, `W1-HAST-20260823`, and `W1-BESTLEX-20260823`
- `wave1-manifest.json`

## Boundary

This is Unitalk bounded-pilot acceptance. It is not Equinet production acceptance, permission to contact prospects, approval of directory claims, or permission to bypass third-party controls.
