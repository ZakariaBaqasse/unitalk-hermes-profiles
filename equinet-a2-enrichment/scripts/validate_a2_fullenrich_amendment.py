#!/usr/bin/env python3
"""Validate the approved A2 FullEnrich source-routing amendment."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "evaluations/fullenrich-source-amendment-20260906"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    failures: list[str] = []
    checks: dict[str, bool] = {}

    def check(name: str, condition: bool) -> None:
        checks[name] = bool(condition)
        if not condition:
            failures.append(name)

    cat_path = ROOT / "foundations/contracts/business/a2-business-field-catalogue-0.3.0.json"
    min_path = ROOT / "foundations/contracts/business/a2-minimum-data-packages-0.3.0.json"
    source_path = ROOT / "foundations/contracts/sources/a2-source-register-0.3.0.json"
    evidence_path = ROOT / "foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.3.0.json"
    provider_path = ROOT / "foundations/contracts/governance/a2-provider-and-cost-policy-0.3.0.json"
    protected_path = ROOT / "foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.3.0.json"
    mapping_path = ROOT / "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.3.0.json"
    integration_path = ROOT / "foundations/contracts/integrations/a2-fullenrich-n8n-integration-0.1.0.json"
    decision_path = ROOT / "foundations/decisions/A2-FULLENRICH-SOURCE-ROUTING-20260906.json"
    paths = [cat_path, min_path, source_path, evidence_path, provider_path, protected_path, mapping_path, integration_path, decision_path]
    check("all_versioned_artifacts_exist", all(path.is_file() for path in paths))
    cat, minimum, source, evidence, provider, protected, mapping, integration, decision = [load(path) for path in paths]

    expected_roles = {
        "farrier": {
            "primary": ["independent_self_employed_farrier", "farrier_business_owner", "farrier_business_founder_cofounder", "lead_head_farrier", "professional_farrier"],
            "secondary": ["associate_staff_farrier", "multi_farrier_practice_farrier", "business_office_practice_manager_with_commercial_responsibility"],
            "review_only": ["apprentice_student_farrier"],
            "excluded": ["farrier_instructor_educator_without_current_commercial_activity", "retired_inactive_farrier_without_current_professional_activity"],
        },
        "horse_owner": {
            "primary": ["owner_horse_owner", "farm_owner_manager", "stable_owner_manager", "equestrian_centre_owner_manager", "breeding_farm_owner_manager", "equine_business_managing_director_general_manager", "operations_manager_with_horse_care_or_purchasing_responsibility"],
            "secondary": ["head_trainer_head_coach", "trainer_professional_rider", "barn_yard_manager", "equine_program_manager", "purchasing_procurement_manager", "assistant_manager_operations_coordinator_with_purchasing_responsibility"],
            "review_only": [], "excluded": [],
        },
    }
    check("approved_target_roles_preserved", all(cat["target_role_model"][segment][bucket] == values for segment, groups in expected_roles.items() for bucket, values in groups.items()))

    sequence = source["source_sequence"]
    by_source = {item["source_id"]: item for item in source["sources"]}
    check("exact_source_sequence", sequence == ["a1_approved_handoff", "hubspot_authoritative_records", "prospect_official_website", "fullenrich_people_search", "fullenrich_people_lookup", "fullenrich_contact_enrichment", "apify_harvestapi_linkedin_profile_search", "apify_harvestapi_email_search", "search_engine_discovery"])
    check("equinet_first_party_not_available", by_source["equinet_authorized_first_party_data"]["register_status"] == "not_available" and by_source["equinet_authorized_first_party_data"]["limits"]["new_source_calls"] == 0)
    check("fullenrich_three_actions_present", all(key in by_source for key in ["fullenrich_people_search", "fullenrich_people_lookup", "fullenrich_contact_enrichment"]))
    search_limits = by_source["fullenrich_people_search"]["limits"]
    check("search_limit_one_and_total_two", search_limits["default_result_limit"] == 1 and search_limits["max_unique_people_returned_per_prospect"] == 2 and search_limits["max_retained_contacts_per_prospect"] == 2)
    check("search_requires_domain_and_role", search_limits["exact_organisation_domain_required"] is True and search_limits["approved_target_role_required"] is True and search_limits["broad_role_free_search"] is False)
    check("contact_enrichment_fields_exact", set(by_source["fullenrich_contact_enrichment"]["limits"]["requested_enrich_fields"]) == {"contact.work_emails", "contact.phones"} and by_source["fullenrich_contact_enrichment"]["limits"]["personal_email_requested"] is False)
    check("fullenrich_before_apify", sequence.index("fullenrich_contact_enrichment") < sequence.index("apify_harvestapi_linkedin_profile_search"))

    fields = {item["field_key"]: item for item in cat["fields"]}
    check("mobile_now_permitted", fields["person.mobile_phone"]["collection_policy"] == "permitted_for_proposal_from_selected_contact_enrichment" and fields["person.mobile_phone"]["paid_lookup_allowed"] is True)
    check("personal_email_disabled", fields["person.personal_email_candidate"]["collection_policy"] == "disabled_not_requested_from_fullenrich" and all(v == "do_not_collect" for v in fields["person.personal_email_candidate"]["priority_by_segment"].values()))
    check("paid_profile_and_work_email_allowed", all(fields[key]["paid_lookup_allowed"] is True for key in ["person.full_name", "person.role_title", "person.business_email"]))
    check("first_party_removed_from_horse_count", "equinet_authorized_first_party_data" not in cat["horse_count_policy"]["net_new_permitted_explicit_sources"] and "equinet_authorized_first_party_data" not in evidence["field_specific_rules"]["organisation.horse_count"]["net_new_sources"])
    for package in minimum["packages"].values():
        contact = package["contact_paths"]["named_target"]
        check(f"{package['segment']}_mobile_contact_alternative", "person.mobile_phone" in contact["at_least_one_verified_field"] and "person.mobile_phone" in contact["preferred_verified_fields"])
    mobile_mapping = next(item for item in mapping["mappings"] if item["canonical_field"] == "person.mobile_phone")
    check("mobile_hubspot_mapping_proposal_only", mobile_mapping["mapping_status"] == "proposed_unverified" and mobile_mapping["write_authorized"] is False)

    check("provider_sequence_and_no_auto_fallback", provider["provider_sequence"][0].startswith("fullenrich") and provider["execution_controls"]["no_automatic_provider_fallback"] is True)
    check("n8n_contract_not_active", integration["status"] == "design_approved_runtime_not_connected" and integration["external_actions_authorized"] is False)
    check("decision_scope_recorded", decision["decisions"]["people_search"]["default_result_limit"] == 1 and decision["decisions"]["contact_enrichment"]["mobile_phone_permitted_and_desired"] is True)

    gap = load_module("gap", ROOT / "scripts/build_a2_gap_plan.py")
    preflight_module = load_module("preflight", ROOT / "scripts/preflight_a2_source_action.py")
    adapter = load_module("adapter", ROOT / "scripts/normalise_fullenrich_response.py")
    classifier = load_module("social", ROOT / "scripts/classify_official_site_social_link.py")
    minimum_evaluator = load_module("minimum", ROOT / "scripts/evaluate_a2_minimum_package.py")
    role_classifier = load_module("roles", ROOT / "scripts/classify_a2_target_role.py")

    check("farrier_role_classifier_preserved", role_classifier.classify({"segment": "farrier", "source_role_title": "Independent Farrier", "evidence_flags": []})["priority"] == "primary")
    check("horse_owner_role_classifier_preserved", role_classifier.classify({"segment": "horse_owner", "source_role_title": "Stable Manager", "evidence_flags": []})["priority"] == "primary")

    source_index = {item["source_id"]: item for item in source["sources"]}
    unknown_routes = [item["source_id"] for item in gap.source_candidates("person.role_title", source_index, {"known_contact_name": False})]
    known_routes = [item["source_id"] for item in gap.source_candidates("person.role_title", source_index, {"known_contact_name": True})]
    email_routes = [item["source_id"] for item in gap.source_candidates("person.business_email", source_index, {})]
    mobile_routes = [item["source_id"] for item in gap.source_candidates("person.mobile_phone", source_index, {})]
    check("gap_plan_routes_unknown_to_search_before_apify", "fullenrich_people_search" in unknown_routes and unknown_routes.index("fullenrich_people_search") < unknown_routes.index("apify_harvestapi_linkedin_profile_search"))
    check("gap_plan_routes_known_to_lookup_before_apify", "fullenrich_people_lookup" in known_routes and known_routes.index("fullenrich_people_lookup") < known_routes.index("apify_harvestapi_linkedin_profile_search"))
    check("gap_plan_routes_work_email_to_fullenrich_before_apify", "fullenrich_contact_enrichment" in email_routes and email_routes.index("fullenrich_contact_enrichment") < email_routes.index("apify_harvestapi_email_search"))
    check("gap_plan_routes_mobile_to_fullenrich", "fullenrich_contact_enrichment" in mobile_routes and "apify_harvestapi_email_search" not in mobile_routes)

    common = {"candidate_id": "SYN-FE-001", "segment": "farrier", "operating_scope": "synthetic_test", "requested_at": "2026-09-06T13:07:00Z", "run_id": "SYN-RUN-001", "execution_mode": "local_fixture_simulation", "fixture_is_synthetic": True, "fixture_reference": "fixtures://fullenrich"}
    valid_search = {**common, "source_id": "fullenrich_people_search", "field_key": "person.role_title", "named_need": "find approved target role", "official_site_check": "completed_fixture", "named_contact_missing": True, "exact_organisation_domain": "example.test", "approved_target_roles": ["Owner"], "result_limit": 1}
    search_result = preflight_module.preflight(valid_search, source, cat, provider)
    check("search_fixture_preflight_passes", search_result["preflight_status"] == "allowed_local_fixture" and search_result["external_call_authorized"] is False)
    invalid_two = {**valid_search, "result_limit": 2}
    invalid_two_result = preflight_module.preflight(invalid_two, source, cat, provider)
    check("second_result_requires_reason", "second_contact_reason_required" in invalid_two_result["blocks"])
    valid_two = {**valid_search, "result_limit": 2, "second_contact_reason": "large_organisation"}
    check("two_results_with_reason_fixture_passes", preflight_module.preflight(valid_two, source, cat, provider)["preflight_status"] == "allowed_local_fixture")
    invalid_repeat = {**valid_search, "is_subsequent_role_search": True, "prior_search_outcome": "succeeded"}
    check("subsequent_search_requires_no_suitable_result", "subsequent_role_search_requires_no_suitable_prior_result" in preflight_module.preflight(invalid_repeat, source, cat, provider)["blocks"])
    invalid_role = {**valid_search, "approved_target_roles": ["Chief Technology Officer"]}
    check("unapproved_search_role_blocked", "unapproved_target_role" in preflight_module.preflight(invalid_role, source, cat, provider)["blocks"])
    invalid_pagination = {**valid_search, "offset": 1}
    check("search_pagination_blocked", "fullenrich_search_pagination_prohibited" in preflight_module.preflight(invalid_pagination, source, cat, provider)["blocks"])
    valid_lookup = {**common, "source_id": "fullenrich_people_lookup", "field_key": "person.role_title", "named_need": "verify known contact", "known_contact_name": True, "company_identifier": "example.test", "result_limit": 1}
    check("lookup_fixture_preflight_passes", preflight_module.preflight(valid_lookup, source, cat, provider)["preflight_status"] == "allowed_local_fixture")
    valid_enrich = {**common, "source_id": "fullenrich_contact_enrichment", "field_key": "person.mobile_phone", "named_need": "retrieve selected contact channels", "selected_contact": True, "selected_contact_count": 1, "requested_enrich_fields": ["contact.work_emails", "contact.phones"]}
    check("contact_enrichment_fixture_preflight_passes", preflight_module.preflight(valid_enrich, source, cat, provider)["preflight_status"] == "allowed_local_fixture")
    invalid_personal = {**valid_enrich, "requested_enrich_fields": ["contact.work_emails", "contact.phones", "contact.personal_emails"]}
    check("personal_email_request_blocked", "fullenrich_enrich_fields_must_be_work_email_and_phone_only" in preflight_module.preflight(invalid_personal, source, cat, provider)["blocks"])
    apify_request = {**common, "source_id": "apify_harvestapi_linkedin_profile_search", "field_key": "person.role_title", "named_need": "fallback role", "execution_mode": "preflight_only", "official_site_check": "completed_fixture", "named_role_gap": True, "max_items": 5, "automatic_query_segmentation": False}
    check("apify_requires_fullenrich_precondition", "fullenrich_precondition_required_before_apify" in preflight_module.preflight(apify_request, source, cat, provider)["blocks"])
    apify_request["fullenrich_status"] = "not_found"
    check("apify_still_runtime_blocked_after_precondition", preflight_module.preflight(apify_request, source, cat, provider)["preflight_status"] == "prepared_runtime_blocked")

    farrier_mobile_only = {
        "fixture_id": "SYN-FE-MOBILE-CONTACTABILITY",
        "segment": "farrier",
        "contact_path": "named_target",
        "research_exhausted": False,
        "field_states": {
            "person.professional_status": "verified",
            "organisation.business_name": "verified",
            "organisation.public_business_location": "verified",
            "organisation.service_area": "verified",
            "organisation.disciplines": "verified",
            "person.full_name": "verified",
            "person.role_title": "verified",
            "relationship.target_role_priority": "verified",
            "person.business_email": "not_found",
            "person.business_phone": "not_found",
            "person.mobile_phone": "verified"
        }
    }
    mobile_minimum_result = minimum_evaluator.evaluate(farrier_mobile_only, minimum)
    check("verified_mobile_satisfies_contact_channel", mobile_minimum_result["package_status"] == "review_ready" and not mobile_minimum_result["unsatisfied_contact_requirements"])

    fixtures = load(EVAL / "fixtures/fullenrich-responses.json")
    search_fixture = fixtures["people_search_response"]
    search_normalised = adapter.normalise({**search_fixture["request"], "provider_payload": search_fixture["provider_payload"]})
    search_contact = search_normalised["contacts"][0]
    check("search_response_minimised", search_normalised["result_count"] == 1 and search_normalised["contact_information_returned"] is False and set(search_contact) == {"provider_person_id", "full_name", "current_role", "organisation_name", "organisation_domain", "location", "professional_network_url"})
    enrich_fixture = fixtures["contact_enrichment_response"]
    enrich_normalised = adapter.normalise({**enrich_fixture["request"], "provider_payload": enrich_fixture["provider_payload"]})
    serialised_enrich = json.dumps(enrich_normalised)
    check("work_email_and_mobile_retained", enrich_normalised["contacts"][0]["business_email"] == "jordan@bluegrass.example" and enrich_normalised["contacts"][0]["mobile_phone"] == "+1 859 555 0101")
    check("personal_email_and_extra_profile_fields_removed", "private@example.test" not in serialised_enrich and "Example skill" not in serialised_enrich and "This must not be retained" not in serialised_enrich and enrich_normalised["unexpected_personal_email_discarded_count"] == 1)
    route = classifier.select_provider_input({"named_role_gap": True, "exact_organisation_domain": "example.test", "approved_target_roles": ["Owner"], "result_limit": 1})
    check("official_site_route_points_to_fullenrich_search", route["route"] == "fullenrich_people_search" and route["runtime_execution"] is False)

    active = load(ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json")
    active_rows = active.get("active_files", [])
    active_hashes_ok = all((ROOT / item["path"]).is_file() and sha(ROOT / item["path"]) == item.get("sha256") for item in active_rows)
    check("active_manifest_count_matches", active.get("active_file_count") == len(active_rows))
    check("active_manifest_hashes_match", active_hashes_ok)
    check("runtime_integrations_remain_disabled", active.get("permissions", {}).get("fullenrich") is False and active.get("permissions", {}).get("n8n") is False and active.get("permissions", {}).get("apify") is False)

    result = {
        "record_type": "a2_fullenrich_amendment_technical_validation",
        "validated_at": "2026-09-06T13:07:00Z",
        "profile": "equinet-a2-enrichment",
        "checks_total": len(checks),
        "checks_passed": sum(checks.values()),
        "checks": checks,
        "failures": failures,
        "external_calls": 0,
        "external_actions": 0,
        "status": "pass" if not failures else "fail",
    }
    EVAL.mkdir(parents=True, exist_ok=True)
    dump_path = EVAL / "technical-validation.json"
    dump_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
