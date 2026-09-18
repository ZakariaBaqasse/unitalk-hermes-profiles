#!/usr/bin/env python3
"""Promote the approved Step 5A operational skill architecture."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "foundations/contracts/skills/a2-operational-skill-manifest-0.1.0-draft.1.json"
APPROVED = ROOT / "foundations/contracts/skills/a2-operational-skill-manifest-0.1.0.json"
DOC = ROOT / "foundations/A2-OPERATIONAL-SKILL-ARCHITECTURE.md"
REVIEW = ROOT / "evaluations/step5a/A2-OPERATIONAL-SKILL-ARCHITECTURE-REVIEW.md"
TECH = ROOT / "evaluations/step5a/technical-validation.json"
ACCEPTANCE = ROOT / "evaluations/step5a/acceptance-record.json"
PROMOTION = ROOT / "evaluations/step5a/promotion-manifest.json"
SOUL = ROOT / "SOUL.md"
ROADMAP = ROOT / "deliverables/A2-DELIVERY-STATUS-AND-ROADMAP.md"
ACTIVE = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"
APPROVED_AT = "2026-08-27T12:10:52Z"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"Expected text not found: {old}")
    return text.replace(old, new, 1)


def main() -> int:
    technical = load(TECH)
    if technical.get("pass") is not True or technical.get("status") != "ready_for_severine_review_not_approved":
        raise RuntimeError("Step 5A draft validation is not ready for promotion")
    draft = load(DRAFT)
    if draft.get("status") != "ready_for_severine_review_not_approved":
        raise RuntimeError("Step 5A draft status mismatch")

    approved = json.loads(json.dumps(draft))
    approved["version"] = "0.1.0"
    approved["status"] = "approved_for_wave_1_build"
    approved["approved_at"] = APPROVED_AT
    approved["approved_by"] = {"name": "Séverine", "role": "Unitalk Operations"}
    approved["decision_checkpoint"]["approval_required_before_wave_1_build"] = False
    approved["decision_checkpoint"]["decision"] = "approved"
    APPROVED.write_text(json.dumps(approved, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    doc = DOC.read_text(encoding="utf-8")
    doc = replace_once(doc, "**Version:** `0.1.0-draft.1`", "**Version:** `0.1.0`")
    doc = replace_once(doc, "**Status:** `READY FOR SÉVERINE REVIEW — NOT APPROVED`", "**Status:** `APPROVED FOR WAVE 1 BUILD`")
    doc = replace_once(doc, "After approval of decisions `5A-1` through `5A-10`, proceed to `Step 5B — Wave 1 Intake and Identity`.", "Decisions `5A-1` through `5A-10` were approved by Séverine. Proceed to `Step 5B — Wave 1 Intake and Identity`.")
    DOC.write_text(doc, encoding="utf-8")

    review = REVIEW.read_text(encoding="utf-8")
    review = replace_once(review, "**Status:** `READY FOR SÉVERINE REVIEW — NOT APPROVED`", "**Status:** `APPROVED`")
    review = replace_once(review, "**Proposed manifest:** `0.1.0-draft.1`", f"**Approved manifest:** `0.1.0`  \n**Approved by:** Séverine, Unitalk Operations  \n**Approved at:** `{APPROVED_AT}`")
    REVIEW.write_text(review, encoding="utf-8")

    soul = SOUL.read_text(encoding="utf-8")
    anchor = "- Twenty Review Layer Contract `0.1.0-draft.1`, approved as a Unitalk working baseline; workspace integration pending."
    if "Operational Skill Architecture `0.1.0`" not in soul:
        soul = replace_once(soul, anchor, anchor + "\n- Operational Skill Architecture `0.1.0`, approved for Wave 1 build.")
    SOUL.write_text(soul, encoding="utf-8")

    roadmap = ROADMAP.read_text(encoding="utf-8")
    roadmap = replace_once(roadmap, "**Next delivery gate:** `Step 5A — Séverine review of Operational Skill Architecture`", "**Next delivery gate:** `Step 5B — Wave 1 Intake and Identity`")
    roadmap = replace_once(roadmap, "### Step 5A — Operational Skill Architecture and Runtime Manifest — READY FOR SÉVERINE REVIEW / NOT APPROVED", "### Step 5A — Operational Skill Architecture and Runtime Manifest — COMPLETED / APPROVED")
    roadmap = replace_once(roadmap, "- Explicit approval of decisions 5A-1 through 5A-10 is required before Wave 1 construction.", f"- Séverine approved decisions 5A-1 through 5A-10 on `{APPROVED_AT}`; Wave 1 construction is authorised.")
    roadmap = replace_once(roadmap, "Review and approve, amend or reject decisions **5A-1 through 5A-10** in the Step 5A Operational Skill Architecture review. Wave 1 construction has not started.", "Build and validate **Step 5B — Wave 1 Intake and Identity**, then present the Wave 1 business review for approval.")
    ROADMAP.write_text(roadmap, encoding="utf-8")

    # Refresh the active foundation manifest after the authorised SOUL update.
    subprocess.run([str(ROOT / ".venv/bin/python"), str(ROOT / "scripts/build_active_foundation_manifest.py")], check=True, cwd=ROOT)
    approved = load(APPROVED)
    approved["active_foundation"] = {"path": str(ACTIVE.relative_to(ROOT)), "sha256": sha(ACTIVE)}
    APPROVED.write_text(json.dumps(approved, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    acceptance = {
        "record_type": "step5a_operational_skill_architecture_acceptance",
        "profile": "equinet-a2-enrichment",
        "step": "5A",
        "decision": "approved_and_promoted",
        "approver": {"name": "Séverine", "role": "Unitalk Operations"},
        "approved_at": APPROVED_AT,
        "approved_decisions": [f"5A-{n}" for n in range(1, 11)],
        "approved_manifest": str(APPROVED.relative_to(ROOT)),
        "approved_manifest_sha256": sha(APPROVED),
        "architecture_document": str(DOC.relative_to(ROOT)),
        "architecture_document_sha256": sha(DOC),
        "review": str(REVIEW.relative_to(ROOT)),
        "review_sha256": sha(REVIEW),
        "draft_validation": str(TECH.relative_to(ROOT)),
        "draft_validation_sha256": sha(TECH),
        "authorizes": ["create and test Wave 1 skill packages", "create local deterministic Wave 1 scripts"],
        "does_not_authorize": ["live Web access", "Apify execution", "provider spend", "Twenty action", "HubSpot access or write", "n8n action", "outreach", "pilot readiness", "production readiness"],
        "next_gate": "Step 5B — Wave 1 Intake and Identity",
    }
    ACCEPTANCE.write_text(json.dumps(acceptance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths = [APPROVED, DOC, REVIEW, TECH, ACCEPTANCE, SOUL, ROADMAP, ACTIVE]
    promotion = {
        "manifest_id": "equinet-a2-step5a-promotion",
        "version": "0.1.0",
        "status": "approved_and_promoted",
        "files": [{"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha(path)} for path in paths],
        "external_actions": 0,
    }
    PROMOTION.write_text(json.dumps(promotion, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pass": True, "decision": acceptance["decision"], "skills_authorised": 10, "next_gate": acceptance["next_gate"], "external_actions": 0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
