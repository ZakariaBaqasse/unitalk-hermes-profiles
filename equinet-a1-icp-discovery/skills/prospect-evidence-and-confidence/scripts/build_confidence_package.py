#!/usr/bin/env python3
"""Validate a rich confidence assessment and invoke the deterministic calculator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


SKILL_DIR = Path(__file__).resolve().parents[1]
PROFILE_DIR = Path(__file__).resolve().parents[3]
ASSESSMENT_SCHEMA = SKILL_DIR / "references" / "confidence-assessment.schema.json"
POLICY_PATH = PROFILE_DIR / "configurations" / "evidence" / "evidence-confidence-rules-v1.yaml"
CANDIDATE_SCHEMA = PROFILE_DIR / "skills" / "a1-prospect-data-contract" / "references" / "prospect-candidate.schema.json"
SCRIPTS_DIR = PROFILE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from calculate_candidate_confidence import calculate as calculate_confidence  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Assessment must be an object.")
    return data


def build(assessment: dict[str, Any]) -> dict[str, Any]:
    schema = load_json(ASSESSMENT_SCHEMA)
    errors = list(Draft202012Validator(schema).iter_errors(assessment))
    if errors:
        raise ValueError("Invalid rich confidence assessment: " + " | ".join(error.message for error in errors))

    with POLICY_PATH.open("r", encoding="utf-8") as handle:
        policy = yaml.safe_load(handle)
    available = set(assessment["available_evidence_ids"])
    for name, value in assessment["dimensions"].items():
        unknown = set(value["evidence_ids"]) - available
        if unknown:
            raise ValueError(f"Dimension {name} references unavailable evidence IDs: {sorted(unknown)}")
    for name, value in assessment["gates"].items():
        unknown = set(value["evidence_ids"]) - available
        if unknown:
            raise ValueError(f"Gate {name} references unavailable evidence IDs: {sorted(unknown)}")

    missing = assessment["confidence_stage_missing_fields"]
    minimum_gate = assessment["gates"]["minimum_data_failed"]["value"]
    if minimum_gate != bool(missing):
        raise ValueError("minimum_data_failed gate must equal whether confidence_stage_missing_fields is non-empty.")

    configured_dimensions = policy["confidence_model"]["dimensions"]
    simple_dimensions: dict[str, str] = {}
    for name, value in assessment["dimensions"].items():
        level = value["level"]
        if level not in configured_dimensions[name]["levels"]:
            raise ValueError(f"Invalid level {level!r} for dimension {name}.")
        simple_dimensions[name] = level
    simple_gates = {name: value["value"] for name, value in assessment["gates"].items()}

    result = calculate_confidence({
        "method_version": assessment["method_version"],
        "dimensions": simple_dimensions,
        "gates": simple_gates,
    }, policy)

    confidence = result["confidence"]
    if simple_dimensions["corroboration"] == "one_strong_source":
        extra = "Confidence relies on one strong primary source; external claims remain subject to targeted verification."
        if extra not in confidence["limitations"]:
            confidence["limitations"].append(extra)

    candidate_schema = load_json(CANDIDATE_SCHEMA)
    wrapper = {"$schema": candidate_schema["$schema"], "$ref": "#/$defs/confidence", "$defs": candidate_schema["$defs"]}
    confidence_errors = list(Draft202012Validator(wrapper).iter_errors(confidence))
    if confidence_errors:
        raise ValueError("Confidence output violates Candidate Schema: " + confidence_errors[0].message)

    return {
        "assessment": assessment,
        "confidence": confidence,
        "audit": {
            **result["audit"],
            "confidence_stage_missing_fields": missing,
            "available_evidence_ids": assessment["available_evidence_ids"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("assessment", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = build(load_json(args.assessment))
    except Exception as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
