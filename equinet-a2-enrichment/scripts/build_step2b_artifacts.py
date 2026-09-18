#!/usr/bin/env python3
"""Build Step 2B field dictionary and state-model artifacts for Equinet A2."""

from __future__ import annotations

import csv
import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
FOUNDATIONS = PROFILE_ROOT / "foundations"
CONTRACTS = FOUNDATIONS / "contracts"
FIELD_DICTIONARY = CONTRACTS / "a2-field-dictionary-0.1.0.csv"
STATE_MODEL = CONTRACTS / "a2-state-model-0.1.0.json"
HUBSPOT_MANIFEST = FOUNDATIONS / "hubspot" / "HUBSPOT-OPERATIONAL-METADATA-MANIFEST.json"

FIELD_COLUMNS = [
    "section",
    "field_path",
    "data_type",
    "required",
    "nullable",
    "cardinality",
    "producer",
    "authority",
    "mutability",
    "state_vocabulary",
    "description",
    "conditions",
]


def state(value: str, meaning: str) -> dict:
    return {"value": value, "meaning": meaning}


def build_state_model() -> dict:
    hubspot = json.loads(HUBSPOT_MANIFEST.read_text(encoding="utf-8"))
    vocabularies = {
        "operating_scope": {
            "owner": "Approved handoff/runtime policy",
            "values": [
                state("synthetic_test", "Synthetic fixtures and controlled contract tests only."),
                state("manual_no_integration_pilot", "Controlled real-data pilot with no external delivery or write."),
                state("integrated_pilot", "Approved connected pilot with scoped integrations and recorded approvals."),
                state("production", "Approved operational scope; this value requires separate production acceptance."),
            ],
        },
        "enrichment_mode": {
            "owner": "Approved request and business field catalogue",
            "values": [
                state("default_minimum_package", "Apply the approved segment-specific minimum enrichment package."),
                state("targeted_fields", "Assess only explicitly requested approved field keys."),
            ],
        },
        "entity_type": {
            "owner": "Canonical A2 entity model",
            "values": [
                state("person", "A professional individual."),
                state("organisation", "A business, farm, stable, practice or other approved organisation."),
            ],
        },
        "field_scope": {
            "owner": "Business field catalogue",
            "values": [
                state("person", "Field belongs to a person entity."),
                state("organisation", "Field belongs to an organisation entity."),
                state("relationship", "Field belongs to an entity relationship."),
                state("record", "Field applies to the A2 record as a whole."),
            ],
        },
        "identity_resolution_status": {
            "owner": "A2 entity resolver plus human review",
            "values": [
                state("unresolved", "The subject identity is not sufficiently resolved."),
                state("possible_match", "A possible identity match requires human review."),
                state("resolved", "The subject identity is resolved for the declared scope."),
                state("conflict", "Material identity evidence conflicts."),
                state("invalid", "The identity cannot be used under the approved minimum rules."),
            ],
        },
        "entity_match_status": {
            "owner": "Entity matcher/source system",
            "values": [
                state("not_checked", "No entity match check was attempted."),
                state("unavailable", "The match source or integration is unavailable."),
                state("no_match", "The match check completed and found no material match."),
                state("possible_match", "A possible entity match requires review."),
                state("confirmed_match", "A match is confirmed for the recorded system and scope."),
                state("conflict", "The candidate match conflicts with material identity evidence."),
                state("error", "The match check failed technically."),
            ],
        },
        "evidence_namespace": {
            "owner": "Canonical evidence model",
            "values": [
                state("a2", "Evidence collected natively by A2 under the A2 source register."),
                state("a1_reference", "Reference to immutable A1 evidence; not relabelled as A2 evidence."),
            ],
        },
        "reliability_level": {
            "owner": "Approved A2 evidence policy",
            "values": [
                state("unassessed", "Evidence reliability has not been assessed."),
                state("low", "Source or claim reliability is weak or materially limited."),
                state("medium", "Source or claim is usable with stated limitations."),
                state("high", "Source is strong for the specific claim under the approved policy."),
            ],
        },
        "requalification_materiality": {
            "owner": "A2 requalification policy",
            "values": [
                state("low", "New evidence is unlikely to alter qualification outcome but is retained."),
                state("medium", "New evidence may alter a criterion or review outcome."),
                state("high", "New evidence may alter exclusion, qualification, score band or routing."),
            ],
        },
        "potential_score_direction": {
            "owner": "A2 evidence interpretation only",
            "values": [
                state("increase", "Evidence may increase an A1 score after A1 validation."),
                state("decrease", "Evidence may decrease an A1 score after A1 validation."),
                state("unchanged", "Evidence is material but is not expected to change numeric score."),
                state("unknown", "The score direction cannot be determined without A1 processing."),
            ],
        },
        "record_kind": {
            "owner": "Unitalk runtime",
            "values": [
                state("synthetic_test", "Explicitly synthetic fixture or controlled test record."),
                state("production", "Record containing real authorised business data. This value does not mean production-ready deployment."),
            ],
        },
        "value_presence_status": {
            "owner": "Deterministic field validator",
            "values": [
                state("known", "A value is recorded with its provenance."),
                state("unknown", "No reliable value is known after the applicable evaluation; no value may be inferred."),
                state("not_applicable", "The field does not apply to this entity or segment."),
            ],
        },
        "availability_status": {
            "owner": "Tool, connector or deterministic controller",
            "values": [
                state("not_checked", "The applicable check has not been attempted."),
                state("unavailable", "The source, integration, account or field is unavailable for the current run."),
                state("not_found", "The check completed successfully and no value was found."),
                state("available", "At least one candidate value or authoritative value is available."),
                state("error", "The check was attempted but failed technically."),
            ],
        },
        "verification_status": {
            "owner": "Deterministic verification policy",
            "values": [
                state("unassessed", "Verification has not yet been evaluated."),
                state("unverified", "A value exists but does not meet the approved verification rule."),
                state("partially_verified", "Some but not all required proof conditions pass."),
                state("verified", "The approved field-specific proof rule passes."),
                state("contradicted", "Permitted evidence materially contradicts the value."),
                state("not_applicable", "Verification is not applicable to this field state."),
                state("error", "Verification failed technically."),
            ],
        },
        "confidence_level": {
            "owner": "Deterministic A2 confidence method",
            "values": [
                state("unassessed", "No confidence result has been calculated."),
                state("low", "Evidence is weak, incomplete or materially uncertain."),
                state("medium", "Evidence is usable but has limitations or incomplete corroboration."),
                state("high", "Evidence meets the approved high-confidence rule."),
            ],
        },
        "freshness_status": {
            "owner": "Deterministic field freshness policy",
            "values": [
                state("unassessed", "Freshness has not been evaluated."),
                state("current", "The value meets the approved field-specific freshness rule."),
                state("stale", "The value exceeds its approved age or has a recheck trigger."),
                state("undated", "The source is usable but no reliable source date is available."),
                state("not_applicable", "Freshness does not apply to this field or source type."),
                state("error", "Freshness evaluation failed technically."),
            ],
        },
        "conflict_status": {
            "owner": "Deterministic conflict policy and human review",
            "values": [
                state("unassessed", "Conflict comparison has not been performed."),
                state("none", "No material conflict is present."),
                state("possible", "Values may conflict and require further comparison."),
                state("material", "A material conflict affects the proposed resolution or protected baseline."),
                state("resolved", "A recorded human or authoritative-system decision resolved the conflict without deleting history."),
            ],
        },
        "field_quality_status": {
            "owner": "Deterministic data-quality controller",
            "values": [
                state("unassessed", "Field quality has not been evaluated."),
                state("complete", "The approved field requirement is satisfied."),
                state("partial", "Some usable data exists but the field requirement is not fully satisfied."),
                state("gap", "A required or requested value remains missing, unavailable or not found."),
                state("conflict", "An unresolved material conflict prevents completion."),
                state("invalid", "The field fails type, policy, evidence or consistency validation."),
                state("error", "The field could not be evaluated due to a technical error."),
            ],
        },
        "protected_field_status": {
            "owner": "Approved protected-field policy",
            "values": [
                state("unassessed", "Protected-field status has not been evaluated."),
                state("not_protected", "The field is not protected by the active policy."),
                state("protected_manual", "The baseline was manually entered and cannot be overwritten automatically."),
                state("protected_policy", "The field is protected by Equinet/Unitalk policy."),
                state("protected_authoritative", "The field is controlled by an authoritative source or read-only system field."),
            ],
        },
        "proposal_action": {
            "owner": "A2 proposal logic",
            "values": [
                state("add", "Propose a value where no usable baseline exists."),
                state("update", "Propose replacing a baseline value after conflict/protection review."),
                state("retain", "Recommend preserving the existing baseline value."),
                state("no_change", "No change is required or proposed."),
                state("hold", "Do not decide until a gap, conflict, permission or review issue is resolved."),
                state("clear_request", "Request explicit human approval to clear a value; never an autonomous delete."),
            ],
        },
        "field_review_decision": {
            "owner": "Authorised human reviewer",
            "values": [
                state("pending", "No field decision has been recorded."),
                state("approved", "The proposed field action is approved within the recorded scope."),
                state("rejected", "The proposed field action is rejected."),
                state("needs_changes", "The proposal requires correction or more evidence."),
                state("held", "The reviewer defers the decision pending a named dependency."),
                state("not_required", "A separate field-level decision is not required under the active policy."),
            ],
        },
        "record_review_decision": {
            "owner": "Authorised human reviewer",
            "values": [
                state("pending", "No record-level decision has been recorded."),
                state("approved", "The record is approved for its next permitted stage, not automatically for outreach or write."),
                state("rejected", "The record is rejected for the stated reason."),
                state("needs_changes", "The record requires correction or more evidence."),
                state("held", "The record is held pending a named dependency."),
                state("blocked", "Policy, duplicate, permission or authoritative status prevents progression."),
            ],
        },
        "application_status": {
            "owner": "Authorised connector/workflow",
            "values": [
                state("not_requested", "No application or external write was requested."),
                state("unavailable", "The destination integration is unavailable."),
                state("pending", "An approved application request exists but has not completed."),
                state("applied", "The approved action was performed and has an external reference."),
                state("failed", "The external action failed."),
                state("reconciled", "The applied result was read back and matched the approved action."),
                state("blocked", "The action is blocked by approval, permission, protected-field or workflow-dependency controls."),
            ],
        },
        "workflow_dependency_status": {
            "owner": "HubSpot mapping/dependency audit",
            "values": [
                state("not_checked", "Workflow/list/form dependencies have not been audited."),
                state("unverified", "A dependency is suspected or known but not fully verified."),
                state("verified_no_side_effect", "The mapped change has no unmanaged workflow/list side effect."),
                state("verified_managed_side_effect", "The side effect is documented, approved and controlled."),
                state("blocked", "An unmanaged or prohibited side effect blocks the action."),
                state("error", "Dependency verification failed technically."),
            ],
        },
        "data_quality_status": {
            "owner": "Deterministic A2 data-quality method",
            "values": [
                state("unassessed", "Record quality has not been calculated."),
                state("incomplete", "The applicable minimum package is not satisfied."),
                state("review_ready", "The no-integration review package is complete enough for human review."),
                state("needs_review", "Gaps or limitations require explicit human attention."),
                state("conflict", "An unresolved material conflict prevents approval."),
                state("invalid", "The record fails schema, policy or consistency validation."),
                state("error", "Quality calculation failed technically."),
            ],
        },
        "duplicate_status": {
            "owner": "Duplicate-check controller/source system",
            "values": [
                state("unavailable", "The duplicate source or integration is unavailable."),
                state("not_checked", "The duplicate check has not run."),
                state("no_match", "The check ran and found no material match."),
                state("possible_match", "A possible match requires human review."),
                state("confirmed_duplicate", "A confirmed duplicate blocks treatment as a new record."),
                state("error", "The duplicate check failed technically."),
            ],
        },
        "eligibility_status": {
            "owner": "Deterministic eligibility controller plus authoritative sources",
            "values": [
                state("not_checked", "Eligibility has not been evaluated."),
                state("unavailable", "Required authoritative checks are unavailable."),
                state("eligible", "All gates for the declared scope pass."),
                state("hold", "A resolvable review or authoritative check is pending."),
                state("blocked", "A confirmed exclusion, duplicate, permission or policy gate prevents progression."),
                state("error", "Eligibility evaluation failed technically."),
            ],
        },
        "outreach_eligibility_status": {
            "owner": "HubSpot authoritative checks plus approved policy and human decision",
            "values": [
                state("not_checked", "Outreach eligibility has not been evaluated."),
                state("unavailable", "CRM consent/customer/Deal/sequence checks are unavailable."),
                state("eligible_for_review", "Checks support human outreach-eligibility review; this is not permission to send."),
                state("approved", "An authorised human approved outreach eligibility for the recorded scope."),
                state("hold", "A consent, customer, Deal, sequence or ownership issue remains unresolved."),
                state("blocked", "A confirmed rule prohibits outreach."),
                state("error", "Eligibility evaluation failed technically."),
            ],
        },
        "owner_routing_status": {
            "owner": "Authoritative CRM plus approved assignment policy",
            "values": [
                state("not_checked", "Owner routing has not been evaluated."),
                state("current_owner_preserved", "The existing valid HubSpot owner is preserved."),
                state("needs_owner_review", "No approved deterministic owner/backup rule can resolve the owner."),
                state("approved_reassignment", "An authorised human approved reassignment under a recorded rule."),
                state("unavailable", "Owner information or integration is unavailable."),
                state("error", "Owner routing failed technically."),
            ],
        },
        "workflow_state": {
            "owner": "A2 workflow/application layer",
            "values": [
                state("initialised", "A valid handoff created the first A2 revision."),
                state("enrichment_planned", "A bounded field-gap plan is validated."),
                state("enrichment_in_progress", "Permitted enrichment work is in progress."),
                state("review_required", "A review package is complete and awaiting human decision."),
                state("record_approved", "The A2 record is human-approved for its next permitted stage."),
                state("changes_requested", "The reviewer requested correction or additional evidence."),
                state("held", "A named dependency temporarily prevents progression."),
                state("blocked", "A policy, duplicate, permission or authoritative state blocks progression."),
                state("record_rejected", "The record is rejected."),
                state("processing_failed", "A processing stage failed and requires controlled recovery."),
                state("ready_for_sync", "The approved record is eligible for a separately authorised sync."),
                state("sync_pending", "A guarded sync is in progress."),
                state("synced", "The approved patch was written and an external reference exists."),
                state("sync_failed", "The guarded sync failed."),
                state("reconciled", "The external write was read back and matched."),
                state("closed", "The lineage is closed for the stated reason."),
            ],
        },
        "requalification_signal_status": {
            "owner": "A2 plus authorised reviewer",
            "values": [
                state("draft", "A2 created a signal that has not been reviewed."),
                state("pending_review", "The signal awaits human review."),
                state("approved_for_return", "The signal is approved for a return payload to A1."),
                state("rejected", "The signal was rejected."),
                state("sent_to_a1", "A durable return was delivered to A1."),
                state("accepted_by_a1", "A1 accepted the return for evidence/scoring review."),
                state("rejected_by_a1", "A1 rejected the return with reasons."),
                state("rescored", "A1 produced a score-revision result."),
                state("error", "The requalification process failed technically."),
            ],
        },
        "requalification_return_status": {
            "owner": "Workflow/A1 receipt",
            "values": [
                state("not_created", "No return payload exists."),
                state("prepared", "The return payload exists but is not delivered."),
                state("delivered", "The durable workflow delivered the return."),
                state("accepted_by_a1", "A1 accepted the exact payload."),
                state("rejected_by_a1", "A1 rejected the payload."),
                state("delivery_failed", "Delivery failed after bounded retries."),
                state("error", "Return processing failed technically."),
            ],
        },
        "score_revision_status": {
            "owner": "A1 deterministic scoring plus human approval",
            "values": [
                state("not_requested", "No A1 score revision was requested."),
                state("pending_a1_review", "A1 is validating returned evidence."),
                state("proposed_by_a1", "A1 produced a deterministic proposed revision."),
                state("approved", "An authorised human approved the revision."),
                state("rejected", "The proposed revision was rejected."),
                state("superseded", "A later approved revision supersedes this revision."),
                state("error", "The revision process failed technically."),
            ],
        },
        "integration_status": {
            "owner": "Connector/runtime configuration",
            "values": [
                state("not_checked", "Integration readiness was not checked for the current run."),
                state("unavailable", "No approved active connection is available."),
                state("connected_read_only", "A verified least-privilege read connection is active."),
                state("connected_guarded_write", "A verified guarded write connection is active for approved actions only."),
                state("error", "The integration check failed technically."),
            ],
        },
        "source_policy_status": {
            "owner": "A2 source register",
            "values": [
                state("approved", "Permitted under the exact recorded A2 access profile."),
                state("conditional", "Permitted only under recorded conditions."),
                state("needs_verification", "Do not retain as evidence until the source decision is resolved."),
                state("blocked", "Do not use for A2 collection or evidence."),
                state("unavailable", "Required source/account/licence is unavailable."),
            ],
        },
        "claim_type": {
            "owner": "Evidence collector and validator",
            "values": [
                state("direct_fact", "The source explicitly states the value or claim."),
                state("reasonable_inference", "The claim is an interpretation supported by evidence but not directly stated."),
                state("contradictory_evidence", "The source materially contradicts another value or claim."),
            ],
        },
        "change_reason": {
            "owner": "Revision builder",
            "values": [
                state("initialisation", "First A2 revision from an accepted handoff."),
                state("enrichment", "New permitted observations or evidence were added."),
                state("correction", "A correction was recorded without erasing history."),
                state("human_review", "A human decision created a new revision."),
                state("requalification_result", "An A1 requalification result was recorded."),
                state("refresh", "Freshness-triggered re-evaluation created a revision."),
                state("reconciliation", "An external action was read back and reconciled."),
            ],
        },
    }

    workflow_transitions = {
        "initialised": ["enrichment_planned", "held", "blocked", "record_rejected"],
        "enrichment_planned": ["enrichment_in_progress", "held", "blocked", "processing_failed"],
        "enrichment_in_progress": ["review_required", "held", "blocked", "processing_failed"],
        "review_required": ["record_approved", "changes_requested", "held", "blocked", "record_rejected"],
        "changes_requested": ["enrichment_planned", "enrichment_in_progress", "review_required", "held", "blocked"],
        "record_approved": ["ready_for_sync", "closed"],
        "held": ["enrichment_planned", "enrichment_in_progress", "review_required", "blocked", "record_rejected"],
        "processing_failed": ["enrichment_planned", "held", "blocked"],
        "ready_for_sync": ["sync_pending", "held", "blocked"],
        "sync_pending": ["synced", "sync_failed"],
        "sync_failed": ["sync_pending", "held", "blocked"],
        "synced": ["reconciled", "sync_failed"],
        "reconciled": ["closed"],
        "blocked": [],
        "record_rejected": [],
        "closed": [],
    }

    return {
        "state_model_id": "equinet-a2-state-model",
        "version": "0.1.0",
        "status": "approved_by_unitalk_for_step_2c",
        "canonical_vocabularies": vocabularies,
        "transition_models": {
            "workflow_state": workflow_transitions,
        },
        "cross_state_rules": [
            "unknown means no reliable value is known; it must never be replaced by an inference.",
            "not_checked means no attempt occurred; unavailable means the source or integration could not be used; not_found means a successful check found no value; error means the attempt failed technically.",
            "verified requires evidence references and an approved field-specific verification rule.",
            "field review approval does not imply application or external write.",
            "application applied requires an external action reference; reconciled requires a read-back result.",
            "protected manual, policy and authoritative fields cannot be applied automatically.",
            "workflow_dependency_status must be verified_no_side_effect or verified_managed_side_effect before any HubSpot write can be applied.",
            "manual_no_integration_pilot records cannot enter ready_for_sync, sync_pending, synced or reconciled.",
            "outreach eligibility approved requires authoritative CRM checks and recorded human approval; public information never creates consent.",
            "A2 may create requalification signals but cannot set score_revision_status to proposed_by_a1 or approved without an A1 result reference.",
            "null external-system IDs do not imply no external record exists; an explicit check status is required.",
            "owner routing defaults to needs_owner_review when no approved assignment rule resolves the owner.",
        ],
        "external_state_references": {
            "hubspot_snapshot_id": hubspot["snapshot_id"],
            "note": "External HubSpot states are mapping references only and are not canonical A2 workflow states.",
            "status_models": hubspot["status_models"],
            "owner_model": {
                "owner_assignment_rules_available": hubspot["users_teams_ownership"]["owner_assignment_rules_available"],
                "backup_owner_rules_available": hubspot["users_teams_ownership"]["backup_owner_rules_available"],
                "ownership_restrictions_configured": hubspot["users_teams_ownership"]["ownership_restrictions_configured"],
            },
            "process_controls": {
                "enrichment_review_asset": hubspot["process_inventory"]["enrichment_review_asset"],
                "enabled_workflows": hubspot["process_inventory"]["enabled_workflows"],
                "workflow_dependency_status": "unverified",
            },
        },
    }


