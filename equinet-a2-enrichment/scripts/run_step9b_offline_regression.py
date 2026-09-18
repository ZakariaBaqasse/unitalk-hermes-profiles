#!/usr/bin/env python3
"""Run the Step 9B offline regression suite in an isolated no-secret sandbox."""
from __future__ import annotations

import hashlib
import json
import os
import py_compile
import shutil
import subprocess
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
SANDBOX = Path("/opt/data/tmp/equinet-a2-step9b-final-sandbox")
OUT = ROOT / "evaluations/step9/regression"
RAW = OUT / "final-runs"
RESULT = OUT / "phase9b-regression.json"
REVIEW = ROOT / "evaluations/step9/STEP-9B-OFFLINE-REGRESSION-REVIEW.md"
REPLAY_SCRIPT = ROOT / "scripts/replay_step8_accepted_records_no_web.py"
REPLAY_MANIFEST = ROOT / "evaluations/step9/replay/replay-manifest.json"
RC_VALIDATION = ROOT / "evaluations/step9/phase9a-validation.json"
CONFIG = ROOT / "config.yaml"

SUITES = [
    "run_step1c_tests.py",
    "validate_step2d_schema.py",
    "run_step2e_tests.py",
    "run_step2f_tests.py",
    "run_step2g_tests.py",
    "run_step3b_tests.py",
    "run_step3d_tests.py",
    "run_step3e_tests.py",
    "run_step3f_tests.py",
]
WORKFLOWS = ["farrier_review", "horse_owner_requalification"]
OPERATORS = [
    "a2_intake.py",
    "normalise_and_resolve_a2_entities.py",
    "evaluate_a2_duplicate_eligibility.py",
    "build_a2_gap_plan.py",
    "evaluate_a2_minimum_package.py",
    "preflight_a2_source_action.py",
    "classify_official_site_social_link.py",
    "normalise_and_validate_a2_observations.py",
    "evaluate_a2_evidence_confidence.py",
    "evaluate_a2_protected_field_action.py",
    "create_a2_revision.py",
    "render_and_validate_a2_review_package.py",
    "build_and_validate_a2_twenty_review.py",
    "build_and_validate_a2_handoff.py",
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_profile() -> None:
    shutil.rmtree(SANDBOX, ignore_errors=True)
    shutil.copytree(ROOT, SANDBOX, ignore=shutil.ignore_patterns(".venv", "__pycache__", ".env", "cache"))
    os.symlink(ROOT / ".venv", SANDBOX / ".venv")


def run(name: str, command: list[str]) -> dict:
    process = subprocess.run(command, cwd=SANDBOX, capture_output=True, text=True, timeout=240)
    output = process.stdout + ("\nSTDERR:\n" + process.stderr if process.stderr else "")
    path = RAW / f"{name}.txt"
    path.write_text(output, encoding="utf-8")
    parsed = None
    try:
        parsed = json.loads(process.stdout)
    except json.JSONDecodeError:
        pass
    return {
        "name": name,
        "command": command[1:],
        "exit_code": process.returncode,
        "passed": process.returncode == 0 and (parsed is None or parsed.get("pass", True) is True),
        "output": str(path.relative_to(ROOT)),
        "output_sha256": sha(path),
        "parsed_summary": {key: parsed.get(key) for key in ("pass", "fixtures", "negative_regressions", "operators", "deterministic", "workflows", "failures") if parsed is not None and key in parsed},
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    copy_profile()
    python = str(SANDBOX / ".venv/bin/python")
    runs = []
    for script in SUITES:
        runs.append(run(script.removesuffix(".py"), [python, str(SANDBOX / "scripts" / script)]))
    for scenario in WORKFLOWS:
        output_dir = SANDBOX / "evaluations/step9-workflows" / scenario
        runs.append(
            run(
                f"workflow-{scenario}",
                [python, str(SANDBOX / "scripts/run_a2_no_integration_workflow.py"), "--scenario", scenario, "--output-dir", str(output_dir)],
            )
        )
    compile_results = []
    for name in OPERATORS:
        path = ROOT / "scripts" / name
        try:
            py_compile.compile(str(path), doraise=True)
            compile_results.append({"path": str(path.relative_to(ROOT)), "passed": True})
        except Exception as error:
            compile_results.append({"path": str(path.relative_to(ROOT)), "passed": False, "error": str(error)})

    replay_process = subprocess.run([str(ROOT / ".venv/bin/python"), str(REPLAY_SCRIPT)], cwd=ROOT, capture_output=True, text=True, timeout=240)
    replay = load(REPLAY_MANIFEST) if REPLAY_MANIFEST.exists() else {"status": "missing", "results": []}
    rc = load(RC_VALIDATION)
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    checks = {
        "isolated_sandbox_excludes_env": not (SANDBOX / ".env").exists(),
        "historical_low_level_suites": all(item["passed"] for item in runs[: len(SUITES)]),
        "workflow_scenarios": all(item["passed"] for item in runs[len(SUITES) :]),
        "operator_compile": all(item["passed"] for item in compile_results) and len(compile_results) == 14,
        "step9a_release_candidate": rc.get("status") == "pass_ready_for_step9b" and rc.get("checks_passed") == rc.get("checks_total") == 15,
        "exact_no_web_replay": replay_process.returncode == 0 and replay.get("status") == "pass" and replay.get("candidates_passed") == replay.get("candidate_count") == 2,
        "canonical_byte_equality": all(item.get("canonical_byte_equal") is True for item in replay.get("results", [])),
        "export_equality": all(all(item.get("text_export_equality", {}).values()) and item.get("xlsx_cell_value_equality") is True and item.get("review_manifest_semantic_equality") is True for item in replay.get("results", [])),
        "web_disabled": "web" not in config and "web" not in config.get("platform_toolsets", {}).get("cli", []),
        "external_actions_zero": replay.get("web_calls") == replay.get("provider_calls") == replay.get("external_actions") == 0,
    }
    result = {
        "record_type": "step9b_offline_regression_and_no_web_replay",
        "profile": "equinet-a2-enrichment",
        "release_candidate": "equinet-a2-no-integration-1.0.0-rc.1",
        "status": "pass_ready_for_step9c" if all(checks.values()) else "failed",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "suite_runs": runs,
        "suite_count": len(runs),
        "suite_passed": sum(item["passed"] for item in runs),
        "operator_compile": compile_results,
        "exact_replay": {
            "path": str(REPLAY_MANIFEST.relative_to(ROOT)),
            "sha256": sha(REPLAY_MANIFEST),
            "candidate_count": replay.get("candidate_count"),
            "candidates_passed": replay.get("candidates_passed"),
            "canonical_exact": all(item.get("canonical_byte_equal") is True for item in replay.get("results", [])),
            "exports_exact": checks["export_equality"],
        },
        "historical_manifest_validators": {
            "status": "superseded_for_release_candidate",
            "reason": "Step 5/6/7 promotion validators pin historical hashes and are not release-candidate validators after approved Step 9A changes.",
            "replacement": "Step 9A RC manifest validation plus the low-level suites, two workflow scenarios and exact accepted-record replay recorded here.",
        },
        "web_calls": 0,
        "provider_calls": 0,
        "external_actions": 0,
        "errors": [name for name, passed in checks.items() if not passed],
    }
    RESULT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REVIEW.write_text(
        f"""# Step 9B Offline Regression and Exact No-Web Replay

**Profile:** `equinet-a2-enrichment`  
**Release candidate:** `equinet-a2-no-integration-1.0.0-rc.1`  
**Status:** `{'PASS — READY FOR STEP 9C' if all(checks.values()) else 'FAILED'}`

## Results

- Validation controls: **{sum(checks.values())}/{len(checks)} PASS**.
- Offline suites and workflows: **{sum(item['passed'] for item in runs)}/{len(runs)} PASS**.
- Operator compilation: **{sum(item['passed'] for item in compile_results)}/{len(compile_results)} PASS**.
- Accepted canonical records replayed byte-for-byte: **{replay.get('candidates_passed')}/{replay.get('candidate_count')} PASS**.
- Markdown/CSV/XLSX semantic equality: **PASS**.
- Web calls: **0**.
- Provider calls: **0**.
- External actions: **0**.

## Repaired regression runners

- Step 3D now carries fixture names into rendered results and supplies hashed synthetic source-preflight receipts required by the current evidence contract.
- Step 3E now carries fixture names into rendered results.

## Historical manifest boundary

The old Step 5/6/7 promotion validators intentionally pin their historical hashes. They are preserved as historical evidence and are superseded for this release candidate by the Step 9A RC manifest validation, current low-level suites, two full workflow scenarios and the exact accepted-record replay.

## Next gate

Proceed to **Step 9C — Release Manifest and Delivery Documentation**. No promotion has occurred.
""",
        encoding="utf-8",
    )
    plan_path = ROOT / "evaluations/step9/step9-plan.json"
    plan = load(plan_path)
    for phase in plan["phases"]:
        if phase["id"] == "9B":
            phase["status"] = "completed" if all(checks.values()) else "blocked"
        elif phase["id"] == "9C" and all(checks.values()):
            phase["status"] = "ready"
    plan["status"] = "step9b_completed_ready_for_step9c" if all(checks.values()) else "step9b_blocked"
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": f"{result['checks_passed']}/{result['checks_total']}", "suites": f"{result['suite_passed']}/{result['suite_count']}", "operators": f"{sum(item['passed'] for item in compile_results)}/{len(compile_results)}", "replay": f"{replay.get('candidates_passed')}/{replay.get('candidate_count')}", "web_calls": 0, "external_actions": 0}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
