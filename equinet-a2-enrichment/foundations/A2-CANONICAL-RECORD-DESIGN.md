# Equinet A2 Canonical Enrichment Record — Design and Field Ownership

**Design version:** `0.1.0`  
**Profile:** `equinet-a2-enrichment`  
**Step:** `2A — Canonical Record Design and Field Ownership`  
**Status:** `APPROVED BY UNITALK OPERATIONS FOR STEP 2B`  
**Deployment language:** English

**Decision:** `APPROVED AS DRAFTED`  
**Approver:** Séverine, Unitalk Operations  
**Decision timestamp:** `2026-08-16T16:37:04Z`  
**Approved scope:** Canonical record structure and ownership decisions R1–R9. This is not approval of the JSON Schema, business field catalogue, integrations, pilot, production or contractual acceptance.

## 1. Purpose

This document defines the stable structure and ownership model for the canonical Equinet A2 Enrichment Record before the JSON Schema and detailed field dictionary are written.

The canonical record will be the lossless source for:

- A2 enrichment state;
- field-level evidence and proposed changes;
- human review;
- requalification signals returned to A1;
- future HubSpot/Twenty mappings;
- audit, reconciliation and derived review views.

It does not yet define the complete business field catalogue, exact state enums, source policy, confidence calculation, HubSpot property mapping or provider selection.

## 2. Approved dependencies

The design depends on:

- A2 Implementation Contract `0.1.1`;
- A1-to-A2 Boundary and Handoff Contract `1.0.1`;
- A1 Prospect Candidate schema `1.0.0`;
- the approved rule that A1 owns scoring and A2 may trigger a new A1-generated, human-approved score revision.

The profile remains `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`.

## 3. Design principles

1. **One lossless canonical JSON record.** Markdown, CSV, Excel and UI views are derived projections only.
2. **One A2 record lineage per accepted A1 handoff version.** A materially changed A1 handoff creates a new linked A2 record lineage.
3. **Immutable revisions.** Every accepted change creates a new A2 record revision; prior revisions remain available for audit.
4. **Immutable upstream input.** The accepted A1-to-A2 handoff and A1 candidate snapshot remain unchanged inside the A2 lineage.
5. **Generic field-assessment structure.** The schema defines how any field is assessed; a separate versioned business catalogue defines which fields A2 enriches.
6. **Evidence before status.** A value cannot become verified without permitted evidence and deterministic validation.
7. **Separate observations from proposals.** A2 may observe several values but proposes at most one resolution for a field in a record revision.
8. **Separate proposal from decision.** A2 proposes; the authorised reviewer decides; an integration applies only an approved action.
9. **Separate commercial fit from enrichment quality.** A1 score and A2 data quality remain distinct.
10. **Score revision without overwrite.** A2 may create a requalification signal; A1 creates a new deterministic score revision after review.
11. **Nullable future integrations.** A null HubSpot, Twenty or workflow ID means no reference exists in this record; it never means that the external system was checked and had no match.
12. **Append-only auditability.** Evidence, approvals, rejections, corrections, sync attempts and score revisions remain traceable.
13. **No hidden autonomy.** No record state may imply outreach, CRM write or downstream delivery without the required approval and verified action reference.
14. **Strict schema later.** The Step 2D JSON Schema will use `additionalProperties: false` and deterministic cross-field validation.

## 4. Record identity and revision model

### 4.1 Stable lineage

An accepted A1 handoff creates one stable `a2_record_id`.

```text
a2_record_id
└── record_revision_id 1
    └── record_revision_id 2
        └── record_revision_id 3
```

Each revision contains:

- `a2_record_id` — stable identifier for the A2 lineage;
- `record_revision_id` — unique immutable revision identifier;
- `revision_number` — deterministic positive sequence;
- `supersedes_revision_id` — prior A2 revision or null for the first revision;
- `created_at` — revision creation timestamp;
- `created_by` — actor/profile/workflow that created the revision;
- `change_reason` — initialisation, enrichment, correction, review, requalification result, refresh or reconciliation.

The durable application or workflow layer determines which revision is current. The historical JSON revisions are not rewritten to change an `is_current` flag.

