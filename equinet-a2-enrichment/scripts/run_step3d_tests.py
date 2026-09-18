#!/usr/bin/env python3
"""Run Step 3D evidence, verification, confidence and freshness tests."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROFILE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from evaluate_a2_evidence_confidence import evaluate  # noqa: E402

ROOT = PROFILE_ROOT / "evaluations" / "step3d"
POLICY = PROFILE_ROOT / "foundations" / "contracts" / "evidence" / "a2-evidence-verification-confidence-freshness-policy-0.1.0-draft.1.json"
FIXTURES = ROOT / "fixtures" / "evidence-cases.json"
SOURCE_REGISTER = PROFILE_ROOT / "foundations" / "contracts" / "sources" / "a2-source-register-0.1.0-draft.1.json"
FIELD_CATALOGUE = PROFILE_ROOT / "foundations" / "contracts" / "business" / "a2-business-field-catalogue-0.1.0-draft.1.json"
STATE_MODEL = PROFILE_ROOT / "foundations" / "contracts" / "a2-state-model-0.1.0.json"
CONTRACT = PROFILE_ROOT / "foundations" / "A2-EVIDENCE-VERIFICATION-CONFIDENCE-FRESHNESS-POLICY.md"
REVIEW = ROOT / "A2-EVIDENCE-POLICY-REVIEW.md"
OUTPUT = ROOT / "technical-validation.json"
MANIFEST = ROOT / "step3d-draft-package-manifest.json"
LANGUAGE = PROFILE_ROOT / "evaluations" / "foundation-clarifications" / "language-audit.json"
BUILDER = SCRIPTS / "build_step3d_evidence_policy.py"
EVALUATOR = SCRIPTS / "evaluate_a2_evidence_confidence.py"
VALIDATOR = Path(__file__).resolve()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def with_fixture_preflight(case: dict) -> dict:
    """Adapt historical fixtures to the current hashed source-preflight contract."""
    value = copy.deepcopy(case)
    if value.get("source_id") in {"a1_approved_handoff", "a1_directory_evidence_reuse"}:
        return value
    receipt = {
        "source_id": value.get("source_id"),
        "field_key": value.get("claim_key"),
        "preflight_status": "completed_fixture" if value.get("source_gate_passed") is True else "blocked",
        "external_actions": 0,
    }
    receipt["preflight_sha256"] = hashlib.sha256(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    value["source_preflight"] = receipt
    return value


def validate_policy(policy: dict) -> list[str]:
    errors = []
    if policy.get("status") != "approved_by_unitalk_as_working_baseline_pending_equinet_confirmation":
        errors.append("policy status must be the approved Unitalk working baseline pending Equinet confirmation")
    approval = policy.get("unitalk_approval", {})
    if approval.get("approver") != "Séverine, Unitalk Operations" or approval.get("scope") != "decisions_3D_1_through_3D_10_and_protected_SOUL_sync":
        errors.append("Unitalk approval metadata is invalid")
    for dependency in policy.get("dependencies", []):
        path = PROFILE_ROOT / dependency["path"]
        if not path.exists() or sha256(path) != dependency["sha256"]:
            errors.append(f"dependency hash mismatch: {dependency['path']}")
    dimensions = policy.get("confidence_dimensions", {})
    if sum(item.get("maximum", 0) for item in dimensions.values()) != 100:
        errors.append("confidence dimension maximums must total 100")
    if policy.get("confidence_bands") != [
        {"level": "high", "minimum": 80, "maximum": 100},
        {"level": "medium", "minimum": 60, "maximum": 79},
        {"level": "low", "minimum": 0, "maximum": 59},
    ]:
        errors.append("confidence bands mismatch")
    caps = {item["condition"]: item["maximum_score"] for item in policy.get("caps", [])}
    expected_caps = {"identity_match_unresolved": 39, "material_conflict": 39, "required_claim_supported_only_by_reasonable_inference": 59, "time_sensitive_claim_is_stale": 59, "source_rights_or_runtime_gate_not_passed": 0}
    if caps != expected_caps:
        errors.append("confidence caps mismatch")

    state_model = load(STATE_MODEL)["canonical_vocabularies"]
    for name in ["verification_status", "confidence_level", "freshness_status", "conflict_status", "claim_type", "reliability_level"]:
        if name not in state_model:
            errors.append(f"state vocabulary missing: {name}")
    source_ids = {item["source_id"] for item in load(SOURCE_REGISTER)["sources"]}
    if not set(policy.get("source_rules", {})).issubset(source_ids):
        errors.append("policy references unknown source ID")
    for source_id in ["apify_harvestapi_linkedin_profile_search", "apify_harvestapi_email_search"]:
        if policy["source_rules"].get(source_id, {}).get("current_status") != "blocked":
            errors.append(f"runtime-blocked source was activated: {source_id}")
    if policy["source_rules"].get("search_engine_discovery", {}).get("retained_evidence") is not False:
        errors.append("search discovery was promoted to retained evidence")

    field_keys = {item["field_key"] for item in load(FIELD_CATALOGUE)["fields"]}
    unknown_freshness = sorted(set(policy.get("field_freshness_days", {})) - field_keys)
    if unknown_freshness:
        errors.append(f"freshness policy references unknown fields: {unknown_freshness}")
    for key, days in policy.get("field_freshness_days", {}).items():
        if not isinstance(days, int) or days <= 0:
            errors.append(f"invalid freshness window: {key}")
    principles = policy.get("principles", {})
    for key in ["confidence_is_not_icp_score", "a2_never_calculates_a1_score", "unknown_is_not_negative_or_fact", "blocked_source_cannot_support_a_claim", "search_snippet_is_discovery_only", "professional_contact_does_not_create_outreach_consent", "a1_evidence_keeps_original_provenance_and_confidence", "official_website_can_confirm_explicit_self_controlled_fact_without_visible_date"]:
        if principles.get(key) is not True:
            errors.append(f"required principle missing: {key}")
    return errors


def negative_regressions(policy: dict) -> list[dict]:
    cases = []
    def run(name, expected, fn):
        value = copy.deepcopy(policy); fn(value); errs = validate_policy(value)
        cases.append({"name": name, "expected_error": expected, "errors": errs, "passed": any(expected in item for item in errs)})
    run("dependency_hash", "dependency hash mismatch", lambda v: v["dependencies"][0].update(sha256="0" * 64))
    run("dimension_total", "maximums must total 100", lambda v: v["confidence_dimensions"]["identity_match"].update(maximum=21))
    run("band_overlap", "confidence bands mismatch", lambda v: v["confidence_bands"][1].update(minimum=59))
    run("cap_removed", "confidence caps mismatch", lambda v: v["caps"].pop())
    run("unknown_source", "unknown source ID", lambda v: v["source_rules"].update(unknown_source={"authority": "blocked_or_unverified"}))
    run("linkedin_activated", "runtime-blocked source was activated", lambda v: v["source_rules"]["apify_harvestapi_linkedin_profile_search"].update(current_status="active"))
    run("email_search_activated", "runtime-blocked source was activated", lambda v: v["source_rules"]["apify_harvestapi_email_search"].update(current_status="active"))
    run("snippet_evidence", "search discovery was promoted", lambda v: v["source_rules"]["search_engine_discovery"].update(retained_evidence=True))
    run("unknown_freshness_field", "freshness policy references unknown fields", lambda v: v["field_freshness_days"].update({"unknown.field": 365}))
    run("a2_scoring", "required principle missing", lambda v: v["principles"].update(a2_never_calculates_a1_score=False))
    run("approval_removed", "Unitalk approval metadata is invalid", lambda v: v["unitalk_approval"].update(scope="draft_only"))
    return cases


def render(policy: dict, cases: list[dict]) -> None:
    windows = "\n".join(f"| `{key}` | {days} days |" for key, days in policy["field_freshness_days"].items())
    rows = "\n".join(f"| `{item['name']}` | {item['source_id']} | {item['confidence_score']} | {item['confidence_level']} | {item['verification_status']} | {'PASS' if item['passed'] else 'FAIL'} |" for item in cases)
    contract = f"""# Equinet A2 Evidence, Verification, Confidence and Freshness Policy

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING`  
**Decision timestamp:** `2026-08-26T18:53:52Z`  
**Profile:** `equinet-a2-enrichment`  
**Step:** `3D — Evidence, Verification, Confidence and Freshness Policies`

## 1. Purpose

This policy assesses the reliability of a field-level A2 claim. It does not measure commercial attractiveness and never replaces the A1 ICP score.

## 2. Confidence calculation

| Dimension | Maximum |
|---|---:|
| Identity match | 20 |
| Source authority | 20 |
| Claim directness | 20 |
| Freshness | 20 |
| Corroboration | 10 |
| Consistency | 10 |
| **Total** | **100** |

Bands: High `80–100`, Medium `60–79`, Low `0–59`.

## 3. Caps

- unresolved identity: maximum `39`;
- material conflict: maximum `39`;
- Required claim supported only by inference: maximum `59`;
- stale time-sensitive claim: maximum `59`;
- source rights/runtime gate not passed: `0` and unusable as evidence.

## 4. Verification states

- `verified`: High confidence, exact identity, direct fact, permitted source, acceptable freshness and no material conflict;
- `partially_verified`: Medium confidence or a documented limitation;
- `unverified`: Low confidence or insufficient evidence;
- `contradicted`: material conflict;
- `not_applicable`: field not applicable under the package/fallback;
- `error`: technical validation failure.

## 5. Source treatment

- A1 evidence preserves its inherited provenance and confidence.
- HubSpot is authoritative only after the read-only connection and permissions pass.
- A current official website can confirm explicit facts controlled by the business without a visible publication date.
- LinkedIn profile data through Apify remains unusable until every rights, vendor and runtime gate passes.
- Apify email search remains separate from LinkedIn provenance and requires exact identity/company match plus provider verification.
- Search snippets remain discovery-only.

## 6. Proposed freshness windows

| Field | Maximum age |
|---|---:|
{windows}

A current official website statement about a fact controlled by the business is treated as current even when no publication date is displayed, unless a stale or conflicting signal exists.

## 7. Conflict handling

An authoritative source takes precedence operationally, but every material conflict remains visible. A current-role disagreement between an official website and LinkedIn produces a hold. Resolution requires a reviewer and reason; prior evidence is preserved.

## 8. Email rules

- Officially published professional email may be verified from one exact official source.
- Future Apify email results require exact identity/company match and provider verification.
- Personal email is discarded by default pending Equinet approval.
- Deliverability does not create outreach consent.
- Provider email must never be labelled as LinkedIn-sourced.

## 9. Decision boundary

Séverine approved decisions 3D-1 through 3D-10 as the Unitalk working baseline and authorised the protected SOUL synchronisation. Equinet confirmation of freshness windows, relevant activity types and personal-email policy remains pending. No source activation, provider call, CRM write or outreach is authorised.
"""
    CONTRACT.write_text(contract, encoding="utf-8")
    review = f"""# Decision Review — Step 3D Evidence Policy

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED AS UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING`  
**Decision timestamp:** `2026-08-26T18:53:52Z`

