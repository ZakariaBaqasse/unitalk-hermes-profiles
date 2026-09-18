#!/usr/bin/env python3
"""Build a bounded A2 field-level enrichment plan without external access."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from a2_wave2_contracts import load_active, load_json_strict

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "foundations/contracts/business/a2-business-field-catalogue-0.3.1.json"
PACKAGES = ROOT / "foundations/contracts/business/a2-minimum-data-packages-0.3.1.json"
SOURCES = ROOT / "foundations/contracts/sources/a2-source-register-0.3.1.json"

ALLOWED_STATES = {
    "verified", "present_unverified", "missing", "unknown", "not_found",
    "unavailable", "conflict", "error",
}
NEED_BY_STATE = {
    "present_unverified": "verification",
    "missing": "gap",
    "unknown": "gap",
    "not_found": "gap",
    "unavailable": "availability",
    "conflict": "conflict",
    "error": "technical_error",
}
SOURCE_SEQUENCE = [
    "a1_approved_handoff",
    "a1_directory_evidence_reuse",
    "hubspot_authoritative_records",
    "prospect_official_website",
    "fullenrich_people_search",
    "fullenrich_people_lookup",
    "fullenrich_contact_enrichment",
    "apify_harvestapi_linkedin_profile_search",
    "apify_harvestapi_email_search",
    "search_engine_discovery",
]
PROFILE_FIELDS = {
    "person.full_name", "person.role_title", "person.public_profile_urls",
    "organisation.business_name", "organisation.public_business_location",
}
CONTACT_ENRICHMENT_FIELDS = {"person.business_email", "person.mobile_phone"}


def load(path: Path) -> dict[str, Any]:
    return load_json_strict(path)


def sha256_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def request_from_canonical(request: dict[str, Any]) -> dict[str, Any]:
    record = request.get("record")
    if not isinstance(record, dict):
        return request
    candidate = record.get("source_handoff", {}).get("handoff_snapshot", {}).get("candidate_snapshot", {})
    scope = record.get("enrichment_scope", {})
    derived_states: dict[str, dict[str, str]] = {}
    for assessment in record.get("field_assessments", []):
        availability = assessment.get("availability_status", "not_checked")
        presence = assessment.get("presence_status", "unknown")
        quality = assessment.get("field_quality_status")
        proposal = assessment.get("proposed_resolution") or {}
        observations = assessment.get("observations") or []
        verification = proposal.get("verification_status") or (observations[-1].get("verification_status") if observations else "unassessed")
        freshness = proposal.get("freshness_status") or (observations[-1].get("freshness_status") if observations else "not_assessed")
        if quality == "conflict" or proposal.get("conflict_status") not in {None, "none"}:
            state = "conflict"
        elif availability in {"not_found", "unavailable", "error"}:
            state = availability
        elif presence == "known" and verification == "verified" and freshness != "stale":
            state = "verified"
        elif presence == "known":
            state = "present_unverified"
        else:
            state = "unknown"
        derived_states[assessment.get("field_key")] = {"state": state, "freshness_status": freshness}
    merged = {
        "candidate_id": candidate.get("candidate_id") or record.get("record_metadata", {}).get("a2_record_id"),
        "segment": candidate.get("segment"),
        "operating_scope": scope.get("operating_scope"),
        "a2_eligibility_status": request.get("wave1_eligibility_result", {}).get("a2_eligibility_status") or record.get("duplicate_and_eligibility", {}).get("a2_eligibility_status"),
        "enrichment_mode": scope.get("mode", "default_minimum_package"),
        "requested_field_keys": scope.get("requested_field_keys", []),
        "field_states": derived_states,
        "input_record_sha256": sha256_json(record),
    }
    for key in ("contact_path", "target_role_not_found", "research_exhausted", "requested_field_keys", "enrichment_mode"):
        if key in request:
            merged[key] = request[key]
    return merged


def field_state(value: Any) -> tuple[str, str]:
    if isinstance(value, str):
        return value, "not_assessed"
    if isinstance(value, dict):
        return str(value.get("state", "unknown")), str(value.get("freshness_status", "not_assessed"))
    return "unknown", "not_assessed"


def source_candidates(field_key: str, source_index: dict[str, dict[str, Any]], request: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[str] = [
        "a1_approved_handoff",
        "a1_directory_evidence_reuse",
        "hubspot_authoritative_records",
        "prospect_official_website",
    ]
    if field_key in PROFILE_FIELDS:
        candidates.append("fullenrich_people_lookup" if request.get("known_contact_name") is True else "fullenrich_people_search")
        candidates.append("apify_harvestapi_linkedin_profile_search")
    if field_key in CONTACT_ENRICHMENT_FIELDS:
        candidates.append("fullenrich_contact_enrichment")
    if field_key == "person.business_email":
        candidates.append("apify_harvestapi_email_search")
    if field_key in {"organisation.website", "organisation.website_domain"}:
        candidates.append("search_engine_discovery")
    ordered = []
    for source_id in SOURCE_SEQUENCE:
        if source_id not in candidates or source_id not in source_index:
            continue
        source = source_index[source_id]
        ordered.append({
            "source_id": source_id,
            "register_status": source.get("register_status"),
            "runtime_readiness": source.get("runtime_readiness"),
            "external_access_planned": False,
        })
    return ordered


def analyse(request: dict[str, Any], catalogue: dict[str, Any], packages: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    request = request_from_canonical(request)
    errors: list[str] = []
    blocked_fields: list[dict[str, str]] = []
    segment = request.get("segment")
    scope = request.get("operating_scope")
    mode = request.get("enrichment_mode", "default_minimum_package")
    eligibility = request.get("a2_eligibility_status")
    field_states = request.get("field_states") if isinstance(request.get("field_states"), dict) else {}
    catalogue_index = {item["field_key"]: item for item in catalogue.get("fields", [])}
    source_index = {item["source_id"]: item for item in sources.get("sources", [])}

    if segment not in catalogue.get("segments", []):
        errors.append(f"unsupported segment {segment!r}")
    if scope not in {"synthetic_test", "manual_no_integration_pilot", "integrated_pilot", "production"}:
        errors.append(f"unsupported operating_scope {scope!r}")
    if mode not in {"default_minimum_package", "targeted_fields"}:
        errors.append(f"unsupported enrichment_mode {mode!r}")
    if eligibility not in {"eligible", "hold", "blocked"}:
        errors.append(f"unsupported a2_eligibility_status {eligibility!r}")
    for key, value in field_states.items():
        state, _ = field_state(value)
        if key not in catalogue_index:
            errors.append(f"unknown field_key {key!r}")
        if state not in ALLOWED_STATES:
            errors.append(f"unsupported field state {state!r} for {key}")

    requested = request.get("requested_field_keys", [])
    if not isinstance(requested, list) or any(not isinstance(key, str) for key in requested):
        errors.append("requested_field_keys must be an array of strings")
        requested = []
    if mode == "targeted_fields" and not requested:
        errors.append("targeted_fields mode requires at least one requested field")

    if errors:
        return _result(request, "invalid_request", [], blocked_fields, errors, None)
    if eligibility == "blocked":
        return _result(request, "blocked", [], blocked_fields, ["Wave 1 eligibility blocks research"], None)
    if eligibility == "hold":
        return _result(request, "held", [], blocked_fields, ["Wave 1 eligibility requires resolution before research"], None)

    package_key = f"{segment}_review_ready"
    package = packages.get("packages", {}).get(package_key)
    if not package:
        return _result(request, "invalid_request", [], blocked_fields, [f"missing package {package_key}"], None)

    target_fields: list[tuple[str, str, list[str]]] = []
    if mode == "default_minimum_package":
        for key in package.get("required_verified_fields", []):
            target_fields.append((key, "required", []))
        contact_path_name = request.get("contact_path", "named_target")
        contact_path = package.get("contact_paths", {}).get(contact_path_name)
        if not contact_path:
            return _result(request, "invalid_request", [], blocked_fields, [f"unsupported contact_path {contact_path_name!r}"], None)
        unmet_flags = [flag for flag, expected in contact_path.get("required_flags", {}).items() if request.get(flag) != expected]
        if unmet_flags:
            return _result(
                request,
                "held",
                [],
                blocked_fields,
                [f"contact-path prerequisite not established: {flag}" for flag in unmet_flags],
                {"package": package_key, "contact_path": contact_path_name, "research_exhausted": request.get("research_exhausted") is True},
            )
        for key in contact_path.get("required_verified_fields", []):
            target_fields.append((key, "conditional_required", []))
        alternatives = list(contact_path.get("at_least_one_verified_field", []))
        if alternatives and not any(field_state(field_states.get(key))[0] == "verified" for key in alternatives):
            target_fields.append((alternatives[0], "conditional_required", alternatives[1:]))
        for key in contact_path.get("preferred_verified_fields", []):
            if field_state(field_states.get(key))[0] != "verified":
                target_fields.append((key, "optional", []))
        for key in contact_path.get("research_target_fields", []):
            if field_state(field_states.get(key))[0] != "verified":
                target_fields.append((key, "conditional_required", []))
    else:
        for key in requested:
            field = catalogue_index.get(key)
            if not field or segment not in field.get("allowed_segments", []):
                blocked_fields.append({"field_key": key, "reason": "unknown_or_not_applicable"})
                continue
            priority = field.get("priority_by_segment", {}).get(segment)
            if priority == "do_not_collect" or str(field.get("collection_policy", "")).startswith("disabled"):
                blocked_fields.append({"field_key": key, "reason": "do_not_collect"})
                continue
            target_fields.append((key, priority or "optional", []))

    # Keep first occurrence and preserve the strongest requirement.
    rank = {"required": 0, "conditional_required": 1, "optional": 2}
    dedup: dict[str, tuple[str, list[str]]] = {}
    for key, priority, alternatives in target_fields:
        if key not in dedup or rank.get(priority, 9) < rank.get(dedup[key][0], 9):
            dedup[key] = (priority, alternatives)

    items = []
    for key, (priority, alternatives) in dedup.items():
        field = catalogue_index.get(key)
        if not field:
            errors.append(f"package references unknown field {key!r}")
            continue
        configured_priority = field.get("priority_by_segment", {}).get(segment)
        if configured_priority == "do_not_collect" or str(field.get("collection_policy", "")).startswith("disabled"):
            blocked_fields.append({"field_key": key, "reason": "do_not_collect"})
            continue
        state, freshness = field_state(field_states.get(key))
        if state == "verified" and freshness != "stale":
            continue
        need_type = "freshness" if freshness == "stale" else NEED_BY_STATE.get(state, "gap")
        item = {
            "plan_item_id": f"PLAN-{len(items)+1:03d}",
            "field_key": key,
            "alternative_field_keys": alternatives,
            "priority": priority,
            "current_state": state,
            "freshness_status": freshness,
            "need_type": need_type,
            "source_candidates": source_candidates(key, source_index, request),
            "external_action_authorized": False,
        }
        items.append(item)

    if errors:
        status = "invalid_request"
    elif blocked_fields and not items:
        status = "blocked"
    elif not items:
        status = "no_research_needed"
    elif request.get("research_exhausted") is True:
        status = "review_required"
    else:
        status = "research_required"

    package_snapshot = {
        "package": package_key,
        "required_field_count": len(package.get("required_verified_fields", [])),
        "contact_path": request.get("contact_path", "named_target"),
        "research_exhausted": request.get("research_exhausted") is True,
    }
    return _result(request, status, items, blocked_fields, errors, package_snapshot)


def _result(request: dict[str, Any], status: str, items: list[dict[str, Any]], blocked: list[dict[str, str]], errors: list[str], package: dict[str, Any] | None) -> dict[str, Any]:
    result = {
        "plan_version": "0.2.0",
        "candidate_id": request.get("candidate_id"),
        "input_record_sha256": request.get("input_record_sha256"),
        "segment": request.get("segment"),
        "operating_scope": request.get("operating_scope"),
        "plan_status": status,
        "minimum_package": package,
        "plan_items": items,
        "blocked_fields": blocked,
        "errors": errors,
        "automatic_rejection": False,
        "automatic_a1_score_change": False,
        "outreach_authorized": False,
        "crm_write_authorized": False,
        "external_calls": 0,
        "external_actions": 0,
    }
    result["plan_sha256"] = sha256_json({k: v for k, v in result.items() if k != "plan_sha256"})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--catalogue", type=Path, default=CATALOGUE)
    parser.add_argument("--packages", type=Path, default=PACKAGES)
    parser.add_argument("--sources", type=Path, default=SOURCES)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    request = load(args.request)
    catalogue = load_active(str(CATALOGUE.relative_to(ROOT))) if args.catalogue == CATALOGUE else load(args.catalogue)
    packages = load_active(str(PACKAGES.relative_to(ROOT))) if args.packages == PACKAGES else load(args.packages)
    sources = load_active(str(SOURCES.relative_to(ROOT))) if args.sources == SOURCES else load(args.sources)
    result = analyse(request, catalogue, packages, sources)
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if result["plan_status"] == "invalid_request" else 0


if __name__ == "__main__":
    raise SystemExit(main())
