#!/usr/bin/env python3
"""Build the provisional Step 3A Equinet A2 Business Field Catalogue."""

from __future__ import annotations

import csv
import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROFILE_ROOT / "foundations" / "contracts" / "business"
JSON_PATH = ROOT / "a2-business-field-catalogue-0.1.0-draft.1.json"
CSV_PATH = ROOT / "a2-business-field-catalogue-0.1.0-draft.1.csv"

VERSION = "0.1.0-draft.1"
STATUS = "approved_by_unitalk_as_working_baseline_pending_equinet_confirmation"
BOTH = ["farrier", "horse_owner"]


def mapping(object_name: str, *properties: str) -> list[dict]:
    return [
        {
            "system": "hubspot",
            "object": object_name,
            "property": prop,
            "status": "mapping_candidate_only",
        }
        for prop in properties
    ]


def field(
    key: str,
    label: str,
    description: str,
    scope: str,
    value_type: str,
    segments: list[str],
    priorities: dict[str, str],
    *,
    collection: str = "permitted_for_proposal",
    data_category: str = "professional_business_data",
    inference: str = "not_permitted",
    paid_lookup: bool = False,
    enum_values: list[str] | None = None,
    source_text_preserved: bool = True,
    requalification_criteria: list[str] | None = None,
    mappings: list[dict] | None = None,
    approval_rule: str = "human_review_required_during_pilot",
    unknown_behaviour: str = "preserve_unknown_and_record_gap_when_required",
) -> dict:
    return {
        "field_key": key,
        "label": label,
        "description": description,
        "scope": scope,
        "value_type": value_type,
        "allowed_segments": segments,
        "priority_by_segment": priorities,
        "collection_policy": collection,
        "data_category": data_category,
        "inference_policy": inference,
        "paid_lookup_allowed": paid_lookup,
        "enum_values": enum_values,
        "source_text_preserved": source_text_preserved,
        "a1_requalification_criterion_ids": requalification_criteria or [],
        "approval_rule": approval_rule,
        "unknown_behaviour": unknown_behaviour,
        "mapping_candidates": mappings or [],
    }


