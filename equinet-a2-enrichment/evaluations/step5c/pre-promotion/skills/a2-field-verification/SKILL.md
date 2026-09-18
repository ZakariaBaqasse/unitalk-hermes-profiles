---
name: a2-field-verification
description: Use when Equinet A2 must validate bounded observations.
---

# A2 Field Verification

## Delivery status

**Version:** `0.1.0-draft.1`  
**Status:** `WAVE 2 DRAFT — NOT APPROVED`

## Mission

Normalise and validate bounded contact, professional and equine-business observations before they enter Wave 3 evidence, confidence, conflict and proposal processing.

## Authoritative dependencies

Resolve the active Business Field Catalogue, Source Register, Evidence Policy and State Model through `foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json`.

Use these focused references:

- `references/contact-verification.md`;
- `references/professional-verification.md`;
- `references/equine-business-verification.md`.

## Inputs

A JSON batch with candidate ID, segment, operating scope and observations. Every available observation requires a catalogue field key, known source ID, a matching hashed `source_preflight` receipt, evidence ID, source reference, raw value and fact type. A free-text approval or source-action status is never sufficient.

## Command

```bash
/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python \
  /opt/data/profiles/equinet-a2-enrichment/scripts/normalise_and_validate_a2_observations.py \
  <observation-batch.json> --output <validated-observations.json>
```

## Workflow

1. Validate batch, field applicability, source ID and source-action state.
2. Preserve the raw value.
3. Normalise deterministically by field type.
4. Reject prohibited, inferred or malformed values.
5. Keep `not_checked`, `unavailable`, `not_found` and `error` distinct when no value exists.
6. Detect conflicting accepted values for the same entity and field.
7. Route privacy-sensitive or ambiguous observations to human review.
8. Mark accepted values `present_unverified` and ready for Wave 3 evidence assessment; do not assign final confidence here.

## Boundaries

- Never guess an email, relationship, role, credential or horse count.
- A business email or phone does not create consent or outreach eligibility.
- Personal email is held for explicit privacy review, with no CRM or outreach use.
- Person and organisation profile URLs remain separate.
- Capturing an official-site social URL does not authorise opening or extracting that social profile.
- Horse-count bands may be derived only from an explicit positive count.
- Final evidence confidence, freshness, protected-field decisions and canonical record mutation belong to Wave 3.

## Outputs

A hashed batch with raw and normalised values, preliminary verification state, field state, privacy route, evidence/source references, conflicts, errors and zero-action safety flags.

## Handoff

Accepted and held observations proceed to `a2-evidence-confidence-and-freshness` only after Wave 2 approval. Rejected observations do not enter the canonical record.
