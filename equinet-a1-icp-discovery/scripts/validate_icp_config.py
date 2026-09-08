#!/usr/bin/env python3
"""Validate the Equinet A1 ICP configuration and its separation from scoring."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "configurations" / "icp" / "equinet-icp-v1.yaml"
CRITERION_ID = re.compile(r"^[a-z0-9][a-z0-9_.-]{2,99}$")
ALLOWED_CATEGORIES = {"fit", "priority", "negative", "exclusion"}
ALLOWED_EFFECTS = {
    "required_for_standard_qualification",
    "qualification_support",
    "priority_signal",
    "future_potential_pathway",
    "negative_signal",
    "exclusion",
}
FORBIDDEN_SCORING_KEYS = {"weight", "weights", "points", "max_points", "score_band", "qualification_threshold"}
REQUIRED_TOP_LEVEL = {
    "config_id",
    "config_version",
    "status",
    "client_approval",
    "applies_to_profile",
    "candidate_schema_version",
    "approval_record",
    "operating_scope",
    "shared_rules",
    "classification_outcomes",
    "exclusion_rules",
    "segments",
    "minimum_review_requirements",
    "scoring_boundary",
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("Configuration root must be a mapping.")
    return data


def walk_keys(value: Any, path: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            current = f"{path}.{key}" if path else str(key)
            yield current, str(key)
            yield from walk_keys(child, current)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_keys(child, f"{path}[{index}]")


def validate_config(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    missing = sorted(REQUIRED_TOP_LEVEL - set(data))
    if missing:
        errors.append(f"Missing top-level keys: {', '.join(missing)}")

    if data.get("config_version") != "2.0.0":
        errors.append("config_version must be 2.0.0.")
    if data.get("status") != "approved_for_production_configuration":
        errors.append("status must record production approval.")
    if data.get("candidate_schema_version") != "1.0.0":
        errors.append("candidate_schema_version must be 1.0.0.")
    if data.get("applies_to_profile") != "equinet-a1-icp-discovery":
        errors.append("Configuration must apply to equinet-a1-icp-discovery.")
    approval = data.get("approval_record", {})
    if approval.get("approved_by") != "Séverine" or len(approval.get("validated_decisions", [])) != 5:
        errors.append("approval_record must preserve Séverine's five validated V1 decisions.")

    scope = data.get("operating_scope", {})
    countries = scope.get("country_scope", {}).get("included_country_codes", [])
    if countries != ["US", "AU", "NZ"]:
        errors.append("Production country scope must be exactly [US, AU, NZ].")
    geography = scope.get("search_geography", {})
    if geography.get("required_user_fields") != ["country", "region", "city"]:
        errors.append("Production geography must require country, region and city.")
    if any(geography.get(key) is not None for key in ("default_country", "default_region", "default_city")):
        errors.append("Production geography must not define location defaults.")
    if geography.get("code_resolution") != "deterministic_approved_mapping_only":
        errors.append("Country and region codes must use deterministic approved mappings.")
    priority = scope.get("segment_priority", [])
    priority_map = {item.get("segment"): item.get("priority") for item in priority if isinstance(item, dict)}
    if priority_map.get("farrier") != "primary" or priority_map.get("horse_owner") != "secondary":
        errors.append("Farrier must be primary and Horse Owner secondary.")

    segments = data.get("segments", {})
    if set(segments) != {"farrier", "horse_owner"}:
        errors.append("segments must contain exactly farrier and horse_owner.")

    all_ids: list[str] = []
    for segment_name in ("farrier", "horse_owner"):
        segment = segments.get(segment_name, {})
        if not segment.get("target_prospect_types"):
            errors.append(f"{segment_name} must define target_prospect_types.")
        criteria = segment.get("criteria", [])
        if not criteria:
            errors.append(f"{segment_name} must define criteria.")
        for index, criterion in enumerate(criteria):
            criterion_id = criterion.get("criterion_id")
            all_ids.append(criterion_id)
            if not isinstance(criterion_id, str) or not CRITERION_ID.fullmatch(criterion_id):
                errors.append(f"{segment_name}.criteria[{index}] has an invalid criterion_id.")
            elif not criterion_id.startswith(f"{segment_name}."):
                errors.append(f"{criterion_id} must start with {segment_name}.")
            if criterion.get("category") not in ALLOWED_CATEGORIES:
                errors.append(f"{criterion_id} has invalid category {criterion.get('category')!r}.")
            if criterion.get("effect") not in ALLOWED_EFFECTS:
                errors.append(f"{criterion_id} has invalid effect {criterion.get('effect')!r}.")
            if not criterion.get("provenance"):
                errors.append(f"{criterion_id} is missing provenance.")

    if len(all_ids) != len(set(all_ids)):
        errors.append("criterion_id values must be unique across both segments.")

    horse_rule = segments.get("horse_owner", {}).get("horse_count_rule", {})
    if horse_rule.get("operator") != "greater_than" or horse_rule.get("value") != 3:
        errors.append("Horse Owner V1 threshold must be greater_than 3.")

    contacts = data.get("shared_rules", {}).get("public_professional_contact_retention", {})
    if contacts.get("allowed") is not True or not contacts.get("conditions"):
        errors.append("Public professional contact retention must be allowed with conditions.")

    scoring = data.get("scoring_boundary", {})
    if any(scoring.get(key) is not False for key in ("weights_defined_here", "score_bands_defined_here", "qualification_threshold_defined_here")):
        errors.append("Numeric scoring rules must remain outside the ICP configuration.")

    for full_path, key in walk_keys(data):
        if key in FORBIDDEN_SCORING_KEYS:
            errors.append(f"Forbidden scoring key in ICP configuration: {full_path}")

    requirements = data.get("minimum_review_requirements", {})
    if not requirements.get("required_paths") or not requirements.get("structural_rules"):
        errors.append("minimum_review_requirements must define required paths and structural rules.")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", nargs="?", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()

    try:
        data = load_yaml(args.config)
    except Exception as exc:
        print(f"INVALID: {args.config}\n- {exc}")
        return 1

    errors = validate_config(data)
    if errors:
        print(f"INVALID: {args.config}")
        for error in errors:
            print(f"- {error}")
        return 1

    criterion_count = sum(len(segment["criteria"]) for segment in data["segments"].values())
    print(f"VALID: {args.config}")
    print(f"Segments: {', '.join(data['segments'])}")
    print(f"Criteria: {criterion_count}")
    print("Scoring weights present: no")
    return 0


if __name__ == "__main__":
    sys.exit(main())