def build_field_rows() -> list[dict]:
    rows: list[dict] = []

    def add(section, path, data_type, required, nullable, cardinality, producer, authority, mutability, state_vocab, description, conditions=""):
        rows.append({
            "section": section,
            "field_path": path,
            "data_type": data_type,
            "required": required,
            "nullable": nullable,
            "cardinality": cardinality,
            "producer": producer,
            "authority": authority,
            "mutability": mutability,
            "state_vocabulary": state_vocab,
            "description": description,
            "conditions": conditions,
        })

    # record_metadata
    add("record_metadata", "record_metadata.schema_version", "string", "yes", "no", "one", "Unitalk release process", "Canonical A2 schema", "immutable_revision", "", "Canonical A2 record schema version.")
    add("record_metadata", "record_metadata.record_kind", "enum", "yes", "no", "one", "Revision builder", "Runtime/test fixture", "immutable_revision", "record_kind", "Synthetic versus real authorised business record.")
    add("record_metadata", "record_metadata.a2_record_id", "string", "yes", "no", "one", "Deterministic initialiser", "A2 lineage", "immutable_input", "", "Stable A2 lineage identifier for one accepted A1 handoff version.")
    add("record_metadata", "record_metadata.record_revision_id", "string", "yes", "no", "one", "Revision builder", "A2 revision store", "immutable_revision", "", "Unique immutable revision identifier.")
    add("record_metadata", "record_metadata.revision_number", "integer", "yes", "no", "one", "Revision builder", "A2 revision store", "immutable_revision", "", "Positive deterministic sequence within the A2 lineage.")
    add("record_metadata", "record_metadata.supersedes_revision_id", "string", "yes", "yes", "zero_or_one", "Revision builder", "A2 revision store", "immutable_revision", "", "Previous revision ID; null only for the first revision.")
    add("record_metadata", "record_metadata.supersedes_a2_record_id", "string", "yes", "yes", "zero_or_one", "Revision builder", "A2 lineage store", "immutable_revision", "", "Prior A2 lineage superseded by a materially changed A1 handoff.")
    add("record_metadata", "record_metadata.run_id", "string", "yes", "no", "one", "Runtime controller", "A2 runtime", "immutable_revision", "", "Run identifier that created the revision.")
    add("record_metadata", "record_metadata.audit_correlation_id", "string", "yes", "no", "one", "Runtime controller", "Audit layer", "immutable_revision", "", "Correlation ID shared across handoff, evidence, review and actions.")
    add("record_metadata", "record_metadata.created_at", "datetime", "yes", "no", "one", "Revision builder", "Audit clock", "immutable_revision", "", "Revision creation timestamp.")
    add("record_metadata", "record_metadata.created_by", "object", "yes", "no", "one", "Revision builder", "Audit identity", "immutable_revision", "", "Actor/profile/workflow that created the revision.")
    add("record_metadata", "record_metadata.change_reason", "enum", "yes", "no", "one", "Revision builder", "A2 state model", "immutable_revision", "change_reason", "Reason a new immutable revision was created.")

    # source_handoff
    add("source_handoff", "source_handoff.handoff_schema_version", "string", "yes", "no", "one", "A1 handoff", "Accepted handoff", "immutable_input", "", "A1-to-A2 handoff schema version.")
    add("source_handoff", "source_handoff.handoff_id", "string", "yes", "no", "one", "A1 handoff", "Accepted handoff", "immutable_input", "", "Stable handoff identifier.")
    add("source_handoff", "source_handoff.idempotency_key", "string", "yes", "no", "one", "A1 handoff", "Accepted handoff", "immutable_input", "", "Delivery and processing idempotency key.")
    add("source_handoff", "source_handoff.operating_scope", "enum", "yes", "no", "one", "A1 handoff", "Accepted handoff", "immutable_input", "operating_scope", "Synthetic, manual no-integration, integrated pilot or production scope.")
    add("source_handoff", "source_handoff.eligibility_status", "enum", "yes", "no", "one", "A1 handoff validator", "Accepted handoff", "immutable_input", "eligibility_status", "Eligibility status accepted by A2.")
    add("source_handoff", "source_handoff.accepted_at", "datetime", "yes", "no", "one", "A2 receiver", "A2 receipt", "immutable_input", "", "Timestamp A2 accepted the input or initialised a controlled manual package.")
    add("source_handoff", "source_handoff.accepted_by", "object", "yes", "no", "one", "A2 receiver", "A2 receipt", "immutable_input", "", "Receiver profile/actor information.")
    add("source_handoff", "source_handoff.candidate_snapshot_sha256", "string", "yes", "no", "one", "A1 handoff validator", "Accepted handoff", "immutable_input", "", "Canonical hash of the embedded A1 candidate snapshot.")
    add("source_handoff", "source_handoff.handoff_snapshot", "object", "yes", "no", "one", "A1 handoff", "Accepted A1-to-A2 envelope", "immutable_input", "", "Complete lossless accepted handoff envelope; A2 cannot edit it.")

    # subject
    add("subject", "subject.identity_resolution_status", "enum", "yes", "no", "one", "A2 entity resolver", "A2 identity review", "deterministic_derived", "identity_resolution_status", "Overall A2 subject identity state.")
    add("subject", "subject.entities", "array<object>", "yes", "no", "one_or_more", "A2 entity resolver", "A2 canonical record", "append_only_history", "", "Person and organisation entities resolved or proposed by A2.")
    add("subject", "subject.entities[].entity_id", "string", "yes", "no", "one", "A2 entity resolver", "A2 lineage", "immutable_revision", "", "Stable entity ID within the A2 lineage.")
    add("subject", "subject.entities[].entity_type", "enum", "yes", "no", "one", "A2 entity resolver", "A2 entity model", "immutable_revision", "entity_type", "Person or organisation.")
    add("subject", "subject.entities[].source_identity_reference", "string", "yes", "yes", "zero_or_one", "A2 entity resolver", "A1 handoff or A2 evidence", "immutable_revision", "", "Reference to A1 identity where applicable.")
    add("subject", "subject.entities[].display_name", "string", "yes", "no", "one", "A2 entity resolver", "Evidence/reviewer", "versioned", "", "Current proposed display name.")
    add("subject", "subject.entities[].aliases", "array<string>", "yes", "no", "zero_or_more", "A2 entity resolver", "Evidence/reviewer", "append_only_history", "", "Known aliases preserved for matching.")
    add("subject", "subject.entities[].match_status", "enum", "yes", "no", "one", "Entity matcher", "Matching evidence", "deterministic_derived", "entity_match_status", "External or internal match status.")
    add("subject", "subject.entities[].external_matches", "array<object>", "yes", "no", "zero_or_more", "Connector/entity matcher", "External source", "append_only_history", "", "Possible or confirmed external record matches.")
    add("subject", "subject.relationships", "array<object>", "yes", "no", "zero_or_more", "A2 entity resolver", "Evidence/reviewer", "append_only_history", "", "Explicit person-organisation and other approved relationships.")
    add("subject", "subject.relationships[].relationship_id", "string", "conditional", "no", "one", "A2 entity resolver", "A2 lineage", "immutable_revision", "", "Unique relationship ID; required for each relationship.")
    add("subject", "subject.relationships[].from_entity_id", "string", "conditional", "no", "one", "A2 entity resolver", "A2 entity model", "immutable_revision", "", "Source entity reference.")
    add("subject", "subject.relationships[].to_entity_id", "string", "conditional", "no", "one", "A2 entity resolver", "A2 entity model", "immutable_revision", "", "Target entity reference.")
    add("subject", "subject.relationships[].relationship_type", "string", "conditional", "no", "one", "A2 entity resolver", "Business field catalogue", "versioned", "", "Approved relationship type such as works_for or owns.")
    add("subject", "subject.relationships[].evidence_ids", "array<string>", "conditional", "no", "one_or_more", "A2 entity resolver", "Evidence registry/A1 handoff", "immutable_revision", "", "Evidence supporting the relationship.")
    add("subject", "subject.material_conflicts", "array<string>", "yes", "no", "zero_or_more", "Conflict controller", "Evidence/reviewer", "append_only_history", "conflict_status", "Material subject-identity conflicts.")

    # enrichment_scope
    add("enrichment_scope", "enrichment_scope.mode", "enum", "yes", "no", "one", "Triggering user/workflow", "Approved request", "immutable_revision", "enrichment_mode", "Default minimum package or targeted fields.")
    add("enrichment_scope", "enrichment_scope.requested_field_keys", "array<string>", "yes", "no", "zero_or_more", "Triggering user/workflow", "Business field catalogue", "immutable_revision", "", "Explicit requested canonical field keys.")
    add("enrichment_scope", "enrichment_scope.field_catalogue_version", "string", "yes", "no", "one", "Runtime preflight", "Approved field catalogue", "immutable_revision", "", "Field catalogue version applied.")
    add("enrichment_scope", "enrichment_scope.source_register_version", "string", "yes", "yes", "zero_or_one", "Runtime preflight", "Approved A2 source register", "immutable_revision", "", "Null until an A2 source register is approved; no live research when null.")
    add("enrichment_scope", "enrichment_scope.operating_scope", "enum", "yes", "no", "one", "Runtime preflight", "Accepted handoff", "immutable_revision", "operating_scope", "Scope must be consistent with source handoff.")
    add("enrichment_scope", "enrichment_scope.limits", "object", "yes", "no", "one", "Runtime policy", "Approved quota policy", "immutable_revision", "", "Candidate/source/call/retry/cost limits for the run.")
    add("enrichment_scope", "enrichment_scope.initiated_by", "object", "yes", "no", "one", "Runtime controller", "Audit identity", "immutable_revision", "", "Initiating user/workflow and purpose.")

    # field_assessments
    add("field_assessments", "field_assessments", "array<object>", "yes", "no", "zero_or_more", "A2 workflow", "A2 canonical record", "append_only_history", "", "Generic field-assessment collection.")
    add("field_assessments", "field_assessments[].field_assessment_id", "string", "conditional", "no", "one", "A2 workflow", "A2 lineage", "immutable_revision", "", "Unique assessment ID; required for each item.")
    add("field_assessments", "field_assessments[].field_key", "string", "conditional", "no", "one", "A2 workflow", "Approved field catalogue", "immutable_revision", "", "Canonical business field key.")
    add("field_assessments", "field_assessments[].entity_id", "string", "conditional", "yes", "zero_or_one", "A2 workflow", "Subject entity model", "immutable_revision", "", "Entity owning the field; null only for record-level fields.")
    add("field_assessments", "field_assessments[].scope", "enum", "conditional", "no", "one", "A2 workflow", "Field catalogue", "immutable_revision", "field_scope", "Person, organisation, relationship or record scope.")
    add("field_assessments", "field_assessments[].field_catalogue_version", "string", "conditional", "no", "one", "Runtime preflight", "Approved field catalogue", "immutable_revision", "", "Catalogue version defining the field.")
    add("field_assessments", "field_assessments[].value_type", "string", "conditional", "no", "one", "Runtime preflight", "Field catalogue", "immutable_revision", "", "Expected canonical value type.")
    add("field_assessments", "field_assessments[].sensitivity_classification", "string", "conditional", "no", "one", "Governance preflight", "Approved data policy", "immutable_revision", "", "Data category and sensitivity classification.")
    add("field_assessments", "field_assessments[].presence_status", "enum", "conditional", "no", "one", "Field controller", "Deterministic state model", "deterministic_derived", "value_presence_status", "Whether a reliable value is known.")
    add("field_assessments", "field_assessments[].availability_status", "enum", "conditional", "no", "one", "Source/tool controller", "Deterministic state model", "deterministic_derived", "availability_status", "Whether the applicable source/check was usable and found data.")
    add("field_assessments", "field_assessments[].field_quality_status", "enum", "conditional", "no", "one", "Quality controller", "Deterministic state model", "deterministic_derived", "field_quality_status", "Overall field-quality state.")
    add("field_assessments", "field_assessments[].baseline", "object", "conditional", "yes", "zero_or_one", "Initialiser/connector", "A1/HubSpot/prior approved revision", "external_authoritative_mirror", "", "Value known before the current A2 proposal.")
    add("field_assessments", "field_assessments[].baseline.value", "canonical_value", "conditional", "yes", "zero_or_one", "Initialiser/connector", "Baseline authority", "immutable_revision", "", "Raw baseline value; nullable when no value exists.")
    add("field_assessments", "field_assessments[].baseline.normalised_value", "canonical_value", "conditional", "yes", "zero_or_one", "Normalizer", "Deterministic method", "deterministic_derived", "", "Normalised baseline value.")
    add("field_assessments", "field_assessments[].baseline.origin", "object", "conditional", "no", "one", "Initialiser/connector", "A1/HubSpot/prior revision", "immutable_revision", "", "Origin system, record and field reference.")
    add("field_assessments", "field_assessments[].baseline.observed_at", "datetime", "conditional", "yes", "zero_or_one", "Initialiser/connector", "Origin source", "immutable_revision", "", "When the baseline was observed or retrieved.")
    add("field_assessments", "field_assessments[].baseline.evidence_ids", "array<string>", "conditional", "no", "zero_or_more", "Initialiser/connector", "A1 handoff/evidence registry", "immutable_revision", "", "Evidence or authoritative references supporting the baseline.")
    add("field_assessments", "field_assessments[].baseline.protected_status", "enum", "conditional", "no", "one", "Protected-field controller", "Approved policy/source metadata", "deterministic_derived", "protected_field_status", "Baseline protection classification.")
    add("field_assessments", "field_assessments[].observations", "array<object>", "conditional", "no", "zero_or_more", "A2 tools/providers/humans", "Evidence registry", "append_only_history", "", "Candidate values observed during A2 enrichment.")
    add("field_assessments", "field_assessments[].observations[].observation_id", "string", "conditional", "no", "one", "Observation builder", "A2 lineage", "immutable_revision", "", "Unique observation ID.")
    add("field_assessments", "field_assessments[].observations[].raw_value", "canonical_value", "conditional", "yes", "zero_or_one", "Source collector", "Permitted source", "immutable_revision", "", "Value exactly as observed where storage is permitted.")
    add("field_assessments", "field_assessments[].observations[].normalised_value", "canonical_value", "conditional", "yes", "zero_or_one", "Normalizer", "Deterministic method", "deterministic_derived", "", "Normalised observation value.")
    add("field_assessments", "field_assessments[].observations[].evidence_ids", "array<string>", "conditional", "no", "one_or_more", "Observation builder", "Evidence registry/A1 handoff", "immutable_revision", "", "Evidence supporting the observation.")
    add("field_assessments", "field_assessments[].observations[].verification_status", "enum", "conditional", "no", "one", "Verification controller", "Approved verification policy", "deterministic_derived", "verification_status", "Observation verification state.")
    add("field_assessments", "field_assessments[].observations[].confidence_level", "enum", "conditional", "no", "one", "Confidence controller", "Approved confidence policy", "deterministic_derived", "confidence_level", "Observation confidence level.")
    add("field_assessments", "field_assessments[].observations[].freshness_status", "enum", "conditional", "no", "one", "Freshness controller", "Approved freshness policy", "deterministic_derived", "freshness_status", "Observation freshness state.")
    add("field_assessments", "field_assessments[].observations[].claim_type", "enum", "conditional", "no", "one", "Evidence collector", "Evidence source", "immutable_revision", "claim_type", "Direct fact, inference or contradiction.")
    add("field_assessments", "field_assessments[].observations[].error", "object", "conditional", "yes", "zero_or_one", "Tool/controller", "Runtime audit", "append_only_history", "", "Structured error/limitation for the observation.")
    add("field_assessments", "field_assessments[].proposed_resolution", "object", "conditional", "yes", "zero_or_one", "A2 proposal logic", "Evidence and policy", "versioned", "", "At most one proposal per assessment and revision.")
    add("field_assessments", "field_assessments[].proposed_resolution.action", "enum", "conditional", "no", "one", "A2 proposal logic", "A2 state model", "immutable_revision", "proposal_action", "Proposed field action.")
    add("field_assessments", "field_assessments[].proposed_resolution.value", "canonical_value", "conditional", "yes", "zero_or_one", "A2 proposal logic", "Evidence and policy", "immutable_revision", "", "Proposed raw/canonical value where applicable.")
    add("field_assessments", "field_assessments[].proposed_resolution.normalised_value", "canonical_value", "conditional", "yes", "zero_or_one", "Normalizer", "Deterministic method", "deterministic_derived", "", "Normalised proposed value.")
    add("field_assessments", "field_assessments[].proposed_resolution.evidence_ids", "array<string>", "conditional", "no", "zero_or_more", "A2 proposal logic", "Evidence registry/A1 handoff", "immutable_revision", "", "Evidence supporting the proposal.")
    add("field_assessments", "field_assessments[].proposed_resolution.rationale", "string", "conditional", "no", "one", "A2 proposal logic", "Evidence and policy", "immutable_revision", "", "Concise evidence-led rationale.")
    add("field_assessments", "field_assessments[].proposed_resolution.verification_status", "enum", "conditional", "no", "one", "Verification controller", "Approved policy", "deterministic_derived", "verification_status", "Proposal verification state.")
    add("field_assessments", "field_assessments[].proposed_resolution.confidence_level", "enum", "conditional", "no", "one", "Confidence controller", "Approved policy", "deterministic_derived", "confidence_level", "Proposal confidence level.")
    add("field_assessments", "field_assessments[].proposed_resolution.freshness_status", "enum", "conditional", "no", "one", "Freshness controller", "Approved policy", "deterministic_derived", "freshness_status", "Proposal freshness state.")
    add("field_assessments", "field_assessments[].proposed_resolution.conflict_status", "enum", "conditional", "no", "one", "Conflict controller", "Approved policy/reviewer", "deterministic_derived", "conflict_status", "Conflict state relative to baseline/other observations.")
    add("field_assessments", "field_assessments[].proposed_resolution.protected_status", "enum", "conditional", "no", "one", "Protected-field controller", "Approved policy", "deterministic_derived", "protected_field_status", "Protection state governing the proposal.")
    add("field_assessments", "field_assessments[].field_review", "object", "conditional", "no", "one", "Authorised reviewer", "Recorded human decision", "human_controlled_decision", "", "Field-level review event; defaults to pending or not_required.")
    add("field_assessments", "field_assessments[].field_review.decision", "enum", "conditional", "no", "one", "Authorised reviewer", "Recorded human decision", "human_controlled_decision", "field_review_decision", "Field decision.")
    add("field_assessments", "field_assessments[].field_review.reviewer", "object", "conditional", "yes", "zero_or_one", "Authorised reviewer", "Approval matrix", "human_controlled_decision", "", "Reviewer identity; required for non-pending decisions except not_required.")
    add("field_assessments", "field_assessments[].field_review.decided_at", "datetime", "conditional", "yes", "zero_or_one", "Authorised reviewer", "Audit clock", "human_controlled_decision", "", "Decision timestamp.")
    add("field_assessments", "field_assessments[].field_review.reason", "string", "conditional", "yes", "zero_or_one", "Authorised reviewer", "Recorded decision", "human_controlled_decision", "", "Decision rationale or hold/change reason.")
    add("field_assessments", "field_assessments[].field_review.corrected_value", "canonical_value", "conditional", "yes", "zero_or_one", "Authorised reviewer", "Recorded decision", "human_controlled_decision", "", "Optional reviewer correction, creating a new revision.")
    add("field_assessments", "field_assessments[].application", "object", "conditional", "no", "one", "Connector/workflow", "External receipt", "connector_controlled_reference", "", "Application/sync state separate from approval.")
    add("field_assessments", "field_assessments[].application.status", "enum", "conditional", "no", "one", "Connector/workflow", "External receipt", "connector_controlled_reference", "application_status", "External application status.")
    add("field_assessments", "field_assessments[].application.destination", "string", "conditional", "yes", "zero_or_one", "Connector/workflow", "Approved mapping", "connector_controlled_reference", "", "Destination system/property reference.")
    add("field_assessments", "field_assessments[].application.external_action_reference", "string", "conditional", "yes", "zero_or_one", "Connector/workflow", "External receipt", "connector_controlled_reference", "", "Required when applied/reconciled.")
    add("field_assessments", "field_assessments[].application.workflow_dependency_status", "enum", "conditional", "no", "one", "Dependency audit", "HubSpot workflow register", "deterministic_derived", "workflow_dependency_status", "Mapped property/list/workflow side-effect status.")
    add("field_assessments", "field_assessments[].application.applied_at", "datetime", "conditional", "yes", "zero_or_one", "Connector/workflow", "External receipt", "connector_controlled_reference", "", "Application timestamp.")
    add("field_assessments", "field_assessments[].application.error", "object", "conditional", "yes", "zero_or_one", "Connector/workflow", "Runtime audit", "append_only_history", "", "Structured application failure.")

    # evidence_registry
    add("evidence_registry", "evidence_registry", "array<object>", "yes", "no", "zero_or_more", "A2 collectors/providers", "A2 evidence registry", "append_only_history", "", "A2-native evidence records; reused A1 evidence remains in source_handoff.")
    add("evidence_registry", "evidence_registry[].evidence_id", "string", "conditional", "no", "one", "Evidence builder", "A2 evidence namespace", "immutable_revision", "", "Unique A2 evidence ID.")
    add("evidence_registry", "evidence_registry[].namespace", "enum", "conditional", "no", "one", "Evidence builder", "A2 evidence policy", "immutable_revision", "evidence_namespace", "A2 evidence namespace; never relabel A1 evidence.")
    add("evidence_registry", "evidence_registry[].source_id", "string", "conditional", "no", "one", "Evidence collector", "A2 source register", "immutable_revision", "", "Versioned source-register ID.")
    add("evidence_registry", "evidence_registry[].source_type", "string", "conditional", "no", "one", "Evidence collector", "A2 source register", "immutable_revision", "", "Source category.")
    add("evidence_registry", "evidence_registry[].source_policy_status", "enum", "conditional", "no", "one", "Runtime preflight", "A2 source register", "immutable_revision", "source_policy_status", "Source permission status applied.")
    add("evidence_registry", "evidence_registry[].source_url", "string", "conditional", "yes", "zero_or_one", "Evidence collector", "Permitted source", "immutable_revision", "", "Canonical source URL where applicable.")
    add("evidence_registry", "evidence_registry[].provider_reference", "string", "conditional", "yes", "zero_or_one", "Provider connector", "Provider receipt", "connector_controlled_reference", "", "Provider request/result reference where applicable.")
    add("evidence_registry", "evidence_registry[].access_method", "string", "conditional", "no", "one", "Evidence collector", "A2 source register", "immutable_revision", "", "Manual, assisted, API or authorised file access profile.")
    add("evidence_registry", "evidence_registry[].retrieved_at", "datetime", "conditional", "no", "one", "Evidence collector", "Audit clock", "immutable_revision", "", "Retrieval timestamp.")
    add("evidence_registry", "evidence_registry[].source_date", "datetime_or_date", "conditional", "yes", "zero_or_one", "Evidence collector", "Source", "immutable_revision", "", "Source publication/update date when available.")
    add("evidence_registry", "evidence_registry[].title", "string", "conditional", "yes", "zero_or_one", "Evidence collector", "Source", "immutable_revision", "", "Source title or record label.")
    add("evidence_registry", "evidence_registry[].excerpt_or_result_summary", "string", "conditional", "no", "one", "Evidence collector", "Source/provider and storage policy", "immutable_revision", "", "Minimum permitted evidence excerpt or result summary.")
    add("evidence_registry", "evidence_registry[].claim_type", "enum", "conditional", "no", "one", "Evidence collector", "Evidence content", "immutable_revision", "claim_type", "Direct fact, inference or contradiction.")
    add("evidence_registry", "evidence_registry[].supports_field_assessment_ids", "array<string>", "conditional", "no", "zero_or_more", "Evidence builder", "A2 record", "immutable_revision", "", "Field assessments supported by this evidence.")
    add("evidence_registry", "evidence_registry[].supports_requalification_signal_ids", "array<string>", "conditional", "no", "zero_or_more", "Evidence builder", "A2 record", "immutable_revision", "", "Requalification signals supported by this evidence.")
    add("evidence_registry", "evidence_registry[].reliability_level", "enum", "conditional", "no", "one", "Evidence policy", "Approved evidence method", "deterministic_derived", "reliability_level", "Source/evidence reliability classification.")
    add("evidence_registry", "evidence_registry[].independence_group_id", "string", "conditional", "yes", "zero_or_one", "Evidence policy", "Source relationship analysis", "immutable_revision", "", "Groups copied/syndicated sources to prevent false corroboration.")
    add("evidence_registry", "evidence_registry[].provider_cost", "object", "conditional", "yes", "zero_or_one", "Provider connector", "Provider receipt", "append_only_history", "", "Credits/cost and cost-status metadata where applicable.")
    add("evidence_registry", "evidence_registry[].supersedes_evidence_id", "string", "conditional", "yes", "zero_or_one", "Evidence correction process", "A2 evidence registry", "append_only_history", "", "Prior evidence corrected without deleting history.")
    add("evidence_registry", "evidence_registry[].data_minimisation_notes", "string", "conditional", "yes", "zero_or_one", "Evidence collector", "Approved governance policy", "immutable_revision", "", "Notes on omitted or restricted fields.")

    # data_quality
    add("data_quality", "data_quality.status", "enum", "yes", "no", "one", "Quality controller", "A2 quality method", "deterministic_derived", "data_quality_status", "Record-level enrichment quality state.")
    add("data_quality", "data_quality.method_version", "string", "yes", "yes", "zero_or_one", "Quality controller", "Approved quality policy", "immutable_revision", "", "Null until the quality method is approved.")
    add("data_quality", "data_quality.calculated_at", "datetime", "yes", "yes", "zero_or_one", "Quality controller", "Audit clock", "deterministic_derived", "", "Calculation timestamp.")
    add("data_quality", "data_quality.required_field_keys", "array<string>", "yes", "no", "zero_or_more", "Quality controller", "Minimum data package", "immutable_revision", "", "Applicable required fields.")
    add("data_quality", "data_quality.missing_field_keys", "array<string>", "yes", "no", "zero_or_more", "Quality controller", "Field assessments", "deterministic_derived", "", "Required fields with no usable value.")
    add("data_quality", "data_quality.unverified_field_keys", "array<string>", "yes", "no", "zero_or_more", "Quality controller", "Field assessments", "deterministic_derived", "", "Fields failing verification requirements.")
    add("data_quality", "data_quality.conflict_field_keys", "array<string>", "yes", "no", "zero_or_more", "Quality controller", "Field assessments", "deterministic_derived", "", "Fields with unresolved material conflicts.")
    add("data_quality", "data_quality.stale_field_keys", "array<string>", "yes", "no", "zero_or_more", "Quality controller", "Freshness policy", "deterministic_derived", "", "Fields that require recheck.")
    add("data_quality", "data_quality.invalid_field_keys", "array<string>", "yes", "no", "zero_or_more", "Quality controller", "Validator", "deterministic_derived", "", "Fields that fail type/policy/consistency validation.")
    add("data_quality", "data_quality.limitations", "array<string>", "yes", "no", "zero_or_more", "Quality controller/reviewer", "Validated record", "append_only_history", "", "Visible limitations for human review.")

    # duplicate_and_eligibility
    add("duplicate_and_eligibility", "duplicate_and_eligibility.checks", "array<object>", "yes", "no", "zero_or_more", "Duplicate/eligibility controllers", "Authoritative check source", "append_only_history", "", "Separate A1, A2, HubSpot and eligibility checks.")
    add("duplicate_and_eligibility", "duplicate_and_eligibility.checks[].check_id", "string", "conditional", "no", "one", "Check controller", "A2 lineage", "immutable_revision", "", "Unique check ID.")
    add("duplicate_and_eligibility", "duplicate_and_eligibility.checks[].check_type", "string", "conditional", "no", "one", "Check controller", "Approved check catalogue", "immutable_revision", "", "Duplicate, customer, Deal, consent, suppression, sequence or other check type.")
    add("duplicate_and_eligibility", "duplicate_and_eligibility.checks[].system", "string", "conditional", "no", "one", "Check controller", "Source system", "immutable_revision", "", "A1, A2, HubSpot, file or provider system.")
    add("duplicate_and_eligibility", "duplicate_and_eligibility.checks[].status", "enum", "conditional", "no", "one", "Check controller", "Source result", "deterministic_derived", "duplicate_status", "Duplicate status when check_type is duplicate; field-specific vocabulary later for other checks.")
    add("duplicate_and_eligibility", "duplicate_and_eligibility.checks[].checked_at", "datetime", "conditional", "yes", "zero_or_one", "Check controller", "Audit clock", "immutable_revision", "", "Check timestamp; null when unavailable/not_checked.")
    add("duplicate_and_eligibility", "duplicate_and_eligibility.checks[].matches_or_references", "array<object>", "conditional", "no", "zero_or_more", "Check controller", "Source result", "append_only_history", "", "Matches, list refs or authoritative status refs.")
    add("duplicate_and_eligibility", "duplicate_and_eligibility.checks[].reason", "string", "conditional", "yes", "zero_or_one", "Check controller", "Source result", "immutable_revision", "", "Reason/limitation/error note.")
    add("duplicate_and_eligibility", "duplicate_and_eligibility.a2_eligibility_status", "enum", "yes", "no", "one", "Eligibility controller", "Approved gates", "deterministic_derived", "eligibility_status", "Eligibility for the declared A2 operating scope.")
    add("duplicate_and_eligibility", "duplicate_and_eligibility.outreach_eligibility_status", "enum", "yes", "no", "one", "CRM/policy/reviewer", "HubSpot and approved policy", "external_authoritative_mirror", "outreach_eligibility_status", "Separate outreach eligibility; unavailable before CRM checks.")
    add("duplicate_and_eligibility", "duplicate_and_eligibility.owner_routing_status", "enum", "yes", "no", "one", "CRM/assignment policy/reviewer", "HubSpot and approved rules", "external_authoritative_mirror", "owner_routing_status", "Owner routing result; defaults to unavailable/needs_owner_review without rules.")
    add("duplicate_and_eligibility", "duplicate_and_eligibility.reasons", "array<string>", "yes", "no", "zero_or_more", "Eligibility controller", "Check results", "deterministic_derived", "", "Visible eligibility reasons and blockers.")
    add("duplicate_and_eligibility", "duplicate_and_eligibility.evaluated_at", "datetime", "yes", "yes", "zero_or_one", "Eligibility controller", "Audit clock", "deterministic_derived", "", "Evaluation timestamp.")
    add("duplicate_and_eligibility", "duplicate_and_eligibility.method_version", "string", "yes", "yes", "zero_or_one", "Eligibility controller", "Approved policy", "immutable_revision", "", "Eligibility method version.")

    # requalification
    add("requalification", "requalification.signals", "array<object>", "yes", "no", "zero_or_more", "A2 evidence/qualification logic", "A2 record", "append_only_history", "", "Potential material evidence changes returned to A1.")
    add("requalification", "requalification.signals[].signal_id", "string", "conditional", "no", "one", "A2 signal builder", "A2 lineage", "immutable_revision", "", "Unique signal ID.")
    add("requalification", "requalification.signals[].affected_criterion_id", "string", "conditional", "no", "one", "A2 signal builder", "A1 ICP configuration", "immutable_revision", "", "A1 criterion potentially affected.")
    add("requalification", "requalification.signals[].prior_criterion_status", "string", "conditional", "no", "one", "A2 signal builder", "A1 handoff", "immutable_revision", "", "Original A1 criterion status.")
    add("requalification", "requalification.signals[].proposed_evidence_status", "string", "conditional", "no", "one", "A2 signal builder", "Evidence only", "immutable_revision", "", "Proposed evidence state, never points or score.")
    add("requalification", "requalification.signals[].evidence_ids", "array<string>", "conditional", "no", "one_or_more", "A2 signal builder", "A2 evidence/A1 refs", "immutable_revision", "", "Evidence supporting the signal.")
    add("requalification", "requalification.signals[].materiality", "enum", "conditional", "no", "one", "A2 signal builder", "Approved policy", "deterministic_derived", "requalification_materiality", "Low, medium or high materiality.")
    add("requalification", "requalification.signals[].potential_score_direction", "enum", "conditional", "no", "one", "A2 signal builder", "Evidence interpretation", "immutable_revision", "potential_score_direction", "Increase, decrease, unchanged or unknown; never a numeric score.")
    add("requalification", "requalification.signals[].status", "enum", "conditional", "no", "one", "A2/reviewer/workflow", "A2 state model", "append_only_history", "requalification_signal_status", "Signal lifecycle state.")
    add("requalification", "requalification.returns", "array<object>", "yes", "no", "zero_or_more", "Workflow", "Durable A1 return/receipt", "append_only_history", "", "Structured return payload references.")
    add("requalification", "requalification.returns[].return_id", "string", "conditional", "no", "one", "Workflow", "Durable return store", "immutable_revision", "", "Return payload ID.")
    add("requalification", "requalification.returns[].signal_ids", "array<string>", "conditional", "no", "one_or_more", "Workflow", "A2 record", "immutable_revision", "", "Approved signals included.")
    add("requalification", "requalification.returns[].status", "enum", "conditional", "no", "one", "Workflow/A1 receipt", "Durable workflow", "append_only_history", "requalification_return_status", "Return delivery/receipt state.")
    add("requalification", "requalification.returns[].approval", "object", "conditional", "yes", "zero_or_one", "Authorised reviewer", "Approval matrix", "human_controlled_decision", "", "Required before delivery during pilot.")
    add("requalification", "requalification.score_revision_references", "array<object>", "yes", "no", "zero_or_more", "A1 return connector", "A1 deterministic scoring", "append_only_history", "", "Authoritative A1 score-revision results.")
    add("requalification", "requalification.score_revision_references[].score_revision_id", "string", "conditional", "no", "one", "A1 scoring connector", "A1 result", "connector_controlled_reference", "", "A1 score revision ID.")
    add("requalification", "requalification.score_revision_references[].status", "enum", "conditional", "no", "one", "A1 scoring/reviewer", "A1 result/approval", "append_only_history", "score_revision_status", "Revision lifecycle state.")
    add("requalification", "requalification.score_revision_references[].score", "number", "conditional", "yes", "zero_or_one", "A1 deterministic scorer", "A1 result", "immutable_input", "", "A1-produced score only; required for proposed/approved result as defined later.")
    add("requalification", "requalification.score_revision_references[].band", "string", "conditional", "yes", "zero_or_one", "A1 deterministic scorer", "A1 result", "immutable_input", "", "A1-produced band only.")
    add("requalification", "requalification.score_revision_references[].model_version", "string", "conditional", "yes", "zero_or_one", "A1 deterministic scorer", "A1 result", "immutable_input", "", "A1 scoring model version.")
    add("requalification", "requalification.score_revision_references[].approval", "object", "conditional", "yes", "zero_or_one", "Authorised A1 reviewer", "A1 approval record", "human_controlled_decision", "", "Required for approved revision.")
    add("requalification", "requalification.score_revision_references[].result_reference", "string", "conditional", "yes", "zero_or_one", "A1 connector", "A1 result store", "connector_controlled_reference", "", "Verifiable A1 result reference.")

    # review
    add("review", "review.record_decision", "enum", "yes", "no", "one", "Authorised reviewer", "Recorded human decision", "human_controlled_decision", "record_review_decision", "Record-level review decision.")
    add("review", "review.reviewer", "object", "yes", "yes", "zero_or_one", "Authorised reviewer", "Approval matrix", "human_controlled_decision", "", "Required for non-pending decisions.")
    add("review", "review.decided_at", "datetime", "yes", "yes", "zero_or_one", "Authorised reviewer", "Audit clock", "human_controlled_decision", "", "Decision timestamp.")
    add("review", "review.reason", "string", "yes", "yes", "zero_or_one", "Authorised reviewer", "Recorded decision", "human_controlled_decision", "", "Reason for rejection, hold, block or changes.")
    add("review", "review.required_field_decisions_complete", "boolean", "yes", "no", "one", "Review validator", "Field reviews", "deterministic_derived", "", "True only when all required field-level decisions are complete.")
    add("review", "review.requested_changes", "array<string>", "yes", "no", "zero_or_more", "Authorised reviewer", "Recorded decision", "append_only_history", "", "Requested corrections or evidence.")

    # workflow
    add("workflow", "workflow.state", "enum", "yes", "no", "one", "Workflow/application layer", "A2 state model", "controlled_transition", "workflow_state", "Current A2 workflow state for this revision.")
    add("workflow", "workflow.previous_state", "enum", "yes", "yes", "zero_or_one", "Workflow/application layer", "Prior revision/state", "immutable_revision", "workflow_state", "Prior workflow state.")
    add("workflow", "workflow.transitioned_at", "datetime", "yes", "no", "one", "Workflow/application layer", "Audit clock", "immutable_revision", "", "Transition timestamp.")
    add("workflow", "workflow.triggered_by", "object", "yes", "no", "one", "Workflow/application layer", "Audit identity", "immutable_revision", "", "Actor/event causing the transition.")
    add("workflow", "workflow.hold_reasons", "array<string>", "yes", "no", "zero_or_more", "Workflow/reviewer", "Check/review results", "append_only_history", "", "Required when held.")
    add("workflow", "workflow.block_reasons", "array<string>", "yes", "no", "zero_or_more", "Workflow/reviewer", "Policy/check results", "append_only_history", "", "Required when blocked.")
    add("workflow", "workflow.failure", "object", "yes", "yes", "zero_or_one", "Workflow", "Runtime audit", "append_only_history", "", "Structured processing/sync failure.")

    # system_references
    for path, description in [
        ("system_references.a1_candidate_id", "A1 candidate ID."),
        ("system_references.a1_handoff_id", "A1-to-A2 handoff ID."),
        ("system_references.twenty_record_id", "Twenty or approved staging record ID."),
        ("system_references.hubspot_contact_id", "Matched/created HubSpot Contact ID."),
        ("system_references.hubspot_company_id", "Matched/created HubSpot Company ID."),
        ("system_references.hubspot_deal_ids", "Relevant HubSpot Deal IDs."),
        ("system_references.hubspot_proposed_patch_id", "Proposed HubSpot patch ID."),
        ("system_references.hubspot_sync_id", "Verified HubSpot sync/action ID."),
        ("system_references.n8n_work_item_id", "n8n/shared work-item ID."),
        ("system_references.n8n_execution_id", "n8n execution ID."),
        ("system_references.provider_request_ids", "Approved provider request IDs."),
        ("system_references.a3_handoff_id", "Future A3 handoff ID."),
        ("system_references.a14_handoff_id", "Future A14 handoff ID."),
        ("system_references.requalification_return_id", "A1 requalification return ID."),
        ("system_references.a1_score_revision_id", "Returned A1 score revision ID."),
    ]:
        dtype = "array<string>" if path.endswith("_ids") else "string"
        is_required_a1_reference = path in {"system_references.a1_candidate_id", "system_references.a1_handoff_id"}
        nullable = "no" if is_required_a1_reference else "yes"
        cardinality = "one" if is_required_a1_reference else ("zero_or_more" if dtype.startswith("array") else "zero_or_one")
        add("system_references", path, dtype, "yes", nullable, cardinality, "Authorised connector/workflow", "Verified external receipt", "connector_controlled_reference", "", description, "Null does not mean checked or absent; a separate status is required." if not is_required_a1_reference else "Must match the immutable source_handoff reference.")

    # governance
    add("governance", "governance.processing_purpose", "string", "yes", "no", "one", "Runtime preflight", "Approved A2 purpose", "immutable_revision", "", "Approved processing purpose.")
    add("governance", "governance.contains_personal_data", "boolean", "yes", "no", "one", "Governance classifier", "Record content", "deterministic_derived", "", "Whether the record contains personal data.")
    add("governance", "governance.data_categories", "array<string>", "yes", "no", "zero_or_more", "Governance classifier", "Approved data policy", "deterministic_derived", "", "Personal/business data categories present.")
    add("governance", "governance.source_register_version", "string", "yes", "yes", "zero_or_one", "Runtime preflight", "Approved A2 source register", "immutable_revision", "", "Null means no live source research is authorised.")
    add("governance", "governance.source_terms_review_status", "enum", "yes", "no", "one", "Runtime preflight", "A2 source register", "deterministic_derived", "source_policy_status", "Overall source-rights readiness for the run.")
    add("governance", "governance.retention_policy_version", "string", "yes", "yes", "zero_or_one", "Runtime preflight", "Approved retention policy", "immutable_revision", "", "Retention policy version; missing policy may block real data.")
    add("governance", "governance.approval_matrix_version", "string", "yes", "yes", "zero_or_one", "Runtime preflight", "Approved matrix", "immutable_revision", "", "Approval matrix applied.")
    add("governance", "governance.consent_check_status", "enum", "yes", "no", "one", "HubSpot connector/policy", "Authoritative CRM", "external_authoritative_mirror", "outreach_eligibility_status", "Consent/outreach check visibility; unavailable without CRM.")
    add("governance", "governance.outreach_authorized", "boolean", "yes", "no", "one", "Guardrail", "Approved action policy", "immutable_revision", "", "Must remain false in A2 foundation/no-integration scope.")
    add("governance", "governance.crm_write_authorized", "boolean", "yes", "no", "one", "Guardrail", "Approved action policy", "immutable_revision", "", "Must remain false until guarded integration approval.")
    add("governance", "governance.provider_use_authorized", "boolean", "yes", "no", "one", "Guardrail", "Provider approval register", "immutable_revision", "", "False until provider/account/data route/budget approval.")
    add("governance", "governance.policy_limitations", "array<string>", "yes", "no", "zero_or_more", "Runtime/reviewer", "Applied policies", "append_only_history", "", "Visible unresolved governance limitations.")

    # audit_and_consumption
    add("audit_and_consumption", "audit_and_consumption.events", "array<object>", "yes", "no", "one_or_more", "Runtime/workflow/connectors", "Audit layer", "append_only_history", "", "Chronological audit events.")
    add("audit_and_consumption", "audit_and_consumption.events[].event_id", "string", "conditional", "no", "one", "Audit layer", "Audit layer", "immutable_revision", "", "Unique event ID.")
    add("audit_and_consumption", "audit_and_consumption.events[].event_type", "string", "conditional", "no", "one", "Audit layer", "Audit event catalogue", "immutable_revision", "", "Run, tool, review, transition or external-action event type.")
    add("audit_and_consumption", "audit_and_consumption.events[].actor", "object", "conditional", "no", "one", "Audit layer", "Verified actor identity", "immutable_revision", "", "Actor/profile/workflow responsible.")
    add("audit_and_consumption", "audit_and_consumption.events[].timestamp", "datetime", "conditional", "no", "one", "Audit layer", "Audit clock", "immutable_revision", "", "Event timestamp.")
    add("audit_and_consumption", "audit_and_consumption.events[].input_references", "array<string>", "conditional", "no", "zero_or_more", "Audit layer", "Artifact/source refs", "immutable_revision", "", "Input artifact/source references.")
    add("audit_and_consumption", "audit_and_consumption.events[].output_references", "array<string>", "conditional", "no", "zero_or_more", "Audit layer", "Artifact refs", "immutable_revision", "", "Output references.")
    add("audit_and_consumption", "audit_and_consumption.events[].model", "string", "conditional", "yes", "zero_or_one", "Runtime", "Gateway metadata", "immutable_revision", "", "Logical/actual model reference when applicable.")
    add("audit_and_consumption", "audit_and_consumption.events[].tools", "array<string>", "conditional", "no", "zero_or_more", "Runtime", "Tool metadata", "immutable_revision", "", "Tools/providers used.")
    add("audit_and_consumption", "audit_and_consumption.events[].usage", "object", "conditional", "yes", "zero_or_one", "Runtime/provider", "Usage receipt", "append_only_history", "", "Tokens, calls, credits and cost metadata.")
    add("audit_and_consumption", "audit_and_consumption.events[].external_action", "object", "conditional", "yes", "zero_or_one", "Connector/workflow", "External receipt", "append_only_history", "", "External action, approval, result and retry metadata.")
    add("audit_and_consumption", "audit_and_consumption.total_usage", "object", "yes", "no", "one", "Deterministic aggregator", "Audit events", "deterministic_derived", "", "Revision/run aggregate usage and cost status.")
    add("audit_and_consumption", "audit_and_consumption.errors", "array<object>", "yes", "no", "zero_or_more", "Runtime/workflow", "Audit events", "append_only_history", "", "Structured errors, retries and blocked reasons.")

    return rows


def main() -> None:
    CONTRACTS.mkdir(parents=True, exist_ok=True)
    state_model = build_state_model()
    STATE_MODEL.write_text(json.dumps(state_model, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    rows = build_field_rows()
    with FIELD_DICTIONARY.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELD_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(json.dumps({
        "field_dictionary": str(FIELD_DICTIONARY),
        "field_rows": len(rows),
        "sections": sorted({row["section"] for row in rows}),
        "state_model": str(STATE_MODEL),
        "vocabularies": len(state_model["canonical_vocabularies"]),
        "workflow_states": len(state_model["canonical_vocabularies"]["workflow_state"]["values"]),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
