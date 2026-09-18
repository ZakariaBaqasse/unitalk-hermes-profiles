# Equinet A2 Review-View Specification

**Specification version:** `0.1.0`  
**Profile:** `equinet-a2-enrichment`  
**Step:** `2H — Review-View Specification`  
**Status:** `PROMOTED BY UNITALK OPERATIONS IN STEP 2I`
**Canonical schema:** `1.0.0`

**Decision:** `APPROVED AS DRAFTED`  
**Approver:** Séverine, Unitalk Operations  
**Decision timestamp:** `2026-08-26T13:22:23Z`

## 1. Purpose

This specification defines deterministic, read-only human-review projections derived from one canonical A2 record revision.

Canonical JSON remains the only lossless source of truth. Markdown, CSV and Excel outputs are disposable review views. They do not update the record, record a decision, perform a sync or authorise an external action.

## 2. Review package

Every package contains:

- `review.md` — compact human-readable decision summary;
- `summary.csv` — one record-level row;
- `review-queue.csv` — fields requiring attention;
- `fields.csv` — all canonical field assessments;
- `evidence.csv` — A1 references and A2 evidence;
- `requalification.csv` — signals, returns and A1 score revisions;
- `audit.csv` — audit and consumption events;
- `review.xlsx` — the same views in a formatted workbook;
- `manifest.json` — source and output hashes, row counts and validation state.

## 3. Decision summary

The summary keeps separate:

- A1 commercial score and band;
- A2 data-quality status;
- A2 eligibility;
- workflow state;
- recorded human decision;
- number of fields, evidence records, review-queue items and requalification items;
- limitations and unresolved governance controls.

A high A1 score never implies that the A2 record is complete or approved.

## 4. Review queue

A field appears in the queue when at least one condition applies:

- field review is pending, held or needs changes;
- field quality is gap, conflict, partial, invalid or error;
- proposed action is add, update, clear request or hold;
- conflict is possible or material;
- the proposed value is protected.

Priority order:

```text
blocked → protected → conflict → gap → change → review
```

Each row shows current baseline, all observations, proposed action/value, evidence IDs, verification, confidence, freshness, conflict, protection, review and application states.

## 5. Evidence view

The evidence view combines:

- A1 evidence retained in the immutable handoff and labelled `a1_reference`;
- A2 evidence from the canonical evidence registry.

It preserves complete IDs and URLs, source-policy status, retrieval/source dates, claim type, reliability, supported assessments/signals, cost status, summary and data-minimisation notes.

## 6. Requalification view

The view displays separate rows for:

- A2 signals;
- A2-to-A1 returns;
- A1-produced score revisions.

Potential score direction remains advisory. Numeric prior/revised scores are displayed only from an authoritative A1 score-revision reference. The view performs no scoring.

## 7. Format rules

### Markdown

Provides a compact decision summary, review queue, gaps/conflicts, requalification, evidence and action boundaries.

### CSV

Arrays and structured values are JSON-encoded inside cells. URLs and identifiers remain complete. CSV files are UTF-8 and lossless for every selected column.

### Excel

Workbook sheets:

1. Read Me;
2. Summary;
3. Review Queue;
4. Fields;
5. Evidence;
6. Requalification;
7. Audit.

The workbook uses Arial, filters, frozen headers, wrapped text and full hyperlinks. It contains no formulas or Excel error values.

## 8. Read-only boundary

The package contains no editable reviewer-action column. Human decisions must be recorded through a future guarded workflow that creates a new canonical revision.

The renderer cannot:

- approve or reject a field or record;
- calculate an A1 score;
- write to HubSpot or Twenty;
- send outreach;
- call a provider;
- alter the canonical source file.

## 9. Validation result

| Check | Result |
|---|---:|
| Representative review packages | 6/6 PASS |
| Negative compatibility/read-only checks | 11/11 PASS |
| Markdown | PASS |
| CSV headers, rows, IDs and hashes | PASS |
| Excel sheet order, rows and headers | PASS |
| Excel formulas | 0 |
| Excel error values | 0 |
| Non-Arial populated cells | 0 |
| Canonical source mutations | 0 |
| External actions | 0 |
| Package manifest files | 74 |
| Independent post-fix review | PASS |

CSV formula-control strings use a reversible Base64-prefixed text encoding. Excel stores `=`, `+`, `-` and `@` prefixes as explicit text; leading tab or carriage return uses the same reversible encoding because SpreadsheetML normalises those control characters. Canonical JSON is never modified.

The carriage-return behaviour was identified after approval and corrected under approved decision H9; the correction is recorded separately without rewriting the original acceptance event.

Representative packages cover normal Farrier review, blocked application/dependency, Farrier conflict, protected Farrier update, Horse Owner gap and Horse Owner requalification.

## 10. Decisions confirmed by Séverine

| ID | Approved decision |
|---|---|
| H1 | Keep canonical JSON as the only lossless and authoritative A2 record. |
| H2 | Approve the Markdown, six-CSV and seven-sheet Excel review package structure. |
| H3 | Separate record summary, decision queue, all fields, evidence, requalification and audit views. |
| H4 | Preserve absence, quality, review, application, conflict, protection, confidence and freshness states without simplification. |
| H5 | Combine A1 evidence references and A2 evidence while preserving namespaces, IDs and full URLs. |
| H6 | Display A1 scores separately from A2 quality and display only A1-produced numeric revisions. |
| H7 | Keep Step 2H outputs read-only with no reviewer-input or writeback mechanism. |
| H8 | Require canonical source hashes, output hashes and row counts in every package manifest. |
| H9 | Require Excel outputs with professional formatting, no formulas and no error values. |
| H10 | Proceed to Step 2I canonical data-contract review and promotion after approval. |

H1–H10 were approved as drafted by Séverine on `2026-08-26T13:22:23Z`. This authorises Step 2I. It does not approve sources, integrations, providers, CRM writes, outreach, pilot, production or contractual acceptance.
