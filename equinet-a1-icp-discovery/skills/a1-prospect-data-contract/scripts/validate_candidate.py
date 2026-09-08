#!/usr/bin/env python3
"""Validate an Equinet A1 Prospect Candidate against the JSON Schema and cross-reference rules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = SKILL_DIR / "references" / "prospect-candidate.schema.json"


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def path_text(error) -> str:
    return "/" + "/".join(str(item) for item in error.absolute_path)


def cross_reference_errors(candidate: dict) -> list[str]:
    errors: list[str] = []
    evidence = candidate.get("source_evidence", [])
    evidence_ids = [item.get("evidence_id") for item in evidence if isinstance(item, dict)]
    evidence_set = set(evidence_ids)
    evidence_by_id = {
        item.get("evidence_id"): item
        for item in evidence
        if isinstance(item, dict) and item.get("evidence_id")
    }

    if len(evidence_ids) != len(evidence_set):
        errors.append("Duplicate evidence_id values are not allowed.")

    blocked = [item.get("evidence_id") for item in evidence if item.get("source_policy_status") == "blocked"]
    if blocked:
        errors.append(f"Blocked sources cannot support a candidate: {', '.join(blocked)}")

    seen_contacts: set[tuple[str, str]] = set()
    for index, contact in enumerate(candidate.get("public_contacts", [])):
        contact_key = (str(contact.get("contact_type")), str(contact.get("value")).strip().lower())
        if contact_key in seen_contacts:
            errors.append(f"public_contacts[{index}] duplicates contact value {contact.get('value')!r}.")
        seen_contacts.add(contact_key)
        for evidence_id in contact.get("evidence_ids", []):
            if evidence_id not in evidence_set:
                errors.append(f"public_contacts[{index}] references unknown evidence_id {evidence_id!r}.")

    contact_labels = {str(contact.get("label") or "") for contact in candidate.get("public_contacts", [])}
    primary_labels = {label for label in contact_labels if label.startswith("Primary named contact —")}
    secondary_labels = {label for label in contact_labels if label.startswith("Secondary named contact —")}
    primary_person = candidate.get("identity", {}).get("person")
    if len(primary_labels) > 1:
        errors.append("A candidate may retain at most one primary named contact.")
    if len(secondary_labels) > 1:
        errors.append("A candidate may retain at most one secondary named contact.")
    if (primary_labels or secondary_labels) and primary_person is None:
        errors.append("Named contact details require the selected primary contact in identity.person.")
    if primary_labels and primary_person:
        full_name = str(primary_person.get("full_name") or "").lower()
        if not all(full_name in label.lower() for label in primary_labels):
            errors.append("Primary named contact labels must identify the same person stored in identity.person.")

    criteria = candidate.get("qualification", {}).get("criteria", [])
    criterion_ids = [item.get("criterion_id") for item in criteria if isinstance(item, dict)]
    criterion_set = set(criterion_ids)
    if len(criterion_ids) != len(criterion_set):
        errors.append("Duplicate qualification criterion_id values are not allowed.")

    for index, criterion in enumerate(criteria):
        criterion_id = criterion.get("criterion_id")
        status = criterion.get("status")
        refs = criterion.get("evidence_ids", [])
        if status == "confirmed" and not refs:
            errors.append(f"qualification.criteria[{index}] is confirmed but has no evidence_id.")
        for evidence_id in refs:
            source = evidence_by_id.get(evidence_id)
            if source is None:
                errors.append(f"qualification.criteria[{index}] references unknown evidence_id {evidence_id!r}.")
                continue
            if status == "confirmed" and source.get("source_policy_status") not in {"approved", "conditional"}:
                errors.append(
                    f"qualification.criteria[{index}] is confirmed using evidence {evidence_id!r} "
                    "that is not approved or conditional."
                )
            if status == "confirmed" and criterion_id not in source.get("supports_claims", []):
                errors.append(
                    f"Evidence {evidence_id!r} does not list confirmed criterion {criterion_id!r} in supports_claims."
                )

    scoring = candidate.get("scoring", {})
    components = scoring.get("components", [])
    component_ids: list[str] = []
    for index, component in enumerate(components):
        criterion_id = component.get("criterion_id")
        component_ids.append(criterion_id)
        if criterion_id not in criterion_set:
            errors.append(f"scoring.components[{index}] references unknown criterion_id {criterion_id!r}.")
        if component.get("points_awarded", 0) > component.get("max_points", 0):
            errors.append(f"scoring.components[{index}] awards more than max_points.")
        for evidence_id in component.get("evidence_ids", []):
            source = evidence_by_id.get(evidence_id)
            if source is None:
                errors.append(f"scoring.components[{index}] references unknown evidence_id {evidence_id!r}.")
            elif source.get("source_policy_status") not in {"approved", "conditional"}:
                errors.append(f"scoring.components[{index}] uses evidence {evidence_id!r} that is not approved or conditional.")
    if len(component_ids) != len(set(component_ids)):
        errors.append("Duplicate scoring component criterion_id values are not allowed.")
    if scoring.get("status") == "scored":
        component_total = sum(float(item.get("points_awarded", 0)) for item in components)
        score = scoring.get("score")
        if score is not None and abs(component_total - float(score)) > 1e-6:
            errors.append(f"scoring.score ({score}) must equal the component total ({component_total:g}).")

    qualification = candidate.get("qualification", {})
    minimum_status = qualification.get("minimum_data_status")
    missing_minimum = qualification.get("missing_minimum_fields", [])
    if minimum_status == "pass" and missing_minimum:
        errors.append("minimum_data_status pass requires an empty missing_minimum_fields list.")
    if minimum_status == "fail" and not missing_minimum:
        errors.append("minimum_data_status fail requires at least one missing_minimum_fields entry.")

    exclusion_status = qualification.get("exclusion_status")
    recommendation = candidate.get("recommendation", {})
    workflow = candidate.get("workflow", {})
    if exclusion_status == "excluded" and recommendation.get("next_action") != "exclude":
        errors.append("An excluded candidate must have recommendation.next_action set to exclude.")
    if exclusion_status == "excluded" and workflow.get("stage") not in {"needs_review", "rejected"}:
        errors.append("An excluded candidate cannot progress beyond review or rejection.")

    expected_match_system = {
        "batch": "current_batch",
        "provided_exclusion_file": "provided_exclusion_file",
        "twenty": "twenty",
        "hubspot": "hubspot",
    }
    for check_name, result in candidate.get("duplicate_check", {}).items():
        status = result.get("status")
        matches = result.get("matches", [])
        if status in {"no_match", "not_checked_no_domain", "possible_match", "possible_duplicate", "confirmed_duplicate", "hubspot_duplicate", "error", "hubspot_check_failed"}:
            if not result.get("checked_at") or not result.get("method_version"):
                errors.append(f"duplicate_check.{check_name} status {status} requires checked_at and method_version.")
        if status in {"possible_match", "possible_duplicate", "confirmed_duplicate", "hubspot_duplicate"} and not matches:
            errors.append(f"duplicate_check.{check_name} status {status} requires at least one match.")
        if status in {"no_match", "not_checked_no_domain"} and matches:
            errors.append(f"duplicate_check.{check_name} status {status} requires an empty matches list.")
        if status == "unavailable" and not result.get("notes"):
            errors.append(f"duplicate_check.{check_name} status unavailable requires an explanatory note.")
        for match in matches:
            expected = expected_match_system.get(check_name)
            if expected and match.get("system") != expected:
                errors.append(
                    f"duplicate_check.{check_name} contains a match for system {match.get('system')!r}; expected {expected!r}."
                )

    decision = workflow.get("review_decision")
    reviewer = workflow.get("reviewer")
    decision_at = workflow.get("decision_at")
    if decision == "none" and (reviewer is not None or decision_at is not None):
        errors.append("review_decision none requires reviewer and decision_at to be null.")
    if decision in {"approved", "rejected", "needs_changes"} and (reviewer is None or decision_at is None):
        errors.append(f"review_decision {decision} requires reviewer and decision_at.")
    if decision == "rejected" and not workflow.get("rejection_reason"):
        errors.append("A rejected decision requires rejection_reason.")
    if decision == "rejected" and workflow.get("stage") != "rejected":
        errors.append("A rejected decision requires workflow.stage rejected.")

    quality = candidate.get("data_quality", {})
    if quality.get("validation_status") == "validated":
        if quality.get("missing_fields") or quality.get("conflicts") or not quality.get("last_validated_at"):
            errors.append("Validated data requires no missing fields, no conflicts and a validation timestamp.")

    references = candidate.get("system_references", {})
    twenty_company_id = references.get("twenty_company_id")
    twenty_person_id = references.get("twenty_person_id")
    relation_status = references.get("twenty_person_relation_status")
    if twenty_person_id and not twenty_company_id:
        errors.append("system_references.twenty_person_id requires twenty_company_id.")
    if twenty_person_id and relation_status != "verified":
        errors.append("A staged Twenty Person requires twenty_person_relation_status verified.")
    if relation_status == "verified" and not (twenty_company_id and twenty_person_id):
        errors.append("twenty_person_relation_status verified requires both Twenty IDs.")
    if relation_status == "not_required" and twenty_person_id:
        errors.append("twenty_person_relation_status not_required cannot include a Twenty Person ID.")
    stage = workflow.get("stage")
    if stage in {"a2_enrichment_in_progress", "a2_review_required", "approved_for_hubspot", "synced", "sync_failed"}:
        if not references.get("a2_handoff_id"):
            errors.append(f"workflow.stage {stage} requires system_references.a2_handoff_id.")
    if stage == "synced":
        if not references.get("hubspot_sync_id"):
            errors.append("workflow.stage synced requires system_references.hubspot_sync_id.")
        if not (references.get("hubspot_contact_id") or references.get("hubspot_company_id")):
            errors.append("workflow.stage synced requires a HubSpot Contact or Company ID.")

    record_kind = candidate.get("record_kind")
    provenance = candidate.get("provenance", {})
    synthetic = provenance.get("synthetic")
    if record_kind == "synthetic_test" and synthetic is not True:
        errors.append("synthetic_test records must set provenance.synthetic to true.")
    if record_kind == "production" and synthetic is not False:
        errors.append("production records must set provenance.synthetic to false.")
    if record_kind == "production" and (not provenance.get("model") or not provenance.get("tools_used")):
        errors.append("production records must identify the model and at least one tool used.")

    return errors


def validate(schema_path: Path, candidate_path: Path) -> int:
    schema = load_json(schema_path)
    candidate = load_json(candidate_path)

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    schema_errors = sorted(validator.iter_errors(candidate), key=lambda err: list(err.absolute_path))
    custom_errors = cross_reference_errors(candidate) if isinstance(candidate, dict) else ["Candidate root must be an object."]

    if not schema_errors and not custom_errors:
        print(f"VALID: {candidate_path}")
        return 0

    print(f"INVALID: {candidate_path}")
    for error in schema_errors:
        print(f"- {path_text(error)}: {error.message}")
    for error in custom_errors:
        print(f"- custom: {error}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    return validate(args.schema, args.candidate)


if __name__ == "__main__":
    sys.exit(main())