### 4.2 New A1 handoff version

A changed A1 candidate snapshot, approval or handoff hash creates a new A2 lineage with:

- a new `a2_record_id`;
- a new immutable source handoff;
- an optional `supersedes_a2_record_id` linking the prior lineage;
- no silent replacement of the prior A2 record.

## 5. Canonical record sections

The future canonical record will contain the following top-level sections.

| Section | Purpose | Primary owner | Mutability class |
|---|---|---|---|
| `record_metadata` | Schema, record, revision and correlation identifiers | Unitalk deterministic runtime | Immutable per revision |
| `source_handoff` | Exact accepted A1-to-A2 input, approval and hash | A1/review layer | Immutable |
| `subject` | A2-resolved person, organisation and relationship entities | A2 proposes; human resolves material conflicts | Versioned |
| `enrichment_scope` | Requested package, targeted fields and run limits | Triggering user/workflow under policy | Immutable per run/revision |
| `field_assessments` | Baselines, observations, proposals, conflicts and decisions | Mixed, field-level ownership | Versioned and append-only by revision |
| `evidence_registry` | A2 evidence, sources, access method and provenance | A2/tools/providers | Append-only; corrections create new evidence |
| `data_quality` | Completeness, gaps, conflicts, freshness and quality result | Deterministic A2 controls | Derived per revision |
| `duplicate_and_eligibility` | A2 checks and authoritative eligibility visibility | Connector/script/reviewer | Versioned |
| `requalification` | Signals, returns and A1 score-revision references | A2 signal; A1 scoring; human approval | Append-only lifecycle |
| `review` | Field-level and record-level decisions | Authorised human reviewer | Append-only decision events |
| `workflow` | A2 processing and release state | Workflow/application layer | Controlled state transitions |
| `system_references` | Nullable Twenty, HubSpot, n8n and provider references | Authorised connectors | Versioned; never inferred |
| `governance` | Purpose, personal-data, consent visibility and retention references | Approved policy/authoritative systems | Versioned policy references |
| `audit_and_consumption` | Actor, model, tools, calls, credits, cost, errors and actions | Runtime/workflow/connectors | Append-only |

## 6. Source handoff ownership

`source_handoff` will retain a complete immutable accepted A1-to-A2 envelope or an equivalent lossless embedded snapshot with:

- handoff schema version;
- handoff ID and idempotency key;
- operating scope;
- approval event;
- eligibility gate results;
- full A1 Prospect Candidate snapshot;
- A1 candidate snapshot hash;
- A1 score, components, band and confidence;
- A1 evidence and source references;
- A1 audit correlation ID;
- action constraints active at acceptance;
- A2 receipt when the operating scope allows one.

A2 must never modify this section. Later corrections belong in A2 observations, proposals or requalification signals.

## 7. Subject and entity model

The A2 record must support:

- a person;
- an organisation;
- a person associated with an organisation;
- additional role-relevant stakeholders;
- explicit relationships between entities.

### Proposed stable entity structure

Each A2-resolved entity receives:

- `entity_id` local to the A2 record lineage;
- `entity_type` such as person or organisation;
- `source_identity_reference` back to the A1 snapshot when applicable;
- display name and aliases;
- identity-resolution status;
- possible or confirmed external matches;
- relationship links;
- material conflicts and review state.

A2 may propose corrections or additional entities, but it does not rewrite the A1 identity snapshot. A confirmed correction creates a new A2 revision and, when material to ICP fit, a requalification signal.

The exact maximum number and permitted stakeholder roles belong in the later business field catalogue and data-minimisation policy, not in the stable schema.

## 8. Generic field-assessment model

The schema will use a generic `field_assessments[]` collection instead of hard-coding every possible enrichment field.

Each assessment will include the following conceptual groups.

### 8.1 Field identity

- `field_assessment_id`;
- `field_key` from a separately versioned business field catalogue;
- `entity_id` or record-level scope;
- data category;
- sensitivity classification;
- expected value type and unit from the catalogue version.

### 8.2 Baseline

The baseline is the value known before the current A2 proposal. It may come from:

- the immutable A1 snapshot;
- an authorised HubSpot value;
- a staging value;
- a prior approved A2 revision;
- an authorised reviewer correction.

