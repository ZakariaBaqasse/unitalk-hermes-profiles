# Equinet A2 Canonical State Model

**Version:** `0.1.0`  
**Status:** `APPROVED BY UNITALK OPERATIONS FOR STEP 2C`  
**Decision:** `APPROVED AS DRAFTED`  
**Approver:** Séverine, Unitalk Operations  
**Decision timestamp:** `2026-08-25T22:20:22Z`  
**Machine-readable vocabulary:** `contracts/a2-state-model-0.1.0.json`

## 1. Purpose

This model defines exact, non-interchangeable states for A2 data, review, workflow, eligibility, application and requalification. HubSpot Lifecycle, Lead, Deal and other portal states remain external mapping references and never become A2 workflow states.

## 2. Critical semantic distinctions

| State | Meaning |
|---|---|
| `unknown` | No reliable value is known after the applicable evaluation; do not infer one. |
| `not_checked` | No attempt has been made. |
| `unavailable` | The source, field, account or integration cannot be used in the current run. |
| `not_found` | A check completed successfully but found no value. |
| `error` | The check was attempted but failed technically. |
| `gap` | A required/requested field remains unsatisfied after applying the relevant rules. |
| `conflict` | Material permitted values disagree and require resolution. |
| `stale` | A value exceeds its field-specific age or recheck rule. |

These states must not be collapsed into a single blank or false value.

## 3. Canonical vocabularies

### `operating_scope`

**Owner:** Approved handoff/runtime policy

| Value | Meaning |
|---|---|
| `synthetic_test` | Synthetic fixtures and controlled contract tests only. |
| `manual_no_integration_pilot` | Controlled real-data pilot with no external delivery or write. |
| `integrated_pilot` | Approved connected pilot with scoped integrations and recorded approvals. |
| `production` | Approved operational scope; this value requires separate production acceptance. |

### `enrichment_mode`

**Owner:** Approved request and business field catalogue

| Value | Meaning |
|---|---|
| `default_minimum_package` | Apply the approved segment-specific minimum enrichment package. |
| `targeted_fields` | Assess only explicitly requested approved field keys. |

### `entity_type`

**Owner:** Canonical A2 entity model

| Value | Meaning |
|---|---|
| `person` | A professional individual. |
| `organisation` | A business, farm, stable, practice or other approved organisation. |

### `field_scope`

**Owner:** Business field catalogue

| Value | Meaning |
|---|---|
| `person` | Field belongs to a person entity. |
| `organisation` | Field belongs to an organisation entity. |
| `relationship` | Field belongs to an entity relationship. |
| `record` | Field applies to the A2 record as a whole. |

### `identity_resolution_status`

**Owner:** A2 entity resolver plus human review

| Value | Meaning |
|---|---|
| `unresolved` | The subject identity is not sufficiently resolved. |
| `possible_match` | A possible identity match requires human review. |
| `resolved` | The subject identity is resolved for the declared scope. |
| `conflict` | Material identity evidence conflicts. |
| `invalid` | The identity cannot be used under the approved minimum rules. |

### `entity_match_status`

**Owner:** Entity matcher/source system

| Value | Meaning |
|---|---|
| `not_checked` | No entity match check was attempted. |
| `unavailable` | The match source or integration is unavailable. |
| `no_match` | The match check completed and found no material match. |
| `possible_match` | A possible entity match requires review. |
| `confirmed_match` | A match is confirmed for the recorded system and scope. |
| `conflict` | The candidate match conflicts with material identity evidence. |
| `error` | The match check failed technically. |

### `evidence_namespace`

**Owner:** Canonical evidence model

| Value | Meaning |
|---|---|
| `a2` | Evidence collected natively by A2 under the A2 source register. |
| `a1_reference` | Reference to immutable A1 evidence; not relabelled as A2 evidence. |

### `reliability_level`

**Owner:** Approved A2 evidence policy

| Value | Meaning |
|---|---|
| `unassessed` | Evidence reliability has not been assessed. |
| `low` | Source or claim reliability is weak or materially limited. |
| `medium` | Source or claim is usable with stated limitations. |
| `high` | Source is strong for the specific claim under the approved policy. |

### `requalification_materiality`

**Owner:** A2 requalification policy

