# Decision Review — Step 2E Deterministic Cross-Field Validator

**Version:** `0.1.0`  
**Status:** `APPROVED BY UNITALK OPERATIONS FOR STEP 2F`  
**Profile status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`  
**Schema version tested:** `1.0.0-draft.2`  
**Technical validation:** PASS  
**Human decision:** APPROVED AS DRAFTED  
**Approver:** Séverine, Unitalk Operations  
**Decision timestamp:** `2026-08-26T10:00:06Z`

## 1. Technical result

| Check | Result |
|---|---:|
| Valid deterministic cases | 7/7 PASS |
| Negative deterministic cases | 52/52 PASS |
| Total cases | 59/59 PASS |
| Pinned validator dependencies | 15/15 PASS |
| External actions performed | 0 |

## 2. What is now validated

The validator runs after JSON Schema and verifies relationships that structural validation cannot prove alone:

- A1 handoff wrapper, embedded IDs and SHA-256 integrity;
- candidate, handoff, record, revision and audit-correlation links;
- synthetic-versus-real consistency;
- unique entities, relationships, assessments, observations and evidence;
- valid entity and relationship references;
- evidence references from observations, proposals and requalification signals;
- field proposal, review and application consistency;
- optional Field Catalogue key/type compatibility;
- data-quality list integrity;
- duplicate hold/block behaviour;
- requalification signal, return and A1 score-revision linkage;
- workflow transitions and prior-revision lineage;
- append-only evidence, requalification and audit history;
- manual no-integration ceilings;
- external-action approvals and usage totals.

## 3. Important boundaries

- The validator never researches or fills missing data.
- It never modifies an invalid record automatically.
- It never performs an external action.
- It never calculates an A1 score.
- The Business Field Catalogue remains external and optional until Step 3A.
- Field-specific evidence, confidence, freshness and protected-field policies remain separately versioned configurations.
- Step 2F remains responsible for the complete Farrier/Horse Owner business fixture matrix.

The review also includes the corrective schema revision `1.0.0-draft.2`, which allows a relationship-scoped field assessment to target an `A2-REL-*` identifier while preserving the approved `entity_id` property name for compatibility.

It also includes Step 2C lifecycle clarification `0.1.1`: a signal or return retains its creation-revision ID while only its approved lifecycle fields may advance in later A2 revisions.

## 4. Negative cases rejected

The suite rejects fifty-two controlled errors, including:

- mismatched handoff IDs or candidate hashes;
- incorrect system references;
- duplicate IDs and assessment targets;
- broken entity, relationship, evidence and data-quality references;
- non-reciprocal or source-blocked evidence use;
- unsupported add/update proposals;
- protected updates without approval;
- application before field and record approval;
- any attempt by A2 to authorise outreach;
- invalid workflow transitions;
- review/workflow disagreement;
- possible duplicates marked eligible;
- mismatched requalification identities and signal snapshots;
- score revisions referencing a missing return;
- score revisions linked to an unaccepted return or inconsistent A1 arithmetic;
- score revisions whose prior scoring does not match the immutable handoff or retained A1 revision;
- inconsistent usage totals;
- inconsistent event-level token arithmetic;
- unknown Field Catalogue keys or value types;
- mutation of append-only evidence history.

## 5. Decisions confirmed by Séverine

| ID | Decision |
|---|---|
| E1 | Run strict JSON Schema validation before any cross-field checks. |
| E2 | Require handoff, hash, candidate, system-reference and audit-correlation agreement. |
| E3 | Require unique identifiers across all repeatable canonical collections. |
| E4 | Require all cross-record evidence and entity references to resolve. |
| E5 | Enforce field baseline, observation, proposal, review and application consistency. |
| E6 | Validate the separate Field Catalogue only when it is supplied. |
| E7 | Enforce data-quality and duplicate/eligibility consistency. |
| E8 | Validate requalification linkage while preserving A1-only numeric scoring. |
| E9 | Require explicit human approval and write authority before application. |
| E10 | Validate state transitions, revision lineage and append-only history. |
| E11 | Enforce synthetic/real separation and no-integration ceilings. |
| E12 | Reconcile available audit usage and never repair or execute an invalid record. |
| E13 | Approve corrective schema `1.0.0-draft.2` and Step 2C lifecycle clarification `0.1.1`. |

## 6. Recorded decision

**Approved as drafted.** E1–E13 are approved and Step 2F may begin.

This approval is limited to the Step 2E deterministic validator and its two corrective clarifications. It does not approve source access, providers, A1/A2 integration, HubSpot/Twenty/n8n access, CRM writes, outreach, pilot, production or contractual acceptance.
