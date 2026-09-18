---
name: a2-duplicate-and-eligibility-review
description: Use whenever Equinet A2 must decide whether an accepted prospect may proceed after identity, duplicate, exclusion or authoritative-check results. Distinguishes unavailable checks from no match and returns continue, hold or block without granting outreach or CRM-write permission.
---

# A2 Duplicate and Eligibility Review

## Delivery status

**Version:** `0.1.0-draft.1`  
**Status:** `WAVE 1 DRAFT — NOT APPROVED`

## Mission

Combine the accepted A1 eligibility result, A2 identity-resolution status and available duplicate checks into a deterministic A2 eligibility recommendation.

## Inputs

A JSON request containing:

- `operating_scope`;
- `a1_eligibility_status`;
- `identity_resolution_status`;
- `checks[]`, each with `check_type`, `system`, `status` and an `authoritative` flag.

Supported duplicate statuses are `unavailable`, `not_checked`, `no_match`, `possible_match`, `confirmed_duplicate` and `error`.

## Command

```bash
/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python \
  /opt/data/profiles/equinet-a2-enrichment/scripts/evaluate_a2_duplicate_eligibility.py \
  <request.json> --output <eligibility.json>
```

## Decision order

1. Block an upstream-blocked record.
2. Hold an upstream hold.
3. Block an invalid identity; hold an unresolved or materially conflicting identity for review.
4. Block a confirmed duplicate.
5. Hold a possible duplicate, unresolved identity or failed required check.
6. In integrated or production scope, hold when an authoritative duplicate check is unavailable.
7. In synthetic or manual no-integration scope, permit A2 enrichment when no local blocker exists while keeping CRM-dependent and outreach checks unavailable.

## Outputs

- `a2_eligibility_status`: `eligible`, `hold` or `blocked`;
- outreach eligibility, which remains unavailable or blocked in Wave 1;
- owner routing as `needs_owner_review`;
- explicit reasons and source checks;
- zero external actions.

## Boundaries

`unavailable` never means `no_match`. This skill cannot declare consent, outreach permission, customer status, Deal status or a clean HubSpot state without an authoritative connected check. It does not write to the canonical record or any external system.

## Handoff

Only `eligible` records proceed to Wave 2 gap analysis. `hold` requires review or an authoritative check. `blocked` stops the A2 workflow for that handoff revision.
