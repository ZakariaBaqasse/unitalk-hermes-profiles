#!/usr/bin/env python3
"""Record formal Step 8 acceptance after all business, replay and closure gates pass."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP8 = ROOT / "evaluations/step8"
CLOSURE = STEP8 / "step8-closure-readiness.json"
STATUS = STEP8 / "step8-current-status.json"
REPLAY = STEP8 / "pilot/A1-RR-PODIATRY-001/behavioral-replay/validation.json"
JONABELL = STEP8 / "pilot/A1-DARLEY-JONABELL-001/final-review-decision.json"
RR = STEP8 / "pilot/A1-RR-PODIATRY-001/final-review-decision.json"
LANGUAGE = ROOT / "evaluations/foundation-clarifications/language-audit.json"
SOUL = ROOT / "SOUL.md"
CONFIG = ROOT / "config.yaml"
CORRECTION = STEP8 / "receipt-scope-correction.json"
ACCEPTANCE = STEP8 / "acceptance-record.json"
RUNTIME_MANIFEST = ROOT / "foundations/contracts/runtime/a2-step8-pilot-acceptance-manifest-0.1.0.json"
ACCEPTED_AT = "2026-08-30T14:10:45Z"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    closure = load(CLOSURE)
    status = load(STATUS)
    replay = load(REPLAY)
    jonabell = load(JONABELL)
    rr = load(RR)
    language = load(LANGUAGE)
    prerequisites = {
        "closure_ready": closure.get("status") == "ready_for_formal_acceptance" and closure.get("checks_passed") == closure.get("checks_total") == 8,
        "status_complete": status.get("status") == "step8_completed_approved_for_step9" and status.get("step8_complete") is True,
        "jonabell_accepted": jonabell.get("decision") == "approved_as_step8_test_result",
        "rood_riddle_accepted_held": rr.get("decision") == "held_as_accepted_step8_test_result",
        "deepseek_replay": replay.get("status") == "pass" and replay.get("checks_passed") == replay.get("checks_total") == 13,
        "language_audit": language.get("pass") is True,
        "soul_gate": "Step 8 is completed and approved for Step 9" in SOUL.read_text(encoding="utf-8"),
        "external_actions_zero": status.get("external_actions") == replay.get("external_actions") == 0,
    }
    if not all(prerequisites.values()):
        raise RuntimeError(f"Step 8 acceptance prerequisites failed: {[key for key, value in prerequisites.items() if not value]}")

    artifacts = [CLOSURE, STATUS, REPLAY, JONABELL, RR, LANGUAGE, SOUL, CONFIG, CORRECTION]
    acceptance = {
        "record_type": "step8_bounded_real_no_integration_pilot_acceptance",
        "profile": "equinet-a2-enrichment",
        "step": "8",
        "decision": "approved_for_step9_evaluation_and_no_integration_freeze",
        "approver": {"name": "Séverine", "role": "Unitalk Operations"},
        "accepted_at": ACCEPTED_AT,
        "approved_scope": "Two-candidate bounded real no-integration pilot with stored public-business evidence, no production write and no outreach.",
        "candidate_decisions": {
            "A1-DARLEY-JONABELL-001": {
                "decision": "approved_as_step8_test_result",
                "canonical_state": "record_approved",
                "target_role_priority": "secondary",
            },
            "A1-RR-PODIATRY-001": {
                "decision": "held_as_accepted_step8_test_result",
                "canonical_state": "held",
                "target_role_priority": "primary",
                "disciplines": ["all breeds and disciplines"],
                "hold_reasons": rr["hold_reasons"],
            },
        },
        "validation": {
            "current_status_checks": f"{status['checks_passed']}/{status['checks_total']} pass",
            "closure_checks": f"{closure['checks_passed']}/{closure['checks_total']} pass",
            "deepseek_behavioral_replay": f"{replay['checks_passed']}/{replay['checks_total']} pass",
            "language_audit": f"{language['files_checked']} files, 0 findings",
            "temporary_web_disabled": closure["runtime"]["temporary_web_disabled"],
            "credential_route_present_without_values_recorded": closure["credential_route"]["openai_api_key_present"] and closure["credential_route"]["openai_base_url_present"] and not closure["credential_route"]["values_recorded"],
            "external_actions": 0,
        },
        "replay_usage": replay["usage"],
        "limitations": [
            "This is Unitalk Step 8 pilot acceptance, not Equinet production acceptance or contractual delivery acceptance.",
            "The profile remains FOUNDATION CONFIGURED — NOT PILOT-READY until Step 9 freeze is approved and promoted.",
            "Rood & Riddle remains held until approved evidence or an Equinet-approved exception resolves the minimum-package gaps.",
            "HubSpot, Twenty, n8n, Apify, outreach and downstream delivery remain unavailable or disabled.",
            "Replay cost is undetermined; estimated cost 0.0 with cost_status unknown must not be interpreted as free usage.",
        ],
        "authoritative_artifacts": [{"path": str(path.relative_to(ROOT)), "sha256": sha(path)} for path in artifacts],
        "next_gate": "Step 9 — Evaluation, Improvement and No-Integration Freeze",
        "profile_status": "FOUNDATION CONFIGURED — NOT PILOT-READY",
        "external_actions": 0,
    }
    ACCEPTANCE.write_text(json.dumps(acceptance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    manifest = {
        "manifest_id": "equinet-a2-step8-pilot-acceptance",
        "version": "0.1.0",
        "status": "approved_for_step9_evaluation_and_no_integration_freeze",
        "approved_at": ACCEPTED_AT,
        "approved_by": acceptance["approver"],
        "acceptance_record": {
            "path": str(ACCEPTANCE.relative_to(ROOT)),
            "sha256": sha(ACCEPTANCE),
        },
        "candidate_count": 2,
        "candidate_outcomes": {
            "approved": 1,
            "held": 1,
        },
        "deepseek_behavioral_replay": {
            "status": "pass",
            "checks": "13/13",
            "model": replay["usage"]["model"],
            "provider": replay["usage"]["provider"],
            "total_tokens": replay["usage"]["total_tokens"],
            "api_calls": replay["usage"]["api_calls"],
            "cost_status": replay["usage"]["cost_status"],
        },
        "temporary_web_disabled": True,
        "external_actions": 0,
        "profile_status": "FOUNDATION CONFIGURED — NOT PILOT-READY",
        "next_gate": acceptance["next_gate"],
    }
    RUNTIME_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "prerequisites": f"{sum(prerequisites.values())}/{len(prerequisites)}", "acceptance_record": str(ACCEPTANCE.relative_to(ROOT)), "acceptance_sha256": sha(ACCEPTANCE), "runtime_manifest": str(RUNTIME_MANIFEST.relative_to(ROOT)), "external_actions": 0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
