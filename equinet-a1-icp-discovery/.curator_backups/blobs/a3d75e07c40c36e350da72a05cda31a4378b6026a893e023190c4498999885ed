#!/usr/bin/env python3
"""Validate an A1 segment-classification decision against schema and ICP types."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker


SKILL_DIR = Path(__file__).resolve().parents[1]
PROFILE_DIR = Path(__file__).resolve().parents[3]
SCHEMA_PATH = SKILL_DIR / "references" / "classification-decision.schema.json"
ICP_PATH = PROFILE_DIR / "configurations" / "icp" / "equinet-icp-v1.yaml"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Classification decision must be an object.")
    return data


def validate(decision: dict[str, Any]) -> list[str]:
    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [f"/{'/'.join(map(str, error.absolute_path))}: {error.message}" for error in validator.iter_errors(decision)]

    with ICP_PATH.open("r", encoding="utf-8") as handle:
        icp = yaml.safe_load(handle)
    segment = decision.get("segment")
    prospect_type = decision.get("prospect_type")
    if segment in icp["segments"]:
        allowed = set(icp["segments"][segment]["target_prospect_types"])
        if prospect_type not in allowed:
            errors.append(f"prospect_type {prospect_type!r} is not allowed for segment {segment!r}.")
    if decision.get("classification_status") == "needs_review" and not decision.get("unresolved_questions"):
        errors.append("needs_review decisions require at least one unresolved question.")
    if decision.get("classification_status") in {"out_of_scope", "blocked"} and not decision.get("rationale"):
        errors.append("out_of_scope or blocked decisions require a rationale.")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("decision", type=Path)
    args = parser.parse_args()
    try:
        decision = load_json(args.decision)
        errors = validate(decision)
    except Exception as exc:
        print(f"INVALID: {exc}")
        return 1
    if errors:
        print(f"INVALID: {args.decision}")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"VALID: {args.decision}")
    print(f"Segment: {decision.get('segment')}")
    print(f"Prospect type: {decision.get('prospect_type')}")
    print(f"Status: {decision.get('classification_status')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
