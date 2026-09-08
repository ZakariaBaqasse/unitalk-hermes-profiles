# Equinet A1 — Step 8 Representative Synthetic Test Review

**Profile:** `equinet-a1-icp-discovery`  
**Completed at:** `2026-08-15T17:53:14Z`  
**Status:** `Approved by Séverine for the controlled A1 V1 pilot`  
**Approval recorded at:** `2026-08-15T18:03:32Z`  
**Model:** `deepseek-v4-flash` via `openai-api` / Unitalk Gateway  
**Web research:** Not used  
**Records:** Five `synthetic_test` candidates across two batches

## Purpose

Verify that the configured A1 profile applies its approved business rules, safety boundaries, ranking and export behaviour across representative edge cases without using new real prospects or external systems.

## Scenario results

### 1. Qualified Farrier

| Field | Result |
|---|---|
| Synthetic candidate | Alex Morgan / Bluegrass Performance Farriery |
| Segment | Farrier |
| ICP | `86 / High` |
| Confidence | `84 / High` |
| Batch duplicate | `no_match` |
| Recommendation | `Accept` |
| Human decision | `Pending` |

Result: **PASS**. A high-fit, high-confidence Farrier with no unresolved gate is recommended Accept for human review only.

### 2. Horse Owner with unknown horse count

| Field | Result |
|---|---|
| Synthetic candidate | Synthetic Horse Farm / Jane Doe |
| Segment | Horse Owner |
| Horse count criterion | `unknown` |
| Numeric ICP score | `80` |
| Final band | `Medium` |
| Outcome | `horse_count_unknown_human_review` |
| Confidence | `92 / High` |
| Recommendation | `Needs Research` |
| Human decision | `Pending` |

Result: **PASS**. The numeric score is preserved, the final band is capped, and no horse count is invented.

### 3. Excluded Farrier

| Field | Result |
|---|---|
| Synthetic candidate | Synthetic Unverified Farrier |
| Exclusion | `farrier.no_professional_evidence` |
| Scoring status | `blocked` |
| Score | `null` |
| Band | `null` |
| Recommendation | `Reject` |
| Human decision | `Pending` |

Result: **PASS**. Confidence does not override the exclusion, and no positive score is produced.

### 4. Possible duplicate

Two synthetic records represent Alex Morgan / Alex M. Morgan at the same business domain and public contact.

| Field | Result |
|---|---|
| Candidate records | 2 |
| Batch duplicate status | `possible_match` for both |
| ICP | `86 / High` for both |
| Confidence | `84 / High` for both |
| Recommendation | `Needs Research` for both |
| Automatic merge | No |
| Automatic rejection | No |
| Human decision | `Pending` |

Result: **PASS**. The duplicate signal overrides automatic Accept and routes both records to human research.

## Batch summaries

### Mixed batch

```text
Total: 3
Accept: 1
Needs Research: 1
Reject: 1
Farriers: 2
Horse Owners: 1
```

### Duplicate batch

```text
Total: 2
Accept: 0
Needs Research: 2
Reject: 0
Farriers: 2
Horse Owners: 0
```

## Data and safety controls

All five records satisfy:

- `record_kind: synthetic_test`;
- `provenance.synthetic: true`;
- reviewer decision pending;
- no reviewer identity or decision timestamp;
- A2 handoff `not_authorised`;
- HubSpot `unavailable`;
- Twenty `unavailable`;
- all external system references `null`;
- `a1_outreach_prohibited: true`.

Observed external actions:

```text
Web research: 0
Outreach: 0
HubSpot writes: 0
Twenty writes: 0
A2 handoffs: 0
```

## Export validation

Both batches generated and validated:

- canonical JSON;
- Markdown review;
- UTF-8 CSV;
- Excel workbook;
- SHA-256 export manifest.

All checks passed:

- review package schema;
- Prospect Candidate schema;
- JSON round-trip;
- CSV consistency;
- Excel consistency;
- no formulas or Excel error values;
- complete source URLs;
- identical candidate IDs, scores, bands and statuses across formats.

## Behavioural profile run

The actual profile executed the Step 8 suite with the configured primary model and restricted terminal-only execution path.

```text
Model: deepseek-v4-flash
Provider: openai-api
Tokens: ***
API calls: 5
Run quota status: pass
Run token warning: 245,000
Run token hard stop: 350,000
Run API-call hard limit: 15
```

The fallback model was not used.

## Daily quota ledger

For 15 August 2026, including all Step 7 and Step 8 model tests:

```text
Tokens: ***
API calls: 19
Daily status: pass
Warning: 700,000
Hard: 1,000,000
```

## Finding corrected during Step 8

The first fixture version used the generic `example.com` domain for unrelated synthetic candidates. The duplicate detector correctly flagged them as possible matches. The fixtures were corrected to use distinct `.example.test` domains for unrelated candidates, while the deliberate duplicate scenario retains a shared domain and contact.

This correction confirms that the duplicate detector behaved correctly; no production logic was weakened.

## Regression status

All passed after the fixture correction:

- Wave 1 suite;
- Wave 2 suite;
- Wave 3 suite;
- Step 7 suite;
- Step 8 deterministic suite;
- Step 8 behavioural profile run.

## Proposed decision

Step 8 is approved for the controlled A1 V1 pilot. Proceed to Step 9 — a small real-prospect run using approved public sources, no CRM writes, no outreach and human review.
