---
name: ranked-prospect-review-package
description: Use after A1 qualification, confidence and scoring whenever one or more Equinet prospects must be assembled into schema-valid Prospect Candidates, ranked, and prepared for human review. Produces deterministic Accept, Reject or Needs Research recommendations without approving candidates, invoking A2 or writing to CRM.
compatibility: Requires Prospect Candidate Schema V1, accepted Wave 1 artifacts, Wave 2 confidence and scoring packages, and local deterministic scripts.
metadata:
  version: 1.3.0
  status: production_validated
---

# Ranked Prospect Review Package

Use this skill after `icp-scoring-and-rationale` and before `prospect-export`.

## Authoritative dependencies

```text
skills/a1-prospect-data-contract/references/prospect-candidate.schema.json
skills/a1-prospect-data-contract/scripts/validate_candidate.py
skills/ranked-prospect-review-package/references/review-input.schema.json
skills/ranked-prospect-review-package/references/review-package.schema.json
configurations/operations/a1-runtime-policy-v1.yaml
```

Run:

```text
/opt/data/profiles/equinet-a1-icp-discovery/.venv/bin/python skills/ranked-prospect-review-package/scripts/build_review_package.py <review-input.json> --output <review-package.json>
```

Do not install packages during execution.

When review packaging and export are requested together, use the single deterministic orchestration command documented in `prospect-export` rather than invoking both wrappers through separate reasoning loops.

## Review-input construction pitfalls

Building the `review-input.json` correctly is the most common source of errors
at this stage. Read `references/review-input-construction.md` before
constructing a review input.

Known pitfalls:

- **Research-seed path**: The research seed lives at `research/seed-{name}.json`,
  NOT at `candidates/{name}/seed-{name}.json` or via `../research/`. Always
  use the absolute path from the run directory.
- **Candidate directory name vs. candidate_id**: The directory under
  `candidates/` uses lowercased-hyphen names (e.g. `jt-holub`), while the
  `candidate_id` field uses a different format (e.g. `A1-JTHOLUB-LEX-001`).
  Use an explicit mapping — never derive the directory from the ID.
- **Package ID pattern**: Must match `^A1-RP-[A-Z0-9_-]{4,80}$`. Use the
  LIVE run short hex suffix (e.g. `A1-RP-LIVE-20260823-469CA5`).
- **Scoring package with confidence**: The `scoring_package` must contain both
  `scoring` and `audit` keys. The `confidence_context` look-up inside the
  assembler cross-checks against the `confidence` in the
  `confidence_package` — if they disagree, assembly fails.
- **Candidates without standalone websites (needs_research seeds)** can still
  be assembled if they have a classification decision with `needs_review`
  status, a qualification package and a scoring package. The builder does
  not reject them as long as the required bundle fields are present.

## Input

Require one review request containing one or more candidate bundles. Each bundle must preserve:

- candidate and run identifiers;
- Research Seed and Classification Decision;
- Qualification Object;
- confidence package;
- scoring package and deterministic audit;
- source-policy and access metadata;
- record kind, model, tools and initiating actor.

Do not accept free-form score, confidence or evidence replacements.

## Deterministic workflow

1. Validate the review request.
2. Assemble one canonical Prospect Candidate per bundle.
3. Preserve qualification criteria, evidence IDs, scoring components, confidence values and limitations.
4. Resolve only stage fields that become available during assembly. Do not change a criterion status.
5. Check exact duplicates within the current batch using public domain, email, phone and identity/location keys.
6. Validate and preserve an optional n8n `hubspot_check`; when it is absent, mark the live HubSpot check as `unavailable`. Initialise `integration_status.twenty` as `not_staged`; the separate `evidence-aware-crm-staging` workflow may later set it to `staged`, `possible_match`, or `sync_failed` from verified reconciliation evidence. Keep any unprovided exclusion file unavailable.
7. Validate every canonical candidate against Prospect Candidate Schema V1 and its cross-reference rules.
8. Derive the recommended review status.
9. Rank candidates deterministically overall and within each segment.
10. Validate and save the review package.

Stop and return exact validation errors if any candidate is invalid.

## Recommended review status

The status is a recommendation for a human reviewer, not an approval.

### `reject`

Use when:

- scoring is blocked;
- the candidate is excluded;
- the final band is `unqualified`;
- the deterministic outcome is an exclusion.

### `needs_research`

Use when:

- confidence is Low;
- a material conflict or missing review field remains;
- a batch duplicate is possible;
- the outcome is an apprentice, horse-count exception, missing mandatory gate or other review pathway;
- a High score has Low confidence.

### `accept`

Use only when:

- final band is High or Medium;
- confidence is High or Medium;
- no exclusion, unresolved data-quality issue or special review pathway applies.

`accept` means suitable for human acceptance review. It does not approve A2 handoff, outreach or a CRM action.

## Ranking

Rank in this order:

1. `accept`;
2. `needs_research`;
3. `reject`.

Within each group sort by final band, numeric ICP score, confidence score, display name and candidate ID. Produce both `overall_rank` and `segment_rank`. Never change the score to alter rank.

## Required review view

For every candidate show:

- identity, segment, prospect type and geography;
- primary named contact, role and selection basis when available;
- optional secondary named contact and organisation general contact, clearly labelled;
- public professional contacts;
- ICP score, final band and scoring outcome;
- confidence score and level;
- confirmed criteria and unearned or uncertain criteria;
- source URLs and evidence summary;
- missing information, conflicts and limitations;
- batch, HubSpot and Twenty duplicate-check states;
- recommended review status and rationale;
- proposed next action;
- human decision state;
- A2 handoff state and blockers;
- method and schema versions;
- separate Twenty Company ID, optional Person ID and verified relation status when staging has occurred.

## Boundaries

Never:

- approve on behalf of Equinet;
- change evidence, criterion statuses, scores, bands or confidence;
- hide unknowns, conflicts, exclusions or unavailable integrations;
- claim a HubSpot check occurred unless a schema-valid n8n result was supplied, or claim a Twenty check occurred;
- initiate A2, outreach or any external action;
- assign a Sales owner without an approved rule.
- map a US state directly to a HubSpot Sales Territory or populate `suggested_territory` without an approved mapping;
- add a candidate to a HubSpot list or change a property that may trigger a dynamic list or workflow;

## Output

Return one schema-valid review package containing canonical candidates and derived review fields. Keep human decision state `pending` unless a real recorded reviewer decision is supplied through an authorised future workflow.

Pass the validated package unchanged to `prospect-export`.
