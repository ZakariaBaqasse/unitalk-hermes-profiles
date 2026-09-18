#!/usr/bin/env python3
"""Finalize the approved A2 FullEnrich no-integration foundation release."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STAMP = "2026-09-06T13:07:00Z"
SNAPSHOT = ROOT / "evaluations/fullenrich-source-amendment-20260906/pre-change"
ACTIVE = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def version_from_skill(path: Path) -> str | None:
    match = re.search(r"\*\*Version:\*\* `([^`]+)`", path.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def refresh_file_entry(path: Path) -> dict[str, Any]:
    return {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha(path)}


def main() -> int:
    # Updated operational architecture manifest, preserving the accepted 0.1.0 file.
    old_operational = ROOT / "foundations/contracts/skills/a2-operational-skill-manifest-0.1.0.json"
    operational = copy.deepcopy(load(old_operational))
    operational["version"] = "0.2.0"
    operational["status"] = "approved_local_no_integration_with_fullenrich_design"
    for wave in operational.get("waves", []):
        tools = wave.get("conditional_future_tools", [])
        if "approved Apify connector" in tools:
            tools[tools.index("approved Apify connector")] = "approved FullEnrich n8n connector"
            tools.append("separately approved Apify fallback connector")
    boundary = operational.setdefault("integration_boundary", {})
    boundary["step_10"] = "Connect FullEnrich through n8n first, then Twenty, HubSpot and any separately approved Apify fallback; replace preparation-only commands with guarded execution adapters."
    boundary["fullenrich_runtime_active"] = False
    boundary["n8n_runtime_active"] = False
    boundary["apify_runtime_active"] = False
    operational_path = ROOT / "foundations/contracts/skills/a2-operational-skill-manifest-0.2.0.json"
    dump(operational_path, operational)

    # Update the SOUL reference after the successor exists.
    soul_path = ROOT / "SOUL.md"
    soul = soul_path.read_text(encoding="utf-8")
    soul = soul.replace("Operational Skill Architecture `0.1.0`, approved for Wave 1 build.", "Operational Skill Architecture `0.2.0`, approved for local no-integration use with the FullEnrich integration design pending activation.")
    soul_path.write_text(soul, encoding="utf-8")

    # Append a current roadmap entry without rewriting prior accepted history.
    roadmap_path = ROOT / "deliverables/A2-DELIVERY-STATUS-AND-ROADMAP.md"
    roadmap = roadmap_path.read_text(encoding="utf-8")
    if "## 7. FullEnrich source-routing amendment" not in roadmap:
        roadmap += f"""\n## 7. FullEnrich source-routing amendment\n\n**Recorded:** `{STAMP}`  \n**Status:** `BUSINESS CONFIGURATION UPDATED — RUNTIME INTEGRATION PENDING`\n\n- Equinet confirmed that no separate first-party enrichment dataset is available.\n- New-source order is official website, FullEnrich, then separately gated Apify/HarvestAPI fallback.\n- FullEnrich People Search requires the exact organisation domain and approved target roles. Its default result limit is one. A later role-specific search is allowed only when no suitable person was returned.\n- No more than two unique people may be returned and retained per prospect. A second contact requires a large organisation or shared purchasing or operational responsibility.\n- People Lookup is used only for a known person whose identity, organisation or current role still needs verification.\n- Contact Enrichment runs only for selected contacts and requests work email plus mobile phone. Personal email is not requested.\n- Mobile is permitted and actively sought; its absence alone does not block review.\n- The n8n integration contract is prepared, but n8n, FullEnrich and Apify remain disconnected and unauthorised for live execution.\n- Next action: receive the FullEnrich API key, verify the account and Premium-plan rates, complete provider governance, deploy the n8n workflow and run bounded connector acceptance.\n"""
    roadmap_path.write_text(roadmap, encoding="utf-8")

    # Business-confirmation runtime manifest successor.
    old_runtime_manifest = ROOT / "foundations/contracts/skills/a2-business-confirmation-runtime-manifest-1.1.0.json"
    runtime_manifest = copy.deepcopy(load(old_runtime_manifest))
    runtime_manifest.update({
        "manifest_id": "equinet-a2-fullenrich-foundation-runtime",
        "version": "1.2.0",
        "status": "pilot_ready_no_integration_fullenrich_design",
        "created_at": STAMP,
        "business_configuration_version": "0.3.0",
        "decision_id": "A2-FULLENRICH-SOURCE-ROUTING-20260906",
    })
    runtime_paths = [item["path"] for item in runtime_manifest.get("files", [])]
    for extra in [
        "scripts/normalise_fullenrich_response.py",
        "foundations/contracts/integrations/a2-fullenrich-n8n-integration-0.1.0.json",
        "integrations/n8n/A2-FULLENRICH-N8N-WORKFLOW-SPEC.md",
    ]:
        if extra not in runtime_paths:
            runtime_paths.append(extra)
    rows = []
    for rel in runtime_paths:
        path = ROOT / rel
        if not path.is_file():
            raise FileNotFoundError(rel)
        row = refresh_file_entry(path)
        if rel.endswith("/SKILL.md"):
            row["version"] = version_from_skill(path)
        rows.append(row)
    runtime_manifest["files"] = rows
    runtime_manifest["runtime_limits"].update({"fullenrich_people_search_default_result_limit": 1, "fullenrich_max_unique_people_per_prospect": 2, "fullenrich_contact_enrichment_selected_contacts_only": True})
    runtime_manifest["integration_states"].update({"fullenrich": "business_approved_not_connected", "n8n": "design_approved_not_connected", "apify_harvestapi": "fallback_not_runtime_active"})
    runtime_manifest["external_actions"] = 0
    runtime_manifest_path = ROOT / "foundations/contracts/skills/a2-fullenrich-amendment-runtime-manifest-1.2.0.json"
    dump(runtime_manifest_path, runtime_manifest)

    # Build the new active manifest from the pre-change manifest.
    old_active = load(SNAPSHOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json")
    active = copy.deepcopy(old_active)
    active.update({
        "version": "1.3.0",
        "status": "pilot_ready_no_integration",
        "active_since": STAMP,
        "release_id": "equinet-a2-fullenrich-foundation-1.2.0",
        "active_business_configuration_version": "0.3.0",
        "current_clarification": "FullEnrich after official website, role-bounded search, selected-contact work-email/mobile enrichment, no personal email and separately gated Apify fallback",
    })
    active["runtime_policy"] = {"path": "foundations/contracts/runtime/a2-no-integration-runtime-policy-1.2.0.yaml", "version": "1.2.0", "sha256": sha(ROOT / "foundations/contracts/runtime/a2-no-integration-runtime-policy-1.2.0.yaml")}
    replacements = {
        "foundations/contracts/business/a2-business-field-catalogue-0.2.0.json": "foundations/contracts/business/a2-business-field-catalogue-0.3.0.json",
        "foundations/contracts/business/a2-business-field-catalogue-0.2.0.csv": "foundations/contracts/business/a2-business-field-catalogue-0.3.0.csv",
        "foundations/contracts/business/a2-minimum-data-packages-0.2.0.json": "foundations/contracts/business/a2-minimum-data-packages-0.3.0.json",
        "foundations/contracts/sources/a2-source-register-0.2.0.json": "foundations/contracts/sources/a2-source-register-0.3.0.json",
        "foundations/contracts/sources/a2-source-register-0.2.0.csv": "foundations/contracts/sources/a2-source-register-0.3.0.csv",
        "foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.2.0.json": "foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.3.0.json",
        "foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.2.0.json": "foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.3.0.json",
        "foundations/contracts/governance/a2-provider-and-cost-policy-0.2.0.json": "foundations/contracts/governance/a2-provider-and-cost-policy-0.3.0.json",
        "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.2.0.json": "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.3.0.json",
        "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.2.0.csv": "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.3.0.csv",
        "foundations/contracts/runtime/a2-no-integration-runtime-policy-1.1.0.yaml": "foundations/contracts/runtime/a2-no-integration-runtime-policy-1.2.0.yaml",
        "foundations/contracts/skills/a2-operational-skill-manifest-0.1.0.json": "foundations/contracts/skills/a2-operational-skill-manifest-0.2.0.json",
        "foundations/contracts/skills/a2-business-confirmation-runtime-manifest-1.1.0.json": "foundations/contracts/skills/a2-fullenrich-amendment-runtime-manifest-1.2.0.json",
    }
    paths = []
    for item in active["active_files"]:
        rel = replacements.get(item["path"], item["path"])
        if rel == "scripts/validate_official_site_social_profile_url_capture.py":
            continue
        if rel not in paths:
            paths.append(rel)
    for rel in [
        "foundations/decisions/A2-FULLENRICH-SOURCE-ROUTING-20260906.json",
        "foundations/decisions/A2-FULLENRICH-SOURCE-ROUTING-20260906.md",
        "foundations/contracts/integrations/a2-fullenrich-n8n-integration-0.1.0.json",
        "integrations/n8n/A2-FULLENRICH-N8N-WORKFLOW-SPEC.md",
        "scripts/normalise_fullenrich_response.py",
    ]:
        if rel not in paths:
            paths.append(rel)
    active["active_files"] = [refresh_file_entry(ROOT / rel) for rel in paths]
    active["active_file_count"] = len(active["active_files"])
    skill_index = {item["path"]: item for item in active["skills"]}
    for rel, item in skill_index.items():
        path = ROOT / rel
        item["version"] = version_from_skill(path)
        item["sha256"] = sha(path)
        item["status"] = "pilot_ready_no_integration"
    active["permissions"].update({"fullenrich": False, "n8n": False, "apify": False})
    active["external_actions"] = 0
    active["supersedes"] = {"manifest_version": old_active["version"], "snapshot_path": str((SNAPSHOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json").relative_to(ROOT)), "sha256": sha(SNAPSHOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json")}
    active["business_confirmation"] = {"decision_id": "A2-FULLENRICH-SOURCE-ROUTING-20260906", "decision_path": "foundations/decisions/A2-FULLENRICH-SOURCE-ROUTING-20260906.json", "equinet_confirmation": "confirmed_via_unitalk_operations", "unitalk_implementation_authorized": True}
    dump(ACTIVE, active)

    # Release manifest deliberately does not include itself.
    release = {
        "release_id": "equinet-a2-fullenrich-foundation-1.2.0",
        "version": "1.2.0",
        "status": "pilot_ready_no_integration_fullenrich_design",
        "created_at": STAMP,
        "profile": "equinet-a2-enrichment",
        "active_foundation": {"path": str(ACTIVE.relative_to(ROOT)), "sha256": sha(ACTIVE)},
        "runtime_policy": active["runtime_policy"],
        "decision": {"path": "foundations/decisions/A2-FULLENRICH-SOURCE-ROUTING-20260906.json", "sha256": sha(ROOT / "foundations/decisions/A2-FULLENRICH-SOURCE-ROUTING-20260906.json")},
        "technical_validation": {"path": "evaluations/fullenrich-source-amendment-20260906/technical-validation.json", "sha256": sha(ROOT / "evaluations/fullenrich-source-amendment-20260906/technical-validation.json")},
        "acceptance_record": {"path": "evaluations/fullenrich-source-amendment-20260906/acceptance-record.json", "sha256": sha(ROOT / "evaluations/fullenrich-source-amendment-20260906/acceptance-record.json")},
        "integration_state": {"fullenrich": "not_connected", "n8n": "not_connected", "apify": "fallback_not_connected"},
        "external_calls": 0,
        "external_actions": 0,
        "limitations": ["No FullEnrich API key is installed.", "No n8n workflow is deployed.", "No live provider call was executed.", "Premium-plan rates and credit caps remain to be verified.", "Provider DPA, data route and three-month retention remain to be approved."],
    }
    release_path = ROOT / "foundations/contracts/runtime/a2-fullenrich-foundation-release-manifest-1.2.0.json"
    dump(release_path, release)

    print(json.dumps({"status": "finalized", "active_manifest_version": active["version"], "active_file_count": active["active_file_count"], "runtime_manifest": str(runtime_manifest_path.relative_to(ROOT)), "release_manifest": str(release_path.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
