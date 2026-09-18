#!/usr/bin/env python3
"""Normalise and validate bounded A2 observations without external actions."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from a2_wave2_contracts import load_active, load_json_strict
from classify_official_site_social_link import classify as classify_social_link

CATALOGUE = ROOT / "foundations/contracts/business/a2-business-field-catalogue-0.3.1.json"
SOURCE_REGISTER = ROOT / "foundations/contracts/sources/a2-source-register-0.3.1.json"

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
ALLOWED_AVAILABILITY = {"not_checked", "unavailable", "not_found", "available", "error"}
ALLOWED_ACTION_STATES = {
    "allowed_local_fixture", "allowed_local_reuse", "preflight_passed_execution_not_authorized",
    "completed", "completed_fixture",
}
TRACKING_PREFIXES = ("utm_",)
TRACKING_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


class ReviewRequired(ValueError):
    """Raised when an observation must be preserved for human review."""


def load(path: Path) -> dict[str, Any]:
    return load_json_strict(path)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def normalise_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must be absolute HTTP(S)")
    host = (parsed.hostname or "").lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    port = f":{parsed.port}" if parsed.port else ""
    clean_query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k.lower() not in TRACKING_KEYS and not k.lower().startswith(TRACKING_PREFIXES)]
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit(("https", host + port, path, urlencode(clean_query), ""))


def normalise_email(value: str) -> str:
    email = value.strip().lower()
    if not EMAIL_RE.fullmatch(email):
        raise ValueError("invalid email syntax")
    return email


def normalise_phone(value: str, country_code: str = "US") -> str:
    digits = re.sub(r"\D", "", value)
    if country_code == "US" and len(digits) == 10:
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    if value.strip().startswith("+") and 8 <= len(digits) <= 15:
        return "+" + digits
    raise ValueError("phone cannot be safely normalised")


def clean_text(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("value must be text")
    cleaned = " ".join(value.split())
    if not cleaned:
        raise ValueError("value must not be empty")
    return cleaned


def normalise_value(field: dict[str, Any], observation: dict[str, Any]) -> Any:
    key = field["field_key"]
    value = observation.get("raw_value")
    value_type = field.get("value_type")
    if key.endswith("public_profile_urls"):
        values = value if isinstance(value, list) else [value]
        out = []
        for raw in values:
            classified = classify_social_link({
                "source": observation.get("source_id"),
                "explicitly_linked": observation.get("explicitly_linked") is True,
                "url": raw,
                "page_context": observation.get("page_context"),
                "named_role_gap": observation.get("named_role_gap") is True,
            })
            if classified["action"] == "hold_attribution_for_review":
                raise ReviewRequired(classified["reason"])
            if classified["action"] != "retain_url_only":
                raise ValueError(f"social link rejected: {classified['reason']}")
            if classified["canonical_field"] != key:
                raise ReviewRequired("social link attribution conflicts with field scope")
            out.append(classified["normalised_url"])
        return sorted(set(out))
    if "email" in key:
        return normalise_email(clean_text(value))
    if "phone" in key:
        return normalise_phone(clean_text(value), observation.get("country_code", "US"))
    if key == "organisation.horse_count":
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError("horse count must be an explicit positive integer")
        return value
    if key == "organisation.horse_count_band":
        raise ValueError("horse-count band is deprecated; horse_count_range is not used by A2")
    if key == "organisation.public_business_location":
        if not isinstance(value, dict) or not isinstance(value.get("components"), list):
            raise ValueError("business location must contain a components array")
        components = {
            str(item.get("key")): item.get("value")
            for item in value["components"]
            if isinstance(item, dict) and item.get("key") and item.get("value") not in {None, ""}
        }
        if not components.get("state_region") or not components.get("country_code"):
            raise ValueError("business location requires state_region and country_code; complete address is preferred when available")
        return {"components": [{"key": component, "value": components[component]} for component in sorted(components)]}
    if key in {"organisation.website", "organisation.website_domain"}:
        url = normalise_url(clean_text(value))
        return (urlsplit(url).hostname or "") if key.endswith("website_domain") else url
    if value_type in {"array_string", "string_array"}:
        values = value if isinstance(value, list) else [value]
        return sorted({clean_text(item) for item in values}, key=str.casefold)
    if value_type == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("value must be an integer")
        return value
    if value_type in {"string", "enum", None}:
        cleaned = clean_text(value)
        allowed = field.get("enum_values")
        if allowed and cleaned not in allowed:
            raise ValueError(f"value is not in the approved vocabulary: {cleaned}")
        return cleaned
    return value


def validate_batch(request: dict[str, Any], catalogue: dict[str, Any], register: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    segment = request.get("segment")
    scope = request.get("operating_scope")
    observations = request.get("observations")
    if segment not in catalogue.get("segments", []):
        errors.append(f"unsupported segment {segment!r}")
    if scope not in {"synthetic_test", "manual_no_integration_pilot", "integrated_pilot", "production"}:
        errors.append(f"unsupported operating_scope {scope!r}")
    if not isinstance(observations, list):
        errors.append("observations must be an array")
        observations = []

    field_index = {item["field_key"]: item for item in catalogue.get("fields", [])}
    source_ids = {item["source_id"] for item in register.get("sources", [])}
    results: list[dict[str, Any]] = []

    for index, obs in enumerate(observations, 1):
        item_errors: list[str] = []
        key = obs.get("field_key")
        field = field_index.get(key)
        availability = obs.get("availability_status", "available")
        fact_type = obs.get("fact_type", "direct_fact")
        action_status = obs.get("source_action_status")
        source_receipt = obs.get("source_preflight")
        source_id = obs.get("source_id")
        evidence_id = obs.get("evidence_id")
        action = "accept_for_wave3_evidence_assessment"
        preliminary = "ready_for_evidence_assessment"
        normalised = None
        field_state = "present_unverified"
        privacy_state = "not_sensitive"

        if not obs.get("observation_id"):
            item_errors.append("observation_id is required")
        if field is None:
            item_errors.append("unknown field_key")
        if source_id not in source_ids:
            item_errors.append("unknown source_id")
        if availability not in ALLOWED_AVAILABILITY:
            item_errors.append("unsupported availability_status")
        if not isinstance(source_receipt, dict):
            item_errors.append("hashed source_preflight receipt is required")
        else:
            supplied_hash = source_receipt.get("preflight_sha256")
            calculated_hash = canonical_hash({k: v for k, v in source_receipt.items() if k != "preflight_sha256"})
            if supplied_hash != calculated_hash:
                item_errors.append("source_preflight receipt hash mismatch")
            if source_receipt.get("candidate_id") != request.get("candidate_id") or source_receipt.get("source_id") != source_id or source_receipt.get("field_key") != key:
                item_errors.append("source_preflight receipt does not match observation scope")
            action_status = source_receipt.get("preflight_status")
            if source_receipt.get("external_call_authorized") is not False or source_receipt.get("external_actions") != 0:
                item_errors.append("source_preflight receipt exceeds Step 5C action boundary")
        if action_status not in ALLOWED_ACTION_STATES:
            item_errors.append("source action did not pass an approved local or runtime gate")
        if availability == "available" and action_status not in {"allowed_local_fixture", "allowed_local_reuse", "completed", "completed_fixture"}:
            item_errors.append("available value requires an executed or fixture-backed source receipt")
        if field and segment not in field.get("allowed_segments", []):
            item_errors.append("field is not applicable to this segment")
        if field and ("do_not_collect" in field.get("priority_by_segment", {}).values() or str(field.get("collection_policy", "")).startswith("disabled")):
            item_errors.append("field is do_not_collect")
        if availability == "available" and not evidence_id:
            item_errors.append("evidence_id is required for an available observation")
        if fact_type not in {"direct_fact", "authorised_confirmation", "provider_result", "derived_from_explicit_value", "reasonable_inference"}:
            item_errors.append("unsupported fact_type")

        if availability != "available":
            if obs.get("raw_value") not in {None, ""}:
                item_errors.append("non-available observation cannot contain a value")
            field_state = {
                "not_checked": "unknown", "unavailable": "unavailable", "not_found": "not_found", "error": "error"
            }.get(availability, "unknown")
            action = "retain_state_only"
            preliminary = "not_applicable"
        elif field:
            if fact_type == "reasonable_inference" and ("email" in key or "phone" in key or key in {"organisation.horse_count", "relationship.role", "relationship.target_role_priority"}):
                item_errors.append("inference is prohibited for this field")
            if "email" in key and obs.get("collection_method") == "generated_pattern":
                item_errors.append("generated email patterns are prohibited")
            if key == "person.personal_email_candidate":
                privacy_state = "held_for_human_privacy_review"
                action = "hold_for_privacy_review"
                preliminary = "privacy_review_required"
            if key in {"person.business_email", "organisation.business_email"} and obs.get("email_kind") == "personal":
                privacy_state = "held_for_human_privacy_review"
                action = "hold_for_privacy_review"
                preliminary = "privacy_review_required"
            if key == "person.role_title" and obs.get("role_current") is not True:
                action = "hold_for_human_review"
                preliminary = "current_role_not_established"
            if key in {"relationship.role", "relationship.target_role_priority"} and not obs.get("supporting_role_evidence_ids"):
                item_errors.append("role classification requires supporting role evidence")
            if key == "relationship.buying_role_recommendation" and not obs.get("recommendation_basis_evidence_ids"):
                item_errors.append("buying-role recommendation requires supporting evidence")
            if key == "organisation.horse_count" and source_id not in {
                "a1_approved_handoff",
                "equinet_representative_confirmation",
                "prospect_official_website",
                "hubspot_authoritative_records",
            }:
                item_errors.append("horse count requires HubSpot owner_horse_count for an existing match or explicit approved evidence for a net-new prospect")
            try:
                normalised = normalise_value(field, obs)
            except ReviewRequired as exc:
                action = "hold_for_human_review"
                preliminary = "review_required"
                normalised = None
                item_errors.append(str(exc))
            except (ValueError, TypeError) as exc:
                item_errors.append(str(exc))

        if item_errors and action != "hold_for_human_review":
            action = "reject_observation"
            preliminary = "invalid"
            field_state = "error"
            normalised = None

        result = {
            "observation_id": obs.get("observation_id", f"OBS-{index:03d}"),
            "field_key": key,
            "entity_id": obs.get("entity_id"),
            "raw_value": obs.get("raw_value"),
            "normalised_value": normalised,
            "availability_status": availability,
            "field_state": field_state,
            "preliminary_verification_status": preliminary,
            "action": action,
            "privacy_state": privacy_state,
            "source_id": source_id,
            "source_url": obs.get("source_url"),
            "evidence_id": evidence_id,
            "errors": item_errors,
            "external_actions": 0,
        }
        results.append(result)

    # Materially different accepted values for the same target field require review.
    groups: dict[tuple[Any, Any], list[dict[str, Any]]] = {}
    for item in results:
        if item["normalised_value"] is not None and item["action"] != "reject_observation":
            groups.setdefault((item["entity_id"], item["field_key"]), []).append(item)
    for (entity_id, field_key), group in groups.items():
        if field_index.get(field_key, {}).get("value_type") == "string_array":
            continue
        fingerprints = {json.dumps(item["normalised_value"], sort_keys=True, ensure_ascii=False) for item in group}
        if len(fingerprints) > 1:
            for item in group:
                item["field_state"] = "conflict"
                item["preliminary_verification_status"] = "conflict_requires_review"
                item["action"] = "hold_for_human_review"

    for item in results:
        field = field_index.get(item["field_key"], {})
        assessment_seed = f"{request.get('candidate_id')}|{item.get('entity_id')}|{item.get('field_key')}"
        item["field_assessment_candidate"] = {
            "field_assessment_id": "A2-FLD-" + hashlib.sha256(assessment_seed.encode()).hexdigest()[:16].upper(),
            "field_key": item.get("field_key"),
            "entity_id": item.get("entity_id"),
            "scope": field.get("scope"),
            "value_type": field.get("value_type"),
            "sensitivity_classification": field.get("data_category"),
            "presence_status": "known" if item.get("normalised_value") is not None else "unknown",
            "availability_status": item.get("availability_status"),
            "field_quality_status": (
                "invalid" if item["action"] == "reject_observation" else
                "conflict" if item["field_state"] == "conflict" else
                "gap" if item["normalised_value"] is None else
                "partial"
            ),
            "canonical_mutation_authorized": False,
        }

    rejected = sum(item["action"] == "reject_observation" for item in results)
    held = sum(item["action"] in {"hold_for_human_review", "hold_for_privacy_review"} for item in results)
    if errors:
        status = "invalid_request"
    elif rejected and held:
        status = "completed_with_holds_and_rejections"
    elif rejected:
        status = "completed_with_rejections"
    elif held:
        status = "completed_with_holds"
    else:
        status = "completed"
    output = {
        "batch_version": "0.1.0-draft.1",
        "candidate_id": request.get("candidate_id"),
        "segment": segment,
        "operating_scope": scope,
        "batch_status": status,
        "observation_count": len(results),
        "accepted_count": len(results) - rejected - held,
        "held_count": held,
        "rejected_count": rejected,
        "observations": results,
        "batch_errors": errors,
        "final_confidence_assigned": False,
        "canonical_record_mutated": False,
        "automatic_a1_score_change": False,
        "outreach_authorized": False,
        "crm_write_authorized": False,
        "external_calls": 0,
        "external_actions": 0,
    }
    output["batch_sha256"] = canonical_hash({k: v for k, v in output.items() if k != "batch_sha256"})
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--catalogue", type=Path, default=CATALOGUE)
    parser.add_argument("--register", type=Path, default=SOURCE_REGISTER)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    request = load(args.request)
    catalogue = load_active(str(CATALOGUE.relative_to(ROOT))) if args.catalogue == CATALOGUE else load(args.catalogue)
    register = load_active(str(SOURCE_REGISTER.relative_to(ROOT))) if args.register == SOURCE_REGISTER else load(args.register)
    result = validate_batch(request, catalogue, register)
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if result["batch_status"] == "invalid_request" else 0


if __name__ == "__main__":
    raise SystemExit(main())
