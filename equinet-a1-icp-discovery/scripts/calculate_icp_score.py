#!/usr/bin/env python3
"""Deterministically calculate the Equinet A1 ICP score."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


PROFILE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = PROFILE_DIR / "configurations" / "scoring" / "icp-scoring-model-v1.yaml"
VALID_STATUSES = {"confirmed", "not_confirmed", "unknown", "contradicted"}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("Scoring model root must be a mapping.")
    return data


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Scoring input root must be an object.")
    return data


def base_band(score: int, bands: dict[str, Any]) -> str:
    for band in ("high", "medium", "low", "unqualified"):
        rule = bands[band]
        if rule["minimum"] <= score <= rule["maximum"]:
            return band
    raise ValueError(f"Score {score} does not fit any configured band.")


def apply_band_caps(raw_band: str, caps: list[dict[str, str]], order: list[str]) -> str:
    final_index = order.index(raw_band)
    for cap in caps:
        final_index = max(final_index, order.index(cap["maximum_band"]))
    return order[final_index]


def blocked_result(model_version: str, reason: str, outcome: str) -> dict[str, Any]:
    return {
        "scoring": {
            "status": "blocked",
            "score": None,
            "band": None,
            "model_version": model_version,
            "components": [],
            "rationale": None,
            "block_reason": reason,
        },
        "audit": {
            "raw_band": None,
            "final_band": None,
            "applied_band_caps": [],
            "outcome": outcome,
            "review_required": True,
            "confirmed_positive_criteria": [],
            "missing_required_gates": [],
        },
    }


def calculate(candidate: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    segment = candidate.get("segment")
    if segment not in model["segments"]:
        raise ValueError(f"Unsupported segment {segment!r}.")
    qualification = candidate.get("qualification")
    if not isinstance(qualification, dict):
        raise ValueError("Scoring input must contain a qualification object.")
    criteria = qualification.get("criteria")
    if not isinstance(criteria, list):
        raise ValueError("qualification.criteria must be a list.")

    criteria_by_id: dict[str, dict[str, Any]] = {}
    for index, criterion in enumerate(criteria):
        if not isinstance(criterion, dict):
            raise ValueError(f"qualification.criteria[{index}] must be an object.")
        criterion_id = criterion.get("criterion_id")
        status = criterion.get("status")
        if not isinstance(criterion_id, str):
            raise ValueError(f"qualification.criteria[{index}] is missing criterion_id.")
        if criterion_id in criteria_by_id:
            raise ValueError(f"Duplicate criterion_id {criterion_id!r}.")
        if status not in VALID_STATUSES:
            raise ValueError(f"Criterion {criterion_id!r} has invalid status {status!r}.")
        if status == "confirmed" and not criterion.get("evidence_ids"):
            raise ValueError(f"Confirmed criterion {criterion_id!r} must reference evidence_ids.")
        criteria_by_id[criterion_id] = criterion

    model_version = model["model_version"]
    segment_model = model["segments"][segment]
    for criterion_id, meaning in segment_model.get("non_scoring_criteria", {}).items():
        if meaning == "exclusion" and criteria_by_id.get(criterion_id, {}).get("status") == "confirmed":
            rule = next(
                value for value in segment_model["special_rules"].values()
                if value.get("trigger", {}).get("criterion_id") == criterion_id
            )
            return blocked_result(model_version, f"Confirmed exclusion criterion: {criterion_id}.", rule["outcome"])

    if qualification.get("exclusion_status") == "excluded":
        return blocked_result(model_version, "Candidate exclusion_status is excluded.", "excluded")

    components: list[dict[str, Any]] = []
    confirmed_positive: list[str] = []
    score = 0
    for criterion_id, weight in segment_model["positive_weights"].items():
        criterion = criteria_by_id.get(criterion_id, {"status": "unknown", "evidence_ids": []})
        if criterion.get("status") == "confirmed":
            points = int(weight)
            score += points
            confirmed_positive.append(criterion_id)
            components.append({
                "criterion_id": criterion_id,
                "points_awarded": points,
                "max_points": points,
                "evidence_ids": criterion.get("evidence_ids", []),
                "notes": "Full V1 weight awarded for confirmed criterion.",
            })

    raw_band = base_band(score, model["bands"])
    caps: list[dict[str, str]] = []
    missing_gates: list[str] = []

    def add_cap(maximum_band: str, outcome: str, reason: str) -> None:
        caps.append({"maximum_band": maximum_band, "outcome": outcome, "reason": reason})

    if segment == "farrier":
        professional_status = criteria_by_id.get("farrier.professional_activity", {}).get("status", "unknown")
        if professional_status != "confirmed":
            missing_gates.append("farrier.professional_activity")
            add_cap("low", "needs_review_missing_professional_activity", "Professional Farrier activity is not confirmed.")
        if criteria_by_id.get("farrier.apprentice_future_potential", {}).get("status") == "confirmed":
            add_cap("low", "future_potential_human_review", "Active apprentice pathway cannot exceed Low in V1.")
        if criteria_by_id.get("farrier.inactive_or_hobbyist", {}).get("status") == "confirmed":
            add_cap("unqualified", "inactive_or_hobbyist_review", "Inactive or hobby-only signal caps the candidate at Unqualified.")
    else:
        commercial_status = criteria_by_id.get("horse_owner.commercial_operation", {}).get("status", "unknown")
        if commercial_status != "confirmed":
            missing_gates.append("horse_owner.commercial_operation")
            add_cap("unqualified", "needs_review_missing_commercial_operation", "Commercial operation is not confirmed.")

        horse_count_status = criteria_by_id.get("horse_owner.more_than_three_horses", {}).get("status", "unknown")
        strong_signals = segment_model["special_rules"]["horse_count_unknown"]["strong_signal_criteria"]
        confirmed_signal_count = sum(
            criteria_by_id.get(criterion_id, {}).get("status") == "confirmed" for criterion_id in strong_signals
        )
        signal_threshold = int(segment_model["special_rules"]["horse_count_unknown"]["minimum_confirmed_strong_signals"])
        if horse_count_status in {"unknown", "not_confirmed"}:
            missing_gates.append("horse_owner.more_than_three_horses")
            if confirmed_signal_count >= signal_threshold:
                add_cap("medium", "horse_count_unknown_human_review", "Horse count is unknown; strong commercial signals trigger review only.")
            else:
                add_cap("unqualified", "insufficient_horse_count_evidence", "Horse count is unknown and strong-signal threshold is not met.")
        elif horse_count_status == "contradicted":
            missing_gates.append("horse_owner.more_than_three_horses")
            if confirmed_signal_count >= signal_threshold:
                add_cap("low", "below_threshold_commercial_exception_review", "Horse count is at/below threshold or contradicted; exception review only.")
            else:
                add_cap("unqualified", "below_threshold_unqualified", "Horse-count threshold is not met and strong-signal threshold is not met.")

        if criteria_by_id.get("horse_owner.single_horse_recreational", {}).get("status") == "confirmed":
            add_cap("unqualified", "recreational_owner_unqualified", "Single-horse recreational signal caps the candidate at Unqualified.")

    order = model["band_order_from_high_to_low"]
    final_band = apply_band_caps(raw_band, caps, order)
    if caps:
        worst_index = max(order.index(cap["maximum_band"]) for cap in caps)
        primary_outcome = next(cap["outcome"] for cap in caps if order.index(cap["maximum_band"]) == worst_index)
    else:
        primary_outcome = segment_model["standard_outcomes"][final_band]

    cap_text = "; ".join(f"{cap['outcome']} ({cap['reason']})" for cap in caps)
    rationale = (
        f"Numeric ICP score {score}/100 from {len(components)} confirmed weighted criteria. "
        f"Raw band {raw_band}; final band {final_band}."
    )
    if cap_text:
        rationale += f" Applied band rule(s): {cap_text}"

    return {
        "scoring": {
            "status": "scored",
            "score": score,
            "band": final_band,
            "model_version": model_version,
            "components": components,
            "rationale": rationale,
            "block_reason": None,
        },
        "audit": {
            "raw_band": raw_band,
            "final_band": final_band,
            "applied_band_caps": caps,
            "outcome": primary_outcome,
            "review_required": True,
            "confirmed_positive_criteria": confirmed_positive,
            "missing_required_gates": missing_gates,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = calculate(load_json(args.candidate), load_yaml(args.model))
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
