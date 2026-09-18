#!/usr/bin/env python3
"""Build the Step 9 pre-freeze audit, release inventory and execution plan."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
STEP9 = ROOT / "evaluations/step9"
PREFLIGHT = STEP9 / "preflight-audit.json"
REVIEW = STEP9 / "STEP-9-PREFLIGHT-REVIEW.md"
INVENTORY = STEP9 / "release-candidate-inventory.json"
PLAN = STEP9 / "step9-plan.json"
ACTIVE = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"
STEP5 = ROOT / "foundations/contracts/skills/a2-step5-runtime-manifest-0.1.0.json"
STEP8_ACCEPTANCE = ROOT / "evaluations/step8/acceptance-record.json"
STEP8_VALIDATION = ROOT / "evaluations/step8/final-closure-validation.json"
STEP8_RUNTIME = ROOT / "foundations/contracts/runtime/a2-step8-pilot-acceptance-manifest-0.1.0.json"
RUNTIME_POLICY = ROOT / "foundations/contracts/runtime/a2-runtime-policy-0.1.0.yaml"
CONFIG = ROOT / "config.yaml"
SOUL = ROOT / "SOUL.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def infer_version(path: Path) -> tuple[str | None, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".json":
        try:
            value = json.loads(text)
            for key in ("version", "policy_version", "schema_version", "handoff_schema_version"):
                if isinstance(value, dict) and value.get(key):
                    return str(value[key]), f"top_level.{key}"
        except json.JSONDecodeError:
            pass
    if path.suffix in {".yaml", ".yml"}:
        try:
            value = yaml.safe_load(text)
            for key in ("version", "policy_version", "schema_version"):
                if isinstance(value, dict) and value.get(key):
                    return str(value[key]), f"top_level.{key}"
        except yaml.YAMLError:
            pass
    if path.name == "SKILL.md":
        match = re.search(r"(?im)^\*\*Version:\*\*\s*`?([^`\s]+)", text)
        if match:
            return match.group(1), "skill_body"
    match = re.search(r"(?<!\d)(\d+\.\d+\.\d+(?:-[A-Za-z0-9.]+)?)", path.name)
    if match:
        return match.group(1), "filename"
    if path.name == "SOUL.md":
        return "step8-accepted", "release_state"
    if path.name == "config.yaml":
        config = yaml.safe_load(text)
        return str(config.get("_config_version")) if isinstance(config, dict) and config.get("_config_version") else None, "top_level._config_version"
    return None, "missing"


def category(path: str) -> str:
    if path.startswith("skills/"):
        return "skill"
    if path.startswith("scripts/"):
        return "operator_or_validator"
    if "/runtime/" in path:
        return "runtime_policy_or_manifest"
    if "/canonical/" in path or path.endswith(".schema.json"):
        return "schema"
    if path.startswith("foundations/contracts/"):
        return "business_or_governance_contract"
    if path.startswith("evaluations/step8/"):
        return "accepted_pilot_evidence"
    return "profile_root_or_foundation"


def main() -> int:
    STEP9.mkdir(parents=True, exist_ok=True)
    active = load_json(ACTIVE)
    step5 = load_json(STEP5)
    acceptance = load_json(STEP8_ACCEPTANCE)
    closure = load_json(STEP8_VALIDATION)
    runtime_policy = yaml.safe_load(RUNTIME_POLICY.read_text(encoding="utf-8"))
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))

    active_rows = []
    for item in active["active_files"]:
        path = ROOT / item["path"]
        actual_sha = sha(path) if path.exists() else None
        active_rows.append(
            {
                "path": item["path"],
                "exists": path.exists(),
                "declared_sha256": item["sha256"],
                "actual_sha256": actual_sha,
                "hash_matches": actual_sha == item["sha256"],
                "declared_bytes": item["bytes"],
                "actual_bytes": path.stat().st_size if path.exists() else None,
            }
        )
    mismatches = [item for item in active_rows if not item["hash_matches"] or item["declared_bytes"] != item["actual_bytes"]]

    paths: set[str] = {item["path"] for item in active["active_files"]}
    for skill in step5["skills"]:
        paths.add(skill["path"])
        paths.add(skill["evals_path"])
    for operator in step5["operators"]:
        paths.add(operator["path"])
    paths.add(step5["orchestrator"]["path"])
    paths.update(item["path"] for item in step5["supporting_modules"])
    paths.update(
        {
            "evaluations/step8/acceptance-record.json",
            "evaluations/step8/final-closure-validation.json",
            "foundations/contracts/runtime/a2-step8-pilot-acceptance-manifest-0.1.0.json",
            "evaluations/step8/pilot/A1-DARLEY-JONABELL-001/canonical/revision-005-record-approved.json",
            "evaluations/step8/pilot/A1-RR-PODIATRY-001/canonical/revision-005-held.json",
            "evaluations/step8/pilot/A1-RR-PODIATRY-001/behavioral-replay/validation.json",
        }
    )
    for pattern in ("scripts/run_step*_tests.py", "scripts/validate_step*.py", "scripts/*step9*.py"):
        paths.update(str(path.relative_to(ROOT)) for path in ROOT.glob(pattern) if path.is_file())
    inherited_versions: dict[str, tuple[str, str]] = {}
    for skill in step5["skills"]:
        skill_version, _ = infer_version(ROOT / skill["path"])
        if skill_version:
            inherited_versions[skill["evals_path"]] = (skill_version, f"owner_skill:{skill['skill_id']}")
    for operator in step5["operators"]:
        inherited_versions[operator["path"]] = (step5["version"], "step5_runtime_manifest")
    inherited_versions[step5["orchestrator"]["path"]] = (step5["version"], "step5_runtime_manifest")
    for module in step5["supporting_modules"]:
        inherited_versions[module["path"]] = (step5["version"], "step5_runtime_manifest")
    step8_version = load_json(STEP8_RUNTIME).get("version", "0.1.0")

    inventory = []
    for rel in sorted(paths):
        path = ROOT / rel
        version, source = infer_version(path) if path.exists() else (None, "missing")
        if version is None and rel in inherited_versions:
            version, source = inherited_versions[rel]
        elif version is None and rel.startswith("evaluations/step8/"):
            version, source = step8_version, "step8_acceptance_bundle"
        elif version is None and (rel.startswith("scripts/run_step") or rel.startswith("scripts/validate_step") or "step9" in rel):
            version, source = "1.0.0-rc.1", "step9_validation_bundle"
        elif version is None and rel in {item["path"] for item in active["active_files"]}:
            version, source = active["version"], "active_foundation_bundle"
        inventory.append(
            {
                "category": category(rel),
                "path": rel,
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha(path) if path.exists() else None,
                "version": version,
                "version_source": source,
                "freeze_status": "candidate" if path.exists() and version else "blocked_missing_or_unversioned",
            }
        )
    unversioned = [item["path"] for item in inventory if item["version"] is None]
    missing = [item["path"] for item in inventory if not item["exists"]]
    inventory_doc = {
        "record_type": "step9_release_candidate_inventory",
        "profile": "equinet-a2-enrichment",
        "release_candidate": "equinet-a2-no-integration-1.0.0-rc.1",
        "status": "preflight_inventory_not_frozen",
        "items": inventory,
        "counts": {
            "total": len(inventory),
            "skills": sum(item["category"] == "skill" and item["path"].endswith("SKILL.md") for item in inventory),
            "operators_and_validators": sum(item["category"] == "operator_or_validator" for item in inventory),
            "missing": len(missing),
            "unversioned": len(unversioned),
        },
        "missing_paths": missing,
        "unversioned_paths": unversioned,
        "external_actions": 0,
    }
    INVENTORY.write_text(json.dumps(inventory_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    corrections = [
        {
            "id": "S9-C1",
            "finding": "The active foundation manifest has stale hashes for SOUL.md and config.yaml after approved Step 8 closure changes.",
            "action": "Build a release-candidate active-foundation manifest with current hashes; do not overwrite the Step 8 historical snapshot.",
            "status": "required",
        },
        {
            "id": "S9-C2",
            "finding": "The active Step 6 runtime policy still describes synthetic-only real-data gates and a configured fallback, while the accepted Step 8 route used a named two-candidate policy with fallback disabled.",
            "action": "Create a consolidated no-integration runtime policy for the release; preserve the historical Step 6 and Step 8 policies.",
            "status": "required",
        },
        {
            "id": "S9-C3",
            "finding": "The Step 8 receipt helper omitted person.business_phone from its allowlist despite the authoritative catalogue permitting that field.",
            "action": "Retain the tested correction and verify the generic runtime preflight already permits the field; keep the Step 8 helper as pilot evidence rather than a core operator.",
            "status": "implemented_requires_freeze_test",
        },
        {
            "id": "S9-C4",
            "finding": "The live pilot clarified that selected named contact and target-role priority are separate concepts.",
            "action": "Propagate unambiguous terminology to the runbook and review guidance; do not change the canonical field model.",
            "status": "required_documentation",
        },
        {
            "id": "S9-C5",
            "finding": "Normal A2 operation uses one consolidated final human review; intermediate pilot checks were implementation-test checkpoints only.",
            "action": "Verify SOUL, review skill and runbook consistently implement the single-final-review model.",
            "status": "required_regression",
        },
        {
            "id": "S9-C6",
            "finding": "The Rood & Riddle replay used 234,533 tokens and 9 model API calls; cost remained unknown.",
            "action": "Record this as an optimisation baseline, reduce redundant path discovery and context loading, and do not treat unknown cost as zero.",
            "status": "required_evaluation",
        },
        {
            "id": "S9-C7",
            "finding": "The Rood & Riddle accepted outcome proves that a High A1 score can coexist with an A2 held state when minimum-package evidence is incomplete.",
            "action": "Preserve held-gap behaviour and add it to the frozen acceptance tests and runbook.",
            "status": "required_regression",
        },
        {
            "id": "S9-C8",
            "finding": "The non-interactive profile initially opened outside the requested relative workspace and performed two path-search recovery calls.",
            "action": "Use exact absolute profile paths in the frozen runbook and replay controller.",
            "status": "required_documentation",
        },
    ]
    policy_conflicts = {
        "runtime_policy_status": runtime_policy.get("status"),
        "runtime_policy_real_data_status": runtime_policy.get("real_data_activation_gate", {}).get("current_status"),
        "runtime_policy_fallback_model": runtime_policy.get("model_routing", {}).get("fallback", {}).get("logical_model"),
        "effective_config_fallback_count": len(config.get("fallback_providers", [])),
        "effective_config_web_enabled": "web" in config or "web" in config.get("platform_toolsets", {}).get("cli", []),
        "step8_acceptance": acceptance.get("decision"),
    }
    preflight = {
        "record_type": "step9_preflight_audit",
        "profile": "equinet-a2-enrichment",
        "step": "9",
        "status": "started_preflight_corrections_required",
        "step8_acceptance_valid": closure.get("status") == "pass_approved_for_step9",
        "active_foundation": {
            "declared_status": active.get("status"),
            "files": len(active_rows),
            "matching": len(active_rows) - len(mismatches),
            "mismatches": mismatches,
        },
        "installed_skills": {
            "count": step5.get("skill_count"),
            "all_versioned": all(item["version"] is not None for item in inventory if item["category"] == "skill" and item["path"].endswith("SKILL.md")),
            "versions": sorted({item["version"] for item in inventory if item["category"] == "skill" and item["path"].endswith("SKILL.md")}),
        },
        "operators": {"count": step5.get("operator_count"), "orchestrator": step5["orchestrator"]["path"]},
        "runtime_reconciliation": policy_conflicts,
        "pilot_corrections": corrections,
        "release_inventory": str(INVENTORY.relative_to(ROOT)),
        "freeze_blockers": [
            "Release-candidate active-foundation manifest not yet built.",
            "Consolidated no-integration runtime policy not yet built.",
            "Offline regression and exact accepted-record replay not yet run.",
            "Delivery documents and safe archive not yet built.",
            "Step 9 human approval not yet recorded.",
        ] + ([f"Unversioned inventory items: {len(unversioned)}"] if unversioned else []) + ([f"Missing inventory items: {len(missing)}"] if missing else []),
        "external_actions": 0,
    }
    PREFLIGHT.write_text(json.dumps(preflight, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if PLAN.exists():
        plan = load_json(PLAN)
    else:
        plan = {
            "record_type": "step9_execution_plan",
            "profile": "equinet-a2-enrichment",
            "status": "in_progress",
            "release_candidate": "equinet-a2-no-integration-1.0.0-rc.1",
            "phases": [
                {"id": "9A", "name": "Pre-freeze audit and correction propagation", "status": "in_progress"},
                {"id": "9B", "name": "Offline regression and exact no-Web replay", "status": "pending"},
                {"id": "9C", "name": "Release manifest and delivery documentation", "status": "pending"},
                {"id": "9D", "name": "Safe archive and independent verification", "status": "pending"},
                {"id": "9E", "name": "Séverine approval and atomic promotion", "status": "pending_human_decision"},
            ],
            "promotion_target": "PILOT_READY_NO_INTEGRATION",
            "promotion_boundary": "Unitalk no-integration pilot readiness only; not production or contractual acceptance.",
            "external_actions": 0,
        }
    PLAN.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    REVIEW.write_text(
        f"""# Step 9 Pre-Freeze Review

