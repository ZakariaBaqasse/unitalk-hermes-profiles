# Equinet A1 — Manual No-Integration Pilot Runbook

## Purpose

Operate `equinet-a1-icp-discovery` safely before HubSpot, Twenty, A2 and n8n are connected.

## Preflight

1. Confirm the active profile is `equinet-a1-icp-discovery`.
2. Run `scripts/validate_step7_runtime_policy.py`.
3. Confirm the source register and ICP configuration load successfully.
4. Confirm the request is within three candidates, Kentucky/Lexington pilot scope and concurrency one.
5. Confirm no prior A1 run holds `cache/a1-runtime.lock`.
6. Record the initiating user and purpose.

Stop if any preflight check fails.

## Research planning

1. Create separate deterministic search plans for Farrier and Horse Owner segments when both are requested.
2. Use Exa for discovery only.
3. Ignore search snippets as evidence.
4. Open the official business destination through Firecrawl.
5. Check landing/relevant page, About/Team/Services and Contact/Location pages when available.
6. Use one additional claim-specific page only when required.
7. Target four successful reads and ten research tool calls per candidate; continue up to eight pages/twenty calls only for About/Team/Contact completion or a material unresolved claim, and record the escalation.
8. Never use a blocked source or bypass access controls.

## Contact capture

Retain only publicly published business information with evidence IDs:

- full address and postal code;
- organisation general email/phone;
- one primary named contact;
- one optional justified secondary named contact.

Use exact labels:

```text
Organisation general contact
Primary named contact — [Name] — [Role]
Secondary named contact — [Name] — [Role]
```

Do not capture every listed employee. Do not use form placeholders or third-party booking contacts. Named-contact availability does not change score or ranking by itself.

## Candidate processing

For each valid Research Seed:

1. validate the seed;
2. classify segment, prospect type and identity;
3. build the complete qualification object;
4. build and validate confidence assessment;
5. run deterministic ICP scoring;
6. assemble the canonical Prospect Candidate;
7. complete current-batch duplicate checks;
8. mark HubSpot and Twenty unavailable;
9. keep human decision pending;
10. block A2 handoff.

Never hand-edit deterministic score or confidence outputs.

## Review and export

Use the combined deterministic review/export path when both steps are required. Produce:

- canonical JSON;
- Markdown review;
- UTF-8 CSV;
- Excel workbook;
- export manifest with hashes and validation states.

Verify candidate IDs, scores, bands, confidence, source URLs, full address and `public_contact_details` across formats.

## Human review

Present the complete results in chat and provide the CSV. Ask the reviewer to assess:

- commercial relevance;
- correct classification;
- confirmed versus unknown criteria;
- evidence quality;
- score and confidence separation;
- recommendation;
- contact selection;
- material limitations.

Do not convert Unitalk quality approval into an Equinet commercial approval. Canonical candidate decisions remain pending until an authorised Equinet reviewer acts.

## Usage monitoring and circuit breaker

- Token warning at 1,000,000 per candidate or run.
- Token escalation at 3,000,000 per candidate or run.
- Daily warning at 5,000,000 and escalation at 10,000,000.
- No local token hard stop during an approved pilot run.
- Technical loop circuit breaker at 50 model iterations per turn.
- No automatic full-run retry.
- One retry per failed tool call.
- Economic hard stop at the Unitalk Gateway prepaid balance; the balance must never become negative.

Warnings require reporting and optimisation review, but they do not abandon an otherwise valid approved workflow. Stop on a real technical loop, technical failure, prohibited source/action or prepaid-balance risk.

## Error handling

- Blocked source → stop using the source and explain the approved alternative.
- CAPTCHA/login/paywall/403/429 → stop; never bypass.
- Identity conflict → `needs_review`.
- Missing official contact → record not publicly published.
- Candidate schema error → do not export as complete.
- Deterministic script error → return the exact error; do not invent a replacement.
- Possible batch duplicate → `Needs Research`; do not merge automatically.
- HubSpot/Twenty unavailable → show limitation; do not claim no duplicate.

## Prohibited actions

- outreach or email sending;
- CRM/Twenty create, update, merge or delete;
- automatic A2 invocation;
- consent inference;
- pricing/legal commitments;
- unauthorised source automation;
- memory promotion of discovered candidates;
- treating public contact information as outreach permission.

## Audit

For each run preserve:

- actor/trigger;
- timestamps and run ID;
- candidate IDs;
- source URLs and excerpts;
- model/provider/tools;
- configuration versions;
- outputs and hashes;
- quota result;
- approval state;
- errors/retries/blocked states;
- external actions performed, normally zero.

## Completion

A manual run is complete when all retained candidates validate, exports pass, quota usage is recorded, results are delivered to the human reviewer and every external action remains blocked.