| Value | Meaning |
|---|---|
| `low` | New evidence is unlikely to alter qualification outcome but is retained. |
| `medium` | New evidence may alter a criterion or review outcome. |
| `high` | New evidence may alter exclusion, qualification, score band or routing. |

### `potential_score_direction`

**Owner:** A2 evidence interpretation only

| Value | Meaning |
|---|---|
| `increase` | Evidence may increase an A1 score after A1 validation. |
| `decrease` | Evidence may decrease an A1 score after A1 validation. |
| `unchanged` | Evidence is material but is not expected to change numeric score. |
| `unknown` | The score direction cannot be determined without A1 processing. |

### `record_kind`

**Owner:** Unitalk runtime

| Value | Meaning |
|---|---|
| `synthetic_test` | Explicitly synthetic fixture or controlled test record. |
| `production` | Record containing real authorised business data. This value does not mean production-ready deployment. |

### `value_presence_status`

**Owner:** Deterministic field validator

| Value | Meaning |
|---|---|
| `known` | A value is recorded with its provenance. |
| `unknown` | No reliable value is known after the applicable evaluation; no value may be inferred. |
| `not_applicable` | The field does not apply to this entity or segment. |

### `availability_status`

**Owner:** Tool, connector or deterministic controller

| Value | Meaning |
|---|---|
| `not_checked` | The applicable check has not been attempted. |
| `unavailable` | The source, integration, account or field is unavailable for the current run. |
| `not_found` | The check completed successfully and no value was found. |
| `available` | At least one candidate value or authoritative value is available. |
| `error` | The check was attempted but failed technically. |

### `verification_status`

**Owner:** Deterministic verification policy

| Value | Meaning |
|---|---|
| `unassessed` | Verification has not yet been evaluated. |
| `unverified` | A value exists but does not meet the approved verification rule. |
| `partially_verified` | Some but not all required proof conditions pass. |
| `verified` | The approved field-specific proof rule passes. |
| `contradicted` | Permitted evidence materially contradicts the value. |
| `not_applicable` | Verification is not applicable to this field state. |
| `error` | Verification failed technically. |

### `confidence_level`

**Owner:** Deterministic A2 confidence method

| Value | Meaning |
|---|---|
| `unassessed` | No confidence result has been calculated. |
| `low` | Evidence is weak, incomplete or materially uncertain. |
| `medium` | Evidence is usable but has limitations or incomplete corroboration. |
| `high` | Evidence meets the approved high-confidence rule. |

### `freshness_status`

**Owner:** Deterministic field freshness policy

| Value | Meaning |
|---|---|
| `unassessed` | Freshness has not been evaluated. |
| `current` | The value meets the approved field-specific freshness rule. |
| `stale` | The value exceeds its approved age or has a recheck trigger. |
| `undated` | The source is usable but no reliable source date is available. |
| `not_applicable` | Freshness does not apply to this field or source type. |
| `error` | Freshness evaluation failed technically. |

### `conflict_status`

**Owner:** Deterministic conflict policy and human review

| Value | Meaning |
|---|---|
| `unassessed` | Conflict comparison has not been performed. |
| `none` | No material conflict is present. |
| `possible` | Values may conflict and require further comparison. |
| `material` | A material conflict affects the proposed resolution or protected baseline. |
| `resolved` | A recorded human or authoritative-system decision resolved the conflict without deleting history. |

### `field_quality_status`

**Owner:** Deterministic data-quality controller

| Value | Meaning |
|---|---|
| `unassessed` | Field quality has not been evaluated. |
| `complete` | The approved field requirement is satisfied. |
| `partial` | Some usable data exists but the field requirement is not fully satisfied. |
| `gap` | A required or requested value remains missing, unavailable or not found. |
| `conflict` | An unresolved material conflict prevents completion. |
| `invalid` | The field fails type, policy, evidence or consistency validation. |
| `error` | The field could not be evaluated due to a technical error. |

### `protected_field_status`

**Owner:** Approved protected-field policy

| Value | Meaning |
|---|---|
| `unassessed` | Protected-field status has not been evaluated. |
| `not_protected` | The field is not protected by the active policy. |
| `protected_manual` | The baseline was manually entered and cannot be overwritten automatically. |
| `protected_policy` | The field is protected by Equinet/Unitalk policy. |
| `protected_authoritative` | The field is controlled by an authoritative source or read-only system field. |

