# Equinet A1 — V1 Evaluation and Improvement Review

**Release:** `equinet-a1-v1-no-integration-1.0.1`  
**Profile:** `equinet-a1-icp-discovery`  
**Target status:** `pilot_ready_no_integration`  
**Evaluation basis:** approved foundation, Waves 1–3, Step 7 runtime controls, Step 8 synthetic suite and Step 9 real-prospect pilot

## Executive assessment

The current A1 configuration is technically and behaviourally suitable for a controlled manual pilot without HubSpot, Twenty, A2 or n8n integrations. It discovers and qualifies permitted public professional prospects, preserves evidence, calculates deterministic confidence and ICP scores, ranks candidates and generates validated review/export packages. Every external action remains blocked and human review remains mandatory.

## Pilot KPI summary

| KPI | Result | Interpretation |
|---|---:|---|
| Real prospects requested | 3 | Controlled maximum |
| Review-ready candidates | 2 | 66.67% of requested candidates |
| Held for more research | 1 | 33.33%; no incomplete candidate was forced |
| Review-ready outputs accepted for quality by Unitalk Operations | 2/2 | 100% of review-ready pilot outputs |
| Step 9 final profile tokens | 33,107 | Below run warning |
| Step 9 final model calls | 4 | Below run call limits |
| Step 9 run usage status | Pass | No monitoring threshold reached |
| Synthetic scenarios passed | 4/4 | Accept, Needs Research, Reject and duplicate pathways |
| External actions | 0 | No outreach, CRM write or A2 handoff |
| Export formats validated | 4/4 | JSON, Markdown, CSV and Excel |

The model-token figure covers the final A1 profile packaging/export operation. Exa, Firecrawl and supervising-session monetary consumption were not available from the tool metadata and must not be treated as zero.

## Post-freeze staged live validation

A later staged real run produced Keene Ridge Farm end to end with validated JSON, Markdown, CSV and Excel outputs:

- ICP score `68 / Medium`;
- confidence `84 / High`;
- outcome `horse_count_unknown_human_review`;
- recommendation `Needs Research`;
- no Farrier was forced when no official business website met the evidence standard;
- no outreach, CRM write or A2 handoff occurred.

The staged workflow used 2,818,553 tokens across multiple user-triggered turns. Under the final policy this is a usage warning for optimisation, not a reason to invalidate the functional pilot. The high usage is concentrated in Research and Qualification/Confidence and remains an optimisation backlog item. Local token hard stops were removed; the technical loop circuit breaker is 50 model iterations per turn and the economic hard stop is the Unitalk Gateway prepaid balance.

## Improvements incorporated from the real pilot

### Official-page coverage

The research workflow now checks, when available:

1. official landing or relevant business page;
2. About, Team or Services page;
3. Contact, Location or Find Us page;
4. one additional material-claim page when required.

The limit is four successful page reads and ten total research tool calls per candidate. Failed pages count as tool calls. One targeted retry is allowed; multiple guessed URLs are prohibited.

### Public business address and contact capture

A1 now retains explicitly published:

- postal code;
- full address;
- organisation general email and phone;
- one primary named contact;
- one optional justified secondary named contact.

Form placeholders and third-party contacts are rejected. Missing information is recorded as not publicly published rather than guessed.

### A1/A2 contact boundary

- `identity.person` stores one selected primary named contact.
- `identity.organisation` stores the prospect organisation.
- `public_contacts[]` stores organisation general contacts, primary contact details and one optional secondary contact with explicit labels.
- `associated_people[]` is deliberately absent from A1 V1.
- A2 owns broader stakeholder and buying-committee enrichment.

Named-contact availability is non-scoring metadata. It does not create points, penalties, ranking changes, purchasing authority or consent.

### Export improvements

The human-review export now includes:

- `postal_code`;
- `full_address`;
- `person_name`;
- `role_title`;
- `public_contact_details` with labels and evidence IDs.

Cross-format tests verify these values in JSON, CSV and Excel.

## Reference real-prospect outcomes

### Rood & Riddle Lexington Podiatry

- ICP: `80 / High`
- Confidence: `84 / High`
- Primary named contact: Manfred Eckert, Co-Founder/Farrier
- Direct named contact details: not publicly published
- Organisation phone and full address retained
- Recommendation: Accept for human review
- Material limitation: institutional Podiatry/Farrier organisation rather than a traditional independent Farrier business

### Jonabell Farm / Darley America

- ICP: `75 / High`
- Confidence: `84 / High`
- Primary named contact: Kate Galvin, Nominations Sales and Operating Manager, Jonabell Farm
- Direct professional email and mobile retained
- Organisation general email, phone and full address retained
- Purchasing influence remains unknown
- Recommendation: Accept for human review
- Material limitation: HubSpot cannot determine whether this is an existing strategic account

### Kentucky Horseshoeing School

Held as `needs_research`; not forced into the final candidate queue because the retained evidence did not establish the standard client-serving Farrier boundary and complete pilot information within the tool budget.

## Final regression result

The no-Web replay exactly matches the approved Step 9 canonical JSON package. All of the following pass:

- Wave 1 research/classification/qualification;
- Wave 2 confidence/scoring;
- Wave 3 review/export;
- Step 7 model/tools/permissions/quotas;
- Step 8 representative synthetic suite;
- Step 9 real-prospect package replay;
- named-contact cardinality and non-scoring controls;
- schema validation and cross-format consistency;
- action boundaries.

## Remaining limitations

The no-integration V1 cannot establish:

- existing HubSpot Contact/Company status;
- customer, opportunity, partner, distributor, competitor or suppression status;
- authoritative consent or communication preference;
- Twenty staging/reviewer state;
- durable A2 handoff state;
- production scheduling or orchestration.

It must therefore remain manual, draft-for-approval and human-reviewed.

## Recommendation

Approve the release candidate as `pilot_ready_no_integration` for a controlled manual Equinet A1 pilot. Do not describe it as fully integrated, autonomous, production-accepted or contractually accepted. Proceed to Step 11 only when the relevant accounts, scopes, data mappings, approval matrix and workflow decisions are available.