def build() -> dict:
    fields = [
        field("person.full_name", "Full name", "Published or authorised name of a named professional contact.", "person", "string", BOTH, {"farrier": "required", "horse_owner": "conditional_required"}, mappings=mapping("contact", "firstname", "lastname")),
        field("person.role_title", "Current role title", "Current source wording for the person's professional role.", "person", "string", BOTH, {"farrier": "required", "horse_owner": "conditional_required"}, requalification_criteria=["farrier.buying_influence", "horse_owner.purchasing_influence"], mappings=mapping("contact", "jobtitle")),
        field("person.business_email", "Professional email", "Explicitly published or authorised professional-use email; never a guessed pattern.", "person", "string", BOTH, {"farrier": "conditional_required", "horse_owner": "conditional_required"}, mappings=mapping("contact", "work_email", "email")),
        field("person.personal_email_candidate", "Personal email candidate", "Email returned by the approved independent provider search and held for human privacy review before any operational use.", "person", "string", BOTH, {"farrier": "optional", "horse_owner": "optional"}, collection="review_only_pending_privacy_retention_and_human_decision", data_category="personal_contact_data", paid_lookup=True, mappings=[], approval_rule="explicit_human_privacy_review_required_no_crm_or_outreach"),
        field("person.business_phone", "Professional phone", "Explicitly published or authorised professional business phone.", "person", "string", BOTH, {"farrier": "conditional_required", "horse_owner": "conditional_required"}, mappings=mapping("contact", "phone")),
        field("person.mobile_phone", "Mobile or direct dial", "Mobile or direct-dial number. Disabled until Equinet separately approves the field, source and purpose.", "person", "string", BOTH, {"farrier": "do_not_collect", "horse_owner": "do_not_collect"}, collection="disabled_pending_equinet_privacy_decision", data_category="personal_contact_data", mappings=mapping("contact", "mobilephone")),
        field("person.secondary_email", "Secondary email", "Secondary professional-use email retained only when encountered without paid lookup.", "person", "string", BOTH, {"farrier": "optional", "horse_owner": "optional"}, mappings=mapping("contact", "secondary_email")),
        field("person.professional_status", "Farrier professional status", "Current Farrier working status using the provisional Unitalk taxonomy.", "person", "enum", ["farrier"], {"farrier": "required"}, enum_values=["full_time", "part_time", "student_apprentice"], requalification_criteria=["farrier.professional_activity", "farrier.apprentice_future_potential", "farrier.inactive_or_hobbyist"], mappings=mapping("contact", "farrier_active_flag")),
        field("person.professional_credential", "Primary professional credential", "One primary current professional credential retained for compatibility with the canonical fixture contract.", "person", "string", ["farrier"], {"farrier": "optional"}, mappings=mapping("contact", "farrier_certifications")),
        field("person.certifications", "Professional certifications", "Current explicitly verified Farrier certifications or memberships.", "person", "string_array", ["farrier"], {"farrier": "optional"}, mappings=mapping("contact", "farrier_certifications")),
        field("person.years_experience", "Years of experience", "Explicitly stated professional years of experience; never derived from age or graduation year without an approved rule.", "person", "integer", ["farrier"], {"farrier": "optional"}, mappings=mapping("contact", "years_experience")),
        field("person.public_profile_urls", "Public professional profile URLs", "Role-relevant public profile URLs collected manually or through an approved official API. Exact HubSpot property mapping remains pending Step 3G verification.", "person", "string_array", BOTH, {"farrier": "optional", "horse_owner": "optional"}, mappings=[]),
        field("person.recent_professional_activity", "Recent professional activity", "Dated public professional activity kept separate from private interests and CRM engagement.", "person", "structured", BOTH, {"farrier": "optional", "horse_owner": "optional"}, mappings=[]),
        field("person.social_signals", "Broad social signals", "Broad social metrics or inferred interests. Disabled until a permitted signal, purpose and access route are approved.", "person", "structured", BOTH, {"farrier": "do_not_collect", "horse_owner": "do_not_collect"}, collection="disabled_pending_source_and_purpose_approval", data_category="social_platform_data"),
        field("organisation.business_name", "Organisation or business name", "Verified public or authorised trading/business name.", "organisation", "string", BOTH, {"farrier": "required", "horse_owner": "required"}, mappings=mapping("company", "name", "trade_name")),
        field("organisation.website", "Official website", "Verified official business website URL.", "organisation", "string", BOTH, {"farrier": "optional", "horse_owner": "optional"}, mappings=mapping("company", "website")),
        field("organisation.website_domain", "Official website domain", "Normalised official domain used as one identity signal, never as a unique match by itself.", "organisation", "string", BOTH, {"farrier": "optional", "horse_owner": "optional"}, mappings=mapping("company", "domain")),
        field("organisation.business_phone", "Organisation general phone", "General published business phone used as a fallback when no named target-role channel is available.", "organisation", "string", BOTH, {"farrier": "conditional_required", "horse_owner": "conditional_required"}, mappings=mapping("company", "phone")),
        field("organisation.business_email", "Organisation general email", "General published business email used as a fallback when no named target-role channel is available.", "organisation", "string", BOTH, {"farrier": "conditional_required", "horse_owner": "conditional_required"}, mappings=mapping("company", "company_email")),
        field("organisation.public_business_location", "Public business location", "Structured public business location; proposed routing minimum is country and state.", "organisation", "structured", BOTH, {"farrier": "required", "horse_owner": "required"}, mappings=mapping("company", "address", "city", "state", "zip", "country")),
        field("organisation.service_area", "Farrier service area", "Explicit service regions stored as structured region labels plus preserved source wording.", "organisation", "string_array", ["farrier"], {"farrier": "required"}, requalification_criteria=["farrier.high_value_service_area"], mappings=[]),
        field("organisation.disciplines", "Equine disciplines", "Explicit professional or organisation disciplines; multiple values permitted.", "organisation", "string_array", BOTH, {"farrier": "required", "horse_owner": "optional"}, requalification_criteria=["farrier.sport_horse_focus", "horse_owner.performance_discipline"], mappings=mapping("contact", "disciplines_worked_with", "owner_primary_discipline")),
        field("organisation.horse_count", "Verified exact horse count", "Exact count only when explicitly stated by an approved source or confirmed by Equinet; never inferred.", "organisation", "integer", ["horse_owner"], {"horse_owner": "optional"}, requalification_criteria=["horse_owner.more_than_three_horses"], mappings=mapping("contact", "owner_horse_count")),
        field("organisation.horse_count_band", "A2 horse-count review band", "A2-only category deterministically derived from a verified exact count; not written to HubSpot during the no-integration pilot.", "organisation", "enum", ["horse_owner"], {"horse_owner": "optional"}, enum_values=["1", "2_4", "5_10", "11_25", "26_50", "51_plus"], inference="deterministic_derivation_from_verified_exact_count_only", source_text_preserved=False, requalification_criteria=["horse_owner.more_than_three_horses"], mappings=mapping("contact", "horse_count_range")),
        field("organisation.stable_type", "Stable or farm type", "Normalised organisation type using the provisional Unitalk taxonomy.", "organisation", "enum", ["horse_owner"], {"horse_owner": "required"}, enum_values=["private_farm", "boarding", "training", "breeding", "backyard", "other"], mappings=mapping("contact", "stable_type")),
        field("organisation.breeds", "Horse breeds", "Explicitly stated horse breeds relevant to the organisation.", "organisation", "string_array", ["horse_owner"], {"horse_owner": "optional"}, mappings=mapping("contact", "owner_breeds")),
        field("organisation.horses_served_per_month", "Horses served per month", "Aggregate Farrier business volume. Disabled until Equinet confirms a use case and permitted source.", "organisation", "integer", ["farrier"], {"farrier": "do_not_collect"}, collection="disabled_pending_equinet_use_case_and_source", mappings=mapping("contact", "farrier_horses_served")),
        field("organisation.client_base_summary", "Aggregate client-base summary", "Aggregate business client types or size only; named client identities are prohibited.", "organisation", "structured", ["farrier"], {"farrier": "do_not_collect"}, collection="disabled_pending_equinet_use_case_and_source"),
        field("relationship.role", "Person-to-organisation role", "Verified relationship role between a retained person and organisation.", "relationship", "string", BOTH, {"farrier": "optional", "horse_owner": "optional"}),
        field("relationship.target_role_priority", "Target-role priority", "Normalised Unitalk role priority derived from the approved targeting table.", "relationship", "enum", BOTH, {"farrier": "conditional_required", "horse_owner": "conditional_required"}, enum_values=["primary", "secondary", "review_only", "excluded", "target_role_not_found"], inference="deterministic_mapping_from_verified_current_role", source_text_preserved=False),
        field("relationship.buying_role_recommendation", "Buying-role recommendation", "Non-binding recommendation derived from a verified role; human approval is required before CRM mapping.", "relationship", "enum", BOTH, {"farrier": "optional", "horse_owner": "optional"}, enum_values=["decision_maker", "influencer", "user", "unknown"], inference="bounded_recommendation_from_verified_role", source_text_preserved=False, mappings=mapping("contact", "hs_buying_role")),
        field("network.mutual_connections", "Mutual connections", "Mutual-connection information. Disabled until an authorised official source, account, purpose and storage rule are approved.", "network", "structured", BOTH, {"farrier": "do_not_collect", "horse_owner": "do_not_collect"}, collection="disabled_pending_official_integration_and_storage_approval", data_category="network_relationship_data"),
    ]

    return {
        "catalogue_id": "equinet-a2-business-field-catalogue",
        "version": VERSION,
        "status": STATUS,
        "profile": "equinet-a2-enrichment",
        "canonical_schema_version": "1.0.0",
        "decision_basis": {
            "authority": "Unitalk working baseline approved by Séverine for Step 3B draft preparation",
            "unitalk_approver": "Séverine, Unitalk Operations",
            "unitalk_approved_at": "2026-08-26T16:49:28Z",
            "equinet_confirmation": "pending",
            "approved_for_live_collection": False,
            "approved_for_pilot": False,
            "approved_for_crm_write": False,
        },
        "segments": ["farrier", "horse_owner"],
        "priority_values": ["required", "conditional_required", "optional", "do_not_collect"],
        "target_role_model": {
            "farrier": {
                "primary": ["independent_farrier_owner", "farrier_business_owner_founder", "lead_farrier"],
                "secondary": ["business_office_administrator"],
                "review_only": ["student_apprentice"],
                "excluded": [],
            },
            "horse_owner": {
                "primary": ["owner_founder", "farm_stable_owner", "farm_stable_manager", "trainer_head_trainer", "breeding_manager"],
                "secondary": ["general_manager", "operations_manager"],
                "review_only": [],
                "excluded": [],
            },
            "source_role_title_must_be_preserved": True,
            "buying_role_is_recommendation_only": True,
        },
        "contact_selection_policy": {
            "maximum_named_contacts": 3,
            "primary_target_role_contacts": 1,
            "additional_role_relevant_contacts": 2,
            "fallback_when_no_target_role": "retain_general_organisation_contact_and_mark_target_role_not_found",
            "minimum_review_contactability": "verified_professional_email_or_verified_business_phone",
            "general_organisation_contact_can_satisfy_review_readiness": True,
            "review_readiness_does_not_establish_outreach_eligibility": True,
        },
        "missing_required_field_policy": {
            "field_quality_status": "gap",
            "record_data_quality_status": "incomplete",
            "automatic_rejection": False,
            "automatic_a1_score_change": False,
            "external_action_authorized": False,
            "visible_in_review_package": True,
            "permitted_workflow_outcomes": ["enrichment_in_progress", "held", "changes_requested"],
            "resolution_options": ["approved_targeted_research", "human_correction", "documented_exception"],
        },
        "horse_count_policy": {
            "exact_count_authority": "verified_explicit_value_only",
            "inference_prohibited": True,
            "derived_band_use": "a2_review_only",
            "bands": [
                {"value": "1", "minimum": 1, "maximum": 1},
                {"value": "2_4", "minimum": 2, "maximum": 4},
                {"value": "5_10", "minimum": 5, "maximum": 10},
                {"value": "11_25", "minimum": 11, "maximum": 25},
                {"value": "26_50", "minimum": 26, "maximum": 50},
                {"value": "51_plus", "minimum": 51, "maximum": None},
            ],
            "hubspot_horse_count_range": "protected_baseline_no_write",
            "new_hubspot_property_proposed": False,
        },
        "collection_boundaries": {
            "reuse_a1_before_new_research": True,
            "new_research_requires_named_gap_conflict_verification_or_freshness_need": True,
            "public_professional_information_does_not_create_outreach_eligibility": True,
            "personal_email_and_mobile_paid_discovery": "disabled_pending_equinet_approval",
            "automated_linkedin_or_social_extraction": "blocked_pending_rights_and_integration_approval",
            "named_client_identity_collection": "prohibited",
            "crm_mapping_candidates_are_not_write_authority": True,
        },
        "fields": fields,
        "open_equinet_confirmations": [
            "target role model by segment",
            "maximum named contacts and fallback",
            "minimum review contactability",
            "horse-count taxonomy and derivation",
            "Required, Conditional Required, Optional and Do Not Collect classifications",
            "personal email and mobile/direct-dial policy before pilot",
            "A2 business reviewer and backup before pilot",
        ],
        "next_gate_after_approval": "Step 3B — Minimum Data Packages",
    }


