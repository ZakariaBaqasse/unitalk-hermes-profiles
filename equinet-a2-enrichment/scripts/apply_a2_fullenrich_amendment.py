#!/usr/bin/env python3
"""Apply the approved 2026-09-06 FullEnrich foundation amendment."""
from __future__ import annotations

import copy
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STAMP = "2026-09-06T13:07:00Z"
DECISION_ID = "A2-FULLENRICH-SOURCE-ROUTING-20260906"
OLD_VERSION = "0.2.0"
NEW_VERSION = "0.3.0"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_required(text: str, old: str, new: str) -> str:
    if old not in text:
        raise ValueError(f"required text not found: {old[:120]}")
    return text.replace(old, new)


def write_source_csv(register: dict[str, Any], path: Path) -> None:
    fields = ["source_id", "name", "source_type", "canonical_url", "business_approval", "source_rights_preflight", "runtime_readiness", "register_status", "purpose", "allowed_access_modes", "permitted_fields", "prohibited_fields", "limits", "notes"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for source in register["sources"]:
            row = {}
            for field in fields:
                value = source.get(field)
                row[field] = json.dumps(value, ensure_ascii=False, separators=(",", ":")) if isinstance(value, (list, dict)) or value is None else value
            writer.writerow(row)


def write_catalogue_csv(catalogue: dict[str, Any], path: Path) -> None:
    fields = ["field_key", "label", "scope", "value_type", "allowed_segments", "farrier_priority", "horse_owner_priority", "collection_policy", "data_category", "inference_policy", "paid_lookup_allowed", "enum_values", "a1_requalification_criterion_ids", "approval_rule", "unknown_behaviour", "mapping_candidates", "description"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for field in catalogue["fields"]:
            priority = field.get("priority_by_segment", {})
            row = {
                "field_key": field.get("field_key"), "label": field.get("label"), "scope": field.get("scope"), "value_type": field.get("value_type"),
                "allowed_segments": json.dumps(field.get("allowed_segments"), ensure_ascii=False, separators=(",", ":")),
                "farrier_priority": priority.get("farrier", "not_applicable"), "horse_owner_priority": priority.get("horse_owner", "not_applicable"),
                "collection_policy": field.get("collection_policy"), "data_category": field.get("data_category"), "inference_policy": field.get("inference_policy"),
                "paid_lookup_allowed": str(bool(field.get("paid_lookup_allowed"))).lower(),
                "enum_values": json.dumps(field.get("enum_values"), ensure_ascii=False, separators=(",", ":")),
                "a1_requalification_criterion_ids": json.dumps(field.get("a1_requalification_criterion_ids", []), ensure_ascii=False, separators=(",", ":")),
                "approval_rule": field.get("approval_rule"), "unknown_behaviour": field.get("unknown_behaviour"),
                "mapping_candidates": json.dumps(field.get("mapping_candidates", []), ensure_ascii=False, separators=(",", ":")),
                "description": field.get("description"),
            }
            writer.writerow(row)


def write_mapping_csv(mapping: dict[str, Any], path: Path) -> None:
    fields = ["canonical_field", "scope", "value_type", "allowed_segments", "mapping_status", "direction", "hubspot_destinations", "conversion", "baseline_authority", "populated_manual_value", "workflow_dependency_status", "write_authorized"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in mapping["mappings"]:
            row = {key: item.get(key) for key in fields}
            for key in ["allowed_segments", "hubspot_destinations"]:
                row[key] = json.dumps(row[key], ensure_ascii=False, separators=(",", ":"))
            row["write_authorized"] = str(bool(row["write_authorized"])).lower()
            writer.writerow(row)


def common_source_fields() -> dict[str, Any]:
    return {
        "stop_conditions": [
            "authentication_failure", "rate_limit", "unexpected_personal_data",
            "scope_or_credit_limit", "provider_policy_failure", "integration_error"
        ],
        "audit_requirements": [
            "actor_profile", "trigger", "timestamp", "source_id", "provider_endpoint",
            "input_scope", "provider_request_id", "output_reference", "approval_state",
            "status", "retries", "credits_before", "credits_used", "credits_after"
        ],
    }


def build_decision() -> tuple[dict[str, Any], str]:
    decision = {
        "record_type": "equinet_a2_fullenrich_source_routing_confirmation",
        "decision_id": DECISION_ID,
        "recorded_at": STAMP,
        "recorded_by": {"name": "Séverine", "role": "Unitalk Operations"},
        "client_authority": "Equinet-confirmed requirements relayed by Séverine",
        "scope": ["source_sequence", "fullenrich_operations", "target_role_search", "contact_limits", "mobile_phone", "personal_email", "n8n_integration_direction"],
        "decisions": {
            "equinet_first_party_enrichment_data": "not_available",
            "new_external_source_sequence": ["prospect_official_website", "fullenrich", "apify_harvestapi_if_separately_gated"],
            "people_search": {
                "trigger": "no_suitable_named_contact_after_official_website",
                "exact_organisation_domain_required": True,
                "approved_target_role_required": True,
                "default_result_limit": 1,
                "next_role_specific_search_allowed_when_no_suitable_person_returned": True,
                "maximum_unique_people_returned_and_retained_per_prospect": 2,
                "second_contact_requires": ["large_organisation", "shared_purchasing_or_operational_responsibility"],
                "broad_role_free_search": False,
            },
            "people_lookup": {
                "trigger": "known_contact_name_with_identity_or_current_role_not_sufficiently_verified",
                "maximum_results": 1,
                "skip_when_name_role_and_organisation_are_already_verified": True,
            },
            "contact_enrichment": {
                "selected_contacts_only": True,
                "requested_fields": ["contact.work_emails", "contact.phones"],
                "personal_email_requested": False,
                "mobile_phone_permitted_and_desired": True,
                "mobile_absence_blocks_review_by_itself": False,
            },
            "retained_contact_limit": {"default": 1, "maximum": 2, "second_contact_requires_reason": True},
            "apify_fallback": "not_automatic; separate preflight after FullEnrich not_found, insufficient_match or approved technical exhaustion",
            "n8n": "approved target orchestration layer; not connected or runtime-active",
        },
        "external_actions_authorized": False,
        "production_acceptance": False,
    }
    md = f"""# Equinet A2 FullEnrich Source-Routing Decision\n\n**Decision ID:** `{DECISION_ID}`  \n**Recorded at:** `{STAMP}`  \n**Recorded by:** Séverine, Unitalk Operations  \n**Status:** `BUSINESS RULES CONFIRMED — INTEGRATION PENDING`\n\n## Confirmed decisions\n\n- Equinet has no separate first-party enrichment dataset. HubSpot remains the authoritative CRM when connected.\n- New external enrichment follows: prospect official website, FullEnrich, then separately gated Apify/HarvestAPI only when needed.\n- FullEnrich `/people/search` is used only when no suitable named contact remains after the official-site check.\n- Search requires the exact organisation domain and an approved target role. The default result limit is one.\n- A later role-specific search is allowed when no suitable person is returned. Across the search sequence, no more than two unique people may be returned and retained per prospect.\n- One named contact is retained by default. A second requires a large organisation or shared purchasing or operational responsibility.\n- FullEnrich `/people/lookup` is used only when a contact name exists but identity, organisation or current role still needs verification. It is skipped when those elements are already verified.\n- FullEnrich `/contact/enrich/bulk` is called only for selected contacts and requests `contact.work_emails` and `contact.phones`.\n- Mobile phone is approved and actively sought. Its absence does not by itself block review.\n- Personal email is not requested, retained, written to CRM or used for outreach.\n- n8n is the approved target orchestration layer. It is not currently connected or runtime-active.\n- Apify fallback is never automatic and requires a separate preflight.\n\n## Approval boundary\n\nThis decision approves the A2 business configuration and implementation work. It does not authorise live FullEnrich, n8n, Apify, CRM-write or outreach execution.\n"""
    return decision, md


def build_source_register(decision_path: Path) -> dict[str, Any]:
    old = load(ROOT / "foundations/contracts/sources/a2-source-register-0.2.0.json")
    reg = copy.deepcopy(old)
    reg["version"] = NEW_VERSION
    reg["status"] = "equinet_confirmed_fullenrich_scope_runtime_integration_pending"
    reg["source_sequence"] = [
        "a1_approved_handoff", "hubspot_authoritative_records", "prospect_official_website",
        "fullenrich_people_search", "fullenrich_people_lookup", "fullenrich_contact_enrichment",
        "apify_harvestapi_linkedin_profile_search", "apify_harvestapi_email_search", "search_engine_discovery"
    ]
    rules = reg["global_rules"]
    rules.pop("no_additional_commercial_enrichment_provider_selected", None)
    rules.update({
        "equinet_first_party_enrichment_dataset_available": False,
        "fullenrich_precedes_apify": True,
        "fullenrich_people_search_default_result_limit": 1,
        "fullenrich_max_unique_people_returned_and_retained_per_prospect": 2,
        "fullenrich_personal_email_requested": False,
        "fullenrich_mobile_phone_permitted": True,
        "fullenrich_contact_enrichment_selected_contacts_only": True,
        "apify_fallback_requires_separate_preflight": True,
    })
    sources = reg["sources"]
    first_party = next(x for x in sources if x["source_id"] == "equinet_authorized_first_party_data")
    first_party.update({
        "name": "Equinet first-party enrichment dataset",
        "purpose": "Record that Equinet has no separate first-party dataset for A2 enrichment.",
        "business_approval": "confirmed_not_available_for_a2_enrichment",
        "source_rights_preflight": "not_applicable",
        "runtime_readiness": "not_available",
        "register_status": "not_available",
        "allowed_access_modes": [],
        "permitted_fields": [],
        "prohibited_fields": ["use as a planned enrichment source"],
        "limits": {"new_source_calls": 0},
        "notes": ["Séverine confirmed that Equinet will not provide separate first-party enrichment data. FullEnrich is a third-party provider, not first-party data."],
    })
    common = common_source_fields()
    fe_search = {
        "source_id": "fullenrich_people_search", "name": "FullEnrich People Search", "source_type": "commercial_people_search_provider",
        "canonical_url": "https://app.fullenrich.com/api/v2/people/search",
        "purpose": "Find a role-relevant named person inside the exact approved prospect organisation when the official website does not provide one.",
        "business_approval": "approved_by_equinet_for_a2_business_purpose",
        "source_rights_preflight": "provider_dpa_retention_and_data_route_review_pending",
        "runtime_readiness": "api_key_n8n_connector_budget_and_account_test_pending", "register_status": "conditional",
        "allowed_access_modes": ["fullenrich_api_v2_via_approved_n8n_workflow_after_all_gates"],
        "permitted_fields": ["person.full_name", "person.role_title", "person.public_profile_urls", "organisation.business_name", "organisation.public_business_location"],
        "prohibited_fields": ["email or phone from Search response", "personal email", "full career history", "education", "skills", "connection counts", "personal description", "role-free broad search", "cross-organisation search"],
        "limits": {
            "trigger": "no_suitable_named_contact_after_official_website_check", "exact_organisation_domain_required": True,
            "approved_target_role_required": True, "default_result_limit": 1,
            "subsequent_role_specific_search_only_when_no_suitable_person_returned": True,
            "max_unique_people_returned_per_prospect": 2, "max_retained_contacts_per_prospect": 2,
            "second_contact_requires_reason": ["large_organisation", "shared_purchasing_or_operational_responsibility"],
            "broad_role_free_search": False, "concurrency": 1, "documented_default_credit_per_returned_person": 0.25,
            "actual_premium_plan_rate_must_be_verified": True,
        },
        "notes": ["Search returns professional profile data, not contact email or phone.", "Use approved A2 target-role aliases and preserve the returned source title.", "Stop once a suitable person is found unless the second-contact rule is already satisfied."],
        **common,
    }
    fe_lookup = {
        "source_id": "fullenrich_people_lookup", "name": "FullEnrich People Lookup", "source_type": "commercial_people_lookup_provider",
        "canonical_url": "https://app.fullenrich.com/api/v2/people/lookup",
        "purpose": "Resolve a known person's identity, current role and organisation before contact enrichment when those facts remain uncertain.",
        "business_approval": "approved_by_equinet_for_a2_business_purpose",
        "source_rights_preflight": "provider_dpa_retention_and_data_route_review_pending",
        "runtime_readiness": "api_key_n8n_connector_budget_and_account_test_pending", "register_status": "conditional",
        "allowed_access_modes": ["fullenrich_api_v2_via_approved_n8n_workflow_after_all_gates"],
        "permitted_fields": ["person.full_name", "person.role_title", "person.public_profile_urls", "organisation.business_name", "organisation.public_business_location"],
        "prohibited_fields": ["email or phone from Lookup response", "personal email", "full career history", "education", "skills", "connection counts", "personal description"],
        "limits": {"trigger": "known_contact_identity_or_current_role_requires_verification", "max_results": 1, "skip_when_name_role_and_organisation_already_verified": True, "exact_company_identifier_required_with_name": True, "concurrency": 1, "documented_default_credit_per_returned_person": 0.25, "actual_premium_plan_rate_must_be_verified": True},
        "notes": ["Lookup returns at most one professional profile and does not return email or phone.", "Prefer a person professional-network URL; otherwise use full name plus exact company domain or company professional-network identifier."],
        **common,
    }
    fe_enrich = {
        "source_id": "fullenrich_contact_enrichment", "name": "FullEnrich Contact Enrichment", "source_type": "commercial_contact_enrichment_provider",
        "canonical_url": "https://app.fullenrich.com/api/v2/contact/enrich/bulk",
        "purpose": "Find a selected person's professional email and mobile phone after identity and role selection.",
        "business_approval": "approved_by_equinet_for_a2_business_purpose",
        "source_rights_preflight": "provider_dpa_retention_and_data_route_review_pending",
        "runtime_readiness": "api_key_n8n_webhook_budget_and_account_test_pending", "register_status": "conditional",
        "allowed_access_modes": ["fullenrich_api_v2_async_via_approved_n8n_workflow_after_all_gates"],
        "permitted_fields": ["person.business_email", "person.mobile_phone", "email verification result", "provider provenance", "verification timestamp"],
        "prohibited_fields": ["contact.personal_emails request", "personal email retention", "unselected-person enrichment", "full career history", "education", "skills", "connection counts", "personal description", "outreach consent inference", "automatic send"],
        "limits": {
            "trigger": "selected_contact_after_role_and_company_match", "selected_contacts_only": True,
            "requested_enrich_fields": ["contact.work_emails", "contact.phones"], "personal_email_requested": False,
            "max_contacts_per_prospect": 2, "second_contact_requires_reason": ["large_organisation", "shared_purchasing_or_operational_responsibility"],
            "concurrency": 1, "max_retry_on_transient_failure": 1,
            "documented_default_work_email_credit_if_found": 1, "documented_default_mobile_credit_if_found": 10,
            "actual_premium_plan_rate_must_be_verified": True, "asynchronous": True, "webhook_signature_required": "X-Signature-SHA1",
        },
        "notes": ["The API request must omit contact.personal_emails.", "A returned phone is stored as person.mobile_phone and is not relabelled as person.business_phone.", "The absence of a mobile does not by itself block review.", "Only field-minimised normalised evidence may leave the n8n integration boundary."],
        **common,
    }
    apify_pos = next(i for i,x in enumerate(sources) if x["source_id"] == "apify_harvestapi_linkedin_profile_search")
    sources[apify_pos:apify_pos] = [fe_search, fe_lookup, fe_enrich]
    apify = next(x for x in sources if x["source_id"] == "apify_harvestapi_linkedin_profile_search")
    apify["purpose"] = "Fallback role/contact search after the official website and FullEnrich return no suitable person or an approved technical exhaustion state."
    apify["limits"]["trigger"] = "named_role_gap_after_official_website_and_fullenrich"
    apify["limits"]["fullenrich_precondition"] = ["not_found", "insufficient_match", "unavailable_after_approved_retry"]
    apify["notes"].append("FullEnrich must be attempted first. Apify fallback is not automatic and requires a new source preflight.")
    apify_email = next(x for x in sources if x["source_id"] == "apify_harvestapi_email_search")
    apify_email["purpose"] = "Fallback professional-email search for a selected matched profile after FullEnrich returns no usable work email."
    apify_email["limits"]["trigger"] = "selected_profile_after_fullenrich_work_email_not_found"
    apify_email["limits"]["fullenrich_precondition"] = ["not_found", "unavailable_after_approved_retry"]
    commercial = next(x for x in sources if x["source_id"] == "commercial_enrichment_provider")
    commercial["name"] = "Other commercial enrichment providers"
    commercial["purpose"] = "Future providers other than the separately approved FullEnrich and Apify actions."
    commercial["notes"] = ["FullEnrich is modelled through three separate approved actions. Apollo, Clay and any other provider remain unselected."]
    reg["open_activation_inputs"] = [
        "Receive and store the Equinet FullEnrich API key in the approved n8n credential store.",
        "Verify the authorised FullEnrich workspace, API-key validity, current credit balance and actual Premium-plan rates.",
        "Complete FullEnrich privacy, security, DPA/subprocessor, three-month provider-retention and deletion review.",
        "Approve FullEnrich test, daily and pilot credit caps plus the spend/consumption owner.",
        "Deploy and test the bounded n8n Search, Lookup, Enrich and signed-webhook workflow.",
        "Provide the authorised Apify workspace/account, credential route, pinned Actor build and runtime owner before any fallback activation.",
        "Complete LinkedIn/HarvestAPI rights and vendor review before any Apify fallback.",
    ]
    reg["decision_record"] = {"path": str(decision_path.relative_to(ROOT)), "sha256": sha(decision_path)}
    return reg


def main() -> int:
    decision, decision_md = build_decision()
    decision_json = ROOT / f"foundations/decisions/{DECISION_ID}.json"
    decision_md_path = ROOT / f"foundations/decisions/{DECISION_ID}.md"
    dump(decision_json, decision)
    decision_md_path.write_text(decision_md, encoding="utf-8")

    # Business field catalogue.
    old_cat = ROOT / "foundations/contracts/business/a2-business-field-catalogue-0.2.0.json"
    cat = copy.deepcopy(load(old_cat))
    cat["version"] = NEW_VERSION
    cat["status"] = "equinet_confirmed_fullenrich_business_configuration_integration_pending"
    cat["decision_record"] = {"path": str(decision_json.relative_to(ROOT)), "sha256": sha(decision_json)}
    boundaries = cat.setdefault("source_handling_boundaries", {})
    boundaries["equinet_first_party_enrichment_dataset"] = "not_available"
    boundaries["fullenrich_people_and_contact_enrichment"] = "business_approved_runtime_integration_pending"
    boundaries["personal_email_and_mobile_paid_discovery"] = "personal_email_not_requested_mobile_approved_for_selected_contacts"
    boundaries["fullenrich_precedes_apify"] = True
    field_index = {x["field_key"]: x for x in cat["fields"]}
    for key in ["person.full_name", "person.role_title", "person.business_email", "person.public_profile_urls", "organisation.business_name", "organisation.public_business_location"]:
        field_index[key]["paid_lookup_allowed"] = True
    personal = field_index["person.personal_email_candidate"]
    personal["priority_by_segment"] = {"farrier": "do_not_collect", "horse_owner": "do_not_collect"}
    personal["collection_policy"] = "disabled_not_requested_from_fullenrich"
    personal["paid_lookup_allowed"] = False
    personal["description"] = "Personal email is not requested from FullEnrich or any A2 provider under the approved configuration."
    personal["approval_rule"] = "collection_not_authorized"
    mobile = field_index["person.mobile_phone"]
    mobile["priority_by_segment"] = {"farrier": "optional", "horse_owner": "optional"}
    mobile["collection_policy"] = "permitted_for_proposal_from_selected_contact_enrichment"
    mobile["paid_lookup_allowed"] = True
    mobile["description"] = "Mobile number returned by approved FullEnrich contact enrichment for a selected contact; actively sought, stored separately from business phone and not required by itself for review readiness."
    mobile["approval_rule"] = "human_review_required_during_pilot_no_outreach_authority"
    mobile["contact_channel_policy"] = "attempt_for_selected_contact_and_count_as_verified_phone_channel_when_valid"
    cat["horse_count_policy"]["net_new_permitted_explicit_sources"] = [x for x in cat["horse_count_policy"]["net_new_permitted_explicit_sources"] if x != "equinet_authorized_first_party_data"]
    cat_json = ROOT / "foundations/contracts/business/a2-business-field-catalogue-0.3.0.json"
    cat_csv = ROOT / "foundations/contracts/business/a2-business-field-catalogue-0.3.0.csv"
    dump(cat_json, cat)
    write_catalogue_csv(cat, cat_csv)

    # Minimum packages.
    minimum = copy.deepcopy(load(ROOT / "foundations/contracts/business/a2-minimum-data-packages-0.2.0.json"))
    minimum["version"] = NEW_VERSION
    minimum["status"] = "equinet_confirmed_fullenrich_business_configuration_integration_pending"
    minimum["business_field_catalogue"] = {"path": str(cat_json.relative_to(ROOT)), "version": NEW_VERSION, "sha256": sha(cat_json), "status": cat["status"]}
    minimum["global_rules"]["mobile_phone_permitted_and_actively_sought"] = True
    minimum["global_rules"]["mobile_phone_absence_blocks_review_by_itself"] = False
    minimum["global_rules"]["personal_email_requested"] = False
    for package in minimum["packages"].values():
        target = package["contact_paths"]["named_target"]
        for list_key in ["at_least_one_verified_field", "preferred_verified_fields"]:
            if "person.mobile_phone" not in target[list_key]:
                target[list_key].append("person.mobile_phone")
        needed = package["contact_paths"]["contact_needed"]["research_target_fields"]
        if "person.mobile_phone" not in needed:
            needed.append("person.mobile_phone")
    min_json = ROOT / "foundations/contracts/business/a2-minimum-data-packages-0.3.0.json"
    dump(min_json, minimum)

    # Source register.
    source_json = ROOT / "foundations/contracts/sources/a2-source-register-0.3.0.json"
    source_csv = ROOT / "foundations/contracts/sources/a2-source-register-0.3.0.csv"
    register = build_source_register(decision_json)
    dump(source_json, register)
    write_source_csv(register, source_csv)

    # Evidence policy.
    evidence = copy.deepcopy(load(ROOT / "foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.2.0.json"))
    evidence["version"] = NEW_VERSION
    evidence["status"] = "equinet_confirmed_fullenrich_policy_integration_pending"
    evidence["unitalk_approval"] = {"approver": "Séverine, Unitalk Operations", "approved_at": STAMP, "scope": "FullEnrich source order, role search, selected-contact work-email/mobile enrichment and no personal-email request"}
    evidence["dependencies"] = [
        {"path": str(source_json.relative_to(ROOT)), "sha256": sha(source_json)},
        {"path": str(cat_json.relative_to(ROOT)), "sha256": sha(cat_json)},
        {"path": "foundations/contracts/a2-state-model-0.1.0.json", "sha256": sha(ROOT / "foundations/contracts/a2-state-model-0.1.0.json")},
        {"path": str(decision_json.relative_to(ROOT)), "sha256": sha(decision_json)},
    ]
    auth = evidence["confidence_dimensions"]["source_authority"]["levels"]
    auth.update({"fullenrich_people_search": 12, "fullenrich_people_lookup": 12, "fullenrich_contact_enrichment": 12})
    evidence["principles"]["fullenrich_search_and_lookup_do_not_supply_contact_channels"] = True
    evidence["principles"]["fullenrich_personal_email_is_not_requested"] = True
    evidence["principles"]["fullenrich_mobile_is_stored_separately_from_business_phone"] = True
    evidence["source_rules"].update({
        "fullenrich_people_search": {"authority": "fullenrich_people_search", "usable_when": "exact organisation domain, approved target role, result and provider gates pass", "current_status": "integration_pending", "contact_channels_returned": False},
        "fullenrich_people_lookup": {"authority": "fullenrich_people_lookup", "usable_when": "known person plus company identifier and provider gates pass", "current_status": "integration_pending", "contact_channels_returned": False},
        "fullenrich_contact_enrichment": {"authority": "fullenrich_contact_enrichment", "usable_when": "selected contact, work-email/mobile-only request and all provider/runtime gates pass", "current_status": "integration_pending", "personal_email_requested": False},
    })
    evidence["conflict_policy"]["official_website_vs_fullenrich_current_role"] = "material_conflict_hold"
    evidence["email_specific_rules"]["fullenrich_work_email"] = "requires_exact_identity_and_company_match_plus_non_invalid_provider_status"
    evidence["email_specific_rules"]["personal_email"] = "not_requested_not_retained"
    evidence["mobile_specific_rules"] = {"fullenrich_phone_output": "map_to_person.mobile_phone_only", "absence_blocks_review_by_itself": False, "does_not_create_consent_or_outreach_eligibility": True}
    evidence["field_specific_rules"]["organisation.horse_count"]["net_new_sources"] = [x for x in evidence["field_specific_rules"]["organisation.horse_count"]["net_new_sources"] if x != "equinet_authorized_first_party_data"]
    evidence["field_specific_rules"]["person.contact_channels"] = {"attempt": ["person.business_email", "person.business_phone", "person.mobile_phone"], "at_least_one_verified_channel_required_when_others_unavailable": True, "mobile_absence_blocks_review_by_itself": False}
    evidence_json = ROOT / "foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.3.0.json"
    dump(evidence_json, evidence)

    # Provider and cost policy.
    provider = copy.deepcopy(load(ROOT / "foundations/contracts/governance/a2-provider-and-cost-policy-0.2.0.json"))
    provider["version"] = NEW_VERSION
    provider["status"] = "equinet_confirmed_fullenrich_scope_runtime_integration_pending"
    provider["unitalk_approval"] = {"approver": "Séverine, Unitalk Operations", "approved_at": STAMP, "scope": "FullEnrich priority, endpoints, result/contact limits, work email, mobile, personal-email exclusion and n8n direction"}
    provider["dependencies"] = [{"path": str(source_json.relative_to(ROOT)), "sha256": sha(source_json)}, {"path": str(decision_json.relative_to(ROOT)), "sha256": sha(decision_json)}]
    providers = provider["providers"]
    providers["fullenrich_people_search"] = {
        "endpoint": "POST https://app.fullenrich.com/api/v2/people/search", "purpose": "find_named_contact_by_exact_organisation_domain_and_approved_target_role",
        "business_approval": "approved", "runtime_status": "integration_pending_api_key_n8n_vendor_budget_and_account_test",
        "billing_model": "documented_0.25_credit_per_returned_person_verify_premium_plan",
        "limits": {"default_result_limit": 1, "maximum_unique_people_returned_and_retained_per_prospect": 2, "second_contact_requires_reason": True, "broad_role_free_search": False, "concurrency": 1},
        "allowed_fields": ["full_name", "employment.current.title", "employment.current.company.name", "employment.current.company.domain", "location", "social_profiles.professional_network.url"],
        "prohibited_fields": ["contact email", "contact phone", "education", "skills", "full employment history", "connection counts", "personal description"],
    }
    providers["fullenrich_people_lookup"] = {
        "endpoint": "POST https://app.fullenrich.com/api/v2/people/lookup", "purpose": "resolve_known_person_identity_current_role_and_company",
        "business_approval": "approved", "runtime_status": "integration_pending_api_key_n8n_vendor_budget_and_account_test",
        "billing_model": "documented_0.25_credit_per_returned_person_verify_premium_plan",
        "limits": {"maximum_results": 1, "skip_when_name_role_and_organisation_already_verified": True, "concurrency": 1},
        "allowed_fields": ["full_name", "employment.current.title", "employment.current.company.name", "employment.current.company.domain", "location", "social_profiles.professional_network.url"],
        "prohibited_fields": ["contact email", "contact phone", "education", "skills", "full employment history", "connection counts", "personal description"],
    }
    providers["fullenrich_contact_enrichment"] = {
        "endpoint": "POST https://app.fullenrich.com/api/v2/contact/enrich/bulk", "purpose": "selected_contact_work_email_and_mobile_enrichment",
        "business_approval": "approved", "runtime_status": "integration_pending_api_key_n8n_webhook_vendor_budget_and_account_test",
        "billing_model": {"documented_work_email_if_found_credits": 1, "documented_mobile_if_found_credits": 10, "personal_email_not_requested": True, "actual_premium_plan_rates_must_be_verified": True},
        "limits": {"max_contacts_per_prospect": 2, "second_contact_requires_reason": True, "max_retry_on_transient_failure": 1, "concurrency": 1},
        "requested_enrich_fields": ["contact.work_emails", "contact.phones"],
        "allowed_fields": ["most_probable_work_email.email", "most_probable_work_email.status", "work_emails[].email", "work_emails[].status", "most_probable_phone.number", "most_probable_phone.region", "phones[].number", "phones[].region"],
        "prohibited_fields": ["contact.personal_emails request", "personal email retention", "unselected-person enrichment", "unapproved profile fields", "automatic outreach"],
        "asynchronous": True, "result_delivery": "signed_webhook_via_n8n", "webhook_signature_header": "X-Signature-SHA1",
    }
    providers["apify_linkedin_profile_search"]["purpose"] = "fallback_role_and_company_match_after_official_site_and_fullenrich"
    providers["apify_linkedin_profile_search"]["input_strategy"]["fullenrich_precondition"] = ["not_found", "insufficient_match", "unavailable_after_approved_retry"]
    providers["apify_independent_email_search"]["purpose"] = "fallback_professional_email_after_fullenrich_not_found"
    providers["apify_independent_email_search"]["fullenrich_precondition"] = ["not_found", "unavailable_after_approved_retry"]
    provider["provider_sequence"] = ["fullenrich_people_search_or_lookup", "fullenrich_contact_enrichment_for_selected_contacts", "apify_harvestapi_separately_preflighted_fallback"]
    provider["execution_controls"]["no_automatic_provider_fallback"] = True
    provider["execution_controls"]["fullenrich_search_default_result_limit"] = 1
    provider["execution_controls"]["maximum_unique_people_returned_and_retained_per_prospect"] = 2
    provider["execution_controls"]["contact_enrichment_selected_contacts_only"] = True
    provider["execution_controls"]["personal_email_requested"] = False
    provider["provider_activation_gates"] = {
        "fullenrich": ["approved_account", "api_key_in_n8n_credential_store", "api_key_verification", "current_credit_balance", "premium_plan_rate_verification", "vendor_and_data_route_review", "three_month_retention_review", "test_daily_and_pilot_caps", "spend_and_consumption_owner", "audit_logging", "n8n_connector_test", "signed_webhook_verification"],
        "apify_harvestapi": ["approved_account", "pinned_actor_build", "rights_or_exception", "vendor_due_diligence", "retention_rule", "test_daily_and_pilot_caps", "spend_and_consumption_owner", "audit_logging", "connector_test", "fullenrich_precondition_receipt"],
    }
    provider["runtime_activation_gate"] = {"all_required": provider["provider_activation_gates"]["fullenrich"], "current_status": "blocked_pending_integration", "external_calls_authorized": False}
    provider["data_governance"]["documented_fullenrich_provider_retention_days"] = 90
    provider["data_governance"]["fullenrich_retention_acceptance_status"] = "pending_review"
    provider["data_governance"]["personal_email_requested"] = False
    provider["open_inputs"] = [
        "Equinet FullEnrich API key stored in the approved n8n credential store",
        "FullEnrich API-key verification and current credit balance",
        "actual Premium-plan Search, work-email and mobile credit rates",
        "FullEnrich vendor, DPA/subprocessor, data-route, retention and deletion approval",
        "FullEnrich test, daily and pilot credit caps plus spend/consumption owner",
        "published n8n workflow and signed-webhook test",
        "bounded synthetic then approved real-data connector acceptance",
        "remaining Apify fallback gates before any fallback execution",
    ]
    provider_json = ROOT / "foundations/contracts/governance/a2-provider-and-cost-policy-0.3.0.json"
    dump(provider_json, provider)

    # Protected policy dependency refresh.
    protected = copy.deepcopy(load(ROOT / "foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.2.0.json"))
    protected["version"] = NEW_VERSION
    protected["status"] = "equinet_confirmed_fullenrich_dependency_refresh_integration_pending"
    for dep in protected["dependencies"]:
        if "business-field-catalogue" in dep["path"]:
            dep.update(path=str(cat_json.relative_to(ROOT)), sha256=sha(cat_json))
        elif "evidence-verification-confidence" in dep["path"]:
            dep.update(path=str(evidence_json.relative_to(ROOT)), sha256=sha(evidence_json))
    protected["fullenrich_contact_rules"] = {"mobile_phone": "propose_only_preserve_existing_manual_value_and_require_review", "business_email": "propose_only_preserve_existing_manual_value_and_require_review", "personal_email": "not_requested", "crm_write_authorized": False}
    protected_json = ROOT / "foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.3.0.json"
    dump(protected_json, protected)

    # HubSpot mapping dependency and mobile status refresh.
    mapping = copy.deepcopy(load(ROOT / "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.2.0.json"))
    mapping["version"] = NEW_VERSION
    mapping["status"] = "equinet_confirmed_fullenrich_mobile_mapping_live_verification_pending"
    for dep in mapping["dependencies"]:
        if "business-field-catalogue" in dep["path"]:
            dep.update(path=str(cat_json.relative_to(ROOT)), sha256=sha(cat_json))
    mobile_map = next(x for x in mapping["mappings"] if x["canonical_field"] == "person.mobile_phone")
    mobile_map["mapping_status"] = "proposed_unverified"
    mobile_map["conversion"] = "e164_normalisation_then_human_review"
    mobile_map["populated_manual_value"] = "preserve_and_hold_on_difference"
    mobile_map["workflow_dependency_status"] = "unverified"
    mobile_map["write_authorized"] = False
    mapping_json = ROOT / "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.3.0.json"
    mapping_csv = ROOT / "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.3.0.csv"
    dump(mapping_json, mapping)
    write_mapping_csv(mapping, mapping_csv)

    # Runtime policy successor.
    runtime_old = ROOT / "foundations/contracts/runtime/a2-no-integration-runtime-policy-1.1.0.yaml"
    runtime_text = runtime_old.read_text(encoding="utf-8")
    runtime_text = replace_required(runtime_text, "policy_version: 1.1.0", "policy_version: 1.2.0")
    runtime_text = replace_required(runtime_text, "release_candidate: equinet-a2-business-confirmation-1.1.0", "release_candidate: equinet-a2-fullenrich-foundation-1.2.0")
    runtime_text = replace_required(runtime_text, "  n8n: false\n  apify: false", "  n8n: false\n  fullenrich: false\n  apify: false")
    runtime_text = replace_required(runtime_text, "- candidate_scope_beyond_explicitly_approved_runs", "- candidate_scope_beyond_explicitly_approved_runs\n- fullenrich_api_key_account_credit_rates_and_vendor_review\n- n8n_workflow_publication_and_signed_webhook_acceptance")
    runtime_text = replace_required(runtime_text, "approved_at: '2026-08-30T14:56:57Z'", f"approved_at: '{STAMP}'")
    runtime_text = replace_required(runtime_text, "- S9-10", "- S9-10\n- FE-1\n- FE-2\n- FE-3\n- FE-4")
    runtime_path = ROOT / "foundations/contracts/runtime/a2-no-integration-runtime-policy-1.2.0.yaml"
    runtime_path.write_text(runtime_text, encoding="utf-8")

    # Integration contract and n8n implementation specification.
    integration_contract = {
        "contract_id": "equinet-a2-fullenrich-n8n-integration", "version": "0.1.0", "status": "design_approved_runtime_not_connected",
        "profile": "equinet-a2-enrichment", "provider": "FullEnrich API v2", "orchestrator": "n8n",
        "credential_boundary": {"fullenrich_api_key": "n8n_credential_store_only", "profile_receives_secret": False, "logs_secret": False},
        "operations": {
            "people_search": {"method": "POST", "path": "/people/search", "synchronous": True, "required": ["candidate_id", "exact_organisation_domain", "approved_target_roles"], "default_limit": 1, "max_unique_people_per_prospect": 2},
            "people_lookup": {"method": "POST", "path": "/people/lookup", "synchronous": True, "required": ["candidate_id", "person_name", "company_identifier"], "max_results": 1},
            "contact_enrich": {"method": "POST", "path": "/contact/enrich/bulk", "synchronous": False, "selected_contacts_only": True, "enrich_fields": ["contact.work_emails", "contact.phones"], "prohibited_enrich_fields": ["contact.personal_emails"], "max_contacts_per_prospect": 2, "completion": "signed_webhook"},
            "credit_balance": {"method": "GET", "path": "/account/credits", "before_paid_action": True},
            "verify_key": {"method": "GET", "path": "/account/keys/verify", "pre_activation_only": True},
        },
        "workflow_tools": ["start_a2_fullenrich_action", "get_a2_fullenrich_result"],
        "webhook_security": {"signature_header": "X-Signature-SHA1", "algorithm": "HMAC-SHA1", "verify_raw_body_before_json_parse": True, "constant_time_compare": True},
        "idempotency": {"components": ["candidate_id", "operation", "role_group_or_selected_contact_id", "source_register_version"], "duplicate_execution": "return_existing_job"},
        "terminal_states": ["succeeded", "not_found", "insufficient_match", "failed", "blocked", "cancelled", "timed_out"],
        "retry": {"transient_technical_failure": 1, "not_found": 0, "invalid_input": 0, "credit_or_policy_block": 0},
        "output_minimisation": {"people": ["provider_person_id", "full_name", "current_role", "organisation_name", "organisation_domain", "location", "professional_network_url"], "contact": ["full_name", "current_role", "professional_network_url", "work_email", "work_email_status", "mobile_phone", "mobile_region"], "discard": ["personal_emails", "education", "skills", "full_employment_history", "connection_counts", "personal_description"]},
        "external_actions_authorized": False, "crm_write_authorized": False, "outreach_authorized": False,
        "activation_requirements": provider["provider_activation_gates"]["fullenrich"],
        "decision_record": {"path": str(decision_json.relative_to(ROOT)), "sha256": sha(decision_json)},
    }
    integration_json = ROOT / "foundations/contracts/integrations/a2-fullenrich-n8n-integration-0.1.0.json"
    dump(integration_json, integration_contract)
    spec = f"""# A2 FullEnrich n8n Integration Specification\n\n**Version:** `0.1.0`  \n**Status:** `DESIGN APPROVED — N8N AND FULLENRICH NOT CONNECTED`  \n**Decision:** `{DECISION_ID}`\n\n## Architecture\n\n```text\nA2 validated source request\n→ narrow n8n start tool\n→ FullEnrich API v2\n→ synchronous Search/Lookup result or asynchronous Enrich job\n→ signed FullEnrich webhook for Enrich\n→ n8n verification and field minimisation\n→ narrow n8n status/result tool\n→ A2 evidence and human-review workflow\n```\n\n## Start tool\n\n`start_a2_fullenrich_action` accepts one candidate-scoped operation: `people_search`, `people_lookup` or `contact_enrich`. It validates the active source policy, role/domain or selected-contact inputs, contact/result limits, idempotency key, credit balance and audit correlation ID before any provider call.\n\n## Status/result tool\n\n`get_a2_fullenrich_result` accepts only the Unitalk job ID. It returns `running`, `succeeded`, `not_found`, `insufficient_match`, `failed`, `blocked`, `cancelled` or `timed_out`, plus a field-minimised result and usage record.\n\n## People Search\n\n- Require the exact approved organisation domain and approved A2 target-role titles.\n- Default `limit` is one.\n- A later role-specific search is permitted only when no suitable person was returned.\n- Stop at two unique returned/retained people per prospect.\n- A second retained contact requires the approved reason.\n- Search results contain profile data only; never treat them as email or phone results.\n\n## People Lookup\n\n- Use only for a known name when identity, organisation or current role needs verification.\n- Prefer person professional-network URL; otherwise use full name plus exact company identifier.\n- Skip Lookup when name, role and organisation are already verified.\n\n## Contact Enrichment\n\n- Run only for selected contacts.\n- Send exactly `contact.work_emails` and `contact.phones`.\n- Never request `contact.personal_emails`.\n- Store returned phones as `person.mobile_phone`, not `person.business_phone`.\n- Persist the `enrichment_id` and correlation fields as strings.\n\n## Webhook and secret controls\n\n- Store the FullEnrich API key only in the n8n credential store.\n- Verify `X-Signature-SHA1` against the raw request body with constant-time comparison before parsing.\n- Reject missing or invalid signatures.\n- Never print or return credentials.\n\n## Retries and fallback\n\n- Retry one approved transient technical failure at most once.\n- Do not retry `not_found`, invalid input, privacy/policy blocks or insufficient credits.\n- Do not invoke Apify automatically. Return a terminal receipt so A2 can run a separate Apify preflight when the approved FullEnrich fallback condition is met.\n\n## Activation boundary\n\nNo live workflow is deployed by this specification. Activation requires n8n access, the API key, account and balance verification, Premium-plan rate confirmation, provider governance approval, caps, signed-webhook testing and a bounded acceptance run.\n"""
    spec_path = ROOT / "integrations/n8n/A2-FULLENRICH-N8N-WORKFLOW-SPEC.md"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(spec, encoding="utf-8")

    # Active prose updates.
    soul_path = ROOT / "SOUL.md"
    soul = soul_path.read_text(encoding="utf-8")
    for old_name, new_name in [
        ("Business Field Catalogue `0.2.0`", "Business Field Catalogue `0.3.0`"),
        ("Minimum Data Packages `0.2.0`", "Minimum Data Packages `0.3.0`"),
        ("A2 Source Register `0.2.0`", "A2 Source Register `0.3.0`"),
        ("Evidence, Verification, Confidence and Freshness Policy `0.2.0`", "Evidence, Verification, Confidence and Freshness Policy `0.3.0`"),
        ("Protected Fields and Conflict Policy `0.2.0`", "Protected Fields and Conflict Policy `0.3.0`"),
        ("Provider and Cost Policy `0.2.0`", "Provider and Cost Policy `0.3.0`"),
        ("Preliminary A2-to-HubSpot Mapping `0.2.0`", "Preliminary A2-to-HubSpot Mapping `0.3.0`"),
        ("No-Integration Runtime Policy `1.1.0`", "No-Integration Runtime Policy `1.2.0`"),
    ]:
        soul = replace_required(soul, old_name, new_name)
    old_sequence = """1. approved A1 handoff and evidence;\n2. HubSpot authoritative records when a read-only connection exists;\n3. authorised Equinet first-party data;\n4. prospect-owned official website;\n5. approved Apify actions only after every source-rights and runtime gate passes;\n6. search engine only to locate an official destination."""
    new_sequence = """1. approved A1 handoff and evidence;\n2. HubSpot authoritative records when a read-only connection exists;\n3. prospect-owned official website;\n4. FullEnrich People Search or People Lookup for the applicable named gap;\n5. FullEnrich Contact Enrichment only for selected contacts;\n6. approved Apify actions only after FullEnrich and every separate source-rights and runtime gate;\n7. search engine only to locate an official destination.\n\nEquinet has no separate first-party enrichment dataset. Recorded Equinet representative confirmation remains a review or correction mechanism, not a planned research source."""
    soul = replace_required(soul, old_sequence, new_sequence)
    old_provider_section = """### Apify and LinkedIn\n\n`harvestapi/linkedin-profile-search` is business-approved for the A2 purpose but not runtime-active. Trigger it only for a named role or contact gap after the official-site check. Prefer an exact LinkedIn company URL explicitly published on the official website; otherwise use a verified company name plus target role. Keep an individual LinkedIn profile URL for authorised human review or a separately approved profile-scraper route rather than passing it to the selected profile-search Actor. Keep the current minimum field allowlist and bounded limits. Do not use the Actor until LinkedIn rights, HarvestAPI vendor review, account, pinned build, budget, retention, audit and connector gates pass.\n\nTreat independent email search as a separate provider action. Provider email must never be labelled as LinkedIn-sourced. Professional email may enter verification after all gates pass. A personal email candidate remains `held_for_human_privacy_review`; before approval it cannot satisfy professional contactability, be written to CRM or be used for outreach.\n\nApollo, Clay and other providers remain unselected and unavailable."""
    new_provider_section = """### FullEnrich, then Apify/LinkedIn fallback\n\nFullEnrich is business-approved as the first commercial provider after the official-site check, but it is not runtime-active. When no suitable named contact is known, use `/people/search` with the exact organisation domain and approved target-role titles, with a default result limit of one. A later role-specific search is allowed only when no suitable person was returned. Across the search sequence, return and retain no more than two unique people; a second retained contact requires a large organisation or shared purchasing or operational responsibility. Never run a broad role-free search.\n\nWhen a name exists but identity, organisation or current role remains uncertain, use `/people/lookup`. Skip Lookup when name, role and organisation are already verified. Search and Lookup return professional-profile data, not contact email or phone.\n\nRun `/contact/enrich/bulk` only for selected contacts and request exactly `contact.work_emails` and `contact.phones`. Do not request personal email. Store provider phone output as `person.mobile_phone`, separate from a published `person.business_phone`. Mobile is approved and actively sought, but its absence does not by itself block review.\n\n`harvestapi/linkedin-profile-search` remains business-approved but not runtime-active. It is a separately preflighted fallback only after FullEnrich returns `not_found`, `insufficient_match` or an approved technical-exhaustion state. Apify fallback is never automatic. Existing LinkedIn rights, HarvestAPI vendor, account, pinned-build, budget, retention, audit and connector gates remain.\n\nApollo, Clay and other providers remain unselected and unavailable."""
    soul = replace_required(soul, old_provider_section, new_provider_section)
    soul = replace_required(soul, "Attempt to verify both professional email and business phone; one verified channel satisfies the minimum when the other is unavailable.", "Attempt to verify professional email, published business phone and FullEnrich mobile for a selected contact. At least one verified channel satisfies the minimum when the others are unavailable; missing mobile alone does not block review.")
    soul = replace_required(soul, "- approved Apify profile or email action;", "- approved FullEnrich Search, Lookup or selected-contact enrichment action;\n- separately approved Apify profile or email fallback action;")
    soul = replace_required(soul, "- Apify/HarvestAPI: business-approved scope defined; rights, vendor, account, build, budget, retention and connector gates pending.\n- Apollo, Clay and other providers: not selected.", "- FullEnrich: business-approved scope defined; API key, account test, Premium-plan rates, vendor/retention review, caps, n8n connector and signed-webhook test pending.\n- Apify/HarvestAPI: fallback scope defined; rights, vendor, account, build, budget, retention and connector gates pending.\n- Apollo, Clay and other providers: not selected.")
    soul = replace_required(soul, "HubSpot, Twenty, n8n, Apify, outreach and delivery remain disabled until their separate gates pass.", "HubSpot, Twenty, n8n, FullEnrich, Apify, outreach and delivery remain disabled until their separate gates pass.")
    soul_path.write_text(soul, encoding="utf-8")

    # Update active skill prose and dependency versions.
    skill_paths = [
        ROOT / "skills/a2-gap-analysis-and-enrichment-planning/SKILL.md",
        ROOT / "skills/a2-permitted-enrichment-research/SKILL.md",
        ROOT / "skills/a2-field-verification/SKILL.md",
        ROOT / "skills/a2-evidence-confidence-and-freshness/SKILL.md",
        ROOT / "skills/a2-data-quality-and-review-readiness/SKILL.md",
        ROOT / "skills/a2-review-package-and-governed-handoffs/SKILL.md",
    ]
    for path in skill_paths:
        text = path.read_text(encoding="utf-8")
        text = text.replace("**Version:** `0.2.0`", "**Version:** `0.3.0`")
        text = text.replace("Business Field Catalogue `0.2.0`", "Business Field Catalogue `0.3.0`")
        text = text.replace("Minimum Data Packages `0.2.0`", "Minimum Data Packages `0.3.0`")
        text = text.replace("Source Register `0.2.0`", "Source Register `0.3.0`")
        path.write_text(text, encoding="utf-8")
    research_path = ROOT / "skills/a2-permitted-enrichment-research/SKILL.md"
    research = research_path.read_text(encoding="utf-8")
    research = replace_required(research, """1. reuse the approved A1 handoff and evidence;\n2. read HubSpot only when a permitted connection exists;\n3. use authorised Equinet first-party data;\n4. inspect the prospect-owned official site for a named gap;\n5. consider the exact approved provider action only after the official-site gap and every rights, vendor, account, build, retention, budget and audit gate;\n6. use search only to locate an official destination, never as retained field evidence.""", """1. reuse the approved A1 handoff and evidence;\n2. read HubSpot only when a permitted connection exists;\n3. inspect the prospect-owned official site for a named gap;\n4. use FullEnrich People Search when no suitable named contact exists, or People Lookup when a known contact still needs identity/current-role verification;\n5. use FullEnrich Contact Enrichment only for selected contacts and request work email plus mobile, never personal email;\n6. consider Apify only as a separately preflighted non-automatic fallback after an approved FullEnrich terminal state;\n7. use search only to locate an official destination, never as retained field evidence.\n\nEquinet has no separate first-party enrichment dataset.""")
    research = replace_required(research, "`harvestapi/linkedin-profile-search` remains blocked. Prefer an exact company LinkedIn URL explicitly published on the official site, otherwise a verified company name plus target role. An individual profile URL follows a separate manual or separately approved profile-scraper route. Email search is a distinct action; it retains professional email only by default and never creates consent.", "FullEnrich remains integration-pending. People Search requires an exact organisation domain, an approved target role and a default result limit of one; a later role-specific search is allowed only when no suitable person is returned. Return and retain at most two unique people per prospect, with the approved reason required for the second. People Lookup is limited to one known person. Contact Enrichment is limited to selected contacts and requests only work email and mobile. Apify remains a separately preflighted, non-automatic fallback.")
    research = research.replace("No live Web, Apify, HubSpot or other external call", "No live Web, FullEnrich, Apify, HubSpot or other external call")
    research_path.write_text(research, encoding="utf-8")

    # Human-readable catalogue and package summaries.
    cat_doc = ROOT / "foundations/A2-BUSINESS-FIELD-CATALOGUE.md"
    text = cat_doc.read_text(encoding="utf-8")
    text = text.replace("**Version:** `0.2.0`", "**Version:** `0.3.0`")
    text = text.replace("a2-business-field-catalogue-0.2.0.json", "a2-business-field-catalogue-0.3.0.json")
    text = replace_required(text, "- Attempt both professional email and business phone; one verified channel satisfies the minimum when the other is unavailable.", "- Attempt professional email, published business phone and FullEnrich mobile for selected contacts; one verified channel satisfies the minimum when the others are unavailable.\n- Mobile is actively sought but its absence alone does not block review. Personal email is not requested.")
    text = replace_required(text, "- one verified professional email or business phone, after attempting both.", "- one verified professional email, published business phone or mobile phone, after attempting the applicable channels.")
    text = replace_required(text, "- Net-new prospect or empty HubSpot value: explicit approved A1 evidence, authorised Equinet first-party data, recorded Equinet confirmation or the prospect-owned official website may support an exact count.", "- Net-new prospect or empty HubSpot value: explicit approved A1 evidence, recorded Equinet confirmation or the prospect-owned official website may support an exact count. Equinet has no separate first-party enrichment dataset.")
    cat_doc.write_text(text, encoding="utf-8")
    min_doc = ROOT / "foundations/A2-MINIMUM-DATA-PACKAGES.md"
    text = min_doc.read_text(encoding="utf-8")
    text = text.replace("**Version:** `0.2.0`", "**Version:** `0.3.0`")
    text = text.replace("attempt both `person.business_email` and `person.business_phone`; at least one verified channel satisfies the minimum when the other is unavailable.", "attempt `person.business_email`, published `person.business_phone` and FullEnrich `person.mobile_phone` for selected contacts; at least one verified channel satisfies the minimum when the others are unavailable. Missing mobile alone does not block review.")
    min_doc.write_text(text, encoding="utf-8")
    mapping_doc = ROOT / "foundations/A2-PRELIMINARY-HUBSPOT-MAPPING.md"
    text = mapping_doc.read_text(encoding="utf-8")
    text = text.replace("**Version:** `0.2.0`", "**Version:** `0.3.0`")
    text += "\n## FullEnrich mobile clarification\n\n`person.mobile_phone` is now a permitted proposal field for selected contacts and maps provisionally to `Contact.mobilephone`. Existing manual values remain protected. No HubSpot write is authorised.\n"
    mapping_doc.write_text(text, encoding="utf-8")

    # Implementation contract clarification.
    contract_path = ROOT / "foundations/A2-IMPLEMENTATION-CONTRACT.md"
    contract = contract_path.read_text(encoding="utf-8")
    contract = replace_required(contract, "1. authoritative live source-system state and validated first-party Equinet entries;", "1. authoritative live source-system state; Equinet has confirmed that no separate first-party enrichment dataset is available;")
    contract += "\n## 20. FullEnrich source-routing amendment — 2026-09-06\n\nThe approved new-source order is prospect official website, FullEnrich and then separately gated Apify/HarvestAPI. FullEnrich People Search is role- and exact-domain-bounded with a default result limit of one and a maximum of two unique returned/retained people per prospect. People Lookup is used only for a known person whose identity, organisation or current role still needs verification. Contact Enrichment runs only for selected contacts and requests work email and mobile phone; personal email is not requested. n8n is the approved target orchestrator but remains unconnected.\n"
    contract_path.write_text(contract, encoding="utf-8")

    print(json.dumps({
        "status": "foundation_artifacts_written",
        "business_configuration_version": NEW_VERSION,
        "decision": str(decision_json.relative_to(ROOT)),
        "source_count": len(register["sources"]),
        "field_count": len(cat["fields"]),
        "integration_contract": str(integration_json.relative_to(ROOT)),
        "n8n_spec": str(spec_path.relative_to(ROOT)),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
