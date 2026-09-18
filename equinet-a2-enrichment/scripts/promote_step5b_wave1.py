#!/usr/bin/env python3
"""Promote the approved Equinet A2 Wave 1 skill package."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "evaluations/step5b"
TECH = EVAL / "technical-validation.json"
BEHAVIOURAL = EVAL / "behavioural-validation.json"
REVIEW = EVAL / "A2-WAVE-1-REVIEW.md"
DRAFT_PACKAGE = EVAL / "wave1-draft-package-manifest.json"
ACCEPTANCE = EVAL / "acceptance-record.json"
PROMOTION = EVAL / "wave1-promotion-manifest.json"
RUNTIME_MANIFEST = ROOT / "foundations/contracts/skills/a2-wave1-runtime-manifest-0.1.0.json"
SOUL = ROOT / "SOUL.md"
ROADMAP = ROOT / "deliverables/A2-DELIVERY-STATUS-AND-ROADMAP.md"
ACTIVE = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"
APPROVED_AT = "2026-08-27T12:34:34Z"

SKILL_IDS = [
    "a2-handoff-intake-and-initialisation",
    "a2-entity-resolution-and-normalisation",
    "a2-duplicate-and-eligibility-review",
]
COMMANDS = [
    "scripts/a2_intake.py",
    "scripts/normalise_and_resolve_a2_entities.py",
    "scripts/evaluate_a2_duplicate_eligibility.py",
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"Expected text not found: {old}")
    return text.replace(old, new, 1)


def main() -> int:
    technical = load(TECH)
    behavioural = load(BEHAVIOURAL)
    if technical.get("pass") is not True or technical.get("deterministic_cases", {}).get("passed") != technical.get("deterministic_cases", {}).get("total"):
        raise RuntimeError("Wave 1 deterministic validation is not ready for promotion")
    if behavioural.get("overall_status") != "pass" or behavioural.get("passed") != behavioural.get("scenario_count"):
        raise RuntimeError("Wave 1 behavioural validation is not ready for promotion")

    snapshot = EVAL / "pre-promotion"
    for skill_id in SKILL_IDS:
        for rel in [f"skills/{skill_id}/SKILL.md", f"skills/{skill_id}/evals/evals.json"]:
            src = ROOT / rel
            dst = snapshot / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                shutil.copy2(src, dst)

    for skill_id in SKILL_IDS:
        path = ROOT / f"skills/{skill_id}/SKILL.md"
        text = path.read_text(encoding="utf-8")
        text = replace_once(text, "**Version:** `0.1.0-draft.1`", "**Version:** `0.1.0`")
        text = replace_once(text, "**Status:** `WAVE 1 DRAFT — NOT APPROVED`", "**Status:** `WAVE 1 APPROVED — LOCAL NO-INTEGRATION MODE`")
        path.write_text(text, encoding="utf-8")

    review = REVIEW.read_text(encoding="utf-8")
    review = replace_once(review, "**Status:** `READY FOR SÉVERINE REVIEW — NOT APPROVED`", f"**Status:** `APPROVED AND PROMOTED`  \n**Approved by:** Séverine, Unitalk Operations  \n**Approved at:** `{APPROVED_AT}`")
    REVIEW.write_text(review, encoding="utf-8")

    runtime = {
        "manifest_id": "equinet-a2-wave1-runtime",
        "version": "0.1.0",
        "status": "approved_local_no_integration",
        "approved_at": APPROVED_AT,
        "approved_by": {"name": "Séverine", "role": "Unitalk Operations"},
        "approved_decisions": [f"W1-{n}" for n in range(1, 11)],
        "skills": [
            {
                "skill_id": skill_id,
                "path": f"skills/{skill_id}/SKILL.md",
                "sha256": sha(ROOT / f"skills/{skill_id}/SKILL.md"),
                "evals_path": f"skills/{skill_id}/evals/evals.json",
                "evals_sha256": sha(ROOT / f"skills/{skill_id}/evals/evals.json"),
                "status": "approved_local_no_integration",
            }
            for skill_id in SKILL_IDS
        ],
        "commands": [
            {"path": rel, "sha256": sha(ROOT / rel), "status": "active_local_no_integration"}
            for rel in COMMANDS
        ],
        "validation": {
            "technical": {"path": str(TECH.relative_to(ROOT)), "sha256": sha(TECH), "deterministic_cases": "14/14 pass"},
            "behavioural": {"path": str(BEHAVIOURAL.relative_to(ROOT)), "sha256": sha(BEHAVIOURAL), "scenarios": "3/3 pass"},
        },
        "permissions": {
            "local_file_processing": True,
            "web_access": False,
            "apify": False,
            "twenty": False,
            "hubspot_read": False,
            "hubspot_write": False,
            "n8n": False,
            "outreach": False,
        },
        "next_gate": "Step 5C — Wave 2 Planning, Research and Verification",
    }
    RUNTIME_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_MANIFEST.write_text(json.dumps(runtime, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    soul = SOUL.read_text(encoding="utf-8")
    anchor = "- Operational Skill Architecture `0.1.0`, approved for Wave 1 build."
    if "Wave 1 Runtime Manifest `0.1.0`" not in soul:
        soul = replace_once(soul, anchor, anchor + "\n- Wave 1 Runtime Manifest `0.1.0`, approved for local no-integration use.")
    soul = replace_once(soul, "The next delivery gate is Step 5 — Operational Skills and Scripts. Until skills, runtime controls, synthetic end-to-end acceptance and a bounded pilot are completed, remain **FOUNDATION CONFIGURED — NOT PILOT-READY**.", "Wave 1 is approved for local no-integration use. The next delivery gate is Step 5C — Wave 2 Planning, Research and Verification. Until all skills, runtime controls, synthetic end-to-end acceptance and a bounded pilot are completed, remain **FOUNDATION CONFIGURED — NOT PILOT-READY**.")
    SOUL.write_text(soul, encoding="utf-8")

    roadmap = ROADMAP.read_text(encoding="utf-8")
    roadmap = replace_once(roadmap, "**Next delivery gate:** `Step 5B — Séverine review of Wave 1 Intake and Identity`", "**Next delivery gate:** `Step 5C — Wave 2 Planning, Research and Verification`")
    roadmap = replace_once(roadmap, "### Step 5B — Wave 1 Intake and Identity — READY FOR SÉVERINE REVIEW / NOT APPROVED", "### Step 5B — Wave 1 Intake and Identity — COMPLETED / APPROVED")
    roadmap = replace_once(roadmap, "- Approval of W1-1 through W1-10 is required before promotion and Wave 2 construction.", f"- Séverine approved W1-1 through W1-10 on `{APPROVED_AT}`; Wave 2 construction is authorised.")
    roadmap = replace_once(roadmap, "Review and approve, amend or reject decisions **W1-1 through W1-10** in the Step 5B Wave 1 review. Wave 2 construction has not started.", "Build and validate **Step 5C — Wave 2 Planning, Research and Verification**, then present the Wave 2 business review for approval.")
    ROADMAP.write_text(roadmap, encoding="utf-8")

    # The active manifest contains approved skills/scripts but not this acceptance, avoiding a hash cycle.
    subprocess.run([str(ROOT / ".venv/bin/python"), str(ROOT / "scripts/build_active_foundation_manifest.py")], check=True, cwd=ROOT)

    acceptance = {
        "record_type": "wave_skill_acceptance",
        "profile": "equinet-a2-enrichment",
        "step": "5B",
        "wave": 1,
        "decision": "approved_and_promoted",
        "approver": {"name": "Séverine", "role": "Unitalk Operations"},
        "approved_at": APPROVED_AT,
        "approved_decisions": [f"W1-{n}" for n in range(1, 11)],
        "runtime_manifest": str(RUNTIME_MANIFEST.relative_to(ROOT)),
        "runtime_manifest_sha256": sha(RUNTIME_MANIFEST),
        "technical_validation": str(TECH.relative_to(ROOT)),
        "technical_validation_sha256": sha(TECH),
        "behavioural_validation": str(BEHAVIOURAL.relative_to(ROOT)),
        "behavioural_validation_sha256": sha(BEHAVIOURAL),
        "active_foundation_manifest": str(ACTIVE.relative_to(ROOT)),
        "active_foundation_manifest_sha256": sha(ACTIVE),
        "skill_count": 3,
        "deterministic_cases": "14/14 pass",
        "behavioural_scenarios": "3/3 pass",
        "external_actions": 0,
        "profile_status": "FOUNDATION CONFIGURED — NOT PILOT-READY",
        "next_gate": "Step 5C — Wave 2 Planning, Research and Verification",
    }
    ACCEPTANCE.write_text(json.dumps(acceptance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    post = EVAL / "post-promotion"
    for src, rel in [(SOUL, "SOUL.md"), (ROADMAP, "A2-DELIVERY-STATUS-AND-ROADMAP.md")]:
        dst = post / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    immutable = [RUNTIME_MANIFEST, *[ROOT / f"skills/{sid}/SKILL.md" for sid in SKILL_IDS], *[ROOT / x for x in COMMANDS], TECH, BEHAVIOURAL, REVIEW, ACCEPTANCE, post / "SOUL.md", post / "A2-DELIVERY-STATUS-AND-ROADMAP.md"]
    promotion = {
        "manifest_id": "equinet-a2-wave1-promotion",
        "version": "0.1.0",
        "status": "approved_and_promoted",
        "files": [{"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha(path)} for path in immutable],
        "active_foundation_manifest": {"path": str(ACTIVE.relative_to(ROOT)), "sha256": sha(ACTIVE)},
        "external_actions": 0,
    }
    PROMOTION.write_text(json.dumps(promotion, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pass": True, "decision": "approved_and_promoted", "skills": 3, "next_gate": acceptance["next_gate"], "external_actions": 0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
