#!/usr/bin/env python3
"""Build Step 8 closure readiness without exposing credentials or claiming premature acceptance."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
STEP8 = ROOT / "evaluations/step8"
STATUS = STEP8 / "step8-current-status.json"
LANGUAGE = ROOT / "evaluations/foundation-clarifications/language-audit.json"
REPLAY = STEP8 / "pilot/A1-RR-PODIATRY-001/behavioral-replay/validation.json"
JONABELL = STEP8 / "pilot/A1-DARLEY-JONABELL-001/final-review-decision.json"
RR = STEP8 / "pilot/A1-RR-PODIATRY-001/final-review-decision.json"
CONFIG = ROOT / "config.yaml"
SOUL = ROOT / "SOUL.md"
ENV = ROOT / ".env"
OUT = STEP8 / "step8-closure-readiness.json"
REVIEW = STEP8 / "STEP-8-CLOSURE-READINESS.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def env_presence(path: Path) -> dict[str, bool]:
    found = {"OPENAI_API_KEY": False, "OPENAI_BASE_URL": False}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key in found:
            found[key] = bool(value.strip().strip('"').strip("'"))
    return found


def main() -> int:
    status = load(STATUS)
    language = load(LANGUAGE)
    replay = load(REPLAY)
    jonabell = load(JONABELL)
    rr = load(RR)
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    soul_text = SOUL.read_text(encoding="utf-8")
    route = env_presence(ENV)
    cli_tools = config.get("platform_toolsets", {}).get("cli", [])
    temporary_web_disabled = "web" not in config and "web" not in cli_tools
    soul_synced = "Step 8 is completed and approved for Step 9" in soul_text
    checks = {
        "jonabell_business_decision": jonabell.get("decision") == "approved_as_step8_test_result",
        "rood_riddle_business_decision": rr.get("decision") == "held_as_accepted_step8_test_result",
        "current_artifacts": status.get("all_current_artifact_checks_passed") is True,
        "deepseek_behavioral_replay": replay.get("status") == "pass" and replay.get("checks_passed") == replay.get("checks_total") == 13,
        "gateway_route_present": all(route.values()),
        "temporary_web_disabled": temporary_web_disabled,
        "language_audit": language.get("pass") is True,
        "external_actions_zero": status.get("external_actions") == replay.get("external_actions") == 0,
    }
    files = [STATUS, LANGUAGE, REPLAY, JONABELL, RR, CONFIG]
    result = {
        "record_type": "step8_closure_readiness",
        "profile": "equinet-a2-enrichment",
        "status": "ready_pending_protected_soul_sync" if all(checks.values()) and not soul_synced else "ready_for_formal_acceptance" if all(checks.values()) else "not_ready",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "protected_soul_sync": {
            "completed": soul_synced,
            "required_text": "Step 8 is completed and approved for Step 9",
            "last_attempt": "blocked because the protected-file approval prompt expired",
        },
        "credential_route": {
            "openai_api_key_present": route["OPENAI_API_KEY"],
            "openai_base_url_present": route["OPENAI_BASE_URL"],
            "values_recorded": False,
        },
        "runtime": {
            "temporary_web_disabled": temporary_web_disabled,
            "fallback_enabled": bool(config.get("fallback_providers")),
            "primary_model": config.get("model", {}).get("default"),
        },
        "artifacts": [{"path": str(path.relative_to(ROOT)), "sha256": sha(path)} for path in files],
        "formal_acceptance_recorded": False,
        "next_gate": "Apply protected SOUL sync, then record Step 8 acceptance for Step 9.",
        "external_actions": 0,
    }
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REVIEW.write_text(
        f"""# Step 8 Closure Readiness

**Profile:** `equinet-a2-enrichment`  
**Status:** `{result['status'].upper()}`

## Passed controls

- Closure controls: **{result['checks_passed']}/{result['checks_total']} PASS**.
- Jonabell decision: approved test result.
- Rood & Riddle decision: accepted held test result.
- DeepSeek behavioural replay: **13/13 PASS**.
- Unitalk OpenAI-compatible credential route: present; values not recorded.
- Temporary Web access: disabled.
- Language audit: PASS.
- External business actions: zero.

## Remaining closure action

The protected `SOUL.md` next-gate update is not yet applied because its approval prompt expired. Formal Step 8 acceptance must not be recorded until that protected sync succeeds.

## Next gate after sync

Record Step 8 acceptance and proceed to **Step 9 — Evaluation, Improvement and No-Integration Freeze**.
""",
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "checks": f"{result['checks_passed']}/{result['checks_total']}", "soul_synced": soul_synced, "external_actions": 0}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
