#!/usr/bin/env python3
"""Build the Step 9 release-candidate active foundation manifest without activating it."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"
STEP5 = ROOT / "foundations/contracts/skills/a2-step5-runtime-manifest-0.1.0.json"
RC_POLICY = ROOT / "evaluations/step9/release-candidate/a2-no-integration-runtime-policy-1.0.0-rc.1.yaml"
STEP8_RUNTIME = ROOT / "foundations/contracts/runtime/a2-step8-pilot-acceptance-manifest-0.1.0.json"
OUT = ROOT / "evaluations/step9/release-candidate/A2-ACTIVE-FOUNDATION-MANIFEST-1.1.0-rc.1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def skill_version(path: Path) -> str:
    match = re.search(r"(?im)^\*\*Version:\*\*\s*`?([^`\s]+)", path.read_text(encoding="utf-8"))
    if not match:
        raise RuntimeError(f"Missing skill version: {path}")
    return match.group(1)


def main() -> int:
    active = load(ACTIVE)
    step5 = load(STEP5)
    rows = []
    seen = set()
    for item in active["active_files"]:
        rel = item["path"]
        path = ROOT / rel
        if not path.exists():
            raise RuntimeError(f"Missing active file: {rel}")
        rows.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha(path)})
        seen.add(rel)
    additions = [
        str(RC_POLICY.relative_to(ROOT)),
        str(STEP8_RUNTIME.relative_to(ROOT)),
    ]
    for rel in additions:
        if rel in seen:
            continue
        path = ROOT / rel
        rows.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha(path)})
        seen.add(rel)
    skills = []
    for item in step5["skills"]:
        path = ROOT / item["path"]
        skills.append(
            {
                "skill_id": item["skill_id"],
                "version": skill_version(path),
                "status": "step9_release_candidate",
                "path": item["path"],
                "sha256": sha(path),
            }
        )
    manifest = {
        "manifest_id": "equinet-a2-active-foundation-release-candidate",
        "version": "1.1.0-rc.1",
        "status": "step9_release_candidate_not_active",
        "profile": "equinet-a2-enrichment",
        "release_candidate": "equinet-a2-no-integration-1.0.0-rc.1",
        "based_on": {
            "path": str(ACTIVE.relative_to(ROOT)),
            "version": active["version"],
            "sha256": sha(ACTIVE),
        },
        "canonical_schema_version": active["canonical_schema_version"],
        "business_configuration_version": active["active_business_configuration_version"],
        "runtime_policy": {
            "path": str(RC_POLICY.relative_to(ROOT)),
            "version": "1.0.0-rc.1",
            "status": "step9_release_candidate_not_approved",
            "sha256": sha(RC_POLICY),
        },
        "step8_acceptance": {
            "path": str(STEP8_RUNTIME.relative_to(ROOT)),
            "version": load(STEP8_RUNTIME)["version"],
            "sha256": sha(STEP8_RUNTIME),
        },
        "skills": skills,
        "active_files": rows,
        "active_file_count": len(rows),
        "corrections_propagated": [
            "S9-C1 current SOUL and config hashes",
            "S9-C2 consolidated no-integration runtime policy",
            "S9-C3 person.business_phone receipt allowlist consistency",
            "S9-C4 selected named contact versus target-role priority terminology",
            "S9-C5 single consolidated final review",
            "S9-C6 measured usage baseline and unknown-cost treatment",
            "S9-C7 A1 score versus A2 held-state separation",
            "S9-C8 absolute-path requirement for frozen runbook and replay controller",
        ],
        "permissions": {
            "local_file_processing": True,
            "manual_approved_handoff_processing": True,
            "web_enabled_by_default": False,
            "conditional_web_requires_candidate_specific_activation": True,
            "hubspot_read": False,
            "hubspot_write": False,
            "twenty": False,
            "n8n": False,
            "apify": False,
            "outreach": False,
            "durable_handoff_delivery": False,
        },
        "promotion_requires": [
            "offline regression pass",
            "exact no-Web accepted-record replay pass",
            "delivery-document validation",
            "safe archive validation",
            "explicit Séverine Step 9 approval",
        ],
        "external_actions": 0,
    }
    OUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    actual = load(OUT)
    mismatches = []
    for item in actual["active_files"]:
        path = ROOT / item["path"]
        if not path.exists() or sha(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
            mismatches.append(item["path"])
    print(json.dumps({"status": manifest["status"], "active_files": len(rows), "skills": len(skills), "hash_mismatches": mismatches, "external_actions": 0}, indent=2))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
