#!/usr/bin/env python3
"""Regression tests for the Equinet A1 Prospect Candidate V1 draft contract."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
EXAMPLES = SKILL_DIR / "references" / "examples"
VALIDATOR_PATH = SKILL_DIR / "scripts" / "validate_candidate.py"

spec = importlib.util.spec_from_file_location("candidate_validator", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_data(data: dict) -> int:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
        json.dump(data, handle, indent=2)
        candidate_path = Path(handle.name)
    try:
        return validator.validate(validator.DEFAULT_SCHEMA, candidate_path)
    finally:
        candidate_path.unlink(missing_ok=True)


def expect(label: str, actual: int, expected: int) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected exit {expected}, received {actual}")
    print(f"PASS: {label}")


def main() -> int:
    farrier_path = EXAMPLES / "valid-farrier-synthetic.json"
    owner_path = EXAMPLES / "valid-horse-owner-synthetic.json"
    invalid_path = EXAMPLES / "invalid-missing-evidence.json"

    expect("valid Farrier", validator.validate(validator.DEFAULT_SCHEMA, farrier_path), 0)
    expect("valid Horse Owner", validator.validate(validator.DEFAULT_SCHEMA, owner_path), 0)
    expect("incomplete candidate rejected", validator.validate(validator.DEFAULT_SCHEMA, invalid_path), 1)

    base = load(farrier_path)

    score_mismatch = copy.deepcopy(base)
    score_mismatch["scoring"]["score"] = 99
    expect("score/component mismatch rejected", validate_data(score_mismatch), 1)

    unknown_source = copy.deepcopy(base)
    unknown_source["source_evidence"][0]["source_policy_status"] = "unknown"
    expect("unknown evidence cannot confirm or score", validate_data(unknown_source), 1)

    approval_without_reviewer = copy.deepcopy(base)
    approval_without_reviewer["workflow"]["review_decision"] = "approved"
    approval_without_reviewer["workflow"]["stage"] = "approved_for_a2"
    expect("approval without reviewer rejected", validate_data(approval_without_reviewer), 1)

    synced_without_references = copy.deepcopy(base)
    synced_without_references["workflow"]["review_decision"] = "approved"
    synced_without_references["workflow"]["reviewer"] = {
        "actor_id": "reviewer-test",
        "actor_role": "A1 Business Reviewer",
        "display_name": "Synthetic Reviewer"
    }
    synced_without_references["workflow"]["decision_at"] = "2026-08-11T12:00:00Z"
    synced_without_references["workflow"]["stage"] = "synced"
    expect("synced state without system references rejected", validate_data(synced_without_references), 1)

    wrong_segment_type = copy.deepcopy(base)
    wrong_segment_type["prospect_type"] = "breeding_farm"
    expect("Farrier with Horse Owner type rejected", validate_data(wrong_segment_type), 1)

    person_without_company = copy.deepcopy(base)
    person_without_company["system_references"].update({
        "twenty_company_id": None,
        "twenty_person_id": "person-1",
        "twenty_person_relation_status": "verified",
    })
    expect("Twenty Person without Company rejected", validate_data(person_without_company), 1)

    linked_person = copy.deepcopy(base)
    linked_person["system_references"].update({
        "twenty_company_id": "company-1",
        "twenty_person_id": "person-1",
        "twenty_person_relation_status": "verified",
    })
    expect("verified Twenty Company-Person relation accepted", validate_data(linked_person), 0)

    print("ALL CONTRACT TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
