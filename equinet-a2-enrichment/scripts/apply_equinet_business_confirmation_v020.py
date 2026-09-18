#!/usr/bin/env python3
"""Publish Equinet-confirmed A2 business contracts version 0.2.0."""
from __future__ import annotations

import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAMP = "2026-08-30T17:05:11Z"
VERSION = "0.2.0"


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def dump(rel: str, value: dict) -> Path:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_cell(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def write_catalogue_csv(path: Path, fields: list[dict]) -> None:
    columns = [
        "field_key", "label", "scope", "value_type", "allowed_segments", "farrier_priority",
        "horse_owner_priority", "collection_policy", "data_category", "inference_policy",
        "paid_lookup_allowed", "enum_values", "a1_requalification_criterion_ids", "approval_rule",
        "unknown_behaviour", "mapping_candidates", "description",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for f in fields:
            writer.writerow({
                "field_key": f["field_key"], "label": f["label"], "scope": f["scope"],
                "value_type": f["value_type"], "allowed_segments": json_cell(f["allowed_segments"]),
                "farrier_priority": f.get("priority_by_segment", {}).get("farrier", "not_applicable"),
                "horse_owner_priority": f.get("priority_by_segment", {}).get("horse_owner", "not_applicable"),
                "collection_policy": f["collection_policy"], "data_category": f["data_category"],
                "inference_policy": f["inference_policy"], "paid_lookup_allowed": json_cell(f["paid_lookup_allowed"]),
                "enum_values": json_cell(f["enum_values"]),
                "a1_requalification_criterion_ids": json_cell(f["a1_requalification_criterion_ids"]),
                "approval_rule": f["approval_rule"], "unknown_behaviour": f["unknown_behaviour"],
                "mapping_candidates": json_cell(f["mapping_candidates"]), "description": f["description"],
            })


def write_source_csv(path: Path, sources: list[dict]) -> None:
    columns = ["source_id", "name", "source_type", "canonical_url", "business_approval",
               "source_rights_preflight", "runtime_readiness", "register_status", "purpose",
               "allowed_access_modes", "permitted_fields", "prohibited_fields", "limits", "notes"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for s in sources:
            row = {key: s.get(key) for key in columns}
            for key in ["allowed_access_modes", "permitted_fields", "prohibited_fields", "limits", "notes"]:
                row[key] = json_cell(row[key])
            row["canonical_url"] = json_cell(row["canonical_url"]) if row["canonical_url"] is None else row["canonical_url"]
            writer.writerow(row)


def write_mapping_csv(path: Path, mappings: list[dict]) -> None:
    columns = ["canonical_field", "scope", "value_type", "allowed_segments", "mapping_status", "direction",
               "hubspot_destinations", "conversion", "baseline_authority", "populated_manual_value",
               "workflow_dependency_status", "write_authorized"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for m in mappings:
            row = {key: m.get(key) for key in columns}
            for key in ["allowed_segments", "hubspot_destinations"]:
                row[key] = json_cell(row[key])
            row["write_authorized"] = json_cell(row["write_authorized"])
            writer.writerow(row)


def field(index: dict[str, dict], key: str) -> dict:
    if key not in index:
        raise KeyError(key)
    return index[key]


def main() -> int:
    decision = {
        "record_type": "equinet_a2_business_confirmation",
        "decision_id": "A2-EQUINET-ROLES-CONTACTS-HORSEOWNER-20260830",
        "recorded_at": STAMP,
        "recorded_by": {"name": "Séverine", "role": "Unitalk Operations"},
        "client_authority": "Equinet-confirmed business requirements relayed by Séverine",
        "named_equinet_approver": None,
        "source_reference": "Unitalk implementation conversation; original Equinet message/reference to be attached when available",
        "scope": ["target_roles", "contact_selection", "horse_owner_priorities", "horse_count", "contact_and_location_completeness", "single_final_review"],
        "decisions": {
            "contact_selection": {
                "default_named_contacts": 1,
                "maximum_named_contacts": 2,
                "second_contact_conditions": ["large_organisation", "shared_purchasing_or_operational_responsibility"],
                "no_suitable_contact": "contact_needed_human_review_no_unrelated_role_outreach",
            },
            "horse_owner_required": ["person.role_title", "organisation.stable_type", "organisation.horse_count", "organisation.breeds", "organisation.public_business_location"],
            "contact_channels": "attempt_both_professional_email_and_business_phone; at_least_one_satisfies_minimum_when_the_other_is_not_available",
            "location": "attempt_complete_address; state_and_country_are_the_minimum",
            "breeds": "at_least_one_verified_value; preserve Mixed or Other when verified",
            "horse_count": "existing HubSpot owner_horse_count is authoritative; net-new prospects may use explicit approved evidence; never infer; ignore horse_count_range; do not derive horse_count_band",
            "missing_information": "always present the consolidated human review; allow a documented collect_during_discovery disposition without changing A1 score",
            "crm_sync": "only after final human review, active HubSpot integration, guarded write and read-back reconciliation",
        },
        "external_actions_authorized": False,
        "hubspot_write_authorized": False,
        "production_acceptance": False,
    }
    decision_path = dump("foundations/decisions/A2-EQUINET-BUSINESS-CONFIRMATION-20260830.json", decision)

    old_cat = load("foundations/contracts/business/a2-business-field-catalogue-0.1.1-draft.1.json")
    cat = deepcopy(old_cat)
    cat["version"] = VERSION
    cat["status"] = "equinet_confirmed_unitalk_implemented_no_integration"
    cat["decision_basis"] = {
        "authority": "Equinet-confirmed business requirements relayed by Séverine and implemented by Unitalk Operations",
        "unitalk_approver": "Séverine, Unitalk Operations",
        "unitalk_approved_at": STAMP,
        "equinet_confirmation": "confirmed_via_unitalk_operations",
        "decision_record": str(decision_path.relative_to(ROOT)),
        "decision_record_sha256": sha(decision_path),
        "approved_for_live_collection": False,
        "approved_for_pilot": True,
        "approved_for_crm_write": False,
    }
    cat["target_role_model"] = {
        "farrier": {
            "primary": ["independent_self_employed_farrier", "farrier_business_owner", "farrier_business_founder_cofounder", "lead_head_farrier", "professional_farrier"],
            "secondary": ["associate_staff_farrier", "multi_farrier_practice_farrier", "business_office_practice_manager_with_commercial_responsibility"],
            "review_only": ["apprentice_student_farrier"],
            "excluded": ["farrier_instructor_educator_without_current_commercial_activity", "retired_inactive_farrier_without_current_professional_activity"],
        },
        "horse_owner": {
            "primary": ["owner_horse_owner", "farm_owner_manager", "stable_owner_manager", "equestrian_centre_owner_manager", "breeding_farm_owner_manager", "equine_business_managing_director_general_manager", "operations_manager_with_horse_care_or_purchasing_responsibility"],
            "secondary": ["head_trainer_head_coach", "trainer_professional_rider", "barn_yard_manager", "equine_program_manager", "purchasing_procurement_manager", "assistant_manager_operations_coordinator_with_purchasing_responsibility"],
            "review_only": [],
            "excluded": [],
        },
        "conditional_evidence_rules": {
            "business_office_practice_manager_with_commercial_responsibility": "commercial_or_purchasing_responsibility_required",
            "operations_manager_with_horse_care_or_purchasing_responsibility": "horse_care_or_purchasing_responsibility_required",
            "assistant_manager_operations_coordinator_with_purchasing_responsibility": "purchasing_responsibility_required",
            "farrier_instructor_educator_without_current_commercial_activity": "exclude_only_when_no_current_commercial_or_professional_farrier_activity",
            "retired_inactive_farrier_without_current_professional_activity": "exclude_only_when_no_current_professional_activity",
        },
        "source_role_title_must_be_preserved": True,
        "buying_role_is_recommendation_only": True,
        "a2_excluded_role_action": "hold_and_create_requalification_signal_for_a1",
    }
    cat["contact_selection_policy"] = {
        "default_named_contacts": 1,
        "maximum_named_contacts": 2,
        "primary_target_role_contacts": 1,
        "additional_role_relevant_contacts": 1,
        "second_contact_requires_reason": True,
        "second_contact_allowed_reasons": ["large_organisation", "shared_purchasing_or_operational_responsibility"],
        "fallback_when_no_target_role": "retain_organisation_information_mark_contact_needed_and_continue_review",
        "contact_needed_review_label": "Contact Needed / Needs Review",
        "unrelated_role_cannot_satisfy_contact_need": True,
        "attempt_both_contact_channels": ["person.business_email", "person.business_phone"],
        "minimum_review_contactability": "verified_professional_email_or_verified_business_phone",
        "general_organisation_contact_can_satisfy_review_readiness": False,
        "review_readiness_does_not_establish_outreach_eligibility": True,
    }
    cat["horse_count_policy"] = {
        "exact_count_authority_order": ["hubspot_owner_horse_count_for_existing_matched_record", "approved_explicit_evidence_for_net_new_or_empty_hubspot_value"],
        "net_new_permitted_explicit_sources": ["a1_approved_handoff", "equinet_authorized_first_party_data", "equinet_representative_confirmation", "prospect_official_website"],
        "inference_prohibited": True,
        "hubspot_property": "Contact.owner_horse_count",
        "existing_hubspot_value_is_authoritative": True,
        "conflict_action": "preserve_hubspot_and_hold_for_human_review",
        "sync_only_after_final_human_review": True,
        "horse_count_range": "ignored_not_used_for_determination_or_sync",
        "derived_band_use": "disabled",
        "bands": [],
        "historical_band_values_preserved": True,
        "new_hubspot_property_proposed": False,
    }
    cat["missing_required_field_policy"]["research_exhausted_workflow"] = "review_required"
    cat["missing_required_field_policy"]["human_dispositions"] = ["needs_changes", "held", "approved_collect_during_discovery", "rejected_for_explicit_business_reason"]
    cat["missing_required_field_policy"]["approved_collect_during_discovery_preserves_incomplete_status"] = True

    idx = {f["field_key"]: f for f in cat["fields"]}
    field(idx, "person.role_title")["priority_by_segment"]["horse_owner"] = "required"
    field(idx, "organisation.horse_count")["priority_by_segment"]["horse_owner"] = "required"
    field(idx, "organisation.horse_count")["description"] = "Verified exact count. Existing matched HubSpot Contact.owner_horse_count is authoritative; net-new prospects may use explicit approved evidence. Never inferred."
    field(idx, "organisation.horse_count")["inference_policy"] = "explicit_value_only_with_hubspot_precedence_for_existing_record"
    field(idx, "organisation.horse_count_band")["priority_by_segment"]["horse_owner"] = "do_not_collect"
    field(idx, "organisation.horse_count_band")["collection_policy"] = "disabled_deprecated_historical_only"
    field(idx, "organisation.horse_count_band")["description"] = "Deprecated historical A2 field. Do not create new values; horse_count_range is ignored."
    field(idx, "organisation.horse_count_band")["mapping_candidates"] = []
    field(idx, "organisation.breeds")["priority_by_segment"]["horse_owner"] = "required"
    field(idx, "organisation.breeds")["description"] = "At least one explicitly verified breed value is required for Horse Owner enrichment completeness. Preserve verified Mixed or Other values as stated."
    location = field(idx, "organisation.public_business_location")
    location["description"] = "Structured public business location. Attempt the complete address when available; state and country are the minimum verified components."
    location["structured_requirements"] = {"minimum_verified_components": ["state", "country"], "preferred_components": ["address", "city", "state", "postal_code", "country"]}
    for key in ["person.business_email", "person.business_phone"]:
        field(idx, key)["contact_channel_policy"] = "attempt_both_if_available_at_least_one_required"

    cat_path = dump("foundations/contracts/business/a2-business-field-catalogue-0.2.0.json", cat)
    cat_csv = ROOT / "foundations/contracts/business/a2-business-field-catalogue-0.2.0.csv"
    write_catalogue_csv(cat_csv, cat["fields"])

    old_pkg = load("foundations/contracts/business/a2-minimum-data-packages-0.1.1-draft.1.json")
    pkg = deepcopy(old_pkg)
    pkg["version"] = VERSION
    pkg["status"] = "equinet_confirmed_unitalk_implemented_no_integration"
    pkg["business_field_catalogue"] = {"path": str(cat_path.relative_to(ROOT)), "version": VERSION, "sha256": sha(cat_path), "status": cat["status"]}
    pkg["global_rules"]["research_exhausted_with_gap_workflow"] = "review_required"
    pkg["global_rules"]["review_required_even_when_incomplete"] = True
    pkg["global_rules"]["human_dispositions"] = ["needs_changes", "held", "approved_collect_during_discovery", "rejected_for_explicit_business_reason"]
    pkg["global_rules"]["approved_collect_during_discovery"] = {"allowed": True, "preserve_data_quality": "incomplete", "automatic_outreach": False, "automatic_crm_write": False}
    for package in pkg["packages"].values():
        named = package["contact_paths"]["named_target"]
        named["preferred_verified_fields"] = ["person.business_email", "person.business_phone"]
        named["at_least_one_verified_field"] = ["person.business_email", "person.business_phone"]
        fallback = package["contact_paths"].pop("general_organisation_fallback")
        package["contact_paths"]["contact_needed"] = {
            "required_flags": {"target_role_not_found": True},
            "research_target_fields": ["person.full_name", "person.role_title", "relationship.target_role_priority", "person.business_email", "person.business_phone"],
            "retained_information_fields": ["organisation.business_email", "organisation.business_phone"],
            "review_ready_allowed": False,
            "review_label": "Contact Needed / Needs Review",
            "unrelated_role_cannot_satisfy": True,
            "research_exhausted_workflow": "review_required",
        }
    owner = pkg["packages"]["horse_owner_review_ready"]
    owner["required_verified_fields"] = ["organisation.business_name", "organisation.public_business_location", "organisation.stable_type", "organisation.horse_count", "organisation.breeds"]
    owner["explicit_horse_count_required"] = True
    owner["horse_count_range_used"] = False
    owner["location_rule"] = {"attempt_complete_address": True, "minimum_verified_components": ["state", "country"]}
    pkg["approval_boundary"] = {
        "unitalk_status": "approved_and_implemented",
        "unitalk_approver": "Séverine, Unitalk Operations",
        "unitalk_approved_at": STAMP,
        "equinet_confirmation": "confirmed_via_unitalk_operations",
        "decision_record": str(decision_path.relative_to(ROOT)),
        "live_use_authorized": False,
        "external_actions_authorized": False,
        "next_gate_after_approval": "Step 10 — Integrations",
    }
    pkg.pop("clarification", None)
    pkg_path = dump("foundations/contracts/business/a2-minimum-data-packages-0.2.0.json", pkg)

    old_src = load("foundations/contracts/sources/a2-source-register-0.1.1-draft.1.json")
    src = deepcopy(old_src)
    src["version"] = VERSION
    src["status"] = "equinet_confirmed_business_scope_runtime_activation_pending"
    src["decision_record"] = {"path": str(decision_path.relative_to(ROOT)), "sha256": sha(decision_path)}
    sidx = {s["source_id"]: s for s in src["sources"]}
    website = sidx["prospect_official_website"]
    if "explicit horse breeds" not in website["permitted_fields"]:
        website["permitted_fields"].append("explicit horse breeds")
    website["notes"].append("An explicit horse count may support a net-new prospect only; an existing matched HubSpot owner_horse_count remains authoritative.")
    hubspot = sidx["hubspot_authoritative_records"]
    hubspot["permitted_fields"] = ["approved Contact, Company and Deal properties", "Contact.owner_horse_count", "Contact.owner_breeds"]
    hubspot["notes"].append("For an existing matched record, Contact.owner_horse_count is authoritative for horse count.")
    harvest = sidx["apify_harvestapi_linkedin_profile_search"]
    harvest["limits"]["max_retained_contacts_per_candidate"] = 2
    harvest["notes"].append("Retain one named contact by default and at most two when a large organisation or shared responsibility is documented.")
    src_path = dump("foundations/contracts/sources/a2-source-register-0.2.0.json", src)
    src_csv = ROOT / "foundations/contracts/sources/a2-source-register-0.2.0.csv"
    write_source_csv(src_csv, src["sources"])

    old_provider = load("foundations/contracts/governance/a2-provider-and-cost-policy-0.1.1-draft.1.json")
    provider = deepcopy(old_provider)
    provider["version"] = VERSION
    provider["status"] = "equinet_confirmed_business_scope_runtime_activation_pending"
    provider["dependencies"][0] = {"path": str(src_path.relative_to(ROOT)), "sha256": sha(src_path)}
    provider["providers"]["apify_linkedin_profile_search"]["limits"]["max_retained_contacts"] = 2
    provider["providers"]["apify_linkedin_profile_search"]["limits"]["default_retained_contacts"] = 1
    provider["providers"]["apify_linkedin_profile_search"]["limits"]["second_contact_requires_reason"] = True
    provider_path = dump("foundations/contracts/governance/a2-provider-and-cost-policy-0.2.0.json", provider)

    old_map = load("foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.1.1-draft.1.json")
    mapping = deepcopy(old_map)
    mapping["version"] = VERSION
    mapping["status"] = "equinet_confirmed_business_mapping_live_verification_pending"
    mapping["dependencies"] = [
        {"path": str(cat_path.relative_to(ROOT)), "sha256": sha(cat_path)},
        *[d for d in mapping.get("dependencies", []) if "business-field-catalogue" not in d.get("path", "")],
    ]
    mapping["known_blockers"] = [b for b in mapping.get("known_blockers", []) if "horse_count_range" not in b]
    midx = {m["canonical_field"]: m for m in mapping["mappings"]}
    hc = midx["organisation.horse_count"]
    hc.update({
        "mapping_status": "equinet_confirmed_live_verification_pending",
        "direction": "read_authoritative_existing_or_propose_net_new_after_review",
        "conversion": "direct_integer",
        "baseline_authority": "hubspot_owner_horse_count_for_existing_match_else_approved_explicit_evidence",
        "populated_manual_value": "preserve_hubspot_and_hold_on_difference",
    })
    band = midx["organisation.horse_count_band"]
    band.update({"mapping_status": "deprecated_ignored", "direction": "none", "hubspot_destinations": [], "conversion": "none", "baseline_authority": "not_applicable", "populated_manual_value": "preserve_historical_only", "workflow_dependency_status": "not_applicable", "write_authorized": False})
    breeds = midx["organisation.breeds"]
    breeds["mapping_status"] = "equinet_confirmed_live_conversion_verification_pending"
    mapping["horse_count_sync_policy"] = {
        "existing_record_read_authority": "Contact.owner_horse_count",
        "net_new_proposal_sources": cat["horse_count_policy"]["net_new_permitted_explicit_sources"],
        "write_gate": "final_human_review_plus_active_guarded_hubspot_write_plus_read_back",
        "horse_count_range": "ignored",
    }
    map_path = dump("foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.2.0.json", mapping)
    map_csv = ROOT / "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.2.0.csv"
    write_mapping_csv(map_csv, mapping["mappings"])

    snapshot_dir = ROOT / "evaluations/equinet-business-confirmation-20260830/pre-change"
    snapshot_files = sorted(p for p in snapshot_dir.iterdir() if p.is_file())
    snapshot_manifest = {
        "record_type": "pre_change_snapshot_manifest",
        "created_at": STAMP,
        "files": [{"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size, "sha256": sha(p)} for p in snapshot_files],
    }
    dump("evaluations/equinet-business-confirmation-20260830/pre-change-manifest.json", snapshot_manifest)

    result = {
        "status": "contracts_published",
        "version": VERSION,
        "decision": str(decision_path.relative_to(ROOT)),
        "outputs": [str(p.relative_to(ROOT)) for p in [cat_path, cat_csv, pkg_path, src_path, src_csv, provider_path, map_path, map_csv]],
        "counts": {"fields": len(cat["fields"]), "sources": len(src["sources"]), "mappings": len(mapping["mappings"]), "max_named_contacts": 2},
        "external_actions": 0,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
