#!/usr/bin/env python3
"""Promote the approved Step 9 release candidate atomically after protected SOUL approval."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
STEP9 = ROOT / "evaluations/step9"
RC_FOUNDATION = STEP9 / "release-candidate/A2-ACTIVE-FOUNDATION-MANIFEST-1.1.0-rc.1.json"
RC_POLICY = STEP9 / "release-candidate/a2-no-integration-runtime-policy-1.0.0-rc.1.yaml"
RC_ARCHIVE_VALIDATION = STEP9 / "safe-archive-validation.json"
ACTIVE = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"
FINAL_POLICY = ROOT / "foundations/contracts/runtime/a2-no-integration-runtime-policy-1.0.0.yaml"
ACCEPTANCE = STEP9 / "acceptance-record.json"
RELEASE_MANIFEST = ROOT / "foundations/contracts/runtime/a2-no-integration-release-manifest-1.0.0.json"
PLAN = STEP9 / "step9-plan.json"
SOUL = ROOT / "SOUL.md"
CONFIG = ROOT / "config.yaml"
APPROVED_AT = "2026-08-30T14:56:57Z"
SKILL_IDS = [
    "a2-handoff-intake-and-initialisation",
    "a2-entity-resolution-and-normalisation",
    "a2-duplicate-and-eligibility-review",
    "a2-gap-analysis-and-enrichment-planning",
    "a2-permitted-enrichment-research",
    "a2-field-verification",
    "a2-evidence-confidence-and-freshness",
    "a2-protected-field-conflict-resolution",
    "a2-data-quality-and-review-readiness",
    "a2-review-package-and-governed-handoffs",
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def version(path: Path) -> str:
    match = re.search(r"(?im)^\*\*Version:\*\*\s*`?([^`\s]+)", path.read_text(encoding="utf-8"))
    if not match:
        raise RuntimeError(f"Missing skill version: {path}")
    return match.group(1)


def main() -> int:
    rc = load(RC_FOUNDATION)
    archive = load(RC_ARCHIVE_VALIDATION)
    soul_text = SOUL.read_text(encoding="utf-8")
    if "**PILOT_READY_NO_INTEGRATION**" not in soul_text or "Proceed to **Step 10 — Integrations**" not in soul_text:
        raise RuntimeError("Protected SOUL promotion is not applied")
    if archive.get("status") != "pass_ready_for_step9e_review" or archive.get("checks_passed") != archive.get("checks_total"):
        raise RuntimeError("Step 9D archive is not approved for Step 9E review")
    for skill_id in SKILL_IDS:
        skill_path = ROOT / "skills" / skill_id / "SKILL.md"
        skill_version = version(skill_path)
        expected = "0.1.1" if skill_id in {"a2-gap-analysis-and-enrichment-planning", "a2-data-quality-and-review-readiness", "a2-review-package-and-governed-handoffs"} else "0.1.0"
        if skill_version != expected:
            raise RuntimeError(f"Skill {skill_id} has version {skill_version}, expected {expected}")

    policy = yaml.safe_load(RC_POLICY.read_text(encoding="utf-8"))
    policy["policy_version"] = "1.0.0"
    policy["status"] = "approved_pilot_ready_no_integration"
    policy["release_candidate"] = "equinet-a2-no-integration-1.0.0"
    policy["approved_at"] = APPROVED_AT
    policy["approved_by"] = {"name": "Séverine", "role": "Unitalk Operations"}
    policy["approved_decisions"] = [f"S9-{index}" for index in range(1, 11)]
    policy["next_gate"] = "Step 10 — Integrations"
    FINAL_POLICY.write_text(yaml.safe_dump(policy, sort_keys=False, allow_unicode=True), encoding="utf-8")

    excluded_runtime = {
        "foundations/contracts/runtime/a2-runtime-policy-0.1.0.yaml",
        "foundations/contracts/runtime/a2-step8-pilot-runtime-policy-0.1.0.yaml",
        str(RC_POLICY.relative_to(ROOT)),
    }
    paths = [item["path"] for item in rc["active_files"] if item["path"] not in excluded_runtime]
    paths.append(str(FINAL_POLICY.relative_to(ROOT)))
    paths = list(dict.fromkeys(paths))
    active_files = []
    for rel in paths:
        path = ROOT / rel
        if not path.exists():
            raise RuntimeError(f"Missing final active file: {rel}")
        active_files.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha(path)})
    skills = []
    for skill_id in SKILL_IDS:
        path = ROOT / "skills" / skill_id / "SKILL.md"
        skills.append({"skill_id": skill_id, "version": version(path), "status": "pilot_ready_no_integration", "path": str(path.relative_to(ROOT)), "sha256": sha(path)})
    active_manifest = {
        "manifest_id": "equinet-a2-active-foundation",
        "version": "1.1.0",
        "status": "pilot_ready_no_integration",
        "active_since": APPROVED_AT,
        "release_id": "equinet-a2-no-integration-1.0.0",
        "canonical_schema_version": rc["canonical_schema_version"],
        "active_business_configuration_version": rc["business_configuration_version"],
        "current_clarification": "Step 9 no-integration release: single final review, contact-role separation and held-state independence",
        "runtime_policy": {"path": str(FINAL_POLICY.relative_to(ROOT)), "version": "1.0.0", "sha256": sha(FINAL_POLICY)},
        "skills": skills,
        "active_files": active_files,
        "active_file_count": len(active_files),
        "historical_runtime_policies": sorted(excluded_runtime),
        "permissions": rc["permissions"],
        "external_actions": 0,
    }
    ACTIVE.write_text(json.dumps(active_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    acceptance = {
        "record_type": "step9_no_integration_release_acceptance",
        "profile": "equinet-a2-enrichment",
        "release_id": "equinet-a2-no-integration-1.0.0",
        "decision": "approved_pilot_ready_no_integration",
        "approved_decisions": [f"S9-{index}" for index in range(1, 11)],
        "approver": {"name": "Séverine", "role": "Unitalk Operations"},
        "approved_at": APPROVED_AT,
        "scope": "Controlled human-reviewed no-integration pilot operation with candidate-specific external-source activation only.",
        "validation_basis": {
            "step9a": "15/15 pass",
            "step9b": "10/10 pass; 11/11 suites; 14/14 operators; 2/2 exact replays",
            "step9c": "10/10 pass",
            "step9d": "11/11 pass",
        },
        "limitations": [
            "Not production acceptance or contractual delivery acceptance.",
            "HubSpot, Twenty, n8n, Apify, outreach and durable downstream delivery remain disabled.",
            "Web is disabled by default and requires candidate-specific approval and runtime activation.",
            "Rood & Riddle remains held pending approved evidence or an Equinet-approved exception.",
            "Detailed retention, administrator visibility, named Equinet reviewers and global cost telemetry remain open.",
        ],
        "profile_status": "PILOT_READY_NO_INTEGRATION",
        "production_acceptance": False,
        "contractual_acceptance": False,
        "authorised_external_actions": [],
        "next_gate": "Step 10 — Integrations",
    }
    ACCEPTANCE.write_text(json.dumps(acceptance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    release_manifest = {
        "manifest_id": "equinet-a2-no-integration-release",
        "release_id": "equinet-a2-no-integration-1.0.0",
        "version": "1.0.0",
        "status": "pilot_ready_no_integration",
        "profile": "equinet-a2-enrichment",
        "approved_at": APPROVED_AT,
        "approved_by": acceptance["approver"],
        "active_foundation": {"path": str(ACTIVE.relative_to(ROOT)), "sha256": sha(ACTIVE)},
        "runtime_policy": {"path": str(FINAL_POLICY.relative_to(ROOT)), "sha256": sha(FINAL_POLICY)},
        "acceptance_record": {"path": str(ACCEPTANCE.relative_to(ROOT)), "sha256": sha(ACCEPTANCE)},
        "skills": skills,
        "step8_acceptance": "approved",
        "step9_validation": {"step9a": "15/15", "step9b": "10/10", "step9c": "10/10", "step9d": "11/11"},
        "production_acceptance": False,
        "contractual_acceptance": False,
        "external_actions": 0,
        "next_gate": "Step 10 — Integrations",
    }
    RELEASE_MANIFEST.write_text(json.dumps(release_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    plan = load(PLAN)
    for phase in plan["phases"]:
        if phase["id"] == "9E":
            phase["status"] = "completed"
    plan["status"] = "completed_pilot_ready_no_integration"
    plan["final_release_id"] = "equinet-a2-no-integration-1.0.0"
    plan["approved_at"] = APPROVED_AT
    PLAN.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"status": "pilot_ready_no_integration", "active_files": len(active_files), "skills": len(skills), "active_manifest": str(ACTIVE.relative_to(ROOT)), "active_manifest_sha256": sha(ACTIVE), "runtime_policy": str(FINAL_POLICY.relative_to(ROOT)), "acceptance_record": str(ACCEPTANCE.relative_to(ROOT)), "release_manifest": str(RELEASE_MANIFEST.relative_to(ROOT)), "external_actions": 0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
