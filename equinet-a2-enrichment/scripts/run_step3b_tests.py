#!/usr/bin/env python3
"""Validate Step 3B minimum packages and deterministic evaluator."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROFILE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from evaluate_a2_minimum_package import evaluate  # noqa: E402

BUSINESS = PROFILE_ROOT / "foundations" / "contracts" / "business"
PACKAGES = BUSINESS / "a2-minimum-data-packages-0.1.0-draft.1.json"
CATALOGUE = BUSINESS / "a2-business-field-catalogue-0.1.0-draft.1.json"
ROOT = PROFILE_ROOT / "evaluations" / "step3b"
FIXTURES = ROOT / "fixtures"
FIXTURE_MANIFEST = FIXTURES / "fixture-manifest.json"
OUTPUT = ROOT / "technical-validation.json"
PACKAGE_MANIFEST = ROOT / "step3b-draft-package-manifest.json"
CONTRACT = PROFILE_ROOT / "foundations" / "A2-MINIMUM-DATA-PACKAGES.md"
REVIEW = ROOT / "A2-MINIMUM-DATA-PACKAGES-REVIEW.md"
BUILDER = SCRIPTS / "build_step3b_minimum_packages.py"
EVALUATOR = SCRIPTS / "evaluate_a2_minimum_package.py"
VALIDATOR = Path(__file__).resolve()
STEP3A_ACCEPTANCE = PROFILE_ROOT / "evaluations" / "step3a" / "acceptance-record.json"
LANGUAGE_AUDIT = PROFILE_ROOT / "evaluations" / "foundation-clarifications" / "language-audit.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_contract(packages: dict, catalogue: dict) -> list[str]:
    errors = []
    expected_top = {
        "package_contract_id", "version", "status", "profile", "canonical_schema_version",
        "business_field_catalogue", "input_contract", "global_rules", "packages",
        "outreach_readiness_boundary", "approval_boundary",
    }
    if set(packages) != expected_top:
        errors.append("top-level package contract keys mismatch")
    if packages.get("version") != "0.1.0-draft.1":
        errors.append("package version must be 0.1.0-draft.1")
    if packages.get("status") != "approved_by_unitalk_as_working_baseline_pending_equinet_confirmation":
        errors.append("package status must be the approved Unitalk working baseline pending Equinet confirmation")
    if packages.get("canonical_schema_version") != "1.0.0":
        errors.append("canonical schema version must be 1.0.0")
    dependency = packages.get("business_field_catalogue", {})
    if dependency.get("version") != catalogue.get("version") or dependency.get("sha256") != sha256(CATALOGUE):
        errors.append("Business Field Catalogue dependency version or hash mismatch")
    if dependency.get("status") != "approved_unitalk_working_baseline_pending_equinet_confirmation":
        errors.append("Business Field Catalogue dependency status mismatch")

    catalogue_keys = {item["field_key"] for item in catalogue["fields"]}
    expected_packages = {"farrier_review_ready": "farrier", "horse_owner_review_ready": "horse_owner"}
    if set(packages.get("packages", {})) != set(expected_packages):
        errors.append("minimum package set mismatch")
    for name, segment in expected_packages.items():
        package = packages.get("packages", {}).get(name, {})
        if package.get("segment") != segment:
            errors.append(f"package segment mismatch: {name}")
        required = package.get("required_verified_fields", [])
        if len(required) != len(set(required)):
            errors.append(f"duplicate required field: {name}")
        for key in required:
            if key not in catalogue_keys:
                errors.append(f"package references unknown field {key}: {name}")
        paths = package.get("contact_paths", {})
        if set(paths) != {"named_target", "general_organisation_fallback"}:
            errors.append(f"contact path set mismatch: {name}")
        for path_name, path in paths.items():
            for key in path.get("required_verified_fields", []) + path.get("at_least_one_verified_field", []) + path.get("documented_exception_fields", []):
                if key not in catalogue_keys:
                    errors.append(f"contact path references unknown field {key}: {name}/{path_name}")
            if not path.get("at_least_one_verified_field"):
                errors.append(f"contact path lacks a verified-channel alternative: {name}/{path_name}")

    missing = packages.get("global_rules", {}).get("missing_required_field", {})
    expected_missing = {
        "field_quality_status": "gap",
        "record_data_quality_status": "incomplete",
        "automatic_rejection": False,
        "automatic_a1_score_change": False,
        "external_action_authorized": False,
        "visible_in_review_package": True,
    }
    if missing != expected_missing:
        errors.append("missing Required field policy mismatch")
    if packages.get("global_rules", {}).get("human_review_required_during_pilot") is not True:
        errors.append("human review must remain required during pilot")
    outreach = packages.get("outreach_readiness_boundary", {})
    if outreach.get("separate_from_a2_review_ready") is not True or outreach.get("current_status") != "unavailable" or outreach.get("send_authorized") is not False:
        errors.append("outreach readiness boundary is unsafe")
    approval = packages.get("approval_boundary", {})
    if approval.get("unitalk_status") != "approved_working_baseline" or approval.get("unitalk_approver") != "Séverine, Unitalk Operations":
        errors.append("Unitalk working-baseline approval metadata is invalid")
    if approval.get("equinet_confirmation") != "pending" or approval.get("live_use_authorized") is not False or approval.get("external_actions_authorized") is not False:
        errors.append("approval boundary exceeds the authorised draft scope")
    return errors


def negative_regressions(packages: dict, catalogue: dict) -> list[dict]:
    cases = []

    def mutate(name: str, expected: str, fn) -> None:
        value = copy.deepcopy(packages)
        fn(value)
        errors = validate_contract(value, catalogue)
        cases.append({"name": name, "expected_error": expected, "errors": errors, "passed": any(expected in item for item in errors)})

    mutate("wrong_catalogue_hash", "dependency version or hash mismatch", lambda value: value["business_field_catalogue"].update(sha256="0" * 64))
    mutate("unknown_required_field", "references unknown field", lambda value: value["packages"]["farrier_review_ready"]["required_verified_fields"].append("person.unknown"))
    mutate("duplicate_required_field", "duplicate required field", lambda value: value["packages"]["farrier_review_ready"]["required_verified_fields"].append(value["packages"]["farrier_review_ready"]["required_verified_fields"][0]))
    mutate("missing_contact_path", "contact path set mismatch", lambda value: value["packages"]["horse_owner_review_ready"]["contact_paths"].pop("general_organisation_fallback"))
    mutate("contact_without_channel", "lacks a verified-channel alternative", lambda value: value["packages"]["farrier_review_ready"]["contact_paths"]["named_target"].update(at_least_one_verified_field=[]))
    mutate("missing_required_auto_reject", "missing Required field policy mismatch", lambda value: value["global_rules"]["missing_required_field"].update(automatic_rejection=True))
    mutate("human_review_disabled", "human review must remain required", lambda value: value["global_rules"].update(human_review_required_during_pilot=False))
    mutate("outreach_send_enabled", "outreach readiness boundary is unsafe", lambda value: value["outreach_readiness_boundary"].update(send_authorized=True))
    mutate("equinet_falsely_confirmed", "approval boundary exceeds", lambda value: value["approval_boundary"].update(equinet_confirmation="approved", live_use_authorized=True))
    mutate("unitalk_approval_removed", "working-baseline approval metadata", lambda value: value["approval_boundary"].update(unitalk_status="draft_for_review"))
    return cases


def render_documents(packages: dict, fixture_results: list[dict]) -> None:
    contract = """# Equinet A2 Minimum Data Packages

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING`  
**Decision timestamp:** `2026-08-26T17:37:05Z`  
**Profile:** `equinet-a2-enrichment`  
**Step:** `3B — Minimum Data Packages`  
**Business Field Catalogue:** `0.1.0-draft.1` Unitalk working baseline

## 1. Purpose

This contract defines the minimum information combinations for an A2 record to become ready for human review. It does not define outreach eligibility and does not authorise any external action.

## 2. Shared rules

- Every field that satisfies a minimum requirement must be `verified`.
- A missing Required field becomes `gap`; the record remains `incomplete`.
- Missing information never automatically rejects the prospect or changes the A1 score.
- Optional fields never block review readiness.
- A material conflict produces `conflict` and a `held` recommendation.
- If research is not exhausted, an incomplete record remains `enrichment_in_progress`.
- If research is exhausted and a required gap remains, the record moves to `held` for human resolution.
- Human review remains mandatory during the pilot.

## 3. Farrier review-ready package

### Core verified fields

1. `person.professional_status`
2. `organisation.business_name`
3. `organisation.public_business_location`
4. `organisation.service_area`
5. `organisation.disciplines`

### Contact path A — named target

- `person.full_name`;
- `person.role_title`;
- `relationship.target_role_priority`;
- at least one of `person.business_email` or `person.business_phone`.

### Contact path B — organisation fallback

- `target_role_not_found = true`;
- at least one of `organisation.business_email` or `organisation.business_phone`.

The missing named-person fields are documented as non-applicable under the approved fallback rather than invented.

## 4. Horse Owner review-ready package

### Core verified fields

1. `organisation.business_name`
2. `organisation.public_business_location`
3. `organisation.stable_type`

The same named-target and organisation-fallback contact paths apply. Exact horse count, horse-count band, discipline and breeds remain optional for A2 review readiness. Their absence does not block review.

## 5. Outreach boundary

A2 review readiness is not outreach readiness. Outreach status remains `unavailable` until HubSpot can authoritatively check consent, suppression, customer, Deal, sequence, owner and business-unit access. Public contact data alone never permits sending.

## 6. Decision status

Séverine approved decisions 3B-1 through 3B-7 as the Unitalk working baseline. Step 3C may begin in draft form. Equinet confirmation remains pending and no live action is enabled.
"""
    CONTRACT.write_text(contract, encoding="utf-8")

    rows = "\n".join(
        f"| `{item['name']}` | {item['segment']} | {item['package_status']} | {item['workflow_recommendation']} | {'PASS' if item['passed'] else 'FAIL'} |"
        for item in fixture_results
    )
    review = f"""# Decision Review — Step 3B Minimum Data Packages

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED AS UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING`  
**Decision timestamp:** `2026-08-26T17:37:05Z`  
**Profile status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`

## 1. Decisions approved as the Unitalk working baseline

| ID | Proposed decision |
|---|---|
| 3B-1 | Require five verified Farrier core fields plus one valid contact path. |
| 3B-2 | Require three verified Horse Owner organisation fields plus one valid contact path. |
| 3B-3 | Accept either a named-target contact path or a documented organisation-general fallback. |
| 3B-4 | Let one verified professional email or business phone satisfy the selected contact path. |
| 3B-5 | Treat a missing Required field as a visible gap and incomplete record, never as automatic rejection. |
| 3B-6 | Keep exact horse count, horse-count band, discipline and breeds optional for Horse Owner review readiness. |
| 3B-7 | Keep outreach readiness unavailable and separate until authoritative HubSpot checks are connected. |

## 2. Expected outcomes exercised

| Scenario | Segment | Package result | Workflow recommendation | Test |
|---|---|---|---|---:|
{rows}

## 3. Approval scope

This approval authorises preparation of Step 3C in draft form. Final client confirmation remains pending. It does not authorise source access, enrichment execution, provider calls, CRM access/write, outreach, pilot or production use.
"""
    REVIEW.write_text(review, encoding="utf-8")


def main() -> int:
    packages = load(PACKAGES)
    catalogue = load(CATALOGUE)
    contract_errors = validate_contract(packages, catalogue)
    fixture_manifest = load(FIXTURE_MANIFEST)
    fixture_results = []
    failures = list(contract_errors)
    for case in fixture_manifest["cases"]:
        snapshot = load(FIXTURES / case["fixture"])
        result = evaluate(snapshot, packages)
        passed = result["package_status"] == case["expected_package_status"] and result["workflow_recommendation"] == case["expected_workflow_recommendation"]
        fixture_results.append({
            "name": case["name"],
            "segment": snapshot["segment"],
            "package_status": result["package_status"],
            "workflow_recommendation": result["workflow_recommendation"],
            "missing_required_fields": result["missing_required_fields"],
            "unsatisfied_contact_requirements": result["unsatisfied_contact_requirements"],
            "automatic_rejection": result["automatic_rejection"],
            "automatic_a1_score_change": result["automatic_a1_score_change"],
            "external_action_authorized": result["external_action_authorized"],
            "passed": passed,
        })
        if not passed:
            failures.append(f"fixture failed: {case['name']}")
        if result["automatic_rejection"] or result["automatic_a1_score_change"] or result["external_action_authorized"]:
            failures.append(f"unsafe outcome: {case['name']}")

    negative = negative_regressions(packages, catalogue)
    for case in negative:
        if not case["passed"]:
            failures.append(f"negative regression failed: {case['name']}")

    render_documents(packages, fixture_results)
    documentation_checks = {
        "contract_version": "**Version:** `0.1.0-draft.1`" in CONTRACT.read_text(encoding="utf-8"),
        "missing_required_policy": "never automatically rejects" in CONTRACT.read_text(encoding="utf-8"),
        "outreach_separate": "A2 review readiness is not outreach readiness" in CONTRACT.read_text(encoding="utf-8"),
        "review_decisions": all(f"| 3B-{number} |" in REVIEW.read_text(encoding="utf-8") for number in range(1, 8)),
        "review_pending": "APPROVED AS UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING" in REVIEW.read_text(encoding="utf-8"),
    }
    for name, passed in documentation_checks.items():
        if not passed:
            failures.append(f"documentation check failed: {name}")

    cli_fixture = FIXTURES / "farrier_named_email_ready.json"
    cli = subprocess.run([sys.executable, str(EVALUATOR), str(cli_fixture)], cwd=PROFILE_ROOT, capture_output=True, text=True)
    cli_result = json.loads(cli.stdout) if cli.returncode == 0 else {}
    cli_check = cli.returncode == 0 and cli_result.get("package_status") == "review_ready"
    if not cli_check:
        failures.append("evaluator CLI smoke test failed")

    language = load(LANGUAGE_AUDIT)
    if language.get("pass") is not True:
        failures.append("deployment-language audit failed")

    result = {
        "step": "3B",
        "version": packages["version"],
        "approval_state": "approved_unitalk_working_baseline_pending_equinet_confirmation",
        "package_contract": {"path": str(PACKAGES.relative_to(PROFILE_ROOT)), "sha256": sha256(PACKAGES)},
        "catalogue_dependency": {"path": str(CATALOGUE.relative_to(PROFILE_ROOT)), "sha256": sha256(CATALOGUE), "passed": packages["business_field_catalogue"]["sha256"] == sha256(CATALOGUE)},
        "contract_validation": {"errors": contract_errors, "passed": not contract_errors},
        "fixture_summary": {
            "total": len(fixture_results),
            "passed": sum(item["passed"] for item in fixture_results),
            "failed": sum(not item["passed"] for item in fixture_results),
            "cases": fixture_results,
        },
        "negative_regressions": {
            "total": len(negative),
            "passed": sum(item["passed"] for item in negative),
            "failed": sum(not item["passed"] for item in negative),
            "cases": negative,
        },
        "documentation_checks": documentation_checks,
        "cli_smoke_test": cli_check,
        "language_audit": {"files_checked": language.get("files_checked"), "findings": len(language.get("findings", [])), "passed": language.get("pass") is True},
        "external_actions": 0,
        "equinet_confirmation": "pending",
        "next_gate_after_approval": "Step 3C — A2 Source Register",
        "failures": failures,
        "pass": not failures,
    }
    ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    fixture_paths = [FIXTURES / case["fixture"] for case in fixture_manifest["cases"]]
    package_paths = [PACKAGES, CATALOGUE, BUILDER, EVALUATOR, VALIDATOR, FIXTURE_MANIFEST, CONTRACT, REVIEW, OUTPUT, *fixture_paths]
    package_paths = sorted(set(package_paths))
    manifest = {
        "manifest_id": "equinet-a2-step3b-draft-package",
        "version": packages["version"],
        "status": "approved_unitalk_working_baseline_pending_equinet_confirmation",
        "files": [{"path": str(path.relative_to(PROFILE_ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in package_paths],
        "file_count": len(package_paths),
        "external_actions": 0,
    }
    PACKAGE_MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "pass": result["pass"],
        "approval_state": result["approval_state"],
        "fixtures": f"{result['fixture_summary']['passed']}/{result['fixture_summary']['total']}",
        "negative_regressions": f"{result['negative_regressions']['passed']}/{result['negative_regressions']['total']}",
        "cli_smoke_test": cli_check,
        "review": str(REVIEW),
        "manifest": str(PACKAGE_MANIFEST),
        "failures": failures,
    }, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
