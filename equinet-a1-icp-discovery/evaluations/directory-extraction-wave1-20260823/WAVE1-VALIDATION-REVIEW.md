# Wave 1 Directory Adapter Validation Review

## Decision recorded

Séverine approved **FarrierIQ**, **HAST** and **Best of Lexington** for bounded pilot use on 23 August 2026. FarrierIQ was approved despite the identified data-quality risk, with mandatory `555` contact filtering and official-site verification.

## Scope

Wave 1 implemented and tested source-specific adapters for:

- FarrierIQ;
- HAST Farrier Directory;
- Best of Lexington — Farriers.

The work used the validated shared extraction foundation. No outreach, CRM write or A2 handoff occurred.

## Test execution

| Test type | Requests | Result |
|---|---:|---|
| Offline adapter tests using saved smoke artifacts | 0 network requests | 26 passed, 0 failed |
| FarrierIQ targeted profile checks | 2 | Technically successful; both exposed `555` placeholder phone numbers |
| Bounded adapter runs | 3 | All completed without provider errors |
| Total Wave 1 live Firecrawl requests | 5 | No retries and no blocked responses |

Cost metadata was not returned by the current provider wrapper and remains `unknown`.

## Source results

### FarrierIQ

- Run ID: `W1-FARRIERIQ-20260823`
- Live-tested adapter version: `1.0.0`; current hardened version: `1.1.0`
- Listings retained: 5
- Coverage: `partial`
- Stop reason: `candidate_limit_reached`
- Listing fields: business name, Kentucky city, service categories and profile URL
- Contacts retained from the listing page: 0
- Targeted profiles checked: 2
- Targeted profiles with `555` telephone numbers: 2
- Technical result: passed
- Data-quality result: hold

The adapter excludes `555` contacts and marks affected profiles `held_for_review`. The current sample strongly suggests demo or placeholder directory content. FarrierIQ records must not be promoted to review-ready prospects until the directory owner or an independent official business source establishes that the listings are genuine.

### HAST

- Run ID: `W1-HAST-20260823`
- Live-tested adapter version: `1.0.0`; current hardened version: `1.1.0`
- Listings retained: 5
- Coverage: `partial`
- Stop reason: `candidate_limit_reached`
- Public contacts retained: 5 across the five listings
- Technical result: passed
- Data-quality result: accepted with limitations

The source is a legacy static HTTP page and states that its list is not complete. Names and public professional phone numbers can be retained with source evidence, but current activity and material claims require corroboration through a secure official source.

### Best of Lexington

- Run ID: `W1-BESTLEX-20260823`
- Live-tested adapter version: `1.0.0`; current hardened version: `1.1.0`
- Listings retained: 5
- Coverage: `complete_snapshot`
- Public business phones retained: 5
- Technical result: passed
- Data-quality result: accepted with limitations

The adapter extracts the five visible Kentucky Farrier cards and excludes claim links, forms and reCAPTCHA content. The directory has low volume and directory claims must be corroborated when material.

## Extracted review sample

| Source | Listing | Public contact result | Operational treatment |
|---|---|---|---|
| FarrierIQ | Adams Horseshoeing | None on listing page | Source-level data-quality hold |
| FarrierIQ | Campbell Professional Farrier | None on listing page | Source-level data-quality hold |
| FarrierIQ | Carter Farrier Services | None on listing page | Source-level data-quality hold |
| FarrierIQ | Davis Horseshoeing | None on listing page | Source-level data-quality hold |
| FarrierIQ | Edwards Professional Farrier | None on listing page | Source-level data-quality hold |
| HAST | Stephen Abell | Public phone retained | Needs official-source freshness verification |
| HAST | Milton Akins | No public contact in sampled record | Needs official-source freshness verification |
| HAST | Marie Aquilina | Public phone retained | Needs official-source freshness verification |
| HAST | Albert Burgess | Two public phones retained | Needs official-source freshness verification |
| HAST | Tom Collier | Public phone retained | Needs official-source freshness verification |
| Best of Lexington | Kentucky Legend Horseshoeing | Public business phone retained | Bounded pilot candidate |
| Best of Lexington | Safe Harbor Farrier Service | Public business phone retained | Bounded pilot candidate |
| Best of Lexington | TG Forge | Public business phone retained | Bounded pilot candidate |
| Best of Lexington | Double M Farrier Service | Public business phone retained | Bounded pilot candidate |
| Best of Lexington | The Balanced Bare Hoof | Public business phone retained | Bounded pilot candidate |

## Validation controls

- 15 normalised listings validate against the directory-listing schema.
- All 15 listings map to valid A1 Research Seeds with status `needs_research`.
- Coverage records validate.
- Three per-run audits validate.
- The append-only audit log contains three events with a valid hash chain.
- External actions: outreach 0, CRM writes 0, A2 handoffs 0.
- HAST and FarrierIQ remain `partial` because the five-candidate cap is not complete coverage.
- Best of Lexington is `complete_snapshot` for the tested five-result page.

## Current runtime states

| Source | Implementation | Operational state |
|---|---|---|
| FarrierIQ | `validated` | `validated_for_bounded_pilot` |
| HAST | `validated` | `validated_for_bounded_pilot` |
| Best of Lexington | `validated` | `validated_for_bounded_pilot` |

All three Wave 1 adapters are enabled for bounded pilot use under their recorded limitations. This is not production acceptance and does not authorise outreach, CRM writes or unsupported claims.
