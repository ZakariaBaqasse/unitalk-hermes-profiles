#!/usr/bin/env python3
"""Build a complete schema-compatible Equinet A1 qualification object."""

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
INPUT_SCHEMA = SKILL_DIR / "references" / "qualification-assessment.schema.json"
ICP_CONFIG = PROFILE_DIR / "configurations" / "icp" / "equinet-icp-v1.yaml"
CANDIDATE_SCHEMA = PROFILE_DIR / "skills" / "a1-prospect-data-contract" / "references" / "prospect-candidate.schema.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Qualification assessment must be an object.")
    return data


def validate_json(instance: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    return [error.message for error in Draft202012Validator(schema).iter_errors(instance)]


def build(assessment: dict[str, Any], icp: dict[str, Any]) -> dict[str, Any]:
    input_schema = load_json(INPUT_SCHEMA)
    input_errors = validate_json(assessment, input_schema)
    if input_errors:
        raise ValueError("Invalid qualification assessment: " + " | ".join(input_errors))

    segment = assessment["segment"]
    segment_config = icp["segments"].get(segment)
    if segment_config is None:
        raise ValueError(f"Unsupported segment {segment!r}.")
    configured = {item["criterion_id"]: item for item in segment_config["criteria"]}
    supplied = assessment["criterion_assessments"]
    unknown_ids = sorted(set(supplied) - set(configured))
    if unknown_ids:
        raise ValueError(f"Unknown criterion IDs for {segment}: {unknown_ids}")

    criteria: list[dict[str, Any]] = []
    exclusion_reasons: list[str] = []
    required_gate_statuses: dict[str, str] = {}
    special_pathways: list[str] = []

    for criterion_id, rule in configured.items():
        value = supplied.get(criterion_id, {"status": "unknown", "evidence_ids": [], "notes": None})
        status = value["status"]
        evidence_ids = value["evidence_ids"]
        if status == "confirmed" and not evidence_ids:
            raise ValueError(f"Confirmed criterion {criterion_id!r} requires evidence_ids.")
        criteria.append({
            "criterion_id": criterion_id,
            "criterion_label": rule["label"],
            "category": rule["category"],
            "status": status,
            "evidence_ids": evidence_ids,
            "notes": value["notes"],
        })
        if rule["effect"] == "required_for_standard_qualification":
            required_gate_statuses[criterion_id] = status
        if rule["effect"] == "future_potential_pathway" and status == "confirmed":
            special_pathways.append(criterion_id)
        if rule["effect"] == "exclusion" and status == "confirmed":
            exclusion_reasons.append(rule["label"])

    missing = assessment["missing_minimum_fields"]
    qualification = {
        "icp_config_version": icp["config_version"],
        "criteria": criteria,
        "minimum_data_status": "pass" if not missing else "fail",
        "missing_minimum_fields": missing,
        "exclusion_status": "excluded" if exclusion_reasons else "eligible",
        "exclusion_reasons": exclusion_reasons,
    }

    candidate_schema = load_json(CANDIDATE_SCHEMA)
    wrapper = {
        "$schema": candidate_schema["$schema"],
        "$ref": "#/$defs/qualification",
        "$defs": candidate_schema["$defs"],
    }
    output_errors = validate_json(qualification, wrapper)
    if output_errors:
        raise ValueError("Qualification output violates Candidate Schema: " + " | ".join(output_errors))

    return {
        "qualification": qualification,
        "audit": {
            "segment": segment,
            "required_gate_statuses": required_gate_statuses,
            "special_pathways": special_pathways,
            "criteria_count": len(criteria),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("assessment", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        with ICP_CONFIG.open("r", encoding="utf-8") as handle:
            icp = yaml.safe_load(handle)
        result = build(load_json(args.assessment), icp)
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
