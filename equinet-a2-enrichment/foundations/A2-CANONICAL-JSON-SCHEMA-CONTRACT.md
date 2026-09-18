# Equinet A2 Canonical Enrichment Record — JSON Schema Contract

**Current schema version:** `1.0.0`  
**Approved baseline:** `1.0.0-draft.1`  
**JSON Schema dialect:** Draft 2020-12  
**Profile:** `equinet-a2-enrichment`  
**Step:** `2D — Canonical A2 JSON Schema`  
**Status:** `PROMOTED BY UNITALK OPERATIONS IN STEP 2I`  
**Created:** `2026-08-26T08:56:07Z`

**Decision:** `APPROVED AS DRAFTED`  
**Approver:** Séverine, Unitalk Operations  
**Decision timestamp:** `2026-08-26T09:01:26Z`  
**Approved scope:** Step 2D decisions D1–D10, Step 2E correction E13 and Step 2I promotion decisions I1–I10. Draft.2 remains preserved in the pre-promotion evidence snapshot.

## 1. Purpose

This contract defines the strict canonical JSON structure for one immutable Equinet A2 Enrichment record revision.

The canonical JSON record is the only lossless A2 record. Future Markdown, CSV, Excel, UI and CRM views are derived projections and must not create a second field model.

This draft does not activate enrichment sources, providers, A1/A2 delivery, HubSpot, Twenty, n8n, CRM writes, outreach, pilot use or production use.

## 2. Authoritative schema

- File: `foundations/contracts/canonical/a2-enrichment-record.schema.json`
- Schema ID: `https://unitalk.ai/schemas/equinet/a2/enrichment-record/1.0.0`
- Current schema hash: `2d3fb023ca1721b7d584b2b457fce51cd44f44d268ab06e9fc119cba1ec13531`

The schema is pinned by `a2-enrichment-record.dependency-manifest.json` to the approved Step 2A–2C foundations and relevant A1 contracts.

## 3. Canonical sections

Every record requires exactly these fourteen top-level sections:

1. `record_metadata`
2. `source_handoff`
3. `subject`
4. `enrichment_scope`
5. `field_assessments`
6. `evidence_registry`
7. `data_quality`
8. `duplicate_and_eligibility`
9. `requalification`
10. `review`
11. `workflow`
12. `system_references`
13. `governance`
14. `audit_and_consumption`

Unknown top-level or nested structural properties are rejected.

## 4. Revision and lineage model

- `a2_record_id` identifies one lineage created from one accepted A1 handoff version.
- `record_revision_id` identifies one immutable A2 revision.
- Revision 1 requires `supersedes_revision_id: null`.
- A later revision requires a prior `A2-REV-*` identifier.
- A materially changed A1 handoff creates a new A2 lineage and may use `supersedes_a2_record_id`.
- The record does not contain a mutable `is_current` flag. The durable application layer controls the operational current pointer.

## 5. Immutable A1 source handoff

`source_handoff.handoff_snapshot` references the complete strict A1-to-A2 Handoff schema `1.0.1`.

The wrapper also records the accepted handoff ID, idempotency key, operating scope, eligibility state, A2 acceptance actor and time, and candidate snapshot hash.

The embedded handoff is immutable input. A2 observations, corrections and requalification signals never rewrite it.

## 6. Generic field-assessment structure

The schema defines a reusable field-assessment container:

```text
baseline
→ observations
→ proposed_resolution
→ field_review
→ application
```

The schema supports scalar, list and strict key/value component representations for generic canonical values. The separate Field Catalogue controls the permitted business type, units and component keys for each `field_key`.

One assessment may contain multiple observations but at most one `proposed_resolution` per immutable revision.

Human approval and external application remain separate. An approved field does not prove that a CRM write occurred.

## 7. Evidence and source boundary

- A2-native evidence uses the `A2-EV-*` namespace.
- Reused A1 evidence remains inside the immutable handoff and is referenced without being relabelled as new A2 evidence.
- Evidence records preserve source, access method, source-policy state, retrieval time, supported assessments/signals, reliability, cost status and data-minimisation notes.
- The schema stores source-policy status but does not activate a source or define field-specific source permissions.

## 8. Requalification boundary

The canonical schema references the approved Step 2C schemas directly:

- A2 requalification signal `0.1.0`;
- A2-to-A1 requalification return `0.1.0`;
- A1 score-revision reference `0.1.0`.

This preserves the full approved payloads. The strict signal schema rejects unapproved score fields such as `points_awarded`. Only the referenced A1 score-revision artifact may contain a revised numeric score.

## 9. External-system references

The schema reserves nullable connector-controlled references for:

- A1 candidate and handoff;
- Twenty or another approved staging record;
- HubSpot Contact, Company, Deals, proposed patch and sync;
- n8n work item and execution;
- provider requests;
- future A3 and A14 handoffs;
- A1 requalification return and score revision.

The A1 candidate and handoff IDs are mandatory. Future connector IDs are nullable.

`null` means only that no verified reference is stored in this revision. It never means that a system was checked, no match exists, the record is eligible or an action was approved.

## 10. Structural safety constraints

The draft schema enforces, where JSON Schema can express the rule safely:

