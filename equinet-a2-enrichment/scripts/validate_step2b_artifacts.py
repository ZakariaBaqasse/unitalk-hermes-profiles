#!/usr/bin/env python3
"""Validate Step 2B field dictionary and state-model artifacts with negative regressions."""

from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = PROFILE_ROOT / "foundations" / "contracts"
FIELD_DICTIONARY = CONTRACTS / "a2-field-dictionary-0.1.0.csv"
STATE_MODEL = CONTRACTS / "a2-state-model-0.1.0.json"
FIELD_DOCUMENT = PROFILE_ROOT / "foundations" / "A2-FIELD-DICTIONARY.md"
STATE_DOCUMENT = PROFILE_ROOT / "foundations" / "A2-STATE-MODEL.md"
OUTPUT = PROFILE_ROOT / "evaluations" / "step2b" / "technical-validation.json"

EXPECTED_SECTIONS = {
    "record_metadata",
    "source_handoff",
    "subject",
    "enrichment_scope",
    "field_assessments",
    "evidence_registry",
    "data_quality",
    "duplicate_and_eligibility",
    "requalification",
    "review",
    "workflow",
    "system_references",
    "governance",
    "audit_and_consumption",
}
ALLOWED_REQUIRED = {"yes", "no", "conditional"}
ALLOWED_NULLABLE = {"yes", "no"}
ALLOWED_MUTABILITY = {
    "immutable_input",
    "immutable_revision",
    "append_only_history",
    "deterministic_derived",
    "versioned",
    "human_controlled_decision",
    "connector_controlled_reference",
    "external_authoritative_mirror",
    "controlled_transition",
}
REQUIRED_FIELD_PATHS = {
    "record_metadata.schema_version",
    "record_metadata.a2_record_id",
    "record_metadata.record_revision_id",
    "source_handoff.handoff_id",
    "source_handoff.handoff_snapshot",
    "subject.entities",
    "field_assessments",
    "field_assessments[].baseline",
    "field_assessments[].observations",
    "field_assessments[].proposed_resolution",
    "field_assessments[].field_review.decision",
    "field_assessments[].application.status",
    "evidence_registry",
    "data_quality.status",
    "duplicate_and_eligibility.a2_eligibility_status",
    "requalification.signals",
    "requalification.returns",
    "requalification.score_revision_references",
    "review.record_decision",
    "workflow.state",
    "system_references.hubspot_contact_id",
    "governance.outreach_authorized",
    "governance.crm_write_authorized",
    "audit_and_consumption.events",
}
REQUIRED_CROSS_RULE_PHRASES = [
    "unknown means no reliable value is known",
    "not_checked means no attempt occurred",
    "field review approval does not imply application",
    "workflow_dependency_status must be verified_no_side_effect or verified_managed_side_effect",
    "manual_no_integration_pilot records cannot enter ready_for_sync",
    "A2 may create requalification signals but cannot set score_revision_status",
    "null external-system IDs do not imply no external record exists",
    "owner routing defaults to needs_owner_review",
]


