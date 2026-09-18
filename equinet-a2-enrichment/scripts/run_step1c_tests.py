#!/usr/bin/env python3
"""Run deterministic Step 1C tests for the Equinet A1-to-A2 handoff contract."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROFILE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_a1_to_a2_handoff import validate_document  # noqa: E402

CONTRACTS = PROFILE_ROOT / "foundations" / "contracts"
HUMAN_CONTRACT = PROFILE_ROOT / "foundations" / "A1-TO-A2-HANDOFF-CONTRACT.md"
HANDOFF_SCHEMA = CONTRACTS / "a1-to-a2-handoff.schema.json"
VALID_DIR = CONTRACTS / "examples" / "valid"
INVALID_DIR = CONTRACTS / "examples" / "invalid"
RESULT_PATH = PROFILE_ROOT / "evaluations" / "step1c" / "technical-validation.json"
DEPENDENCY_MANIFEST = CONTRACTS / "dependencies" / "a1-dependency-manifest.json"
SOURCE_A1_SCHEMA = Path("/opt/data/profiles/equinet-a1-icp-discovery/skills/a1-prospect-data-contract/references/prospect-candidate.schema.json")
SOURCE_A1_VALIDATOR = Path("/opt/data/profiles/equinet-a1-icp-discovery/skills/a1-prospect-data-contract/scripts/validate_candidate.py")
PINNED_A1_SCHEMA = CONTRACTS / "dependencies" / "a1-prospect-candidate.schema.json"
PINNED_A1_VALIDATOR = CONTRACTS / "dependencies" / "a1_validate_candidate.py"

EXPECTED_INVALID = {
    "invalid-missing-human-approval.json": "candidate workflow.stage must be approved_for_a2",
    "invalid-recommendation-not-pass-to-a2.json": "candidate recommendation.next_action must be pass_to_a2",
    "invalid-possible-duplicate-declared-eligible.json": "duplicate_batch gate must be needs_review",
    "invalid-snapshot-hash.json": "snapshot hash mismatch",
    "invalid-no-integration-claims-delivered.json": "manual_no_integration_pilot cannot progress beyond ready_for_delivery",
    "invalid-synthetic-crm-write-authorized.json": "scope_permissions gate must be fail",
    "invalid-receipt-handoff-id.json": "A2 receipt handoff_id must equal handoff_id",
    "invalid-duplicate-gate-id.json": "eligibility gate IDs must be unique",
    "invalid-excluded-candidate.json": "candidate workflow.stage must be approved_for_a2",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    failures: list[str] = []
    cases: list[dict] = []

    contract_text = HUMAN_CONTRACT.read_text(encoding="utf-8")
    handoff_schema = json.loads(HANDOFF_SCHEMA.read_text(encoding="utf-8"))
    static_checks = {
        "contract_version": "**Contract version:** `1.0.1`" in contract_text,
        "contract_approved_status": "APPROVED BY UNITALK OPERATIONS FOR A2 FOUNDATION" in contract_text,
        "recorded_decision": "**Decision:** `APPROVED AS DRAFTED`" in contract_text,
        "decision_ids_h1_to_h6": all(f"| H{number} |" in contract_text for number in range(1, 7)),
        "score_revision_clarification": "A1 alone creates a new deterministic score revision" in contract_text,
        "schema_id": handoff_schema.get("$id") == "https://unitalk.ai/schemas/equinet/a1-a2/handoff/1.0.1",
        "schema_version_const": handoff_schema.get("properties", {}).get("handoff_schema_version", {}).get("const") == "1.0.1",
        "strict_root": handoff_schema.get("additionalProperties") is False,
    }
    for check_name, passed in static_checks.items():
        if not passed:
            failures.append(f"Static contract check failed: {check_name}")

    manifest = json.loads(DEPENDENCY_MANIFEST.read_text(encoding="utf-8"))
    dependency_checks = {
        "source_schema_hash": sha256(SOURCE_A1_SCHEMA),
        "pinned_schema_hash": sha256(PINNED_A1_SCHEMA),
        "manifest_schema_hash": manifest["sha256"],
        "source_validator_hash": sha256(SOURCE_A1_VALIDATOR),
        "pinned_validator_hash": sha256(PINNED_A1_VALIDATOR),
        "manifest_validator_hash": manifest["validator_sha256"],
    }
    schema_hashes = {
        dependency_checks["source_schema_hash"],
        dependency_checks["pinned_schema_hash"],
        dependency_checks["manifest_schema_hash"],
    }
    validator_hashes = {
        dependency_checks["source_validator_hash"],
        dependency_checks["pinned_validator_hash"],
        dependency_checks["manifest_validator_hash"],
    }
    dependency_checks["schema_copy_match"] = len(schema_hashes) == 1
    dependency_checks["validator_copy_match"] = len(validator_hashes) == 1
    if not dependency_checks["schema_copy_match"]:
        failures.append("Pinned A1 schema does not match source and manifest hashes.")
    if not dependency_checks["validator_copy_match"]:
        failures.append("Pinned A1 validator does not match source and manifest hashes.")

    for path in sorted(VALID_DIR.glob("*.json")):
        result = validate_document(path)
        passed = result["valid"]
        cases.append({
            "fixture": path.name,
            "expected": "valid",
            "actual": "valid" if result["valid"] else "invalid",
            "passed": passed,
            "errors": result["errors"],
        })
        if not passed:
            failures.append(f"Valid fixture failed: {path.name}")

    for filename, expected_error in EXPECTED_INVALID.items():
        path = INVALID_DIR / filename
        result = validate_document(path)
        combined = "\n".join(result["errors"])
        passed = (not result["valid"]) and expected_error in combined
        cases.append({
            "fixture": filename,
            "expected": "invalid",
            "expected_error": expected_error,
            "actual": "valid" if result["valid"] else "invalid",
            "passed": passed,
            "errors": result["errors"],
        })
        if not passed:
            failures.append(f"Invalid fixture did not fail as expected: {filename}")

    result = {
        "step": "1C",
        "contract_version": "1.0.1",
        "approval_state": "approved_for_a2_foundation",
        "static_checks": static_checks,
        "dependency_checks": dependency_checks,
        "summary": {
            "valid_expected": len(list(VALID_DIR.glob("*.json"))),
            "invalid_expected": len(EXPECTED_INVALID),
            "cases_total": len(cases),
            "cases_passed": sum(1 for case in cases if case["passed"]),
            "cases_failed": sum(1 for case in cases if not case["passed"]),
        },
        "cases": cases,
        "failures": failures,
        "pass": not failures,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
