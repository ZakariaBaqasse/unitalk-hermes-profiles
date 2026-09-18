---
name: a2-twenty-connector
description: "Use when A2 reads or writes Companies and People in Twenty."
version: 0.1.0
author: Unitalk
license: Proprietary
metadata:
  hermes:
    tags: [equinet, a2, twenty]
    related_skills: [a2-twenty-fullenrich-workflow, a2-twenty-write-governance]
---

# A2 Twenty Connector

## When to Use

Use for bounded retrieval, claim, create, update, association and read-back reconciliation against Twenty.

## Status

`IMPLEMENTED — LIVE WRITE ACCEPTANCE PENDING`

## Commands

```bash
# Latest two eligible Farrier Companies
python scripts/pull_twenty_companies.py --run-id <id> --batch-size 2 --segment FARRIER --claim --output <batch.json>

# One eligible Company by immutable Twenty ID
python scripts/pull_twenty_companies.py --run-id <id> --batch-size 1 --company-id <uuid> --claim --output <batch.json>

# Exact Company name; ambiguous names are rejected
python scripts/pull_twenty_companies.py --run-id <id> --batch-size 1 --company-name "Exact Company Name" --claim --output <batch.json>

# Explicit reprocessing of a Company in any status
python scripts/pull_twenty_companies.py --run-id <id> --batch-size 1 --company-id <uuid> --allow-any-status --claim --output <batch.json>

python scripts/push_twenty_enrichment.py <write-plan.json> --output <dry-run.json>
python scripts/push_twenty_enrichment.py <write-plan.json> --apply --output <result.json>
```

## Rules

Translate user scope into explicit allowlisted filters. Supported filters are enrichment status, null-status migration, Company ID, exact Company name, segment, city, state, country, created/updated date bounds, and allowlisted ordering. Filters are sent to Twenty and checked again locally. The default ordering is latest `createdAt` first. Exact-name ambiguity is rejected; immutable Company ID is preferred. Reprocessing a non-eligible status requires explicit `--allow-any-status`. Pull only eligible Companies and include direct People relations with `depth=1`. Claim before paid actions and verify the claim. Accept only validated write plans. A1 fields are read-only. Create associations through `companyId`. Use literal field token `a2FullenrichPersonid`. Never auto-write personal email. Reconcile every live write.