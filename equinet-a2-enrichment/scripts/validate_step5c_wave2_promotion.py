#!/usr/bin/env python3
"""Post-promotion validation for Equinet A2 Step 5C Wave 2."""
from __future__ import annotations

import hashlib
import json
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from a2_wave2_contracts import ContractError, load_json_strict
from build_a2_gap_plan import analyse as build_gap_plan
from normalise_and_validate_a2_observations import validate_batch
from preflight_a2_source_action import preflight
from validate_step5c_wave2 import prepare_observation_request, prepare_source_request

EVAL = ROOT / "evaluations/step5c"
RUNTIME = ROOT / "foundations/contracts/skills/a2-wave2-runtime-manifest-0.1.0.json"
ACCEPTANCE = EVAL / "acceptance-record.json"
PROMOTION = EVAL / "wave2-promotion-manifest.json"
ACTIVE = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"
FIXTURES = EVAL / "fixtures/wave2-cases.json"
TECH = EVAL / "technical-validation.json"
BEHAVIOURAL = EVAL / "behavioural-validation.json"
LANGUAGE = ROOT / "evaluations/foundation-clarifications/language-audit.json"
OUTPUT = EVAL / "post-promotion-validation.json"
CATALOGUE = ROOT / "foundations/contracts/business/a2-business-field-catalogue-0.1.1-draft.1.json"
PACKAGES = ROOT / "foundations/contracts/business/a2-minimum-data-packages-0.1.1-draft.1.json"
REGISTER = ROOT / "foundations/contracts/sources/a2-source-register-0.1.1-draft.1.json"
PROVIDERS = ROOT / "foundations/contracts/governance/a2-provider-and-cost-policy-0.1.1-draft.1.json"
SKILLS = [
    ROOT / "skills/a2-gap-analysis-and-enrichment-planning/SKILL.md",
    ROOT / "skills/a2-permitted-enrichment-research/SKILL.md",
    ROOT / "skills/a2-field-verification/SKILL.md",
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add(cases: list, errors: list[str], name: str, passed: bool) -> None:
    cases.append({"name": name, "passed": passed})
    if not passed:
        errors.append(f"post-promotion case failed: {name}")


def main() -> int:
    errors: list[str] = []
    runtime, acceptance, promotion, active = map(load, [RUNTIME, ACCEPTANCE, PROMOTION, ACTIVE])
    tech, behavioural, fixtures = map(load, [TECH, BEHAVIOURAL, FIXTURES])
    catalogue, packages, register, providers = map(load, [CATALOGUE, PACKAGES, REGISTER, PROVIDERS])

    if runtime.get("status") != "approved_local_no_integration" or acceptance.get("decision") != "approved_and_promoted":
        errors.append("Wave 2 approval state mismatch")
    if acceptance.get("approved_decisions") != [f"W2-{number}" for number in range(1, 11)]:
        errors.append("Wave 2 decision set mismatch")
    if tech.get("pass") is not True or tech.get("deterministic_cases", {}).get("passed") != 24:
        errors.append("pre-promotion technical validation mismatch")
    if behavioural.get("overall_status") != "pass" or behavioural.get("passed") != 3:
        errors.append("behavioural validation mismatch")
    for skill in SKILLS:
        text = skill.read_text(encoding="utf-8")
        if "**Version:** `0.1.0`" not in text or "**Status:** `WAVE 2 APPROVED — LOCAL NO-INTEGRATION MODE`" not in text:
            errors.append(f"skill not promoted: {skill.parent.name}")
    for section in ("skills", "references", "commands", "supporting_modules"):
        for item in runtime.get(section, []):
            for path_key, hash_key in [("path", "sha256"), ("evals_path", "evals_sha256")]:
                if path_key not in item:
                    continue
                path = ROOT / item[path_key]
                if not path.is_file() or sha(path) != item[hash_key]:
                    errors.append(f"runtime manifest hash mismatch: {item[path_key]}")
    for item in active.get("active_files", []):
        path = ROOT / item["path"]
        if not path.is_file() or sha(path) != item["sha256"]:
            errors.append(f"active foundation hash mismatch: {item['path']}")
    for item in promotion.get("files", []):
        path = ROOT / item["path"]
        if not path.is_file() or sha(path) != item["sha256"]:
            errors.append(f"promotion file hash mismatch: {item['path']}")
    if sha(RUNTIME) != acceptance.get("runtime_manifest_sha256"):
        errors.append("acceptance runtime manifest hash mismatch")
    active_paths = {item.get("path") for item in active.get("active_files", [])}
    later_wave_active = "foundations/contracts/skills/a2-wave3-runtime-manifest-0.1.0.json" in active_paths
    if not later_wave_active and sha(ACTIVE) != acceptance.get("active_foundation_manifest_sha256"):
        errors.append("acceptance active foundation hash mismatch")
    if not later_wave_active and promotion.get("active_foundation_manifest", {}).get("sha256") != sha(ACTIVE):
        errors.append("promotion active foundation hash mismatch")
    if later_wave_active and "foundations/contracts/skills/a2-wave2-runtime-manifest-0.1.0.json" not in active_paths:
        errors.append("Wave 2 runtime manifest missing from later active foundation")

    cases: list[dict] = []
    for case in fixtures["gap_cases"]:
        result = build_gap_plan(case["request"], catalogue, packages, register)
        expected = case["expected"]
        passed = result["plan_status"] == expected["plan_status"] and result["external_actions"] == 0
        if "plan_item_count" in expected:
            passed = passed and len(result["plan_items"]) == expected["plan_item_count"]
        if "contains_field" in expected:
            matches = [item for item in result["plan_items"] if item["field_key"] == expected["contains_field"]]
            passed = passed and bool(matches) and matches[0]["need_type"] == expected.get("need_type", matches[0]["need_type"])
        if "excluded_field" in expected:
            passed = passed and all(item["field_key"] != expected["excluded_field"] for item in result["plan_items"])
        if "blocked_field" in expected:
            passed = passed and any(item["field_key"] == expected["blocked_field"] for item in result["blocked_fields"])
        add(cases, errors, case["name"], passed)

    for case in fixtures["source_cases"]:
        result = preflight(prepare_source_request(case["request"]), register, catalogue, providers)
        expected = case["expected"]
        passed = result["preflight_status"] == expected["preflight_status"] and result["audit_complete"] is True and result["external_call_authorized"] is False and result["external_actions"] == 0
        if "field_gate" in expected:
            passed = passed and result["field_gate"] == expected["field_gate"]
        if "contains_block" in expected:
            passed = passed and expected["contains_block"] in result["blocks"]
        add(cases, errors, case["name"], passed)

    for case in fixtures["observation_cases"]:
        result = validate_batch(prepare_observation_request(case["request"], register, catalogue, providers), catalogue, register)
        expected = case["expected"]
        passed = result["batch_status"] == expected["batch_status"] and result["external_actions"] == 0 and result["canonical_record_mutated"] is False
        for key in ("accepted_count", "held_count", "rejected_count"):
            if key in expected:
                passed = passed and result[key] == expected[key]
        if "email" in expected:
            passed = passed and result["observations"][0]["normalised_value"] == expected["email"]
        if "phone" in expected:
            passed = passed and result["observations"][1]["normalised_value"] == expected["phone"]
        if "normalised_value" in expected:
            passed = passed and result["observations"][0]["normalised_value"] == expected["normalised_value"]
        if "field_states" in expected:
            passed = passed and [item["field_state"] for item in result["observations"]] == expected["field_states"]
        if "field_state" in expected:
            passed = passed and all(item["field_state"] == expected["field_state"] for item in result["observations"])
        add(cases, errors, case["name"], passed)

    forged = {
        "candidate_id": "SYN-FORGE-001", "segment": "farrier", "operating_scope": "synthetic_test",
        "observations": [{
            "observation_id": "OBS-FORGED", "field_key": "person.role_title", "entity_id": "P-FORGED",
            "raw_value": "Owner", "source_id": "prospect_official_website", "source_action_status": "allowed_local_fixture",
            "source_preflight": {"preflight_sha256": "forged", "preflight_status": "allowed_local_fixture"},
            "source_url": "https://example.com/team", "evidence_id": "EV-FORGED", "availability_status": "available",
            "fact_type": "direct_fact", "role_current": True,
        }],
    }
    forged_result = validate_batch(forged, catalogue, register)
    add(cases, errors, "forged-source-preflight-rejected", forged_result["rejected_count"] == 1 and "source_preflight receipt hash mismatch" in forged_result["observations"][0]["errors"])

    fallback = {
        "candidate_id": "SYN-FALLBACK-001", "segment": "horse_owner", "operating_scope": "synthetic_test",
        "a2_eligibility_status": "eligible", "enrichment_mode": "default_minimum_package",
        "contact_path": "general_organisation_fallback", "target_role_not_found": False, "field_states": {},
    }
    fallback_result = build_gap_plan(fallback, catalogue, packages, register)
    add(cases, errors, "fallback-without-target-role-search-held", fallback_result["plan_status"] == "held" and any("target_role_not_found" in item for item in fallback_result["errors"]))

    canonical = load(ROOT / "foundations/contracts/canonical/examples/valid/valid-synthetic-initialised-record.json")
    canonical_request = {"record": canonical, "wave1_eligibility_result": {"a2_eligibility_status": "eligible"}, "contact_path": "general_organisation_fallback", "target_role_not_found": True, "research_exhausted": False}
    first = build_gap_plan(canonical_request, catalogue, packages, register)
    second = build_gap_plan(canonical_request, catalogue, packages, register)
    add(cases, errors, "canonical-record-input-idempotent", first["plan_status"] == "research_required" and first == second and bool(first.get("input_record_sha256")))

    with tempfile.TemporaryDirectory(prefix="a2-wave2-post-json-") as temp_name:
        temp = Path(temp_name)
        duplicate = temp / "duplicate.json"; duplicate.write_text('{"a":1,"a":2}\n', encoding="utf-8")
        nonfinite = temp / "nonfinite.json"; nonfinite.write_text('{"a":NaN}\n', encoding="utf-8")
        for name, path, expected in [("duplicate-json-key-rejected", duplicate, "duplicate JSON key"), ("non-finite-json-number-rejected", nonfinite, "non-finite JSON number")]:
            try:
                load_json_strict(path); passed = False
            except ContractError as exc:
                passed = expected in str(exc)
            add(cases, errors, name, passed)

    language = load(LANGUAGE)
    if language.get("pass") is not True:
        errors.append("language audit failed")
    result = {
        "step": "5C",
        "stage": "post_promotion",
        "status": "approved_and_promoted" if not errors else "promotion_validation_failed",
        "skills": 3,
        "deterministic_replay": {"total": len(cases), "passed": sum(item["passed"] for item in cases), "cases": cases},
        "behavioural_replay": {"total": behavioural.get("scenario_count"), "passed": behavioural.get("passed"), "status": behavioural.get("overall_status")},
        "active_foundation_files": len(active.get("active_files", [])),
        "language_audit": {"files_checked": language.get("files_checked"), "passed": language.get("pass") is True},
        "external_calls": 0,
        "external_actions": 0,
        "next_gate": "Step 5D — Wave 3 Decision, Review and Handoffs",
        "failures": errors,
        "pass": not errors,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pass": result["pass"], "replay": f"{result['deterministic_replay']['passed']}/{result['deterministic_replay']['total']}", "behavioural": f"{result['behavioural_replay']['passed']}/{result['behavioural_replay']['total']}", "active_foundation_files": result["active_foundation_files"], "external_actions": 0, "failures": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
