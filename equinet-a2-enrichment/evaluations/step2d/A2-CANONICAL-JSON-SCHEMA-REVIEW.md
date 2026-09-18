# Decision Review — Step 2D Canonical A2 JSON Schema

**Version:** `1.0.0-draft.1`  
**Status:** `APPROVED BY UNITALK OPERATIONS FOR STEP 2E`  
**Profile status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`  
**Technical validation:** PASS  
**Human decision:** APPROVED AS DRAFTED  
**Approver:** Séverine, Unitalk Operations  
**Decision timestamp:** `2026-08-26T09:01:26Z`

## 1. Technical result

| Check | Result |
|---|---:|
| JSON Schema Draft 2020-12 compilation | PASS |
| Canonical sections | 14/14 PASS |
| Strict local object schemas | PASS — 0 unstrict objects |
| Pinned dependency hashes | 8/8 PASS |
| State-vocabulary bindings | 39/39 PASS |
| Approved external schema references | 4/4 PASS |
| CRM mapping exclusion checks | 4/4 PASS |
| Valid smoke fixtures | 2/2 PASS |
| Negative smoke fixtures | 5/5 PASS |
| Total smoke cases | 7/7 PASS |

## 2. What this schema establishes

The schema establishes one lossless canonical JSON record with fourteen required sections, immutable record revisions, the full A1 handoff, generic field assessments, A2 evidence, human review, workflow state, external references, governance and audit/consumption.

Every locally defined structural object is closed with `additionalProperties: false`.

## 3. Record shape

```text
record_metadata
source_handoff
subject
enrichment_scope
field_assessments
evidence_registry
data_quality
duplicate_and_eligibility
requalification
review
workflow
system_references
governance
audit_and_consumption
```

## 4. Field-assessment shape

```text
baseline
→ observations
→ proposed_resolution
→ field_review
→ application
```

The schema supports generic scalar, list and strict component-based structured values. The separate Field Catalogue determines which type and component keys are valid for a business field.

## 5. Requalification and scoring

The record references the complete approved Step 2C contracts. A2 may store signals and approved returns, but the schema rejects unapproved A2 score fields. Numeric score revisions remain A1-produced artifacts.

## 6. External references

The schema reserves nullable references for HubSpot, Twenty, n8n, providers, A3, A14 and A1 requalification results.

A null external ID means only that no verified reference is stored. It does not mean the external system was checked or found no record.

## 7. Structural guardrails

The schema already rejects:

- unknown structural fields;
- incorrect schema versions;
- invalid approved state values;
- revision 1 claiming a prior revision;
- completed reviews without an appropriate reviewer and timestamp;
- applied/reconciled actions without an external reference;
- manual no-integration records entering sync states;
- no-integration records claiming external connector IDs or CRM-write authority;
- a score-producing property added to an A2 signal.

## 8. Deliberately external configurations

The schema does not embed:

- the Business Field Catalogue;
- minimum data packages;
- source/provider rules;
- field confidence/freshness rules;
- protected-field lists;
- the approval matrix;
- HubSpot/Twenty mappings;
- retention rules.

This allows those business and system configurations to evolve without changing the canonical record structure.

## 9. Deferred checks

Step 2E will validate cross-field references, IDs, evidence namespaces, workflow transitions, protected fields, external receipts and requalification package consistency.

Step 2F will create the complete Farrier/Horse Owner positive and negative regression fixture set.

## 10. Decisions confirmed by Séverine

| ID | Decision |
|---|---|
| D1 | Accept `1.0.0-draft.1` as the Step 2D schema proposal. |
| D2 | Require exactly the fourteen approved canonical sections. |
| D3 | Require strict locally defined structural objects. |
| D4 | Preserve the full A1 handoff through its approved schema reference. |
| D5 | Use generic strict values and keep business types in the Field Catalogue. |
| D6 | Reuse the complete Step 2C schemas and preserve A1-only numeric scoring. |
| D7 | Keep future system IDs nullable and connector-controlled. |
| D8 | Enforce structural no-integration and approval ceilings in the schema. |
| D9 | Keep mutable field, policy and CRM mapping configurations outside the schema. |
| D10 | Complete cross-field checks in Step 2E and full business fixtures in Step 2F. |

## 11. Recorded decision

**Approved as drafted.** D1–D10 are approved and Step 2E may begin.

This approval is limited to the Step 2D canonical schema. It does not approve source access, providers, integrations, CRM write, outreach, pilot, production or contractual acceptance.
