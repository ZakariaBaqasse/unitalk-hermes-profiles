# Decision Review — Step 2B Field Dictionary and State Model

**Version:** `0.1.0`  
**Status:** `APPROVED BY UNITALK OPERATIONS FOR STEP 2C`  
**Profile status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`  
**Technical validation:** PASS  
**Human decision:** APPROVED AS DRAFTED  
**Approver:** Séverine, Unitalk Operations  
**Decision date:** `2026-08-25T22:20:22Z`

## 1. Technical result

| Check | Result |
|---|---:|
| Canonical sections | 14/14 PASS |
| Field paths | 216 unique paths PASS |
| State vocabularies | 37 PASS |
| Workflow states | 16 PASS |
| Cross-state safety rules | 12 PASS |
| Documentation checks | 6/6 PASS |
| Negative regressions | 9/9 PASS |
| Language audit | PASS |

The negative tests correctly reject:

- duplicate field paths;
- a missing canonical section;
- an unknown state vocabulary;
- duplicate state values;
- an invalid workflow transition;
- a mutable source handoff;
- a non-nullable future external reference;
- A2 as producer of a numeric score revision;
- removal of the no-integration sync restriction.

## 2. What the Field Dictionary defines

The dictionary defines 216 structural paths across:

- record metadata;
- immutable source handoff;
- subjects, entities and relationships;
- enrichment scope;
- generic field assessments;
- A2 evidence registry;
- record data quality;
- duplicate and eligibility checks;
- requalification and A1 score revisions;
- field-level and record-level review;
- A2 workflow;
- external-system references;
- governance;
- audit and consumption.

It deliberately does not yet define the business field catalogue such as email, service area, certification or horse count. Those business fields will use the generic `field_assessments[]` structure after Equinet confirms the relevant priorities.

## 3. Critical state distinctions

| State | Meaning |
|---|---|
| `unknown` | No reliable value is known after the applicable evaluation. Do not infer one. |
| `not_checked` | No attempt was made. |
| `unavailable` | The source, account, field or integration could not be used. |
| `not_found` | The check completed successfully and found no value. |
| `error` | The attempt failed technically. |
| `gap` | A required or requested field remains unsatisfied. |
| `conflict` | Material permitted values disagree and require resolution. |
| `stale` | The value exceeds its field-specific age or recheck rule. |

These states remain separate so missing data is never silently converted into a false value or invented fact.

## 4. Proposed A2 workflow states

```text
initialised
→ enrichment_planned
→ enrichment_in_progress
→ review_required
→ record_approved | changes_requested | held | blocked | record_rejected
→ ready_for_sync
→ sync_pending
→ synced | sync_failed
→ reconciled
→ closed
```

`processing_failed` is a controlled recovery state.

For `manual_no_integration_pilot`, the record may be reviewed and closed, but cannot enter:

```text
ready_for_sync
sync_pending
synced
reconciled
```

## 5. Ownership and action boundaries

- The accepted A1 handoff is immutable.
- A2 observations are append-only.
- A2 creates one proposed resolution per field/revision.
- A human controls field and record decisions.
- Approval does not prove that an external action occurred.
- Only a verified connector can record `applied` or `reconciled`.
- Future HubSpot/Twenty/n8n/provider IDs remain nullable.
- `null` never means that an external record was checked and absent.
- A1 remains the only producer of a numeric score revision.
- No HubSpot write can proceed while workflow dependencies are unverified.
- Missing owner rules produce `needs_owner_review`.

## 6. External HubSpot states

HubSpot states remain external mapping references and are not A2 workflow states:

- Lifecycle Stage;
- Lead Status;
- Deal Pipeline and Deal Stage;
- Company Account Status;
- Sample Request Pipeline and Approval Status;
- Ticket Pipeline.

Known limitations remain visible:

- Ticket stage `Rename 1` is unresolved;
- Account Status values `Block` and `Ship` lack approved A2 business meaning;
- no owner/backup assignment rules exist;
- no enrichment-review asset exists;
- workflow property/list dependencies remain unverified.

## 7. Decisions confirmed by Séverine

| ID | Approved decision |
|---|---|
| B1 | Keep `unknown`, `not_checked`, `unavailable`, `not_found`, `error`, `gap`, `conflict` and `stale` as distinct meanings. |
| B2 | Use separate orthogonal vocabularies for presence, availability, verification, confidence, freshness, conflict, quality, review and application instead of one overloaded status. |
| B3 | Approve the 14-section, 216-path structural field dictionary as the basis for Step 2D JSON Schema. |
| B4 | Keep baseline, observations, proposed resolution, human decision and application state separate for every field assessment. |
| B5 | Use `record_approved` and `record_rejected` as A2 workflow states to avoid ambiguity with HubSpot/Sample Request approval states. |
| B6 | Keep HubSpot Lifecycle, Lead, Deal, Ticket, Sample Request and Account Status values as external references only. |
| B7 | Use `needs_owner_review` when no approved owner rule resolves the owner, and block future writes while `workflow_dependency_status` is unverified. |
| B8 | Keep the no-integration ceiling: reviewed records cannot enter sync states. |
| B9 | Keep A2 requalification signals separate from A1-produced score revisions; A2 cannot create the numeric score. |
| B10 | Keep future external-system IDs nullable and connector-controlled; null never proves no external match. |

## 8. Deferred items

Approval of Step 2B does not approve:

- the business field catalogue;
- Farrier/Horse Owner Required/Optional/Do Not Collect decisions;
- minimum data packages;
- field-specific evidence, confidence or freshness thresholds;
- source activation or paid providers;
- HubSpot/Twenty mapping;
- live enrichment, CRM write, outreach, pilot or production use.

## 9. Recorded decision

**Approved as drafted.** B1–B10 are approved and Step 2C may begin.

This is not approval of the business field catalogue, sources, integrations, live enrichment, CRM write, outreach, pilot, production or contractual acceptance.
