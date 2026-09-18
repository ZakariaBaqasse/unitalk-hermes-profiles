#!/usr/bin/env python3
"""Preflight one A2 source action without performing external access."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from a2_wave2_contracts import load_active, load_json_strict
from classify_a2_target_role import ALIASES, norm

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "foundations/contracts/sources/a2-source-register-0.3.0.json"
CATALOGUE = ROOT / "foundations/contracts/business/a2-business-field-catalogue-0.3.0.json"
PROVIDERS = ROOT / "foundations/contracts/governance/a2-provider-and-cost-policy-0.3.0.json"

PROFILE_SEARCH_FIELDS = {
    "person.full_name", "person.role_title", "organisation.business_name",
    "organisation.public_business_location", "person.public_profile_urls",
}
FULLENRICH_CONTACT_FIELDS = {"person.business_email", "person.mobile_phone"}
OFFICIAL_SITE_BLOCKED_FIELDS = {
    "person.personal_email_candidate", "person.mobile_phone", "person.social_signals",
    "organisation.horses_served_per_month", "organisation.client_base_summary",
    "network.mutual_connections", "relationship.role",
    "relationship.target_role_priority", "relationship.buying_role_recommendation",
    "organisation.horse_count_band",
}
LOCAL_REUSE_SOURCES = {"a1_approved_handoff", "a1_directory_evidence_reuse"}
PROVIDER_SOURCES = {
    "fullenrich_people_search": "fullenrich_people_search",
    "fullenrich_people_lookup": "fullenrich_people_lookup",
    "fullenrich_contact_enrichment": "fullenrich_contact_enrichment",
    "apify_harvestapi_linkedin_profile_search": "apify_linkedin_profile_search",
    "apify_harvestapi_email_search": "apify_independent_email_search",
}
SECOND_CONTACT_REASONS = {"large_organisation", "shared_purchasing_or_operational_responsibility"}
FULLENRICH_FALLBACK_STATES = {"not_found", "insufficient_match", "unavailable_after_approved_retry"}


def load(path: Path) -> dict[str, Any]:
    return load_json_strict(path)


def hash_payload(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def bounded_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def field_allowed(source_id: str, field_key: str, source: dict[str, Any], field: dict[str, Any]) -> tuple[bool, str]:
    priority = field.get("priority_by_segment", {})
    if "do_not_collect" in priority.values() or str(field.get("collection_policy", "")).startswith("disabled"):
        return False, "field_is_do_not_collect"
    permitted = source.get("permitted_fields", [])
    if field_key in permitted:
        return True, "exact_field_allowlist_match"
    if source_id in LOCAL_REUSE_SOURCES:
        return True, "reuse_only_for_field_already_present_in_handoff"
    if source_id == "hubspot_authoritative_records":
        has_mapping = any(item.get("system") == "hubspot" for item in field.get("mapping_candidates", []))
        return has_mapping, "approved_hubspot_mapping_candidate_required"
    if source_id in {"equinet_authorized_first_party_data", "equinet_representative_confirmation"}:
        return True, "field_requires_asset_or_reviewer_specific_approval"
    if source_id == "prospect_official_website":
        return (field_key not in OFFICIAL_SITE_BLOCKED_FIELDS, "official_site_business_field_boundary")
    if source_id in {"fullenrich_people_search", "fullenrich_people_lookup"}:
        return (field_key in PROFILE_SEARCH_FIELDS, "fullenrich_people_profile_minimum_allowlist")
    if source_id == "fullenrich_contact_enrichment":
        return (field_key in FULLENRICH_CONTACT_FIELDS, "fullenrich_selected_contact_channel_allowlist")
    if source_id == "apify_harvestapi_linkedin_profile_search":
        return (field_key in PROFILE_SEARCH_FIELDS, "profile_search_minimum_allowlist")
    if source_id == "apify_harvestapi_email_search":
        if field_key=*** "person.business_email":
            return True, "professional_email_only"
        if field_key=*** "person.personal_email_candidate":
            return True, "personal_email_privacy_review_only"
        return False, "email_search_field_not_permitted"
    if source_id == "search_engine_discovery":
        return (field_key in {"organisation.website", "organisation.website_domain"}, "destination_discovery_only")
    return False, "field_not_permitted_by_source"


def preflight(request: dict[str, Any], register: dict[str, Any], catalogue: dict[str, Any], providers: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    blocks: list[str] = []
    warnings: list[str] = []
    source_id = request.get("source_id")
    field_key=reques...ey")
    execution_mode = request.get("execution_mode", "preflight_only")
    source_index = {item["source_id"]: item for item in register.get("sources", [])}
    field_index = {item["field_key"]: item for item in catalogue.get("fields", [])}
    source = source_index.get(source_id)
    field = field_index.get(field_key)

    if not request.get("candidate_id"):
        errors.append("candidate_id is required")
    if not request.get("named_need"):
        errors.append("named_need is required")
    if request.get("operating_scope") not in {"synthetic_test", "manual_no_integration_pilot", "integrated_pilot", "production"}:
        errors.append("unsupported operating_scope")
    if execution_mode not in {"preflight_only", "local_fixture_simulation", "live"}:
        errors.append("unsupported execution_mode")
    if source is None:
        errors.append(f"unknown source_id {source_id!r}")
    if field is None:
        errors.append(f"unknown field_key {field_key!r}")

    field_gate = "not_evaluated"
    if source and field:
        allowed, field_gate = field_allowed(source_id, field_key, source, field)
        if not allowed:
            blocks.append(field_gate)

    if source:
        status = source.get("register_status")
        if status in {"blocked", "not_selected", "not_available", "integration_pending"}:
            blocks.append(f"source_register_status_{status}")
        if source_id == "prospect_official_website":
            if request.get("official_site_check") not in {"planned", "completed_fixture", "completed"}:
                blocks.append("official_site_check_scope_missing")
            if request.get("open_linked_social_profile") is True:
                blocks.append("opening_linked_social_profile_is_not_authorised")
        if source_id == "fullenrich_people_search":
            if request.get("official_site_check") not in {"completed_fixture", "completed"}:
                blocks.append("fullenrich_people_search_must_follow_official_site_check")
            if request.get("named_contact_missing") is not True:
                blocks.append("named_contact_missing_required")
            domain = request.get("exact_organisation_domain")
            if not isinstance(domain, str) or not re.fullmatch(r"(?i)[a-z0-9](?:[a-z0-9-]{0,62}\.)+[a-z]{2,63}", domain.strip()):
                blocks.append("exact_organisation_domain_required")
            roles = request.get("approved_target_roles")
            segment = request.get("segment")
            if not isinstance(roles, list) or not roles:
                blocks.append("approved_target_role_required")
            elif segment not in ALIASES:
                blocks.append("approved_target_role_segment_required")
            else:
                approved_titles = {
                    norm(alias)
                    for groups in ALIASES[segment].values()
                    for aliases in groups.values()
                    for alias in aliases
                }
                if any(not isinstance(role, str) or norm(role) not in approved_titles for role in roles):
                    blocks.append("unapproved_target_role")
            if request.get("broad_role_free_search") is True:
                blocks.append("broad_role_free_search_prohibited")
            if request.get("offset") not in {None, 0} or request.get("search_after") is not None:
                blocks.append("fullenrich_search_pagination_prohibited")
            result_limit = bounded_int(request.get("result_limit", 1), 1)
            prior_unique = bounded_int(request.get("prior_unique_people_returned", 0), 0)
            if result_limit < 1 or result_limit > 2 or prior_unique + result_limit > 2:
                blocks.append("fullenrich_unique_people_limit_exceeded")
            if result_limit > 1 and request.get("second_contact_reason") not in SECOND_CONTACT_REASONS:
                blocks.append("second_contact_reason_required")
            if request.get("is_subsequent_role_search") is True and request.get("prior_search_outcome") not in {"not_found", "insufficient_match"}:
                blocks.append("subsequent_role_search_requires_no_suitable_prior_result")
        if source_id == "fullenrich_people_lookup":
            if request.get("known_contact_name") is not True:
                blocks.append("known_contact_name_required")
            if not request.get("company_identifier"):
                blocks.append("company_identifier_required")
            if request.get("name_role_and_organisation_verified") is True:
                blocks.append("people_lookup_not_needed_for_verified_identity")
            if bounded_int(request.get("result_limit", 1), 1) != 1:
                blocks.append("people_lookup_result_limit_must_equal_one")
        if source_id == "fullenrich_contact_enrichment":
            if request.get("selected_contact") is not True:
                blocks.append("selected_contact_required")
            if set(request.get("requested_enrich_fields") or []) != {"contact.work_emails", "contact.phones"}:
                blocks.append("fullenrich_enrich_fields_must_be_work_email_and_phone_only")
            count = bounded_int(request.get("selected_contact_count", 1), 1)
            if count < 1 or count > 2:
                blocks.append("selected_contact_limit_exceeded")
            if count > 1 and request.get("second_contact_reason") not in SECOND_CONTACT_REASONS:
                blocks.append("second_contact_reason_required")
        if source_id == "apify_harvestapi_linkedin_profile_search":
            if request.get("official_site_check") not in {"completed_fixture", "completed"}:
                blocks.append("named_role_gap_must_follow_official_site_check")
            if request.get("named_role_gap") is not True:
                blocks.append("named_role_gap_required")
            if request.get("automatic_query_segmentation") is True:
                blocks.append("automatic_query_segmentation_prohibited")
            if bounded_int(request.get("max_items", 5), 6) > 5:
                blocks.append("max_items_exceeds_provider_limit")
            if request.get("fullenrich_status") not in FULLENRICH_FALLBACK_STATES:
                blocks.append("fullenrich_precondition_required_before_apify")
        if source_id == "apify_harvestapi_email_search":
            if request.get("selected_profile_match") is not True:
                blocks.append("selected_profile_match_required")
            if int(request.get("max_searches", 1)) > 3:
                blocks.append("max_email_searches_exceeds_limit")
            if request.get("fullenrich_status") not in {"not_found", "unavailable_after_approved_retry"}:
                blocks.append("fullenrich_work_email_precondition_required_before_apify")
        if source_id == "search_engine_discovery" and request.get("retain_search_snippet") is True:
            blocks.append("search_snippet_cannot_be_retained_as_evidence")

    provider_missing: list[str] = []
    provider_block_reasons: list[str] = []
    if source_id in PROVIDER_SOURCES:
        provider = providers.get("providers", {}).get(PROVIDER_SOURCES[source_id], {})
        provider_group = "fullenrich" if source_id.startswith("fullenrich_") else "apify_harvestapi"
        if provider.get("runtime_status") != "active":
            provider_missing = list(providers.get("provider_activation_gates", {}).get(provider_group, providers.get("runtime_activation_gate", {}).get("all_required", [])))
            provider_block_reasons.append("provider_runtime_activation_gate_blocked")
        if providers.get("runtime_activation_gate", {}).get("external_calls_authorized") is not True:
            provider_block_reasons.append("provider_external_calls_not_authorized")

    fixture_ok = (
        execution_mode == "local_fixture_simulation"
        and request.get("fixture_is_synthetic") is True
        and bool(request.get("fixture_reference"))
    )
    if execution_mode == "local_fixture_simulation" and not fixture_ok:
        blocks.append("synthetic_fixture_reference_required")

    # Step 5C never executes live calls, even when a request claims runtime permission.
    if execution_mode == "live":
        blocks.append("step_5c_live_external_access_disabled")

    if errors:
        status = "invalid_request"
    elif blocks:
        status = "blocked"
    elif source_id in PROVIDER_SOURCES and fixture_ok:
        status = "allowed_local_fixture"
        warnings.append("Synthetic fixture validation does not satisfy or bypass the live provider activation gates.")
    elif source_id in PROVIDER_SOURCES:
        status = "prepared_runtime_blocked"
    elif fixture_ok:
        status = "allowed_local_fixture"
    elif source_id in LOCAL_REUSE_SOURCES:
        status = "allowed_local_reuse"
    else:
        status = "preflight_passed_execution_not_authorized"
        warnings.append("Step 5C records policy readiness only; runtime activation belongs to Step 6 or later.")

    effective_blocks = sorted(set(blocks + ([] if fixture_ok else provider_block_reasons)))
    audit = {
        "actor_profile": request.get("actor_profile", "equinet-a2-enrichment"),
        "trigger": request.get("trigger", request.get("named_need")),
        "timestamp": request.get("requested_at"),
        "run_id": request.get("run_id"),
        "source_id": source_id,
        "input_scope": {"candidate_id": request.get("candidate_id"), "field_key": field_key, "named_need": request.get("named_need")},
        "source_urls": request.get("source_urls", []),
        "output_reference": request.get("output_reference"),
        "approval_state": "fixture_only" if fixture_ok else (source.get("business_approval") if source else None),
        "status": status,
        "retries": bounded_int(request.get("retry_number", 0), 0),
        "usage_and_cost": {"api_calls": 0, "cost_amount": 0, "currency": "USD", "cost_status": "no_external_call"},
    }
    audit_complete = bool(audit["actor_profile"] and audit["trigger"] and audit["timestamp"] and audit["run_id"] and audit["source_id"])

    result = {
        "preflight_version": "0.1.0-draft.1",
        "candidate_id": request.get("candidate_id"),
        "source_id": source_id,
        "field_key": field_key,
        "named_need": request.get("named_need"),
        "execution_mode": execution_mode,
        "preflight_status": status,
        "field_gate": field_gate,
        "register_status": source.get("register_status") if source else None,
        "business_approval": source.get("business_approval") if source else None,
        "source_rights_preflight": source.get("source_rights_preflight") if source else None,
        "runtime_readiness": source.get("runtime_readiness") if source else None,
        "allowed_access_modes": source.get("allowed_access_modes", []) if source else [],
        "limits": source.get("limits", {}) if source else {},
        "stop_conditions": source.get("stop_conditions", []) if source else [],
        "audit_requirements": source.get("audit_requirements", []) if source else [],
        "provider_missing_activation_gates": provider_missing,
        "live_runtime_blocks": sorted(set(provider_block_reasons)),
        "blocks": effective_blocks,
        "warnings": warnings,
        "audit": audit,
        "audit_complete": audit_complete,
        "external_call_authorized": False,
        "external_calls": 0,
        "external_actions": 0,
        "outreach_authorized": False,
        "crm_write_authorized": False,
    }
    result["preflight_sha256"] = hash_payload({k: v for k, v in result.items() if k != "preflight_sha256"})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--register", type=Path, default=REGISTER)
    parser.add_argument("--catalogue", type=Path, default=CATALOGUE)
    parser.add_argument("--providers", type=Path, default=PROVIDERS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    request = load(args.request)
    register = load_active(str(REGISTER.relative_to(ROOT))) if args.register == REGISTER else load(args.register)
    catalogue = load_active(str(CATALOGUE.relative_to(ROOT))) if args.catalogue == CATALOGUE else load(args.catalogue)
    providers = load_active(str(PROVIDERS.relative_to(ROOT))) if args.providers == PROVIDERS else load(args.providers)
    result = preflight(request, register, catalogue, providers)
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if result["preflight_status"] == "invalid_request" else 0


if __name__ == "__main__":
    raise SystemExit(main())