- strict objects with `additionalProperties: false`;
- exact schema version;
- complete fourteen-section record structure;
- approved Step 2B state vocabularies;
- revision-one and later-revision lineage shapes;
- targeted-field requests containing at least one key;
- default-package requests containing no explicit keys;
- synthetic record and synthetic operating-scope alignment;
- reviewer and timestamp presence for completed human decisions;
- action receipts for `applied` and `reconciled` application states;
- reasons for held, blocked and failed workflow states;
- no-integration records excluded from sync states and external references;
- `synced` or `reconciled` requiring CRM-write authorisation and a HubSpot sync reference;
- `record_approved` requiring an approved record decision and complete required field decisions;
- no A2 score fields inside requalification signals.

## 11. Configuration deliberately outside the schema

The following remain separate versioned configurations:

- Business Field Catalogue;
- Farrier and Horse Owner minimum data packages;
- source and provider policy;
- confidence and freshness rules;
- protected-field catalogue;
- approval matrix;
- HubSpot/Twenty object and property mapping;
- retention and deletion policy;
- operational quotas and field-specific normalisation rules.

No HubSpot internal property name is embedded in the canonical schema.

## 12. Step 2E responsibilities

The deterministic cross-field validator will enforce rules that JSON Schema cannot reliably express alone:

- identifier equality across handoff, record, evidence, signals and system references;
- evidence-reference existence and namespace integrity;
- Field Catalogue type and value checks;
- unique IDs inside each record;
- workflow transition validity against the prior revision;
- protected-field proposal, decision and application consistency;
- external action receipt and reconciliation integrity;
- no-integration ceilings across all nested payloads;
- requalification signal/return/revision relationship integrity;
- immutable handoff and revision hashes.

## 13. Step 2F responsibilities

Step 2F will add the complete representative fixture and regression suite, including Farrier, Horse Owner, gap, conflict, duplicate, requalification, protected-field and false-sync scenarios.

Step 2D contains only schema smoke fixtures required to prove structural validity.

## 14. Technical validation result

| Check | Result |
|---|---:|
| Draft 2020-12 compilation | PASS |
| Canonical sections | 14/14 PASS |
| Local strict object schemas | PASS — 0 unstrict objects |
| Pinned dependency hashes | 8/8 PASS |
| State-vocabulary bindings | 39/39 PASS |
| Approved external schema references | 4/4 PASS |
| CRM mapping exclusion checks | 4/4 PASS |
| Valid smoke fixtures | 2/2 PASS |
| Negative smoke fixtures | 5/5 PASS |
| Total smoke cases | 7/7 PASS |

Negative smoke fixtures correctly reject:

- an unknown top-level property;
- an unknown nested property;
- an incorrect schema version;
- a no-integration record claiming a sync;
- an A2 requalification signal containing `points_awarded`.

## 15. Open items

- deterministic cross-field validator in Step 2E;
- full regression fixtures in Step 2F;
- Business Field Catalogue and minimum packages in Step 3;
- named A2 reviewer and backup;
- active A1/A2, HubSpot, Twenty, n8n and provider integrations;
- retention, permissions and production approval.

### Draft.2 correction approved during Step 2E

Draft.1 allowed relationship scope conceptually but constrained `field_assessments[].entity_id` to `A2-ENT-*` values. Draft.2 keeps the approved property name for compatibility and permits an `A2-REL-*` target only when `scope` is `relationship`. This correction was approved through Step 2E decision E13.

## 16. Decisions confirmed by Séverine

| ID | Approved decision |
|---|---|
| D1 | Use `a2-enrichment-record.schema.json` version `1.0.0-draft.1` as the Step 2D Unitalk proposal. |
| D2 | Require exactly the fourteen approved canonical sections in every record revision. |
| D3 | Apply `additionalProperties: false` to every locally defined structural object. |
| D4 | Preserve the complete A1-to-A2 handoff through the approved external schema reference. |
| D5 | Use generic strict canonical-value shapes while leaving business value types, units and component keys to the separate Field Catalogue. |
| D6 | Reference the complete Step 2C signal, return and A1 score-revision schemas; A2 remains unable to calculate a score. |
| D7 | Keep HubSpot, Twenty, n8n, provider and downstream IDs nullable and connector-controlled; null does not prove a check or absence. |
| D8 | Enforce structural no-integration and approval ceilings in the schema without claiming integration readiness. |
| D9 | Keep business fields, minimum packages, source rules, confidence/freshness rules, protected fields, CRM mappings and retention outside the stable schema. |
| D10 | Assign cross-field integrity to the deterministic Step 2E validator and full business variants to the Step 2F regression suite. |

D1–D10 were approved as drafted by Séverine on `2026-08-26T09:01:26Z`. This authorises Step 2E. It does not approve live enrichment, source use, provider spend, integration, CRM write, outreach, pilot, production or contractual acceptance.

## 17. Step 2I promotion

Séverine approved decisions I1–I10 on `2026-08-26T15:15:50Z`. The approved `1.0.0-draft.2` structure was promoted without a canonical field, type, state, required-rule or conditional-rule change. Active synthetic fixtures and dependent tooling were regenerated against `1.0.0`; the complete pre-promotion state is retained in a hashed snapshot. This promotion establishes the stable canonical data contract only. It does not approve live enrichment, integrations, external actions, pilot readiness, production readiness or contractual acceptance.
