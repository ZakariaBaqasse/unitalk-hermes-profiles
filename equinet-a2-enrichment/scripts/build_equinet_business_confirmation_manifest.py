#!/usr/bin/env python3
"""Build A2 active-foundation manifest 1.2.0 for Equinet confirmation release."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"
PREVIOUS = ROOT / "evaluations/equinet-business-confirmation-20260830/pre-change/A2-ACTIVE-FOUNDATION-MANIFEST.json"
OUT = CURRENT
STAMP = "2026-08-30T17:05:11Z"
REPLACEMENTS = {
    "foundations/contracts/business/a2-business-field-catalogue-0.1.1-draft.1.json": "foundations/contracts/business/a2-business-field-catalogue-0.2.0.json",
    "foundations/contracts/business/a2-business-field-catalogue-0.1.1-draft.1.csv": "foundations/contracts/business/a2-business-field-catalogue-0.2.0.csv",
    "foundations/contracts/business/a2-minimum-data-packages-0.1.1-draft.1.json": "foundations/contracts/business/a2-minimum-data-packages-0.2.0.json",
    "foundations/contracts/sources/a2-source-register-0.1.1-draft.1.json": "foundations/contracts/sources/a2-source-register-0.2.0.json",
    "foundations/contracts/sources/a2-source-register-0.1.1-draft.1.csv": "foundations/contracts/sources/a2-source-register-0.2.0.csv",
    "foundations/contracts/governance/a2-provider-and-cost-policy-0.1.1-draft.1.json": "foundations/contracts/governance/a2-provider-and-cost-policy-0.2.0.json",
    "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.1.1-draft.1.json": "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.2.0.json",
    "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.1.1-draft.1.csv": "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.2.0.csv",
    "foundations/contracts/runtime/a2-no-integration-runtime-policy-1.0.0.yaml": "foundations/contracts/runtime/a2-no-integration-runtime-policy-1.1.0.yaml",
    "foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.1.1-draft.1.json": "foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.2.0.json",
    "foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.1.1-draft.1.json": "foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.2.0.json",
}
ADDITIONS = [
    "foundations/decisions/A2-EQUINET-BUSINESS-CONFIRMATION-20260830.json",
    "foundations/decisions/A2-EQUINET-BUSINESS-CONFIRMATION-20260830.md",
    "foundations/A2-BUSINESS-FIELD-CATALOGUE.md",
    "foundations/A2-MINIMUM-DATA-PACKAGES.md",
    "foundations/A2-PRELIMINARY-HUBSPOT-MAPPING.md",
    "deliverables/A2-DELIVERY-STATUS-AND-ROADMAP.md",
    "scripts/classify_a2_target_role.py",
    "scripts/validate_a2_contact_selection.py",
    "foundations/contracts/skills/a2-business-confirmation-runtime-manifest-1.1.0.json",
]
HISTORICAL_RUNTIME_MANIFESTS = {
    "foundations/contracts/skills/a2-operational-skill-manifest-0.1.0.json",
    "foundations/contracts/skills/a2-wave1-runtime-manifest-0.1.0.json",
    "foundations/contracts/skills/a2-wave2-runtime-manifest-0.1.0.json",
    "foundations/contracts/skills/a2-wave3-runtime-manifest-0.1.0.json",
    "foundations/contracts/skills/a2-step5-runtime-manifest-0.1.0.json",
}
SKILL_VERSIONS = {
    "a2-entity-resolution-and-normalisation": "0.2.0",
    "a2-gap-analysis-and-enrichment-planning": "0.2.0",
    "a2-permitted-enrichment-research": "0.2.0",
    "a2-field-verification": "0.2.0",
    "a2-evidence-confidence-and-freshness": "0.2.0",
    "a2-protected-field-conflict-resolution": "0.2.0",
    "a2-data-quality-and-review-readiness": "0.2.0",
    "a2-review-package-and-governed-handoffs": "0.2.0",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    old = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    paths = [
        REPLACEMENTS.get(item["path"], item["path"])
        for item in old["active_files"]
        if item["path"] not in HISTORICAL_RUNTIME_MANIFESTS
    ]
    for rel in ADDITIONS:
        if rel not in paths:
            paths.append(rel)
    missing = [rel for rel in paths if not (ROOT / rel).is_file()]
    if missing:
        print(json.dumps({"status": "fail", "missing": missing}, indent=2))
        return 1
    skills = []
    for item in old.get("skills", []):
        updated = dict(item)
        skill_id = updated.get("skill_id")
        if skill_id in SKILL_VERSIONS:
            updated["version"] = SKILL_VERSIONS[skill_id]
            updated["status"] = "pilot_ready_no_integration"
            updated["sha256"] = sha(ROOT / updated["path"])
        skills.append(updated)
    runtime_path = "foundations/contracts/runtime/a2-no-integration-runtime-policy-1.1.0.yaml"
    manifest = dict(old)
    manifest.update({
        "version": "1.2.0",
        "status": "pilot_ready_no_integration",
        "active_since": STAMP,
        "release_id": "equinet-a2-business-confirmation-1.1.0",
        "active_business_configuration_version": "0.2.0",
        "current_clarification": "Equinet-confirmed target roles, two-contact limit, Horse Owner completeness, evidence-based horse count and open-gap final review",
        "runtime_policy": {"path": runtime_path, "version": "1.1.0", "sha256": sha(ROOT / runtime_path)},
        "skills": skills,
        "active_files": [{"path": rel, "bytes": (ROOT / rel).stat().st_size, "sha256": sha(ROOT / rel)} for rel in paths],
        "supersedes": {"manifest_version": old.get("version"), "snapshot_path": str(PREVIOUS.relative_to(ROOT)), "sha256": sha(PREVIOUS)},
        "business_confirmation": {
            "decision_id": "A2-EQUINET-ROLES-CONTACTS-HORSEOWNER-20260830",
            "decision_path": "foundations/decisions/A2-EQUINET-BUSINESS-CONFIRMATION-20260830.json",
            "equinet_confirmation": "confirmed_via_unitalk_operations",
            "unitalk_implementation_authorized": True,
        },
    })
    OUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass", "version": manifest["version"], "active_files": len(paths), "skills": len(skills), "output": str(OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
