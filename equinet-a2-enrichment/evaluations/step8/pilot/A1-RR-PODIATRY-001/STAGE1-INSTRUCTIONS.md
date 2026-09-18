# Step 8 Rood & Riddle — Stored-Page Profile Test Instructions

**Profile:** `equinet-a2-enrichment`  
**Candidate:** `A1-RR-PODIATRY-001`  
**Mode:** analyse existing approved artifacts only; no Web or external provider call

## Authoritative inputs

- `evaluations/step8/handoffs/A1-RR-PODIATRY-001.handoff.json`
- `evaluations/step8/intake/A1-RR-PODIATRY-001/initial-record.json`
- `evaluations/step8/planning/A1-RR-PODIATRY-001.reuse-snapshot.json`
- `evaluations/step8/planning/A1-RR-PODIATRY-001.gap-plan.json`
- `evaluations/step8/collection/A1-RR-PODIATRY-001/page-01.md`
- `evaluations/step8/collection/A1-RR-PODIATRY-001/page-02.md`
- `evaluations/step8/collection/A1-RR-PODIATRY-001/page-03.md`
- `evaluations/step8/collection/collection-manifest.json`
- the active business field catalogue, minimum-data packages, source register and runtime policy

## Required assessment scope

Assess and report:

1. current `person.role_title` for Manfred Eckert;
2. `person.professional_status` — do not infer full-time or part-time from a team listing or title;
3. `organisation.service_area` — do not treat the Lexington address alone as proof of service area;
4. `organisation.disciplines` — preserve the official wording and distinguish hospital-wide evidence from a Podiatry-team-specific claim;
5. named professional email or phone for Manfred Eckert — do not use form placeholders and do not attribute the organisation phone to him;
6. organisation fallback contactability from approved A1 evidence;
7. `relationship.target_role_priority` as a reviewable classification, never as a sourced fact;
8. missing required fields and their effect on minimum-package readiness.

## Mandatory boundaries

- Use the stored pages and approved A1 handoff only.
- Do not make Web, Exa, Firecrawl, Apify, HubSpot, Twenty or n8n calls.
- Do not open biography or social links.
- Do not treat `example@example.com` or form placeholders as contact data.
- Do not infer purchasing authority, service area, employment status or direct contact details.
- Do not change the A1 score.
- Do not create outreach eligibility, CRM changes or downstream delivery.
- A missing required field is a visible gap, not an automatic rejection.
- The final normal workflow has one consolidated human review; no intermediate human decision is required for this test run.

## Required deterministic command

For every direct official-site observation that will enter the observation batch, create a bounded source receipt with:

```bash
scripts/build_step8_collection_receipt.py
```

Then validate the observation batch with:

```bash
scripts/normalise_and_validate_a2_observations.py
```

Do not invent command success. Save command exit codes and result references.

## Required outputs

Create under `evaluations/step8/pilot/A1-RR-PODIATRY-001/`:

- `stage1-analysis.json`
- `receipts/*.json` for each direct observation
- `observation-batch.json`
- `validated-observations.json`
- `stage1-audit.json`

The analysis must separate:

- accepted direct observations;
- unresolved/not-found required fields;
- reviewable role-priority classification;
- contact-path readiness;
- minimum-package readiness;
- limitations.

The audit must record the active logical model, Unitalk gateway, upstream provider/region, exact input file hashes, commands, usage metadata from the run when available, and zero external actions.

## Completion response

Write and validate the required files before replying. Return no raw page content. Reply in at most twelve lines with the output paths, accepted observation count, unresolved required fields, contact-path status, validation status, model/API usage status and external-action count.