### `proposal_action`

**Owner:** A2 proposal logic

| Value | Meaning |
|---|---|
| `add` | Propose a value where no usable baseline exists. |
| `update` | Propose replacing a baseline value after conflict/protection review. |
| `retain` | Recommend preserving the existing baseline value. |
| `no_change` | No change is required or proposed. |
| `hold` | Do not decide until a gap, conflict, permission or review issue is resolved. |
| `clear_request` | Request explicit human approval to clear a value; never an autonomous delete. |

### `field_review_decision`

**Owner:** Authorised human reviewer

| Value | Meaning |
|---|---|
| `pending` | No field decision has been recorded. |
| `approved` | The proposed field action is approved within the recorded scope. |
| `rejected` | The proposed field action is rejected. |
| `needs_changes` | The proposal requires correction or more evidence. |
| `held` | The reviewer defers the decision pending a named dependency. |
| `not_required` | A separate field-level decision is not required under the active policy. |

### `record_review_decision`

**Owner:** Authorised human reviewer

| Value | Meaning |
|---|---|
| `pending` | No record-level decision has been recorded. |
| `approved` | The record is approved for its next permitted stage, not automatically for outreach or write. |
| `rejected` | The record is rejected for the stated reason. |
| `needs_changes` | The record requires correction or more evidence. |
| `held` | The record is held pending a named dependency. |
| `blocked` | Policy, duplicate, permission or authoritative status prevents progression. |

### `application_status`

**Owner:** Authorised connector/workflow

| Value | Meaning |
|---|---|
| `not_requested` | No application or external write was requested. |
| `unavailable` | The destination integration is unavailable. |
| `pending` | An approved application request exists but has not completed. |
| `applied` | The approved action was performed and has an external reference. |
| `failed` | The external action failed. |
| `reconciled` | The applied result was read back and matched the approved action. |
| `blocked` | The action is blocked by approval, permission, protected-field or workflow-dependency controls. |

### `workflow_dependency_status`

**Owner:** HubSpot mapping/dependency audit

| Value | Meaning |
|---|---|
| `not_checked` | Workflow/list/form dependencies have not been audited. |
| `unverified` | A dependency is suspected or known but not fully verified. |
| `verified_no_side_effect` | The mapped change has no unmanaged workflow/list side effect. |
| `verified_managed_side_effect` | The side effect is documented, approved and controlled. |
| `blocked` | An unmanaged or prohibited side effect blocks the action. |
| `error` | Dependency verification failed technically. |

### `data_quality_status`

**Owner:** Deterministic A2 data-quality method

| Value | Meaning |
|---|---|
| `unassessed` | Record quality has not been calculated. |
| `incomplete` | The applicable minimum package is not satisfied. |
| `review_ready` | The no-integration review package is complete enough for human review. |
| `needs_review` | Gaps or limitations require explicit human attention. |
| `conflict` | An unresolved material conflict prevents approval. |
| `invalid` | The record fails schema, policy or consistency validation. |
| `error` | Quality calculation failed technically. |

### `duplicate_status`

**Owner:** Duplicate-check controller/source system

| Value | Meaning |
|---|---|
| `unavailable` | The duplicate source or integration is unavailable. |
| `not_checked` | The duplicate check has not run. |
| `no_match` | The check ran and found no material match. |
| `possible_match` | A possible match requires human review. |
| `confirmed_duplicate` | A confirmed duplicate blocks treatment as a new record. |
| `error` | The duplicate check failed technically. |

### `eligibility_status`

**Owner:** Deterministic eligibility controller plus authoritative sources

| Value | Meaning |
|---|---|
| `not_checked` | Eligibility has not been evaluated. |
| `unavailable` | Required authoritative checks are unavailable. |
| `eligible` | All gates for the declared scope pass. |
| `hold` | A resolvable review or authoritative check is pending. |
| `blocked` | A confirmed exclusion, duplicate, permission or policy gate prevents progression. |
| `error` | Eligibility evaluation failed technically. |

### `outreach_eligibility_status`

**Owner:** HubSpot authoritative checks plus approved policy and human decision