The baseline stores:

- value and normalised value where applicable;
- authoritative origin or source reference;
- observed/retrieved timestamp;
- manual/protected status;
- external record/property reference when available;
- evidence references or authoritative-system reference;
- status such as available, unavailable or not checked.

A baseline is never silently replaced inside the same revision.

### 8.3 Observations

A2 may collect zero, one or several observations for a field. Each observation stores:

- observation ID;
- raw and normalised value;
- evidence IDs;
- source/provider reference;
- retrieval or verification date;
- direct fact versus inference;
- verification result;
- confidence input;
- freshness input;
- error or limitation.

Conflicting observations remain visible. A2 does not delete an inconvenient observation to manufacture agreement.

### 8.4 Proposed resolution

A2 may prepare at most one proposed resolution per field assessment and revision:

- proposed action such as add, update, retain, no change, hold or clear-request;
- proposed value and normalised value;
- evidence references;
- rationale;
- deterministic confidence result;
- freshness result;
- conflict status;
- protected-field status;
- recommended reviewer action.

A `clear-request` is only a proposal and requires explicit human approval. A2 cannot autonomously delete an authoritative value.

### 8.5 Field decision and application

The authorised reviewer records:

- approved, rejected, needs changes or held;
- reviewer and role;
- decision timestamp;
- reason and optional corrected value;
- approved action scope.

A separate sync/application state records whether an approved action was:

- not requested;
- not available;
- pending;
- applied;
- failed;
- reconciled.

Approval does not prove application. Application requires a verified external action reference.

## 9. Evidence registry ownership

A2 evidence receives an A2-specific namespace and must not reuse an A1 evidence ID for new evidence.

Each A2 evidence record will preserve:

- stable evidence ID;
- source/provider identity;
- source URL or provider record reference;
- source type and source-policy status;
- access method;
- retrieval and source dates where available;
- title, excerpt or permitted result summary;
- fact, inference or contradiction classification;
- supported field assessments and requalification signals;
- reliability and independence metadata;
- applicable provider action, credit or cost metadata;
- data-minimisation and storage notes.

A1 evidence remains inside `source_handoff`. When A2 reuses it, A2 references the original A1 evidence ID and snapshot rather than copying it into the A2 evidence namespace as new evidence.

Evidence is append-only. A correction creates a superseding evidence record with a reason; it does not rewrite the original evidence history.

## 10. Data-quality ownership

A2 data quality describes the enrichment record, not commercial fit.

It will cover:

- field coverage and completion state;
- missing mandatory or requested fields;
- unverified fields;
- unresolved conflicts;
- stale fields;
- identity-resolution limitations;
- duplicate-check state;
- provider/source failures;
- minimum-package readiness when the relevant configuration exists;
- deterministic record-level quality status.

A high A1 ICP score does not imply high A2 data quality. High A2 data quality does not change the A1 score without the approved requalification lifecycle.

## 11. Duplicate and eligibility ownership

The A2 record must preserve separate states for:

- A1 duplicate checks received in the handoff;
- A2 local or provider duplicate checks;
- future HubSpot duplicate checks;
- customer, active opportunity, partner, distributor, consent, suppression and outreach-eligibility visibility.

States such as unavailable, not checked, no match, possible match, confirmed duplicate and error remain distinct.

A2 may recommend a hold or block. Authoritative CRM status and human decisions control production eligibility when the integration becomes available.

## 12. Requalification and score-revision ownership

### 12.1 `requalification_signal`

A2 owns creation of a signal when verified new evidence may strengthen, weaken or contradict an A1 criterion. The signal will contain:

- signal ID;
- affected A1 criterion ID;
- prior A1 criterion state;
- proposed evidence state, not proposed points;
- A2 evidence IDs and reused A1 evidence references;
- materiality and potential score direction;
- reason and limitations;
- created-at and created-by metadata;
- review/routing status.

A2 must not populate a replacement A1 score, band or score components in the signal.

### 12.2 `requalification_return`

After the applicable review gate, the workflow may package one or more signals into a return payload to A1. The return preserves:

