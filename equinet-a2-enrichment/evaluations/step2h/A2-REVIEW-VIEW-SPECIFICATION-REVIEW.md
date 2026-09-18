# Decision Review — Step 2H Review-View Specification

**Version:** `0.1.0`  
**Status:** `APPROVED BY UNITALK OPERATIONS FOR STEP 2I`  
**Profile status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`  
**Technical validation:** PASS  
**Human decision:** APPROVED AS DRAFTED  
**Approver:** Séverine, Unitalk Operations  
**Decision timestamp:** `2026-08-26T13:22:23Z`

## 1. Technical result

| Check | Result |
|---|---:|
| Representative packages | 6/6 PASS |
| Negative checks | 11/11 PASS |
| Formats | Markdown, six CSV files and Excel |
| Excel sheets | 7/7 PASS |
| Formula cells | 0 |
| Excel error values | 0 |
| Non-Arial populated cells | 0 |
| Canonical mutations | 0 |
| External actions | 0 |
| Package manifest files | 74 |
| Independent post-fix review | PASS |

CSV formula-control strings use a reversible Base64-prefixed text encoding. Excel preserves `=`, `+`, `-` and `@` values as explicit text and reversibly encodes leading tab or carriage-return values.

The carriage-return correction is recorded as a post-approval H9 implementation correction.

## 2. Representative views

- normal Farrier review queue;
- blocked application and workflow dependency;
- Farrier material conflict with both observed values and independent evidence;
- protected Farrier website update awaiting approval;
- Horse Owner required-data gap;
- Horse Owner requalification with signal, return and A1-produced score revision.

## 3. Information shown

- current and proposed values;
- complete observations;
- verification, confidence and freshness;
- gaps, conflicts and protected status;
- evidence IDs, source status and full URLs;
- field and record review states;
- application state;
- A1 score and band, visibly separate from A2 data quality;
- requalification direction and returned A1 score revision;
- audit events and consumption metadata.

## 4. Safety boundary

The views are read-only projections. They cannot approve a record, change canonical JSON, calculate an A1 score, write to CRM, call a provider or send outreach.

No reviewer-input column is included. A future guarded workflow must create a new canonical revision for any human decision.

## 5. Decisions confirmed by Séverine

| ID | Decision |
|---|---|
| H1 | Keep canonical JSON as the sole lossless source of truth. |
| H2 | Approve the Markdown, CSV and seven-sheet Excel package. |
| H3 | Separate summary, queue, complete fields, evidence, requalification and audit. |
| H4 | Preserve all canonical state distinctions. |
| H5 | Preserve A1/A2 evidence namespaces, identifiers and full URLs. |
| H6 | Keep A1 score separate from A2 quality and display only A1-produced score revisions. |
| H7 | Keep all Step 2H views read-only with no writeback. |
| H8 | Require hashes and row counts in every package manifest. |
| H9 | Require professional, formula-free and error-free Excel output. |
| H10 | Proceed to Step 2I canonical data-contract review and promotion after approval. |

## 6. Recorded decision

**Approved as drafted.** H1–H10 are approved and Step 2I may begin.

This approval is limited to the review-view specification and deterministic renderer. It does not approve integrations, CRM writes, outreach, pilot, production or contractual acceptance.