def read_rows() -> list[dict]:
    with FIELD_DICTIONARY.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_data(rows: list[dict], model: dict) -> list[str]:
    errors: list[str] = []
    paths = [row.get("field_path", "") for row in rows]
    sections = {row.get("section", "") for row in rows}

    if len(paths) != len(set(paths)):
        errors.append("duplicate field_path values are not allowed")
    if sections != EXPECTED_SECTIONS:
        errors.append(f"section set mismatch: missing={sorted(EXPECTED_SECTIONS-sections)}, extra={sorted(sections-EXPECTED_SECTIONS)}")
    missing_paths = sorted(REQUIRED_FIELD_PATHS - set(paths))
    if missing_paths:
        errors.append("missing required field paths: " + ", ".join(missing_paths))

    vocabularies = model.get("canonical_vocabularies", {})
    for row in rows:
        path = row.get("field_path", "<missing>")
        if row.get("required") not in ALLOWED_REQUIRED:
            errors.append(f"{path}: invalid required value")
        if row.get("nullable") not in ALLOWED_NULLABLE:
            errors.append(f"{path}: invalid nullable value")
        if row.get("mutability") not in ALLOWED_MUTABILITY:
            errors.append(f"{path}: invalid mutability {row.get('mutability')!r}")
        vocab = row.get("state_vocabulary")
        if vocab and vocab not in vocabularies:
            errors.append(f"{path}: unknown state vocabulary {vocab!r}")
        if row.get("data_type") == "enum" and not vocab:
            errors.append(f"{path}: enum field requires state_vocabulary")

    for vocab_name, vocabulary in vocabularies.items():
        values = [item.get("value") for item in vocabulary.get("values", [])]
        if not values:
            errors.append(f"{vocab_name}: vocabulary has no values")
        if len(values) != len(set(values)):
            errors.append(f"{vocab_name}: duplicate state values")
        if not vocabulary.get("owner"):
            errors.append(f"{vocab_name}: missing owner")
        for item in vocabulary.get("values", []):
            if not item.get("meaning"):
                errors.append(f"{vocab_name}.{item.get('value')}: missing meaning")

    workflow_values = {
        item["value"]
        for item in vocabularies.get("workflow_state", {}).get("values", [])
    }
    transitions = model.get("transition_models", {}).get("workflow_state", {})
    if set(transitions) != workflow_values:
        errors.append("workflow transition source states must equal workflow_state vocabulary")
    for source, targets in transitions.items():
        unknown_targets = sorted(set(targets) - workflow_values)
        if unknown_targets:
            errors.append(f"workflow transition {source} has unknown targets: {unknown_targets}")

    rules_text = "\n".join(model.get("cross_state_rules", []))
    for phrase in REQUIRED_CROSS_RULE_PHRASES:
        if phrase.casefold() not in rules_text.casefold():
            errors.append(f"missing cross-state rule: {phrase}")

    source_handoff_rows = [row for row in rows if row.get("section") == "source_handoff"]
    if any(row.get("mutability") != "immutable_input" for row in source_handoff_rows):
        errors.append("every source_handoff field must be immutable_input")

    external_refs = [
        row for row in rows
        if row.get("section") == "system_references"
        and row.get("field_path") not in {"system_references.a1_candidate_id", "system_references.a1_handoff_id"}
    ]
    if any(row.get("nullable") != "yes" for row in external_refs):
        errors.append("future external system references must remain nullable")

    a1_refs = {
        row["field_path"]: row
        for row in rows
        if row.get("field_path") in {"system_references.a1_candidate_id", "system_references.a1_handoff_id"}
    }
    if any(row.get("nullable") != "no" for row in a1_refs.values()) or len(a1_refs) != 2:
        errors.append("A1 candidate and handoff system references must be present and non-nullable")

    score_rows = [row for row in rows if row.get("field_path") == "requalification.score_revision_references[].score"]
    if len(score_rows) != 1 or score_rows[0].get("producer") != "A1 deterministic scorer":
        errors.append("A1 deterministic scorer must be the only score-revision score producer")

    external = model.get("external_state_references", {})
    if external.get("note") != "External HubSpot states are mapping references only and are not canonical A2 workflow states.":
        errors.append("external HubSpot state separation note missing")
    if external.get("process_controls", {}).get("workflow_dependency_status") != "unverified":
        errors.append("HubSpot workflow dependency status must remain unverified")
    if external.get("owner_model", {}).get("owner_assignment_rules_available") is not False:
        errors.append("owner assignment rules must remain unavailable")

    hubspot_states = set()
    for model_name, value in external.get("status_models", {}).items():
        if isinstance(value, list):
            hubspot_states.update(str(item) for item in value)
        elif isinstance(value, dict):
            for nested in value.values():
                if isinstance(nested, list):
                    hubspot_states.update(str(item) for item in nested)
    collisions = sorted(workflow_values & hubspot_states)
    if collisions:
        errors.append(f"canonical workflow states collide with HubSpot external states: {collisions}")

    return errors


