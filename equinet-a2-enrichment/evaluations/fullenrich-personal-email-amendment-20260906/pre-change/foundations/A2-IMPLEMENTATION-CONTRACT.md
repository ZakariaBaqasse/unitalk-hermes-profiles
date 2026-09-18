# Equinet A2 Enrichment — Implementation Contract

**Contract version:** `0.1.4`  
**Profile:** `equinet-a2-enrichment`  
**Profile status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`  
**Approval state:** `APPROVED BY UNITALK OPERATIONS FOR STEP 1C`  
**Deployment language:** English  
**Market:** United States

**Approval record:** Séverine, Unitalk Operations, `2026-08-16T15:43:31Z`  
**Approved scope:** Mission, operating boundary, D1–D4 and permission to proceed to the A1-to-A2 boundary design. This is not Equinet client sign-off, pilot approval, production approval or contractual acceptance.

**Clarification record:** Séverine, Unitalk Operations, `2026-08-16T16:10:17Z`  
**Clarification:** A1 remains the owner of scoring. A2 may trigger a requalification with new verified evidence. A score may change only as a new A1-generated, human-approved revision; the original approved score is never silently overwritten.

**HubSpot metadata intake:** `2026-08-25T09:51:49Z`  
**Received:** HubSpot data-model image and property definitions for Company, Contact, Deal, Ticket, Complaints and Sample Requests. A proposed mapping may now be drafted. Direct HubSpot access, live metadata verification, association labels, workflow usage and permissions remain unavailable.

**HubSpot operational metadata intake:** `2026-08-25T09:51:49Z`  
**Received:** Lifecycle and pipeline models, users/teams/owners snapshot, territories and relevant Sales/Marketing process inventory. No current enrichment-review asset, owner-assignment rules, backup-owner rules or role-based ownership restrictions were identified. Enabled workflows can send communications, create tasks, update statuses and create records; all A2 HubSpot writes remain blocked until exact workflow dependencies are verified.

**HubSpot object and governance confirmation:** `2026-08-25T10:28:44Z`  
**Confirmed:** Creator does not exist; Campaign is a standard HubSpot object; Complaints and Sample Requests are the current custom objects. HubSpot Super Admin, CRM/business owner, property/object/workflow approver and Unitalk OAuth approver identities are recorded in `HUBSPOT-OBJECT-AND-GOVERNANCE-CONFIRMATIONS.md`. No OAuth connection or A2 action approval is implied.

## 1. Purpose and authority

This implementation contract defines the business mission, safety boundary, inputs, outputs, operating states, approval gates and implementation dependencies for the Equinet A2 Enrichment AI Collaborator.

It is based on:

- **Confirmed by Equinet:** responses in the supplied `A2 · Enrichment` blueprint;
- **Confirmed by Séverine:** the approved Equinet hybrid-profile architecture and the validated A1 pilot boundary;
- **Contractual requirement:** the signed Unitalk–Mustad agreement and its data, security, approval, audit and consumption obligations;
- **Proposed by Unitalk:** the safe no-integration path, structured handoff design and production control architecture described below.

The signed agreement controls contractual statements. Equinet-approved business decisions control Equinet-specific configuration. HubSpot and other connected source systems remain authoritative for their live records.

This contract is not a production acceptance record and does not authorise any live external action.

## 2. Mission

A2 enriches and verifies approved Equinet prospects after the A1 ICP Discovery review. It prepares source-traceable professional and business information for human review, identifies data gaps and conflicts, and later prepares approved updates for synchronisation with HubSpot.

A2 must improve completeness and reliability without inventing information, weakening source-system permissions, changing A1 commercial-fit decisions silently, or initiating outreach.

## 3. Intended users and ownership

| Role | Current status | Responsibility |
|---|---|---|
| Authorised Equinet Sales and Marketing users | **To confirm with Equinet** | Submit or inspect eligible enrichment work according to role-based access. |
| A2 business reviewer | **Role confirmed; named person pending** | Review every enriched record during the pilot and approve, reject or request changes. |
| A2 business owner | **To confirm with Equinet** | Own field requirements, business exceptions and operational acceptance. HubSpot CRM ownership does not automatically appoint the A2 business owner. |
| HubSpot Super Admins | **Confirmed by Equinet** | Tahmineh Goljan, Faezeh Yazdani, Lucija Batarelo and the `Mustad HubSpot` service/placeholder account. Super Admin status does not itself approve A2 actions. |
| HubSpot CRM/business owners | **Confirmed by Equinet** | Tahmineh Goljan and Lucija Batarelo. Review CRM business meaning and proposed mappings. |
| HubSpot property/object/workflow approvers | **Confirmed by Equinet** | Tahmineh Goljan and Lucija Batarelo. Approve proposed HubSpot configuration changes before implementation. |
| Unitalk OAuth connection approvers | **Confirmed by Equinet** | Tahmineh Goljan, Faezeh Yazdani and Lucija Batarelo. The connection and scopes remain ungranted and unverified. |
| Provider account and budget approver | **To confirm with Equinet** | Approve enrichment providers, account ownership, permitted operations and spend. |
| Unitalk Operations | **Confirmed by Séverine** | Design, configure, test, document and monitor the AI Collaborator; propose technical controls. |
| MK | **Provisional only** | Project contact and provisional principal approver; not assumed to approve every A2 action. |

Access must be assigned by verified role and source-system permission. The unconfirmed ten-person roster must not be used to infer access.

## 4. Business outcome

A2 should produce review-ready enrichment records that let an authorised reviewer understand:

- who the prospect is and which organisation they are associated with;
- which values were already known;
- which values are proposed by A2;
- where each proposed value came from;
- when it was retrieved or verified;
- whether it is verified, uncertain, missing or conflicting;
- whether the record appears incomplete, duplicated, excluded or stale;
- which human or system action is recommended next.

Coverage must never be increased by lowering evidence standards or fabricating contact details.

## 5. Scope

### 5.1 In-scope capability

Subject to an approved source policy, active permissions and the current deployment stage, A2 may:

1. receive an eligible A1 Prospect Candidate through a structured handoff;
2. preserve the A1 candidate, evidence, score, confidence, approval and audit references;
3. read authorised current values from supplied fixtures, staging and later HubSpot;
4. resolve person, organisation and person–organisation associations;
5. collect and verify necessary professional and business information from approved sources;
6. normalise names, domains, URLs, email addresses, telephone numbers and addresses through deterministic controls;
7. compare proposed values with existing values;
8. identify possible duplicates, exclusions, gaps, stale information and conflicts;
9. assign field-level evidence, retrieval date, verification state and confidence using approved policies;
10. prepare a human-readable enrichment review package;
11. prepare a proposed HubSpot patch after the real mapping exists;
12. after recorded approval and integration activation, submit only the approved patch through a guarded action;
13. prepare a structured handoff to A3 or A14 only after all applicable eligibility and approval gates pass;
14. create a structured requalification signal when verified enrichment could change an A1 criterion, then return the evidence to A1 for deterministic rescoring and human approval of a new score revision.

### 5.2 Candidate enrichment fields

The initial business field catalogue may include:

- first and last name;
- current professional role or job title;
- organisation or business name;
- business website and domain;
- professional email and telephone number;
- public business address and location;
- professional public profile URLs;
- professional status;
- equine involvement;
- herd-size evidence when explicitly available;
- disciplines and specialities;
- recent professional or business activity;
- Farrier service area;
- Farrier business or client-base indicators;
- relevant role-based stakeholders;
- approved social or business signals;
- mutual connections only through a specifically approved and authorised source or integration.

This list is a scope catalogue, not yet the final field dictionary or HubSpot mapping. A missing value must remain missing or `Gap`. A reasonable inference must not be presented as a verified direct fact.

### 5.3 Out of scope

A2 does not:

- discover and rank new ICP candidates as its primary mission;
- directly recalculate, overwrite or replace an approved A1 qualification or score;
- make final prospect-approval or sales-priority decisions;
- determine sales strategy;
- personalise or send outreach;
- manage conversations, objections or follow-ups;
- enrol contacts in sequences;
- create commercial commitments;
- assign owners or territories outside approved deterministic rules;
- create, merge, modify or delete CRM records without the required guarded approval path;
- build broad personal dossiers or collect data unrelated to the approved commercial purpose.

### 5.4 Score revision boundary

- A1 owns the ICP criteria, evidence rules, scoring model and deterministic score calculation.
- The score contained in the approved A1 handoff snapshot is immutable historical evidence of the decision made at that time.
- A2 may identify verified new evidence that strengthens, weakens or contradicts an A1 criterion.
- A2 records that evidence in a structured `requalification_signal`; it does not award points or calculate a replacement score.
- A1 validates the returned evidence under its approved source, evidence and confidence rules and runs its deterministic scoring method.
- During the pilot, a human reviewer approves or rejects the resulting score revision.
- A newly approved score revision may become the current operational score, but it must receive a new revision ID and must not erase the original score, components, evidence or approval history.

## 6. Trigger and eligibility contract

### 6.1 Primary trigger — Unitalk proposal for approval

The normal A2 path begins when an A1 candidate has a recorded human decision approving it for enrichment and reaches the future durable state `approved_for_a2` in the selected review/staging layer.

The technical event, status field, webhook and staging application remain **integration pending**.

### 6.2 Manual trigger — pending decision

A future authorised user may be allowed to request enrichment for an existing HubSpot or staging record outside the standard A1 flow. This path remains disabled until Equinet confirms:

- eligible user roles;
- permitted record classes;
- required approval state;
- duplicate and exclusion checks;
- audit and cost attribution.

### 6.3 Minimum intake gate

A2 must reject or hold an intake when:

- A1 approval is absent or invalid;
- the input schema or identity cannot be validated;
- the candidate is rejected or excluded;
- a confirmed duplicate must be reconciled first;
- the record is a known customer, active opportunity, partner, distributor or opted-out contact and no approved exception applies;
- required source permissions are absent;
- the run would require an unapproved provider or spend;
- the audit correlation ID is missing.

Exact intake fields and state transitions will be defined in Step 1C and the canonical data contract.

## 7. Authoritative source and decision precedence

When values conflict, apply this precedence until a more detailed approved source hierarchy replaces it:

1. authoritative live source-system state; Equinet has confirmed that no separate first-party enrichment dataset is available;
2. manually entered HubSpot values and other protected fields;
3. information directly confirmed by an authorised Equinet reviewer;
4. explicit current facts published on the prospect's official business website;
5. approved verification or enrichment providers within their authorised field scope;
6. other approved public professional sources;
7. search results or directory seeds for discovery only, not retained proof unless their destination source is independently permitted and verified.

A higher-ranked source does not authorise automatic overwrite. Material conflicts and all protected-field differences require human review during the pilot.

Organisation memory may provide context but must not override authoritative source-system values.

## 8. Protected fields and conflict handling

### 8.1 Confirmed protected categories

The following must not be automatically overwritten:

- every manually entered HubSpot field;
- available email address;
- available telephone number;
- lifecycle or customer status;
- any additional field later designated as protected by Equinet.

### 8.2 Required comparison states

Every proposed field change must preserve at least:

- existing value;
- proposed value;
- source reference;
- retrieved or verified date;
- verification state;
- confidence level;
- protected-field indicator;
- conflict indicator and reason;
- recommended reviewer action;
- final human decision when recorded.

During the pilot, A2 prepares proposals only. It does not resolve material conflicts by writing over the existing value.

## 9. Evidence, verification and data-quality boundary

### 9.1 Confirmed principles

- Every enriched value must be traceable to its source where technically possible.
- Enrichment date and confidence must be recorded.
- Missing or unverifiable data must be flagged rather than invented.
- First-party and verified sources take priority.
- Critical conflicts require review.

### 9.2 Definitions pending Unitalk proposal and approval

Separate versioned policies must define:

- `Verified`;
- `High confidence`;
- `Medium confidence`;
- `Low confidence`;
- `Partial`;
- `Gap`;
- `Conflict`;
- field-level versus record-level confidence;
- acceptable proof for each field category;
- corroboration and source-independence requirements;
- freshness periods and re-verification triggers.

These definitions must not be embedded only in free-form prompts.

## 10. Privacy, consent and data minimisation

A2 may process only information necessary for approved prospect identification, qualification support, professional verification and business outreach preparation.

A2 must not:

- collect sensitive personal data unrelated to the approved purpose;
- infer protected or sensitive characteristics;
- treat public information as consent;
- infer opt-in, outreach eligibility or lawful basis;
- bypass login, access controls, CAPTCHA or source restrictions;
- use Mustad Data to train or fine-tune a model made available to third parties;
- send unapproved data to an unapproved provider or subprocessor.

Consent, opt-out, suppression and customer-status fields must be read from their authoritative system when the integration becomes available. Until then, outreach eligibility remains `unavailable` or `not_checked` and downstream outreach is blocked.

Retention and deletion rules remain **governance pending** until the applicable DPA and Equinet policy are confirmed.

## 11. Action and approval matrix

| Action | Foundation stage | Future no-integration pilot | Future integrated pilot |
|---|---|---|---|
| Inspect synthetic fixtures | Allowed for Unitalk validation | Allowed | Allowed |
| Research live public professional data | Prohibited | Allowed only under approved source policy and bounded pilot | Allowed under approved policy and permissions |
| Use paid enrichment or verification credits | Prohibited | Prohibited unless separately approved | Approval, account, scope and hard cost control required |
| Prepare proposed values | Draft design only | Allowed | Allowed |
| Approve an enriched record | Not available | Human reviewer only | Human reviewer only unless a later exception is approved |
| Write to HubSpot | Prohibited | Prohibited | Guarded action after recorded approval only |
| Change protected fields | Prohibited | Proposal and review only | Proposal and explicit field-level approval only |
| Directly overwrite or recalculate an approved A1 score | Prohibited | Prohibited; create a requalification signal | Prohibited; A1 creates a new deterministic score revision after review |
| Mark `Ready for Outreach` | Prohibited | Prohibited without authoritative eligibility checks | Only through an approved deterministic gate and human decision |
| Send outreach or enrol in a sequence | Prohibited | Prohibited | Outside A2 scope |
| Route to A3 or A14 | Prohibited | Structured draft handoff only; no delivery claim | After recorded eligibility and approval gates |

Default action mode is **DRAFT FOR APPROVAL**.

## 12. Target workflow

```text
Eligible A1 candidate approved for enrichment
→ validate handoff, identity, approval and audit references
→ read authorised existing values
→ run duplicate, exclusion and eligibility checks where available
→ create bounded enrichment plan
→ retrieve permitted enrichment data
→ normalise and validate proposed values
→ attach field-level sources, dates and confidence
→ compare with existing and protected values
→ flag gaps, conflicts, stale values and uncertain matches
→ generate review package
→ human approves, rejects or requests changes
→ if approved and integration active, execute guarded HubSpot patch
→ reconcile and audit the result
→ route eligible record to A3/A14 or return material qualification evidence to A1
```

If a required integration is unavailable, the workflow must stop at a validated review artifact or manual handoff. It must not claim that a downstream action occurred.

## 13. Inputs

### Required design-time inputs

- approved A1 Prospect Candidate contract and examples;
- Equinet A2 business blueprint and responses;
- approved organisational policies and contractual controls.

### Required run-time inputs for a future no-integration pilot

- schema-valid A1 candidate or explicitly approved manual fixture;
- recorded A1/reviewer decision;
- candidate and run identifiers;
- source evidence already collected by A1;
- requested enrichment scope;
- approved source policy and run limits;
- initiating actor and audit correlation ID.

### Required production inputs — integration pending

- authoritative HubSpot object/property mapping;
- current CRM record and associations;
- customer, opportunity, partner, distributor, consent and suppression states;
- staging/review work-item state;
- owner and territory context where authorised;
- provider permissions, scopes and budget state.

## 14. Outputs

A2 will ultimately produce:

1. a canonical A2 Enrichment Record;
2. a field-level current-versus-proposed comparison;
3. evidence and verification records;
4. gaps, conflicts, freshness and duplicate findings;
5. a record-level data-quality status;
6. a human review package with a pending decision;
7. an approved HubSpot patch payload when authorised;
8. a reconciliation and audit result after any write;
9. a structured `requalification_signal`, a later `requalification_return` payload to A1, and the resulting A1 score-revision reference when one is approved.

The canonical JSON record will be the lossless source. Markdown, CSV and Excel will be derived review views only.

## 15. Systems of record and supporting systems

| Information or state | Authority |
|---|---|
| Live prospect/customer/contact/company/Deal state | HubSpot |
| A1 ICP qualification, original score and later score revisions | Validated A1 output, A1 deterministic scoring and recorded human approval |
| A2 enrichment evidence and review work item | Future approved Unitalk/staging state; tool pending |
| Human approval | Recorded approval event in the approved review layer |
| Organisation context | Unitalk/Honcho, subject to source-system precedence |
| Workflow status, retries and correlation IDs | Future durable workflow/audit state orchestrated by n8n or approved equivalent |
| Provider credit and consumption state | Provider plus Unitalk consumption controls |

Twenty may be evaluated as the staging/review layer, but it is not confirmed and must not replace HubSpot as Equinet's customer-facing source of truth without an approved design.

## 16. Integration status

| Integration | Current state | Consequence |
|---|---|---|
| A1 durable handoff | Not connected | File-based or fixture-based testing only |
| HubSpot read | Not connected; object/property, lifecycle/pipeline, users/teams/owners and process snapshots received; live verification pending | Draft mapping and external-state design are possible, but no authoritative record checks can run |
| HubSpot write | Not connected and not authorised; workflow trigger/action dependencies are not verified | No CRM updates; every future mapped write requires dependency audit, approval and reconciliation controls |
| Twenty or alternative review staging | Not selected; no existing HubSpot enrichment-review asset identified | Review package must remain file/manual during early tests or use a separately approved review layer |
| n8n | Not connected | No triggers, waits, retries, routing or scheduled refresh |
| Paid enrichment provider | None approved or connected | No paid/deep enrichment |
| Email/phone verification provider | None approved or connected | Provider verification unavailable |
| LinkedIn Sales Navigator | No paid licence or approved integration | No automated access; mutual connections unavailable |
| HubSpot Breeze AI | Not confirmed as required or enabled | Must not be treated as a dependency |
| A3 and A14 handoffs | Not connected | No downstream delivery claim |

### 16.1 HubSpot object and governance confirmations

- Creator does not exist in HubSpot and is not required for A2.
- Campaign exists as a standard HubSpot object; Unitalk must not propose a duplicate Campaign custom object.
- Complaints and Sample Requests are confirmed custom objects.
- Existing Sample Request approval workflows do not constitute an A2 enrichment-review workflow.
- The named HubSpot technical and OAuth approvers route future configuration and connection decisions; they do not replace the A2 reviewer, approval matrix or production-acceptance authority.

## 17. Cost and consumption controls

- The Unitalk Gateway prepaid balance is the economic hard stop and must never become negative.
- No provider call or subscription spend is authorised until Mustad/Equinet approves the provider, account owner, permitted use and budget.
- Provider selection must compare coverage, precision, provenance, freshness, API rights, privacy, latency and cost for US Horse Owner and Farrier records.
- A2 must avoid recollecting valid A1 data.
- Every paid action must record provider, operation, units or credits, cost when available, candidate, run and approver.
- Retries must be bounded and duplicate paid calls prevented through idempotency controls.

## 18. Error, retry and fallback behaviour

A2 must:

- stop on invalid approval, blocked source, permission conflict, access barrier, unapproved spend or missing audit identity;
- hold possible duplicates for review;
- preserve the existing value when a proposal fails validation or conflicts with a protected field;
- represent unavailable, not checked, no match, possible match, confirmed duplicate and technical error as distinct states;
- use bounded retries only for approved transient failures;
- never rerun a paid operation automatically without idempotency protection;
- route repeated failures to an auditable manual queue;
- preserve valid partial artifacts and mark the run incomplete or blocked;
- fall back to a draft/manual review package when integrations are unavailable.
- block any proposed HubSpot write when the mapped property, list-membership effect or enabled workflow dependency has not been verified.

## 19. Audit requirements

For every future A2 run and external action, record where applicable:

- actor and profile;
- initiating user or workflow trigger;
- timestamp, run ID, candidate ID and correlation ID;
- A1 input reference and approval state;
- source URLs, provider record references and retrieval dates;
- existing values and proposed values;
- model and tools used;
- configuration, policy and schema versions;
- confidence, conflict, gap, duplicate and eligibility states;
- review decision, approver and timestamp;
- external action attempted or performed;
- success, failure, retry, blocked or reconciled state;
- token, API-call, credit and cost metadata when available.

Audit records must not claim an external action that cannot be verified.

## 20. Acceptance ladder

### Step 1B — Implementation Contract

This step passes only when:

- all required contract sections exist;
- confirmed facts, Unitalk proposals and missing decisions remain distinguishable;
- no unavailable integration is presented as active;
- the action matrix preserves human review and CRM-write restrictions;
- Séverine approves the implementation boundary for the next foundation step.

### Foundation and no-integration acceptance

Later gates must separately validate:

- A1-to-A2 handoff contract;
- canonical A2 schema and deterministic validators;
- source, evidence, verification, confidence, conflict and freshness policies;
- operational skills and scripts;
- profile-level behavioural compliance;
- synthetic and bounded real-data outputs;
- zero external writes or outreach;
- validated review exports and audit metadata;
- measured usage and unresolved limitations.

### Integrated pilot and production acceptance

Production requires, at minimum:

- approved HubSpot model and per-field mapping;
- verified granular read/write scopes;
- selected review/staging layer;
- confirmed approval matrix and backup owner;
- approved provider, data rights and budget controls;
- privacy, retention and administrator-visibility decisions;
- n8n trigger, idempotency, retries, dead-letter handling and monitoring;
- guarded HubSpot action with approval evidence;
- reconciliation, rollback and audit tests;
- representative integrated pilot results;
- recorded Equinet production approval.

Contractual acceptance remains separate from production approval.

## 21. Open items register

### Confirmed by Séverine for Step 1C

1. The primary trigger is a recorded human A1 decision leading to `approved_for_a2`.
2. A1 owns scoring. A2 preserves the original A1 score, may trigger requalification with verified new evidence, and never directly recalculates or silently overwrites the score. Any change is a new A1-generated, human-approved score revision.
3. Every enriched record requires human review during the pilot.
4. A2 cannot write to HubSpot or route to A3/A14 during the no-integration pilot.

### Required before the no-integration pilot

1. Final initial A2 field catalogue and minimum data packages for Horse Owners and Farriers.
2. Approved A2 source register and assisted-access methods.
3. Verification, confidence, data-quality and conflict definitions.
4. Exact protected-field policy beyond the currently confirmed categories.
5. Exact freshness periods and event-based re-verification triggers.
6. Named Unitalk reviewer and role-based Equinet reviewer process.
7. Bounded pilot volume, source-call limits and success measures.
8. Retention handling for rejected or incomplete pilot records.

### Required before integrated pilot or production

1. Complete the remaining HubSpot intake: association labels/cardinalities, exact relevant workflow criteria/actions and field dependencies, representative anonymised records, fill-rate/usage information where available, confirmed business-unit access boundary and read-only verification access.
2. Per-profile HubSpot read/write mapping.
3. Review/staging tool selection and state model.
4. Manual-trigger policy for existing records.
5. Provider selection, account ownership, data rights and approved budget.
6. A2 action-level approval matrix, named primary reviewer and backup. HubSpot technical, CRM, configuration and OAuth approvers are confirmed separately.
7. Owner and territory rules.
8. Consent, suppression and exclusion configuration.
9. n8n orchestration and guarded-action design.
10. A3 and A14 handoff contracts.
11. DPA, retention, deletion and administrator-visibility rules.
12. Measurable definitions for enrichment timeliness and verified-contact coverage.
13. Written delivery and acceptance evidence for the applicable contractual milestones.

## 22. Step 1B decision

**Decision:** `APPROVED AS DRAFTED`  
**Approver:** Séverine, Unitalk Operations  
**Decision timestamp:** `2026-08-16T15:43:31Z`

This approval means only:

- the mission, scope, action boundary, source-of-truth precedence and staged delivery approach may be used for Step 1C;
- decisions D1–D4 are approved;
- unresolved integration, provider, governance and production items remain open.

It does not approve the final A2 schema, source policy, confidence rules, skills, runtime, integrations, pilot, production use or contractual acceptance.

## 20. FullEnrich source-routing amendment — 2026-09-06

The approved new-source order is prospect official website, FullEnrich and then separately gated Apify/HarvestAPI. FullEnrich People Search is role- and exact-domain-bounded with a default result limit of one and a maximum of two unique returned/retained people per prospect. People Lookup is used only for a known person whose identity, organisation or current role still needs verification. Contact Enrichment runs only for selected contacts and requests work email and mobile phone; personal email is not requested. n8n is the approved target orchestrator but remains unconnected.
