#!/usr/bin/env python3
"""Evaluate an A2 field-state snapshot against a Step 3B minimum package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGES = PROFILE_ROOT / "foundations" / "contracts" / "business" / "a2-minimum-data-packages-0.3.0.json"
SATISFIED = "verified"
ALLOWED_STATES = {"verified", "present_unverified", "missing", "unknown", "not_found", "unavailable", "conflict", "error"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(snapshot: dict, packages: dict) -> dict:
    errors: list[str] = []
    segment = snapshot.get("segment")
    package_key=f"{seg...ady"
    package = packages.get("packages", {}).get(package_key)
    if package is None:
        return {
            "fixture_id": snapshot.get("fixture_id"),
            "segment": segment,
            "package": None,
            "package_status": "invalid",
            "data_quality_status": "invalid",
            "workflow_recommendation": "processing_failed",
            "missing_required_fields": [],
            "unsatisfied_contact_requirements": [],
            "documented_exception_fields": [],
            "conflict_field_keys": snapshot.get("conflict_field_keys", []),
            "error_field_keys": snapshot.get("error_field_keys", []),
            "automatic_rejection": False,
            "automatic_a1_score_change": False,
            "external_action_authorized": False,
            "human_review_required": True,
            "errors": [f"unknown segment {segment!r}"],
        }

    field_states = snapshot.get("field_states")
    if not isinstance(field_states, dict):
        field_states = {}
        errors.append("field_states must be an object")
    for key, state in field_states.items():
        if state not in ALLOWED_STATES:
            errors.append(f"unsupported field state {state!r} for {key}")

    contact_path_name = snapshot.get("contact_path")
    contact_path = package["contact_paths"].get(contact_path_name)
    if contact_path is None:
        errors.append(f"unsupported contact path {contact_path_name!r}")
        contact_path = {"required_verified_fields": [], "at_least_one_verified_field": []}

    missing_required = [key for key in package["required_verified_fields"] if field_states.get(key) != SATISFIED]
    missing_required.extend(key for key in contact_path.get("required_verified_fields", []) if field_states.get(key) != SATISFIED)
    missing_required = sorted(set(missing_required))

    unsatisfied_contact = []
    contact_options = contact_path.get("at_least_one_verified_field", [])
    if contact_options and not any(field_states.get(key) == SATISFIED for key in contact_options):
        unsatisfied_contact = list(contact_options)
    preferred_missing = [
        key for key in contact_path.get("preferred_verified_fields", [])
        if field_states.get(key) != SATISFIED
    ]
    contact_path_incomplete = contact_path.get("review_ready_allowed") is False

    for flag, expected in contact_path.get("required_flags", {}).items():
        if snapshot.get(flag) != expected:
            errors.append(f"required flag {flag} must be {expected!r}")

    conflicts = sorted(set(snapshot.get("conflict_field_keys", [])))
    technical_errors = sorted(set(snapshot.get("error_field_keys", [])))
    research_exhausted = snapshot.get("research_exhausted") is True

    if errors and (package_key not in packages.get("packages", {}) or segment not in {"farrier", "horse_owner"}):
        package_status = "invalid"
        quality = "invalid"
        workflow = "processing_failed"
    elif conflicts:
        package_status = "needs_review"
        quality = "conflict"
        workflow = "held"
    elif technical_errors:
        package_status = "needs_review"
        quality = "error"
        workflow = "processing_failed"
    elif missing_required or unsatisfied_contact or contact_path_incomplete or errors:
        package_status = "incomplete"
        quality = "incomplete"
        if research_exhausted:
            workflow = contact_path.get(
                "research_exhausted_workflow",
                packages.get("global_rules", {}).get("research_exhausted_with_gap_workflow", "review_required"),
            )
        else:
            workflow = "enrichment_in_progress"
    else:
        package_status = "review_ready"
        quality = "review_ready"
        workflow = "review_required"

    return {
        "fixture_id": snapshot.get("fixture_id"),
        "segment": segment,
        "package": package_key,
        "package_status": package_status,
        "data_quality_status": quality,
        "workflow_recommendation": workflow,
        "missing_required_fields": missing_required,
        "unsatisfied_contact_requirements": unsatisfied_contact,
        "preferred_missing_fields": preferred_missing,
        "documented_exception_fields": contact_path.get("documented_exception_fields", []) if contact_path_name == "general_organisation_fallback" else [],
        "conflict_field_keys": conflicts,
        "error_field_keys": technical_errors,
        "automatic_rejection": False,
        "automatic_a1_score_change": False,
        "external_action_authorized": False,
        "human_review_required": True,
        "review_queue_label": contact_path.get("review_label"),
        "human_dispositions": packages.get("global_rules", {}).get("human_dispositions", []),
        "outreach_readiness_status": packages["outreach_readiness_boundary"]["current_status"],
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--packages", type=Path, default=DEFAULT_PACKAGES)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(load(args.snapshot), load(args.packages))
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if result["package_status"] == "invalid" else 0


if __name__ == "__main__":
    raise SystemExit(main())
