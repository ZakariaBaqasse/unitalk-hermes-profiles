#!/usr/bin/env python3
"""Validate Equinet A2 Step 5C Wave 2 skills and deterministic commands."""
from __future__ import annotations

import hashlib
import json
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from a2_wave2_contracts import ContractError, load_json_strict
from build_a2_gap_plan import analyse as build_gap_plan
from normalise_and_validate_a2_observations import validate_batch
from preflight_a2_source_action import preflight

EVAL = ROOT / "evaluations/step5c"
FIXTURES = EVAL / "fixtures/wave2-cases.json"
OUTPUT = EVAL / "technical-validation.json"
PACKAGE = EVAL / "wave2-draft-package-manifest.json"
REVIEW = EVAL / "A2-WAVE-2-REVIEW.md"
BEHAVIOURAL = EVAL / "behavioural-validation.json"
LANGUAGE = ROOT / "evaluations/foundation-clarifications/language-audit.json"
STEP5B = ROOT / "evaluations/step5b/acceptance-record.json"
ACTIVE = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"
ARCHITECTURE = ROOT / "foundations/contracts/skills/a2-operational-skill-manifest-0.1.0.json"
CATALOGUE = ROOT / "foundations/contracts/business/a2-business-field-catalogue-0.1.1-draft.1.json"
PACKAGES = ROOT / "foundations/contracts/business/a2-minimum-data-packages-0.1.1-draft.1.json"
REGISTER = ROOT / "foundations/contracts/sources/a2-source-register-0.1.1-draft.1.json"
PROVIDERS = ROOT / "foundations/contracts/governance/a2-provider-and-cost-policy-0.1.1-draft.1.json"

SKILLS = [
    ROOT / "skills/a2-gap-analysis-and-enrichment-planning/SKILL.md",
    ROOT / "skills/a2-permitted-enrichment-research/SKILL.md",
    ROOT / "skills/a2-field-verification/SKILL.md",
]
EVAL_FILES = [path.parent / "evals/evals.json" for path in SKILLS]
REFERENCES = [
    ROOT / "skills/a2-field-verification/references/contact-verification.md",
    ROOT / "skills/a2-field-verification/references/professional-verification.md",
    ROOT / "skills/a2-field-verification/references/equine-business-verification.md",
]
COMMANDS = [
    ROOT / "scripts/build_a2_gap_plan.py",
    ROOT / "scripts/preflight_a2_source_action.py",
    ROOT / "scripts/normalise_and_validate_a2_observations.py",
]
SUPPORT_MODULES = [ROOT / "scripts/a2_wave2_contracts.py"]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_source_request(request: dict) -> dict:
    prepared = json.loads(json.dumps(request))
    prepared.setdefault("actor_profile", "equinet-a2-enrichment")
    prepared.setdefault("trigger", prepared.get("named_need"))
    prepared.setdefault("requested_at", "2026-08-27T13:00:00Z")
    prepared.setdefault("run_id", f"W2-{prepared.get('candidate_id', 'UNKNOWN')}")
    return prepared


def prepare_observation_request(request: dict, register: dict, catalogue: dict, providers: dict) -> dict:
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
        observation["source_preflight"] = preflight(prepare_source_request(preflight_request), register, catalogue, providers)
    return prepared


def record_case(bucket: list, failures: list[str], name: str, result: dict, expected: dict, passed: bool) -> None:
    bucket.append({"name": name, "expected": expected, "result": result, "passed": passed})
    if not passed:
        failures.append(f"deterministic case failed: {name}")


