# Step 8 Jonabell Stage 1 — Profile Test Instructions

**Profile:** `equinet-a2-enrichment`  
**Scope:** approved public business data for `A1-DARLEY-JONABELL-001` only  
**Mode:** local analysis of already collected pages; no new Web call

## Inputs

- `evaluations/step8/handoffs/A1-DARLEY-JONABELL-001.handoff.json`
- `evaluations/step8/intake/A1-DARLEY-JONABELL-001/initial-record.json`
- `evaluations/step8/planning/A1-DARLEY-JONABELL-001.reuse-snapshot.json`
- `evaluations/step8/planning/A1-DARLEY-JONABELL-001.gap-plan.json`
- `evaluations/step8/collection/A1-DARLEY-JONABELL-001/page-01.md`
- `evaluations/step8/collection/A1-DARLEY-JONABELL-001/page-02.md`
- `evaluations/step8/collection/collection-manifest.json`

## Required scope

Assess only:

1. `organisation.stable_type` from the explicit working thoroughbred farm and breeding-operation statements;
2. current `person.role_title` for Kate Galvin;
3. current `person.business_email` for Kate Galvin;
4. a separate human-review recommendation for `relationship.target_role_priority`.

## Mandatory boundaries

- Preserve the exact published role title.
- Do not infer purchasing authority.
- Recommend `secondary` target-role priority only as a reviewable classification; do not present it as a sourced fact.
- Do not collect or operationalise the published mobile number.
- Do not set an exact farm horse count from the seven named stallions.
- Do not open social-profile destinations.
- Do not use Web, Exa, Firecrawl, Apify, HubSpot, Twenty or n8n in this stage; use the stored pages only.
- Do not calculate or change the A1 score.
- Do not create outreach eligibility.

## Required commands

For each direct official-site observation, first create a receipt using:

```bash
scripts/build_step8_collection_receipt.py
```

Then validate the observation batch using:

```bash
scripts/normalise_and_validate_a2_observations.py
```

## Outputs

Create under `evaluations/step8/pilot/A1-DARLEY-JONABELL-001/`:

- `stage1-analysis.json`;
- `receipts/stable-type.json`;
- `receipts/role-title.json`;
- `receipts/business-email.json`;
- `observation-batch.json`;
- `validated-observations.json`;
- `stage1-audit.json`.

The audit must record the active model, Unitalk gateway, source file hashes, commands, result references, unavailable usage/cost as `unavailable`, and zero external actions.

Stop after Stage 1. Do not create a canonical revision or process Rood & Riddle until Séverine reviews these outputs.