| Value | Meaning |
|---|---|
| `not_checked` | Outreach eligibility has not been evaluated. |
| `unavailable` | CRM consent/customer/Deal/sequence checks are unavailable. |
| `eligible_for_review` | Checks support human outreach-eligibility review; this is not permission to send. |
| `approved` | An authorised human approved outreach eligibility for the recorded scope. |
| `hold` | A consent, customer, Deal, sequence or ownership issue remains unresolved. |
| `blocked` | A confirmed rule prohibits outreach. |
| `error` | Eligibility evaluation failed technically. |

### `owner_routing_status`

**Owner:** Authoritative CRM plus approved assignment policy

| Value | Meaning |
|---|---|
| `not_checked` | Owner routing has not been evaluated. |
| `current_owner_preserved` | The existing valid HubSpot owner is preserved. |
| `needs_owner_review` | No approved deterministic owner/backup rule can resolve the owner. |
| `approved_reassignment` | An authorised human approved reassignment under a recorded rule. |
| `unavailable` | Owner information or integration is unavailable. |
| `error` | Owner routing failed technically. |

### `workflow_state`

**Owner:** A2 workflow/application layer

| Value | Meaning |
|---|---|
| `initialised` | A valid handoff created the first A2 revision. |
| `enrichment_planned` | A bounded field-gap plan is validated. |
| `enrichment_in_progress` | Permitted enrichment work is in progress. |
| `review_required` | A review package is complete and awaiting human decision. |
| `record_approved` | The A2 record is human-approved for its next permitted stage. |
| `changes_requested` | The reviewer requested correction or additional evidence. |
| `held` | A named dependency temporarily prevents progression. |
| `blocked` | A policy, duplicate, permission or authoritative state blocks progression. |
| `record_rejected` | The record is rejected. |
| `processing_failed` | A processing stage failed and requires controlled recovery. |
| `ready_for_sync` | The approved record is eligible for a separately authorised sync. |
| `sync_pending` | A guarded sync is in progress. |
| `synced` | The approved patch was written and an external reference exists. |
| `sync_failed` | The guarded sync failed. |
| `reconciled` | The external write was read back and matched. |
| `closed` | The lineage is closed for the stated reason. |

### `requalification_signal_status`

**Owner:** A2 plus authorised reviewer

| Value | Meaning |
|---|---|
| `draft` | A2 created a signal that has not been reviewed. |
| `pending_review` | The signal awaits human review. |
| `approved_for_return` | The signal is approved for a return payload to A1. |
| `rejected` | The signal was rejected. |
| `sent_to_a1` | A durable return was delivered to A1. |
| `accepted_by_a1` | A1 accepted the return for evidence/scoring review. |
| `rejected_by_a1` | A1 rejected the return with reasons. |
| `rescored` | A1 produced a score-revision result. |
| `error` | The requalification process failed technically. |

### `requalification_return_status`

**Owner:** Workflow/A1 receipt

| Value | Meaning |
|---|---|
| `not_created` | No return payload exists. |
| `prepared` | The return payload exists but is not delivered. |
| `delivered` | The durable workflow delivered the return. |
| `accepted_by_a1` | A1 accepted the exact payload. |
| `rejected_by_a1` | A1 rejected the payload. |
| `delivery_failed` | Delivery failed after bounded retries. |
| `error` | Return processing failed technically. |

### `score_revision_status`

**Owner:** A1 deterministic scoring plus human approval

| Value | Meaning |
|---|---|
| `not_requested` | No A1 score revision was requested. |
| `pending_a1_review` | A1 is validating returned evidence. |
| `proposed_by_a1` | A1 produced a deterministic proposed revision. |
| `approved` | An authorised human approved the revision. |
| `rejected` | The proposed revision was rejected. |
| `superseded` | A later approved revision supersedes this revision. |
| `error` | The revision process failed technically. |

### `integration_status`

**Owner:** Connector/runtime configuration

| Value | Meaning |
|---|---|
| `not_checked` | Integration readiness was not checked for the current run. |
| `unavailable` | No approved active connection is available. |
| `connected_read_only` | A verified least-privilege read connection is active. |
| `connected_guarded_write` | A verified guarded write connection is active for approved actions only. |
| `error` | The integration check failed technically. |

### `source_policy_status`

**Owner:** A2 source register

| Value | Meaning |
|---|---|
| `approved` | Permitted under the exact recorded A2 access profile. |
| `conditional` | Permitted only under recorded conditions. |
| `needs_verification` | Do not retain as evidence until the source decision is resolved. |
| `blocked` | Do not use for A2 collection or evidence. |
| `unavailable` | Required source/account/licence is unavailable. |