def write_csv(catalogue: dict) -> None:
    columns = [
        "field_key", "label", "scope", "value_type", "allowed_segments", "farrier_priority",
        "horse_owner_priority", "collection_policy", "data_category", "inference_policy",
        "paid_lookup_allowed", "enum_values", "a1_requalification_criterion_ids",
        "approval_rule", "unknown_behaviour", "mapping_candidates", "description",
    ]
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for item in catalogue["fields"]:
            writer.writerow({
                "field_key": item["field_key"],
                "label": item["label"],
                "scope": item["scope"],
                "value_type": item["value_type"],
                "allowed_segments": json.dumps(item["allowed_segments"], separators=(",", ":")),
                "farrier_priority": item["priority_by_segment"].get("farrier", "not_applicable"),
                "horse_owner_priority": item["priority_by_segment"].get("horse_owner", "not_applicable"),
                "collection_policy": item["collection_policy"],
                "data_category": item["data_category"],
                "inference_policy": item["inference_policy"],
                "paid_lookup_allowed": str(item["paid_lookup_allowed"]).lower(),
                "enum_values": json.dumps(item["enum_values"], separators=(",", ":")),
                "a1_requalification_criterion_ids": json.dumps(item["a1_requalification_criterion_ids"], separators=(",", ":")),
                "approval_rule": item["approval_rule"],
                "unknown_behaviour": item["unknown_behaviour"],
                "mapping_candidates": json.dumps(item["mapping_candidates"], separators=(",", ":")),
                "description": item["description"],
            })


def main() -> None:
    catalogue = build()
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(catalogue, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(catalogue)
    print(json.dumps({
        "catalogue": str(JSON_PATH),
        "csv": str(CSV_PATH),
        "version": VERSION,
        "status": STATUS,
        "field_count": len(catalogue["fields"]),
    }, indent=2))


if __name__ == "__main__":
    main()
