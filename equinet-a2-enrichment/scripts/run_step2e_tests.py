#!/usr/bin/env python3
"""Run Step 2E deterministic cross-field validator regressions."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROFILE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_a2_enrichment_record import validate  # noqa: E402

ROOT = PROFILE_ROOT / "evaluations" / "step2e"
FIXTURES = ROOT / "fixtures"
MANIFEST_PATH = FIXTURES / "test-manifest.json"
OUTPUT = ROOT / "technical-validation.json"
SCHEMA_PATH = PROFILE_ROOT / "foundations" / "contracts" / "canonical" / "a2-enrichment-record.schema.json"
VALIDATOR_MANIFEST_PATH = PROFILE_ROOT / "foundations" / "contracts" / "canonical" / "a2-cross-field-validator.manifest.json"
STEP2I_APPROVAL = PROFILE_ROOT / "evaluations" / "step2i" / "approval-record.json"
LEGACY_SCHEMA = PROFILE_ROOT / "evaluations" / "step2i" / "pre-promotion-evidence" / "a2-enrichment-record-1.0.0-draft.2.schema.json"
LEGACY_VALIDATOR_MANIFEST = PROFILE_ROOT / "evaluations" / "step2i" / "pre-promotion-evidence" / "a2-cross-field-validator.manifest.json"
CONTRACT_PATH = PROFILE_ROOT / "foundations" / "A2-CROSS-FIELD-VALIDATOR-CONTRACT.md"
REVIEW_PATH = ROOT / "A2-CROSS-FIELD-VALIDATOR-REVIEW.md"
ACCEPTANCE_RECORD = ROOT / "acceptance-record.json"
STEP2D_CORRECTION = PROFILE_ROOT / "evaluations" / "step2d" / "correction-draft2-record.json"
STEP2C_CLARIFICATION = PROFILE_ROOT / "evaluations" / "foundation-clarifications" / "step2c-requalification-lifecycle-clarification.json"
STEP2G_CORRECTION = ROOT / "step2g-initialisation-compatibility-correction.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = load(MANIFEST_PATH)
    failures: list[str] = []
    results: list[dict] = []

    for case in manifest["cases"]:
        record_path = FIXTURES / case["record"]
        previous_path = FIXTURES / case["previous_record"] if case.get("previous_record") else None
        catalogue_path = FIXTURES / case["field_catalogue"] if case.get("field_catalogue") else None
        result = validate(
            load(record_path),
            previous=load(previous_path) if previous_path else None,
            field_catalogue=load(catalogue_path) if catalogue_path else None,
        )
        expected_valid = case["expected_valid"]
        expected_error = case.get("expected_error")
        combined = "\n".join(result["errors"])
        passed = result["valid"] == expected_valid and (expected_error is None or expected_error in combined)
        results.append({
            "name": case["name"],
            "record": case["record"],
            "previous_record": case.get("previous_record"),
            "field_catalogue": case.get("field_catalogue"),
            "expected": "valid" if expected_valid else "invalid",
            "actual": "valid" if result["valid"] else "invalid",
            "expected_error": expected_error,
            "passed": passed,
            "errors": result["errors"],
        })
        if not passed:
            failures.append(f"case failed: {case['name']}")

    documentation_checks = {}
    if CONTRACT_PATH.exists() and REVIEW_PATH.exists():
        contract = CONTRACT_PATH.read_text(encoding="utf-8")
        review = REVIEW_PATH.read_text(encoding="utf-8")
        acceptance = load(ACCEPTANCE_RECORD)
        step2d_correction = load(STEP2D_CORRECTION)
        step2c_clarification = load(STEP2C_CLARIFICATION)
        step2g_correction = load(STEP2G_CORRECTION)
        step2i_approval = load(STEP2I_APPROVAL)
        documentation_checks = {
            "contract_version": "**Validator version:** `0.1.0`" in contract,
            "contract_approved": "**Step:** `2E — Deterministic Cross-Field Validator`" in contract and "APPROVED BY UNITALK OPERATIONS FOR STEP 2F" in contract,
            "review_version": "**Version:** `0.1.0`" in review,
            "decisions_e1_to_e13": all(f"| E{number} |" in review for number in range(1, 14)),
            "a2_score_boundary": "A2 cannot create points, a replacement score or a replacement band." in contract,
            "step2f_boundary": "Step 2F" in contract,
            "acceptance_decision": acceptance.get("decision") == "approved_as_drafted",
            "acceptance_validator_hash": acceptance.get("validator_sha256") == sha256(SCRIPTS / "validate_a2_enrichment_record.py"),
            "historical_acceptance_manifest_hash": acceptance.get("validator_manifest_sha256") == sha256(LEGACY_VALIDATOR_MANIFEST),
            "step2g_correction_approved": step2g_correction.get("status") == "approved_in_step_2g",
            "historical_acceptance_schema_hash": acceptance.get("canonical_schema_sha256") == sha256(LEGACY_SCHEMA),
            "step2d_correction_approved": step2d_correction.get("status") == "approved_in_step_2e",
            "step2c_clarification_approved": step2c_clarification.get("status") == "approved_in_step_2e",
            "next_gate": acceptance.get("next_gate") == "Step 2F — Fixtures and Regression Tests",
            "step2i_promotion_approved": step2i_approval.get("decision") == "approved" and step2i_approval.get("promotion_authorized") is True,
        }
        for name, passed in documentation_checks.items():
            if not passed:
                failures.append(f"documentation check failed: {name}")

    valid_count = sum(1 for case in manifest["cases"] if case["expected_valid"])
    invalid_count = sum(1 for case in manifest["cases"] if not case["expected_valid"])
    validator_manifest = load(VALIDATOR_MANIFEST_PATH)
    dependency_checks = []
    for dependency in validator_manifest["dependencies"]:
        path = PROFILE_ROOT / dependency["path"]
        actual = sha256(path)
        passed = actual == dependency["sha256"]
        dependency_checks.append({"path": dependency["path"], "expected": dependency["sha256"], "actual": actual, "passed": passed})
        if not passed:
            failures.append(f"validator dependency hash mismatch: {dependency['path']}")
    result = {
        "step": "2E",
        "validator_version": "0.1.0",
        "approval_state": "promoted_in_step_2i",
        "schema": {"path": str(SCHEMA_PATH), "version": "1.0.0", "sha256": sha256(SCHEMA_PATH)},
        "validator_manifest": {"path": str(VALIDATOR_MANIFEST_PATH), "dependency_count": len(dependency_checks), "sha256": sha256(VALIDATOR_MANIFEST_PATH), "checks": dependency_checks, "passed": all(item["passed"] for item in dependency_checks)},
        "coverage": {
            "schema_first": True,
            "current_record_cross_fields": True,
            "previous_revision_comparison": True,
            "optional_external_field_catalogue": True,
            "no_external_actions": True,
        },
        "documentation_checks": documentation_checks,
        "summary": {
            "valid_expected": valid_count,
            "invalid_expected": invalid_count,
            "cases_total": len(results),
            "cases_passed": sum(item["passed"] for item in results),
            "cases_failed": sum(not item["passed"] for item in results),
        },
        "cases": results,
        "failures": failures,
        "pass": not failures,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