## Decisions approved as the Unitalk working baseline

| ID | Proposed decision |
|---|---|
| 3D-1 | Use the six weighted dimensions `20/20/20/20/10/10`. |
| 3D-2 | Use High `80–100`, Medium `60–79`, Low `0–59`. |
| 3D-3 | Cap unresolved identity and material conflicts at `39`. |
| 3D-4 | Cap Required claims supported only by inference and stale time-sensitive claims at `59`. |
| 3D-5 | Give evidence from a source with an unmet rights/runtime gate a score of `0`. |
| 3D-6 | Let a current official website verify explicit self-controlled facts without a visible date. |
| 3D-7 | Keep search snippets discovery-only and preserve inherited A1 evidence confidence. |
| 3D-8 | Treat Apify email search as independent provider evidence; require identity/company match and never infer consent. |
| 3D-9 | Apply the proposed field freshness windows, subject to Equinet confirmation. |
| 3D-10 | Let verified material evidence trigger an A1 requalification signal without A2 calculating a score. |

## Deterministic cases

| Case | Source | Score | Confidence | Verification | Test |
|---|---|---:|---|---|---:|
{rows}

## Approval scope

This approval establishes the Unitalk working baseline and authorises preparation of Step 3E in draft form. It does not activate a source, provider, CRM action, outreach, pilot or production workflow.
"""
    REVIEW.write_text(review, encoding="utf-8")


def main() -> int:
    policy = load(POLICY)
    policy_errors = validate_policy(policy)
    fixture_data = load(FIXTURES)
    fixture_results = []
    failures = list(policy_errors)
    for case in fixture_data["cases"]:
        result = evaluate(with_fixture_preflight(case), policy)
        expected = case["expected"]
        passed = all(result[key] == value for key, value in expected.items()) and not result["errors"]
        fixture_results.append({"name": case["name"], **result, "expected": expected, "passed": passed})
        if not passed:
            failures.append(f"fixture failed: {case['name']}")
        if result["a1_score_changed"] or result["outreach_authorized"]:
            failures.append(f"unsafe result: {case['name']}")

    negative = negative_regressions(policy)
    if any(not item["passed"] for item in negative):
        failures.append("negative regression failed")
    render(policy, fixture_results)
    documentation_checks = {
        "contract_version": "**Version:** `0.1.0-draft.1`" in CONTRACT.read_text(encoding="utf-8"),
        "confidence_is_not_score": "never replaces the A1 ICP score" in CONTRACT.read_text(encoding="utf-8"),
        "source_gate_zero": "source rights/runtime gate not passed: `0`" in CONTRACT.read_text(encoding="utf-8"),
        "review_decisions": all(f"| 3D-{number} |" in REVIEW.read_text(encoding="utf-8") for number in range(1, 11)),
        "review_pending": "APPROVED AS UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING" in REVIEW.read_text(encoding="utf-8"),
    }
    for name, passed in documentation_checks.items():
        if not passed:
            failures.append(f"documentation check failed: {name}")
    language = load(LANGUAGE)
    if language.get("pass") is not True:
        failures.append("language audit failed")

    result = {
        "step": "3D", "version": policy["version"], "approval_state": "approved_unitalk_working_baseline_pending_equinet_confirmation",
        "policy": {"path": str(POLICY.relative_to(PROFILE_ROOT)), "sha256": sha256(POLICY)},
        "policy_validation": {"errors": policy_errors, "passed": not policy_errors},
        "fixtures": {"total": len(fixture_results), "passed": sum(item["passed"] for item in fixture_results), "cases": fixture_results},
        "negative_regressions": {"total": len(negative), "passed": sum(item["passed"] for item in negative), "cases": negative},
        "documentation_checks": documentation_checks,
        "language_audit": {"files_checked": language.get("files_checked"), "findings": len(language.get("findings", [])), "passed": language.get("pass") is True},
        "external_actions": 0, "a1_score_changes": 0, "runtime_activation": False,
        "next_gate_after_approval": "Step 3E — Protected Fields and Conflict Policy",
        "failures": failures, "pass": not failures,
    }
    ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    package_paths = [POLICY, FIXTURES, BUILDER, EVALUATOR, VALIDATOR, CONTRACT, REVIEW, OUTPUT]
    manifest = {"manifest_id": "equinet-a2-step3d-draft-package", "version": policy["version"], "status": "approved_unitalk_working_baseline_pending_equinet_confirmation", "files": [{"path": str(path.relative_to(PROFILE_ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in package_paths], "file_count": len(package_paths), "external_actions": 0}
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pass": result["pass"], "approval_state": result["approval_state"], "fixtures": f"{result['fixtures']['passed']}/{result['fixtures']['total']}", "negative_regressions": f"{result['negative_regressions']['passed']}/{result['negative_regressions']['total']}", "review": str(REVIEW), "manifest": str(MANIFEST), "failures": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
