#!/usr/bin/env python3
"""Validate an Equinet A2 canonical record beyond JSON Schema shape."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from validate_step2c_artifacts import configs as step2c_configs
from validate_step2c_artifacts import return_errors as step2c_return_errors
from validate_step2c_artifacts import revision_errors as step2c_revision_errors
from validate_step2c_artifacts import signal_errors as step2c_signal_errors
from validate_a1_to_a2_handoff import cross_field_errors as handoff_cross_field_errors

PROFILE_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = PROFILE_ROOT / "foundations" / "contracts"
SCHEMA_PATH = CONTRACTS / "canonical" / "a2-enrichment-record.schema.json"
STATE_MODEL_PATH = CONTRACTS / "a2-state-model-0.1.0.json"
EXTERNAL_SCHEMAS = [
    CONTRACTS / "dependencies" / "a1-prospect-candidate.schema.json",
    CONTRACTS / "a1-to-a2-handoff.schema.json",
    CONTRACTS / "requalification" / "a2-requalification-signal.schema.json",
    CONTRACTS / "requalification" / "a2-requalification-return.schema.json",
    CONTRACTS / "requalification" / "a1-score-revision-reference.schema.json",
]

SYNC_STATES = {"ready_for_sync", "sync_pending", "synced", "reconciled"}
ACTIVE_APPLICATION_STATES = {"pending", "applied", "failed", "reconciled"}
PROTECTED_STATES = {"protected_manual", "protected_policy", "protected_authoritative"}
APPROVED_SIGNAL_STATES = {"approved_for_return", "sent_to_a1", "accepted_by_a1", "rescored"}
A1_RESULT_SIGNAL_STATES = {"accepted_by_a1", "rescored"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def make_registry(schema: dict) -> Registry:
    registry = Registry()
    for path in EXTERNAL_SCHEMAS:
        dependency = load_json(path)
        registry = registry.with_resource(dependency["$id"], Resource.from_contents(dependency))
    return registry.with_resource(schema["$id"], Resource.from_contents(schema))


def schema_errors(record: dict, schema: dict, registry: Registry) -> list[str]:
    validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(record), key=lambda error: (list(error.absolute_path), error.message))
    rendered = []
    for error in errors:
        location = "/" + "/".join(str(part) for part in error.absolute_path)
        rendered.append(f"schema:{location}: {error.message}")
    return rendered


def duplicate_values(values: list[Any]) -> set[Any]:
    seen: set[Any] = set()
    duplicates: set[Any] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def all_references(record: dict) -> tuple[set[str], set[str]]:
    a1_evidence = {
        item.get("evidence_id")
        for item in record["source_handoff"]["handoff_snapshot"]["candidate_snapshot"].get("source_evidence", [])
        if item.get("evidence_id")
    }
    a2_evidence = {
        item.get("evidence_id")
        for item in record.get("evidence_registry", [])
        if item.get("evidence_id") and item.get("namespace") == "a2"
    }
    return a1_evidence, a2_evidence


def check_reference_list(errors: list[str], label: str, references: list[str], allowed: set[str]) -> None:
    for reference in references:
        if reference not in allowed:
            errors.append(f"{label} references unknown evidence ID {reference}")


def value_matches_type(value: object, value_type: str) -> bool:
    if value is None:
        return True
    checks = {
        "string": lambda item: isinstance(item, str),
        "enum": lambda item: isinstance(item, str),
        "date": lambda item: isinstance(item, str),
        "datetime": lambda item: isinstance(item, str),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
        "string_array": lambda item: isinstance(item, list) and all(isinstance(part, str) for part in item),
        "number_array": lambda item: isinstance(item, list) and all(isinstance(part, (int, float)) and not isinstance(part, bool) for part in item),
        "structured": lambda item: isinstance(item, dict) and "components" in item,
    }
    checker = checks.get(value_type)
    return checker(value) if checker else False


def check_current_record(record: dict, field_catalogue: dict | None = None) -> list[str]:
    errors: list[str] = []
    a1_criteria, a1_weights, a1_scoring_config = step2c_configs()
    metadata = record["record_metadata"]
    source = record["source_handoff"]
    handoff = source["handoff_snapshot"]
    candidate = handoff["candidate_snapshot"]
    enrichment_scope = record["enrichment_scope"]
    system_refs = record["system_references"]
    governance = record["governance"]
    workflow = record["workflow"]
    review = record["review"]

    # Immutable source wrapper integrity and identifier agreement.
    mirror_pairs = [
        ("source_handoff.handoff_schema_version", source["handoff_schema_version"], handoff["handoff_schema_version"]),
        ("source_handoff.handoff_id", source["handoff_id"], handoff["handoff_id"]),
        ("source_handoff.idempotency_key", source["idempotency_key"], handoff["idempotency_key"]),
        ("source_handoff.operating_scope", source["operating_scope"], handoff["operating_scope"]),
        ("source_handoff.eligibility_status", source["eligibility_status"], handoff["eligibility"]["status"]),
        ("source_handoff.candidate_snapshot_sha256", source["candidate_snapshot_sha256"], handoff["snapshot_integrity"]["candidate_snapshot_sha256"]),
        ("enrichment_scope.operating_scope", enrichment_scope["operating_scope"], source["operating_scope"]),
        ("system_references.a1_candidate_id", system_refs["a1_candidate_id"], candidate["candidate_id"]),
        ("system_references.a1_handoff_id", system_refs["a1_handoff_id"], source["handoff_id"]),
        ("record_metadata.audit_correlation_id", metadata["audit_correlation_id"], handoff["provenance"]["audit_correlation_id"]),
    ]
    for label, actual, expected in mirror_pairs:
        if actual != expected:
            errors.append(f"{label} does not match its authoritative source")

    actual_candidate_hash = canonical_hash(candidate)
    if source["candidate_snapshot_sha256"] != actual_candidate_hash:
        errors.append("source_handoff candidate snapshot hash mismatch")
    a1_schema = load_json(EXTERNAL_SCHEMAS[0])
    for handoff_error in handoff_cross_field_errors(handoff, a1_schema):
        errors.append(f"embedded handoff invalid: {handoff_error}")

    if source["eligibility_status"] != "eligible":
        errors.append("canonical A2 record requires an eligible accepted handoff")
    if source["accepted_by"]["profile_id"] != "equinet-a2-enrichment":
        errors.append("source_handoff accepted_by profile must be equinet-a2-enrichment")
    if handoff.get("a2_receipt") is not None and source["accepted_at"] != handoff["a2_receipt"]["received_at"]:
        errors.append("source_handoff accepted_at does not match the A2 receipt")
    if source["operating_scope"] == "manual_no_integration_pilot":
        if handoff["delivery_state"] != "ready_for_delivery":
            errors.append("manual no-integration canonical record requires a ready_for_delivery handoff")
    elif handoff["delivery_state"] != "accepted_by_a2":
        errors.append("connected or synthetic canonical record requires accepted_by_a2 handoff state")

    synthetic_flags = [
        metadata["record_kind"] == "synthetic_test",
        source["operating_scope"] == "synthetic_test",
        candidate["record_kind"] == "synthetic_test",
        bool(handoff["provenance"]["synthetic"]),
    ]
    if any(synthetic_flags) and not all(synthetic_flags):
        errors.append("synthetic/production classification is inconsistent across record and handoff")
    if enrichment_scope["field_catalogue_version"] != next(
        (item["field_catalogue_version"] for item in record["field_assessments"]),
        enrichment_scope["field_catalogue_version"],
    ):
        errors.append("enrichment_scope field_catalogue_version does not match field assessments")
    if any(item["field_catalogue_version"] != enrichment_scope["field_catalogue_version"] for item in record["field_assessments"]):
        errors.append("field assessments use inconsistent field_catalogue_version values")
    if enrichment_scope["source_register_version"] != governance["source_register_version"]:
        errors.append("enrichment_scope and governance source_register_version values must match")
    if governance["outreach_authorized"]:
        errors.append("A2 must not authorise outreach")

    # Revision-local IDs and graph references.
    entities = record["subject"]["entities"]
    entity_ids = [item["entity_id"] for item in entities]
    for duplicate in sorted(duplicate_values(entity_ids)):
        errors.append(f"duplicate entity_id {duplicate}")
    entity_types = {item["entity_id"]: item["entity_type"] for item in entities}

    relationships = record["subject"]["relationships"]
    relationship_ids = [item["relationship_id"] for item in relationships]
    for duplicate in sorted(duplicate_values(relationship_ids)):
        errors.append(f"duplicate relationship_id {duplicate}")
    relationship_id_set = set(relationship_ids)
    for relationship in relationships:
        for field in ("from_entity_id", "to_entity_id"):
            if relationship[field] not in entity_types:
                errors.append(f"relationship {relationship['relationship_id']} references unknown {field} {relationship[field]}")
    assessments = record["field_assessments"]
    assessment_ids = [item["field_assessment_id"] for item in assessments]
    for duplicate in sorted(duplicate_values(assessment_ids)):
        errors.append(f"duplicate field_assessment_id {duplicate}")
    assessment_id_set = set(assessment_ids)
    assessment_keys = {item["field_key"] for item in assessments}
    assessment_targets = [(item["scope"], item["entity_id"], item["field_key"]) for item in assessments]
    for duplicate in sorted(duplicate_values(assessment_targets), key=str):
        errors.append(f"duplicate field assessment target {duplicate}")

    observation_ids: list[str] = []
    a1_evidence_ids, a2_evidence_ids = all_references(record)
    permitted_evidence_ids = a1_evidence_ids | a2_evidence_ids

    for entity_item in entities:
        for match in entity_item["external_matches"]:
            check_reference_list(errors, f"external match {match['match_id']}", match["evidence_ids"], permitted_evidence_ids)

    evidence_records = record["evidence_registry"]
    if metadata["record_kind"] == "production" and evidence_records:
        if enrichment_scope["source_register_version"] is None:
            errors.append("production A2 evidence requires an approved source_register_version")
        if governance["source_terms_review_status"] not in {"approved", "conditional"}:
            errors.append("production A2 evidence requires an approved or conditional source policy state")
    raw_evidence_ids = [item["evidence_id"] for item in evidence_records]
    for duplicate in sorted(duplicate_values(raw_evidence_ids)):
        errors.append(f"duplicate evidence_id {duplicate}")
    for item in evidence_records:
        if item["namespace"] == "a1_reference" and item["source_id"] not in a1_evidence_ids:
            errors.append(f"A1 evidence reference {item['evidence_id']} does not identify evidence in the immutable handoff")
        if item["supersedes_evidence_id"] is not None and item["supersedes_evidence_id"] not in a2_evidence_ids:
            errors.append(f"evidence {item['evidence_id']} supersedes unknown A2 evidence {item['supersedes_evidence_id']}")
        if (item["provider_reference"] is not None or item["provider_cost"] is not None) and not governance["provider_use_authorized"]:
            errors.append(f"evidence {item['evidence_id']} claims provider use without authorisation")
        for assessment_id in item["supports_field_assessment_ids"]:
            if assessment_id not in assessment_id_set:
                errors.append(f"evidence {item['evidence_id']} supports unknown field assessment {assessment_id}")

    supersession = {
        item["evidence_id"]: item["supersedes_evidence_id"]
        for item in evidence_records
        if item["supersedes_evidence_id"] is not None
    }
    for evidence_key in supersession:
        visited: set[str] = set()
        current_key: str | None = evidence_key
        while current_key is not None and current_key in supersession:
            if current_key in visited:
                errors.append(f"evidence supersession cycle detected at {current_key}")
                break
            visited.add(current_key)
            current_key=supers...key]

    for relationship in relationships:
        check_reference_list(errors, f"relationship {relationship['relationship_id']}", relationship["evidence_ids"], permitted_evidence_ids)

    a2_evidence_by_id = {
        item["evidence_id"]: item for item in evidence_records if item["namespace"] == "a2"
    }

    def require_reverse_assessment_link(label: str, aid: str, evidence_ids: list[str]) -> None:
        for evidence_reference in evidence_ids:
            evidence_item = a2_evidence_by_id.get(evidence_reference)
            if evidence_item is not None and aid not in evidence_item["supports_field_assessment_ids"]:
                errors.append(f"{label} uses A2 evidence {evidence_reference} without reciprocal field-assessment support")
            if evidence_item is not None and evidence_item["source_policy_status"] in {"blocked", "needs_verification", "unavailable"}:
                errors.append(f"{label} uses A2 evidence {evidence_reference} that is not approved for evidentiary use")

    for assessment in assessments:
        aid = assessment["field_assessment_id"]
        scope = assessment["scope"]
        target_id = assessment["entity_id"]
        if scope == "record" and target_id is not None:
            errors.append(f"field assessment {aid} has record scope but a non-null entity_id")
        elif scope in {"person", "organisation"}:
            if target_id not in entity_types:
                errors.append(f"field assessment {aid} references unknown entity {target_id}")
            elif entity_types[target_id] != scope:
                errors.append(f"field assessment {aid} scope does not match entity type")
        elif scope == "relationship" and target_id not in relationship_id_set:
            errors.append(f"field assessment {aid} references unknown relationship {target_id}")

        baseline = assessment["baseline"]
        if baseline:
            check_reference_list(errors, f"field assessment {aid} baseline", baseline["evidence_ids"], permitted_evidence_ids)
            require_reverse_assessment_link(f"field assessment {aid} baseline", aid, baseline["evidence_ids"])

        observations = assessment["observations"]
        observation_ids.extend(item["observation_id"] for item in observations)
        for observation in observations:
            check_reference_list(errors, f"observation {observation['observation_id']}", observation["evidence_ids"], permitted_evidence_ids)
            require_reverse_assessment_link(f"observation {observation['observation_id']}", aid, observation["evidence_ids"])
            if observation["verification_status"] == "verified" and not observation["evidence_ids"]:
                errors.append(f"verified observation {observation['observation_id']} requires evidence")

        proposal = assessment["proposed_resolution"]
        if proposal:
            check_reference_list(errors, f"field assessment {aid} proposal", proposal["evidence_ids"], permitted_evidence_ids)
            require_reverse_assessment_link(f"field assessment {aid} proposal", aid, proposal["evidence_ids"])
            if proposal["action"] in {"add", "update"}:
                if proposal["value"] is None and proposal["normalised_value"] is None:
                    errors.append(f"field assessment {aid} add/update proposal requires a value")
                if not proposal["evidence_ids"]:
                    errors.append(f"field assessment {aid} add/update proposal requires evidence")
            if proposal["action"] in {"retain", "no_change"} and baseline is None:
                errors.append(f"field assessment {aid} retain/no_change proposal requires a baseline")
            if proposal["action"] == "clear_request" and proposal["value"] is not None:
                errors.append(f"field assessment {aid} clear_request proposal must not contain a replacement value")
            if proposal["verification_status"] == "verified" and not proposal["evidence_ids"]:
                errors.append(f"verified proposal {aid} requires evidence")

        field_review = assessment["field_review"]
        application = assessment["application"]
        if field_review["decision"] == "approved" and proposal is None:
            errors.append(f"field assessment {aid} cannot approve a missing proposal")
        if application["status"] in ACTIVE_APPLICATION_STATES:
            if field_review["decision"] != "approved":
                errors.append(f"field assessment {aid} application requires approved field review")
            if review["record_decision"] != "approved":
                errors.append(f"field assessment {aid} application requires approved record review")
            if not governance["crm_write_authorized"]:
                errors.append(f"field assessment {aid} application requires crm_write_authorized")
        protected_status = proposal["protected_status"] if proposal else (baseline["protected_status"] if baseline else "unassessed")
        if baseline and baseline["protected_status"] in PROTECTED_STATES and proposal and proposal["protected_status"] == "not_protected":
            errors.append(f"field assessment {aid} cannot downgrade a protected baseline")
        if application["status"] in ACTIVE_APPLICATION_STATES and protected_status in PROTECTED_STATES and proposal and proposal["action"] in {"update", "clear_request"}:
            if field_review["decision"] != "approved" or governance["approval_matrix_version"] is None:
                errors.append(f"protected field assessment {aid} requires explicit approved review and approval matrix")
        if assessment["availability_status"] in {"not_checked", "unavailable", "not_found"} and observations:
            errors.append(f"field assessment {aid} cannot contain observations when availability is {assessment['availability_status']}")
        if assessment["presence_status"] == "known":
            values_present = bool(
                (baseline and (baseline["value"] is not None or baseline["normalised_value"] is not None))
                or any(item["raw_value"] is not None or item["normalised_value"] is not None for item in observations)
                or (proposal and (proposal["value"] is not None or proposal["normalised_value"] is not None))
            )
            if not values_present:
                errors.append(f"field assessment {aid} is known but contains no value")
        if proposal and proposal["action"] == "clear_request" and proposal["normalised_value"] is not None:
            errors.append(f"field assessment {aid} clear_request proposal must not contain a normalised replacement value")

    for duplicate in sorted(duplicate_values(observation_ids)):
        errors.append(f"duplicate observation_id {duplicate}")

    # Optional Field Catalogue enforcement. The catalogue remains an external configuration.
    if field_catalogue is not None:
        catalogue_version = field_catalogue.get("version")
        if enrichment_scope["field_catalogue_version"] != catalogue_version:
            errors.append("enrichment_scope field_catalogue_version does not match supplied Field Catalogue")
        catalogue_keys = [item.get("field_key") for item in field_catalogue.get("fields", [])]
        for duplicate in sorted(duplicate_values(catalogue_keys)):
            errors.append(f"duplicate Field Catalogue key {duplicate}")
        fields = {item["field_key"]: item for item in field_catalogue.get("fields", [])}
        segment = candidate.get("segment")
        for assessment in assessments:
            key = assessment["field_key"]
            if assessment["field_catalogue_version"] != catalogue_version:
                errors.append(f"field assessment {assessment['field_assessment_id']} catalogue version mismatch")
            if key not in fields:
                errors.append(f"field assessment {assessment['field_assessment_id']} uses unknown Field Catalogue key {key}")
            else:
                approved_type = fields[key].get("value_type")
                allowed_segments = fields[key].get("allowed_segments")
                if allowed_segments is not None and segment not in allowed_segments:
                    errors.append(f"field assessment {assessment['field_assessment_id']} is not allowed for segment {segment}")
                if assessment["value_type"] != approved_type:
                    errors.append(f"field assessment {assessment['field_assessment_id']} value_type does not match Field Catalogue")
                values_to_check: list[tuple[str, object]] = []
                if assessment["baseline"] is not None:
                    values_to_check.append(("baseline.normalised_value", assessment["baseline"]["normalised_value"]))
                values_to_check.extend(
                    (f"observations[{index}].normalised_value", observation["normalised_value"])
                    for index, observation in enumerate(assessment["observations"])
                )
                if assessment["proposed_resolution"] is not None:
                    values_to_check.append(("proposed_resolution.normalised_value", assessment["proposed_resolution"]["normalised_value"]))
                values_to_check.append(("field_review.corrected_value", assessment["field_review"]["corrected_value"]))
                for value_path, value in values_to_check:
                    if not value_matches_type(value, approved_type):
                        errors.append(f"field assessment {assessment['field_assessment_id']} {value_path} does not match Field Catalogue type {approved_type}")
        if enrichment_scope["mode"] == "default_minimum_package":
            expected_required = {
                key for key, definition in fields.items()
                if definition.get("priority_by_segment", definition.get("requirement_by_segment", {})).get(segment) == "required"
            }
            if set(record["data_quality"]["required_field_keys"]) != expected_required:
                errors.append("data_quality.required_field_keys does not match the Field Catalogue minimum package")

    quality = record["data_quality"]
    for name in ["required_field_keys", "missing_field_keys", "unverified_field_keys", "conflict_field_keys", "stale_field_keys", "invalid_field_keys"]:
        for key in quality[name]:
            if key not in assessment_keys:
                errors.append(f"data_quality.{name} references field key without an assessment: {key}")
    if not set(quality["missing_field_keys"]).issubset(set(quality["required_field_keys"])):
        errors.append("data_quality.missing_field_keys must be a subset of required_field_keys")
    assessments_by_key={item[...y"]: item for item in assessments}
    for key in quality["missing_field_keys"]:
        assessment = assessments_by_key.get(key)
        if assessment and assessment["presence_status"] == "known" and assessment["field_quality_status"] not in {"gap", "invalid", "error"}:
            errors.append(f"data_quality marks known usable field as missing: {key}")
    if quality["status"] == "review_ready" and any(
        quality[name] for name in ["missing_field_keys", "conflict_field_keys", "invalid_field_keys"]
    ):
        errors.append("data_quality review_ready cannot contain missing, conflict or invalid fields")
    if workflow["state"] != "initialised":
        for key in enrichment_scope["requested_field_keys"]:
            if key not in assessment_keys:
                errors.append(f"requested enrichment field has no assessment: {key}")

    checks = record["duplicate_and_eligibility"]["checks"]
    check_ids = [item["check_id"] for item in checks]
    for duplicate in sorted(duplicate_values(check_ids)):
        errors.append(f"duplicate eligibility check_id {duplicate}")
    duplicate_statuses = [item["status"] for item in checks if item["check_type"] == "duplicate"]
    if "confirmed_duplicate" in duplicate_statuses and record["duplicate_and_eligibility"]["a2_eligibility_status"] != "blocked":
        errors.append("confirmed duplicate requires blocked A2 eligibility")
    if "possible_match" in duplicate_statuses and record["duplicate_and_eligibility"]["a2_eligibility_status"] not in {"hold", "blocked"}:
        errors.append("possible duplicate requires hold or blocked A2 eligibility")
    if record["duplicate_and_eligibility"]["owner_routing_status"] == "approved_reassignment":
        if review["record_decision"] != "approved" or governance["approval_matrix_version"] is None:
            errors.append("approved owner reassignment requires approved record review and approval matrix")
    for check in checks:
        if check["status"] in {"not_checked", "unavailable"} and check["checked_at"] is not None:
            errors.append(f"eligibility check {check['check_id']} must not claim checked_at for {check['status']}")
        if check["status"] in {"no_match", "possible_match", "confirmed_duplicate"} and check["checked_at"] is None:
            errors.append(f"eligibility check {check['check_id']} requires checked_at for {check['status']}")

    # Requalification graph integrity.
    signals = record["requalification"]["signals"]
    signal_ids = [item["signal_id"] for item in signals]
    for duplicate in sorted(duplicate_values(signal_ids)):
        errors.append(f"duplicate requalification signal_id {duplicate}")
    signal_by_id = {item["signal_id"]: item for item in signals}
    for signal in signals:
        errors.extend(step2c_signal_errors(signal, a1_criteria))
        expected_pairs = [
            ("a2_record_id", metadata["a2_record_id"]),
            ("a1_candidate_id", candidate["candidate_id"]),
            ("a1_handoff_id", source["handoff_id"]),
            ("a1_candidate_snapshot_sha256", source["candidate_snapshot_sha256"]),
            ("audit_correlation_id", metadata["audit_correlation_id"]),
            ("synthetic", metadata["record_kind"] == "synthetic_test"),
        ]
        for field, expected in expected_pairs:
            if signal[field] != expected:
                errors.append(f"requalification signal {signal['signal_id']} {field} mismatch")
        if metadata["revision_number"] == 1 and signal["a2_record_revision_id"] != metadata["record_revision_id"]:
            errors.append(f"new requalification signal {signal['signal_id']} must identify its creation revision")
        check_reference_list(errors, f"requalification signal {signal['signal_id']} A1", signal["a1_evidence_ids"], a1_evidence_ids)
        check_reference_list(errors, f"requalification signal {signal['signal_id']} A2", signal["a2_evidence_ids"], a2_evidence_ids)
        for evidence_reference in signal["a2_evidence_ids"]:
            evidence_item = a2_evidence_by_id.get(evidence_reference)
            if evidence_item is not None and signal["signal_id"] not in evidence_item["supports_requalification_signal_ids"]:
                errors.append(f"requalification signal {signal['signal_id']} uses A2 evidence {evidence_reference} without reciprocal signal support")
            if evidence_item is not None and evidence_item["source_policy_status"] in {"blocked", "needs_verification", "unavailable"}:
                errors.append(f"requalification signal {signal['signal_id']} uses A2 evidence {evidence_reference} that is not approved for evidentiary use")
        for field_id in signal["field_assessment_ids"]:
            if field_id not in assessment_id_set:
                errors.append(f"requalification signal {signal['signal_id']} references unknown field assessment {field_id}")

    for item in evidence_records:
        for signal_id in item["supports_requalification_signal_ids"]:
            if signal_id not in signal_by_id:
                errors.append(f"evidence {item['evidence_id']} supports unknown requalification signal {signal_id}")

    returns = record["requalification"]["returns"]
    return_ids = [item["return_id"] for item in returns]
    for duplicate in sorted(duplicate_values(return_ids)):
        errors.append(f"duplicate requalification return_id {duplicate}")
    return_by_id = {item["return_id"]: item for item in returns}
    for returned in returns:
        errors.extend(step2c_return_errors(returned, a1_criteria))
        for field, expected in [
            ("a2_record_id", metadata["a2_record_id"]),
            ("a1_candidate_id", candidate["candidate_id"]),
            ("a1_handoff_id", source["handoff_id"]),
            ("a1_candidate_snapshot_sha256", source["candidate_snapshot_sha256"]),
            ("audit_correlation_id", metadata["audit_correlation_id"]),
            ("synthetic", metadata["record_kind"] == "synthetic_test"),
        ]:
            if returned[field] != expected:
                errors.append(f"requalification return {returned['return_id']} {field} mismatch")
        if metadata["revision_number"] == 1 and returned["a2_record_revision_id"] != metadata["record_revision_id"]:
            errors.append(f"new requalification return {returned['return_id']} must identify its creation revision")
        for snapshot in returned["signal_snapshots"]:
            signal_id = snapshot["signal_id"]
            if signal_id not in signal_by_id:
                errors.append(f"requalification return {returned['return_id']} contains unknown signal {signal_id}")
            else:
                immutable_snapshot = {key: value for key, value in snapshot.items() if key not in {"status", "review"}}
                immutable_signal = {key: value for key, value in signal_by_id[signal_id].items() if key not in {"status", "review"}}
                if immutable_snapshot != immutable_signal:
                    errors.append(f"requalification return {returned['return_id']} signal snapshot differs from canonical signal {signal_id}")
        if returned["signal_snapshot_sha256"] != canonical_hash(returned["signal_snapshots"]):
            errors.append(f"requalification return {returned['return_id']} signal snapshot hash mismatch")

    revisions = record["requalification"]["score_revision_references"]
    revision_ids = [item["score_revision_id"] for item in revisions]
    for duplicate in sorted(duplicate_values(revision_ids)):
        errors.append(f"duplicate A1 score_revision_id {duplicate}")
    revision_by_id = {item["score_revision_id"]: item for item in revisions}
    for revision in revisions:
        errors.extend(step2c_revision_errors(revision, a1_criteria, a1_weights, a1_scoring_config))
        if revision["a1_candidate_id"] != candidate["candidate_id"]:
            errors.append(f"score revision {revision['score_revision_id']} candidate mismatch")
        if revision["source_requalification_return_id"] not in return_by_id:
            errors.append(f"score revision {revision['score_revision_id']} references unknown requalification return")
        else:
            source_return = return_by_id[revision["source_requalification_return_id"]]
            if source_return["status"] != "accepted_by_a1":
                errors.append(f"score revision {revision['score_revision_id']} requires an accepted_by_a1 return")
            returned_signal_ids = {item["signal_id"] for item in source_return["signal_snapshots"]}
            if not set(revision["source_signal_ids"]).issubset(returned_signal_ids):
                errors.append(f"score revision {revision['score_revision_id']} uses signals outside its referenced return")
        check_reference_list(errors, f"score revision {revision['score_revision_id']}", revision["validated_evidence_ids"], permitted_evidence_ids)
        for signal_id in revision["source_signal_ids"]:
            if signal_id not in signal_by_id:
                errors.append(f"score revision {revision['score_revision_id']} references unknown signal {signal_id}")
            elif signal_by_id[signal_id]["status"] not in A1_RESULT_SIGNAL_STATES:
                errors.append(f"score revision {revision['score_revision_id']} uses signal not accepted by A1")
        if revision["audit_correlation_id"] != metadata["audit_correlation_id"]:
            errors.append(f"score revision {revision['score_revision_id']} audit correlation mismatch")
        if revision["synthetic"] != (metadata["record_kind"] == "synthetic_test"):
            errors.append(f"score revision {revision['score_revision_id']} synthetic marker mismatch")
        prior_revision_id = revision["prior_revision_id"]
        if prior_revision_id is None:
            if revision["prior_scoring"] != candidate["scoring"]:
                errors.append(f"score revision {revision['score_revision_id']} prior_scoring does not match immutable A1 handoff scoring")
        elif prior_revision_id == revision["score_revision_id"]:
            errors.append(f"score revision {revision['score_revision_id']} cannot reference itself as prior revision")
        elif prior_revision_id not in revision_by_id:
            errors.append(f"score revision {revision['score_revision_id']} references unavailable prior score revision")
        elif revision["prior_scoring"] != revision_by_id[prior_revision_id]["revised_scoring"]:
            errors.append(f"score revision {revision['score_revision_id']} prior_scoring does not match prior revised_scoring")

    if system_refs["requalification_return_id"] is not None and system_refs["requalification_return_id"] not in return_by_id:
        errors.append("system_references.requalification_return_id does not exist in requalification returns")
    if system_refs["a1_score_revision_id"] is not None and system_refs["a1_score_revision_id"] not in set(revision_ids):
        errors.append("system_references.a1_score_revision_id does not exist in score revision references")

    # Workflow, review, action and no-integration ceilings.
    transitions = load_json(STATE_MODEL_PATH)["transition_models"]["workflow_state"]
    if metadata["revision_number"] == 1:
        if workflow["previous_state"] is not None:
            errors.append("first revision workflow.previous_state must be null")
        if workflow["state"] != "initialised":
            errors.append("first revision workflow state must be initialised")
    elif workflow["previous_state"] is None:
        errors.append("later revision workflow.previous_state is required")
    elif workflow["state"] not in transitions.get(workflow["previous_state"], []):
        errors.append(f"invalid workflow transition {workflow['previous_state']} -> {workflow['state']}")

    expected_review_by_state = {
        "review_required": "pending",
        "record_approved": "approved",
        "changes_requested": "needs_changes",
        "held": "held",
        "record_rejected": "rejected",
    }
    expected_review = expected_review_by_state.get(workflow["state"])
    if expected_review and review["record_decision"] != expected_review:
        errors.append(f"workflow state {workflow['state']} requires record review decision {expected_review}")
    completed_field_decisions = bool(assessments) and all(
        assessment["field_review"]["decision"] in {"approved", "rejected", "not_required"}
        for assessment in assessments
    )
    if review["required_field_decisions_complete"] and not completed_field_decisions:
        errors.append("required_field_decisions_complete is true while field reviews remain unresolved")
    if workflow["state"] == "blocked" and review["record_decision"] != "blocked":
        errors.append("workflow state blocked requires record review decision blocked")

    handoff_constraints = handoff["constraints"]
    if governance["crm_write_authorized"] and not handoff_constraints["crm_write_authorized"]:
        errors.append("canonical CRM-write authority cannot exceed immutable handoff authority")
    if governance["provider_use_authorized"] and not handoff_constraints["paid_provider_authorized"]:
        errors.append("canonical provider authority cannot exceed immutable handoff authority")

    external_action_refs = {
        event["external_action"]["external_reference"]: event
        for event in record["audit_and_consumption"]["events"]
        if event["external_action"] is not None and event["external_action"]["external_reference"] is not None
    }
    for assessment in assessments:
        application = assessment["application"]
        if application["status"] in {"applied", "reconciled"}:
            reference = application["external_action_reference"]
            event = external_action_refs.get(reference)
            if event is None or event["external_action"]["state"] != "succeeded":
                errors.append(f"field assessment {assessment['field_assessment_id']} application lacks a matching successful audit action")
            if application["status"] == "reconciled" and (event is None or event["event_type"] != "external_action_reconciled"):
                errors.append(f"field assessment {assessment['field_assessment_id']} reconciliation lacks a read-back audit event")

    scope = source["operating_scope"]
    if scope == "synthetic_test":
        if governance["crm_write_authorized"] or governance["provider_use_authorized"]:
            errors.append("synthetic_test record cannot authorise CRM write or provider use")
        synthetic_external_fields = [
            "twenty_record_id", "hubspot_contact_id", "hubspot_company_id", "hubspot_deal_ids",
            "hubspot_proposed_patch_id", "hubspot_sync_id", "n8n_work_item_id", "n8n_execution_id",
            "provider_request_ids", "a3_handoff_id", "a14_handoff_id",
        ]
        if any(system_refs[field] is not None for field in synthetic_external_fields):
            errors.append("synthetic_test record cannot claim real external-system references")
        for assessment in assessments:
            if assessment["application"]["status"] in ACTIVE_APPLICATION_STATES:
                errors.append(f"synthetic_test field assessment {assessment['field_assessment_id']} cannot apply externally")
    if scope == "manual_no_integration_pilot":
        if workflow["state"] in SYNC_STATES:
            errors.append("manual_no_integration_pilot record cannot enter a sync state")
        if record["requalification"]["score_revision_references"]:
            errors.append("manual_no_integration_pilot record cannot contain an A1 score revision result")
        for signal in signals:
            if signal["status"] in {"sent_to_a1", "accepted_by_a1", "rejected_by_a1", "rescored"}:
                errors.append(f"manual_no_integration_pilot signal {signal['signal_id']} exceeds the approved return ceiling")
        for returned in returns:
            if returned["status"] != "prepared":
                errors.append(f"manual_no_integration_pilot return {returned['return_id']} must remain prepared")
        for assessment in assessments:
            if assessment["application"]["status"] in ACTIVE_APPLICATION_STATES:
                errors.append(f"manual_no_integration_pilot field assessment {assessment['field_assessment_id']} cannot apply externally")
        for item in evidence_records:
            if item["provider_reference"] is not None or item["provider_cost"] is not None:
                errors.append(f"manual_no_integration_pilot evidence {item['evidence_id']} cannot claim provider execution")
        if record["audit_and_consumption"]["total_usage"]["provider_calls"] != 0:
            errors.append("manual_no_integration_pilot provider_calls must be zero")
        for event in record["audit_and_consumption"]["events"]:
            action = event["external_action"]
            if action is not None and action["state"] in {"pending", "succeeded", "failed"}:
                errors.append(f"manual_no_integration_pilot audit event {event['event_id']} cannot claim an external action")

    # Audit uniqueness and conservative usage reconciliation.
    events = record["audit_and_consumption"]["events"]
    event_ids = [item["event_id"] for item in events]
    for duplicate in sorted(duplicate_values(event_ids)):
        errors.append(f"duplicate audit event_id {duplicate}")
    for event in events:
        usage = event["usage"]
        if usage is not None and usage["total_tokens"] is not None and usage["input_tokens"] is not None and usage["output_tokens"] is not None:
            if usage["total_tokens"] != usage["input_tokens"] + usage["output_tokens"]:
                errors.append(f"audit event {event['event_id']} total_tokens does not equal input_tokens plus output_tokens")
        action = event["external_action"]
        if action and action["state"] == "succeeded":
            if action["external_reference"] is None:
                errors.append(f"successful external action {event['event_id']} requires an external reference")
            if action["approval_reference"] is None:
                errors.append(f"successful external action {event['event_id']} requires an approval reference")

    totals = record["audit_and_consumption"]["total_usage"]
    usage_events = [event["usage"] for event in events if event["usage"] is not None]
    for field in ["input_tokens", "output_tokens", "total_tokens", "api_calls", "credits", "cost_amount"]:
        if totals[field] is not None and all(item[field] is not None for item in usage_events):
            expected_total = sum(item[field] for item in usage_events)
            if totals[field] != expected_total:
                errors.append(f"audit total_usage.{field} does not equal event usage total")

    return errors


def check_previous_revision(record: dict, previous: dict) -> list[str]:
    errors: list[str] = []
    current_meta = record["record_metadata"]
    prior_meta = previous["record_metadata"]
    if current_meta["a2_record_id"] != prior_meta["a2_record_id"]:
        errors.append("current and previous revisions must share a2_record_id")
    if current_meta["record_revision_id"] == prior_meta["record_revision_id"]:
        errors.append("record_revision_id must be new for every revision")
    if current_meta["revision_number"] != prior_meta["revision_number"] + 1:
        errors.append("revision_number must increment by exactly one")
    if current_meta["supersedes_revision_id"] != prior_meta["record_revision_id"]:
        errors.append("supersedes_revision_id must equal the previous record_revision_id")
    if record["source_handoff"] != previous["source_handoff"]:
        errors.append("source_handoff changed across revisions")
    if record["workflow"]["previous_state"] != previous["workflow"]["state"]:
        errors.append("workflow.previous_state does not match the previous revision state")

    for collection_path, id_field in [
        (("evidence_registry",), "evidence_id"),
        (("audit_and_consumption", "events"), "event_id"),
    ]:
        current_collection: Any = record
        prior_collection: Any = previous
        for part in collection_path:
            current_collection = current_collection[part]
            prior_collection = prior_collection[part]
        current_by_id = {item[id_field]: item for item in current_collection}
        for item in prior_collection:
            item_id = item[id_field]
            if item_id not in current_by_id:
                errors.append(f"append-only collection {'/'.join(collection_path)} dropped {item_id}")
            elif current_by_id[item_id] != item:
                errors.append(f"append-only collection {'/'.join(collection_path)} mutated {item_id}")

    def lifecycle_check(
        collection_name: str,
        id_field: str,
        status_field: str,
        mutable_fields: set[str],
        transitions: dict[str, set[str]],
    ) -> None:
        prior_items = {item[id_field]: item for item in previous["requalification"][collection_name]}
        current_items = {item[id_field]: item for item in record["requalification"][collection_name]}
        for item_id, prior_item in prior_items.items():
            if item_id not in current_items:
                errors.append(f"requalification {collection_name} history dropped {item_id}")
                continue
            current_item = current_items[item_id]
            prior_stable = {key: value for key, value in prior_item.items() if key not in mutable_fields}
            current_stable = {key: value for key, value in current_item.items() if key not in mutable_fields}
            if prior_stable != current_stable:
                errors.append(f"requalification {collection_name} immutable payload mutated {item_id}")
            prior_status = prior_item[status_field]
            current_status = current_item[status_field]
            if current_status != prior_status and current_status not in transitions.get(prior_status, set()):
                errors.append(f"invalid {collection_name} lifecycle transition {prior_status} -> {current_status} for {item_id}")
            for decision_field in ("review", "approval", "a1_receipt"):
                if decision_field in prior_item and prior_item[decision_field] is not None:
                    if current_item.get(decision_field) != prior_item[decision_field]:
                        errors.append(f"requalification {collection_name} immutable {decision_field} mutated {item_id}")
            if collection_name == "returns":
                prior_delivery = prior_item["delivery"]
                current_delivery = current_item["delivery"]
                if current_delivery["attempt_count"] < prior_delivery["attempt_count"]:
                    errors.append(f"requalification return delivery attempt_count decreased for {item_id}")
                if prior_delivery["external_event_reference"] is not None and current_delivery["external_event_reference"] != prior_delivery["external_event_reference"]:
                    errors.append(f"requalification return external_event_reference mutated for {item_id}")

        new_ids = set(current_items) - set(prior_items)
        for item_id in new_ids:
            item = current_items[item_id]
            creation_revision = item.get("a2_record_revision_id")
            if creation_revision is not None and creation_revision != current_meta["record_revision_id"]:
                errors.append(f"new requalification {collection_name} item {item_id} must identify the current creation revision")

    lifecycle_check(
        "signals",
        "signal_id",
        "status",
        {"status", "review"},
        {
            "draft": {"pending_review", "error"},
            "pending_review": {"approved_for_return", "rejected", "error"},
            "approved_for_return": {"sent_to_a1", "error"},
            "sent_to_a1": {"accepted_by_a1", "rejected_by_a1", "error"},
            "accepted_by_a1": {"rescored", "error"},
            "rejected": set(),
            "rejected_by_a1": set(),
            "rescored": set(),
            "error": set(),
        },
    )
    lifecycle_check(
        "returns",
        "return_id",
        "status",
        {"status", "approval", "delivery", "a1_receipt"},
        {
            "prepared": {"delivered", "delivery_failed", "error"},
            "delivered": {"accepted_by_a1", "rejected_by_a1", "delivery_failed", "error"},
            "delivery_failed": {"delivered", "error"},
            "accepted_by_a1": set(),
            "rejected_by_a1": set(),
            "error": set(),
        },
    )
    lifecycle_check(
        "score_revision_references",
        "score_revision_id",
        "revision_status",
        {"revision_status", "review"},
        {
            "proposed_by_a1": {"approved", "rejected", "error"},
            "approved": {"superseded"},
            "rejected": set(),
            "superseded": set(),
            "error": set(),
        },
    )

    prior_assessments = {item["field_assessment_id"]: item for item in previous["field_assessments"]}
    current_assessments = {item["field_assessment_id"]: item for item in record["field_assessments"]}
    for assessment_id, prior_assessment in prior_assessments.items():
        if assessment_id not in current_assessments:
            errors.append(f"field assessment history dropped {assessment_id}")
            continue
        prior_observations = {item["observation_id"]: item for item in prior_assessment["observations"]}
        current_observations = {item["observation_id"]: item for item in current_assessments[assessment_id]["observations"]}
        for observation_id, observation in prior_observations.items():
            if observation_id not in current_observations:
                errors.append(f"observation history dropped {observation_id}")
            elif current_observations[observation_id] != observation:
                errors.append(f"observation history mutated {observation_id}")
    return errors


def validate(record: dict, previous: dict | None = None, field_catalogue: dict | None = None) -> dict:
    schema = load_json(SCHEMA_PATH)
    errors = schema_errors(record, schema, make_registry(schema))
    if not errors:
        errors.extend(check_current_record(record, field_catalogue))
        if record["record_metadata"]["revision_number"] > 1 and previous is None:
            errors.append("later revision requires the previous record for lineage validation")
        if previous is not None:
            prior_schema_errors = schema_errors(previous, schema, make_registry(schema))
            if prior_schema_errors:
                errors.extend(f"previous:{item}" for item in prior_schema_errors)
            else:
                # The prior revision may have used another catalogue version; its
                # policy receipt is validated separately from the current run.
                errors.extend(f"previous:{item}" for item in check_current_record(previous, None))
                errors.extend(check_previous_revision(record, previous))
    return {
        "schema_version": schema["properties"]["record_metadata"]["properties"]["schema_version"]["const"],
        "record_id": record.get("record_metadata", {}).get("a2_record_id"),
        "record_revision_id": record.get("record_metadata", {}).get("record_revision_id"),
        "previous_revision_checked": previous is not None,
        "field_catalogue_checked": field_catalogue is not None,
        "valid": not errors,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--previous-record", type=Path)
    parser.add_argument("--field-catalogue", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    record = load_json(args.record)
    previous = load_json(args.previous_record) if args.previous_record else None
    field_catalogue = load_json(args.field_catalogue) if args.field_catalogue else None
    result = validate(record, previous=previous, field_catalogue=field_catalogue)
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
