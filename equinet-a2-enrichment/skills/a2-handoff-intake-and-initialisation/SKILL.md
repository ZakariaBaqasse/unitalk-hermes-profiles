---
name: a2-handoff-intake-and-initialisation
description: Use whenever Equinet A2 receives, validates or initialises an A1-approved prospect handoff. Enforces the complete A1-to-A2 contract, immutable snapshot preservation and idempotent canonical record creation before any enrichment work.
---

# A2 Handoff Intake and Initialisation

## Delivery status

**Version:** `0.1.0`  
**Status:** `WAVE 1 APPROVED — LOCAL NO-INTEGRATION MODE`

## Mission

Accept only an eligible, approved and integrity-valid A1 handoff, then create or return the deterministic first A2 canonical revision. This skill performs no enrichment research and no external action.

## Authoritative dependencies

Resolve current versions through:

`/opt/data/profiles/equinet-a2-enrichment/foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json`

Required contracts:

- A1-to-A2 Handoff Contract and schema;
- Handoff-to-Record Initialisation Contract;
- Canonical A2 Enrichment Record Schema;
- Cross-Field Validator Contract.

Do not replace these contracts with summaries in this skill.

## Inputs

- one complete A1-to-A2 handoff JSON file;
- one destination path for the canonical A2 record when persistence is requested;
- one idempotency-ledger path, or the command default.

## Command

```bash
/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python \
  /opt/data/profiles/equinet-a2-enrichment/scripts/a2_intake.py \
  <handoff.json> --output <a2-record.json> --ledger <ledger.json>
```

Use `--include-record` only when the full canonical JSON is explicitly required in stdout. Normally write the record to disk and return the compact command result.

## Workflow

1. Parse JSON strictly; reject duplicate keys and non-finite numbers.
2. Run the pinned handoff schema and cross-field validator.
3. Require the correct target profile, human approval, `pass_to_a2` recommendation and eligible status.
4. Apply the operating-scope delivery-state ceiling.
5. Preserve the full handoff and A1 snapshot without modification.
6. Create only the person and organisation entities explicitly present upstream.
7. Initialise empty A2 assessment, evidence and requalification containers.
8. Keep data quality unassessed, review pending and every external permission false.
9. Reserve the handoff ID and idempotency key in the locked ledger.
10. Write the canonical record atomically and validate it before success.

## Outputs

- `valid` status;
- handoff and canonical record IDs;
- handoff and record hashes;
- `created` or `unchanged` write state;
- canonical record path when persisted;
- zero external actions.

## Stop and escalation rules

Reject the intake when approval, recommendation, eligibility, target profile, scope, hash, receipt or action constraints fail. Reject identifier reuse with different content. Never repair a malformed handoff, infer missing approval or report delivery that did not occur.

## Handoff

A valid canonical initial revision proceeds to `a2-entity-resolution-and-normalisation`. Invalid or ambiguous input remains blocked and is returned to the A1/Unitalk owner for correction.
