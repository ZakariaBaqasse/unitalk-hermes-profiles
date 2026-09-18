#!/usr/bin/env python3
"""Build the Step 3E protected-field and conflict-policy draft."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROFILE_ROOT / "foundations" / "contracts" / "governance"
POLICY = ROOT / "a2-protected-fields-and-conflict-policy-0.1.0-draft.1.json"
FIXTURES = PROFILE_ROOT / "evaluations" / "step3e" / "fixtures" / "cases.json"
FIELD_CATALOGUE = PROFILE_ROOT / "foundations" / "contracts" / "business" / "a2-business-field-catalogue-0.1.0-draft.1.json"
EVIDENCE_POLICY = PROFILE_ROOT / "foundations" / "contracts" / "evidence" / "a2-evidence-verification-confidence-freshness-policy-0.1.0-draft.1.json"
HUBSPOT_PROPERTIES = Path("/opt/data/profiles/equinet/attachments/Property_Definitions (1).csv")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_policy() -> dict:
    return {
        "policy_id": "equinet-a2-protected-fields-and-conflicts",
        "version": "0.1.0-draft.1",
        "status": "approved_by_unitalk_as_working_baseline_pending_equinet_confirmation",
        "profile": "equinet-a2-enrichment",
        "unitalk_approval": {
            "approver": "Séverine, Unitalk Operations",
            "approved_at": "2026-08-26T19:39:20Z",
            "scope": "decisions_3E_1_through_3E_10"
        },
        "dependencies": [
            {"path": str(FIELD_CATALOGUE.relative_to(PROFILE_ROOT)), "sha256": sha256(FIELD_CATALOGUE)},
            {"path": str(EVIDENCE_POLICY.relative_to(PROFILE_ROOT)), "sha256": sha256(EVIDENCE_POLICY)},
            {"path": str(HUBSPOT_PROPERTIES), "sha256": sha256(HUBSPOT_PROPERTIES)},
        ],
        "global_rules": {
            "current_hubspot_write_authorized": False,
            "existing_manual_value_preserved": True,
            "protected_field_never_overwritten_automatically": True,
            "null_or_missing_connector_reference_is_not_a_negative_check_result": True,
            "workflow_dependency_verification_required_before_write": True,
            "list_membership_impact_verification_required_before_write": True,
            "idempotency_receipt_and_readback_required_for_future_write": True,
            "a1_snapshot_never_mutated": True,
            "a2_numeric_score_change_prohibited": True,
        },
        "protection_classes": {
            "authoritative_control": {"default_action": "read_only_preserve", "exception_allowed": False},
            "system_read_only": {"default_action": "read_only_preserve", "exception_allowed": False},
            "owner_and_routing": {"default_action": "preserve_or_needs_owner_review", "exception_allowed": True},
            "manual_business_value": {"default_action": "preserve_and_propose_with_review", "exception_allowed": True},
            "a2_enrichment_candidate": {"default_action": "propose_only", "exception_allowed": True},
            "review_only_personal_data": {"default_action": "hold_for_privacy_review", "exception_allowed": True},
            "prohibited_personal_or_sensitive": {"default_action": "reject_collection", "exception_allowed": False},
        },
        "hubspot_protected_fields": [
            {"object": "Contact", "property": "do_not_contact", "class": "authoritative_control", "reason": "contact prohibition"},
            {"object": "Company", "property": "do_not_contact", "class": "authoritative_control", "reason": "company prohibition"},
            {"object": "Contact", "property": "gdpr_consent", "class": "authoritative_control", "reason": "consent"},
            {"object": "Company", "property": "gdpr_consent", "class": "authoritative_control", "reason": "consent"},
            {"object": "Contact", "property": "hs_legal_basis", "class": "authoritative_control", "reason": "legal basis"},
            {"object": "Contact", "property": "hs_marketable_status", "class": "system_read_only", "reason": "marketing-contact status"},
            {"object": "Contact", "property": "hs_current_customer", "class": "authoritative_control", "reason": "customer status"},
            {"object": "Company", "property": "hs_current_customer", "class": "authoritative_control", "reason": "customer status"},
            {"object": "Contact", "property": "lifecyclestage", "class": "authoritative_control", "reason": "lifecycle"},
            {"object": "Company", "property": "lifecyclestage", "class": "authoritative_control", "reason": "lifecycle"},
            {"object": "Contact", "property": "hs_lead_status", "class": "authoritative_control", "reason": "lead status"},
            {"object": "Company", "property": "hs_lead_status", "class": "authoritative_control", "reason": "lead status"},
            {"object": "Contact", "property": "hubspot_owner_id", "class": "owner_and_routing", "reason": "record owner"},
            {"object": "Company", "property": "hubspot_owner_id", "class": "owner_and_routing", "reason": "record owner"},
            {"object": "Deal", "property": "hubspot_owner_id", "class": "owner_and_routing", "reason": "deal owner"},
            {"object": "Deal", "property": "dealstage", "class": "authoritative_control", "reason": "deal state"},
            {"object": "Contact", "property": "hs_sequences_is_enrolled", "class": "system_read_only", "reason": "sequence state"},
            {"object": "Contact", "property": "hs_sequences_enrolled_count", "class": "system_read_only", "reason": "sequence state"},
            {"object": "Contact", "property": "hs_latest_sequence_enrolled", "class": "system_read_only", "reason": "sequence state"},
            {"object": "Contact", "property": "hs_latest_sequence_enrolled_date", "class": "system_read_only", "reason": "sequence state"},
            {"object": "Contact", "property": "hs_latest_sequence_ended_date", "class": "system_read_only", "reason": "sequence state"},
            {"object": "Contact", "property": "hs_contact_enrichment_opt_out", "class": "system_read_only", "reason": "enrichment opt-out"},
            {"object": "Contact", "property": "hs_contact_enrichment_opt_out_timestamp", "class": "system_read_only", "reason": "enrichment opt-out timestamp"},
            {"object": "Contact", "property": "business_unit_optout_18640656", "class": "system_read_only", "reason": "Mustad USA email opt-out"},
            {"object": "Contact", "property": "hs_email_optout_2431422236", "class": "system_read_only", "reason": "Customer Service Communication opt-out"},
            {"object": "Contact", "property": "hs_email_optout_2585761664", "class": "system_read_only", "reason": "Marketing Information opt-out; duplicate label exists"},
            {"object": "Contact", "property": "hs_email_optout_627076427", "class": "system_read_only", "reason": "Marketing Information opt-out; duplicate label exists"},
            {"object": "Contact", "property": "hs_email_optout_627076428", "class": "system_read_only", "reason": "One-to-One opt-out"},
            {"object": "Contact", "property": "contact_verified", "class": "manual_business_value", "reason": "semantics not yet aligned with A2 verification"},
            {"object": "Contact", "property": "data_quality", "class": "manual_business_value", "reason": "semantics not yet aligned with A2 quality"},
            {"object": "Company", "property": "data_quality", "class": "manual_business_value", "reason": "semantics not yet aligned with A2 quality"},
            {"object": "Company", "property": "mailing_verified", "class": "manual_business_value", "reason": "verification semantics require approval"}
        ],
        "manual_value_rule": {
            "applies_to": "any populated HubSpot field not proven system-generated",
            "on_same_value": "no_change",
            "on_empty_baseline_and_verified_proposal": "propose_add_for_human_review",
            "on_different_value": "preserve_baseline_create_conflict_and_hold",
            "silent_overwrite": False,
        },
        "conflict_precedence": [
            "authoritative_control_or_system_read_only",
            "authorised_current_first_party_record",
            "existing_manual_crm_value",
            "current_explicit_official_business_website_fact",
            "approved_official_registry_fact",
            "approved_linkedin_profile_evidence",
            "approved_email_provider_result",
            "reused_directory_context",
            "search_discovery_never_evidence"
        ],
        "field_level_exception_requirements": [
            "field_key", "current_value", "proposed_value", "evidence_ids", "reason",
            "approval_matrix_version", "reviewer_id", "reviewer_role", "approved_at",
            "approved_action", "scope", "expiry_or_single_use", "workflow_dependency_status"
        ],
        "workflow_dependency_gate": {
            "enabled_workflows_observed": 28,
            "lists_observed": 32,
            "exact_trigger_action_dependencies_verified": False,
            "default_status": "workflow_dependency_unverified",
            "write_action": "blocked",
        },
        "decision_matrix": [
            {"case": "same_value", "action": "no_change", "review": "not_required"},
            {"case": "empty_unprotected_baseline_verified_proposal", "action": "propose_add", "review": "required"},
            {"case": "different_manual_or_protected_baseline", "action": "preserve_and_hold", "review": "required"},
            {"case": "authoritative_control_conflict", "action": "preserve_authoritative_and_block", "review": "required"},
            {"case": "material_non_authoritative_conflict", "action": "hold", "review": "required"},
            {"case": "unverified_or_low_confidence_proposal", "action": "reject_proposal", "review": "visible"},
            {"case": "approved_exception_but_workflow_unverified", "action": "approved_proposal_write_blocked", "review": "recorded"},
            {"case": "a1_score_related_evidence", "action": "create_requalification_signal", "review": "required"}
        ],
        "open_confirmations": [
            "Name the A2 business reviewer and backup.",
            "Approve the action-level exception matrix.",
            "Confirm which non-control HubSpot values are always treated as manually protected.",
            "Verify exact workflow and list dependencies before any future mapped write.",
            "Confirm owner and territory reassignment rules.",
        ],
    }


def case(name: str, protection_class: str, baseline: str, proposal: str, confidence: str, conflict: str, review: str, workflow: str, crm_write: bool, expected: str, *, a1_requalification_required: bool = False) -> dict:
    return {"name": name, "protection_class": protection_class, "baseline_state": baseline, "proposal_state": proposal, "confidence": confidence, "conflict": conflict, "review_decision": review, "workflow_dependency_status": workflow, "crm_write_authorized": crm_write, "a1_requalification_required": a1_requalification_required, "expected_action": expected}


def build_fixtures() -> None:
    cases = [
        case("same_manual_value", "manual_business_value", "populated", "same", "high", "none", "pending", "not_checked", False, "no_change"),
        case("empty_unprotected_add", "a2_enrichment_candidate", "empty", "different", "high", "none", "approved", "verified_no_side_effect", False, "propose_add"),
        case("different_manual_value", "manual_business_value", "populated", "different", "high", "material", "pending", "not_checked", False, "preserve_and_hold"),
        case("consent_conflict", "authoritative_control", "populated", "different", "high", "material", "approved", "verified_no_side_effect", True, "preserve_authoritative_and_block"),
        case("read_only_sequence", "system_read_only", "populated", "different", "high", "none", "approved", "verified_no_side_effect", True, "read_only_preserve"),
        case("owner_without_approval", "owner_and_routing", "populated", "different", "high", "none", "pending", "not_checked", False, "preserve_or_needs_owner_review"),
        case("low_confidence_proposal", "a2_enrichment_candidate", "empty", "different", "low", "none", "pending", "not_checked", False, "reject_proposal"),
        case("approved_but_workflow_unknown", "a2_enrichment_candidate", "empty", "different", "high", "none", "approved", "not_checked", True, "approved_proposal_write_blocked"),
        case("prohibited_personal_data", "prohibited_personal_or_sensitive", "empty", "different", "high", "none", "approved", "verified_no_side_effect", True, "reject_collection"),
        case("personal_email_candidate", "review_only_personal_data", "empty", "different", "high", "none", "pending", "not_checked", False, "hold_for_privacy_review"),
        case("score_related_evidence", "a2_enrichment_candidate", "empty", "different", "high", "none", "approved", "verified_no_side_effect", False, "create_requalification_signal", a1_requalification_required=True),
    ]
    write(FIXTURES, {"version": "0.1.0-draft.1", "cases": cases})


def main() -> None:
    policy = build_policy()
    write(POLICY, policy)
    build_fixtures()
    print(json.dumps({"policy": str(POLICY), "protected_field_count": len(policy["hubspot_protected_fields"]), "fixture_count": len(json.loads(FIXTURES.read_text())["cases"])}, indent=2))


if __name__ == "__main__":
    main()
