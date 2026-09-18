#!/usr/bin/env python3
"""Preflight one A2 source action without performing external access."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from a2_wave2_contracts import load_active, load_json_strict

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "foundations/contracts/sources/a2-source-register-0.2.0.json"
CATALOGUE = ROOT / "foundations/contracts/business/a2-business-field-catalogue-0.2.0.json"
PROVIDERS = ROOT / "foundations/contracts/governance/a2-provider-and-cost-policy-0.2.0.json"

PROFILE_SEARCH_FIELDS = {
    "person.full_name", "person.role_title", "organisation.business_name",
    "organisation.public_business_location", "person.public_profile_urls",
}
OFFICIAL_SITE_BLOCKED_FIELDS = {
    "person.personal_email_candidate", "person.mobile_phone", "person.social_signals",
    "organisation.horses_served_per_month", "organisation.client_base_summary",
    "network.mutual_connections", "relationship.role",
    "relationship.target_role_priority", "relationship.buying_role_recommendation",
    "organisation.horse_count_band",
}
LOCAL_REUSE_SOURCES = {"a1_approved_handoff", "a1_directory_evidence_reuse"}
PROVIDER_SOURCES = {
    "apify_harvestapi_linkedin_profile_search": "apify_linkedin_profile_search",
    "apify_harvestapi_email_search": "apify_independent_email_search",
}


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
        if status in {"blocked", "not_selected", "integration_pending"}:
            blocks.append(f"source_register_status_{status}")
        if source_id == "prospect_official_website":
            if request.get("official_site_check") not in {"planned", "completed_fixture", "completed"}:
                blocks.append("official_site_check_scope_missing")
            if request.get("open_linked_social_profile") is True:
                blocks.append("opening_linked_social_profile_is_not_authorised")
        if source_id == "apify_harvestapi_linkedin_profile_search":
            if request.get("official_site_check") not in {"completed_fixture", "completed"}:
                blocks.append("named_role_gap_must_follow_official_site_check")
            if request.get("named_role_gap") is not True:
                blocks.append("named_role_gap_required")
            if request.get("automatic_query_segmentation") is True:
                blocks.append("automatic_query_segmentation_prohibited")
            if bounded_int(request.get("max_items", 5), 6) > 5:
                blocks.append("max_items_exceeds_provider_limit")
        if source_id == "apify_harvestapi_email_search":
            if request.get("selected_profile_match") is not True:
                blocks.append("selected_profile_match_required")
            if int(request.get("max_searches", 1)) > 3:
                blocks.append("max_email_searches_exceeds_limit")
        if source_id == "search_engine_discovery" and request.get("retain_search_snippet") is True:
            blocks.append("search_snippet_cannot_be_retained_as_evidence")

    provider_missing: list[str] = []
    provider_block_reasons: list[str] = []
    if source_id in PROVIDER_SOURCES:
        provider = providers.get("providers", {}).get(PROVIDER_SOURCES[source_id], {})
        if str(provider.get("runtime_status", "")).startswith("blocked"):
            provider_missing = list(providers.get("runtime_activation_gate", {}).get("all_required", []))
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
