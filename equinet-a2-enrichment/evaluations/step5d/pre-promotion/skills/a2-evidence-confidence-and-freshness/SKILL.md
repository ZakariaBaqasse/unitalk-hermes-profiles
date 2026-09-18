---
name: a2-evidence-confidence-and-freshness
description: Use when Equinet A2 must assess evidence quality.
---

# A2 Evidence, Confidence and Freshness

## Delivery status

**Version:** `0.1.0-draft.1`  
**Status:** `WAVE 3 DRAFT — NOT APPROVED`

## Mission

Create traceable evidence results and apply the active six-dimension confidence, verification and freshness policy without changing the A1 ICP score.

## Authoritative dependencies

Resolve the Evidence Policy, Source Register, Business Field Catalogue and State Model through the Active Foundation Manifest. Preserve inherited A1 evidence confidence rather than rescoring it.

## Inputs

One field observation with field-assessment ID, source ID, claim key/value, evidence references, identity match, directness, freshness, corroboration, consistency and a matching hashed Wave 2 `source_preflight` receipt. A1 references require their inherited confidence object.

## Command

```bash
/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python \
  /opt/data/profiles/equinet-a2-enrichment/scripts/evaluate_a2_evidence_confidence.py \
  <evidence.json> --output <evidence-result.json>
```

## Workflow

1. Verify the active policy by manifest hash.
2. Resolve source authority from the policy.
3. Score identity, authority, directness, freshness, corroboration and consistency.
4. Apply unresolved-identity, conflict, inference, stale and source-gate caps.
5. Return verification, confidence and freshness separately.
6. Preserve A1 confidence when the evidence namespace is inherited.

## Boundaries

Confidence is not ICP fit. Blocked or unverified sources cannot support a claim. Unknown remains unknown. No output grants consent, outreach, CRM write or numeric score authority.

## Outputs

A deterministic evidence ID, dimension components, caps, confidence score/level, verification and freshness state, source references and zero-action flags.

## Handoff

Pass evidence-backed field results to protected-field conflict resolution. Material new A1 evidence may later create a requalification signal, never replacement points.
