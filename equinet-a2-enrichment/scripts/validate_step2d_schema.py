#!/usr/bin/env python3
"""Validate the Step 2D canonical A2 JSON Schema and smoke fixtures."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

PROFILE_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = PROFILE_ROOT / "foundations" / "contracts"
ROOT = CONTRACTS / "canonical"
SCHEMA_PATH = ROOT / "a2-enrichment-record.schema.json"
MANIFEST_PATH = ROOT / "a2-enrichment-record.dependency-manifest.json"
STATE_MODEL_PATH = CONTRACTS / "a2-state-model-0.1.0.json"
FIELD_DICTIONARY_PATH = CONTRACTS / "a2-field-dictionary-0.1.0.csv"
OUTPUT = PROFILE_ROOT / "evaluations" / "step2d" / "technical-validation.json"
CONTRACT_DOCUMENT = PROFILE_ROOT / "foundations" / "A2-CANONICAL-JSON-SCHEMA-CONTRACT.md"
REVIEW_DOCUMENT = PROFILE_ROOT / "evaluations" / "step2d" / "A2-CANONICAL-JSON-SCHEMA-REVIEW.md"
ACCEPTANCE_RECORD = PROFILE_ROOT / "evaluations" / "step2d" / "acceptance-record.json"
CORRECTION_RECORD = PROFILE_ROOT / "evaluations" / "step2d" / "correction-draft2-record.json"
STEP2I_APPROVAL = PROFILE_ROOT / "evaluations" / "step2i" / "approval-record.json"
LEGACY_SCHEMA = PROFILE_ROOT / "evaluations" / "step2i" / "pre-promotion-evidence" / "a2-enrichment-record-1.0.0-draft.2.schema.json"
VALID_DIR = ROOT / "examples" / "valid"
INVALID_DIR = ROOT / "examples" / "invalid"

EXTERNAL_SCHEMAS = [
    CONTRACTS / "dependencies" / "a1-prospect-candidate.schema.json",
    CONTRACTS / "a1-to-a2-handoff.schema.json",
    CONTRACTS / "requalification" / "a2-requalification-signal.schema.json",
    CONTRACTS / "requalification" / "a2-requalification-return.schema.json",
    CONTRACTS / "requalification" / "a1-score-revision-reference.schema.json",
]

EXPECTED_TOP_LEVEL = [
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
]

EXPECTED_INVALID = {
    "invalid-extra-root-property.json": "Additional properties are not allowed",
    "invalid-extra-nested-property.json": "Additional properties are not allowed",
    "invalid-schema-version.json": "was expected",
    "invalid-no-integration-sync.json": "should not be valid under",
    "invalid-a2-score-field.json": "Additional properties are not allowed",
}

VOCAB_PATHS = {
    ("properties", "record_metadata", "properties", "record_kind"): "record_kind",
    ("properties", "record_metadata", "properties", "change_reason"): "change_reason",
    ("properties", "source_handoff", "properties", "operating_scope"): "operating_scope",
    ("properties", "source_handoff", "properties", "eligibility_status"): "eligibility_status",
    ("properties", "subject", "properties", "identity_resolution_status"): "identity_resolution_status",
    ("properties", "enrichment_scope", "properties", "mode"): "enrichment_mode",
    ("properties", "enrichment_scope", "properties", "operating_scope"): "operating_scope",
    ("properties", "data_quality", "properties", "status"): "data_quality_status",
    ("properties", "duplicate_and_eligibility", "properties", "a2_eligibility_status"): "eligibility_status",
    ("properties", "duplicate_and_eligibility", "properties", "outreach_eligibility_status"): "outreach_eligibility_status",
    ("properties", "duplicate_and_eligibility", "properties", "owner_routing_status"): "owner_routing_status",
    ("properties", "review", "properties", "record_decision"): "record_review_decision",
    ("properties", "workflow", "properties", "state"): "workflow_state",
    ("properties", "governance", "properties", "source_terms_review_status"): "source_policy_status",
    ("properties", "governance", "properties", "consent_check_status"): "outreach_eligibility_status",
    ("$defs", "entity", "properties", "entity_type"): "entity_type",
    ("$defs", "entity", "properties", "match_status"): "entity_match_status",
    ("$defs", "observation", "properties", "verification_status"): "verification_status",
    ("$defs", "observation", "properties", "confidence_level"): "confidence_level",
    ("$defs", "observation", "properties", "freshness_status"): "freshness_status",
    ("$defs", "observation", "properties", "claim_type"): "claim_type",
    ("$defs", "proposal", "properties", "action"): "proposal_action",
    ("$defs", "proposal", "properties", "verification_status"): "verification_status",
    ("$defs", "proposal", "properties", "confidence_level"): "confidence_level",
    ("$defs", "proposal", "properties", "freshness_status"): "freshness_status",
    ("$defs", "proposal", "properties", "conflict_status"): "conflict_status",
    ("$defs", "proposal", "properties", "protected_status"): "protected_field_status",
    ("$defs", "fieldReview", "properties", "decision"): "field_review_decision",
    ("$defs", "application", "properties", "status"): "application_status",
    ("$defs", "application", "properties", "workflow_dependency_status"): "workflow_dependency_status",
    ("$defs", "fieldAssessment", "properties", "scope"): "field_scope",
    ("$defs", "fieldAssessment", "properties", "presence_status"): "value_presence_status",
    ("$defs", "fieldAssessment", "properties", "availability_status"): "availability_status",
    ("$defs", "fieldAssessment", "properties", "field_quality_status"): "field_quality_status",
    ("$defs", "evidence", "properties", "namespace"): "evidence_namespace",
    ("$defs", "evidence", "properties", "source_policy_status"): "source_policy_status",
    ("$defs", "evidence", "properties", "claim_type"): "claim_type",
    ("$defs", "evidence", "properties", "reliability_level"): "reliability_level",
    ("$defs", "eligibilityCheck", "properties", "status"): "duplicate_status",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_path(value: dict, path: tuple[str, ...]):
    current = value
    for part in path:
        current = current[part]
    return current


def collect_unstrict_objects(value: object, path: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(value, dict):
        if value.get("type") == "object" and value.get("additionalProperties") is not False:
            failures.append(path)
        for key, child in value.items():
            failures.extend(collect_unstrict_objects(child, f"{path}/{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            failures.extend(collect_unstrict_objects(child, f"{path}/{index}"))
    return failures


def registry(schema: dict) -> Registry:
    result = Registry()
    for path in EXTERNAL_SCHEMAS:
        resource_schema = load_json(path)
        result = result.with_resource(resource_schema["$id"], Resource.from_contents(resource_schema))
    result = result.with_resource(schema["$id"], Resource.from_contents(schema))
    return result


def schema_errors(document: dict, schema: dict, schema_registry: Registry) -> list[str]:
    validator = Draft202012Validator(schema, registry=schema_registry, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda error: (list(error.absolute_path), error.message))
    rendered = []
    for error in errors:
        path = "/" + "/".join(str(part) for part in error.absolute_path)
        rendered.append(f"schema:{path}: {error.message}")
    return rendered


def main() -> int:
    schema = load_json(SCHEMA_PATH)
    manifest = load_json(MANIFEST_PATH)
    state_model = load_json(STATE_MODEL_PATH)
    contract_text = CONTRACT_DOCUMENT.read_text(encoding="utf-8")
    review_text = REVIEW_DOCUMENT.read_text(encoding="utf-8")
    acceptance = load_json(ACCEPTANCE_RECORD)
    correction = load_json(CORRECTION_RECORD)
    step2i_approval = load_json(STEP2I_APPROVAL)
    failures: list[str] = []

    try:
        Draft202012Validator.check_schema(schema)
        schema_compiles = True
    except Exception as exc:  # pragma: no cover - surfaced in report
        schema_compiles = False
        failures.append(f"schema compilation failed: {exc}")

    manifest_checks = []
    if manifest.get("schema_sha256") != sha256(SCHEMA_PATH):
        failures.append("schema hash mismatch in dependency manifest")
    for dependency in manifest.get("dependencies", []):
        path = PROFILE_ROOT / dependency["path"]
        actual = sha256(path)
        passed = actual == dependency["sha256"]
        manifest_checks.append({"path": dependency["path"], "expected": dependency["sha256"], "actual": actual, "passed": passed})
        if not passed:
            failures.append(f"dependency hash mismatch: {dependency['path']}")

    top_level_properties = list(schema.get("properties", {}).keys())
    if top_level_properties != EXPECTED_TOP_LEVEL:
        failures.append("top-level canonical section order/set mismatch")
    if schema.get("required") != EXPECTED_TOP_LEVEL:
        failures.append("required top-level canonical section set mismatch")
    if schema.get("properties", {}).get("record_metadata", {}).get("properties", {}).get("schema_version", {}).get("const") != "1.0.0":
        failures.append("schema version const is not 1.0.0")

    unstrict_objects = collect_unstrict_objects(schema)
    if unstrict_objects:
        failures.extend(f"object schema is not strict: {path}" for path in unstrict_objects)

    vocab_checks = []
    for path, vocabulary in VOCAB_PATHS.items():
        schema_values = get_path(schema, path).get("enum")
        approved_values = [item["value"] for item in state_model["canonical_vocabularies"][vocabulary]["values"]]
        passed = schema_values == approved_values
        vocab_checks.append({"schema_path": "/".join(path), "vocabulary": vocabulary, "passed": passed})
        if not passed:
            failures.append(f"state vocabulary mismatch: {vocabulary} at {'/'.join(path)}")

    required_refs = {
        "handoff": "https://unitalk.ai/schemas/equinet/a1-a2/handoff/1.0.1",
        "signal": "https://unitalk.ai/schemas/equinet/a2/requalification-signal/0.1.0",
        "return": "https://unitalk.ai/schemas/equinet/a2/requalification-return/0.1.0",
        "revision": "https://unitalk.ai/schemas/equinet/a2/a1-score-revision-reference/0.1.0",
    }
    schema_text = SCHEMA_PATH.read_text(encoding="utf-8")
    ref_checks = {name: ref in schema_text for name, ref in required_refs.items()}
    for name, passed in ref_checks.items():
        if not passed:
            failures.append(f"missing approved external schema reference: {name}")

    forbidden_embedded_mapping_terms = ["lifecyclestage", "hs_lead_status", "dealstage", "hubspot_property_mapping"]
    mapping_boundary_checks = {term: term not in schema_text for term in forbidden_embedded_mapping_terms}
    for term, passed in mapping_boundary_checks.items():
        if not passed:
            failures.append(f"CRM mapping leaked into canonical schema: {term}")

    contract_metadata = schema.get("x-unitalk-contract", {})
    required_external_configs = {
        "business_field_catalogue",
        "minimum_data_packages",
        "source_and_provider_policy",
        "confidence_and_freshness_rules",
        "protected_field_catalogue",
        "approval_matrix",
        "hubspot_twenty_crm_mapping",
        "retention_and_deletion_policy",
    }
    if set(contract_metadata.get("external_configurations", [])) != required_external_configs:
        failures.append("external configuration boundary is incomplete or changed")
    if contract_metadata.get("cross_field_validator_step") != "2E":
        failures.append("cross-field validator ownership must remain Step 2E")

    documentation_checks = {
        "contract_approved": "PROMOTED BY UNITALK OPERATIONS IN STEP 2I" in contract_text,
        "review_approved": "APPROVED BY UNITALK OPERATIONS FOR STEP 2E" in review_text,
        "decision_recorded": "APPROVED AS DRAFTED" in contract_text,
        "decisions_d1_to_d10": all(f"| D{number} |" in contract_text for number in range(1, 11)),
        "accepted_baseline_preserved": acceptance.get("artifact_version") == "1.0.0-draft.1" and acceptance.get("decision") == "approved_as_drafted",
        "correction_version": correction.get("corrected_schema_version") == "1.0.0-draft.2",
        "historical_correction_hash": correction.get("corrected_schema_sha256") == sha256(LEGACY_SCHEMA),
        "correction_approved_in_step2e": correction.get("status") == "approved_in_step_2e",
        "acceptance_next_gate": acceptance.get("next_gate") == "Step 2E — Deterministic Cross-Field Validator",
        "step2i_promotion_approved": step2i_approval.get("decision") == "approved" and step2i_approval.get("promotion_authorized") is True,
    }
    for check_name, passed in documentation_checks.items():
        if not passed:
            failures.append(f"documentation or acceptance check failed: {check_name}")

    schema_registry = registry(schema)
    cases = []
    for path in sorted(VALID_DIR.glob("*.json")):
        errors = schema_errors(load_json(path), schema, schema_registry)
        passed = not errors
        cases.append({"fixture": path.name, "expected": "valid", "actual": "valid" if passed else "invalid", "passed": passed, "errors": errors})
        if not passed:
            failures.append(f"valid smoke fixture failed: {path.name}")

    for filename, expected_error in EXPECTED_INVALID.items():
        path = INVALID_DIR / filename
        errors = schema_errors(load_json(path), schema, schema_registry)
        combined = "\n".join(errors)
        passed = bool(errors) and expected_error in combined
        cases.append({"fixture": filename, "expected": "invalid", "expected_error": expected_error, "actual": "invalid" if errors else "valid", "passed": passed, "errors": errors})
        if not passed:
            failures.append(f"invalid smoke fixture did not fail as expected: {filename}")

    result = {
        "step": "2D",
        "schema_version": "1.0.0",
        "approval_state": "promoted_in_step_2i",
        "schema_path": str(SCHEMA_PATH),
        "schema_sha256": sha256(SCHEMA_PATH),
        "schema_compiles": schema_compiles,
        "canonical_sections": {"expected": len(EXPECTED_TOP_LEVEL), "actual": len(top_level_properties), "passed": top_level_properties == EXPECTED_TOP_LEVEL},
        "strict_local_object_schemas": {"checked": True, "unstrict_paths": unstrict_objects, "passed": not unstrict_objects},
        "dependency_hashes": {"count": len(manifest_checks), "checks": manifest_checks, "passed": all(item["passed"] for item in manifest_checks)},
        "state_vocabulary_checks": {"count": len(vocab_checks), "checks": vocab_checks, "passed": all(item["passed"] for item in vocab_checks)},
        "approved_schema_references": {"checks": ref_checks, "passed": all(ref_checks.values())},
        "mapping_boundary": {"checks": mapping_boundary_checks, "passed": all(mapping_boundary_checks.values())},
        "documentation_and_acceptance": {"checks": documentation_checks, "passed": all(documentation_checks.values())},
        "smoke_tests": {
            "valid_expected": len(list(VALID_DIR.glob("*.json"))),
            "invalid_expected": len(EXPECTED_INVALID),
            "total": len(cases),
            "passed": sum(case["passed"] for case in cases),
            "failed": sum(not case["passed"] for case in cases),
            "cases": cases,
        },
        "deferred_to_step_2e": [
            "cross-record and cross-section identifier equality",
            "evidence-reference resolution and namespace integrity",
            "field-catalogue type and value validation",
            "workflow transition validation against the prior revision",
            "protected-field decision and application consistency",
            "application receipt and reconciliation checks",
            "A2 requalification package consistency beyond referenced schema shape",
        ],
        "deferred_to_step_2f": "Full Farrier/Horse Owner positive and negative regression fixture suite.",
        "failures": failures,
        "pass": not failures,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
