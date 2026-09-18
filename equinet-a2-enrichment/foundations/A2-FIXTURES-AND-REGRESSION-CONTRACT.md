# Equinet A2 Fixtures and Regression Test Contract

**Suite version:** `0.1.0`  
**Profile:** `equinet-a2-enrichment`  
**Step:** `2F — Fixtures and Regression Tests`  
**Status:** `APPROVED BY UNITALK OPERATIONS FOR STEP 2G`  
**Canonical schema:** `1.0.0` — promoted in Step 2I  
**Cross-field validator:** `0.1.0`

**Decision:** `APPROVED AS DRAFTED`  
**Approver:** Séverine, Unitalk Operations  
**Decision timestamp:** `2026-08-26T10:38:53Z`

## 1. Purpose

This suite proves that the canonical A2 record and deterministic validator support representative Farrier and Horse Owner workflows before handoff initialisation, operational skills or integrations are built.

All records are synthetic test artifacts. The suite performs no live research, provider call, CRM access, write, outreach or downstream delivery.

## 2. Test architecture

Each case is declared in a machine-readable scenario manifest and contains:

- a canonical record fixture;
- an optional prior revision;
- the external synthetic Field Catalogue when business validation is required;
- the expected valid or invalid result;
- the exact expected failure reason for a negative case;
- expected business state assertions for a positive case.

Every record first passes or fails the strict JSON Schema and then the Step 2E cross-field validator. Positive cases must also match their declared segment, workflow, data-quality, eligibility, review, requalification and external-action outcomes.

## 3. Valid Farrier coverage

The suite covers:

- initial record creation from a valid A1 Farrier handoff;
- enrichment planning with a visible required-email gap;
- evidence-backed email and professional-credential enrichment;
- transition to human review;
- human-approved record with no external application;
- material conflicting email evidence routed to `held`;
- confirmed duplicate routed to `blocked`;
- protected website update retained as a proposal awaiting explicit field review.

## 4. Valid Horse Owner coverage

The suite covers:

- initial record creation from a valid A1 Horse Owner handoff;
- enrichment planning with a visible horse-count gap;
- evidence-backed horse-count enrichment;
- transition to human review;
- human-approved record with no external application;
- unresolved required-data gap routed to `held`;
- possible duplicate routed to `hold` and human review;
- complete A2-to-A1 requalification with an A1-produced score revision.

## 5. Synthetic Field Catalogue

The test-only catalogue defines representative fields for:

- person name, role, business email and professional credential;
- organisation name, website, service area, horse count and disciplines;
- person-to-organisation relationship role.

It defines test-only segment applicability and minimum-package requirements. It is not the Equinet-approved Business Field Catalogue and must not be promoted to operational configuration.

## 6. Negative regression coverage

The suite rejects:

- missing or blocked evidence;
- protected-field application without approval;
- false synthetic synchronisation;
- A2 score production;
- prohibited outreach;
- provider use without approval;
- cross-segment fields;
- missing required-package assessments;
- review-ready records containing conflicts;
- confirmed duplicates marked eligible;
- invalid A1 score revision arithmetic;
- record approval with unresolved field decisions.

The Step 2E suite remains part of the regression chain and separately covers identifier, hash, lifecycle, append-only and adversarial edge cases.

## 7. Acceptance boundaries

A valid fixture proves that the schema and deterministic rules accept the intended synthetic state. It does not prove:

- live source quality;
- provider accuracy;
- HubSpot or Twenty mapping correctness;
- OAuth scope or user permission correctness;
- n8n execution;
- CRM write safety in a connected environment;
- outreach eligibility;
- pilot or production readiness.

## 8. Technical result

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
| All records explicitly synthetic | PASS |
| External actions performed | 0 |

An independent adversarial review was run before this result was finalised. It led to semantic scenario assertions, per-fixture hashes, gated synthetic-only checks, computed external-action checks, an evidence-backed protected-field proposal, exact negative error counts and complete fixture inclusion in the package manifest.

## 9. Decisions confirmed by Séverine

| ID | Approved decision |
|---|---|
| F1 | Accept the synthetic Farrier and Horse Owner fixtures as the Step 2F business-regression baseline. |
| F2 | Validate complete lifecycle chains through prior-revision pairs rather than treating isolated later revisions as valid. |
| F3 | Preserve explicit valid gap, conflict, possible-duplicate, confirmed-duplicate and protected-field review paths. |
| F4 | Require positive cases to match declared business outcomes in addition to passing technical validation. |
| F5 | Require every negative case to fail for its named expected reason. |
| F6 | Keep all Step 2F fixtures synthetic and prohibit external actions during the suite. |
| F7 | Use the test-only Field Catalogue solely to verify external catalogue binding, segment applicability, required sets and value types. |
| F8 | Keep the actual Equinet Business Field Catalogue and minimum packages for Step 3 approval. |
| F9 | Retain Step 2E adversarial tests and all prior foundation validations in the regression chain. |
| F10 | Proceed next to deterministic A1-handoff-to-A2-record initialisation in Step 2G after approval. |

F1–F10 were approved as drafted by Séverine on `2026-08-26T10:38:53Z`. This authorises Step 2G. It does not approve live data access, providers, integrations, CRM writes, outreach, pilot, production or contractual acceptance.
