---
name: a2-gap-analysis-and-enrichment-planning
description: Use when Equinet A2 must plan named enrichment gaps.
---

# A2 Gap Analysis and Enrichment Planning

## Delivery status

**Version:** `0.2.0`  
**Status:** `PILOT_READY_NO_INTEGRATION`

## Mission

Compare an eligible Wave 1 record with the active Business Field Catalogue and segment-specific Minimum Data Package, then create the smallest field-level plan needed for review readiness or an approved targeted request.

## Authoritative dependencies

Resolve current files through `foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json`. The active Step 5C baseline is:

- Business Field Catalogue `0.2.0`;
- Minimum Data Packages `0.2.0`;
- Source Register `0.2.0`;
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
8. Return `no_research_needed`, `research_required`, `review_required`, `held`, `blocked` or `invalid_request`.

The selected named contact and target-role priority are separate dimensions. A person may be the only or best named contact retained for the record while their verified role maps to `secondary`. Conversely, a verified `primary` role does not satisfy named-contactability when no named professional email or phone is available. Preserve both states independently.

Retain one selected named contact by default and at most two when a large organisation or shared purchasing or operational responsibility is documented. A second contact requires a recorded reason. If no suitable target-role person is found, preserve organisation information, set `target_role_not_found`, label the record `Contact Needed / Needs Review` and carry it to the consolidated review; an unrelated role or general contact does not satisfy the target-contact gap.

For Horse Owner records, plan current role, stable/farm type, exact horse count, at least one verified breed and public business location as required. Attempt both professional email and business phone; one verified channel is sufficient when the other is unavailable. Attempt the complete address, with state and country as the minimum.

## Boundaries

- Optional fields do not block the default minimum package and are planned only when explicitly requested.
- `do_not_collect` fields are blocked, not researched.
- A missing required field creates a gap; it never rejects the prospect or changes the A1 score.
- A2 never calculates an ICP score.
- A plan does not authorise Web, provider, CRM, outreach or any external action.
- Research exhaustion with unresolved business-data gaps produces the consolidated human review. Use `held` only for a dependency that truly blocks progression; otherwise offer `approved_collect_during_discovery` while preserving the incomplete state and named gaps.

## Outputs

A hashed, deterministic plan containing named plan items, field priority, need type, alternatives, source candidates, blocked fields, status and zero-action safety flags.

## Handoff

Each plan item must pass `a2-permitted-enrichment-research` before a source attempt. A `no_research_needed` result proceeds to Wave 3 data-quality handling after Wave 2 approval.
