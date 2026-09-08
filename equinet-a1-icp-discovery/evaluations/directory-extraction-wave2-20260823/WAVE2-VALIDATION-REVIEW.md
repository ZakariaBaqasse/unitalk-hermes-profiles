# Wave 2 Directory Adapter Validation Review

## Decision recorded

Séverine approved HorseProFinder, NewHorse and Mad Barn for bounded pilot use with the limitations below on 23 August 2026.

## Scope

Wave 2 implemented and tested source-specific adapters for:

- HorseProFinder Kentucky Farriers;
- NewHorse Kentucky Farriers;
- Mad Barn Lexington Farriers.

The work used the shared bounded extraction foundation. No outreach, CRM write or A2 handoff occurred.

## Test execution

| Test type | Requests | Result |
|---|---:|---|
| Offline adapter tests using saved live payloads | 0 network requests | 45 passed, 0 failed |
| Targeted individual-profile tests | 3 | All technically successful |
| Kentucky/Lexington listing preflight reads | 3 | All technically successful |
| Bounded adapter runs | 3 | All produced five validated listings |
| Total Wave 2 Firecrawl requests | 9 | No provider error recorded |
| Additional browser discovery read | 1 | Used only to identify the public Mad Barn directory route |

Cost metadata was not returned by the current provider wrapper and remains `unknown`.

## Source results

### HorseProFinder

- Run ID: `W2-HORSEPRO-20260823`
- Adapter version: `1.0.0`
- Listings retained: 5
- Coverage: `partial`
- Next cursor: Kentucky page offset 5
- Contacts on sampled listing records: 0
- Targeted profile: technically accessible; category and URL-based location are available, but no phone, email or official website was published in the extracted profile.
- Recommendation: approve as a discovery source. Require official-site research and freshness verification before a candidate becomes review-ready; default images and sparse profile content are not evidence of current activity.

### NewHorse

- Run ID: `W2-NEWHORSE-20260823`
- Adapter version: `1.0.0`
- Listings retained: 5
- Coverage: `partial`
- Next cursor: Kentucky page offset 5, followed by server page 2 after the current page is exhausted
- Public contacts on sampled listing records: 1
- Targeted profile: public phone, location and multiple specialties were extracted; contact-form labels and image noise were excluded.
- Recommendation: approve with self-submitted-content and duplicate-review controls. Verify current activity and material claims independently.

### Mad Barn

- Run ID: `W2-MADBARN-20260823`
- Adapter version: `1.0.0`
- Listings retained: 5
- Coverage: `partial`
- Next cursor: Lexington page offset 5
- Contacts on listing cards: 0
- Targeted profile: public phone, email and Lexington address were extracted.
- Recommendation: approve with official-site corroboration and identity reconciliation before candidate creation.

## Extracted review sample

| Source | Listing | City | Contact in listing |
|---|---|---|---|
| HorseProFinder | Maureen Tierney | Paris | None |
| HorseProFinder | Gila Hoof Care | Louisville | None |
| HorseProFinder | Rob Wagner farrier service | Bedford | None |
| HorseProFinder | Mike Ratcliff Horseshoeing | Campbellsburg | None |
| HorseProFinder | Farley’s Farrier Service, LLC | Berry | None |
| NewHorse | Kentucky legend horseshoeing | Frankfort | None |
| NewHorse | Sean Petrilli | Paint Lick | None |
| NewHorse | KentuckyLegendHorseshoeing | Richmond | None |
| NewHorse | Heavyhound horseshoeing | Henderson | None |
| NewHorse | KO Farrier Service | Lebanon Junction | Public phone |
| Mad Barn | Bobby Menker, CJF, APF-I | Lexington | None on card |
| Mad Barn | Carlos Carvajal, CF | Lexington | None on card |
| Mad Barn | Henry Siegel | Lexington | None on card |
| Mad Barn | J. T. Holub, APF | Lexington | None on card; profile fields tested separately |
| Mad Barn | James Holub Equine Services | Lexington | None on card |

## Duplicate and identity review

A deterministic duplicate signal identified the following likely collision group:

- Best of Lexington — `Kentucky Legend Horseshoeing`, Richmond;
- NewHorse — `Kentucky legend horseshoeing`, Frankfort;
- NewHorse — `KentuckyLegendHorseshoeing`, Richmond.

These records must remain separate source listings until A1 verifies the current official business identity. No automatic merge was performed.

Mad Barn also exposes both `J. T. Holub, APF` and `James Holub Equine Services`. Existing A1 evidence indicates a likely person-and-organisation relationship, but the directory adapter must not merge them automatically.

## Validation controls

- 15 normalised listings validate against the directory-listing schema.
- All 15 listings map to valid A1 Research Seeds with status `needs_research`.
- All three coverage records are `partial` because the five-candidate cap was reached.
- Each source has a resumable cursor.
- The full audit log contains six valid hash-linked events, including three Wave 2 events.
- External actions: outreach 0, CRM writes 0, A2 handoffs 0.
- Cross-source duplicates are flagged for review rather than merged.

## Current runtime states

| Source | Implementation | Operational state |
|---|---|---|
| HorseProFinder | `validated` | `validated_for_bounded_pilot` |
| NewHorse | `validated` | `validated_for_bounded_pilot` |
| Mad Barn | `validated` | `validated_for_bounded_pilot` |

All three Wave 2 adapters are enabled for bounded pilot use under their documented limitations. This is not production acceptance and does not authorise outreach, CRM writes or unsupported claims.