### `claim_type`

**Owner:** Evidence collector and validator

| Value | Meaning |
|---|---|
| `direct_fact` | The source explicitly states the value or claim. |
| `reasonable_inference` | The claim is an interpretation supported by evidence but not directly stated. |
| `contradictory_evidence` | The source materially contradicts another value or claim. |

### `change_reason`

**Owner:** Revision builder

| Value | Meaning |
|---|---|
| `initialisation` | First A2 revision from an accepted handoff. |
| `enrichment` | New permitted observations or evidence were added. |
| `correction` | A correction was recorded without erasing history. |
| `human_review` | A human decision created a new revision. |
| `requalification_result` | An A1 requalification result was recorded. |
| `refresh` | Freshness-triggered re-evaluation created a revision. |
| `reconciliation` | An external action was read back and reconciled. |

## 4. A2 workflow transitions

| From | Allowed next states |
|---|---|
| `initialised` | `enrichment_planned`, `held`, `blocked`, `record_rejected` |
| `enrichment_planned` | `enrichment_in_progress`, `held`, `blocked`, `processing_failed` |
| `enrichment_in_progress` | `review_required`, `held`, `blocked`, `processing_failed` |
| `review_required` | `record_approved`, `changes_requested`, `held`, `blocked`, `record_rejected` |
| `changes_requested` | `enrichment_planned`, `enrichment_in_progress`, `review_required`, `held`, `blocked` |
| `record_approved` | `ready_for_sync`, `closed` |
| `held` | `enrichment_planned`, `enrichment_in_progress`, `review_required`, `blocked`, `record_rejected` |
| `processing_failed` | `enrichment_planned`, `held`, `blocked` |
| `ready_for_sync` | `sync_pending`, `held`, `blocked` |
| `sync_pending` | `synced`, `sync_failed` |
| `sync_failed` | `sync_pending`, `held`, `blocked` |
| `synced` | `reconciled`, `sync_failed` |
| `reconciled` | `closed` |
| `blocked` | Terminal |
| `record_rejected` | Terminal |
| `closed` | Terminal |

### No-integration ceiling

A `manual_no_integration_pilot` record may be human-approved and closed for review purposes, but it cannot enter `ready_for_sync`, `sync_pending`, `synced` or `reconciled`.

## 5. External HubSpot state references

The following are external source-system states, not canonical A2 workflow states:

- HubSpot Lifecycle Stage;
- HubSpot Lead Status;
- Deal Pipeline and Deal Stage;
- Company Account Status;
- Sample Request Pipeline and Approval Status;
- Ticket Pipeline.

Known limitations:

- `Rename 1` is an unresolved Ticket-stage placeholder.
- Company Account Status values `Block` and `Ship` lack approved A2 business meaning.
- owner-assignment and backup-owner rules are unavailable.
- no HubSpot enrichment-review asset exists.
- workflow field/list dependencies remain unverified.

## 6. Cross-state rules

- unknown means no reliable value is known; it must never be replaced by an inference.
- not_checked means no attempt occurred; unavailable means the source or integration could not be used; not_found means a successful check found no value; error means the attempt failed technically.
- verified requires evidence references and an approved field-specific verification rule.
- field review approval does not imply application or external write.
- application applied requires an external action reference; reconciled requires a read-back result.
- protected manual, policy and authoritative fields cannot be applied automatically.
- workflow_dependency_status must be verified_no_side_effect or verified_managed_side_effect before any HubSpot write can be applied.
- manual_no_integration_pilot records cannot enter ready_for_sync, sync_pending, synced or reconciled.
- outreach eligibility approved requires authoritative CRM checks and recorded human approval; public information never creates consent.
- A2 may create requalification signals but cannot set score_revision_status to proposed_by_a1 or approved without an A1 result reference.
- null external-system IDs do not imply no external record exists; an explicit check status is required.
- owner routing defaults to needs_owner_review when no approved assignment rule resolves the owner.

## 7. Step 2B approval boundary

Approval of these vocabularies authorises their use in Step 2C and Step 2D. It does not approve field-specific business rules, confidence thresholds, source activation, HubSpot mapping, external actions, pilot or production use.
