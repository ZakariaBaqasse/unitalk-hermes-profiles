#!/usr/bin/env python3
"""Verify the final Step 2I acceptance record and closure state."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROFILE_ROOT / "evaluations" / "step2i"
ACCEPTANCE = ROOT / "acceptance-record.json"
OUTPUT = ROOT / "closure-verification.json"
REVIEW_MANIFEST = ROOT / "review-package-manifest.json"
REVIEW = ROOT / "A2-CANONICAL-DATA-CONTRACT-PROMOTION-REVIEW.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    acceptance = load(ACCEPTANCE)
    failures = []
    references = {
        "schema": (acceptance["schema_path"], acceptance["schema_sha256"]),
        "dependency_manifest": (acceptance["dependency_manifest"], acceptance["dependency_manifest_sha256"]),
        "validator_manifest": (acceptance["validator_manifest"], acceptance["validator_manifest_sha256"]),
        "promotion_manifest": (acceptance["promotion_manifest"], acceptance["promotion_manifest_sha256"]),
        "technical_validation": (acceptance["technical_validation"], acceptance["technical_validation_sha256"]),
        "pre_promotion_snapshot": (acceptance["pre_promotion_snapshot"], acceptance["pre_promotion_snapshot_sha256"]),
    }
    reference_checks = {}
    for name, (relative, expected) in references.items():
        path = PROFILE_ROOT / relative
        actual = sha256(path) if path.exists() else None
        passed = actual == expected
        reference_checks[name] = {"path": relative, "expected": expected, "actual": actual, "passed": passed}
        if not passed:
            failures.append(f"acceptance reference failed: {name}")

    technical = load(PROFILE_ROOT / acceptance["technical_validation"])
    promotion_manifest = load(PROFILE_ROOT / acceptance["promotion_manifest"])
    review_manifest = load(REVIEW_MANIFEST)
    review_entry = next(item for item in review_manifest["files"] if item["path"] == str(REVIEW.relative_to(PROFILE_ROOT)))
    review_preserved = review_entry["sha256"] == sha256(REVIEW)

    state_checks = {
        "decision": acceptance.get("decision") == "approved_and_promoted",
        "schema_version": acceptance.get("schema_version") == "1.0.0",
        "decisions_i1_i10": set(acceptance.get("approved_decisions", {})) == {f"I{number}" for number in range(1, 11)},
        "technical_validation": technical.get("pass") is True and technical.get("approval_state") == "approved_and_promoted",
        "promotion_manifest": promotion_manifest.get("approval_state") == "approved_and_promoted",
        "review_evidence_preserved": review_preserved,
        "next_gate": acceptance.get("next_gate") == "Step 3A — Business Field Catalogue",
        "profile_status": acceptance.get("profile_status") == "FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY",
        "external_actions": acceptance.get("post_promotion_results", {}).get("external_actions") == 0,
        "integrations_activated": acceptance.get("post_promotion_results", {}).get("integrations_activated") == 0,
    }
    for name, passed in state_checks.items():
        if not passed:
            failures.append(f"closure state check failed: {name}")

    result = {
        "step": "2I",
        "status": "closed_approved_and_promoted" if not failures else "closure_failed",
        "acceptance_record": str(ACCEPTANCE.relative_to(PROFILE_ROOT)),
        "acceptance_record_sha256": sha256(ACCEPTANCE),
        "reference_checks": reference_checks,
        "state_checks": state_checks,
        "external_actions": 0,
        "next_gate": "Step 3A — Business Field Catalogue",
        "failures": failures,
        "pass": not failures,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
