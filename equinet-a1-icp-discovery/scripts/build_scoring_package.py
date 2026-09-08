#!/usr/bin/env python3
"""Invoke deterministic ICP scoring and build a schema-validated explanation package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


PROFILE_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = PROFILE_DIR / "skills" / "icp-scoring-and-rationale"
PACKAGE_SCHEMA = SKILL_DIR / "references" / "scoring-package.schema.json"
SCORING_MODEL = PROFILE_DIR / "configurations" / "scoring" / "icp-scoring-model-v1.yaml"
CANDIDATE_SCHEMA = PROFILE_DIR / "skills" / "a1-prospect-data-contract" / "references" / "prospect-candidate.schema.json"
SCRIPTS_DIR = PROFILE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from calculate_icp_score import calculate as calculate_icp  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Candidate input must be an object.")
    return data


def confidence_interpretation(scoring: dict[str, Any], confidence: dict[str, Any] | None) -> str:
    if scoring.get("status") == "blocked":
        return "ICP scoring is blocked; evidence confidence does not override the exclusion or authorise priority treatment."
    if confidence is None:
        return "Confidence has not been calculated; do not treat the ICP result as fully validated."
    band = scoring.get("band")
    level = confidence.get("level")
    if band == "high" and level == "low":
        return "High commercial fit with Low evidence confidence: potentially attractive, but more evidence is required before priority treatment."
    if band == "high" and level == "high":
        return "High commercial fit with High evidence confidence: attractive and well-supported for human review."
    if band in {"low", "unqualified"} and level == "high":
        return "The candidate is well documented but has low commercial fit under the approved ICP model."
    return f"ICP band {band}; evidence confidence {level}. Review both values together."


def build(candidate: dict[str, Any]) -> dict[str, Any]:
    with SCORING_MODEL.open("r", encoding="utf-8") as handle:
        model = yaml.safe_load(handle)
    result = calculate_icp(candidate, model)
    scoring = result["scoring"]
    audit = result["audit"]

    candidate_schema = load_json(CANDIDATE_SCHEMA)
    scoring_wrapper = {"$schema": candidate_schema["$schema"], "$ref": "#/$defs/scoring", "$defs": candidate_schema["$defs"]}
    errors = list(Draft202012Validator(scoring_wrapper).iter_errors(scoring))
    if errors:
        raise ValueError("Scoring output violates Candidate Schema: " + errors[0].message)

    segment = candidate.get("segment")
    weights = model["segments"][segment]["positive_weights"]
    qualification = candidate.get("qualification", {})
    statuses = {item["criterion_id"]: item["status"] for item in qualification.get("criteria", [])}
    unearned = [] if scoring["status"] == "blocked" else [
        criterion_id for criterion_id in weights if statuses.get(criterion_id) != "confirmed"
    ]
    confirmed = [
        {"criterion_id": item["criterion_id"], "points": int(item["points_awarded"]), "evidence_ids": item["evidence_ids"]}
        for item in scoring.get("components", [])
    ]
    band_rules = [f"{item['outcome']}: maximum {item['maximum_band']} — {item['reason']}" for item in audit.get("applied_band_caps", [])]

    confidence = candidate.get("confidence")
    confidence_context = None
    if isinstance(confidence, dict) and all(key in confidence for key in ("level", "score", "method_version")):
        confidence_context = {key: confidence[key] for key in ("level", "score", "method_version")}

    if scoring["status"] == "blocked":
        summary = f"ICP scoring is blocked: {scoring['block_reason']}"
    else:
        summary = (
            f"ICP score {scoring['score']}/100; final band {scoring['band']}. "
            f"{len(confirmed)} weighted criteria earned points. Outcome: {audit['outcome']}."
        )

    package = {
        "scoring": scoring,
        "audit": audit,
        "explanation": {
            "summary": summary,
            "confirmed_criteria": confirmed,
            "unearned_weighted_criteria": unearned,
            "applied_band_rules": band_rules,
            "outcome": audit["outcome"],
            "review_required": bool(audit["review_required"]),
            "confidence_interpretation": confidence_interpretation(scoring, confidence_context),
        },
        "confidence_context": confidence_context,
    }

    schema = load_json(PACKAGE_SCHEMA)
    package_errors = list(Draft202012Validator(schema).iter_errors(package))
    if package_errors:
        raise ValueError("Scoring package is invalid: " + package_errors[0].message)
    return package


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        package = build(load_json(args.candidate))
    except Exception as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    rendered = json.dumps(package, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
