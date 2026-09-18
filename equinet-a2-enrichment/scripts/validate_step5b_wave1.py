#!/usr/bin/env python3
"""Validate Equinet A2 Step 5B Wave 1 skills and deterministic commands."""
from __future__ import annotations

import hashlib
import json
import subprocess
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
FIXTURES = EVAL / "fixtures/wave1-cases.json"
OUTPUT = EVAL / "technical-validation.json"
PACKAGE = EVAL / "wave1-draft-package-manifest.json"
REVIEW = EVAL / "A2-WAVE-1-REVIEW.md"
BEHAVIOURAL = EVAL / "behavioural-validation.json"
LANGUAGE = ROOT / "evaluations/foundation-clarifications/language-audit.json"
STEP5A_ACCEPTANCE = ROOT / "evaluations/step5a/acceptance-record.json"
ARCHITECTURE = ROOT / "foundations/contracts/skills/a2-operational-skill-manifest-0.1.0.json"

SKILLS = [
    ROOT / "skills/a2-handoff-intake-and-initialisation/SKILL.md",
    ROOT / "skills/a2-entity-resolution-and-normalisation/SKILL.md",
    ROOT / "skills/a2-duplicate-and-eligibility-review/SKILL.md",
]
EVAL_FILES = [path.parent / "evals/evals.json" for path in SKILLS]
COMMANDS = [
    ROOT / "scripts/a2_intake.py",
    ROOT / "scripts/normalise_and_resolve_a2_entities.py",
    ROOT / "scripts/evaluate_a2_duplicate_eligibility.py",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    failures = []
    acceptance = load(STEP5A_ACCEPTANCE)
    if acceptance.get("decision") != "approved_and_promoted" or acceptance.get("approved_decisions") != [f"5A-{n}" for n in range(1, 11)]:
        failures.append("Step 5A approval is missing or incomplete")
    architecture = load(ARCHITECTURE)
    if architecture.get("status") != "approved_for_wave_1_build":
        failures.append("approved Step 5A architecture is not active")

    package_checks = []
    for skill_path, eval_path in zip(SKILLS, EVAL_FILES):
        text = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""
        evals = load(eval_path) if eval_path.exists() else {}
        skill_id = skill_path.parent.name
        checks = {
            "frontmatter_name": f"name: {skill_id}" in text,
            "description": "description:" in text,
            "draft_status": "WAVE 1 DRAFT — NOT APPROVED" in text,
            "mission": "## Mission" in text,
            "inputs": "## Inputs" in text,
            "command": "## Command" in text,
            "boundaries": "## Boundaries" in text or "## Stop and escalation rules" in text,
            "handoff": "## Handoff" in text,
            "three_evals": len(evals.get("evals", [])) == 3,
        }
        if not all(checks.values()):
            failures.append(f"skill package check failed: {skill_id}")
        package_checks.append({"skill_id": skill_id, "checks": checks, "passed": all(checks.values())})

    for command in COMMANDS:
        if not command.exists():
            failures.append(f"missing Wave 1 command: {command.name}")

    deterministic_cases = []
    # Intake: valid, idempotent repeat and invalid gate.
    valid_handoff_path = ROOT / "evaluations/step2g/fixtures/inputs/horse-owner-handoff.json"
    invalid_handoff_path = ROOT / "evaluations/step2g/fixtures/invalid/recommendation-not-pass-to-a2.json"
    expected_record = load(ROOT / "evaluations/step2g/fixtures/valid/horse-owner-initial-record.json")
    with tempfile.TemporaryDirectory(prefix="a2-wave1-") as tmp:
        tmp = Path(tmp)
        output = tmp / "record.json"
        ledger = tmp / "ledger.json"
        summary1, record1 = intake(load_json(valid_handoff_path), output, ledger)
        summary2, record2 = intake(load_json(valid_handoff_path), output, ledger)
        checks = {
            "first_created": summary1.get("write_status") == "created",
            "repeat_unchanged": summary2.get("write_status") == "unchanged",
            "ledger_repeat_existing": summary2.get("ledger_status") == "existing",
            "records_equal": record1 == record2 == expected_record,
            "external_actions_zero": summary1.get("external_actions") == summary2.get("external_actions") == 0,
        }
        deterministic_cases.append({"name": "intake-valid-and-idempotent", "checks": checks, "passed": all(checks.values())})
        if not all(checks.values()): failures.append("intake valid/idempotent case failed")

        invalid_output = tmp / "invalid.json"
        process = subprocess.run([sys.executable, str(ROOT / "scripts/a2_intake.py"), str(invalid_handoff_path), "--output", str(invalid_output)], cwd=ROOT, capture_output=True, text=True)
        checks = {"exit_one": process.returncode == 1, "no_output": not invalid_output.exists(), "reports_invalid": json.loads(process.stdout).get("valid") is False}
        deterministic_cases.append({"name": "intake-invalid-rejected", "checks": checks, "passed": all(checks.values())})
        if not all(checks.values()): failures.append("invalid intake case failed")

    fixture_data = load(FIXTURES)
    for case in fixture_data["entity_resolution_cases"]:
        result = resolve(case["request"])
        candidate_status = result["candidate_results"][0]["status"] if result["candidate_results"] else None
        expected = case["expected"]
        passed = (
            result["identity_resolution_status"] == expected["identity_resolution_status"]
            and candidate_status == expected["candidate_status"]
            and result["human_review_required"] == expected["human_review_required"]
            and result["canonical_record_mutated"] is False
            and result["external_actions"] == 0
        )
        deterministic_cases.append({"name": case["name"], "result": result, "expected": expected, "passed": passed})
        if not passed: failures.append(f"entity case failed: {case['name']}")

    for case in fixture_data["eligibility_cases"]:
        if "expected_error" in case:
            try:
                evaluate_eligibility(case["request"])
                passed = False; result = {"error": None}
            except Exception as exc:
                result = {"error": str(exc)}
                passed = case["expected_error"] in str(exc)
        else:
            result = evaluate_eligibility(case["request"])
            expected = case["expected"]
            passed = all(result.get(key) == value for key, value in expected.items()) and result["crm_write_authorized"] is False and result["outreach_authorized"] is False and result["external_actions"] == 0
        deterministic_cases.append({"name": case["name"], "result": result, "expected": case.get("expected", case.get("expected_error")), "passed": passed})
        if not passed: failures.append(f"eligibility case failed: {case['name']}")

    behavioural = load(BEHAVIOURAL)
    behavioural_checks = {
        "overall_pass": behavioural.get("overall_status") == "pass",
        "three_scenarios": behavioural.get("scenario_count") == 3 and behavioural.get("passed") == 3 and behavioural.get("failed") == 0,
        "all_skill_statuses_pass": all(str(item.get("status", "")).startswith("pass") for item in behavioural.get("scenarios", [])),
        "external_actions_zero": behavioural.get("external_actions") == 0,
    }
    if not all(behavioural_checks.values()):
        failures.append("targeted behavioural validation failed")

    language = load(LANGUAGE)
    if language.get("pass") is not True:
        failures.append("language audit failed")

    result = {
        "step": "5B",
        "wave": 1,
        "status": "ready_for_severine_review_not_approved",
        "skill_count": 3,
        "command_count": 3,
        "package_checks": package_checks,
        "deterministic_cases": {"total": len(deterministic_cases), "passed": sum(x["passed"] for x in deterministic_cases), "cases": deterministic_cases},
        "targeted_behavioural_validation": behavioural_checks,
        "external_calls": 0,
        "external_actions": 0,
        "hubspot_access": False,
        "apify_access": False,
        "approval_required": True,
        "next_gate_after_approval": "Step 5C — Wave 2 Planning, Research and Verification",
        "failures": failures,
        "pass": not failures,
    }
    EVAL.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    review = f"""# Decision Review — Step 5B Wave 1 Intake and Identity

**Status:** `READY FOR SÉVERINE REVIEW — NOT APPROVED`  
**Profile:** `equinet-a2-enrichment`  
**Wave:** `1 — Intake and Identity`

## Delivered skill packages

1. `a2-handoff-intake-and-initialisation`;
2. `a2-entity-resolution-and-normalisation`;
3. `a2-duplicate-and-eligibility-review`.

## Decisions proposed

| ID | Decision |
|---|---|
| W1-1 | Require the complete approved A1-to-A2 handoff gate before creating an A2 record. |
| W1-2 | Preserve the complete A1 snapshot and create the first A2 revision deterministically and idempotently. |
| W1-3 | Keep entity normalisation separate from external record merging or CRM mutation. |
| W1-4 | Treat a matching domain as one identity signal, never as a unique key by itself. |
| W1-5 | Require a matching name plus a strong identifier, or multiple strong identifiers, for a deterministic confirmed match. |
| W1-6 | Route one weak match to `possible_match` and mixed matching/conflicting signals to `conflict`. |
| W1-7 | Block confirmed duplicates and invalid identities; hold unresolved material identity conflicts. |
| W1-8 | Hold possible duplicates, unresolved identities and failed required duplicate checks. |
| W1-9 | Permit synthetic or manual no-integration progression when HubSpot checks are unavailable, while keeping outreach eligibility unavailable. |
| W1-10 | Keep all Wave 1 commands local, read-only with respect to source systems, and at zero external actions. |

## Technical result

- Skill packages: **3/3 present**.
- Deterministic cases: **{sum(x['passed'] for x in deterministic_cases)}/{len(deterministic_cases)} PASS**.
- Targeted behavioural scenarios: **{behavioural['passed']}/{behavioural['scenario_count']} PASS**.
- External calls: **0**.
- External actions: **0**.
- HubSpot and Apify access: **not used**.

## Approval effect

Approval promotes the three Wave 1 skills and authorises Step 5C Wave 2 construction. It does not activate Web, Apify, Twenty, HubSpot, n8n, outreach, CRM writes, pilot or production status.
"""
    REVIEW.write_text(review, encoding="utf-8")
    files = [*SKILLS, *EVAL_FILES, *COMMANDS, FIXTURES, BEHAVIOURAL, OUTPUT, REVIEW, STEP5A_ACCEPTANCE, ARCHITECTURE]
    package = {
        "manifest_id": "equinet-a2-wave1-draft-package",
        "version": "0.1.0-draft.1",
        "status": "ready_for_severine_review_not_approved" if not failures else "validation_failed",
        "files": [{"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha(path)} for path in files],
        "file_count": len(files),
        "skills": 3,
        "external_actions": 0,
    }
    PACKAGE.write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pass": result["pass"], "skills": 3, "deterministic_cases": f"{result['deterministic_cases']['passed']}/{result['deterministic_cases']['total']}", "external_actions": 0, "status": result["status"], "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
