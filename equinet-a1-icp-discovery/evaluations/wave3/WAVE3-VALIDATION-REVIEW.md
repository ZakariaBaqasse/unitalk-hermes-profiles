# Equinet A1 — Wave 3 Validation Review

**Profile:** `equinet-a1-icp-discovery`  
**Skills:** `ranked-prospect-review-package`, `prospect-export`  
**Review completed at:** `2026-08-14T16:56:26Z`  
**Business design:** Approved by Séverine on 14 August 2026  
**Technical validation:** Passed  
**Controlled behavioural validation:** Passed  
**Decision:** `Approved by Séverine for the A1 V1 pilot`  
**Approval recorded at:** `2026-08-14T16:58:28Z`  
**Promotion applied:** `Yes`

**Post-promotion verification:** Official validation passed for both Wave 3 skills, and the complete Wave 1, Wave 2 and Wave 3 regression suites passed.

## Scope

Wave 3 assembles validated Wave 1 and Wave 2 artifacts into ranked canonical Prospect Candidates and exports the review queue to JSON, Markdown, CSV and Excel.

## Technical validation

All tests passed:

- both skill packages pass official validation;
- all Python scripts compile;
- James Holub remains `86 / High` ICP and `84 / High` confidence;
- mixed batches rank `Accept`, `Needs Research`, `Reject` deterministically;
- Farrier and Horse Owner results remain separate;
- unknown-count Horse Owner remains `80` numeric, final `Medium`, `horse_count_unknown_human_review`;
- current-batch duplicate matching triggers `Needs Research`;
- invalid score/component drift blocks export;
- JSON, Markdown, CSV and Excel are created and read back;
- IDs, order, scores, statuses and full source URLs agree across formats;
- Excel contains no formulas or Excel error values.

## Controlled behavioural validation

The actual `equinet-a1-icp-discovery` profile loaded both Wave 3 skills and processed the accepted James Holub fixture.

| Check | Observed result |
|---|---|
| Candidate count | `1` |
| Recommendation | `Accept` for human review |
| ICP | `86 / High` |
| Confidence | `84 / High` |
| Human decision | `Pending` |
| Batch duplicate | `No match` |
| HubSpot | `Unavailable` |
| Twenty | `Unavailable` |
| A2 | `Not authorised / not triggered` |
| Review package schema | Passed |
| Prospect Candidate schema | Passed |
| JSON round-trip | Passed |
| CSV consistency | Passed |
| Excel consistency | Passed |
| Excel formula/error check | Passed |
| Outreach | None |
| CRM write | None |
| A2 handoff | None |

The behavioural output preserved all approved evidence, score, confidence, recommendation and integration states.

## Created outputs

```text
evaluations/wave3/behavioral-validation/james/review-package.json
evaluations/wave3/behavioral-validation/james/exports/james-holub-behavioural.json
evaluations/wave3/behavioral-validation/james/exports/james-holub-behavioural.md
evaluations/wave3/behavioral-validation/james/exports/james-holub-behavioural.csv
evaluations/wave3/behavioral-validation/james/exports/james-holub-behavioural.xlsx
evaluations/wave3/behavioral-validation/james/exports/james-holub-behavioural-manifest.json
```

## Acceptance boundary

Promotion would approve both skills for the controlled A1 V1 pilot only. It would not:

- constitute Equinet production acceptance;
- approve any candidate on Equinet's behalf;
- enable outreach;
- enable HubSpot or Twenty writes;
- authorise A2 handoff;
- complete Step 7 model, tools and permissions audit.

## Applied status

```text
version: 1.0.0
status: validated_for_a1_v1_pilot
```

After promotion, Step 6 — A1 Skills is complete. The next profile step is Step 7 — model, tools and permissions audit.
