#!/usr/bin/env python3
"""Deterministically calculate A1 candidate evidence confidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


PROFILE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = PROFILE_DIR / "configurations" / "evidence" / "evidence-confidence-rules-v1.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("Policy root must be a mapping.")
    return data


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Assessment root must be an object.")
    return data


def confidence_level(score: int, bands: dict[str, Any]) -> str:
    for level in ("high", "medium", "low"):
        band = bands[level]
        if band["minimum"] <= score <= band["maximum"]:
            return level
    raise ValueError(f"Score {score} does not fit a configured confidence band.")


def calculate(assessment: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    model = policy["confidence_model"]
    expected_method = model["method_version"]
    supplied_method = assessment.get("method_version")
    if supplied_method not in (None, expected_method):
        raise ValueError(f"Assessment method_version must be {expected_method!r}.")

    dimensions = assessment.get("dimensions")
    gates = assessment.get("gates")
    if not isinstance(dimensions, dict) or not isinstance(gates, dict):
        raise ValueError("Assessment must contain dimensions and gates objects.")

    required_dimensions = set(policy["confidence_assessment_input"]["required_dimensions"])
    required_gates = set(policy["confidence_assessment_input"]["required_gates"])
    if set(dimensions) != required_dimensions:
        raise ValueError(f"Dimension keys must be exactly: {sorted(required_dimensions)}")
    if set(gates) != required_gates:
        raise ValueError(f"Gate keys must be exactly: {sorted(required_gates)}")
    if any(not isinstance(value, bool) for value in gates.values()):
        raise ValueError("All gate values must be booleans.")

    invalidating = model["invalidating_gates"]
    invalid_reasons = [invalidating[key] for key in invalidating if gates.get(key)]
    if invalid_reasons:
        raise ValueError("Invalid confidence assessment: " + " | ".join(invalid_reasons))

    dimension_scores: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []
    raw_score = 0
    for dimension_name, dimension_config in model["dimensions"].items():
        selected_level = dimensions[dimension_name]
        levels = dimension_config["levels"]
        if selected_level not in levels:
            raise ValueError(
                f"Invalid level {selected_level!r} for {dimension_name}; expected one of {sorted(levels)}"
            )
        points = int(levels[selected_level])
        raw_score += points
        dimension_scores[dimension_name] = {
            "level": selected_level,
            "points": points,
            "maximum": int(dimension_config["max_points"]),
        }
        reasons.append(f"{dimension_name}: {selected_level} ({points}/{dimension_config['max_points']})")

    adjusted_score = raw_score
    applied_caps: list[dict[str, Any]] = []
    limitations: list[str] = []
    for gate_name, cap in model["score_caps"].items():
        if gates.get(gate_name):
            maximum = int(cap["maximum_score"])
            adjusted_score = min(adjusted_score, maximum)
            applied_caps.append({"gate": gate_name, "maximum_score": maximum, "reason": cap["reason"]})
            limitations.append(cap["reason"])

    level = confidence_level(adjusted_score, model["bands"])
    if not limitations:
        limitations.append("No confidence score cap was triggered.")

    return {
        "confidence": {
            "level": level,
            "score": adjusted_score,
            "method_version": expected_method,
            "reasons": reasons,
            "limitations": limitations,
        },
        "audit": {
            "raw_score": raw_score,
            "adjusted_score": adjusted_score,
            "dimension_scores": dimension_scores,
            "applied_caps": applied_caps,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("assessment", type=Path)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        result = calculate(load_json(args.assessment), load_yaml(args.policy))
    except Exception as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
