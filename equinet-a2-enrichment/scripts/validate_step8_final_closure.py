#!/usr/bin/env python3
"""Validate final Step 8 acceptance and release the profile to Step 9 only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
STEP8 = ROOT / "evaluations/step8"
ACCEPTANCE = STEP8 / "acceptance-record.json"
RUNTIME = ROOT / "foundations/contracts/runtime/a2-step8-pilot-acceptance-manifest-0.1.0.json"
CLOSURE = STEP8 / "step8-closure-readiness.json"
STATUS = STEP8 / "step8-current-status.json"
REPLAY = STEP8 / "pilot/A1-RR-PODIATRY-001/behavioral-replay/validation.json"
LANGUAGE = ROOT / "evaluations/foundation-clarifications/language-audit.json"
SOUL = ROOT / "SOUL.md"
CONFIG = ROOT / "config.yaml"
OUTPUT = STEP8 / "final-closure-validation.json"
REVIEW = STEP8 / "STEP-8-FINAL-ACCEPTANCE.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    acceptance = load(ACCEPTANCE)
    runtime = load(RUNTIME)
    closure = load(CLOSURE)
    status = load(STATUS)
    replay = load(REPLAY)
    language = load(LANGUAGE)
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    artifact_hashes = all((ROOT / item["path"]).exists() and sha(ROOT / item["path"]) == item["sha256"] for item in acceptance["authoritative_artifacts"])
    cli_tools = config.get("platform_toolsets", {}).get("cli", [])
    checks = {
        "acceptance_decision": acceptance.get("decision") == "approved_for_step9_evaluation_and_no_integration_freeze",
        "runtime_manifest": runtime.get("status") == acceptance.get("decision") and runtime["acceptance_record"]["sha256"] == sha(ACCEPTANCE),
        "acceptance_artifact_hashes": artifact_hashes,
        "closure_readiness": closure.get("status") == "ready_for_formal_acceptance" and closure.get("checks_passed") == closure.get("checks_total") == 8,
        "current_status": status.get("status") == "step8_completed_approved_for_step9" and status.get("step8_complete") is True and status.get("checks_passed") == status.get("checks_total") == 11,
        "deepseek_replay": replay.get("status") == "pass" and replay.get("checks_passed") == replay.get("checks_total") == 13,
        "soul_next_gate": "Step 8 is completed and approved for Step 9" in SOUL.read_text(encoding="utf-8"),
        "temporary_web_disabled": "web" not in config and "web" not in cli_tools,
        "language_audit": language.get("pass") is True,
        "boundaries": acceptance.get("external_actions") == runtime.get("external_actions") == status.get("external_actions") == replay.get("external_actions") == 0,
        "profile_not_pilot_ready_yet": acceptance.get("profile_status") == runtime.get("profile_status") == "FOUNDATION CONFIGURED — NOT PILOT-READY",
    }
    result = {
        "record_type": "step8_final_closure_validation",
        "profile": "equinet-a2-enrichment",
        "status": "pass_approved_for_step9" if all(checks.values()) else "failed",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "acceptance_record": str(ACCEPTANCE.relative_to(ROOT)),
        "acceptance_sha256": sha(ACCEPTANCE),
        "runtime_manifest": str(RUNTIME.relative_to(ROOT)),
        "runtime_manifest_sha256": sha(RUNTIME),
        "next_gate": "Step 9 — Evaluation, Improvement and No-Integration Freeze",
        "profile_status": "FOUNDATION CONFIGURED — NOT PILOT-READY",
        "external_actions": 0,
        "errors": [name for name, passed in checks.items() if not passed],
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REVIEW.write_text(
        f"""# Step 8 Final Acceptance

**Profile:** `equinet-a2-enrichment`  
**Decision:** `APPROVED FOR STEP 9 — EVALUATION, IMPROVEMENT AND NO-INTEGRATION FREEZE`  
**Validation:** `{result['checks_passed']}/{result['checks_total']} PASS`

## Accepted outcomes

- Jonabell: approved Step 8 test result; target-role priority `secondary`.
- Rood & Riddle: accepted held Step 8 test result; target-role priority `primary`; organisation-level disciplines `["all breeds and disciplines"]`.
- DeepSeek stored-page replay: 13/13 PASS; accepted canonical record unchanged.
- Temporary Web access: disabled.
- External business actions: zero.

## Boundary

This is Unitalk Step 8 acceptance only. It is not Equinet production acceptance, contractual delivery acceptance or approval for CRM writes, outreach or downstream delivery. The profile remains **FOUNDATION CONFIGURED — NOT PILOT-READY** until Step 9 is approved and promoted.

## Next gate

**Step 9 — Evaluation, Improvement and No-Integration Freeze**.
""",
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "checks": f"{result['checks_passed']}/{result['checks_total']}", "acceptance_sha256": result["acceptance_sha256"], "next_gate": result["next_gate"], "external_actions": 0}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
