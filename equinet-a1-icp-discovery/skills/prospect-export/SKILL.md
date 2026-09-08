---
name: prospect-export
description: Use only after ranked-prospect-review-package has produced a validated Equinet A1 review package and the user needs review-ready Markdown, canonical JSON, CSV or Excel. Exports all formats deterministically, preserves full URLs and JSON-serialised lists, validates cross-format consistency, and never writes to HubSpot, Twenty or A2.
compatibility: Requires a schema-valid Ranked Prospect Review Package, Prospect Candidate Schema V1 and openpyxl in the profile virtual environment.
metadata:
  version: 1.0.0
  status: production_validated
---

# Prospect Export

Use this skill only after `ranked-prospect-review-package`.

## Authoritative dependencies

```text
skills/a1-prospect-data-contract/references/prospect-candidate.schema.json
skills/a1-prospect-data-contract/references/export-view.md
skills/ranked-prospect-review-package/references/review-package.schema.json
skills/prospect-export/references/export-manifest.schema.json
```

Run:

```text
/opt/data/profiles/equinet-a1-icp-discovery/.venv/bin/python skills/prospect-export/scripts/export_review_package.py <review-package.json> --output-dir <directory> --prefix <name>
```

Do not install packages during execution.

## Optimised combined path

When the review package still needs to be built, run both deterministic stages in one process:

```text
/opt/data/profiles/equinet-a1-icp-discovery/.venv/bin/python scripts/run_review_export_pipeline.py <review-input.json> --review-output <review-package.json> --export-dir <directory> --prefix <name> --audit-output <audit.json>
```

Use separate wrappers only when a validated review package already exists. The combined path reduces model/tool loops without changing any candidate data or validation rule.

## Canonical source

The validated review-package JSON and its embedded Prospect Candidates are lossless and authoritative. Markdown, CSV and Excel are derived human-review views. Never infer a value from formatting or create a competing data model.

## Required outputs

Generate:

1. `<prefix>.json` — exact canonical review package;
2. `<prefix>.md` — compact queue plus candidate detail sections;
3. `<prefix>.csv` — one row per candidate using the approved export columns;
4. `<prefix>.xlsx` — review workbook;
5. `<prefix>-manifest.json` — file hashes, row counts and validation results.

## CSV rules

- UTF-8 with header row;
- one candidate per row;
- arrays serialised as JSON arrays;
- null values exported as empty cells;
- URLs preserved in full;
- candidate ID, run ID and schema version always present.

## Excel workbook

Create these sheets:

- `Review Queue` — compact decision table with a blank human decision column and list choices `Accept`, `Reject`, `Needs Research`;
- `Candidate Data` — the complete approved human-review export columns;
- `Evidence` — one row per evidence record;
- `Criteria` — one row per qualification criterion;
- `Score Components` — one row per scored component;
- `Read Me` — scope, status mapping, integration limitations and provenance.

Use a professional Arial font, frozen headers, filters, readable widths and wrapped text. Do not truncate stored URLs, excerpts or rationales. Do not use formulas in V1.

## Markdown

Lead with package summary and integration limitations. Show one compact row per candidate. Put evidence, rationale, missing information and limitations in detail sections.

## Validation

Before claiming completion:

- validate the input review package;
- validate every embedded Prospect Candidate;
- read back the JSON, CSV and Excel outputs;
- verify candidate IDs, scores, bands, confidence, statuses and URLs agree;
- verify workbook formulas and Excel error values are absent;
- record SHA-256 hashes and validation results in the manifest.

If any validation fails, stop and report the exact error. Do not describe the export as complete.

## Boundaries

Never:

- change candidate data, ranking, review recommendation or score;
- write a reviewer decision on the human's behalf;
- infer consent;
- write to HubSpot or Twenty;
- trigger A2 or outreach;
- claim a file exists before it is created and validated.
