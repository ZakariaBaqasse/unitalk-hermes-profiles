#!/usr/bin/env python3
"""Build provisional Step 3B minimum data packages and fixtures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
BUSINESS = PROFILE_ROOT / "foundations" / "contracts" / "business"
CATALOGUE = BUSINESS / "a2-business-field-catalogue-0.1.0-draft.1.json"
PACKAGE_PATH = BUSINESS / "a2-minimum-data-packages-0.1.0-draft.1.json"
FIXTURES = PROFILE_ROOT / "evaluations" / "step3b" / "fixtures"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_packages() -> dict:
    return {
        "package_contract_id": "equinet-a2-minimum-data-packages",
        "version": "0.1.0-draft.1",
        "status": "approved_by_unitalk_as_working_baseline_pending_equinet_confirmation",
        "profile": "equinet-a2-enrichment",
        "canonical_schema_version": "1.0.0",
        "business_field_catalogue": {
            "path": str(CATALOGUE.relative_to(PROFILE_ROOT)),
            "version": "0.1.0-draft.1",
            "sha256": sha256(CATALOGUE),
            "status": "approved_unitalk_working_baseline_pending_equinet_confirmation",
        },
        "input_contract": {
            "field_states": ["verified", "present_unverified", "missing", "unknown", "not_found", "unavailable", "conflict", "error"],
            "verified_only_satisfies_required_field": True,
            "unknown_or_not_found_never_becomes_a_value": True,
            "record_must_pass_canonical_validation_first": True,
        },
        "global_rules": {
            "human_review_required_during_pilot": True,
            "review_readiness_is_not_outreach_eligibility": True,
            "review_readiness_is_not_crm_write_authority": True,
            "missing_required_field": {
                "field_quality_status": "gap",
                "record_data_quality_status": "incomplete",
                "automatic_rejection": False,
                "automatic_a1_score_change": False,
                "external_action_authorized": False,
                "visible_in_review_package": True,
            },
            "material_conflict": {
                "record_data_quality_status": "conflict",
                "workflow_recommendation": "held",
                "human_resolution_required": True,
            },
            "research_not_exhausted_workflow": "enrichment_in_progress",
            "research_exhausted_with_gap_workflow": "held",
        },
        "packages": {
            "farrier_review_ready": {
                "segment": "farrier",
                "purpose": "Minimum A2 package for human review of a Farrier prospect.",
                "required_verified_fields": [
                    "person.professional_status",
                    "organisation.business_name",
                    "organisation.public_business_location",
                    "organisation.service_area",
                    "organisation.disciplines",
                ],
                "contact_paths": {
                    "named_target": {
                        "required_verified_fields": ["person.full_name", "person.role_title", "relationship.target_role_priority"],
                        "at_least_one_verified_field": ["person.business_email", "person.business_phone"],
                    },
                    "general_organisation_fallback": {
                        "required_flags": {"target_role_not_found": True},
                        "at_least_one_verified_field": ["organisation.business_email", "organisation.business_phone"],
                        "documented_exception_fields": ["person.full_name", "person.role_title", "relationship.target_role_priority"],
                    },
                },
                "optional_fields_do_not_block": True,
            },
            "horse_owner_review_ready": {
                "segment": "horse_owner",
                "purpose": "Minimum A2 package for human review of a Horse Owner organisation prospect.",
                "required_verified_fields": [
                    "organisation.business_name",
                    "organisation.public_business_location",
                    "organisation.stable_type",
                ],
                "contact_paths": {
                    "named_target": {
                        "required_verified_fields": ["person.full_name", "person.role_title", "relationship.target_role_priority"],
                        "at_least_one_verified_field": ["person.business_email", "person.business_phone"],
                    },
                    "general_organisation_fallback": {
                        "required_flags": {"target_role_not_found": True},
                        "at_least_one_verified_field": ["organisation.business_email", "organisation.business_phone"],
                        "documented_exception_fields": ["person.full_name", "person.role_title", "relationship.target_role_priority"],
                    },
                },
                "explicit_horse_count_required": False,
                "optional_fields_do_not_block": True,
            },
        },
        "outreach_readiness_boundary": {
            "separate_from_a2_review_ready": True,
            "current_status": "unavailable",
            "reason": "HubSpot authoritative consent, suppression, customer, Deal and sequence checks are not connected.",
            "required_authoritative_checks": ["consent", "suppression", "customer_status", "deal_status", "sequence_status", "owner_and_business_unit_access"],
            "public_contact_data_never_satisfies_outreach_eligibility": True,
            "send_authorized": False,
        },
        "approval_boundary": {
            "unitalk_status": "approved_working_baseline",
            "unitalk_approver": "Séverine, Unitalk Operations",
            "unitalk_approved_at": "2026-08-26T17:37:05Z",
            "equinet_confirmation": "pending",
            "live_use_authorized": False,
            "external_actions_authorized": False,
            "next_gate_after_approval": "Step 3C — A2 Source Register",
        },
    }


def fixture(name: str, segment: str, contact_path: str, verified: list[str], *, target_role_not_found: bool = False, research_exhausted: bool = False, conflicts: list[str] | None = None, errors: list[str] | None = None, extra_states: dict[str, str] | None = None) -> dict:
    fields = {key: "verified" for key in verified}
    fields.update(extra_states or {})
    return {
        "fixture_id": name,
        "segment": segment,
        "contact_path": contact_path,
        "target_role_not_found": target_role_not_found,
        "research_exhausted": research_exhausted,
        "field_states": fields,
        "conflict_field_keys": conflicts or [],
        "error_field_keys": errors or [],
    }


def build_fixtures() -> None:
    farrier_core = [
        "person.professional_status", "organisation.business_name", "organisation.public_business_location",
        "organisation.service_area", "organisation.disciplines",
    ]
    named = ["person.full_name", "person.role_title", "relationship.target_role_priority"]
    owner_core = ["organisation.business_name", "organisation.public_business_location", "organisation.stable_type"]
    cases = [
        ("farrier_named_email_ready", fixture("farrier_named_email_ready", "farrier", "named_target", farrier_core + named + ["person.business_email"]), "review_ready", "review_required"),
        ("farrier_named_phone_ready", fixture("farrier_named_phone_ready", "farrier", "named_target", farrier_core + named + ["person.business_phone"]), "review_ready", "review_required"),
        ("farrier_general_fallback_ready", fixture("farrier_general_fallback_ready", "farrier", "general_organisation_fallback", farrier_core + ["organisation.business_email"], target_role_not_found=True), "review_ready", "review_required"),
        ("horse_owner_named_ready_without_horse_count", fixture("horse_owner_named_ready_without_horse_count", "horse_owner", "named_target", owner_core + named + ["person.business_email"]), "review_ready", "review_required"),
        ("horse_owner_general_fallback_ready", fixture("horse_owner_general_fallback_ready", "horse_owner", "general_organisation_fallback", owner_core + ["organisation.business_phone"], target_role_not_found=True), "review_ready", "review_required"),
        ("farrier_missing_service_area", fixture("farrier_missing_service_area", "farrier", "named_target", [key for key in farrier_core + named + ["person.business_email"] if key != "organisation.service_area"], research_exhausted=False), "incomplete", "enrichment_in_progress"),
        ("farrier_exhausted_missing_service_area", fixture("farrier_exhausted_missing_service_area", "farrier", "named_target", [key for key in farrier_core + named + ["person.business_email"] if key != "organisation.service_area"], research_exhausted=True), "incomplete", "held"),
        ("farrier_missing_all_contact_channels", fixture("farrier_missing_all_contact_channels", "farrier", "named_target", farrier_core + named), "incomplete", "enrichment_in_progress"),
        ("horse_owner_optional_fields_missing", fixture("horse_owner_optional_fields_missing", "horse_owner", "named_target", owner_core + named + ["person.business_phone"], extra_states={"organisation.horse_count": "not_found", "organisation.breeds": "unknown"}), "review_ready", "review_required"),
        ("horse_owner_material_conflict", fixture("horse_owner_material_conflict", "horse_owner", "named_target", owner_core + named + ["person.business_email"], conflicts=["organisation.stable_type"]), "needs_review", "held"),
        ("general_fallback_without_marker", fixture("general_fallback_without_marker", "horse_owner", "general_organisation_fallback", owner_core + ["organisation.business_email"], target_role_not_found=False), "incomplete", "enrichment_in_progress"),
        ("invalid_unknown_segment", fixture("invalid_unknown_segment", "unknown_segment", "named_target", []), "invalid", "processing_failed"),
    ]
    FIXTURES.mkdir(parents=True, exist_ok=True)
    manifest_cases = []
    for name, value, expected_status, expected_workflow in cases:
        path = FIXTURES / f"{name}.json"
        write(path, value)
        manifest_cases.append({
            "name": name,
            "fixture": path.name,
            "expected_package_status": expected_status,
            "expected_workflow_recommendation": expected_workflow,
        })
    write(FIXTURES / "fixture-manifest.json", {"version": "0.1.0-draft.1", "cases": manifest_cases})


def main() -> None:
    packages = build_packages()
    write(PACKAGE_PATH, packages)
    build_fixtures()
    print(json.dumps({
        "package_contract": str(PACKAGE_PATH),
        "version": packages["version"],
        "status": packages["status"],
        "fixture_count": len(load_manifest()["cases"]),
    }, indent=2))


def load_manifest() -> dict:
    return json.loads((FIXTURES / "fixture-manifest.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
