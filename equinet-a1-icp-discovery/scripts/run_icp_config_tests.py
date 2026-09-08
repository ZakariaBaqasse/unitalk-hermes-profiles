#!/usr/bin/env python3
"""Regression tests for the Equinet A1 ICP configuration."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


PROFILE_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = PROFILE_DIR / "scripts" / "validate_icp_config.py"
CONFIG_PATH = PROFILE_DIR / "configurations" / "icp" / "equinet-icp-v1.yaml"

spec = importlib.util.spec_from_file_location("icp_validator", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


def expect_valid(label: str, data: dict) -> None:
    errors = validator.validate_config(data)
    if errors:
        raise AssertionError(f"{label} should be valid: {errors}")
    print(f"PASS: {label}")


def expect_invalid(label: str, data: dict, expected_text: str) -> None:
    errors = validator.validate_config(data)
    if not errors:
        raise AssertionError(f"{label} should be invalid")
    if not any(expected_text in error for error in errors):
        raise AssertionError(f"{label} did not produce expected error {expected_text!r}: {errors}")
    print(f"PASS: {label}")


def main() -> int:
    base = validator.load_yaml(CONFIG_PATH)
    expect_valid("current ICP configuration", base)

    wrong_threshold = copy.deepcopy(base)
    wrong_threshold["segments"]["horse_owner"]["horse_count_rule"]["value"] = 5
    expect_invalid("wrong Horse Owner threshold rejected", wrong_threshold, "greater_than 3")

    scoring_weight = copy.deepcopy(base)
    scoring_weight["segments"]["farrier"]["criteria"][0]["weight"] = 20
    expect_invalid("scoring weight rejected", scoring_weight, "Forbidden scoring key")

    duplicate_criterion = copy.deepcopy(base)
    duplicate_criterion["segments"]["horse_owner"]["criteria"][0]["criterion_id"] = \
        duplicate_criterion["segments"]["farrier"]["criteria"][0]["criterion_id"]
    expect_invalid("duplicate criterion rejected", duplicate_criterion, "unique")

    missing_segment = copy.deepcopy(base)
    del missing_segment["segments"]["horse_owner"]
    expect_invalid("missing Horse Owner segment rejected", missing_segment, "exactly farrier and horse_owner")

    contacts_disallowed = copy.deepcopy(base)
    contacts_disallowed["shared_rules"]["public_professional_contact_retention"]["allowed"] = False
    expect_invalid("public contact decision regression rejected", contacts_disallowed, "must be allowed")

    wrong_priority = copy.deepcopy(base)
    wrong_priority["operating_scope"]["segment_priority"][0]["priority"] = "secondary"
    expect_invalid("Farrier pilot priority regression rejected", wrong_priority, "Farrier must be primary")

    lost_approval = copy.deepcopy(base)
    lost_approval["approval_record"]["validated_decisions"] = []
    expect_invalid("loss of Séverine approval record rejected", lost_approval, "five validated V1 decisions")

    print("ALL ICP CONFIG TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
