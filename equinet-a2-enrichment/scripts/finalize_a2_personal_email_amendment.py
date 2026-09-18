#!/usr/bin/env python3
"""Finalize the A2 incidental-personal-email correction release."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STAMP = "2026-09-06T13:38:10Z"
SNAPSHOT = ROOT / "evaluations/fullenrich-personal-email-amendment-20260906/pre-change"
ACTIVE = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"
EVAL = ROOT / "evaluations/fullenrich-personal-email-amendment-20260906"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_row(rel: str) -> dict[str, Any]:
    path = ROOT / rel
    return {"path": rel, "bytes": path.stat().st_size, "sha256": sha(path)}


def skill_version(path: Path) -> str | None:
    match = re.search(r"\*\*Version:\*\* `([^`]+)`", path.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def main() -> int:
    # Operational architecture successor.
    operational = copy.deepcopy(load(ROOT / "foundations/contracts/skills/a2-operational-skill-manifest-0.2.0.json"))
    operational["version"] = "0.2.1"
    operational["status"] = "approved_local_no_integration_with_incidental_personal_email_handling"
    operational["personal_email_policy"] = {"requested_by_default": False, "incidental_return_retained": True, "canonical_field": "person.personal_email_candidate", "human_review_required": True, "professional_contactability": False, "automatic_crm_write": False, "outreach_authority": False}
    operational_path = ROOT / "foundations/contracts/skills/a2-operational-skill-manifest-0.2.1.json"
    dump(operational_path, operational)

    # Runtime policy successor.
    old_runtime = ROOT / "foundations/contracts/runtime/a2-no-integration-runtime-policy-1.2.0.yaml"
    runtime = old_runtime.read_text(encoding="utf-8")
    runtime = runtime.replace("policy_version: 1.2.0", "policy_version: 1.2.1", 1)
    runtime = runtime.replace("release_candidate: equinet-a2-fullenrich-foundation-1.2.0", "release_candidate: equinet-a2-personal-email-correction-1.2.1", 1)
    runtime = runtime.replace("  fullenrich_n8n_contract: foundations/contracts/integrations/a2-fullenrich-n8n-integration-0.1.0.json", "  fullenrich_n8n_contract: foundations/contracts/integrations/a2-fullenrich-n8n-integration-0.1.1.json\n  incidental_personal_email_decision: foundations/decisions/A2-FULLENRICH-INCIDENTAL-PERSONAL-EMAIL-20260906.json")
    runtime = runtime.replace("- FE-4", "- FE-4\n- PE-1\n- PE-2\n- PE-3")
    runtime_path = ROOT / "foundations/contracts/runtime/a2-no-integration-runtime-policy-1.2.1.yaml"
    runtime_path.write_text(runtime, encoding="utf-8")

    # Update SOUL version references.
    soul_path = ROOT / "SOUL.md"; soul = soul_path.read_text(encoding="utf-8")
    soul = soul.replace("Operational Skill Architecture `0.2.0`", "Operational Skill Architecture `0.2.1`")
    soul_path.write_text(soul, encoding="utf-8")

    # Append roadmap correction.
    roadmap_path = ROOT / "deliverables/A2-DELIVERY-STATUS-AND-ROADMAP.md"; roadmap = roadmap_path.read_text(encoding="utf-8")
    if "## 8. Incidental FullEnrich personal-email correction" not in roadmap:
        roadmap += f"""\n## 8. Incidental FullEnrich personal-email correction\n\n**Recorded:** `{STAMP}`  \n**Status:** `BUSINESS CONFIGURATION UPDATED — RUNTIME INTEGRATION PENDING`\n\n- FullEnrich personal email remains excluded from the default request fields.\n- If FullEnrich returns a personal email incidentally, A2 retains it as `person.personal_email_candidate` with provider provenance and verification status.\n- The personal email remains separate from professional email, requires human review, does not satisfy professional contactability, and grants no consent, outreach or automatic CRM-write authority.\n- The n8n and FullEnrich runtime remains disconnected.\n"""
    roadmap_path.write_text(roadmap, encoding="utf-8")

    # Runtime manifest successor.
    runtime_manifest = copy.deepcopy(load(ROOT / "foundations/contracts/skills/a2-fullenrich-amendment-runtime-manifest-1.2.0.json"))
    runtime_manifest.update({"manifest_id": "equinet-a2-personal-email-correction-runtime", "version": "1.2.1", "status": "pilot_ready_no_integration_personal_email_correction", "created_at": STAMP, "business_configuration_version": "0.3.1", "decision_id": "A2-FULLENRICH-INCIDENTAL-PERSONAL-EMAIL-20260906"})
    runtime_paths = [x["path"] for x in runtime_manifest["files"]]
    runtime_paths = ["foundations/contracts/integrations/a2-fullenrich-n8n-integration-0.1.1.json" if x == "foundations/contracts/integrations/a2-fullenrich-n8n-integration-0.1.0.json" else x for x in runtime_paths]
    rows = []
    for rel in runtime_paths:
        path = ROOT / rel
        row = file_row(rel)
        if rel.endswith("/SKILL.md"): row["version"] = skill_version(path)
        rows.append(row)
    runtime_manifest["files"] = rows
    runtime_manifest["personal_email_policy"] = {"requested_by_default": False, "incidental_return_retained": True, "canonical_field": "person.personal_email_candidate", "human_review_required": True, "professional_contactability": False, "automatic_crm_write": False, "outreach_authority": False}
    runtime_manifest_path = ROOT / "foundations/contracts/skills/a2-personal-email-correction-runtime-manifest-1.2.1.json"
    dump(runtime_manifest_path, runtime_manifest)

    # Active foundation successor from the frozen 1.3.0 baseline.
    active = copy.deepcopy(load(SNAPSHOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"))
    active.update({"version": "1.3.1", "status": "pilot_ready_no_integration", "active_since": STAMP, "release_id": "equinet-a2-personal-email-correction-1.2.1", "active_business_configuration_version": "0.3.1", "current_clarification": "FullEnrich personal email is not requested by default but is retained separately with provenance and human review if returned incidentally"})
    active["runtime_policy"] = {"path": str(runtime_path.relative_to(ROOT)), "version": "1.2.1", "sha256": sha(runtime_path)}
    replacements = {
        "foundations/contracts/business/a2-business-field-catalogue-0.3.0.json": "foundations/contracts/business/a2-business-field-catalogue-0.3.1.json",
        "foundations/contracts/business/a2-business-field-catalogue-0.3.0.csv": "foundations/contracts/business/a2-business-field-catalogue-0.3.1.csv",
        "foundations/contracts/business/a2-minimum-data-packages-0.3.0.json": "foundations/contracts/business/a2-minimum-data-packages-0.3.1.json",
        "foundations/contracts/sources/a2-source-register-0.3.0.json": "foundations/contracts/sources/a2-source-register-0.3.1.json",
        "foundations/contracts/sources/a2-source-register-0.3.0.csv": "foundations/contracts/sources/a2-source-register-0.3.1.csv",
        "foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.3.0.json": "foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.3.1.json",
        "foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.3.0.json": "foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.3.1.json",
        "foundations/contracts/governance/a2-provider-and-cost-policy-0.3.0.json": "foundations/contracts/governance/a2-provider-and-cost-policy-0.3.1.json",
        "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.3.0.json": "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.3.1.json",
        "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.3.0.csv": "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.3.1.csv",
        "foundations/contracts/integrations/a2-fullenrich-n8n-integration-0.1.0.json": "foundations/contracts/integrations/a2-fullenrich-n8n-integration-0.1.1.json",
        "foundations/contracts/runtime/a2-no-integration-runtime-policy-1.2.0.yaml": "foundations/contracts/runtime/a2-no-integration-runtime-policy-1.2.1.yaml",
        "foundations/contracts/skills/a2-operational-skill-manifest-0.2.0.json": "foundations/contracts/skills/a2-operational-skill-manifest-0.2.1.json",
        "foundations/contracts/skills/a2-fullenrich-amendment-runtime-manifest-1.2.0.json": "foundations/contracts/skills/a2-personal-email-correction-runtime-manifest-1.2.1.json",
    }
    paths = []
    for item in active["active_files"]:
        rel = replacements.get(item["path"], item["path"])
        if rel not in paths: paths.append(rel)
    for rel in ["foundations/decisions/A2-FULLENRICH-INCIDENTAL-PERSONAL-EMAIL-20260906.json", "foundations/decisions/A2-FULLENRICH-INCIDENTAL-PERSONAL-EMAIL-20260906.md"]:
        if rel not in paths: paths.append(rel)
    active["active_files"] = [file_row(rel) for rel in paths]
    active["active_file_count"] = len(active["active_files"])
    for item in active["skills"]:
        path = ROOT / item["path"]
        item["version"] = skill_version(path); item["sha256"] = sha(path); item["status"] = "pilot_ready_no_integration"
    active["permissions"].update({"fullenrich": False, "n8n": False, "apify": False})
    active["external_actions"] = 0
    active["supersedes"] = {"manifest_version": "1.3.0", "snapshot_path": str((SNAPSHOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json").relative_to(ROOT)), "sha256": sha(SNAPSHOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json")}
    active["business_confirmation"] = {"decision_id": "A2-FULLENRICH-INCIDENTAL-PERSONAL-EMAIL-20260906", "decision_path": "foundations/decisions/A2-FULLENRICH-INCIDENTAL-PERSONAL-EMAIL-20260906.json", "equinet_confirmation": "confirmed_via_unitalk_operations", "unitalk_implementation_authorized": True}
    dump(ACTIVE, active)

    release = {
        "release_id": "equinet-a2-personal-email-correction-1.2.1", "version": "1.2.1", "status": "pilot_ready_no_integration_personal_email_correction", "created_at": STAMP, "profile": "equinet-a2-enrichment",
        "active_foundation": {"path": str(ACTIVE.relative_to(ROOT)), "sha256": sha(ACTIVE)},
        "runtime_policy": active["runtime_policy"],
        "decision": {"path": "foundations/decisions/A2-FULLENRICH-INCIDENTAL-PERSONAL-EMAIL-20260906.json", "sha256": sha(ROOT / "foundations/decisions/A2-FULLENRICH-INCIDENTAL-PERSONAL-EMAIL-20260906.json")},
        "integration_state": {"fullenrich": "not_connected", "n8n": "not_connected", "apify": "fallback_not_connected"},
        "external_calls": 0, "external_actions": 0,
        "limitations": ["No FullEnrich API key is installed.", "No n8n workflow is deployed.", "No live provider call was executed.", "Premium-plan rates and credit caps remain to be verified.", "Provider DPA, data route and retention remain to be approved."]
    }
    validation = EVAL / "technical-validation.json"; acceptance = EVAL / "acceptance-record.json"
    if validation.is_file(): release["technical_validation"] = {"path": str(validation.relative_to(ROOT)), "sha256": sha(validation)}
    if acceptance.is_file(): release["acceptance_record"] = {"path": str(acceptance.relative_to(ROOT)), "sha256": sha(acceptance)}
    release_path = ROOT / "foundations/contracts/runtime/a2-personal-email-correction-release-manifest-1.2.1.json"; dump(release_path, release)
    print(json.dumps({"status": "finalized", "active_manifest_version": active["version"], "active_file_count": active["active_file_count"], "runtime_policy": str(runtime_path.relative_to(ROOT)), "release_manifest": str(release_path.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
