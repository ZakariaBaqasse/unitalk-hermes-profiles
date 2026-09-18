---
name: a2-protected-field-conflict-resolution
description: Use when Equinet A2 compares proposed and protected values.
---

# A2 Protected-Field Conflict Resolution

## Delivery status

**Version:** `0.1.0-draft.1`  
**Status:** `WAVE 3 DRAFT — NOT APPROVED`

## Mission

Compare evidence-backed observations with existing values and produce one safe field proposal without silently overwriting authoritative, read-only, owner, manual or privacy-sensitive data.

## Authoritative dependencies

Resolve the active Protected Fields Policy, Evidence Policy, Field Catalogue and HubSpot Mapping through the Active Foundation Manifest.

## Inputs

Field key and target, protection class, baseline/proposed values and states, evidence IDs, confidence, conflict, review decision, workflow dependency state, CRM-write flag and requalification relevance.

## Command

```bash
/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python \
  /opt/data/profiles/equinet-a2-enrichment/scripts/evaluate_a2_protected_field_action.py \
  <field-case.json> --output <proposal.json>
```

## Decision rules

- Same value: `no_change`.
- Empty unprotected baseline plus high confidence: `propose_add`.
- Different manual value or material conflict: `preserve_and_hold`.
- Authoritative control conflict: `preserve_authoritative_and_block`.
- System read-only: `read_only_preserve`.
- Owner change without approved routing: `preserve_or_needs_owner_review`.
- Personal email: privacy review only.
- A1-material evidence: `create_requalification_signal`, never score mutation.

## Boundaries

No silent overwrite, clear, owner assignment, consent/lifecycle change or CRM write. Approval without verified workflow/list dependencies remains write-blocked. A proposal is not an applied value.

## Outputs

A deterministic proposal ID, action, preserved baseline, proposed value, evidence lineage, review requirement and explicit false external-write/action flags.

## Handoff

Pass proposals to data-quality and review-readiness evaluation. A later reviewed proposal may prepare a patch, but only a guarded connector can execute it.
