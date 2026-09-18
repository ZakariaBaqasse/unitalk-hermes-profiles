#!/usr/bin/env python3
"""Build Step 2F Farrier and Horse Owner business-regression fixtures."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import sys
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROFILE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_step2d_schema import base_record  # noqa: E402

CONTRACTS = PROFILE_ROOT / "foundations" / "contracts"
STEP2E = PROFILE_ROOT / "evaluations" / "step2e" / "fixtures"
ROOT = PROFILE_ROOT / "evaluations" / "step2f"
FIXTURES = ROOT / "fixtures"
VALID = FIXTURES / "valid"
INVALID = FIXTURES / "invalid"
CATALOGUE_PATH = FIXTURES / "a2-step2f-synthetic-field-catalogue.json"
MANIFEST_PATH = FIXTURES / "scenario-manifest.json"
MATRIX_PATH = ROOT / "A2-STEP2F-SCENARIO-MATRIX.csv"
CATALOGUE_VERSION = "synthetic-step2f-0.1.0"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def actor(role: str = "A2 Synthetic Runtime") -> dict:
    return {
        "actor_id": "UNITALK-A2-STEP2F",
        "actor_role": role,
        "display_name": "Synthetic Step 2F Actor",
        "profile_id": "equinet-a2-enrichment",
        "workflow_id": None,
    }


def application(status: str = "not_requested") -> dict:
    return {
        "status": status,
        "destination": None,
        "external_action_reference": None,
        "workflow_dependency_status": "not_checked",
        "applied_at": None,
        "error": None,
    }


def field_review(decision: str = "pending") -> dict:
    if decision in {"pending", "not_required"}:
        return {"decision": decision, "reviewer": None, "decided_at": None, "reason": None, "corrected_value": None}
    return {
        "decision": decision,
        "reviewer": actor("A2 Business Reviewer"),
        "decided_at": "2026-08-26T11:40:00Z",
        "reason": f"Synthetic {decision} decision for deterministic regression.",
        "corrected_value": None,
    }


def baseline_assessment(aid: str, key: str, target_id: str | None, scope: str, value_type: str, value: object, a1_evidence_id: str) -> dict:
    return {
        "field_assessment_id": aid,
        "field_key": key,
        "entity_id": target_id,
        "scope": scope,
        "field_catalogue_version": CATALOGUE_VERSION,
        "value_type": value_type,
        "sensitivity_classification": "professional_business_data",
        "presence_status": "known",
        "availability_status": "available",
        "field_quality_status": "complete",
        "baseline": {
            "value": value,
            "normalised_value": value,
            "origin": {
                "system": "a1_handoff",
                "record_reference": a1_evidence_id,
                "field_reference": key,
                "source_kind": "a1_handoff",
            },
            "observed_at": "2026-08-16T15:30:00Z",
            "evidence_ids": [a1_evidence_id],
            "protected_status": "unassessed",
        },
        "observations": [],
        "proposed_resolution": {
            "action": "retain",
            "value": value,
            "normalised_value": value,
            "evidence_ids": [a1_evidence_id],
            "rationale": "Retain the value supplied by the approved A1 handoff.",
            "verification_status": "verified",
            "confidence_level": "medium",
            "freshness_status": "undated",
            "conflict_status": "none",
            "protected_status": "unassessed",
        },
        "field_review": field_review("not_required"),
        "application": application(),
    }


def gap_assessment(aid: str, key: str, target_id: str | None, scope: str, value_type: str) -> dict:
    return {
        "field_assessment_id": aid,
        "field_key": key,
        "entity_id": target_id,
        "scope": scope,
        "field_catalogue_version": CATALOGUE_VERSION,
        "value_type": value_type,
        "sensitivity_classification": "professional_business_data",
        "presence_status": "unknown",
        "availability_status": "not_checked",
        "field_quality_status": "gap",
        "baseline": None,
        "observations": [],
        "proposed_resolution": None,
        "field_review": field_review("pending"),
        "application": application(),
    }


def a2_evidence(evidence_id: str, assessment_ids: list[str], summary: str) -> dict:
    return {
        "evidence_id": evidence_id,
        "namespace": "a2",
        "source_id": "synthetic_step2f_business_site",
        "source_type": "synthetic_business_website",
        "source_policy_status": "approved",
        "source_url": "https://example.com/step2f-fixture",
        "provider_reference": None,
        "access_method": "synthetic_fixture",
        "retrieved_at": "2026-08-26T11:20:00Z",
        "source_date": None,
        "title": "Synthetic Step 2F Evidence",
        "excerpt_or_result_summary": summary,
        "claim_type": "direct_fact",
        "supports_field_assessment_ids": assessment_ids,
        "supports_requalification_signal_ids": [],
        "reliability_level": "medium",
        "independence_group_id": None,
        "provider_cost": None,
        "supersedes_evidence_id": None,
        "data_minimisation_notes": "Synthetic fixture only.",
    }


def enrich_assessment(assessment: dict, evidence_id: str, raw_value: object, normalised_value: object) -> None:
    assessment.update({
        "presence_status": "known",
        "availability_status": "available",
        "field_quality_status": "complete",
        "observations": [{
            "observation_id": f"A2-OBS-{assessment['field_assessment_id'].removeprefix('A2-FLD-')}",
            "raw_value": raw_value,
            "normalised_value": normalised_value,
            "evidence_ids": [evidence_id],
            "verification_status": "verified",
            "confidence_level": "medium",
            "freshness_status": "undated",
            "claim_type": "direct_fact",
            "error": None,
        }],
        "proposed_resolution": {
            "action": "add",
            "value": normalised_value,
            "normalised_value": normalised_value,
            "evidence_ids": [evidence_id],
            "rationale": "Synthetic evidence supports the proposed field value.",
            "verification_status": "verified",
            "confidence_level": "medium",
            "freshness_status": "undated",
            "conflict_status": "none",
            "protected_status": "not_protected",
        },
    })


def advance(previous: dict, tag: str, number: int, state: str, change_reason: str = "enrichment") -> dict:
    record = copy.deepcopy(previous)
    previous_revision_id = previous["record_metadata"]["record_revision_id"]
    record["record_metadata"].update({
        "record_revision_id": f"A2-REV-{tag}_{number:03d}",
        "revision_number": number,
        "supersedes_revision_id": previous_revision_id,
        "created_at": f"2026-08-26T11:{number:02d}:00Z",
        "change_reason": change_reason,
    })
    record["workflow"].update({
        "state": state,
        "previous_state": previous["workflow"]["state"],
        "transitioned_at": f"2026-08-26T11:{number:02d}:00Z",
        "hold_reasons": [],
        "block_reasons": [],
        "failure": None,
    })
    record["audit_and_consumption"]["events"].append({
        "event_id": f"A2-EVENT-{tag}_{number:03d}",
        "event_type": f"workflow_{state}",
        "actor": actor(),
        "timestamp": f"2026-08-26T11:{number:02d}:00Z",
        "input_references": [previous_revision_id],
        "output_references": [record["record_metadata"]["record_revision_id"]],
        "model": None,
        "tools": ["deterministic-step2f-fixture-builder"],
        "usage": None,
        "external_action": None,
    })
    return record


def make_initial(handoff: dict, tag: str) -> dict:
    record = base_record(handoff)
    record["record_metadata"].update({
        "a2_record_id": f"A2-{tag}_001",
        "record_revision_id": f"A2-REV-{tag}_001",
        "run_id": f"A2-RUN-{tag}_001",
        "audit_correlation_id": handoff["provenance"]["audit_correlation_id"],
    })
    record["source_handoff"]["accepted_by"] = actor()
    record["enrichment_scope"]["field_catalogue_version"] = CATALOGUE_VERSION
    record["enrichment_scope"]["initiated_by"] = actor()
    record["workflow"]["triggered_by"] = actor()
    record["system_references"]["a1_candidate_id"] = handoff["candidate_snapshot"]["candidate_id"]
    record["system_references"]["a1_handoff_id"] = handoff["handoff_id"]
    record["audit_and_consumption"]["events"][0]["event_id"] = f"A2-EVENT-{tag}_001"
    record["audit_and_consumption"]["events"][0]["actor"] = actor()
    record["audit_and_consumption"]["events"][0]["output_references"] = [record["record_metadata"]["record_revision_id"]]
    return record


def build_catalogue() -> dict:
    return {
        "catalogue_id": "equinet-a2-step2f-synthetic-catalogue",
        "version": CATALOGUE_VERSION,
        "status": "synthetic_test_only",
        "fields": [
            {"field_key": "person.full_name", "value_type": "string", "allowed_segments": ["farrier", "horse_owner"], "requirement_by_segment": {"farrier": "required", "horse_owner": "optional"}},
            {"field_key": "person.role_title", "value_type": "string", "allowed_segments": ["farrier", "horse_owner"], "requirement_by_segment": {"farrier": "required", "horse_owner": "optional"}},
            {"field_key": "person.business_email", "value_type": "string", "allowed_segments": ["farrier", "horse_owner"], "requirement_by_segment": {"farrier": "required", "horse_owner": "optional"}},
            {"field_key": "person.professional_credential", "value_type": "string", "allowed_segments": ["farrier"], "requirement_by_segment": {"farrier": "optional"}},
            {"field_key": "organisation.business_name", "value_type": "string", "allowed_segments": ["farrier", "horse_owner"], "requirement_by_segment": {"farrier": "required", "horse_owner": "required"}},
            {"field_key": "organisation.website", "value_type": "string", "allowed_segments": ["farrier", "horse_owner"], "requirement_by_segment": {"farrier": "required", "horse_owner": "required"}},
            {"field_key": "organisation.service_area", "value_type": "string_array", "allowed_segments": ["farrier"], "requirement_by_segment": {"farrier": "optional"}},
            {"field_key": "organisation.horse_count", "value_type": "integer", "allowed_segments": ["horse_owner"], "requirement_by_segment": {"horse_owner": "required"}},
            {"field_key": "organisation.disciplines", "value_type": "string_array", "allowed_segments": ["horse_owner"], "requirement_by_segment": {"horse_owner": "optional"}},
            {"field_key": "relationship.role", "value_type": "string", "allowed_segments": ["farrier", "horse_owner"], "requirement_by_segment": {"farrier": "optional", "horse_owner": "optional"}},
        ],
    }


def prepare_owner_chain() -> dict[str, dict]:
    initial = copy.deepcopy(load(STEP2E / "valid" / "valid-initial-record.json"))
    initial["record_metadata"].update({"a2_record_id": "A2-STEP2F_OWNER_001", "record_revision_id": "A2-REV-STEP2F_OWNER_001", "run_id": "A2-RUN-STEP2F_OWNER_001"})
    initial["enrichment_scope"]["field_catalogue_version"] = CATALOGUE_VERSION
    initial["audit_and_consumption"]["events"][0]["event_id"] = "A2-EVENT-STEP2F_OWNER_001"
    initial["audit_and_consumption"]["events"][0]["output_references"] = ["A2-REV-STEP2F_OWNER_001"]

    organisation = initial["subject"]["entities"][0]
    organisation["entity_id"] = "A2-ENT-STEP2F_OWNER_ORG"
    candidate = initial["source_handoff"]["handoff_snapshot"]["candidate_snapshot"]
    evidence_id = candidate["source_evidence"][0]["evidence_id"]

    planned = advance(initial, "STEP2F_OWNER", 2, "enrichment_planned")
    planned["field_assessments"] = [
        baseline_assessment("A2-FLD-OWNER-NAME", "organisation.business_name", organisation["entity_id"], "organisation", "string", candidate["identity"]["organisation"]["name"], evidence_id),
        baseline_assessment("A2-FLD-OWNER-WEBSITE", "organisation.website", organisation["entity_id"], "organisation", "string", candidate["identity"]["organisation"]["website"], evidence_id),
        gap_assessment("A2-FLD-OWNER-HORSE-COUNT", "organisation.horse_count", organisation["entity_id"], "organisation", "integer"),
    ]
    planned["data_quality"].update({
        "status": "incomplete", "required_field_keys": ["organisation.business_name", "organisation.website", "organisation.horse_count"],
        "missing_field_keys": ["organisation.horse_count"], "unverified_field_keys": [], "conflict_field_keys": [], "stale_field_keys": [], "invalid_field_keys": [],
        "limitations": ["Horse count has not yet been checked."],
    })

    progress = advance(planned, "STEP2F_OWNER", 3, "enrichment_in_progress")
    evidence = a2_evidence("A2-EV-STEP2F-OWNER-HORSES", ["A2-FLD-OWNER-HORSE-COUNT"], "Synthetic evidence confirms a horse count of twelve.")
    progress["evidence_registry"].append(evidence)
    horse_count = next(item for item in progress["field_assessments"] if item["field_key"] == "organisation.horse_count")
    enrich_assessment(horse_count, evidence["evidence_id"], "12 horses", 12)
    progress["data_quality"].update({"status": "review_ready", "calculated_at": "2026-08-26T11:30:00Z", "missing_field_keys": [], "unverified_field_keys": [], "limitations": []})

    review_ready = advance(progress, "STEP2F_OWNER", 4, "review_required")
    approved = advance(review_ready, "STEP2F_OWNER", 5, "record_approved", "human_review")
    for assessment in approved["field_assessments"]:
        if assessment["proposed_resolution"] and assessment["field_review"]["decision"] == "pending":
            assessment["field_review"] = field_review("approved")
    approved["review"] = {
        "record_decision": "approved", "reviewer": actor("A2 Business Reviewer"),
        "decided_at": "2026-08-26T11:50:00Z", "reason": "Synthetic owner record approved for the next permitted stage.",
        "required_field_decisions_complete": True, "requested_changes": [],
    }
    return {"initial": initial, "planned": planned, "progress": progress, "review_ready": review_ready, "approved": approved}


def prepare_farrier_chain() -> dict[str, dict]:
    handoff = load(CONTRACTS / "examples" / "valid" / "valid-farrier-handoff.json")
    initial = make_initial(handoff, "STEP2F_FARRIER")
    initial["governance"]["contains_personal_data"] = True
    initial["governance"]["data_categories"] = ["synthetic_professional_contact_data"]
    candidate = handoff["candidate_snapshot"]
    evidence_id = candidate["source_evidence"][0]["evidence_id"]
    initial["subject"] = {
        "identity_resolution_status": "resolved",
        "entities": [
            {"entity_id": "A2-ENT-STEP2F_FARRIER_PERSON", "entity_type": "person", "source_identity_reference": "candidate_snapshot.identity.person", "display_name": candidate["identity"]["person"]["full_name"], "aliases": [], "match_status": "not_checked", "external_matches": []},
            {"entity_id": "A2-ENT-STEP2F_FARRIER_ORG", "entity_type": "organisation", "source_identity_reference": "candidate_snapshot.identity.organisation", "display_name": candidate["identity"]["organisation"]["name"], "aliases": [], "match_status": "not_checked", "external_matches": []},
        ],
        "relationships": [{"relationship_id": "A2-REL-STEP2F_FARRIER_WORKS", "from_entity_id": "A2-ENT-STEP2F_FARRIER_PERSON", "to_entity_id": "A2-ENT-STEP2F_FARRIER_ORG", "relationship_type": "works_for", "evidence_ids": [evidence_id]}],
        "material_conflicts": [],
    }

    planned = advance(initial, "STEP2F_FARRIER", 2, "enrichment_planned")
    planned["field_assessments"] = [
        baseline_assessment("A2-FLD-FARRIER-NAME", "person.full_name", "A2-ENT-STEP2F_FARRIER_PERSON", "person", "string", candidate["identity"]["person"]["full_name"], evidence_id),
        baseline_assessment("A2-FLD-FARRIER-ROLE", "person.role_title", "A2-ENT-STEP2F_FARRIER_PERSON", "person", "string", candidate["identity"]["person"]["role_title"], evidence_id),
        baseline_assessment("A2-FLD-FARRIER-BUSINESS", "organisation.business_name", "A2-ENT-STEP2F_FARRIER_ORG", "organisation", "string", candidate["identity"]["organisation"]["name"], evidence_id),
        baseline_assessment("A2-FLD-FARRIER-WEBSITE", "organisation.website", "A2-ENT-STEP2F_FARRIER_ORG", "organisation", "string", candidate["identity"]["organisation"]["website"], evidence_id),
        gap_assessment("A2-FLD-FARRIER-EMAIL", "person.business_email", "A2-ENT-STEP2F_FARRIER_PERSON", "person", "string"),
        gap_assessment("A2-FLD-FARRIER-CREDENTIAL", "person.professional_credential", "A2-ENT-STEP2F_FARRIER_PERSON", "person", "string"),
    ]
    planned["data_quality"].update({
        "status": "incomplete",
        "required_field_keys": ["person.full_name", "person.role_title", "person.business_email", "organisation.business_name", "organisation.website"],
        "missing_field_keys": ["person.business_email"], "unverified_field_keys": [], "conflict_field_keys": [], "stale_field_keys": [], "invalid_field_keys": [],
        "limitations": ["Business email has not yet been checked."],
    })

    progress = advance(planned, "STEP2F_FARRIER", 3, "enrichment_in_progress")
    email_evidence = a2_evidence("A2-EV-STEP2F-FARRIER-EMAIL", ["A2-FLD-FARRIER-EMAIL"], "Synthetic official site publishes a professional email address.")
    email_evidence.update({"source_id": "synthetic_step2f_primary_site", "source_url": "https://example.com/step2f-primary", "independence_group_id": "synthetic-source-primary"})
    credential_evidence = a2_evidence("A2-EV-STEP2F-FARRIER-CREDENTIAL", ["A2-FLD-FARRIER-CREDENTIAL"], "Synthetic official registry confirms a professional credential.")
    credential_evidence.update({"source_id": "synthetic_step2f_registry", "source_url": "https://example.org/step2f-registry", "independence_group_id": "synthetic-source-registry"})
    progress["evidence_registry"].extend([email_evidence, credential_evidence])
    enrich_assessment(next(item for item in progress["field_assessments"] if item["field_key"] == "person.business_email"), email_evidence["evidence_id"], "farrier@example.com", "farrier@example.com")
    enrich_assessment(next(item for item in progress["field_assessments"] if item["field_key"] == "person.professional_credential"), credential_evidence["evidence_id"], "Synthetic Certified Farrier", "Synthetic Certified Farrier")
    progress["data_quality"].update({"status": "review_ready", "calculated_at": "2026-08-26T11:30:00Z", "missing_field_keys": [], "unverified_field_keys": [], "limitations": []})

    review_ready = advance(progress, "STEP2F_FARRIER", 4, "review_required")
    approved = advance(review_ready, "STEP2F_FARRIER", 5, "record_approved", "human_review")
    for assessment in approved["field_assessments"]:
        if assessment["proposed_resolution"] and assessment["field_review"]["decision"] == "pending":
            assessment["field_review"] = field_review("approved")
    approved["review"] = {
        "record_decision": "approved", "reviewer": actor("A2 Business Reviewer"),
        "decided_at": "2026-08-26T11:50:00Z", "reason": "Synthetic Farrier record approved for the next permitted stage.",
        "required_field_decisions_complete": True, "requested_changes": [],
    }
    return {"initial": initial, "planned": planned, "progress": progress, "review_ready": review_ready, "approved": approved}


def main() -> None:
    catalogue = build_catalogue()
    write(CATALOGUE_PATH, catalogue)
    owner = prepare_owner_chain()
    farrier = prepare_farrier_chain()

    cases: list[dict] = []

    def valid(name: str, record: dict, previous: dict | None, expected: dict, use_catalogue: bool = True) -> None:
        record_path = VALID / f"{name}.json"
        write(record_path, record)
        case = {"name": name, "record": str(record_path.relative_to(FIXTURES)), "expected_valid": True, "expected": expected}
        if use_catalogue:
            case["field_catalogue"] = CATALOGUE_PATH.name
        if previous is not None:
            previous_path = VALID / f"{name}-previous.json"
            write(previous_path, previous)
            case["previous_record"] = str(previous_path.relative_to(FIXTURES))
        cases.append(case)

    valid("farrier-initial", farrier["initial"], None, {"segment": "farrier", "workflow_state": "initialised", "data_quality_status": "unassessed", "a2_eligibility_status": "not_checked", "record_decision": "pending", "external_actions": 0}, use_catalogue=False)
    valid("farrier-planned-gap", farrier["planned"], farrier["initial"], {"segment": "farrier", "workflow_state": "enrichment_planned", "data_quality_status": "incomplete", "a2_eligibility_status": "not_checked", "record_decision": "pending", "external_actions": 0, "missing_field_keys": ["person.business_email"]})
    valid("farrier-enrichment-in-progress", farrier["progress"], farrier["planned"], {"segment": "farrier", "workflow_state": "enrichment_in_progress", "data_quality_status": "review_ready", "a2_eligibility_status": "not_checked", "record_decision": "pending", "external_actions": 0})
    valid("farrier-review-required", farrier["review_ready"], farrier["progress"], {"segment": "farrier", "workflow_state": "review_required", "data_quality_status": "review_ready", "a2_eligibility_status": "not_checked", "record_decision": "pending", "external_actions": 0})
    valid("farrier-record-approved", farrier["approved"], farrier["review_ready"], {"segment": "farrier", "workflow_state": "record_approved", "data_quality_status": "review_ready", "a2_eligibility_status": "not_checked", "record_decision": "approved", "external_actions": 0})

    valid("horse-owner-initial", owner["initial"], None, {"segment": "horse_owner", "workflow_state": "initialised", "data_quality_status": "unassessed", "a2_eligibility_status": "not_checked", "record_decision": "pending", "external_actions": 0}, use_catalogue=False)
    valid("horse-owner-planned-gap", owner["planned"], owner["initial"], {"segment": "horse_owner", "workflow_state": "enrichment_planned", "data_quality_status": "incomplete", "a2_eligibility_status": "not_checked", "record_decision": "pending", "external_actions": 0, "missing_field_keys": ["organisation.horse_count"]})
    valid("horse-owner-enrichment-in-progress", owner["progress"], owner["planned"], {"segment": "horse_owner", "workflow_state": "enrichment_in_progress", "data_quality_status": "review_ready", "a2_eligibility_status": "not_checked", "record_decision": "pending", "external_actions": 0})
    valid("horse-owner-review-required", owner["review_ready"], owner["progress"], {"segment": "horse_owner", "workflow_state": "review_required", "data_quality_status": "review_ready", "a2_eligibility_status": "not_checked", "record_decision": "pending", "external_actions": 0})
    valid("horse-owner-record-approved", owner["approved"], owner["review_ready"], {"segment": "horse_owner", "workflow_state": "record_approved", "data_quality_status": "review_ready", "a2_eligibility_status": "not_checked", "record_decision": "approved", "external_actions": 0})

    owner_gap = advance(owner["planned"], "STEP2F_OWNER_GAP", 3, "held", "human_review")
    owner_gap["review"] = {"record_decision": "held", "reviewer": actor("A2 Business Reviewer"), "decided_at": "2026-08-26T11:40:00Z", "reason": "Required horse-count evidence remains unavailable.", "required_field_decisions_complete": False, "requested_changes": ["Obtain approved horse-count evidence."]}
    owner_gap["workflow"]["hold_reasons"] = ["Required horse-count evidence remains unavailable."]
    valid("horse-owner-gap-held", owner_gap, owner["planned"], {"segment": "horse_owner", "workflow_state": "held", "data_quality_status": "incomplete", "a2_eligibility_status": "not_checked", "record_decision": "held", "external_actions": 0, "missing_field_keys": ["organisation.horse_count"], "hold_reason_count": 1})

    farrier_conflict = advance(farrier["progress"], "STEP2F_FARRIER_CONFLICT", 4, "held", "human_review")
    conflict_evidence = a2_evidence("A2-EV-STEP2F-FARRIER-EMAIL-CONFLICT", ["A2-FLD-FARRIER-EMAIL"], "Synthetic second source publishes a conflicting professional email.")
    conflict_evidence.update({"source_id": "synthetic_step2f_secondary_site", "source_url": "https://example.org/step2f-secondary", "title": "Synthetic Independent Secondary Source", "independence_group_id": "synthetic-source-secondary"})
    farrier_conflict["evidence_registry"].append(conflict_evidence)
    email_field = next(item for item in farrier_conflict["field_assessments"] if item["field_key"] == "person.business_email")
    email_field["observations"].append({"observation_id": "A2-OBS-FARRIER-EMAIL-CONFLICT", "raw_value": "other@example.com", "normalised_value": "other@example.com", "evidence_ids": [conflict_evidence["evidence_id"]], "verification_status": "verified", "confidence_level": "medium", "freshness_status": "undated", "claim_type": "contradictory_evidence", "error": None})
    email_field["field_quality_status"] = "conflict"
    email_field["proposed_resolution"].update({"action": "hold", "value": None, "normalised_value": None, "evidence_ids": ["A2-EV-STEP2F-FARRIER-EMAIL", conflict_evidence["evidence_id"]], "rationale": "Conflicting professional email values require review.", "conflict_status": "material"})
    email_field["field_review"] = field_review("held")
    farrier_conflict["data_quality"].update({"status": "conflict", "conflict_field_keys": ["person.business_email"], "limitations": ["Conflicting professional email values."]})
    farrier_conflict["review"] = {"record_decision": "held", "reviewer": actor("A2 Business Reviewer"), "decided_at": "2026-08-26T11:40:00Z", "reason": "Material field conflict.", "required_field_decisions_complete": False, "requested_changes": ["Resolve the email conflict."]}
    farrier_conflict["workflow"]["hold_reasons"] = ["Material field conflict."]
    valid("farrier-conflict-held", farrier_conflict, farrier["progress"], {"segment": "farrier", "workflow_state": "held", "data_quality_status": "conflict", "a2_eligibility_status": "not_checked", "record_decision": "held", "external_actions": 0, "conflict_field_keys": ["person.business_email"], "contradictory_observation_count": 1})

    possible_duplicate = advance(owner["planned"], "STEP2F_OWNER_DUP", 3, "held", "human_review")
    possible_duplicate["duplicate_and_eligibility"].update({"a2_eligibility_status": "hold", "evaluated_at": "2026-08-26T11:30:00Z", "method_version": "synthetic-dedup-0.1.0", "reasons": ["Possible duplicate requires review."]})
    possible_duplicate["duplicate_and_eligibility"]["checks"] = [{"check_id": "A2-CHECK-STEP2F-OWNER-DUP", "check_type": "duplicate", "system": "a2_local", "status": "possible_match", "checked_at": "2026-08-26T11:30:00Z", "matches_or_references": [{"reference_type": "candidate", "reference_id": "A2-OTHER-OWNER", "system": "a2_local", "object_type": "organisation"}], "reason": "Synthetic possible duplicate."}]
    possible_duplicate["review"] = {"record_decision": "held", "reviewer": actor("A2 Business Reviewer"), "decided_at": "2026-08-26T11:40:00Z", "reason": "Possible duplicate requires review.", "required_field_decisions_complete": False, "requested_changes": ["Resolve duplicate."]}
    possible_duplicate["workflow"]["hold_reasons"] = ["Possible duplicate requires review."]
    valid("horse-owner-possible-duplicate-held", possible_duplicate, owner["planned"], {"segment": "horse_owner", "workflow_state": "held", "data_quality_status": "incomplete", "a2_eligibility_status": "hold", "record_decision": "held", "external_actions": 0, "duplicate_statuses": ["possible_match"]})

    confirmed_duplicate = advance(farrier["planned"], "STEP2F_FARRIER_DUP", 3, "blocked", "human_review")
    confirmed_duplicate["duplicate_and_eligibility"].update({"a2_eligibility_status": "blocked", "evaluated_at": "2026-08-26T11:30:00Z", "method_version": "synthetic-dedup-0.1.0", "reasons": ["Confirmed duplicate blocks progression."]})
    confirmed_duplicate["duplicate_and_eligibility"]["checks"] = [{"check_id": "A2-CHECK-STEP2F-FARRIER-DUP", "check_type": "duplicate", "system": "a2_local", "status": "confirmed_duplicate", "checked_at": "2026-08-26T11:30:00Z", "matches_or_references": [{"reference_type": "candidate", "reference_id": "A2-OTHER-FARRIER", "system": "a2_local", "object_type": "person"}], "reason": "Synthetic confirmed duplicate."}]
    confirmed_duplicate["review"] = {"record_decision": "blocked", "reviewer": actor("A2 Business Reviewer"), "decided_at": "2026-08-26T11:40:00Z", "reason": "Confirmed duplicate.", "required_field_decisions_complete": False, "requested_changes": []}
    confirmed_duplicate["workflow"]["block_reasons"] = ["Confirmed duplicate."]
    valid("farrier-confirmed-duplicate-blocked", confirmed_duplicate, farrier["planned"], {"segment": "farrier", "workflow_state": "blocked", "data_quality_status": "incomplete", "a2_eligibility_status": "blocked", "record_decision": "blocked", "external_actions": 0, "duplicate_statuses": ["confirmed_duplicate"]})

    protected = advance(farrier["progress"], "STEP2F_FARRIER_PROTECTED", 4, "review_required")
    website = next(item for item in protected["field_assessments"] if item["field_key"] == "organisation.website")
    website_evidence = a2_evidence("A2-EV-STEP2F-FARRIER-WEBSITE-NEW", ["A2-FLD-FARRIER-WEBSITE"], "A distinct synthetic source publishes the proposed replacement website.")
    website_evidence.update({"source_id": "synthetic_step2f_alternate_site", "source_url": "https://example.org/bluegrass-hoof-care-new", "title": "Synthetic Alternate Business Website"})
    protected["evidence_registry"].append(website_evidence)
    website["baseline"]["protected_status"] = "protected_manual"
    website["observations"].append({
        "observation_id": "A2-OBS-FARRIER-WEBSITE-NEW", "raw_value": "https://example.org/bluegrass-hoof-care-new",
        "normalised_value": "https://example.org/bluegrass-hoof-care-new", "evidence_ids": [website_evidence["evidence_id"]],
        "verification_status": "verified", "confidence_level": "medium", "freshness_status": "undated",
        "claim_type": "direct_fact", "error": None
    })
    website["proposed_resolution"].update({"action": "update", "value": "https://example.org/bluegrass-hoof-care-new", "normalised_value": "https://example.org/bluegrass-hoof-care-new", "evidence_ids": [website_evidence["evidence_id"]], "protected_status": "protected_manual"})
    website["field_review"] = field_review("pending")
    protected["review"]["required_field_decisions_complete"] = False
    valid("farrier-protected-update-awaiting-review", protected, farrier["progress"], {"segment": "farrier", "workflow_state": "review_required", "data_quality_status": "review_ready", "a2_eligibility_status": "not_checked", "record_decision": "pending", "external_actions": 0, "protected_pending_count": 1, "proposed_actions": ["add", "update"]})

    step2e_full = load(STEP2E / "valid" / "valid-complete-requalification-record.json")
    step2e_prior = load(STEP2E / "valid" / "valid-initial-record.json")
    step2e_full["enrichment_scope"].update({"mode": "targeted_fields", "requested_field_keys": ["organisation.horse_count"], "field_catalogue_version": CATALOGUE_VERSION})
    for assessment in step2e_full["field_assessments"]:
        assessment["field_catalogue_version"] = CATALOGUE_VERSION
    valid("horse-owner-complete-requalification", step2e_full, step2e_prior, {"segment": "horse_owner", "workflow_state": "enrichment_planned", "data_quality_status": "needs_review", "a2_eligibility_status": "not_checked", "record_decision": "pending", "external_actions": 0, "requalification_signals": 1, "requalification_returns": 1, "score_revisions": 1, "signal_statuses": ["accepted_by_a1"], "return_statuses": ["accepted_by_a1"], "score_revision_statuses": ["approved"]})

    def invalid(name: str, record: dict, previous: dict | None, expected_error: str, expected_error_count: int = 1) -> None:
        record_path = INVALID / f"{name}.json"
        write(record_path, record)
        previous_path = None
        if previous is not None:
            previous_path = INVALID / f"{name}-previous.json"
            write(previous_path, previous)
        case = {"name": name, "record": str(record_path.relative_to(FIXTURES)), "field_catalogue": CATALOGUE_PATH.name, "expected_valid": False, "expected_error": expected_error, "expected_error_count": expected_error_count}
        if previous_path:
            case["previous_record"] = str(previous_path.relative_to(FIXTURES))
        cases.append(case)

    item = copy.deepcopy(farrier["progress"])
    item["evidence_registry"] = []
    invalid("missing-evidence", item, farrier["planned"], "references unknown evidence ID", expected_error_count=4)

    item = copy.deepcopy(farrier["progress"])
    item["evidence_registry"][0]["source_policy_status"] = "blocked"
    invalid("blocked-source-evidence", item, farrier["planned"], "not approved for evidentiary use", expected_error_count=2)

    item = copy.deepcopy(protected)
    website = next(field for field in item["field_assessments"] if field["field_key"] == "organisation.website")
    website["application"]["status"] = "pending"
    invalid("protected-overwrite-without-approval", item, farrier["progress"], "requires explicit approved review and approval matrix", expected_error_count=5)

    item = copy.deepcopy(owner["review_ready"])
    item["workflow"]["state"] = "synced"
    item["system_references"]["hubspot_sync_id"] = "FAKE-SYNC"
    item["governance"]["crm_write_authorized"] = True
    invalid("false-synthetic-sync", item, owner["progress"], "synthetic_test record cannot authorise CRM write or provider use", expected_error_count=4)

    item = copy.deepcopy(step2e_full)
    item["requalification"]["signals"][0]["points_awarded"] = 20
    invalid("a2-score-production", item, step2e_prior, "Additional properties are not allowed")

    item = copy.deepcopy(owner["review_ready"])
    item["governance"]["outreach_authorized"] = True
    invalid("prohibited-outreach", item, owner["progress"], "A2 must not authorise outreach")

    item = copy.deepcopy(farrier["progress"])
    item["evidence_registry"][0]["provider_reference"] = "UNAPPROVED-PROVIDER-REQUEST"
    invalid("provider-without-approval", item, farrier["planned"], "claims provider use without authorisation")

    item = copy.deepcopy(owner["review_ready"])
    cross_segment = gap_assessment("A2-FLD-OWNER-CREDENTIAL", "person.professional_credential", None, "record", "string")
    item["field_assessments"].append(cross_segment)
    invalid("cross-segment-field", item, owner["progress"], "is not allowed for segment horse_owner")

    item = advance(owner["initial"], "STEP2F_OWNER_MISSING", 2, "enrichment_planned")
    item["field_assessments"] = [
        baseline_assessment("A2-FLD-OWNER-NAME", "organisation.business_name", "A2-ENT-STEP2F_OWNER_ORG", "organisation", "string", item["source_handoff"]["handoff_snapshot"]["candidate_snapshot"]["identity"]["organisation"]["name"], "EV-TEST002"),
        baseline_assessment("A2-FLD-OWNER-WEBSITE", "organisation.website", "A2-ENT-STEP2F_OWNER_ORG", "organisation", "string", item["source_handoff"]["handoff_snapshot"]["candidate_snapshot"]["identity"]["organisation"]["website"], "EV-TEST002"),
    ]
    item["data_quality"]["required_field_keys"] = ["organisation.business_name", "organisation.website", "organisation.horse_count"]
    item["data_quality"]["missing_field_keys"] = ["organisation.horse_count"]
    item["data_quality"]["status"] = "incomplete"
    invalid("required-package-missing-assessment", item, owner["initial"], "references field key without an assessment", expected_error_count=2)

    item = copy.deepcopy(owner["review_ready"])
    item["data_quality"]["status"] = "review_ready"
    item["data_quality"]["conflict_field_keys"] = ["organisation.horse_count"]
    invalid("review-ready-with-conflict", item, owner["progress"], "review_ready cannot contain missing, conflict or invalid fields")

    item = copy.deepcopy(owner["review_ready"])
    item["duplicate_and_eligibility"]["checks"] = [{"check_id": "A2-CHECK-STEP2F-BAD-DUP", "check_type": "duplicate", "system": "a2_local", "status": "confirmed_duplicate", "checked_at": "2026-08-26T11:30:00Z", "matches_or_references": [{"reference_type": "candidate", "reference_id": "A2-DUPLICATE", "system": "a2_local", "object_type": "organisation"}], "reason": "Synthetic confirmed duplicate."}]
    item["duplicate_and_eligibility"]["a2_eligibility_status"] = "eligible"
    invalid("confirmed-duplicate-marked-eligible", item, owner["progress"], "confirmed duplicate requires blocked A2 eligibility")

    item = copy.deepcopy(step2e_full)
    item["requalification"]["score_revision_references"][0]["revised_scoring"]["score"] = 99
    invalid("invalid-a1-score-revision", item, step2e_prior, "revised scoring score must equal component total", expected_error_count=3)

    item = advance(farrier["review_ready"], "STEP2F_FARRIER_BADREVIEW", 5, "record_approved", "human_review")
    email_field = next(field for field in item["field_assessments"] if field["field_key"] == "person.business_email")
    email_field["field_review"] = field_review("approved")
    item["review"] = {"record_decision": "approved", "reviewer": actor("A2 Business Reviewer"), "decided_at": "2026-08-26T11:50:00Z", "reason": "Synthetic approval.", "required_field_decisions_complete": True, "requested_changes": []}
    invalid("record-approved-with-incomplete-field-decisions", item, farrier["review_ready"], "required_field_decisions_complete is true while field reviews remain unresolved")

    for case in cases:
        record_path = FIXTURES / case["record"]
        case["record_sha256"] = file_hash(record_path)
        if case.get("previous_record"):
            case["previous_record_sha256"] = file_hash(FIXTURES / case["previous_record"])
    write(MANIFEST_PATH, {"step": "2F", "suite_version": "0.1.0", "catalogue": CATALOGUE_PATH.name, "cases": cases})
    with MATRIX_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["scenario", "segment", "expected_result", "workflow_state", "data_quality_status", "eligibility_status", "record_decision", "previous_record", "expected_error"])
        writer.writeheader()
        for case in cases:
            record = load(FIXTURES / case["record"])
            expected = case.get("expected", {})
            writer.writerow({
                "scenario": case["name"],
                "segment": record["source_handoff"]["handoff_snapshot"]["candidate_snapshot"]["segment"],
                "expected_result": "valid" if case["expected_valid"] else "invalid",
                "workflow_state": expected.get("workflow_state", record["workflow"]["state"]),
                "data_quality_status": expected.get("data_quality_status", record["data_quality"]["status"]),
                "eligibility_status": expected.get("a2_eligibility_status", record["duplicate_and_eligibility"]["a2_eligibility_status"]),
                "record_decision": expected.get("record_decision", record["review"]["record_decision"]),
                "previous_record": case.get("previous_record", ""),
                "expected_error": case.get("expected_error", ""),
            })
    print(json.dumps({
        "catalogue": str(CATALOGUE_PATH),
        "valid_cases": sum(case["expected_valid"] for case in cases),
        "invalid_cases": sum(not case["expected_valid"] for case in cases),
        "total_cases": len(cases),
        "manifest": str(MANIFEST_PATH),
        "matrix": str(MATRIX_PATH),
    }, indent=2))


if __name__ == "__main__":
    main()
