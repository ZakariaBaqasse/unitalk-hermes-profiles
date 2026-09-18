---
name: a2-gap-analysis-and-enrichment-planning
description: Use when Equinet A2 must plan named enrichment gaps.
---

# A2 Gap Analysis and Enrichment Planning

## Delivery status

**Version:** `0.1.0-draft.1`  
**Status:** `WAVE 2 DRAFT — NOT APPROVED`

## Mission

Compare an eligible Wave 1 record with the active Business Field Catalogue and segment-specific Minimum Data Package, then create the smallest field-level plan needed for review readiness or an approved targeted request.

## Authoritative dependencies

Resolve current files through `foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json`. The active Step 5C baseline is:

- Business Field Catalogue `0.1.1-draft.1`;
- Minimum Data Packages `0.1.1-draft.1`;
- Source Register `0.1.1-draft.1`;
- Step 5A Operational Skill Manifest `0.1.0`.

Do not copy catalogue priorities, package thresholds or source statuses into this skill.

## Inputs

A JSON request with candidate ID, segment, operating scope, Wave 1 eligibility, enrichment mode, contact path, requested field keys when targeted, field states and whether research is exhausted.

Field states remain distinct: `verified`, `present_unverified`, `missing`, `unknown`, `not_found`, `unavailable`, `conflict` and `error`.

## Command

```bash
/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python \
  /opt/data/profiles/equinet-a2-enrichment/scripts/build_a2_gap_plan.py \
  <request.json> --output <gap-plan.json>
```

## Workflow

1. Require Wave 1 `eligible`; hold or block otherwise.
2. Reuse approved A1 and A1-directory evidence before proposing new access.
3. For `default_minimum_package`, resolve the segment package and selected contact path.
4. For `targeted_fields`, accept only applicable catalogue fields.
5. Do not plan a fresh/current verified field.
6. Label every remaining need as gap, verification, freshness, conflict, availability or technical error.
7. Include ordered source candidates as planning options only; each new source action requires the research skill's preflight.
8. Return `no_research_needed`, `research_required`, `held`, `blocked` or `invalid_request`.

## Boundaries

- Optional fields do not block the default minimum package and are planned only when explicitly requested.
- `do_not_collect` fields are blocked, not researched.
- A missing required field creates a gap; it never rejects the prospect or changes the A1 score.
- A2 never calculates an ICP score.
- A plan does not authorise Web, provider, CRM, outreach or any external action.
- Research exhaustion with an unresolved need produces a hold for human review.

## Outputs

A hashed, deterministic plan containing named plan items, field priority, need type, alternatives, source candidates, blocked fields, status and zero-action safety flags.

## Handoff

Each plan item must pass `a2-permitted-enrichment-research` before a source attempt. A `no_research_needed` result proceeds to Wave 3 data-quality handling after Wave 2 approval.
