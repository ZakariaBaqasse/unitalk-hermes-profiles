---
name: a2-data-quality-and-review-readiness
description: Use when Equinet A2 must finalise a review revision.
---

# A2 Data Quality and Review Readiness

## Delivery status

**Version:** `0.2.0`  
**Status:** `PILOT_READY_NO_INTEGRATION`

## Mission

Evaluate completeness and consistency, recommend the next human-review state and finalise a new immutable canonical revision while preserving every prior revision and the A1 snapshot.

## Authoritative dependencies

Use the canonical schema and cross-field validator, active Field Catalogue and Minimum Data Packages. Later revisions require their exact predecessor.

## Inputs

The prior canonical record and one complete proposed next revision, plus the active catalogue. The proposed revision must contain the evidence, assessments, quality, review, workflow and audit state produced by the approved skills.

## Command

```bash
/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python \
  /opt/data/profiles/equinet-a2-enrichment/scripts/create_a2_revision.py \
  <previous.json> <proposed.json> --output <revision-result.json>
```

## Workflow

1. Validate the previous record.
2. Validate the proposed record against schema, catalogue and predecessor.
3. Require a new revision ID, exact sequence increment and supersession pointer.
4. Preserve the complete source handoff.
5. Keep evidence, observations and audit append-only.
6. Distinguish review-ready, incomplete, conflict and error outcomes through canonical quality/workflow states.

## Boundaries

A missing required field never rejects a prospect or changes its A1 score. Prior revisions are immutable. No external application is claimed without a receipt. No-integration records cannot enter sync states.

An A1 `high` score does not make the A2 minimum package complete. If approved research is exhausted and required business data remains missing, preserve the A1 score, keep data quality `incomplete` and generate the consolidated human review with every named gap. Use `held` only when a named dependency truly prevents progression. Otherwise the reviewer may record `approved_collect_during_discovery`; this preserves the open gaps and authorises neither outreach nor a CRM write.

Normal operation uses one consolidated final human review. Implementation-test checkpoints do not create additional runtime approvals.

## Outputs

A validation result with previous and new record hashes, lineage IDs, the validated proposed record, zero-action flags and explicit errors.

## Handoff

Only a valid canonical revision may enter review-package generation or governed handoff preparation.
