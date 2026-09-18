#!/usr/bin/env python3
"""Run Step 2F business fixtures through the canonical A2 validator."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROFILE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_a2_enrichment_record import validate  # noqa: E402

ROOT = PROFILE_ROOT / "evaluations" / "step2f"
FIXTURES = ROOT / "fixtures"
SCENARIO_MANIFEST = FIXTURES / "scenario-manifest.json"
OUTPUT = ROOT / "technical-validation.json"
PACKAGE_MANIFEST = ROOT / "step2f-package-manifest.json"
SCHEMA_PATH = PROFILE_ROOT / "foundations" / "contracts" / "canonical" / "a2-enrichment-record.schema.json"
STEP2E_VALIDATION = PROFILE_ROOT / "evaluations" / "step2e" / "technical-validation.json"
REVIEW_PATH = ROOT / "A2-FIXTURES-AND-REGRESSION-REVIEW.md"
CONTRACT_PATH = PROFILE_ROOT / "foundations" / "A2-FIXTURES-AND-REGRESSION-CONTRACT.md"
ACCEPTANCE_RECORD = ROOT / "acceptance-record.json"
STEP2G_CORRECTION = ROOT / "step2g-compatibility-correction.json"
STEP2I_APPROVAL = PROFILE_ROOT / "evaluations" / "step2i" / "approval-record.json"
LEGACY_PACKAGE_MANIFEST = PROFILE_ROOT / "evaluations" / "step2i" / "pre-promotion-evidence" / "step2f-package-manifest.json"

REQUIRED_VALID_SCENARIOS = {
    "farrier-initial",
    "farrier-planned-gap",
    "farrier-enrichment-in-progress",
    "farrier-review-required",
    "farrier-record-approved",
    "horse-owner-initial",
    "horse-owner-planned-gap",
    "horse-owner-enrichment-in-progress",
    "horse-owner-review-required",
    "horse-owner-record-approved",
    "horse-owner-gap-held",
    "farrier-conflict-held",
    "horse-owner-possible-duplicate-held",
    "farrier-confirmed-duplicate-blocked",
    "farrier-protected-update-awaiting-review",
    "horse-owner-complete-requalification",
}

REQUIRED_NEGATIVE_SCENARIOS = {
    "missing-evidence",
    "blocked-source-evidence",
    "protected-overwrite-without-approval",
    "false-synthetic-sync",
    "a2-score-production",
    "prohibited-outreach",
    "provider-without-approval",
    "cross-segment-field",
    "required-package-missing-assessment",
    "review-ready-with-conflict",
    "confirmed-duplicate-marked-eligible",
    "invalid-a1-score-revision",
    "record-approved-with-incomplete-field-decisions",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def business_assertions(record: dict, expected: dict) -> list[str]:
    errors: list[str] = []
    candidate = record["source_handoff"]["handoff_snapshot"]["candidate_snapshot"]
    actual = {
        "segment": candidate["segment"],
        "workflow_state": record["workflow"]["state"],
        "data_quality_status": record["data_quality"]["status"],
        "a2_eligibility_status": record["duplicate_and_eligibility"]["a2_eligibility_status"],
        "record_decision": record["review"]["record_decision"],
        "external_actions": sum(
            event["external_action"] is not None
            for event in record["audit_and_consumption"]["events"]
        ),
        "requalification_signals": len(record["requalification"]["signals"]),
        "requalification_returns": len(record["requalification"]["returns"]),
        "score_revisions": len(record["requalification"]["score_revision_references"]),
        "missing_field_keys": sorted(record["data_quality"]["missing_field_keys"]),
        "conflict_field_keys": sorted(record["data_quality"]["conflict_field_keys"]),
        "duplicate_statuses": sorted(
            item["status"] for item in record["duplicate_and_eligibility"]["checks"]
            if item["check_type"] == "duplicate"
        ),
        "hold_reason_count": len(record["workflow"]["hold_reasons"]),
        "contradictory_observation_count": sum(
            observation["claim_type"] == "contradictory_evidence"
            for assessment in record["field_assessments"]
            for observation in assessment["observations"]
        ),
        "protected_pending_count": sum(
            assessment["proposed_resolution"] is not None
            and assessment["proposed_resolution"]["action"] in {"update", "clear_request"}
            and assessment["proposed_resolution"]["protected_status"] in {"protected_manual", "protected_policy", "protected_authoritative"}
            and assessment["field_review"]["decision"] == "pending"
            for assessment in record["field_assessments"]
        ),
        "proposed_actions": sorted({
            assessment["proposed_resolution"]["action"]
            for assessment in record["field_assessments"]
            if assessment["proposed_resolution"] is not None
            and assessment["proposed_resolution"]["action"] in {"add", "update", "clear_request", "hold"}
        }),
        "signal_statuses": sorted(item["status"] for item in record["requalification"]["signals"]),
        "return_statuses": sorted(item["status"] for item in record["requalification"]["returns"]),
        "score_revision_statuses": sorted(item["revision_status"] for item in record["requalification"]["score_revision_references"]),
    }
    for key, expected_value in expected.items():
        if actual.get(key) != expected_value:
            errors.append(f"business assertion {key}: expected {expected_value!r}, got {actual.get(key)!r}")
    return errors


def main() -> int:
    scenario_manifest = load(SCENARIO_MANIFEST)
    cases = scenario_manifest["cases"]
    failures: list[str] = []
    results: list[dict] = []

    case_names = [case["name"] for case in cases]
    duplicate_names = sorted({name for name in case_names if case_names.count(name) > 1})
    if duplicate_names:
        failures.append(f"duplicate scenario names: {duplicate_names}")

    valid_names = {case["name"] for case in cases if case["expected_valid"]}
    invalid_names = {case["name"] for case in cases if not case["expected_valid"]}
    missing_valid = sorted(REQUIRED_VALID_SCENARIOS - valid_names)
    missing_invalid = sorted(REQUIRED_NEGATIVE_SCENARIOS - invalid_names)
    if missing_valid:
        failures.append(f"missing required valid scenarios: {missing_valid}")
    if missing_invalid:
        failures.append(f"missing required negative scenarios: {missing_invalid}")

    cases_by_name = {case["name"]: case for case in cases}
    semantic_requirements = {
        "farrier-planned-gap": {"missing_field_keys"},
        "horse-owner-planned-gap": {"missing_field_keys"},
        "horse-owner-gap-held": {"missing_field_keys", "hold_reason_count"},
        "farrier-conflict-held": {"conflict_field_keys", "contradictory_observation_count"},
        "horse-owner-possible-duplicate-held": {"duplicate_statuses"},
        "farrier-confirmed-duplicate-blocked": {"duplicate_statuses"},
        "farrier-protected-update-awaiting-review": {"protected_pending_count", "proposed_actions"},
        "horse-owner-complete-requalification": {"requalification_signals", "requalification_returns", "score_revisions", "signal_statuses", "return_statuses", "score_revision_statuses"},
    }
    semantic_manifest_checks = {}
    for scenario_name, required_keys in semantic_requirements.items():
        expected = cases_by_name.get(scenario_name, {}).get("expected", {})
        passed = required_keys.issubset(expected)
        semantic_manifest_checks[scenario_name] = passed
        if not passed:
            failures.append(f"scenario {scenario_name} lacks required semantic assertions")

    for case in cases:
        record_path = FIXTURES / case["record"]
        previous_path = FIXTURES / case["previous_record"] if case.get("previous_record") else None
        catalogue_path = FIXTURES / case["field_catalogue"] if case.get("field_catalogue") else None
        record = load(record_path)
        integrity_errors = []
        if sha256(record_path) != case.get("record_sha256"):
            integrity_errors.append("fixture hash mismatch")
        if previous_path and sha256(previous_path) != case.get("previous_record_sha256"):
            integrity_errors.append("previous fixture hash mismatch")
        validation = validate(
            record,
            previous=load(previous_path) if previous_path else None,
            field_catalogue=load(catalogue_path) if catalogue_path else None,
        )
        errors = integrity_errors + list(validation["errors"])
        if case["expected_valid"]:
            errors.extend(business_assertions(record, case["expected"]))
            passed = validation["valid"] and not errors
        else:
            passed = (
                not integrity_errors
                and (not validation["valid"])
                and case["expected_error"] in "\n".join(errors)
                and len(errors) == case["expected_error_count"]
            )
        result = {
            "name": case["name"],
            "segment": record["source_handoff"]["handoff_snapshot"]["candidate_snapshot"]["segment"],
            "expected": "valid" if case["expected_valid"] else "invalid",
            "actual": "valid" if validation["valid"] else "invalid",
            "expected_error": case.get("expected_error"),
            "expected_error_count": case.get("expected_error_count"),
            "passed": passed,
            "errors": errors,
        }
        results.append(result)
        if not passed:
            failures.append(f"scenario failed: {case['name']}")

    valid_total = sum(case["expected_valid"] for case in cases)
    invalid_total = sum(not case["expected_valid"] for case in cases)
    segment_counts = {
        segment: sum(result["segment"] == segment for result in results)
        for segment in {result["segment"] for result in results}
    }

    contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
    review_text = REVIEW_PATH.read_text(encoding="utf-8")
    documentation_checks = {
        "contract_version": "**Suite version:** `0.1.0`" in contract_text,
        "contract_approved": "**Step:** `2F — Fixtures and Regression Tests`" in contract_text and "APPROVED BY UNITALK OPERATIONS FOR STEP 2G" in contract_text,
        "review_version": "**Version:** `0.1.0`" in review_text,
        "decisions_f1_to_f10": all(f"| F{number} |" in review_text for number in range(1, 11)),
        "synthetic_only_boundary": "All records are synthetic test artifacts." in contract_text,
        "step2g_boundary": "Step 2G" in contract_text,
    }
    for name, passed in documentation_checks.items():
        if not passed:
            failures.append(f"documentation check failed: {name}")

    referenced_paths = set()
    for case in cases:
        referenced_paths.add(FIXTURES / case["record"])
        if case.get("previous_record"):
            referenced_paths.add(FIXTURES / case["previous_record"])
    all_records_synthetic = True
    recorded_external_action_claims = 0
    for path in sorted(referenced_paths):
        record = load(path)
        if record["record_metadata"]["record_kind"] != "synthetic_test" or not record["source_handoff"]["handoff_snapshot"]["provenance"]["synthetic"]:
            all_records_synthetic = False
        recorded_external_action_claims += sum(
            event["external_action"] is not None
            for event in record["audit_and_consumption"]["events"]
        )
    if not all_records_synthetic:
        failures.append("Step 2F fixture package contains a non-synthetic record")
    if recorded_external_action_claims:
        failures.append("Step 2F fixture package contains an external-action claim")

    package_files = [
        SCRIPTS / "validate_a2_enrichment_record.py",
        SCRIPTS / "build_step2f_fixtures.py",
        SCRIPTS / "run_step2f_tests.py",
        SCHEMA_PATH,
        SCENARIO_MANIFEST,
        FIXTURES / scenario_manifest["catalogue"],
        STEP2E_VALIDATION,
        CONTRACT_PATH,
        REVIEW_PATH,
        ROOT / "INDEPENDENT-ADVERSARIAL-REVIEW-RESOLUTION.md",
        ROOT / "A2-STEP2F-SCENARIO-MATRIX.csv",
        *sorted(referenced_paths),
    ]
    package_manifest = {
        "manifest_id": "equinet-a2-step2f-regression-package",
        "version": "0.1.0",
        "status": "approved_by_unitalk_for_step_2g",
        "files": [
            {"path": str(path.relative_to(PROFILE_ROOT)), "sha256": sha256(path)}
            for path in package_files
        ],
    }
    PACKAGE_MANIFEST.write_text(json.dumps(package_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    acceptance = load(ACCEPTANCE_RECORD)
    step2g_correction = load(STEP2G_CORRECTION)
    step2i_approval = load(STEP2I_APPROVAL)
    acceptance_checks = {
        "decision": acceptance.get("decision") == "approved_as_drafted",
        "suite_version": acceptance.get("suite_version") == "0.1.0",
        "historical_package_manifest_hash": acceptance.get("package_manifest_sha256") == sha256(LEGACY_PACKAGE_MANIFEST),
        "step2g_correction_approved": step2g_correction.get("status") == "approved_in_step_2g",
        "next_gate": acceptance.get("next_gate") == "Step 2G — Handoff-to-Record Initialisation",
        "step2i_promotion_approved": step2i_approval.get("decision") == "approved" and step2i_approval.get("promotion_authorized") is True,
    }
    for name, passed in acceptance_checks.items():
        if not passed:
            failures.append(f"acceptance check failed: {name}")

    result = {
        "step": "2F",
        "suite_version": "0.1.0",
        "approval_state": "promoted_in_step_2i",
        "canonical_schema_version": "1.0.0",
        "validator_version": "0.1.0",
        "coverage": {
            "required_valid_scenarios": sorted(REQUIRED_VALID_SCENARIOS),
            "required_negative_scenarios": sorted(REQUIRED_NEGATIVE_SCENARIOS),
            "missing_valid_scenarios": missing_valid,
            "missing_negative_scenarios": missing_invalid,
            "semantic_manifest_checks": semantic_manifest_checks,
            "segment_case_counts": segment_counts,
            "all_records_synthetic": all_records_synthetic,
            "recorded_external_action_claims": recorded_external_action_claims,
            "external_actions_performed": 0,
        },
        "documentation_checks": documentation_checks,
        "acceptance_checks": acceptance_checks,
        "summary": {
            "valid_expected": valid_total,
            "invalid_expected": invalid_total,
            "cases_total": len(results),
            "cases_passed": sum(result["passed"] for result in results),
            "cases_failed": sum(not result["passed"] for result in results),
        },
        "package_manifest": {"path": str(PACKAGE_MANIFEST), "sha256": sha256(PACKAGE_MANIFEST), "file_count": len(package_files)},
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
