#!/usr/bin/env python3
"""Regression tests for the A1 Evidence and Confidence Rules."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


PROFILE_DIR = Path(__file__).resolve().parents[1]
POLICY_PATH = PROFILE_DIR / "configurations" / "evidence" / "evidence-confidence-rules-v1.yaml"
VALIDATOR_PATH = PROFILE_DIR / "scripts" / "validate_evidence_confidence_rules.py"
CALCULATOR_PATH = PROFILE_DIR / "scripts" / "calculate_candidate_confidence.py"


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validator = import_module("evidence_validator", VALIDATOR_PATH)
calculator = import_module("confidence_calculator", CALCULATOR_PATH)


def base_gates() -> dict[str, bool]:
    return {
        "mandatory_claim_inference_only": False,
        "unresolved_identity_conflict": False,
        "critical_evidence_conflict": False,
        "minimum_data_failed": False,
        "blocked_source_used": False,
        "no_evidence": False,
        "fabricated_or_untraceable_evidence": False,
    }


def high_assessment() -> dict:
    return {
        "method_version": "evidence-confidence-1.0.0",
        "dimensions": {
            "identity_certainty": "strong_unique_match",
            "source_quality": "authoritative_or_two_strong",
            "evidence_directness": "all_material_claims_direct",
            "corroboration": "two_or_more_independent_sources",
            "freshness": "current_within_claim_window",
            "completeness": "complete_for_review",
        },
        "gates": base_gates(),
    }


def assert_result(label: str, result: dict, score: int, level: str) -> None:
    actual = result["confidence"]
    if actual["score"] != score or actual["level"] != level:
        raise AssertionError(f"{label}: expected {score}/{level}, received {actual['score']}/{actual['level']}")
    print(f"PASS: {label}")


def expect_value_error(label: str, assessment: dict, policy: dict, expected: str) -> None:
    try:
        calculator.calculate(assessment, policy)
    except ValueError as exc:
        if expected not in str(exc):
            raise AssertionError(f"{label}: unexpected error {exc}")
        print(f"PASS: {label}")
        return
    raise AssertionError(f"{label}: expected ValueError")


def main() -> int:
    policy = validator.load_yaml(POLICY_PATH)
    errors = validator.validate_policy(policy)
    if errors:
        raise AssertionError(f"Current policy should be valid: {errors}")
    print("PASS: current evidence policy")

    high = high_assessment()
    assert_result("high confidence", calculator.calculate(high, policy), 100, "high")

    website = copy.deepcopy(high)
    website["dimensions"]["source_quality"] = "authoritative_primary_business_source"
    website["dimensions"]["corroboration"] = "one_strong_source"
    assert_result("single authoritative business website may be High", calculator.calculate(website, policy), 92, "high")

    inference = copy.deepcopy(high)
    inference["gates"]["mandatory_claim_inference_only"] = True
    assert_result("mandatory inference capped at Low", calculator.calculate(inference, policy), 59, "low")

    conflict = copy.deepcopy(high)
    conflict["gates"]["critical_evidence_conflict"] = True
    assert_result("critical conflict capped at Low", calculator.calculate(conflict, policy), 39, "low")

    blocked = copy.deepcopy(high)
    blocked["gates"]["blocked_source_used"] = True
    expect_value_error("blocked source invalidates assessment", blocked, policy, "blocked source")

    invalid_level = copy.deepcopy(high)
    invalid_level["dimensions"]["freshness"] = "perfect_forever"
    expect_value_error("unknown dimension level rejected", invalid_level, policy, "Invalid level")

    drift = copy.deepcopy(policy)
    drift["confidence_model"]["dimensions"]["freshness"]["max_points"] = 20
    drift_errors = validator.validate_policy(drift)
    if not any("total 100" in error for error in drift_errors):
        raise AssertionError(f"Point-total regression was not rejected: {drift_errors}")
    print("PASS: confidence maximum drift rejected")

    freshness_regression = copy.deepcopy(policy)
    freshness_regression["freshness_policy"]["current_official_business_website"]["visible_publication_date_required"] = True
    freshness_errors = validator.validate_policy(freshness_regression)
    if not any("must not require a visible publication date" in error for error in freshness_errors):
        raise AssertionError(f"Official-site freshness regression was not rejected: {freshness_errors}")
    print("PASS: official business website requires no visible publication date")

    approval_regression = copy.deepcopy(policy)
    approval_regression["approval_record"]["approved_decisions"] = []
    approval_errors = validator.validate_policy(approval_regression)
    if not any("five retained evidence decisions" in error for error in approval_errors):
        raise AssertionError(f"Approval-record regression was not rejected: {approval_errors}")
    print("PASS: Séverine approval record preserved")

    output = calculator.calculate(website, policy)["confidence"]
    required_fields = {"level", "score", "method_version", "reasons", "limitations"}
    if set(output) != required_fields:
        raise AssertionError("Calculator confidence output does not match Candidate confidence fields.")
    print("PASS: Candidate confidence output shape")

    print("ALL EVIDENCE AND CONFIDENCE TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