def run_regressions(rows: list[dict], model: dict) -> list[dict]:
    cases = []

    def check(name: str, mutated_rows: list[dict], mutated_model: dict, expected: str):
        errors = validate_data(mutated_rows, mutated_model)
        passed = any(expected in error for error in errors)
        cases.append({"name": name, "expected_error": expected, "errors": errors, "passed": passed})

    duplicate_rows = copy.deepcopy(rows)
    duplicate_rows.append(copy.deepcopy(duplicate_rows[0]))
    check("duplicate_field_path", duplicate_rows, model, "duplicate field_path")

    missing_section = [row for row in copy.deepcopy(rows) if row["section"] != "review"]
    check("missing_section", missing_section, model, "section set mismatch")

    unknown_vocab = copy.deepcopy(rows)
    unknown_vocab[0]["state_vocabulary"] = "does_not_exist"
    check("unknown_state_vocabulary", unknown_vocab, model, "unknown state vocabulary")

    duplicate_state_model = copy.deepcopy(model)
    duplicate_state_model["canonical_vocabularies"]["availability_status"]["values"].append(
        copy.deepcopy(duplicate_state_model["canonical_vocabularies"]["availability_status"]["values"][0])
    )
    check("duplicate_state", rows, duplicate_state_model, "duplicate state values")

    bad_transition = copy.deepcopy(model)
    bad_transition["transition_models"]["workflow_state"]["initialised"].append("hubspot_customer")
    check("unknown_transition", rows, bad_transition, "unknown targets")

    mutable_handoff = copy.deepcopy(rows)
    for row in mutable_handoff:
        if row["field_path"] == "source_handoff.handoff_snapshot":
            row["mutability"] = "versioned"
    check("mutable_source_handoff", mutable_handoff, model, "source_handoff field must be immutable_input")

    nonnullable_external = copy.deepcopy(rows)
    for row in nonnullable_external:
        if row["field_path"] == "system_references.hubspot_contact_id":
            row["nullable"] = "no"
    check("nonnullable_future_reference", nonnullable_external, model, "future external system references must remain nullable")

    a2_score = copy.deepcopy(rows)
    for row in a2_score:
        if row["field_path"] == "requalification.score_revision_references[].score":
            row["producer"] = "A2"
    check("a2_score_producer", a2_score, model, "A1 deterministic scorer must be the only")

    missing_rule = copy.deepcopy(model)
    missing_rule["cross_state_rules"] = [
        rule for rule in missing_rule["cross_state_rules"]
        if "manual_no_integration_pilot records cannot enter ready_for_sync" not in rule
    ]
    check("missing_no_integration_rule", rows, missing_rule, "manual_no_integration_pilot records cannot enter ready_for_sync")

    return cases


def main() -> int:
    rows = read_rows()
    model = json.loads(STATE_MODEL.read_text(encoding="utf-8"))
    errors = validate_data(rows, model)
    field_text = FIELD_DOCUMENT.read_text(encoding="utf-8")
    state_text = STATE_DOCUMENT.read_text(encoding="utf-8")
    documentation_checks = {
        "field_document_version": "**Version:** `0.1.0`" in field_text,
        "state_document_version": "**Version:** `0.1.0`" in state_text,
        "field_document_approved": "APPROVED BY UNITALK OPERATIONS FOR STEP 2C" in field_text,
        "state_document_approved": "APPROVED BY UNITALK OPERATIONS FOR STEP 2C" in state_text,
        "recorded_decision": "**Decision:** `APPROVED AS DRAFTED`" in field_text and "**Decision:** `APPROVED AS DRAFTED`" in state_text,
        "critical_state_distinctions": all(value in state_text for value in ["`unknown`", "`not_checked`", "`unavailable`", "`not_found`", "`error`", "`gap`", "`conflict`", "`stale`"]),
        "field_row_count": f"**Total field paths:** {len(rows)}" in field_text,
    }
    for check_name, passed in documentation_checks.items():
        if not passed:
            errors.append(f"documentation check failed: {check_name}")
    regressions = run_regressions(rows, model)
    failed_regressions = [case["name"] for case in regressions if not case["passed"]]
    if failed_regressions:
        errors.append("negative regressions failed: " + ", ".join(failed_regressions))

    result = {
        "step": "2B",
        "version": "0.1.0",
        "approval_state": "approved_for_step_2c",
        "field_dictionary": {
            "path": str(FIELD_DICTIONARY),
            "rows": len(rows),
            "sections": sorted({row["section"] for row in rows}),
        },
        "state_model": {
            "path": str(STATE_MODEL),
            "vocabularies": len(model.get("canonical_vocabularies", {})),
            "workflow_states": len(model.get("canonical_vocabularies", {}).get("workflow_state", {}).get("values", [])),
            "cross_state_rules": len(model.get("cross_state_rules", [])),
        },
        "documentation_checks": documentation_checks,
        "negative_regressions": {
            "total": len(regressions),
            "passed": sum(case["passed"] for case in regressions),
            "failed": failed_regressions,
            "cases": regressions,
        },
        "errors": errors,
        "pass": not errors,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
