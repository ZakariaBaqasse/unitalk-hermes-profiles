#!/usr/bin/env python3
"""Validate the Equinet A1 ICP Scoring Model against the ICP configuration."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


PROFILE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = PROFILE_DIR / "configurations" / "scoring" / "icp-scoring-model-v1.yaml"
DEFAULT_ICP = PROFILE_DIR / "configurations" / "icp" / "equinet-icp-v1.yaml"
EXPECTED_BANDS = {
    "high": {"minimum": 75, "maximum": 100},
    "medium": {"minimum": 50, "maximum": 74},
    "low": {"minimum": 25, "maximum": 49},
    "unqualified": {"minimum": 0, "maximum": 24},
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be a mapping.")
    return data


def validate_model(model: dict[str, Any], icp: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "model_id", "model_version", "status", "applies_to_profile", "candidate_schema_version",
        "icp_config_version", "evidence_confidence_version", "approval_record", "principles", "criterion_status_points",
        "bands", "qualification_threshold", "band_order_from_high_to_low", "common_rules", "segments", "scoring_output"
    }
    missing = sorted(required - set(model))
    if missing:
        errors.append(f"Missing top-level keys: {', '.join(missing)}")
    if model.get("model_version") != "1.1.0":
        errors.append("model_version must be 1.1.0.")
    if model.get("status") != "approved_for_production":
        errors.append("status must record production approval.")
    if model.get("applies_to_profile") != "equinet-a1-icp-discovery":
        errors.append("Scoring model must apply to equinet-a1-icp-discovery.")
    expected_versions = {
        "candidate_schema_version": "1.0.0",
        "icp_config_version": "2.0.0",
        "evidence_confidence_version": "1.2.0",
    }
    if any(model.get(key) != value for key, value in expected_versions.items()):
        errors.append("Scoring model must target Candidate Schema 1.0.0, ICP Configuration 2.0.0 and Evidence/Confidence 1.2.0.")
    approval = model.get("approval_record", {})
    if approval.get("approved_by") != "Séverine" or len(approval.get("approved_decisions", [])) != 8:
        errors.append("approval_record must preserve Séverine's eight approved V1 scoring decisions.")

    bands = model.get("bands", {})
    simplified = {key: {"minimum": value.get("minimum"), "maximum": value.get("maximum")} for key, value in bands.items()}
    if simplified != EXPECTED_BANDS:
        errors.append("Bands must be High 75-100, Medium 50-74, Low 25-49 and Unqualified 0-24.")
    if model.get("qualification_threshold") != 50:
        errors.append("Qualification threshold must be 50 in V1.")
    if model.get("band_order_from_high_to_low") != ["high", "medium", "low", "unqualified"]:
        errors.append("Band order is invalid.")

    if set(model.get("segments", {})) != {"farrier", "horse_owner"}:
        errors.append("Scoring model must contain exactly farrier and horse_owner segments.")

    for segment_name in ("farrier", "horse_owner"):
        segment_model = model.get("segments", {}).get(segment_name, {})
        weights = segment_model.get("positive_weights", {})
        if sum(weights.values()) != 100:
            errors.append(f"{segment_name} positive weights must total 100, received {sum(weights.values())}.")
        if segment_model.get("maximum_positive_points") != 100:
            errors.append(f"{segment_name} maximum_positive_points must be 100.")

        icp_criteria = {item["criterion_id"]: item for item in icp["segments"][segment_name]["criteria"]}
        assigned = set(weights) | set(segment_model.get("non_scoring_criteria", {}))
        if assigned != set(icp_criteria):
            missing_ids = sorted(set(icp_criteria) - assigned)
            extra_ids = sorted(assigned - set(icp_criteria))
            errors.append(f"{segment_name} criterion assignment mismatch; missing={missing_ids}, extra={extra_ids}.")
        for criterion_id in weights:
            criterion = icp_criteria.get(criterion_id, {})
            if criterion.get("effect") not in {"required_for_standard_qualification", "qualification_support", "priority_signal"}:
                errors.append(f"Weighted criterion {criterion_id} has incompatible ICP effect {criterion.get('effect')!r}.")
        if any(not isinstance(value, int) or value <= 0 for value in weights.values()):
            errors.append(f"{segment_name} weights must be positive integers.")

    farrier = model.get("segments", {}).get("farrier", {})
    if farrier.get("positive_weights", {}).get("farrier.professional_activity") != 20:
        errors.append("Farrier professional_activity weight must be 20 in V1.")
    if farrier.get("special_rules", {}).get("apprentice_future_potential", {}).get("maximum_band") != "low":
        errors.append("Farrier apprentice pathway must remain capped at Low.")
    if farrier.get("special_rules", {}).get("inactive_or_hobbyist", {}).get("maximum_band") != "unqualified":
        errors.append("Inactive/hobbyist Farrier must remain capped at Unqualified.")

    owner = model.get("segments", {}).get("horse_owner", {})
    if owner.get("positive_weights", {}).get("horse_owner.commercial_operation") != 25:
        errors.append("Horse Owner commercial_operation weight must be 25 in V1.")
    if owner.get("positive_weights", {}).get("horse_owner.more_than_three_horses") != 20:
        errors.append("Horse Owner more_than_three_horses weight must be 20 in V1.")
    unknown = owner.get("special_rules", {}).get("horse_count_unknown", {})
    below = owner.get("special_rules", {}).get("horse_count_at_or_below_three", {})
    if unknown.get("minimum_confirmed_strong_signals") != 2 or below.get("minimum_confirmed_strong_signals") != 2:
        errors.append("Horse-count exception must require two strong commercial signals.")
    if unknown.get("if_threshold_met", {}).get("maximum_band") != "medium":
        errors.append("Unknown horse count with strong signals must be capped at Medium.")
    if below.get("if_threshold_met", {}).get("maximum_band") != "low":
        errors.append("At/below-three horse count with strong signals must be capped at Low.")

    if model.get("criterion_status_points") != {
        "confirmed": "full_weight",
        "not_confirmed": "zero",
        "unknown": "zero",
        "contradicted": "zero",
    }:
        errors.append("Criterion status point rules must award full weight only to confirmed criteria.")

    overlap = model.get("common_rules", {}).get("overlap_controls", {}).get("farrier_product_usage_and_buying_influence", {})
    if set(overlap.get("criteria", [])) != {"farrier.product_usage_or_influence", "farrier.buying_influence"}:
        errors.append("Farrier product-usage/buying-influence overlap control is missing or invalid.")
    if not overlap.get("award_both_only_when"):
        errors.append("Farrier overlap control must explain when both related criteria may score.")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", nargs="?", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--icp", type=Path, default=DEFAULT_ICP)
    args = parser.parse_args()
    try:
        model = load_yaml(args.model)
        icp = load_yaml(args.icp)
    except Exception as exc:
        print(f"INVALID: {exc}")
        return 1
    errors = validate_model(model, icp)
    if errors:
        print(f"INVALID: {args.model}")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"VALID: {args.model}")
    for segment_name, segment in model["segments"].items():
        print(f"{segment_name}: criteria={len(segment['positive_weights'])}, total={sum(segment['positive_weights'].values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
