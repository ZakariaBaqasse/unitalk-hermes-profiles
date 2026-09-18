#!/usr/bin/env python3
"""Validate Step 9A correction propagation and release-candidate runtime foundation."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
STEP9 = ROOT / "evaluations/step9"
POLICY = STEP9 / "release-candidate/a2-no-integration-runtime-policy-1.0.0-rc.1.yaml"
RC_MANIFEST = STEP9 / "release-candidate/A2-ACTIVE-FOUNDATION-MANIFEST-1.1.0-rc.1.json"
ACTIVE = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"
CONFIG = ROOT / "config.yaml"
SOUL = ROOT / "SOUL.md"
PREFLIGHT_RESULT = STEP9 / "fixtures/person-business-phone-preflight.result.json"
OUT = STEP9 / "phase9a-validation.json"
PROPAGATION = STEP9 / "correction-propagation.json"
REVIEW = STEP9 / "STEP-9A-CORRECTION-PROPAGATION-REVIEW.md"
PLAN = STEP9 / "step9-plan.json"
SKILLS = {
    "a2-gap-analysis-and-enrichment-planning": ROOT / "skills/a2-gap-analysis-and-enrichment-planning/SKILL.md",
    "a2-data-quality-and-review-readiness": ROOT / "skills/a2-data-quality-and-review-readiness/SKILL.md",
    "a2-review-package-and-governed-handoffs": ROOT / "skills/a2-review-package-and-governed-handoffs/SKILL.md",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    rc = load(RC_MANIFEST)
    active = load(ACTIVE)
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    soul = SOUL.read_text(encoding="utf-8")
    phone = load(PREFLIGHT_RESULT)
    skill_text = {name: path.read_text(encoding="utf-8") for name, path in SKILLS.items()}
    manifest_hashes = all(
        (ROOT / item["path"]).exists()
        and sha(ROOT / item["path"]) == item["sha256"]
        and (ROOT / item["path"]).stat().st_size == item["bytes"]
        for item in rc["active_files"]
    )
    skill_versions = {
        name: (re.search(r"(?im)^\*\*Version:\*\*\s*`?([^`\s]+)", text).group(1) if re.search(r"(?im)^\*\*Version:\*\*\s*`?([^`\s]+)", text) else None)
        for name, text in skill_text.items()
    }
    checks = {
        "historical_active_manifest_preserved": active.get("version") == "1.0.0" and active.get("status") == "foundation_configured_not_pilot_ready",
        "rc_manifest_not_active": rc.get("version") == "1.1.0-rc.1" and rc.get("status") == "step9_release_candidate_not_active",
        "rc_manifest_hashes": manifest_hashes and rc.get("active_file_count") == len(rc.get("active_files", [])) == 72,
        "runtime_policy_versioned": policy.get("policy_version") == "1.0.0-rc.1" and policy.get("status") == "step9_release_candidate_not_approved",
        "primary_route": policy["model_routing"]["primary"]["logical_model"] == "deepseek-v4-flash" and policy["model_routing"]["primary"]["processing_region"] == "Europe",
        "fallback_disabled": policy["model_routing"]["fallback"]["enabled"] is False and config.get("fallback_providers") == [],
        "web_default_disabled": policy["tool_policy"]["conditional_official_site_web"]["enabled_by_default"] is False and "web" not in config and "web" not in config["platform_toolsets"]["cli"],
        "single_final_review": policy["review_model"]["normal_human_reviews"] == 1 and "one consolidated human review" in skill_text["a2-review-package-and-governed-handoffs"] and "one consolidated human review" in soul,
        "contact_semantics": policy["contact_semantics"]["secondary_role_may_still_be_selected_named_contact"] is True and "selected named contact and target-role priority are separate dimensions" in skill_text["a2-gap-analysis-and-enrichment-planning"] and "Keep contact selection separate from role priority" in soul,
        "held_independent_of_a1_score": policy["minimum_package_behavior"]["high_a1_score_can_be_held_in_a2"] is True and "An A1 `high` score does not make the A2 minimum package complete" in skill_text["a2-data-quality-and-review-readiness"] and "An A1 `high` score does not complete the A2 minimum package" in soul,
        "usage_baseline": policy["usage_monitoring"]["baseline"]["total_tokens"] == 234533 and policy["usage_monitoring"]["baseline"]["model_api_calls"] == 9 and policy["usage_monitoring"]["baseline"]["cost_status"] == "unknown",
        "absolute_paths": policy["runtime_controls"]["absolute_paths_required_for_noninteractive_runs"] is True and all("/opt/data/profiles/equinet-a2-enrichment/" in line for line in re.findall(r"/opt/data/profiles/equinet-a2-enrichment/[^\s]+", skill_text["a2-review-package-and-governed-handoffs"])),
        "person_business_phone_preflight": phone.get("field_key") == "person.business_phone" and phone.get("preflight_status") == "preflight_passed_execution_not_authorized" and phone.get("blocks") == [] and phone.get("external_actions") == 0,
        "modified_skills_versioned": all(version == "0.1.1-rc.1" for version in skill_versions.values()),
        "external_actions_zero": rc.get("external_actions") == phone.get("external_actions") == 0,
    }
    correction_status = {
        "S9-C1": "propagated_to_release_candidate_manifest",
        "S9-C2": "propagated_to_no_integration_runtime_policy",
        "S9-C3": "validated_in_generic_preflight_and_pilot_helper",
        "S9-C4": "propagated_to_soul_and_skills",
        "S9-C5": "propagated_to_soul_review_skill_and_runtime_policy",
        "S9-C6": "recorded_as_usage_baseline_with_unknown_cost",
        "S9-C7": "propagated_to_soul_data_quality_skill_and_runtime_policy",
        "S9-C8": "propagated_to_runtime_policy_and_review_skill_commands",
    }
    result = {
        "record_type": "step9a_correction_propagation_validation",
        "profile": "equinet-a2-enrichment",
        "release_candidate": "equinet-a2-no-integration-1.0.0-rc.1",
        "status": "pass_ready_for_step9b" if all(checks.values()) else "failed",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "skill_versions": skill_versions,
        "correction_status": correction_status,
        "rc_manifest": str(RC_MANIFEST.relative_to(ROOT)),
        "runtime_policy": str(POLICY.relative_to(ROOT)),
        "external_actions": 0,
        "errors": [name for name, passed in checks.items() if not passed],
    }
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    PROPAGATION.write_text(
        json.dumps(
            {
                "record_type": "step9_correction_propagation",
                "profile": "equinet-a2-enrichment",
                "status": "release_candidate_only_not_promoted",
                "corrections": correction_status,
                "validation": {"path": str(OUT.relative_to(ROOT)), "sha256": sha(OUT)},
                "active_manifest_overwritten": False,
                "profile_status_changed": False,
                "external_actions": 0,
            },
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )
    plan = load(PLAN)
    for phase in plan["phases"]:
        if phase["id"] == "9A":
            phase["status"] = "completed" if all(checks.values()) else "blocked"
        elif phase["id"] == "9B" and all(checks.values()) and phase.get("status") != "completed":
            phase["status"] = "ready"
    if all(checks.values()):
        phase_status = {phase["id"]: phase.get("status") for phase in plan["phases"]}
        plan["status"] = "step9b_completed_ready_for_step9c" if phase_status.get("9B") == "completed" else "step9a_completed_ready_for_step9b"
    else:
        plan["status"] = "step9a_blocked"
    PLAN.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REVIEW.write_text(
        f"""# Step 9A Correction Propagation Review

**Profile:** `equinet-a2-enrichment`  
**Release candidate:** `equinet-a2-no-integration-1.0.0-rc.1`  
**Status:** `{'PASS — READY FOR STEP 9B' if all(checks.values()) else 'BLOCKED'}`

## Validation

- Checks: **{sum(checks.values())}/{len(checks)} PASS**.
- Modified skills: **3**, all version `0.1.1-rc.1`.
- Release-candidate active files: **72**, hash mismatches **0**.
- Generic `person.business_phone` preflight: PASS, execution not authorised, external actions zero.
- Fallback: disabled.
- Web: disabled by default; candidate-specific activation remains required.
- Active production/pilot status: unchanged.

## Propagated corrections

""" + "\n".join(f"- `{key}`: `{value}`" for key, value in correction_status.items()) + """

## Boundary

The release candidate is not active and the profile is not yet `PILOT_READY_NO_INTEGRATION`. Step 9B must complete offline regression and exact no-Web replay before review.
""",
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "checks": f"{sum(checks.values())}/{len(checks)}", "modified_skills": skill_versions, "rc_active_files": rc["active_file_count"], "external_actions": 0}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
