# Equinet A1 — Wave 3 Draft Technical Review

**Profile:** `equinet-a1-icp-discovery`  
**Skills:** `ranked-prospect-review-package`, `prospect-export`  
**Created at:** `2026-08-14T16:46:38Z`  
**Status:** `Drafts technically valid — business review pending`  
**Promotion applied:** `No`

## Implemented capabilities

### Ranked Prospect Review Package

- assembles Wave 1 and Wave 2 artifacts into canonical Prospect Candidates;
- validates every candidate against Prospect Candidate Schema V1 and cross-reference rules;
- performs a real current-batch duplicate check;
- marks HubSpot and Twenty unavailable;
- keeps A2 handoff unauthorised;
- recommends `Accept`, `Needs Research` or `Reject` for a human reviewer;
- ranks candidates overall and within each segment;
- preserves score, confidence, evidence, unknowns and limitations.

### Prospect Export

Generates and validates:

- canonical JSON;
- Markdown review;
- UTF-8 CSV with JSON-serialised lists;
- Excel workbook;
- export manifest with SHA-256 hashes and validation results.

The Excel workbook contains:

1. `Review Queue` — compact human decision table;
2. `Candidate Data` — complete approved export columns;
3. `Evidence`;
4. `Criteria`;
5. `Score Components`;
6. `Read Me`.

## Deterministic review logic

| Recommended status | Rule |
|---|---|
| `Accept` | High or Medium final band, High or Medium confidence, no exclusion, unresolved quality issue, special review pathway or batch duplicate. |
| `Needs Research` | Low confidence, unresolved missing/conflicting data, possible batch duplicate, Low band, apprentice pathway, horse-count exception or another mandatory review pathway. |
| `Reject` | Scoring blocked, confirmed exclusion, Unqualified final band or exclusion outcome. |

A recommendation never records a human decision, invokes A2, writes to CRM or authorises outreach.

## Ranking logic

1. `Accept`;
2. `Needs Research`;
3. `Reject`;
4. within each status: final band, ICP score, confidence score, display name and candidate ID.

Scores and confidence values are never changed for ranking.

## Technical test results

All Wave 3 tests passed:

- both skill packages pass official validation;
- Python compilation passed;
- both skills contain three evaluation cases and explicit action boundaries;
- accepted James Holub candidate remains `86 / High` ICP and `84 / High` confidence;
- James is recommended `Accept` for human review only;
- mixed batch ranks `Accept`, `Needs Research`, `Reject`;
- Farrier and Horse Owner counts remain separate;
- unknown-count Horse Owner remains `80` numeric, final `Medium`, `horse_count_unknown_human_review`;
- shared business domain triggers a possible batch duplicate and `Needs Research`;
- JSON, Markdown, CSV and Excel are generated;
- cross-format candidate IDs, order, scores and full source URLs match;
- Excel contains no formulas or Excel error values;
- score/component drift is rejected before export.

## First real review output — James Holub

| Field | Result |
|---|---|
| Candidate | J.T. Holub / James Holub Equine Services |
| Segment / type | Farrier / `farrier_independent` |
| Location | Lexington, Kentucky |
| ICP | `86 / High` |
| Confidence | `84 / High` |
| Recommendation | `Accept` for human review |
| Human decision | Pending |
| Batch duplicate | No match in the current one-candidate batch |
| HubSpot | Unavailable |
| Twenty | Unavailable |
| A2 | Not authorised / not triggered |

Visible limitations:

- confidence relies on one strong primary business source;
- explicit client-base size is not stated;
- current professional-association membership is not stated;
- no current formal certification credential is confirmed; experience and training evidence remain visible separately.

## Generated and verified artifacts

```text
evaluations/wave3/iteration-1/james-review-package.json
evaluations/wave3/iteration-1/exports/james-holub-review.json
evaluations/wave3/iteration-1/exports/james-holub-review.md
evaluations/wave3/iteration-1/exports/james-holub-review.csv
evaluations/wave3/iteration-1/exports/james-holub-review.xlsx
evaluations/wave3/iteration-1/exports/james-holub-review-manifest.json
```

## Pending business checkpoint

Séverine must confirm or request changes to:

1. the `Accept`, `Needs Research`, `Reject` recommendation rules;
2. the ranking order;
3. the compact review table fields;
4. the Excel sheet structure;
5. the level of evidence and limitation detail in Markdown.

After business approval, run one controlled behavioural end-to-end test through the actual profile, correct any observed issue, then promote both skills from Draft if accepted.
