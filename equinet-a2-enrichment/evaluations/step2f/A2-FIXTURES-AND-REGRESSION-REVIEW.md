# Decision Review — Step 2F Fixtures and Regression Tests

**Version:** `0.1.0`  
**Status:** `APPROVED BY UNITALK OPERATIONS FOR STEP 2G`  
**Profile status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`  
**Canonical schema:** `1.0.0-draft.2`  
**Cross-field validator:** `0.1.0`  
**Technical validation:** PASS  
**Human decision:** APPROVED AS DRAFTED  
**Approver:** Séverine, Unitalk Operations  
**Decision timestamp:** `2026-08-26T10:38:53Z`

## 1. Technical result

| Check | Result |
|---|---:|
| Valid business scenarios | 16/16 PASS |
| Negative business scenarios | 13/13 PASS |
| Total Step 2F scenarios | 29/29 PASS |
| Farrier scenarios | 13 |
| Horse Owner scenarios | 16 |
| Required scenario names present | PASS |
| Scenario and prior-revision fixture hashes | PASS |
| Package manifest files | 67 |
| All records synthetic | PASS |
| Recorded external-action claims | 0 |
| External actions performed | 0 |
| Independent post-fix review | PASS |

## 2. Valid scenario coverage

### Farrier

- initialisation;
- planning with a visible gap;
- enrichment in progress;
- review required;
- record approved without external write;
- material conflict held;
- confirmed duplicate blocked;
- protected update awaiting explicit approval.

### Horse Owner

- initialisation;
- planning with horse-count gap;
- enrichment in progress;
- review required;
- record approved without external write;
- unresolved gap held;
- possible duplicate held;
- complete requalification resulting in an A1-produced score revision.

## 3. Negative coverage

The suite rejects missing evidence, blocked evidence, protected overwrite, false sync, A2 score production, outreach authorisation, unauthorised provider use, cross-segment fields, missing required assessments, invalid review-ready status, duplicate eligibility errors, invalid A1 score arithmetic and incomplete field decisions.

Every positive scenario has scenario-specific assertions. Every negative scenario must produce its named error and the exact expected error count, preventing an unrelated validation failure from being mistaken for coverage.

## 4. Important limitation

The Business Field Catalogue used here is explicitly synthetic and exists only to test the validation mechanism. It does not replace the future Equinet-approved Field Catalogue or minimum data packages.

No live source, CRM, provider or workflow was used.

## 5. Decisions confirmed by Séverine

| ID | Decision |
|---|---|
| F1 | Accept the synthetic Farrier and Horse Owner fixture set as the Step 2F baseline. |
| F2 | Validate lifecycle progression through explicit prior-revision pairs. |
| F3 | Retain valid gap, conflict, duplicate and protected-field review states. |
| F4 | Validate declared business outcomes in addition to schema compliance. |
| F5 | Require negative cases to fail for their named expected reason. |
| F6 | Keep every Step 2F fixture synthetic and perform no external action. |
| F7 | Use the synthetic Field Catalogue only to test external catalogue enforcement. |
| F8 | Defer the real Equinet Field Catalogue and minimum packages to Step 3. |
| F9 | Keep Step 2E adversarial tests and prior foundation checks in regression. |
| F10 | Proceed to Step 2G handoff-to-record initialisation after approval. |

## 6. Recorded decision

**Approved as drafted.** F1–F10 are approved and Step 2G may begin.

This approval is limited to the synthetic fixture and regression package. It does not approve live data access, providers, integrations, CRM writes, outreach, pilot, production or contractual acceptance.
