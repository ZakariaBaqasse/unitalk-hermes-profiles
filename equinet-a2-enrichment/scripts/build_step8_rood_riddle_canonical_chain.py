#!/usr/bin/env python3
"""Build and validate the bounded Rood & Riddle Step 8 canonical review package."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_a2_minimum_package import evaluate as evaluate_minimum
from validate_a2_enrichment_record import validate

BASE = ROOT / "evaluations/step8/pilot/A1-RR-PODIATRY-001"
INITIAL = ROOT / "evaluations/step8/intake/A1-RR-PODIATRY-001/initial-record.json"
REUSE = ROOT / "evaluations/step8/planning/A1-RR-PODIATRY-001.reuse-snapshot.json"
RAW = BASE / "observation-batch.json"
VALID = BASE / "validated-observations.json"
EVIDENCE = BASE / "evidence-confidence/manifest.json"
USAGE = BASE / "profile-usage.json"
PACKAGES = ROOT / "foundations/contracts/business/a2-minimum-data-packages-0.1.1-draft.1.json"
OUT = BASE / "canonical"
CATALOGUE_VERSION = "0.1.1-draft.1"
EXPECTED_ACCEPTED = {"person.role_title", "organisation.disciplines"}
EXPECTED_GAPS = {
    "person.professional_status",
    "organisation.service_area",
    "person.business_email",
    "person.business_phone",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def actor() -> dict:
    return {
        "actor_id": "UNITALK-A2-STEP8",
        "actor_role": "A2 Bounded Pilot Runtime",
        "display_name": "Equinet A2 Enrichment Unitalk AI Collaborator",
        "profile_id": "equinet-a2-enrichment",
        "workflow_id": None,
    }


def app() -> dict:
    return {
        "status": "not_requested",
        "destination": None,
        "external_action_reference": None,
        "workflow_dependency_status": "not_checked",
        "applied_at": None,
        "error": None,
    }


def review(decision: str = "not_required") -> dict:
    return {"decision": decision, "reviewer": None, "decided_at": None, "reason": None, "corrected_value": None}


def origin(key: str, evidence: list[str]) -> dict:
    return {"system": "a1_handoff", "record_reference": evidence[0], "field_reference": key, "source_kind": "a1_handoff"}


def assessment(
    assessment_id: str,
    key: str,
    target: str,
    scope: str,
    value_type: str,
    value,
    evidence_ids: list[str],
    *,
    quality: str = "complete",
    verification: str = "verified",
    confidence: str = "high",
    freshness: str = "current",
    availability: str | None = None,
) -> dict:
    if value_type == "structured" and isinstance(value, dict):
        value = {"components": [{"key": key, "value": part} for key, part in value.items() if part is not None]}
    present = value is not None
    return {
        "field_assessment_id": assessment_id,
        "field_key": key,
        "entity_id": target,
        "scope": scope,
        "field_catalogue_version": CATALOGUE_VERSION,
        "value_type": value_type,
        "sensitivity_classification": "professional_business_data",
        "presence_status": "known" if present else "unknown",
        "availability_status": availability or ("available" if present else "not_checked"),
        "field_quality_status": quality,
        "baseline": {
            "value": value,
            "normalised_value": value,
            "origin": origin(key, evidence_ids),
            "observed_at": "2026-08-30T10:42:29Z",
            "evidence_ids": evidence_ids,
            "protected_status": "unassessed",
        } if present else None,
        "observations": [],
        "proposed_resolution": {
            "action": "retain",
            "value": value,
            "normalised_value": value,
            "evidence_ids": evidence_ids,
            "rationale": "Retain the approved A1 handoff value following bounded A2 verification.",
            "verification_status": verification,
            "confidence_level": confidence,
            "freshness_status": freshness,
            "conflict_status": "none",
            "protected_status": "unassessed",
        } if present else None,
        "field_review": review(),
        "application": app(),
    }


def advance(previous: dict, number: int, state: str, event_type: str, timestamp: str) -> dict:
    record = copy.deepcopy(previous)
    previous_id = previous["record_metadata"]["record_revision_id"]
    revision_id = f"{previous['record_metadata']['a2_record_id'].replace('A2-INIT_', 'A2-REV-STEP8_')}_{number:03d}"
    record["record_metadata"].update(
        {
            "record_revision_id": revision_id,
            "revision_number": number,
            "supersedes_revision_id": previous_id,
            "created_at": timestamp,
            "created_by": actor(),
            "change_reason": "enrichment",
        }
    )
    record["workflow"].update(
        {
            "state": state,
            "previous_state": previous["workflow"]["state"],
            "transitioned_at": timestamp,
            "triggered_by": actor(),
            "hold_reasons": [],
            "block_reasons": [],
            "failure": None,
        }
    )
    record["audit_and_consumption"]["events"].append(
        {
            "event_id": f"A2-EVENT-STEP8-RR-{number:03d}",
            "event_type": event_type,
            "actor": actor(),
            "timestamp": timestamp,
            "input_references": [previous_id],
            "output_references": [revision_id],
            "model": None,
            "tools": ["deterministic-step8-canonical-builder"],
            "usage": None,
            "external_action": None,
        }
    )
    return record


def add_observation(target: dict, source: dict, confidence: dict) -> None:
    value = source["normalised_value"]
    freshness = confidence["freshness_status"]
    if freshness == "current_official_undated":
        freshness = "undated"
    target["observations"] = [
        {
            "observation_id": source["observation_id"],
            "raw_value": source["raw_value"],
            "normalised_value": value,
            "evidence_ids": [source["evidence_id"]],
            "verification_status": "verified",
            "confidence_level": "high",
            "freshness_status": freshness,
            "claim_type": "direct_fact",
            "error": None,
        }
    ]
    target["presence_status"] = "known"
    target["availability_status"] = "available"
    target["field_quality_status"] = "complete"
    target["proposed_resolution"] = {
        "action": "no_change" if target["baseline"] is not None else "add",
        "value": value,
        "normalised_value": value,
        "evidence_ids": [source["evidence_id"]],
        "rationale": "Current official-site evidence supports this bounded Step 8 field proposal.",
        "verification_status": "verified",
        "confidence_level": "high",
        "freshness_status": freshness,
        "conflict_status": "none",
        "protected_status": "not_protected",
    }
    if target["baseline"] is None:
        target["field_review"] = review("pending")


def evidence_record(source: dict, field_assessment_id: str, retrieved_at: str) -> dict:
    return {
        "evidence_id": source["evidence_id"],
        "namespace": "a2",
        "source_id": "prospect_official_website",
        "source_type": "prospect_owned_website",
        "source_policy_status": "approved",
        "source_url": source["source_url"],
        "provider_reference": None,
        "access_method": "firecrawl_bounded_public_web_read",
        "retrieved_at": retrieved_at,
        "source_date": None,
        "title": "Rood & Riddle official website",
        "excerpt_or_result_summary": source["page_context"][:1000],
        "claim_type": "direct_fact",
        "supports_field_assessment_ids": [field_assessment_id],
        "supports_requalification_signal_ids": [],
        "reliability_level": "high",
        "independence_group_id": "roodandriddle.com",
        "provider_cost": None,
        "supersedes_evidence_id": None,
        "data_minimisation_notes": "Retains only the approved business claim and source reference; form placeholders and unrelated people are excluded.",
    }


def main() -> int:
    initial = load(INITIAL)
    reuse = load(REUSE)
    raw = load(RAW)
    validated = load(VALID)
    evidence_manifest = load(EVIDENCE)
    packages = load(PACKAGES)
    raw_by_id = {item["observation_id"]: item for item in raw["observations"]}
    valid_by_key={item[...y"]: item for item in validated["observations"]}
    accepted = {key for key, item in valid_by_key.items() if item["action"] == "accept_for_wave3_evidence_assessment"}
    gaps = {key for key, item in valid_by_key.items() if item["action"] == "retain_state_only" and item["field_state"] in {"unknown", "not_found", "unavailable"}}
    if not EXPECTED_ACCEPTED.issubset(accepted):
        raise RuntimeError(f"Required accepted observations missing: {sorted(EXPECTED_ACCEPTED - accepted)}")
    if not EXPECTED_GAPS.issubset(gaps):
        raise RuntimeError(f"Required explicit gaps missing: {sorted(EXPECTED_GAPS - gaps)}")
    if any("example@example.com" in json.dumps(item).lower() for item in raw["observations"]):
        raise RuntimeError("Contact form placeholder was incorrectly retained")

    person_id = next(item["entity_id"] for item in initial["subject"]["entities"] if item["entity_type"] == "person")
    org_id = next(item["entity_id"] for item in initial["subject"]["entities"] if item["entity_type"] == "organisation")
    values = reuse["reused_a1_values"]
    ids = {
        "organisation.business_name": "A2-FLD-STEP8-RR-ORG-NAME",
        "organisation.public_business_location": "A2-FLD-STEP8-RR-LOCATION",
        "organisation.website": "A2-FLD-STEP8-RR-WEBSITE",
        "organisation.website_domain": "A2-FLD-STEP8-RR-DOMAIN",
        "organisation.business_phone": "A2-FLD-STEP8-RR-ORG-PHONE",
        "person.full_name": "A2-FLD-STEP8-RR-PERSON-NAME",
        "person.role_title": valid_by_key["person.role_title"]["field_assessment_candidate"]["field_assessment_id"],
        "person.professional_status": valid_by_key["person.professional_status"]["field_assessment_candidate"]["field_assessment_id"],
        "organisation.service_area": valid_by_key["organisation.service_area"]["field_assessment_candidate"]["field_assessment_id"],
        "organisation.disciplines": valid_by_key["organisation.disciplines"]["field_assessment_candidate"]["field_assessment_id"],
        "person.business_email": valid_by_key["person.business_email"]["field_assessment_candidate"]["field_assessment_id"],
        "person.business_phone": valid_by_key["person.business_phone"]["field_assessment_candidate"]["field_assessment_id"],
        "relationship.target_role_priority": "A2-FLD-STEP8-RR-ROLE-PRIORITY",
    }

    now = datetime.now(timezone.utc).replace(microsecond=0)
    timestamps = [(now + timedelta(seconds=index)).isoformat().replace("+00:00", "Z") for index in range(3)]
    rev2 = advance(initial, 2, "enrichment_planned", "workflow_enrichment_planned", timestamps[0])
    rev2["enrichment_scope"].update(
        {
            "field_catalogue_version": CATALOGUE_VERSION,
            "source_register_version": "0.1.1-draft.1",
            "limits": {
                "max_records": 1,
                "max_source_calls": 5,
                "max_provider_calls": 0,
                "max_retries": 1,
                "max_concurrency": 1,
                "max_cost_usd": 0,
                "policy_version": "a2-step8-bounded-pilot-runtime-0.1.0",
            },
            "initiated_by": actor(),
        }
    )
    rev2["governance"].update(
        {
            "source_register_version": "0.1.1-draft.1",
            "source_terms_review_status": "approved",
            "processing_purpose": "Bounded enrichment of an authorised public-business Farrier prospect for human review.",
            "policy_limitations": [
                "No HubSpot, Twenty, n8n, Apify, outreach or downstream delivery.",
                "Form placeholders are not contact data.",
                "No employment status, service area or purchasing authority is inferred.",
            ],
        }
    )
    rev2["field_assessments"] = [
        assessment(ids["organisation.business_name"], "organisation.business_name", org_id, "organisation", "string", values["organisation.business_name"]["value"], values["organisation.business_name"]["evidence_ids"]),
        assessment(ids["organisation.public_business_location"], "organisation.public_business_location", org_id, "organisation", "structured", values["organisation.public_business_location"]["value"], values["organisation.public_business_location"]["evidence_ids"]),
        assessment(ids["organisation.website"], "organisation.website", org_id, "organisation", "string", values["organisation.website"]["value"], values["organisation.website"]["evidence_ids"]),
        assessment(ids["organisation.website_domain"], "organisation.website_domain", org_id, "organisation", "string", values["organisation.website_domain"]["value"], values["organisation.website_domain"]["evidence_ids"]),
        assessment(ids["organisation.business_phone"], "organisation.business_phone", org_id, "organisation", "string", values["organisation.business_phone"]["value"], values["organisation.business_phone"]["evidence_ids"]),
        assessment(ids["person.full_name"], "person.full_name", person_id, "person", "string", values["person.full_name"]["value"], values["person.full_name"]["evidence_ids"]),
        assessment(ids["person.role_title"], "person.role_title", person_id, "person", "string", values["person.role_title"]["value"], values["person.role_title"]["evidence_ids"], quality="partial", verification="partially_verified", confidence="medium"),
        assessment(ids["person.professional_status"], "person.professional_status", person_id, "person", "enum", None, [], quality="gap", availability=valid_by_key["person.professional_status"]["field_state"]),
        assessment(ids["organisation.service_area"], "organisation.service_area", org_id, "organisation", "string_array", None, [], quality="gap", availability=valid_by_key["organisation.service_area"]["field_state"]),
        assessment(ids["organisation.disciplines"], "organisation.disciplines", org_id, "organisation", "string_array", None, [], quality="partial", availability="not_checked"),
        assessment(ids["person.business_email"], "person.business_email", person_id, "person", "string", None, [], quality="gap", availability=valid_by_key["person.business_email"]["field_state"]),
        assessment(ids["person.business_phone"], "person.business_phone", person_id, "person", "string", None, [], quality="gap", availability=valid_by_key["person.business_phone"]["field_state"]),
    ]
    rev2["data_quality"].update(
        {
            "status": "unassessed",
            "method_version": "a2-step8-quality-0.1.0",
            "calculated_at": None,
            "required_field_keys": [],
            "missing_field_keys": [],
            "unverified_field_keys": ["person.role_title", "organisation.disciplines"],
            "conflict_field_keys": [],
            "stale_field_keys": [],
            "invalid_field_keys": [],
            "limitations": ["Bounded stored-page assessment is pending."],
        }
    )

    rev3 = advance(rev2, 3, "enrichment_in_progress", "workflow_enrichment_in_progress", timestamps[1])
    relationship_id = "A2-REL-STEP8-RR-WORKS-FOR"
    rev3["subject"]["relationships"] = [
        {
            "relationship_id": relationship_id,
            "from_entity_id": person_id,
            "to_entity_id": org_id,
            "relationship_type": "works_for",
            "evidence_ids": [valid_by_key["person.role_title"]["evidence_id"]],
        }
    ]
    confidence_by_key={item[...y"]: item for item in evidence_manifest["results"]}
    assessments_by_key={item[...y"]: item for item in rev3["field_assessments"]}
    for key in sorted(EXPECTED_ACCEPTED):
        add_observation(assessments_by_key[key], valid_by_key[key], confidence_by_key[key])

    role_item = valid_by_key["person.role_title"]
    rev3["field_assessments"].append(
        {
            "field_assessment_id": ids["relationship.target_role_priority"],
            "field_key": "relationship.target_role_priority",
            "entity_id": relationship_id,
            "scope": "relationship",
            "field_catalogue_version": CATALOGUE_VERSION,
            "value_type": "enum",
            "sensitivity_classification": "professional_business_data",
            "presence_status": "known",
            "availability_status": "available",
            "field_quality_status": "partial",
            "baseline": None,
            "observations": [],
            "proposed_resolution": {
                "action": "add",
                "value": "primary",
                "normalised_value": "primary",
                "evidence_ids": [role_item["evidence_id"]],
                "rationale": "Human-reviewable classification from the verified Co-Founder/Farrier role; not a sourced fact and not proof of purchasing authority.",
                "verification_status": "partially_verified",
                "confidence_level": "medium",
                "freshness_status": "not_applicable",
                "conflict_status": "none",
                "protected_status": "not_protected",
            },
            "field_review": review("pending"),
            "application": app(),
        }
    )

    accepted_raw = [raw_by_id[item["observation_id"]] for item in validated["observations"] if item["action"] == "accept_for_wave3_evidence_assessment"]
    rev3["evidence_registry"] = [
        evidence_record(source, valid_by_key[source["field_key"]]["field_assessment_candidate"]["field_assessment_id"], timestamps[1])
        for source in accepted_raw
    ]
    role_evidence = next(item for item in rev3["evidence_registry"] if item["evidence_id"] == role_item["evidence_id"])
    role_evidence["supports_field_assessment_ids"].append(ids["relationship.target_role_priority"])

    field_states = {key: value["state"] for key, value in reuse["field_states"].items()}
    for key in accepted:
        field_states[key] = "verified"
    for key in gaps:
        field_states[key] = valid_by_key[key]["field_state"]
    field_states["relationship.target_role_priority"] = "present_unverified"
    minimum_input = {
        "fixture_id": "step8-rood-riddle-final",
        "segment": "farrier",
        "contact_path": "named_target",
        "target_role_not_found": False,
        "research_exhausted": True,
        "field_states": field_states,
        "conflict_field_keys": [],
        "error_field_keys": [],
    }
    minimum_result = evaluate_minimum(minimum_input, packages)
    minimum_dir = BASE / "minimum-package"
    minimum_dir.mkdir(parents=True, exist_ok=True)
    (minimum_dir / "input.json").write_text(json.dumps(minimum_input, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (minimum_dir / "result.json").write_text(json.dumps(minimum_result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if minimum_result["package_status"] != "incomplete" or minimum_result["workflow_recommendation"] != "held":
        raise RuntimeError(f"Unexpected minimum-package result: {minimum_result}")

    required = [
        "person.professional_status",
        "organisation.business_name",
        "organisation.public_business_location",
        "organisation.service_area",
        "organisation.disciplines",
        "person.full_name",
        "person.role_title",
        "relationship.target_role_priority",
        "person.business_email",
        "person.business_phone",
    ]
    missing = sorted(
        key
        for key in set(minimum_result["missing_required_fields"] + minimum_result["unsatisfied_contact_requirements"])
        if field_states.get(key) in {"missing", "unknown", "not_found", "unavailable"}
    )
    rev3["data_quality"].update(
        {
            "status": "incomplete",
            "method_version": "a2-step8-quality-0.1.0",
            "calculated_at": timestamps[1],
            "required_field_keys": required,
            "missing_field_keys": missing,
            "unverified_field_keys": ["relationship.target_role_priority"],
            "conflict_field_keys": [],
            "stale_field_keys": [],
            "invalid_field_keys": [],
            "limitations": [
                "The stored official pages do not establish full-time, part-time or apprentice professional status for Manfred Eckert.",
                "The Lexington location does not establish the Podiatry service area.",
                "No named professional email or phone for Manfred Eckert was found in the bounded pages; form placeholders were excluded.",
                "The organisation general phone remains available as fallback contactability but does not satisfy the named-target contact path.",
                "The hospital-wide statement 'all breeds and disciplines' is retained as organisation-level context and is not narrowed to a specific Podiatry discipline.",
                "HubSpot customer, Deal, consent, suppression and owner checks are unavailable.",
            ],
        }
    )
    usage = load(USAGE) if USAGE.exists() else {}
    model_completed = usage.get("completed") is True and usage.get("failed") is not True
    api_calls = usage.get("api_calls") if isinstance(usage.get("api_calls"), int) else 0
    usage_block = {
        "input_tokens": usage.get("input_tokens") if model_completed else None,
        "output_tokens": usage.get("output_tokens") if model_completed else None,
        "total_tokens": usage.get("total_tokens") if model_completed else None,
        "api_calls": api_calls,
        "credits": usage.get("credits") if model_completed else None,
        "cost_amount": usage.get("estimated_cost_usd") if model_completed else None,
        "currency": "USD",
        "cost_status": "known" if model_completed and usage.get("estimated_cost_usd") is not None else "unknown",
    }
    rev3["audit_and_consumption"]["total_usage"].update(usage_block)
    rev3["audit_and_consumption"]["events"][-1]["model"] = usage.get("model") if model_completed else None
    rev3["audit_and_consumption"]["events"][-1]["tools"] = [
        "deterministic-recovery-from-approved-stored-pages",
        "build_step8_collection_receipt.py",
        "normalise_and_validate_a2_observations.py",
        "evaluate_a2_evidence_confidence.py",
        "evaluate_a2_minimum_package.py",
    ]
    rev3["audit_and_consumption"]["events"][-1]["usage"] = usage_block

    rev4 = advance(rev3, 4, "review_required", "workflow_review_required", timestamps[2])
    rev4["review"] = {
        "record_decision": "pending",
        "reviewer": None,
        "decided_at": None,
        "reason": None,
        "required_field_decisions_complete": False,
        "requested_changes": [],
    }

    OUT.mkdir(parents=True, exist_ok=True)
    records = [
        ("revision-002-enrichment-planned.json", rev2, initial),
        ("revision-003-enrichment-in-progress.json", rev3, rev2),
        ("revision-004-review-required.json", rev4, rev3),
    ]
    results = []
    for name, record, previous in records:
        path = OUT / name
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        validation = validate(record, previous=previous)
        results.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha(path),
                "revision_id": record["record_metadata"]["record_revision_id"],
                "workflow": record["workflow"]["state"],
                "valid": validation["valid"],
                "errors": validation["errors"],
            }
        )
    manifest = {
        "record_type": "step8_rood_riddle_canonical_revision_chain",
        "candidate_id": "A1-RR-PODIATRY-001",
        "status": "valid_review_package_ready_with_material_gaps" if all(item["valid"] for item in results) else "validation_failed",
        "records": results,
        "minimum_package_result": str((minimum_dir / "result.json").relative_to(ROOT)),
        "minimum_package_status": minimum_result["package_status"],
        "workflow_recommendation": minimum_result["workflow_recommendation"],
        "final_record": results[-1]["path"],
        "final_review_decision": "pending",
        "recommended_record_decision": "held",
        "hubspot_write": False,
        "outreach": False,
        "external_actions": 0,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0 if all(item["valid"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
