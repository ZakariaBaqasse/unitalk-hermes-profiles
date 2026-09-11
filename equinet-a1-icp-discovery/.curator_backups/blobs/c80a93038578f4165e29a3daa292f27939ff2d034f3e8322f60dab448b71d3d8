---
name: equinet-icp-qualification
version: 1.0.0
status: production_validated
description: Use after post-n8n enrichment and segment classification to assess every approved Equinet ICP criterion, apply minimum-data and exclusion rules, and produce the schema-compatible qualification object. Never rediscovers leads or calculates ICP points/confidence; it prepares deterministic inputs for later evidence and scoring skills.
compatibility: Requires accepted post-n8n website evidence, ICP Configuration 2.0.0, Evidence and Confidence Rules 1.2.0, Prospect Candidate Schema V1, and a classification decision.
---

# Equinet ICP Qualification

Use this skill after accepted website enrichment and segment classification, before confidence or scoring. n8n discovery/deduplication is complete; apply the approved business criteria to the supplied lead without adding points or searching for new leads.

## Authoritative dependencies

Resolve from the active profile home:

```text
configurations/icp/equinet-icp-v1.yaml
configurations/evidence/evidence-confidence-rules-v1.yaml
skills/a1-prospect-data-contract/references/prospect-candidate.schema.json
skills/equinet-icp-qualification/references/qualification-assessment.schema.json
```

Use the existing profile runtime to build the qualification object:

```text
/opt/hermes/.venv/bin/python skills/equinet-icp-qualification/scripts/build_qualification.py <assessment.json>
```

Do not run `pip install` or `uv pip install` during qualification. Store temporary inputs under the profile `tmp/` or evaluation workspace.

## Input requirements

Accept:

- a `confirmed` or `needs_review` classification decision;
- the classified segment;
- accepted, cited official-website evidence records gathered by Hermes with approved web tools;
- a proposed status for each observed ICP criterion;
- missing minimum-review fields.

Do not qualify an out-of-scope or blocked classification as eligible.
Treat n8n lead fields as discovery context only. They may guide which accepted evidence to inspect, but cannot by themselves confirm a criterion. Do not repeat discovery, deduplication or website retrieval in this skill.

## Criterion states

Use exactly:

- `confirmed`: the criterion is directly supported or supported by an approved role-based rule;
- `not_confirmed`: research was performed and did not establish the criterion;
- `unknown`: available evidence is insufficient;
- `contradicted`: direct evidence conflicts with or disproves the criterion.

Every `confirmed` criterion requires evidence references. Do not confirm a mandatory criterion from a reasonable inference alone.

## Assessment workflow

1. Load the current segment criteria from `equinet-icp-v1.yaml`.
2. Create one assessment entry for every criterion in that segment.
3. Map research evidence to the relevant criteria.
4. Apply the Evidence and Confidence Rules when deciding direct fact versus inference.
5. Keep missing information as `unknown`.
6. Identify confirmed exclusion criteria.
7. Evaluate the approved minimum review package.
8. Build the deterministic qualification object.
9. Validate the output against the Prospect Candidate qualification schema.
10. Hand the candidate to `prospect-evidence-and-confidence`, then `icp-scoring-and-rationale`.

## Farrier rules

Assess all Farrier criteria, including:

- professional activity;
- product usage or influence;
- product fit;
- client base;
- regular activity;
- service area;
- specialisation;
- certification/experience;
- sport-horse focus;
- business size;
- buying influence;
- recent engagement;
- apprentice future potential;
- inactive/hobbyist signal;
- absence of professional evidence.

Do not double-count a generic professional role as both product usage and explicit buying influence. Confirm both only when evidence establishes distinct usage/need and decision/recommendation influence.

## Horse Owner rules

Assess all Horse Owner criteria, including:

- commercial operation;
- more than three horses;
- purchasing influence;
- product fit;
- performance discipline;
- breeding activity;
- professional network;
- high-equine-activity location;
- recent buying/expansion signal;
- single-horse recreational signal;
- absence of commercial evidence.

Never infer horse count from photos, acreage, buildings, event participation, follower count or stable appearance.

If horse count is unknown or contradicted, preserve that status. The scoring skill will apply the approved exception pathway.

## Minimum data

The approved minimum review package is defined in the ICP configuration. Assess it against the complete candidate context actually provided.

- If a required full-candidate field is absent at this stage, list it in `missing_minimum_fields`; do not treat it as present merely because another skill will add it later.
- Synthetic tests may pass an explicitly complete candidate context, but must not use an empty list by default.
- Any missing required minimum field produces:

```text
minimum_data_status: fail
```

Do not hide missing minimum fields to make a candidate appear ready.

## Exclusion status

- Confirmed segment exclusion criterion → `excluded`.
- `farrier.no_professional_evidence` means no evidence of **professional** hoof-care activity. It may be confirmed when direct evidence establishes hobby-only/non-professional activity; it does not mean that no evidence of any kind exists.
- In a hobby-only case, `farrier.inactive_or_hobbyist` and `farrier.no_professional_evidence` may both be confirmed when the evidence directly supports both meanings.
- `horse_owner.no_commercial_evidence` may be confirmed when direct evidence establishes recreational/non-commercial activity with no professional or commercial orientation.
- No confirmed segment exclusion criterion → `eligible` for ICP review.
- CRM exclusions remain in duplicate/exclusion checks and are not invented here.

HubSpot is unavailable in V1; do not claim customer, opportunity, partner, distributor, competitor, opt-out or duplicate eligibility.

## Deterministic output

The builder returns:

- `qualification.icp_config_version`;
- all segment criteria with labels/categories/status/evidence/notes;
- minimum data status and missing fields;
- exclusion status and reasons;
- audit information for required gates and special pathways.

The qualification object must be directly compatible with the Prospect Candidate Schema.

## Boundaries

Do not:

- calculate numeric ICP points;
- calculate confidence;
- change criterion definitions;
- create new criteria ad hoc;
- confirm criteria without evidence;
- infer CRM eligibility;
- use n8n hints or search snippets as criterion evidence;
- rediscover or deduplicate leads;
- contact the candidate;
- write to HubSpot or Twenty;
- approve A2 handoff.

## Handoff

Preserve every criterion status, evidence ID, missing field and exclusion reason. Later skills must consume the deterministic qualification object rather than reconstructing the assessment from prose.
