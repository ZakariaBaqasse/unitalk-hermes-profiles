#!/usr/bin/env python3
"""Validate the Rood & Riddle DeepSeek behavioural replay and accepted-record integrity."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evaluations/step8/pilot/A1-RR-PODIATRY-001"
REPLAY = BASE / "behavioral-replay/result.json"
USAGE = BASE / "behavioral-replay/usage.json"
TOOL_AUDIT = BASE / "behavioral-replay/session-tool-audit.json"
DECISION = BASE / "final-review-decision.json"
MANIFEST = BASE / "canonical/manifest.json"
OUTPUT = BASE / "behavioral-replay/validation.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    replay = load(REPLAY)
    usage = load(USAGE)
    tools = load(TOOL_AUDIT)
    decision = load(DECISION)
    manifest = load(MANIFEST)
    accepted_path = ROOT / decision["approved_revision"]
    expected_findings = {
        "person_role_title": "Co-Founder/Farrier",
        "person_professional_status": "not_found",
        "organisation_service_area": "not_found",
        "organisation_disciplines": ["all breeds and disciplines"],
        "person_business_email": "not_found",
        "person_business_phone": "not_found",
        "organisation_phone_available": True,
        "organisation_phone_is_named_contact_phone": False,
    }
    expected_classifications = {
        "target_role_priority": "primary",
        "target_role_priority_is_sourced_fact": False,
        "purchasing_authority_established": False,
        "disciplines_scope": "organisation_level_not_podiatry_specific",
    }
    expected_boundaries = {
        "new_web_calls": 0,
        "external_actions": 0,
        "crm_writes": 0,
        "outreach_actions": 0,
        "a1_score_changed": False,
    }
    final_record = manifest["final_record"]
    manifest_item = next(item for item in manifest["records"] if item["path"] == final_record)
    checks = {
        "result_contract": set(replay) == {"record_type", "candidate_id", "profile", "model", "mode", "findings", "classifications", "minimum_package", "comparison_to_accepted_package", "boundaries", "status"},
        "identity": replay.get("candidate_id") == "A1-RR-PODIATRY-001" and replay.get("profile") == "equinet-a2-enrichment",
        "model": replay.get("model") == usage.get("model") == "deepseek-v4-flash" and usage.get("provider") == "openai-api",
        "completed": usage.get("completed") is True and usage.get("failed") is False and isinstance(usage.get("api_calls"), int) and usage["api_calls"] > 0,
        "cost_not_misreported": usage.get("cost_status") == "unknown",
        "findings_match": replay.get("findings") == expected_findings,
        "classifications_match": replay.get("classifications") == expected_classifications,
        "minimum_package_match": replay.get("minimum_package") == {"status": "incomplete", "recommended_record_decision": "held"},
        "material_match": replay.get("comparison_to_accepted_package") == {"material_match": True, "differences": []},
        "boundaries_match": replay.get("boundaries") == expected_boundaries,
        "session_tools_read_only": tools.get("external_tool_calls") == 0 and tools.get("accepted_artifact_write_calls") == 0 and tools.get("permitted_result_write_calls") == 1,
        "accepted_revision_unchanged": accepted_path.exists() and sha(accepted_path) == decision["approved_revision_sha256"] == manifest_item["sha256"],
        "status_pass": replay.get("status") == "pass",
    }
    result = {
        "record_type": "step8_rood_riddle_behavioral_replay_validation",
        "candidate_id": "A1-RR-PODIATRY-001",
        "status": "pass" if all(checks.values()) else "failed",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "usage": {
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "api_calls": usage.get("api_calls"),
            "model": usage.get("model"),
            "provider": usage.get("provider"),
            "cost_amount": usage.get("estimated_cost_usd"),
            "cost_status": usage.get("cost_status"),
        },
        "session_id": usage.get("session_id"),
        "accepted_revision_sha256": sha(accepted_path),
        "external_actions": 0,
        "errors": [name for name, passed in checks.items() if not passed],
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