- return ID;
- A2 record and revision IDs;
- original A1 candidate and score references;
- approved signals and evidence;
- return approval;
- delivery and receipt states;
- A1 processing status.

### 12.3 A1 score revision reference

A1 owns evidence acceptance and deterministic rescoring. A2 may store only the returned authoritative result:

- A1 score revision ID;
- prior revision ID;
- A1 candidate ID;
- scoring model version;
- approved score and band returned by A1;
- A1 approval actor and timestamp;
- result reference and integrity metadata.

The original handoff score remains immutable. The latest approved revision may become operationally current, but every revision remains traceable.

## 13. Human review ownership

The canonical record must support both:

### Field-level review

Used to approve, reject, correct or hold individual proposed values.

### Record-level review

Used to decide whether the A2 record is:

- approved for further controlled processing;
- held for more research;
- returned for changes;
- blocked or rejected;
- eligible for a later approved sync or downstream handoff.

A record-level approval cannot silently approve a protected field when the policy requires explicit field-level approval.

During the pilot, every enriched record requires record-level human review. Protected-field changes and material conflicts require explicit field-level review.

## 14. Workflow state ownership

The canonical record will reserve controlled states for the A2 lifecycle, with exact enums defined in Step 2B.

The conceptual path is:

```text
initialised
→ enrichment_planned
→ enrichment_in_progress
→ review_required
→ approved | changes_requested | held | blocked | rejected
→ ready_for_sync
→ sync_pending
→ synced | sync_failed
→ reconciled
```

No-integration records cannot progress to `ready_for_sync`, `sync_pending`, `synced` or `reconciled`.

Requalification has a separate lifecycle and must not be represented by changing the A2 workflow state alone.

## 15. System-reference ownership

The record reserves nullable references for:

- source handoff and A1 candidate;
- Twenty or alternative staging record;
- HubSpot Contact, Company and later relevant object IDs;
- HubSpot proposed-patch and sync IDs;
- n8n workflow execution and work-item IDs;
- provider request/response IDs;
- A3 and A14 future handoff IDs;
- A1 requalification return and score revision IDs.

External-system references are written only by the authorised connector or workflow that verified them. A null value means no reference is recorded; it does not prove no record exists externally.

Exact HubSpot object and property mappings remain outside the canonical schema.

## 16. Governance ownership

The canonical record will reference, rather than duplicate, approved policies for:

- processing purpose;
- source permissions;
- provider/subprocessor approval;
- personal-data classification;
- consent, opt-out and suppression visibility;
- retention and deletion;
- administrator visibility;
- protected fields;
- approval matrix;
- cost and consumption controls.

The record must preserve the policy versions applied to each run or decision. Missing governance configuration remains visible and may block the applicable action.

## 17. Audit and consumption ownership

The record revision must preserve or reference:

- actor, profile and trigger;
- timestamps and correlation IDs;
- model, tools, providers and source calls;
- schema and policy versions;
- input and output artifact references;
- approval events;
- external action attempts and results;
- retry and idempotency references;
- token, API-call, credit and cost metadata when available;
- errors, warnings and blocked reasons.

Audit events are append-only. Corrections create new events or revisions.

## 18. Mutability classes

| Class | Meaning | Examples |
|---|---|---|
| Immutable input | Never modified after acceptance | source handoff, A1 snapshot, original A1 score |
| Immutable revision | One canonical JSON revision is never edited after release | record revision metadata and content |
| Append-only history | New records may be added; prior records remain | evidence, observations, approvals, audit, score revisions |
| Deterministic derived state | Recomputed in a new revision from authoritative inputs | confidence, freshness, completeness, quality status |
| Human-controlled decision | Changes only through a new recorded decision event | field and record approvals |
| External-authoritative mirror | Refreshed from the connected source in a new revision | CRM baseline, customer status, suppression state |
| Connector-controlled reference | Written only after verified external action | HubSpot IDs, sync IDs, workflow execution IDs |

## 19. Source-of-truth precedence

