#!/usr/bin/env python3
"""Regression tests for the Equinet A1 ICP Scoring Model."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator


PROFILE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = PROFILE_DIR / "configurations" / "scoring" / "icp-scoring-model-v1.yaml"
ICP_PATH = PROFILE_DIR / "configurations" / "icp" / "equinet-icp-v1.yaml"
VALIDATOR_PATH = PROFILE_DIR / "scripts" / "validate_icp_scoring_model.py"
CALCULATOR_PATH = PROFILE_DIR / "scripts" / "calculate_icp_score.py"
CANDIDATE_SCHEMA_PATH = PROFILE_DIR / "skills" / "a1-prospect-data-contract" / "references" / "prospect-candidate.schema.json"


def scoring_schema_validator() -> Draft202012Validator:
    schema = json.loads(CANDIDATE_SCHEMA_PATH.read_text(encoding="utf-8"))
    wrapper = {
        "$schema": schema.get("$schema", "https://json-schema.org/draft/2020-12/schema"),
        "$ref": "#/$defs/scoring",
        "$defs": schema["$defs"],
    }
    return Draft202012Validator(wrapper)


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validator = import_module("scoring_validator", VALIDATOR_PATH)
calculator = import_module("scoring_calculator", CALCULATOR_PATH)


def criterion(criterion_id: str, status: str = "confirmed") -> dict:
    return {
        "criterion_id": criterion_id,
        "status": status,
        "evidence_ids": [f"EV-{criterion_id.upper().replace('.', '_')}"] if status == "confirmed" else [],
    }


def candidate(segment: str, confirmed: list[str], statuses: dict[str, str] | None = None, exclusion_status: str = "eligible") -> dict:
    status_map = {criterion_id: "confirmed" for criterion_id in confirmed}
    status_map.update(statuses or {})
    return {
        "segment": segment,
        "qualification": {
            "criteria": [criterion(criterion_id, status) for criterion_id, status in status_map.items()],
            "exclusion_status": exclusion_status,
        },
    }


def assert_scored(label: str, result: dict, score: int, band: str, outcome: str) -> None:
    scoring = result["scoring"]
    audit = result["audit"]
    if scoring["status"] != "scored" or scoring["score"] != score or scoring["band"] != band or audit["outcome"] != outcome:
        raise AssertionError(
            f"{label}: expected scored {score}/{band}/{outcome}, received "
            f"{scoring['status']} {scoring['score']}/{scoring['band']}/{audit['outcome']}"
        )
    if sum(item["points_awarded"] for item in scoring["components"]) != score:
        raise AssertionError(f"{label}: components do not sum to numeric score.")
    schema_errors = list(scoring_schema_validator().iter_errors(scoring))
    if schema_errors:
        raise AssertionError(f"{label}: scoring output violates Candidate Schema: {schema_errors[0].message}")
    print(f"PASS: {label}")


def assert_blocked(label: str, result: dict, outcome: str) -> None:
    if result["scoring"]["status"] != "blocked" or result["audit"]["outcome"] != outcome:
        raise AssertionError(f"{label}: expected blocked/{outcome}, received {result}")
    schema_errors = list(scoring_schema_validator().iter_errors(result["scoring"]))
    if schema_errors:
        raise AssertionError(f"{label}: blocked scoring output violates Candidate Schema: {schema_errors[0].message}")
    print(f"PASS: {label}")


def main() -> int:
    model = validator.load_yaml(MODEL_PATH)
    icp = validator.load_yaml(ICP_PATH)
    errors = validator.validate_model(model, icp)
    if errors:
        raise AssertionError(f"Current scoring model should be valid: {errors}")
    print("PASS: current scoring model")

    farrier_weights = list(model["segments"]["farrier"]["positive_weights"])
    owner_weights = list(model["segments"]["horse_owner"]["positive_weights"])

    assert_scored(
        "ideal Farrier",
        calculator.calculate(candidate("farrier", farrier_weights), model),
        100, "high", "high_priority_farrier"
    )

    farrier_medium = [
        "farrier.professional_activity",
        "farrier.product_usage_or_influence",
        "farrier.product_fit",
        "farrier.regular_business_activity",
    ]
    assert_scored(
        "medium Farrier",
        calculator.calculate(candidate("farrier", farrier_medium), model),
        55, "medium", "qualified_farrier"
    )

    apprentice = candidate("farrier", farrier_weights + ["farrier.apprentice_future_potential"])
    assert_scored(
        "apprentice capped at Low",
        calculator.calculate(apprentice, model),
        100, "low", "future_potential_human_review"
    )

    blocked_farrier = candidate("farrier", ["farrier.no_professional_evidence"], exclusion_status="excluded")
    assert_blocked(
        "Farrier exclusion",
        calculator.calculate(blocked_farrier, model),
        "excluded_no_professional_evidence"
    )

    assert_scored(
        "ideal Horse Owner",
        calculator.calculate(candidate("horse_owner", owner_weights), model),
        100, "high", "high_priority_horse_owner"
    )

    owner_without_count = [criterion_id for criterion_id in owner_weights if criterion_id != "horse_owner.more_than_three_horses"]
    unknown_count = candidate(
        "horse_owner",
        owner_without_count,
        {"horse_owner.more_than_three_horses": "unknown"},
    )
    assert_scored(
        "unknown horse count with strong signals",
        calculator.calculate(unknown_count, model),
        80, "medium", "horse_count_unknown_human_review"
    )

    below_count = candidate(
        "horse_owner",
        owner_without_count,
        {"horse_owner.more_than_three_horses": "contradicted"},
    )
    assert_scored(
        "at or below three with strong signals",
        calculator.calculate(below_count, model),
        80, "low", "below_threshold_commercial_exception_review"
    )

    insufficient = candidate(
        "horse_owner",
        ["horse_owner.commercial_operation", "horse_owner.product_fit"],
        {"horse_owner.more_than_three_horses": "unknown"},
    )
    assert_scored(
        "unknown horse count without enough strong signals",
        calculator.calculate(insufficient, model),
        35, "unqualified", "insufficient_horse_count_evidence"
    )

    blocked_owner = candidate("horse_owner", ["horse_owner.no_commercial_evidence"], exclusion_status="excluded")
    assert_blocked(
        "Horse Owner exclusion",
        calculator.calculate(blocked_owner, model),
        "excluded_no_commercial_evidence"
    )

    missing_evidence = candidate("farrier", ["farrier.professional_activity"])
    missing_evidence["qualification"]["criteria"][0]["evidence_ids"] = []
    try:
        calculator.calculate(missing_evidence, model)
    except ValueError as exc:
        if "must reference evidence_ids" not in str(exc):
            raise
        print("PASS: confirmed criterion without evidence rejected")
    else:
        raise AssertionError("Confirmed criterion without evidence should be rejected")

    drift = copy.deepcopy(model)
    drift["segments"]["farrier"]["positive_weights"]["farrier.engagement_signal"] = 30
    drift_errors = validator.validate_model(drift, icp)
    if not any("must total 100" in error for error in drift_errors):
        raise AssertionError(f"Farrier weight drift was not rejected: {drift_errors}")
    print("PASS: weight-total regression rejected")

    approval_drift = copy.deepcopy(model)
    approval_drift["approval_record"]["approved_decisions"] = []
    approval_errors = validator.validate_model(approval_drift, icp)
    if not any("eight approved V1 scoring decisions" in error for error in approval_errors):
        raise AssertionError(f"Scoring approval-record regression was not rejected: {approval_errors}")
    print("PASS: Séverine scoring approval record preserved")

    version_drift = copy.deepcopy(model)
    version_drift["model_version"] = "1.1.0-draft.1"
    version_errors = validator.validate_model(version_drift, icp)
    if not any("model_version must be 1.1.0" in error for error in version_errors):
        raise AssertionError(f"Scoring model-version regression was not rejected: {version_errors}")
    print("PASS: scoring model version preserved")

    print("ALL ICP SCORING TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
