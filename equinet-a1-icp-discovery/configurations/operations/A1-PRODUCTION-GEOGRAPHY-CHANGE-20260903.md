# A1 Production Geography and Location-Preflight Amendment — 2026-09-03

## Decision

A1 production discovery is approved for:

- United States (`US`)
- Australia (`AU`)
- New Zealand (`NZ`)

The initiating user must supply country, region/state and city. Country and region codes are derived through `configurations/geography/location-resolution-v1.json`; they are not mandatory user inputs.

If country, region/state or city is missing, ambiguous or inconsistent, the interactive profile asks for clarification and does not launch n8n. Complete and unambiguous input requires no redundant confirmation. Unattended API or cron requests reject incomplete or ambiguous locations before n8n invocation.

## Production status

A1 is authorised for production operation within the versioned country, source and action scope. Full two-lane evidence from one cited run is not required for this production decision. Production acceptance does not imply contractual acceptance.

Acceptance evidence:

- n8n workflow `3tBw9IHcr4knwM4H`
- n8n execution `1215`
- application run `A1-20260902182623-B0A7B5`
- `runtime/n8n-poll-tickets/A1-20260902182623-B0A7B5.json`
- `runtime/n8n-poll-tickets/two-lane-v1/final-staging-index.json`

## Version changes

- ICP configuration: `1.1.0` → `2.0.0`
- Source register: `1.5.0` → `2.0.0`
- Runtime policy: `3.2.0` → `4.0.0`
- Scoring model: `1.0.0` → `1.1.0`
- Evidence-confidence policy: `1.1.0` → `1.2.0`
- Public website enrichment policy: `1.2.0` → `1.3.0`

## Source capability boundary

Country approval does not imply source support. Google Maps is the primary geography-generic source. Best of Lexington remains fixed to Lexington, Kentucky. FarrierIQ remains US-only until verified elsewhere. NewHorse requires explicit verified opaque geography IDs. HorseProFinder and Mad Barn require verified routes. Unsupported sources are skipped before network access.

## Retained controls

- overall request ceiling: 200
- one active discovery run
- source concurrency: one
- sequential source execution
- no active per-source run or daily candidate cap
- stop on terms, robots, CAPTCHA, login, 403, 429 or rate-limit conflict
- no HubSpot writes
- no outreach or A2 automation
- Twenty Company plus optional linked Person review staging with duplicate preflight and read-back reconciliation (superseded by runtime policy 4.1.0)
