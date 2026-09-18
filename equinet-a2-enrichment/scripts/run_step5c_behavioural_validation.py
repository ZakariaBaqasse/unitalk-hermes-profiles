#!/usr/bin/env python3
"""Run three targeted Step 5C behavioural scenarios using exact operator commands."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evaluations/step5c/fixtures/wave2-cases.json"
OUTPUT = ROOT / "evaluations/step5c/behavioural-validation.json"


def run_command(script: str, request: dict, tmp: Path) -> tuple[int, dict]:
    input_path = tmp / f"{script}.input.json"
    output_path = tmp / f"{script}.output.json"
    input_path.write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    process = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), str(input_path), "--output", str(output_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    parsed = json.loads(output_path.read_text(encoding="utf-8")) if output_path.exists() else json.loads(process.stdout)
    return process.returncode, parsed


def prepare_source_request(request: dict) -> dict:
    prepared = json.loads(json.dumps(request))
    prepared.setdefault("actor_profile", "equinet-a2-enrichment")
    prepared.setdefault("trigger", prepared.get("named_need"))
    prepared.setdefault("requested_at", "2026-08-27T13:00:00Z")
    prepared.setdefault("run_id", f"W2-{prepared.get('candidate_id', 'UNKNOWN')}")
    return prepared


def prepare_observations(request: dict, tmp: Path) -> dict:
    prepared = json.loads(json.dumps(request))
    for observation in prepared.get("observations", []):
        source_id = observation.get("source_id")
        local_reuse = source_id in {"a1_approved_handoff", "a1_directory_evidence_reuse"}
        unavailable_source = observation.get("availability_status") == "unavailable"
        preflight_request = {
            "candidate_id": prepared.get("candidate_id"),
            "operating_scope": prepared.get("operating_scope"),
            "source_id": source_id,
            "field_key": observation.get("field_key"),
            "named_need": f"validate {observation.get('field_key')}",
            "execution_mode": "preflight_only" if local_reuse or unavailable_source else "local_fixture_simulation",
            "fixture_is_synthetic": False if local_reuse or unavailable_source else True,
            "fixture_reference": None if local_reuse or unavailable_source else f"fixtures://{observation.get('observation_id')}",
            "official_site_check": "completed_fixture",
            "named_role_gap": True,
            "selected_profile_match": True,
            "max_items": 5,
            "max_searches": 1,
            "automatic_query_segmentation": False,
        }
        _, observation["source_preflight"] = run_command("preflight_a2_source_action.py", prepare_source_request(preflight_request), tmp)
    return prepared


def main() -> int:
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    gap = {item["name"]: item for item in fixtures["gap_cases"]}
    source = {item["name"]: item for item in fixtures["source_cases"]}
    obs = {item["name"]: item for item in fixtures["observation_cases"]}
    scenarios = []

    with tempfile.TemporaryDirectory(prefix="a2-wave2-behavioural-") as name:
        tmp = Path(name)
        rc_complete, complete = run_command("build_a2_gap_plan.py", gap["complete-farrier-no-research"]["request"], tmp)
        rc_gap, required_gap = run_command("build_a2_gap_plan.py", gap["horse-owner-required-gap"]["request"], tmp)
        checks = {
            "complete_record_stops_research": rc_complete == 0 and complete["plan_status"] == "no_research_needed" and complete["plan_items"] == [],
            "required_gap_is_named": rc_gap == 0 and required_gap["plan_status"] == "research_required" and required_gap["plan_items"][0]["field_key"] == "organisation.stable_type",
            "required_gap_does_not_reject_or_rescore": required_gap["automatic_rejection"] is False and required_gap["automatic_a1_score_change"] is False,
            "external_actions_zero": complete["external_actions"] == required_gap["external_actions"] == 0,
        }
        scenarios.append({"skill_id": "a2-gap-analysis-and-enrichment-planning", "status": "pass" if all(checks.values()) else "fail", "checks": checks})

        rc_site, site = run_command("preflight_a2_source_action.py", prepare_source_request(source["official-site-synthetic-fixture-allowed"]["request"]), tmp)
        rc_provider, provider = run_command("preflight_a2_source_action.py", prepare_source_request(source["apify-profile-runtime-blocked"]["request"]), tmp)
        checks = {
            "official_site_fixture_allowed": rc_site == 0 and site["preflight_status"] == "allowed_local_fixture",
            "provider_is_runtime_blocked": rc_provider == 0 and provider["preflight_status"] == "prepared_runtime_blocked",
            "provider_missing_gates_are_visible": len(provider["provider_missing_activation_gates"]) == 12,
            "no_external_call_authorised": site["external_call_authorized"] is False and provider["external_call_authorized"] is False,
            "audit_envelopes_complete": site["audit_complete"] is True and provider["audit_complete"] is True,
            "external_actions_zero": site["external_actions"] == provider["external_actions"] == 0,
        }
        scenarios.append({"skill_id": "a2-permitted-enrichment-research", "status": "pass" if all(checks.values()) else "fail", "checks": checks})

        contact_request = prepare_observations(obs["professional-contact-normalised"]["request"], tmp)
        mixed_request = prepare_observations(obs["inferred-horse-count-rejected-personal-email-held"]["request"], tmp)
        rc_contact, contact = run_command("normalise_and_validate_a2_observations.py", contact_request, tmp)
        rc_mixed, mixed = run_command("normalise_and_validate_a2_observations.py", mixed_request, tmp)
        checks = {
            "professional_contact_normalised": rc_contact == 0 and contact["accepted_count"] == 2 and contact["observations"][0]["normalised_value"] == "owner@example.com" and contact["observations"][1]["normalised_value"] == "+185****0100",
            "inferred_horse_count_rejected": rc_mixed == 0 and mixed["observations"][0]["action"] == "reject_observation",
            "personal_email_held": mixed["observations"][1]["action"] == "hold_for_privacy_review",
            "final_confidence_not_assigned": contact["final_confidence_assigned"] is False and mixed["final_confidence_assigned"] is False,
            "no_crm_or_outreach_authority": contact["crm_write_authorized"] is False and contact["outreach_authorized"] is False,
            "external_actions_zero": contact["external_actions"] == mixed["external_actions"] == 0,
        }
        scenarios.append({"skill_id": "a2-field-verification", "status": "pass" if all(checks.values()) else "fail", "checks": checks})

    passed = sum(item["status"] == "pass" for item in scenarios)
    result = {
        "record_type": "wave2_targeted_behavioural_validation",
        "profile": "equinet-a2-enrichment",
        "step": "5C",
        "wave": 2,
        "method": "the exact Wave 2 operator commands were executed through subprocesses against synthetic fixtures in a temporary directory",
        "scenarios": scenarios,
        "scenario_count": len(scenarios),
        "passed": passed,
        "failed": len(scenarios) - passed,
        "overall_status": "pass" if passed == len(scenarios) else "fail",
        "external_calls": 0,
        "external_actions": 0,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["overall_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
