#!/usr/bin/env python3
"""Post-promotion verification for Equinet A2 Wave 1."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from a2_intake import intake
from evaluate_a2_duplicate_eligibility import evaluate as evaluate_eligibility
from initialize_a2_record import load_json
from normalise_and_resolve_a2_entities import resolve

EVAL = ROOT / "evaluations/step5b"
RUNTIME = ROOT / "foundations/contracts/skills/a2-wave1-runtime-manifest-0.1.0.json"
ACCEPTANCE = EVAL / "acceptance-record.json"
PROMOTION = EVAL / "wave1-promotion-manifest.json"
ACTIVE = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"
FIXTURES = EVAL / "fixtures/wave1-cases.json"
OUTPUT = EVAL / "post-promotion-validation.json"
LANGUAGE = ROOT / "evaluations/foundation-clarifications/language-audit.json"
SKILLS = [
    ROOT / "skills/a2-handoff-intake-and-initialisation/SKILL.md",
    ROOT / "skills/a2-entity-resolution-and-normalisation/SKILL.md",
    ROOT / "skills/a2-duplicate-and-eligibility-review/SKILL.md",
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    errors = []
    runtime = load(RUNTIME); acceptance = load(ACCEPTANCE); promotion = load(PROMOTION); active = load(ACTIVE); fixtures = load(FIXTURES)
    if runtime.get("status") != "approved_local_no_integration" or acceptance.get("decision") != "approved_and_promoted":
        errors.append("Wave 1 approval state mismatch")
    if acceptance.get("approved_decisions") != [f"W1-{n}" for n in range(1, 11)]:
        errors.append("Wave 1 decision set mismatch")
    for skill in SKILLS:
        text = skill.read_text(encoding="utf-8")
        if "**Version:** `0.1.0`" not in text or "**Status:** `WAVE 1 APPROVED — LOCAL NO-INTEGRATION MODE`" not in text:
            errors.append(f"skill not promoted: {skill.parent.name}")
    for item in runtime.get("skills", []):
        for path_key, hash_key in [("path", "sha256"), ("evals_path", "evals_sha256")]:
            path = ROOT / item[path_key]
            if not path.exists() or sha(path) != item[hash_key]:
                errors.append(f"runtime manifest skill hash mismatch: {item[path_key]}")
    for item in runtime.get("commands", []):
        path = ROOT / item["path"]
        if not path.exists() or sha(path) != item["sha256"]:
            errors.append(f"runtime manifest command hash mismatch: {item['path']}")
    for item in active.get("active_files", []):
        path = ROOT / item["path"]
        if not path.exists() or sha(path) != item["sha256"]:
            errors.append(f"active foundation hash mismatch: {item['path']}")
    for item in promotion.get("files", []):
        path = ROOT / item["path"]
        if not path.exists() or sha(path) != item["sha256"]:
            errors.append(f"promotion file hash mismatch: {item['path']}")
    if sha(RUNTIME) != acceptance.get("runtime_manifest_sha256"):
        errors.append("acceptance runtime manifest hash mismatch")
    active_paths = {item.get("path") for item in active.get("active_files", [])}
    later_wave_active = "foundations/contracts/skills/a2-wave2-runtime-manifest-0.1.0.json" in active_paths
    if not later_wave_active and sha(ACTIVE) != acceptance.get("active_foundation_manifest_sha256"):
        errors.append("acceptance active foundation hash mismatch")
    if later_wave_active and "foundations/contracts/skills/a2-wave1-runtime-manifest-0.1.0.json" not in active_paths:
        errors.append("Wave 1 runtime manifest missing from later active foundation")

    deterministic = []
    handoff = load_json(ROOT / "evaluations/step2g/fixtures/inputs/horse-owner-handoff.json")
    with tempfile.TemporaryDirectory(prefix="a2-wave1-post-") as tmp:
        tmp = Path(tmp); out = tmp / "record.json"; ledger = tmp / "ledger.json"
        one, rec1 = intake(handoff, out, ledger); two, rec2 = intake(handoff, out, ledger)
        passed = one.get("write_status") == "created" and two.get("write_status") == "unchanged" and one.get("record_sha256") == two.get("record_sha256") and rec1 == rec2
        deterministic.append({"name": "intake-idempotency", "passed": passed})
        if not passed: errors.append("post-promotion intake idempotency failed")
    for case in fixtures["entity_resolution_cases"]:
        result = resolve(case["request"]); expected = case["expected"]
        candidate = result["candidate_results"][0]["status"] if result["candidate_results"] else None
        passed = result["identity_resolution_status"] == expected["identity_resolution_status"] and candidate == expected["candidate_status"] and result["human_review_required"] == expected["human_review_required"]
        deterministic.append({"name": case["name"], "passed": passed})
        if not passed: errors.append(f"post-promotion entity case failed: {case['name']}")
    for case in fixtures["eligibility_cases"]:
        if "expected_error" in case:
            try: evaluate_eligibility(case["request"]); passed = False
            except Exception as exc: passed = case["expected_error"] in str(exc)
        else:
            result = evaluate_eligibility(case["request"]); passed = all(result.get(k) == v for k, v in case["expected"].items()) and result["external_actions"] == 0
        deterministic.append({"name": case["name"], "passed": passed})
        if not passed: errors.append(f"post-promotion eligibility case failed: {case['name']}")
    language = load(LANGUAGE)
    if language.get("pass") is not True: errors.append("language audit failed")
    result = {
        "step": "5B",
        "stage": "post_promotion",
        "status": "approved_and_promoted" if not errors else "promotion_validation_failed",
        "skills": 3,
        "deterministic_replay": {"total": len(deterministic), "passed": sum(x["passed"] for x in deterministic), "cases": deterministic},
        "active_foundation_files": len(active.get("active_files", [])),
        "language_audit": {"files_checked": language.get("files_checked"), "passed": language.get("pass") is True},
        "external_actions": 0,
        "next_gate": "Step 5C — Wave 2 Planning, Research and Verification",
        "failures": errors,
        "pass": not errors,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pass": result["pass"], "replay": f"{result['deterministic_replay']['passed']}/{result['deterministic_replay']['total']}", "active_foundation_files": result["active_foundation_files"], "external_actions": 0, "failures": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
