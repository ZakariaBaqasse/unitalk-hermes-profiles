#!/usr/bin/env python3
"""Build representative Step 2H records and review-view packages."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from render_a2_review_views import render_bundle

PROFILE_ROOT = Path(__file__).resolve().parents[1]
STEP2F = PROFILE_ROOT / "evaluations" / "step2f" / "fixtures" / "valid"
ROOT = PROFILE_ROOT / "evaluations" / "step2h"
FIXTURES = ROOT / "fixtures"
SAMPLES = ROOT / "samples"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def main() -> None:
    blocked = copy.deepcopy(load(STEP2F / "farrier-review-required.json"))
    field = next(item for item in blocked["field_assessments"] if item["field_key"] == "person.full_name")
    field["application"] = {
        "status": "blocked",
        "destination": None,
        "external_action_reference": None,
        "workflow_dependency_status": "blocked",
        "applied_at": None,
        "error": {
            "code": "WORKFLOW_DEPENDENCY_BLOCKED",
            "message": "Synthetic workflow dependency blocks application.",
            "retryable": False,
            "occurred_at": "2026-08-26T11:45:00Z",
            "details": ["Synthetic Step 2H blocked-application fixture."],
        },
    }
    blocked_path = FIXTURES / "farrier-application-blocked.json"
    write(blocked_path, blocked)

    samples = [
        ("farrier-review-required", STEP2F / "farrier-review-required.json", STEP2F / "farrier-review-required-previous.json"),
        ("farrier-conflict-held", STEP2F / "farrier-conflict-held.json", STEP2F / "farrier-conflict-held-previous.json"),
        ("horse-owner-requalification", STEP2F / "horse-owner-complete-requalification.json", STEP2F / "horse-owner-complete-requalification-previous.json"),
        ("horse-owner-gap-held", STEP2F / "horse-owner-gap-held.json", STEP2F / "horse-owner-gap-held-previous.json"),
        ("farrier-protected-update", STEP2F / "farrier-protected-update-awaiting-review.json", STEP2F / "farrier-protected-update-awaiting-review-previous.json"),
        ("farrier-application-blocked", blocked_path, STEP2F / "farrier-review-required-previous.json"),
    ]
    results = []
    for name, record, previous in samples:
        manifest = render_bundle(record, SAMPLES / name, previous)
        results.append({"name": name, "record": str(record), "previous": str(previous), "canonical_record_sha256": manifest["canonical_record_sha256"], "row_counts": manifest["row_counts"]})
    print(json.dumps({"sample_count": len(results), "samples": results}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
