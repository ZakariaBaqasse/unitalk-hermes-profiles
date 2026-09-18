---
name: a2-evidence-confidence-and-freshness
description: Use when Equinet A2 must assess evidence quality.
---

# A2 Evidence, Confidence and Freshness

## Delivery status

**Version:** `0.3.1`  
**Status:** `WAVE 3 APPROVED — LOCAL NO-INTEGRATION MODE`

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

For horse count, an existing matched HubSpot `owner_horse_count` is authoritative. Net-new prospects or an empty HubSpot value may use an explicit exact count from the approved A1 handoff, recorded Equinet confirmation or the prospect-owned official website. Equinet has no separate first-party enrichment dataset. A conflicting non-authoritative value cannot replace populated HubSpot data without review. `horse_count_range` is not evidence and new `horse_count_band` values are prohibited.

## Outputs

A deterministic evidence ID, dimension components, caps, confidence score/level, verification and freshness state, source references and zero-action flags.

## Handoff

Pass evidence-backed field results to protected-field conflict resolution. Material new A1 evidence may later create a requalification signal, never replacement points.
