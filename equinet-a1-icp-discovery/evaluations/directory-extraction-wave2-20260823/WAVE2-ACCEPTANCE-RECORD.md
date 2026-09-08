# Wave 2 Directory Adapter Acceptance Record

## Decision

**Accepted for bounded pilot use with documented limitations**

## Approver

- Approver: Séverine
- Role: Unitalk Operations
- Approved at: 2026-08-23T16:17:37Z
- Approval source: explicit selection in the Unitalk implementation conversation

## Accepted components

| Source | Adapter | Version | Operational status |
|---|---|---:|---|
| HorseProFinder | `horseprofinder` | 1.0.0 | `validated_for_bounded_pilot` |
| NewHorse | `newhorse` | 1.0.0 | `validated_for_bounded_pilot` |
| Mad Barn | `mad_barn_directory` | 1.0.0 | `validated_for_bounded_pilot` |

## Approval scope

The approval covers bounded public-directory discovery under the Source Register and source-runtime profile limits:

- maximum five retained listings per source per pilot run;
- maximum 50 candidates per source per day;
- one page and concurrency 1 per source run;
- persistent request pacing;
- immediate stop on 403, 429, CAPTCHA, login, paywall, robots/terms conflict or unexpected sensitive data;
- no outreach, CRM write or A2 handoff;
- all records remain `needs_research` until official-site verification.

## Accepted limitations

### HorseProFinder

- The Kentucky listing page provides names, locations, categories and profile URLs.
- The sampled profile provided no public phone, email or official website.
- Default images and sparse profile content create an additional freshness risk.
- Use as a discovery source only and perform official-site research and freshness verification before candidate promotion.

### NewHorse

- Listings and profiles contain self-submitted descriptions and specialties.
- Public contacts may be retained only when explicitly displayed.
- Current activity and material claims require independent verification.
- Duplicate review is mandatory before candidate creation.

### Mad Barn

- Listing cards provide names, services, locations and profile URLs.
- Individual profiles may provide public phone, email and address.
- Official-site corroboration and identity reconciliation are mandatory before candidate creation.

## Duplicate decision

The `Kentucky Legend Horseshoeing` records from Best of Lexington and NewHorse remain separate source listings. Two NewHorse records also appear to represent the same business. The system records a `possible_duplicate` review signal and performs no automatic merge.

Mad Barn records `J. T. Holub, APF` and `James Holub Equine Services` separately. They require person-and-organisation reconciliation before one current candidate record is selected.

## Evidence

- `WAVE2-VALIDATION-REVIEW.md`
- `wave2-validation.json`
- `offline-adapter-test-results.json`
- three targeted profile artifacts
- three Kentucky/Lexington listing artifacts
- runtime runs `W2-HORSEPRO-20260823`, `W2-NEWHORSE-20260823` and `W2-MADBARN-20260823`
- `wave2-manifest.json`

## Boundary

This is Unitalk bounded-pilot acceptance. It is not Equinet production acceptance, permission to contact prospects, acceptance of self-submitted directory claims or permission to bypass third-party controls.
