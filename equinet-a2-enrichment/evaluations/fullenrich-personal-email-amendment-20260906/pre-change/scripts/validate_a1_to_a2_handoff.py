#!/usr/bin/env python3
"""Validate Equinet A1-to-A2 handoff envelopes and cross-field invariants."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

PROFILE_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = PROFILE_ROOT / "foundations" / "contracts"
DEFAULT_SCHEMA = CONTRACTS / "a1-to-a2-handoff.schema.json"
A1_SCHEMA_PATH = CONTRACTS / "dependencies" / "a1-prospect-candidate.schema.json"
A1_VALIDATOR_PATH = CONTRACTS / "dependencies" / "a1_validate_candidate.py"

GATE_IDS = {
    "candidate_schema",
    "human_approval",
    "recommendation",
    "exclusion",
    "minimum_data",
    "identity_quality",
    "duplicate_batch",
    "duplicate_exclusion_file",
    "source_policy",
    "scoring_state",
    "audit_identity",
    "scope_permissions",
    "hubspot_duplicate",
    "hubspot_eligibility",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def candidate_sha256(candidate: dict) -> str:
    return hashlib.sha256(canonical_bytes(candidate)).hexdigest()


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_a1_cross_validator():
    spec = importlib.util.spec_from_file_location("pinned_a1_validate_candidate", A1_VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load pinned A1 validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.cross_reference_errors


def schema_errors(document: dict, schema: dict, a1_schema: dict) -> list[str]:
    Draft202012Validator.check_schema(a1_schema)
    Draft202012Validator.check_schema(schema)
    registry = Registry().with_resource(
        a1_schema["$id"],
        Resource.from_contents(a1_schema),
    )
    validator = Draft202012Validator(
        schema,
        registry=registry,
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    rendered: list[str] = []
    for error in errors:
        path = "/" + "/".join(str(item) for item in error.absolute_path)
        rendered.append(f"schema:{path}: {error.message}")
    return rendered


def expected_gate_statuses(document: dict, candidate_errors: list[str]) -> dict[str, str]:
    candidate = document.get("candidate_snapshot", {})
    workflow = candidate.get("workflow", {})
    qualification = candidate.get("qualification", {})
    quality = candidate.get("data_quality", {})
    duplicates = candidate.get("duplicate_check", {})
    integrations = document.get("integration_availability", {})
    constraints = document.get("constraints", {})
    scope = document.get("operating_scope")

    expected: dict[str, str] = {}
    expected["candidate_schema"] = "fail" if candidate_errors else "pass"

    approved = (
        workflow.get("stage") == "approved_for_a2"
        and workflow.get("review_decision") == "approved"
        and workflow.get("reviewer") is not None
        and workflow.get("decision_at") is not None
    )
    expected["human_approval"] = "pass" if approved else "fail"
    expected["recommendation"] = (
        "pass" if candidate.get("recommendation", {}).get("next_action") == "pass_to_a2" else "fail"
    )

    exclusion = qualification.get("exclusion_status")
    expected["exclusion"] = "fail" if exclusion == "excluded" else ("needs_review" if exclusion in {"needs_review", "not_checked"} else "pass")

    minimum = qualification.get("minimum_data_status")
    expected["minimum_data"] = "fail" if minimum == "fail" else ("needs_review" if minimum == "needs_review" else "pass")

    quality_status = quality.get("validation_status")
    expected["identity_quality"] = "fail" if quality_status == "invalid" else ("needs_review" if quality_status == "conflict" else "pass")

    for gate_id, check_name in [
        ("duplicate_batch", "batch"),
        ("duplicate_exclusion_file", "provided_exclusion_file"),
    ]:
        duplicate_status = duplicates.get(check_name, {}).get("status")
        if duplicate_status == "confirmed_duplicate":
            expected[gate_id] = "fail"
        elif duplicate_status in {"possible_match", "error"}:
            expected[gate_id] = "needs_review"
        elif duplicate_status in {"unavailable", "not_checked"}:
            expected[gate_id] = "unavailable"
        else:
            expected[gate_id] = "pass"

    blocked_source = any(
        item.get("source_policy_status") == "blocked"
        for item in candidate.get("source_evidence", [])
        if isinstance(item, dict)
    )
    expected["source_policy"] = "fail" if blocked_source else "pass"
    expected["scoring_state"] = "pass" if candidate.get("scoring", {}).get("status") == "scored" else "fail"
    expected["audit_identity"] = "pass" if candidate.get("provenance", {}).get("audit_correlation_id") else "fail"

    prohibited_scope = (
        constraints.get("a1_score_mutation_authorized") is not False
        or constraints.get("outreach_authorized") is not False
        or (scope in {"synthetic_test", "manual_no_integration_pilot"} and constraints.get("crm_write_authorized") is not False)
        or (scope in {"synthetic_test", "manual_no_integration_pilot"} and constraints.get("downstream_delivery_authorized") is not False)
        or (scope in {"synthetic_test", "manual_no_integration_pilot"} and constraints.get("paid_provider_authorized") is not False)
    )
    expected["scope_permissions"] = "fail" if prohibited_scope else "pass"

    hubspot_status = candidate.get("duplicate_check", {}).get("hubspot", {}).get("status")
    if hubspot_status == "confirmed_duplicate":
        expected["hubspot_duplicate"] = "fail"
    elif hubspot_status in {"possible_match", "error"}:
        expected["hubspot_duplicate"] = "needs_review"
    elif hubspot_status in {"unavailable", "not_checked", None}:
        expected["hubspot_duplicate"] = "unavailable"
    else:
        expected["hubspot_duplicate"] = "pass"

    if scope in {"integrated_pilot", "production"}:
        expected["hubspot_eligibility"] = "pass" if integrations.get("hubspot_read") == "connected" else "unavailable"
    else:
        expected["hubspot_eligibility"] = "unavailable"

    return expected


def expected_eligibility(scope: str, statuses: dict[str, str]) -> str:
    if any(status == "fail" for status in statuses.values()):
        return "blocked"

    required_core = {
        "candidate_schema",
        "human_approval",
        "recommendation",
        "exclusion",
        "minimum_data",
        "identity_quality",
        "duplicate_batch",
        "source_policy",
        "scoring_state",
        "audit_identity",
        "scope_permissions",
    }
    if any(statuses[gate] in {"needs_review", "unavailable"} for gate in required_core):
        return "hold"

    if statuses["duplicate_exclusion_file"] == "needs_review":
        return "hold"

    if scope in {"integrated_pilot", "production"}:
        if statuses["hubspot_duplicate"] in {"needs_review", "unavailable"}:
            return "hold"
        if statuses["hubspot_eligibility"] in {"needs_review", "unavailable"}:
            return "hold"

    return "eligible"


def cross_field_errors(document: dict, a1_schema: dict) -> list[str]:
    errors: list[str] = []
    candidate = document.get("candidate_snapshot", {})
    a1_schema_validator = Draft202012Validator(a1_schema, format_checker=FormatChecker())
    candidate_schema_errors = list(a1_schema_validator.iter_errors(candidate))
    a1_cross = load_a1_cross_validator()
    candidate_custom_errors = a1_cross(candidate) if isinstance(candidate, dict) else ["candidate root must be an object"]
    candidate_errors = [error.message for error in candidate_schema_errors] + list(candidate_custom_errors)
    if candidate_errors:
        errors.append("A1 candidate validation failed: " + " | ".join(candidate_errors))

    handoff_id = document.get("handoff_id")
    candidate_ref = candidate.get("system_references", {}).get("a2_handoff_id")
    if candidate_ref != handoff_id:
        errors.append("candidate system_references.a2_handoff_id must equal handoff_id")

    actual_hash = candidate_sha256(candidate)
    declared_hash = document.get("snapshot_integrity", {}).get("candidate_snapshot_sha256")
    if declared_hash != actual_hash:
        errors.append(f"snapshot hash mismatch: declared {declared_hash!r}, calculated {actual_hash!r}")

    workflow = candidate.get("workflow", {})
    approval = document.get("approval_event", {})
    trigger = document.get("trigger_event", {})
    if workflow.get("stage") != "approved_for_a2":
        errors.append("candidate workflow.stage must be approved_for_a2")
    if workflow.get("review_decision") != "approved":
        errors.append("candidate workflow.review_decision must be approved")
    if workflow.get("reviewer") != approval.get("reviewer"):
        errors.append("approval_event.reviewer must match candidate workflow.reviewer")
    if workflow.get("decision_at") != approval.get("decision_at"):
        errors.append("approval_event.decision_at must match candidate workflow.decision_at")
    if candidate.get("recommendation", {}).get("next_action") != "pass_to_a2":
        errors.append("candidate recommendation.next_action must be pass_to_a2")

    try:
        if parse_datetime(trigger.get("occurred_at")) < parse_datetime(approval.get("decision_at")):
            errors.append("trigger_event.occurred_at cannot precede approval_event.decision_at")
        if parse_datetime(document.get("created_at")) < parse_datetime(trigger.get("occurred_at")):
            errors.append("handoff created_at cannot precede trigger_event.occurred_at")
    except (TypeError, ValueError):
        pass

    gates = document.get("eligibility", {}).get("gates", [])
    gate_ids = [gate.get("gate_id") for gate in gates if isinstance(gate, dict)]
    if len(gate_ids) != len(set(gate_ids)):
        errors.append("eligibility gate IDs must be unique")
    missing = sorted(GATE_IDS - set(gate_ids))
    extra = sorted(set(gate_ids) - GATE_IDS)
    if missing:
        errors.append("missing eligibility gates: " + ", ".join(missing))
    if extra:
        errors.append("unknown eligibility gates: " + ", ".join(extra))

    expected = expected_gate_statuses(document, candidate_errors)
    declared = {gate.get("gate_id"): gate.get("status") for gate in gates if isinstance(gate, dict)}
    for gate_id, expected_status in expected.items():
        if declared.get(gate_id) != expected_status:
            errors.append(f"{gate_id} gate must be {expected_status}; got {declared.get(gate_id)!r}")

    scope = document.get("operating_scope")
    calculated_eligibility = expected_eligibility(scope, expected)
    declared_eligibility = document.get("eligibility", {}).get("status")
    if declared_eligibility != calculated_eligibility:
        errors.append(
            f"eligibility.status must be {calculated_eligibility}; got {declared_eligibility!r}"
        )

    state = document.get("delivery_state")
    delivery = document.get("delivery", {})
    receipt = document.get("a2_receipt")
    if scope == "manual_no_integration_pilot" and state not in {"prepared", "ready_for_delivery"}:
        errors.append("manual_no_integration_pilot cannot progress beyond ready_for_delivery")
    if state in {"delivered", "accepted_by_a2", "rejected_by_a2"}:
        if not delivery.get("external_event_reference"):
            errors.append(f"delivery_state {state} requires an external_event_reference")
        if delivery.get("attempt_count", 0) < 1 or not delivery.get("last_attempt_at"):
            errors.append(f"delivery_state {state} requires a delivery attempt and timestamp")
    if state in {"accepted_by_a2", "rejected_by_a2"}:
        if not isinstance(receipt, dict):
            errors.append(f"delivery_state {state} requires an A2 receipt")
        else:
            if receipt.get("handoff_id") != handoff_id:
                errors.append("A2 receipt handoff_id must equal handoff_id")
            if receipt.get("candidate_snapshot_sha256") != actual_hash:
                errors.append("A2 receipt snapshot hash must equal the calculated candidate snapshot hash")
    elif receipt is not None:
        errors.append(f"delivery_state {state} requires a2_receipt to be null")

    constraints = document.get("constraints", {})
    if any(
        constraints.get(field) is True
        for field in ["crm_write_authorized", "downstream_delivery_authorized", "paid_provider_authorized"]
    ) and not constraints.get("external_action_approval_reference"):
        errors.append("external action permission requires external_action_approval_reference")

    integration_states = document.get("integration_availability", {})
    if scope == "manual_no_integration_pilot" and "connected" in integration_states.values():
        errors.append("manual_no_integration_pilot cannot declare an integration connected")

    candidate_synthetic = candidate.get("provenance", {}).get("synthetic") is True
    envelope_synthetic = document.get("provenance", {}).get("synthetic") is True
    if scope == "synthetic_test":
        if candidate.get("record_kind") != "synthetic_test" or not candidate_synthetic or not envelope_synthetic:
            errors.append("synthetic_test scope requires a synthetic A1 candidate and synthetic envelope provenance")
    elif candidate.get("record_kind") != "production" or candidate_synthetic or envelope_synthetic:
        errors.append("non-synthetic operating scopes require a production A1 candidate and non-synthetic provenance")

    audit_id = candidate.get("provenance", {}).get("audit_correlation_id")
    if document.get("provenance", {}).get("audit_correlation_id") != audit_id:
        errors.append("handoff audit_correlation_id must equal the A1 candidate audit_correlation_id")

    return errors


def validate_document(path: Path, schema_path: Path = DEFAULT_SCHEMA) -> dict:
    schema = load_json(schema_path)
    a1_schema = load_json(A1_SCHEMA_PATH)
    document = load_json(path)
    errors = schema_errors(document, schema, a1_schema)
    errors.extend(cross_field_errors(document, a1_schema))
    return {
        "path": str(path),
        "valid": not errors,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("handoff", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    result = validate_document(args.handoff, args.schema)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