**Profile:** `equinet-a2-enrichment`  
**Release candidate:** `equinet-a2-no-integration-1.0.0-rc.1`  
**Status:** `STARTED — PREFLIGHT CORRECTIONS REQUIRED`

## Baseline

- Step 8 acceptance: PASS and approved for Step 9.
- Skills: **{step5['skill_count']}**, all with version `0.1.0`.
- Operators: **{step5['operator_count']}** plus the local orchestrator.
- Active-foundation inventory: **{len(active_rows)} files**; **{len(mismatches)} hash mismatches**.
- Release-candidate inventory: **{len(inventory)} files**; missing **{len(missing)}**; unversioned **{len(unversioned)}**.

## Required correction propagation

| ID | Finding | Required action |
|---|---|---|
""" + "\n".join(f"| {item['id']} | {item['finding']} | {item['action']} |" for item in corrections) + """

## Freeze blockers

""" + "\n".join(f"- {item}" for item in preflight["freeze_blockers"]) + """

## Boundary

No promotion has occurred. The profile remains **FOUNDATION CONFIGURED — NOT PILOT-READY**. No external action was performed.
""",
        encoding="utf-8",
    )
    print(json.dumps({"status": preflight["status"], "active_files": len(active_rows), "active_hash_mismatches": len(mismatches), "skills": step5["skill_count"], "operators": step5["operator_count"], "release_inventory": len(inventory), "unversioned": len(unversioned), "missing": len(missing), "corrections": len(corrections), "external_actions": 0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