def main() -> int:
    failures: list[str] = []
    prerequisite_checks = {}
    step5b = load(STEP5B)
    prerequisite_checks["step5b_approved"] = step5b.get("decision") == "approved_and_promoted"
    prerequisite_checks["step5b_next_gate"] = step5b.get("next_gate") == "Step 5C — Wave 2 Planning, Research and Verification"
    active = load(ACTIVE)
    active_paths = {item["path"]: item["sha256"] for item in active.get("active_files", [])}
    for path in [CATALOGUE, PACKAGES, REGISTER, PROVIDERS, ARCHITECTURE]:
        rel = str(path.relative_to(ROOT))
        prerequisite_checks[f"active:{rel}"] = active_paths.get(rel) == sha(path)
    if not all(prerequisite_checks.values()):
        failures.append("one or more Step 5C prerequisites are not active and hash-valid")

    package_checks = []
    approved_mode = all(
        "**Version:** `0.1.0`" in path.read_text(encoding="utf-8")
        and "**Status:** `WAVE 2 APPROVED — LOCAL NO-INTEGRATION MODE`" in path.read_text(encoding="utf-8")
        for path in SKILLS
        if path.exists()
    ) and all(path.exists() for path in SKILLS)
    for skill_path, eval_path in zip(SKILLS, EVAL_FILES):
        text = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""
        evals = load(eval_path) if eval_path.exists() else {}
        skill_id = skill_path.parent.name
        checks = {
            "frontmatter_name": f"name: {skill_id}" in text,
            "concise_description": "description:" in text.split("---", 2)[1] if text.startswith("---") else False,
            "delivery_status": (
                "WAVE 2 APPROVED — LOCAL NO-INTEGRATION MODE" in text
                if approved_mode
                else "WAVE 2 DRAFT — NOT APPROVED" in text
            ),
            "mission": "## Mission" in text,
            "dependencies": "## Authoritative dependencies" in text,
            "inputs": "## Inputs" in text,
            "command": "## Command" in text,
            "workflow_or_order": "## Workflow" in text or "## Source order" in text,
            "boundaries": "## Boundaries" in text,
            "outputs": "## Outputs" in text,
            "handoff": "## Handoff" in text,
            "three_evals": len(evals.get("evals", [])) == 3,
        }
        package_checks.append({"skill_id": skill_id, "checks": checks, "passed": all(checks.values())})
        if not all(checks.values()):
            failures.append(f"skill package check failed: {skill_id}")
    if not all(path.exists() for path in REFERENCES):
        failures.append("one or more field-verification references are missing")

    compile_checks = []
    for command in [*COMMANDS, *SUPPORT_MODULES]:
        try:
            py_compile.compile(str(command), doraise=True)
            compile_checks.append({"path": str(command.relative_to(ROOT)), "passed": True})
        except Exception as exc:
            compile_checks.append({"path": str(command.relative_to(ROOT)), "passed": False, "error": str(exc)})
            failures.append(f"compile failed: {command.name}")

    fixtures = load(FIXTURES)
    catalogue, packages, register, providers = map(load, [CATALOGUE, PACKAGES, REGISTER, PROVIDERS])
    cases = []

    for case in fixtures["gap_cases"]:
        result = build_gap_plan(case["request"], catalogue, packages, register)
        exp = case["expected"]
        passed = result["plan_status"] == exp["plan_status"] and result["external_actions"] == 0 and result["automatic_rejection"] is False and result["automatic_a1_score_change"] is False
        if "plan_item_count" in exp:
            passed = passed and len(result["plan_items"]) == exp["plan_item_count"]
        if "contains_field" in exp:
            matches = [item for item in result["plan_items"] if item["field_key"] == exp["contains_field"]]
            passed = passed and bool(matches) and matches[0]["need_type"] == exp.get("need_type", matches[0]["need_type"])
        if "excluded_field" in exp:
            passed = passed and all(item["field_key"] != exp["excluded_field"] for item in result["plan_items"])
        if "blocked_field" in exp:
            passed = passed and any(item["field_key"] == exp["blocked_field"] for item in result["blocked_fields"])
        record_case(cases, failures, case["name"], result, exp, passed)

    for case in fixtures["source_cases"]:
        result = preflight(prepare_source_request(case["request"]), register, catalogue, providers)
        exp = case["expected"]
        passed = result["preflight_status"] == exp["preflight_status"] and result["audit_complete"] is True and result["external_call_authorized"] is False and result["external_calls"] == 0 and result["external_actions"] == 0
        if "field_gate" in exp:
            passed = passed and result["field_gate"] == exp["field_gate"]
        if "contains_block" in exp:
            passed = passed and exp["contains_block"] in result["blocks"]
        record_case(cases, failures, case["name"], result, exp, passed)

    for case in fixtures["observation_cases"]:
        prepared_request = prepare_observation_request(case["request"], register, catalogue, providers)
        result = validate_batch(prepared_request, catalogue, register)
        exp = case["expected"]
        passed = result["batch_status"] == exp["batch_status"] and result["external_actions"] == 0 and result["canonical_record_mutated"] is False and result["final_confidence_assigned"] is False
        for key in ("accepted_count", "held_count", "rejected_count"):
            if key in exp:
                passed = passed and result[key] == exp[key]
        if "email" in exp:
            passed = passed and result["observations"][0]["normalised_value"] == exp["email"]
        if "phone" in exp:
            passed = passed and result["observations"][1]["normalised_value"] == exp["phone"]
        if "normalised_value" in exp:
            passed = passed and result["observations"][0]["normalised_value"] == exp["normalised_value"]
        if "field_states" in exp:
            passed = passed and [item["field_state"] for item in result["observations"]] == exp["field_states"]
        if "field_state" in exp:
            passed = passed and all(item["field_state"] == exp["field_state"] for item in result["observations"])
        record_case(cases, failures, case["name"], result, exp, passed)

    forged_request = {
        "candidate_id": "SYN-FORGE-001",
        "segment": "farrier",
        "operating_scope": "synthetic_test",
        "observations": [{
            "observation_id": "OBS-FORGED",
            "field_key": "person.role_title",
            "entity_id": "P-FORGED",
            "raw_value": "Owner",
            "source_id": "prospect_official_website",
            "source_action_status": "allowed_local_fixture",
            "source_preflight": {"preflight_sha256": "forged", "preflight_status": "allowed_local_fixture"},
            "source_url": "https://example.com/team",
            "evidence_id": "EV-FORGED",
            "availability_status": "available",
            "fact_type": "direct_fact",
            "role_current": True,
        }],
    }
    forged_result = validate_batch(forged_request, catalogue, register)
    forged_expected = {"batch_status": "completed_with_rejections", "reason": "source_preflight receipt hash mismatch"}
    forged_pass = (
        forged_result["batch_status"] == "completed_with_rejections"
        and forged_result["rejected_count"] == 1
        and "source_preflight receipt hash mismatch" in forged_result["observations"][0]["errors"]
    )
    record_case(cases, failures, "forged-source-preflight-rejected", forged_result, forged_expected, forged_pass)

    fallback_request = {
        "candidate_id": "SYN-FALLBACK-001",
        "segment": "horse_owner",
        "operating_scope": "synthetic_test",
        "a2_eligibility_status": "eligible",
        "enrichment_mode": "default_minimum_package",
        "contact_path": "general_organisation_fallback",
        "target_role_not_found": False,
        "field_states": {},
    }
    fallback_result = build_gap_plan(fallback_request, catalogue, packages, register)
    fallback_expected = {"plan_status": "held", "reason": "target_role_not_found prerequisite"}
    fallback_pass = fallback_result["plan_status"] == "held" and any("target_role_not_found" in item for item in fallback_result["errors"])
    record_case(cases, failures, "fallback-without-target-role-search-held", fallback_result, fallback_expected, fallback_pass)

    canonical_record = load(ROOT / "foundations/contracts/canonical/examples/valid/valid-synthetic-initialised-record.json")
    canonical_request = {
        "record": canonical_record,
        "wave1_eligibility_result": {"a2_eligibility_status": "eligible"},
        "contact_path": "general_organisation_fallback",
        "target_role_not_found": True,
        "research_exhausted": False,
    }
    canonical_first = build_gap_plan(canonical_request, catalogue, packages, register)
    canonical_second = build_gap_plan(canonical_request, catalogue, packages, register)
    canonical_expected = {"plan_status": "research_required", "input_record_hash": "present", "idempotent": True}
    canonical_pass = (
        canonical_first["plan_status"] == "research_required"
        and bool(canonical_first.get("input_record_sha256"))
        and canonical_first == canonical_second
        and canonical_first["plan_sha256"] == canonical_second["plan_sha256"]
    )
    record_case(cases, failures, "canonical-record-input-idempotent", canonical_first, canonical_expected, canonical_pass)

    with tempfile.TemporaryDirectory(prefix="a2-wave2-json-") as temp_name:
        temp = Path(temp_name)
        duplicate_path = temp / "duplicate.json"
        duplicate_path.write_text('{"candidate_id":"A","candidate_id":"B"}\n', encoding="utf-8")
        nonfinite_path = temp / "nonfinite.json"
        nonfinite_path.write_text('{"value":NaN}\n', encoding="utf-8")
        for name, path, expected_error in [
            ("duplicate-json-key-rejected", duplicate_path, "duplicate JSON key"),
            ("non-finite-json-number-rejected", nonfinite_path, "non-finite JSON number"),
        ]:
            try:
                load_json_strict(path)
                strict_result = {"error": None}
                strict_pass = False
            except ContractError as exc:
                strict_result = {"error": str(exc)}
                strict_pass = expected_error in str(exc)
            record_case(cases, failures, name, strict_result, {"error_contains": expected_error}, strict_pass)

    language_run = subprocess.run([sys.executable, str(ROOT / "scripts/audit_profile_language.py")], cwd=ROOT, capture_output=True, text=True)
    language = load(LANGUAGE)
    language_check = language_run.returncode == 0 and language.get("pass") is True
    if not language_check:
        failures.append("deployment-language audit failed")

    behavioural_checks = {"available": BEHAVIOURAL.exists()}
    if BEHAVIOURAL.exists():
        behavioural = load(BEHAVIOURAL)
        behavioural_checks.update({
            "overall_pass": behavioural.get("overall_status") == "pass",
            "three_scenarios": behavioural.get("scenario_count") == 3 and behavioural.get("passed") == 3,
            "external_actions_zero": behavioural.get("external_actions") == 0,
        })
    else:
        behavioural_checks.update({"overall_pass": False, "three_scenarios": False, "external_actions_zero": False})
        failures.append("targeted behavioural validation is missing")

    result = {
        "step": "5C",
        "wave": 2,
        "status": ("approved_and_promoted" if approved_mode else "ready_for_severine_review_not_approved") if not failures else "validation_failed",
        "prerequisite_checks": prerequisite_checks,
        "skill_count": 3,
        "command_count": 3,
        "supporting_module_count": 1,
        "reference_count": 3,
        "package_checks": package_checks,
        "compile_checks": compile_checks,
        "deterministic_cases": {"total": len(cases), "passed": sum(case["passed"] for case in cases), "cases": cases},
        "targeted_behavioural_validation": behavioural_checks,
        "language_audit": {"files_checked": language.get("files_checked"), "passed": language_check},
        "external_calls": 0,
        "external_actions": 0,
        "approval_required": not approved_mode,
        "promotion_performed": approved_mode,
        "next_gate_after_approval": "Step 5D — Wave 3 Decision, Review and Handoffs",
        "failures": failures,
        "pass": not failures,
    }
    EVAL.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    review_status = "APPROVED AND PROMOTED" if approved_mode else "READY FOR SÉVERINE REVIEW — NOT APPROVED"
    approval_lines = "\n**Approved by:** Séverine, Unitalk Operations  \n**Approved at:** `2026-08-27T13:32:09Z`  " if approved_mode else ""
    approval_effect = (
        "The three Wave 2 skill packages are approved for local no-integration use and Step 5D Wave 3 construction is authorised. This does not activate Web, Apify, Twenty, HubSpot, n8n, outreach, CRM writes, pilot or production status."
        if approved_mode
        else "Approval will promote the three Wave 2 skill packages for local no-integration use and authorise Step 5D Wave 3 construction. It will not activate Web, Apify, Twenty, HubSpot, n8n, outreach, CRM writes, pilot or production status."
    )
    review = f"""# Decision Review — Step 5C Wave 2 Planning, Research and Verification

**Status:** `{review_status}`  {approval_lines}
**Profile:** `equinet-a2-enrichment`  
**Wave:** `2 — Planning, Research and Verification`

## Delivered skill packages

1. `a2-gap-analysis-and-enrichment-planning`;
2. `a2-permitted-enrichment-research`;
3. `a2-field-verification` with contact, professional and equine-business references.

## Decisions proposed

| ID | Decision |
|---|---|
| W2-1 | Require Wave 1 eligibility before gap planning or research. |
| W2-2 | Reuse approved A1 evidence before proposing any new source access. |
| W2-3 | Plan required and conditional fields for the selected minimum package; plan optional fields only when explicitly requested. |
| W2-4 | Keep gap, verification, freshness, conflict, unavailable, not-found and technical-error states distinct. |
| W2-5 | Require one named field need and an active-register source preflight for every new source action. |
| W2-6 | Bound future official-site checks to the active limits, retain explicit professional social URLs, and never open the linked social platform under this permission. |
| W2-7 | Keep HarvestAPI profile and email actions separate and runtime-blocked until every rights, vendor, account, build, retention, budget, audit and connector gate passes. |
| W2-8 | Reject guessed contacts, keep personal email in privacy review, and never infer consent or outreach authority from contact availability. |
| W2-9 | Preserve current role and equine facts as direct claims; reject inferred horse counts and keep person/organisation profile URLs separate. |
| W2-10 | Keep Step 5C local and fixture-backed with zero external actions; final evidence confidence, protected-field decisions and canonical mutation remain in Wave 3. |

## Technical result

- Skill packages: **3/3 present**.
- Focused references: **3/3 present**.
- Deterministic cases: **{sum(case['passed'] for case in cases)}/{len(cases)} PASS**.
- Targeted behavioural scenarios: **{load(BEHAVIOURAL).get('passed', 0) if BEHAVIOURAL.exists() else 0}/3 PASS**.
- External calls/actions: **0/0**.
- Deployment-language audit: **{'PASS' if language_check else 'FAIL'} — {language.get('files_checked')} files checked**.

## Approval effect

{approval_effect}

## Inputs still pending from Equinet

Target roles, final field priorities, reviewer/backup, personal-email disposition, live source permissions, provider budget/retention, HubSpot scopes and source-system access boundaries remain pending. These do not prevent controlled local Wave 2 validation.
"""
    REVIEW.write_text(review, encoding="utf-8")

    files = [*SKILLS, *EVAL_FILES, *REFERENCES, *COMMANDS, *SUPPORT_MODULES, FIXTURES, BEHAVIOURAL, OUTPUT, REVIEW, EVAL / "A2-WAVE-2-IMPLEMENTATION-PLAN.md", STEP5B, ACTIVE, ARCHITECTURE, CATALOGUE, PACKAGES, REGISTER, PROVIDERS]
    files = [path for path in files if path.exists()]
    package_path = EVAL / ("wave2-approved-package-manifest.json" if approved_mode else "wave2-draft-package-manifest.json")
    package = {
        "manifest_id": "equinet-a2-wave2-approved-package" if approved_mode else "equinet-a2-wave2-draft-package",
        "version": "0.1.0" if approved_mode else "0.1.0-draft.1",
        "status": ("approved_and_promoted" if approved_mode else "ready_for_severine_review_not_approved") if not failures else "validation_failed",
        "files": [{"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha(path)} for path in files],
        "file_count": len(files),
        "skills": 3,
        "commands": 3,
        "supporting_modules": 1,
        "references": 3,
        "deterministic_cases": f"{sum(case['passed'] for case in cases)}/{len(cases)} pass",
        "external_calls": 0,
        "external_actions": 0,
        "promotion_performed": approved_mode,
    }
    package_path.write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pass": result["pass"], "skills": 3, "deterministic_cases": package["deterministic_cases"], "behavioural": behavioural_checks, "external_actions": 0, "status": result["status"], "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