| Data | Source of truth |
|---|---|
| Original candidate, A1 evidence and original score | Immutable accepted A1 handoff |
| Current live CRM values | HubSpot after integration |
| A2 observations and evidence | Canonical A2 record and approved evidence policy |
| Proposed field resolution | A2 proposal in the canonical record |
| Field and record decision | Recorded authorised human decision |
| A1 score revision | A1 deterministic scoring output plus human approval |
| External action result | Authorised connector/application receipt |
| Organisation context | Unitalk/Honcho, subordinate to authoritative live systems |

When authorities conflict, the record preserves both values and routes the conflict. It does not silently overwrite the lower-precedence value or erase history.

## 20. Stable schema versus later configuration

### Stable canonical schema

The schema will define:

- record and revision structure;
- generic entities and relationships;
- generic field assessments;
- evidence and observation shape;
- proposals and review decisions;
- quality, duplicate and requalification containers;
- system-reference and audit containers.

### Separate versioned business configuration

The following remain outside the schema:

- list of fields A2 enriches;
- Horse Owner and Farrier minimum data packages;
- field value types, units and normalisation methods;
- protected-field catalogue;
- allowed sources and providers per field;
- confidence and freshness rules;
- source priority and conflict policy;
- review matrix;
- budget and call limits;
- HubSpot/Twenty mappings;
- retention rules.

This separation allows Equinet to change business rules or system mappings without breaking the canonical record structure.

## 21. Information deliberately nullable until integration

The record must allow explicit null or unavailable states for:

- HubSpot Contact and Company IDs;
- CRM property names and associations;
- customer, Deal, partner and distributor state;
- consent, opt-out and suppression checks;
- owner and territory;
- staging record and review-work-item IDs;
- n8n workflow references;
- provider request IDs;
- sync and reconciliation IDs;
- A3/A14 delivery references.

Null does not mean checked, absent, eligible or approved. Each applicable check has a separate status.

## 22. Open items not blocking Step 2A

The following are deferred to later steps and remain visible:

- exact field and state definitions in Step 2B;
- canonical JSON types and required fields in Step 2D;
- final field catalogue and minimum packages in Step 3;
- source, confidence, freshness and conflict policies in Step 3;
- named Equinet reviewers and backup owner;
- maximum stakeholder scope and role categories;
- provider raw-payload retention rules;
- detailed retention and deletion policy;
- HubSpot/Twenty object and property mappings;
- production workflow and integration permissions.

## 23. Step 2A acceptance criteria

Step 2A is ready for approval when:

- every future canonical section has a purpose and owner;
- A1 input, A2 evidence, human decisions and connector actions are separated;
- baseline, observations, proposed resolution, decision and application are distinct;
- A1 scoring ownership and the score-revision lifecycle are explicit;
- mutable business rules remain outside the stable schema;
- future HubSpot/Twenty references are nullable and do not imply checks;
- revisions and history cannot be silently overwritten;
- the design is entirely in English;
- Séverine's approval of decisions R1–R9 is recorded below.

## 24. Decisions confirmed by Séverine

| ID | Approved decision |
|---|---|
| R1 | Create one A2 record lineage per accepted A1 handoff version. A materially changed A1 handoff creates a new linked lineage. |
| R2 | Make every released A2 JSON revision immutable; changes create a new `record_revision_id` and retain prior revisions. |
| R3 | Embed the complete accepted A1-to-A2 handoff as immutable source input so the A2 record is lossless and usable without live integrations. |
| R4 | Use generic `field_assessments[]` in the stable schema and keep the list of business fields in a separate versioned catalogue. |
| R5 | Model each field as baseline + observations + one proposed resolution + human decision + separate application state. |
| R6 | Use an A2-specific evidence namespace; reference reused A1 evidence without relabelling it as new A2 evidence. |
| R7 | Support both field-level and record-level review; protected-field changes require explicit field-level approval. |
| R8 | Store `requalification_signal`, `requalification_return` and returned A1 score-revision references while keeping A1 responsible for deterministic rescoring. |
| R9 | Keep external-system IDs nullable and connector-controlled; null never means checked, absent or eligible. |

R1–R9 were approved as drafted by Séverine on `2026-08-16T16:37:04Z`. This authorises Step 2B Field Dictionary and State Model. It does not approve the JSON Schema, business field catalogue, integrations, pilot, production writes, outreach or contractual acceptance.
