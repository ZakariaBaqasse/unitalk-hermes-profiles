#!/usr/bin/env python3
"""Assemble, validate, rank and package Equinet A1 Prospect Candidates for human review."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker

SKILL_DIR = Path(__file__).resolve().parents[1]
PROFILE_DIR = Path(__file__).resolve().parents[3]
INPUT_SCHEMA = SKILL_DIR / "references" / "review-input.schema.json"
PACKAGE_SCHEMA = SKILL_DIR / "references" / "review-package.schema.json"
CANDIDATE_SCHEMA = PROFILE_DIR / "skills" / "a1-prospect-data-contract" / "references" / "prospect-candidate.schema.json"
LOCATION_POLICY = PROFILE_DIR / "configurations" / "geography" / "location-resolution-v1.json"
VALIDATOR_DIR = PROFILE_DIR / "skills" / "a1-prospect-data-contract" / "scripts"
if str(VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(VALIDATOR_DIR))
from validate_candidate import cross_reference_errors  # noqa: E402

with LOCATION_POLICY.open("r", encoding="utf-8") as handle:
    LOCATION_RULES = json.load(handle)
APPROVED_COUNTRY_CODES = set(LOCATION_RULES["approved_country_codes"])
GEOGRAPHY_RULE_VERSION = f"equinet-a1-location-{LOCATION_RULES['version']}"

SOURCE_TYPE_MAP = {
    "public_business_website": "business_website",
    "business_website": "business_website",
    "official_registry": "official_registry",
    "professional_association": "professional_association",
    "public_directory": "public_directory",
    "public_social_profile": "public_social_profile",
    "public_event_listing": "public_event_listing",
    "public_sale_record": "public_sale_record",
    "map_listing": "map_listing",
    "news_or_press": "news_or_press",
    "client_provided_authorised_file": "client_provided_authorised_file",
    "crm_authoritative": "crm_authoritative",
    "other_approved_public_source": "other_approved_public_source",
}
BAND_ORDER = {"high": 0, "medium": 1, "low": 2, "unqualified": 3, None: 4}
STATUS_ORDER = {"accept": 0, "needs_research": 1, "reject": 2}
REVIEW_OUTCOMES = {
    "horse_count_unknown_human_review",
    "below_threshold_commercial_exception_review",
    "future_potential_human_review",
    "inactive_or_hobbyist_review",
    "needs_review_missing_professional_activity",
    "needs_review_missing_commercial_operation",
    "insufficient_horse_count_evidence",
}
RESOLVED_STAGE_FIELDS = {
    "candidate_id",
    "scoring.status",
    "confidence.level",
    "confidence.score",
    "recommendation.next_action",
    "workflow.stage",
    "provenance.audit_correlation_id",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def schema_errors(schema: dict[str, Any], value: Any) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.absolute_path))
    return [f"/{'/'.join(str(part) for part in error.absolute_path)}: {error.message}" for error in errors]


def validate_or_raise(schema_path: Path, value: Any, label: str) -> None:
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    errors = schema_errors(schema, value)
    if errors:
        raise ValueError(f"Invalid {label}: " + " | ".join(errors))


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def website_domain(website: str | None) -> str | None:
    if not website:
        return None
    host = (urlparse(website).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host or None


def source_evidence(bundle: dict[str, Any], criteria: list[dict[str, Any]], contacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seed = bundle["research_seed"]
    claim_map: dict[str, list[str]] = defaultdict(list)
    for criterion in criteria:
        for evidence_id in criterion.get("evidence_ids", []):
            claim_map[evidence_id].append(criterion["criterion_id"])
    for contact in contacts:
        for evidence_id in contact.get("evidence_ids", []):
            claim_map[evidence_id].append(f"public_contact.{contact['contact_type']}")

    evidence: list[dict[str, Any]] = []
    for item in seed.get("source_candidates", []):
        evidence_id = item["evidence_id"]
        supports = unique(claim_map.get(evidence_id, []) or ["identity"])
        source_type = SOURCE_TYPE_MAP.get(item.get("source_type"), "other_approved_public_source")
        evidence.append({
            "evidence_id": evidence_id,
            "source_url": item["source_url"],
            "source_name": item.get("source_name") or "Public source",
            "source_type": source_type,
            "source_policy_status": bundle["source_policy_status"],
            "access_method": bundle["access_method"],
            "retrieved_at": item["retrieved_at"],
            "title": item.get("source_name"),
            "evidence_excerpt": item["evidence_excerpt"],
            "fact_or_inference": item.get("fact_or_inference", "direct_fact"),
            "supports_claims": supports,
            "reliability_level": "high" if bundle["source_policy_status"] == "approved" else "medium",
        })
    if not evidence:
        raise ValueError(f"Candidate {bundle['candidate_id']} has no source evidence.")
    return evidence


def identity(bundle: dict[str, Any]) -> dict[str, Any]:
    seed = bundle["research_seed"]
    classification = bundle["classification_decision"]
    hint = seed.get("identity_hint", {})
    identity_type = classification.get("identity_type")
    person_name = hint.get("person_name")
    organisation_name = hint.get("organisation_name")
    website = seed.get("website")
    person = None
    organisation = None
    if identity_type in {"person", "person_and_organisation"} or person_name:
        if person_name:
            person = {
                "full_name": person_name,
                "first_name": None,
                "last_name": None,
                "role_title": hint.get("role_title") or ("Farrier" if classification.get("segment") == "farrier" else None),
            }
    if identity_type in {"organisation", "person_and_organisation"} or organisation_name:
        if organisation_name:
            organisation = {
                "name": organisation_name,
                "website": website,
                "domain": website_domain(website),
            }
    display_name = hint.get("display_name") or organisation_name or person_name
    if not display_name or (person is None and organisation is None):
        raise ValueError(f"Candidate {bundle['candidate_id']} does not have a resolvable identity.")
    aliases = unique([value for value in [person_name, organisation_name] if value and value != display_name])
    return {"display_name": display_name, "person": person, "organisation": organisation, "aliases": aliases}


def location(seed: dict[str, Any]) -> dict[str, Any]:
    hint = seed.get("location_hint", {})
    country = str(hint.get("country_code") or "").strip().upper()
    state = hint.get("state_region")
    city = hint.get("city")
    if country and country not in APPROVED_COUNTRY_CODES:
        geography = "out_of_scope"
    elif country and state and city:
        geography = "in_scope"
    else:
        geography = "uncertain"
    return {
        "country_code": country,
        "state_region": state,
        "city": city,
        "postal_code": hint.get("postal_code"),
        "public_address": hint.get("public_address"),
        "geography_status": geography,
        "geography_rule_version": GEOGRAPHY_RULE_VERSION,
    }


def unavailable_check(notes: str) -> dict[str, Any]:
    return {"status": "unavailable", "checked_at": None, "method_version": None, "matches": [], "notes": notes}


def unprovided_check(status: str, generated_at: str) -> dict[str, Any]:
    if status == "no_match":
        return {"status": "no_match", "checked_at": generated_at, "method_version": "provided-exclusion-1.0.0", "matches": [], "notes": "The supplied exclusion file check reported no match."}
    if status == "not_checked":
        return {"status": "not_checked", "checked_at": None, "method_version": None, "matches": [], "notes": "No exclusion-file check was requested."}
    return unavailable_check("No authorised Equinet exclusion file was supplied for this run.")


def resolved_minimum(qualification: dict[str, Any]) -> tuple[str, list[str]]:
    remaining = [field for field in qualification.get("missing_minimum_fields", []) if field not in RESOLVED_STAGE_FIELDS]
    if remaining:
        return "needs_review", remaining
    return "pass", []


def assemble_candidate(bundle: dict[str, Any], request: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    seed = bundle["research_seed"]
    classification = bundle["classification_decision"]
    qualification = copy.deepcopy(bundle["qualification_package"]["qualification"])
    confidence_package = bundle["confidence_package"]
    scoring_package = bundle["scoring_package"]
    confidence = copy.deepcopy(confidence_package["confidence"])
    scoring = copy.deepcopy(scoring_package["scoring"])
    audit = copy.deepcopy(scoring_package.get("audit", {}))

    if classification.get("segment") not in {"farrier", "horse_owner"}:
        raise ValueError(f"Candidate {bundle['candidate_id']} has no confirmed supported segment.")
    if scoring.get("status") not in {"scored", "blocked"}:
        raise ValueError(f"Candidate {bundle['candidate_id']} has not completed deterministic scoring.")
    score_context = scoring_package.get("confidence_context")
    if score_context and (score_context.get("score") != confidence.get("score") or score_context.get("level") != confidence.get("level")):
        raise ValueError(f"Candidate {bundle['candidate_id']} has inconsistent scoring and confidence packages.")

    minimum_status, missing = resolved_minimum(qualification)
    qualification["minimum_data_status"] = minimum_status
    qualification["missing_minimum_fields"] = missing
    contacts = copy.deepcopy(seed.get("public_contacts", []))
    evidence = source_evidence(bundle, qualification["criteria"], contacts)
    candidate_identity = identity(bundle)
    candidate_location = location(seed)
    unresolved_identity = confidence_package.get("assessment", {}).get("gates", {}).get("unresolved_identity_conflict", {}).get("value", False)
    critical_conflict = confidence_package.get("assessment", {}).get("gates", {}).get("critical_evidence_conflict", {}).get("value", False)
    conflicts = list(seed.get("conflicts", [])) if (unresolved_identity or critical_conflict) else []
    quality_status = "validated" if not missing and not conflicts else ("conflict" if conflicts else "partially_validated")
    contains_personal = candidate_identity["person"] is not None or bool(contacts)

    candidate = {
        "schema_version": "1.1.0",
        "record_kind": bundle["record_kind"],
        "candidate_id": bundle["candidate_id"],
        "run_id": seed.get("run_id") or request["run_id"],
        "discovered_at": seed["discovered_at"],
        "updated_at": request["generated_at"],
        "segment": classification["segment"],
        "prospect_type": classification["prospect_type"],
        "identity": candidate_identity,
        "location": candidate_location,
        "public_contacts": contacts,
        "source_evidence": evidence,
        "qualification": qualification,
        "scoring": scoring,
        "confidence": confidence,
        "duplicate_check": {
            "batch": {"status": "not_checked", "checked_at": None, "method_version": None, "matches": [], "notes": "Batch duplicate check pending package assembly."},
            "provided_exclusion_file": unprovided_check(bundle.get("provided_exclusion_file_status", "unavailable"), request["generated_at"]),
            "twenty": unavailable_check("Twenty is not connected for A1 V1."),
            "hubspot": copy.deepcopy(bundle.get("hubspot_check")) if bundle.get("hubspot_check") is not None else unavailable_check("HubSpot metadata is available for integration design, but the live connector and record values are unavailable; customer, opportunity, consent and exclusion status are unknown."),
        },
        "data_quality": {
            "validation_status": quality_status,
            "missing_fields": missing,
            "conflicts": conflicts,
            "last_validated_at": request["generated_at"] if quality_status == "validated" else None,
        },
        "data_governance": {
            "contains_personal_data": contains_personal,
            "collection_context": "public_business_information",
            "source_terms_review_status": "confirmed" if bundle["source_policy_status"] == "approved" else "conditional",
            "retention_policy_version": None,
            "a1_outreach_prohibited": True,
        },
        "recommendation": {
            "next_action": "review",
            "priority_rank": None,
            "suggested_owner": None,
            "suggested_territory": None,
            "notes": "Pending deterministic review recommendation and human decision.",
        },
        "workflow": {
            "stage": "needs_review",
            "review_decision": "none",
            "reviewer": None,
            "decision_at": None,
            "rejection_reason": None,
        },
        "system_references": {
            "twenty_company_id": None,
            "twenty_person_id": None,
            "twenty_person_relation_status": None,
            "a2_handoff_id": None,
            "hubspot_contact_id": None,
            "hubspot_company_id": None,
            "hubspot_sync_id": None,
        },
        "provenance": {
            "created_by_profile": "equinet-a1-icp-discovery",
            "initiated_by": request["initiated_by"],
            "model": bundle["model"],
            "tools_used": bundle["tools_used"],
            "audit_correlation_id": f"{request['package_id']}:{bundle['candidate_id']}",
            "synthetic": bundle["record_kind"] == "synthetic_test",
        },
    }
    context = {
        "audit": audit,
        "scoring_explanation": scoring_package.get("explanation", {}),
        "research_missing": seed.get("missing_information", []),
    }
    return candidate, context


def normalised(value: str | None) -> str:
    return "".join(character.lower() for character in (value or "") if character.isalnum())


def duplicate_fields(candidate: dict[str, Any]) -> dict[str, set[str]]:
    identity_value = candidate["identity"]
    location_value = candidate["location"]
    contacts = candidate["public_contacts"]
    organisation = identity_value.get("organisation") or {}
    fields = {
        "domain": {normalised(organisation.get("domain"))} if organisation.get("domain") else set(),
        "email": {normalised(item["value"]) for item in contacts if item["contact_type"] == "email"},
        "phone": {normalised(item["value"]) for item in contacts if item["contact_type"] == "phone"},
        "identity_location": {normalised(identity_value["display_name"] + "|" + (location_value.get("city") or ""))},
    }
    return {name: {value for value in values if value} for name, values in fields.items()}


def apply_batch_duplicate_checks(candidates: list[dict[str, Any]], generated_at: str) -> None:
    fields = {candidate["candidate_id"]: duplicate_fields(candidate) for candidate in candidates}
    for candidate in candidates:
        matches = []
        candidate_id = candidate["candidate_id"]
        for other in candidates:
            if other["candidate_id"] == candidate_id:
                continue
            shared = [name for name in fields[candidate_id] if fields[candidate_id][name] & fields[other["candidate_id"]][name]]
            if not shared:
                continue
            exact = any(name in {"domain", "email", "phone"} for name in shared)
            matches.append({
                "system": "current_batch",
                "record_id": other["candidate_id"],
                "record_url": None,
                "match_level": "exact" if exact else "probable",
                "matched_fields": sorted(shared),
            })
        candidate["duplicate_check"]["batch"] = {
            "status": "possible_match" if matches else "no_match",
            "checked_at": generated_at,
            "method_version": "a1-batch-duplicate-1.0.0",
            "matches": matches,
            "notes": "Possible current-batch identity match requires human review." if matches else "No exact or probable match found within the current review batch.",
        }


def review_status(candidate: dict[str, Any], context: dict[str, Any]) -> tuple[str, str]:
    scoring = candidate["scoring"]
    confidence = candidate["confidence"]
    qualification = candidate["qualification"]
    quality = candidate["data_quality"]
    outcome = context["audit"].get("outcome", "review_required")
    band = scoring.get("band")

    if scoring.get("status") == "blocked" or qualification.get("exclusion_status") == "excluded" or band == "unqualified" or outcome.startswith("excluded"):
        reason = scoring.get("block_reason") or (qualification.get("exclusion_reasons") or ["Candidate does not meet the approved ICP."])[0]
        return "reject", f"Reject recommendation: {reason} Human review is still required before recording a final rejection."
    if (
        confidence.get("level") == "low"
        or quality.get("missing_fields")
        or quality.get("conflicts")
        or candidate["duplicate_check"]["batch"]["status"] == "possible_match"
        or candidate["duplicate_check"]["hubspot"]["status"] in {"possible_match", "possible_duplicate", "confirmed_duplicate", "hubspot_duplicate", "error", "hubspot_check_failed"}
        or outcome in REVIEW_OUTCOMES
        or band == "low"
    ):
        return "needs_research", f"Needs Research recommendation: deterministic outcome `{outcome}` or evidence/duplicate limitations require human follow-up."
    if band in {"high", "medium"} and confidence.get("level") in {"high", "medium"}:
        return "accept", f"Accept recommendation for human review: final band {band} with {confidence['level']} evidence confidence and no unresolved review gate."
    return "needs_research", "Needs Research recommendation: the candidate does not meet the controlled Accept conditions."


def review_limitations(candidate: dict[str, Any], context: dict[str, Any]) -> list[str]:
    limitations = [
        value
        for value in candidate["confidence"].get("limitations", [])
        if not value.lower().startswith("no confidence score cap was triggered")
    ]
    confirmed = {
        entry["criterion_id"]
        for entry in candidate["qualification"]["criteria"]
        if entry["status"] == "confirmed"
    }
    for value in context.get("research_missing", []):
        lowered = value.lower()
        if candidate["segment"] == "farrier" and "horse count or client base size" in lowered:
            limitations.append("Explicit client base size is not stated.")
            continue
        if "pricing or product brand usage" in lowered and any(identifier.endswith("product_usage_or_influence") for identifier in confirmed):
            continue
        limitations.append(value)
    limitations.extend(candidate["data_quality"].get("conflicts", []))
    return unique(limitations)


def integration_details(candidate: dict[str, Any]) -> tuple[list[str], list[str]]:
    hubspot_status = candidate["duplicate_check"]["hubspot"]["status"]
    limitations = [
        "Mandatory Twenty Company staging has not completed for this review package.",
        "A2 handoff is not triggered and requires recorded human approval.",
    ]
    blockers = ["Human approval is not recorded.", "Twenty Company staging has not completed."]
    if hubspot_status == "unavailable":
        limitations.insert(0, "HubSpot metadata is available, but live duplicate, customer, opportunity, consent and exclusion checks are unavailable.")
        blockers.insert(1, "HubSpot checks are unavailable.")
    elif hubspot_status in {"not_checked", "not_checked_no_domain"}:
        limitations.insert(0, "The HubSpot duplicate check was not completed.")
        blockers.insert(1, "The HubSpot duplicate check is pending.")
    elif hubspot_status in {"error", "hubspot_check_failed"}:
        limitations.insert(0, "The HubSpot duplicate check returned an error and requires follow-up.")
        blockers.insert(1, "The HubSpot duplicate check error is unresolved.")
    elif hubspot_status in {"possible_match", "possible_duplicate", "confirmed_duplicate", "hubspot_duplicate"}:
        limitations.insert(0, f"The HubSpot duplicate check returned {hubspot_status}; human resolution is required.")
        blockers.insert(1, "The HubSpot duplicate result requires human resolution.")
    return limitations, blockers


def hubspot_integration_status(candidates: list[dict[str, Any]]) -> str:
    statuses = [candidate["duplicate_check"]["hubspot"]["status"] for candidate in candidates]
    completed = {"no_match", "possible_match", "possible_duplicate", "confirmed_duplicate", "hubspot_duplicate"}
    if statuses and all(status in completed for status in statuses):
        return "checked"
    if statuses and all(status == "unavailable" for status in statuses):
        return "unavailable"
    return "partial"


def validate_candidate(candidate: dict[str, Any]) -> None:
    schema = load_json(CANDIDATE_SCHEMA)
    errors = schema_errors(schema, candidate) + [f"custom: {error}" for error in cross_reference_errors(candidate)]
    if errors:
        raise ValueError(f"Invalid Prospect Candidate {candidate.get('candidate_id')}: " + " | ".join(errors))


def build(request: dict[str, Any]) -> dict[str, Any]:
    validate_or_raise(INPUT_SCHEMA, request, "review input")
    assembled: list[tuple[dict[str, Any], dict[str, Any]]] = [assemble_candidate(bundle, request) for bundle in request["candidates"]]
    candidates = [candidate for candidate, _ in assembled]
    if len({candidate["candidate_id"] for candidate in candidates}) != len(candidates):
        raise ValueError("Review input contains duplicate candidate_id values.")
    apply_batch_duplicate_checks(candidates, request["generated_at"])

    items = []
    for candidate, context in assembled:
        status, rationale = review_status(candidate, context)
        candidate["recommendation"]["next_action"] = "exclude" if status == "reject" else "review"
        hubspot_status = candidate["duplicate_check"]["hubspot"]["status"]
        if hubspot_status == "unavailable":
            candidate["recommendation"]["notes"] = rationale + " HubSpot metadata is available, but live HubSpot checks are unavailable. Mandatory Twenty Company staging has not completed."
        else:
            candidate["recommendation"]["notes"] = rationale + f" HubSpot check status: {hubspot_status}. Mandatory Twenty Company staging has not completed."
        limitations = review_limitations(candidate, context)
        integration_limitations, a2_blockers = integration_details(candidate)
        criteria = candidate["qualification"]["criteria"]
        confirmed = [entry["criterion_id"] for entry in criteria if entry["status"] == "confirmed"]
        uncertain = [entry["criterion_id"] for entry in criteria if entry["status"] in {"unknown", "contradicted"}]
        items.append({
            "candidate_id": candidate["candidate_id"],
            "overall_rank": 1,
            "segment_rank": 1,
            "recommended_review_status": status,
            "recommendation_rationale": rationale,
            "reviewer_decision": "pending",
            "scoring_outcome": context["audit"].get("outcome", "review_required"),
            "applied_band_rules": list(context["audit"].get("applied_band_caps", [])),
            "confirmed_criteria": confirmed,
            "uncertain_criteria": uncertain,
            "source_urls": unique([entry["source_url"] for entry in candidate["source_evidence"]]),
            "limitations": limitations,
            "integration_limitations": integration_limitations,
            "a2_handoff": {
                "status": "not_authorised",
                "blockers": a2_blockers,
            },
            "prospect_candidate": candidate,
        })

    def sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
        candidate = item["prospect_candidate"]
        score = candidate["scoring"].get("score")
        confidence = candidate["confidence"].get("score")
        return (
            STATUS_ORDER[item["recommended_review_status"]],
            BAND_ORDER[candidate["scoring"].get("band")],
            -(score if score is not None else -1),
            -(confidence if confidence is not None else -1),
            candidate["identity"]["display_name"].lower(),
            candidate["candidate_id"],
        )

    items.sort(key=sort_key)
    segment_counts: dict[str, int] = defaultdict(int)
    for overall_rank, item in enumerate(items, start=1):
        segment = item["prospect_candidate"]["segment"]
        segment_counts[segment] += 1
        item["overall_rank"] = overall_rank
        item["segment_rank"] = segment_counts[segment]
        item["prospect_candidate"]["recommendation"]["priority_rank"] = overall_rank
        validate_candidate(item["prospect_candidate"])

    counts = Counter(item["recommended_review_status"] for item in items)
    segments = Counter(item["prospect_candidate"]["segment"] for item in items)
    package = {
        "schema_version": "1.1.0",
        "package_id": request["package_id"],
        "run_id": request["run_id"],
        "generated_at": request["generated_at"],
        "generated_by": "equinet-a1-icp-discovery",
        "integration_status": {"hubspot": hubspot_integration_status(candidates), "twenty": "not_staged", "a2": "not_triggered"},
        "summary": {
            "total": len(items),
            "accept": counts["accept"],
            "needs_research": counts["needs_research"],
            "reject": counts["reject"],
            "farrier": segments["farrier"],
            "horse_owner": segments["horse_owner"],
        },
        "candidates": items,
    }
    validate_or_raise(PACKAGE_SCHEMA, package, "review package")
    if sum(package["summary"][key] for key in ["accept", "needs_research", "reject"]) != package["summary"]["total"]:
        raise ValueError("Review-package status counts do not equal total candidates.")
    return package


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("review_input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        package = build(load_json(args.review_input))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"VALID: {args.output}")
        return 0
    except Exception as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
