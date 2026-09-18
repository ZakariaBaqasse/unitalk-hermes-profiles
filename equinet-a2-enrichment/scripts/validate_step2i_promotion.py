#!/usr/bin/env python3
"""Validate the completed Step 2I canonical data-contract promotion."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PROFILE_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROFILE_ROOT / "evaluations" / "step2i"
SCHEMA = PROFILE_ROOT / "foundations" / "contracts" / "canonical" / "a2-enrichment-record.schema.json"
DEPENDENCY_MANIFEST = PROFILE_ROOT / "foundations" / "contracts" / "canonical" / "a2-enrichment-record.dependency-manifest.json"
VALIDATOR_MANIFEST = PROFILE_ROOT / "foundations" / "contracts" / "canonical" / "a2-cross-field-validator.manifest.json"
SPEC = PROFILE_ROOT / "foundations" / "contracts" / "canonical" / "a2-review-view-spec-0.1.0.json"
PROPOSED_SCHEMA = ROOT / "proposed" / "a2-enrichment-record-1.0.0.schema.json"
APPROVAL = ROOT / "approval-record.json"
SNAPSHOT = ROOT / "pre-promotion-snapshot.tar.gz"
OUTPUT = ROOT / "post-promotion-technical-validation.json"
MANIFEST = ROOT / "promotion-manifest.json"

EXPECTED_SNAPSHOT_SHA256 = "907ad381e494efbdb14091cb6a029bd344ecd6322b5d74df554143f13511b5ae"
EXPECTED_COUNTS = {
    "step2d": {"smoke_tests.passed": 7},
    "step2e": {"summary.cases_passed": 59},
    "step2f": {"summary.cases_passed": 29},
    "step2g": {"summary.cases_passed": 11, "summary.deterministic_controls_passed": 15},
    "step2h": {"summary.sample_packages_passed": 6, "summary.negative_checks_passed": 11},
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_path(value: dict, dotted: str) -> Any:
    current: Any = value
    for part in dotted.split("."):
        current = current[part]
    return current


def differing_paths(left: Any, right: Any, path: str = "$") -> list[str]:
    if type(left) is not type(right):
        return [path]
    if isinstance(left, dict):
        paths = []
        for key in sorted(set(left) | set(right)):
            child = f"{path}/{key}"
            if key not in left or key not in right:
                paths.append(child)
            else:
                paths.extend(differing_paths(left[key], right[key], child))
        return paths
    if isinstance(left, list):
        if len(left) != len(right):
            return [path]
        paths = []
        for index, (a, b) in enumerate(zip(left, right)):
            paths.extend(differing_paths(a, b, f"{path}/{index}"))
        return paths
    return [] if left == right else [path]


def iter_record_versions(path: Path) -> list[dict]:
    results = []
    for file_path in sorted(path.rglob("*.json")):
        try:
            value = load(file_path)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(value, dict) and isinstance(value.get("record_metadata"), dict) and "schema_version" in value["record_metadata"]:
            results.append({
                "path": str(file_path.relative_to(PROFILE_ROOT)),
                "version": value["record_metadata"]["schema_version"],
            })
    return results


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    failures: list[str] = []
    approval = load(APPROVAL)
    schema = load(SCHEMA)
    proposed = load(PROPOSED_SCHEMA)
    dependency_manifest = load(DEPENDENCY_MANIFEST)
    validator_manifest = load(VALIDATOR_MANIFEST)
    spec = load(SPEC)

    approval_checks = {
        "decision": approval.get("decision") == "approved",
        "promotion_authorized": approval.get("promotion_authorized") is True,
        "decisions_i1_i10": set(approval.get("approved_decisions", {})) == {f"I{number}" for number in range(1, 11)},
        "approver": approval.get("approver", {}).get("name") == "Séverine",
    }

    schema_checks = {
        "version": schema["properties"]["record_metadata"]["properties"]["schema_version"]["const"] == "1.0.0",
        "schema_id": schema.get("$id") == "https://unitalk.ai/schemas/equinet/a2/enrichment-record/1.0.0",
        "status": schema.get("x-unitalk-contract", {}).get("status") == "promoted_by_unitalk_in_step_2i",
        "sections": len(schema.get("required", [])) == 14 and schema.get("required") == list(schema.get("properties", {})),
        "dependency_manifest_version": dependency_manifest.get("schema_version") == "1.0.0",
        "dependency_manifest_status": dependency_manifest.get("status") == "promoted_by_unitalk_in_step_2i",
        "dependency_manifest_schema_hash": dependency_manifest.get("schema_sha256") == sha256(SCHEMA),
        "validator_manifest_status": validator_manifest.get("status") == "promoted_by_unitalk_in_step_2i",
        "review_spec_version": spec.get("canonical_input", {}).get("schema_version") == "1.0.0",
        "review_spec_status": spec.get("status") == "promoted_by_unitalk_in_step_2i",
    }

    proposed_normalized = json.loads(json.dumps(proposed))
    proposed_normalized["x-unitalk-contract"]["status"] = "promoted_by_unitalk_in_step_2i"
    schema_difference_paths = differing_paths(proposed_normalized, schema)
    semantic_promotion_check = not schema_difference_paths

    suite_paths = {
        "step2d": PROFILE_ROOT / "evaluations" / "step2d" / "technical-validation.json",
        "step2e": PROFILE_ROOT / "evaluations" / "step2e" / "technical-validation.json",
        "step2f": PROFILE_ROOT / "evaluations" / "step2f" / "technical-validation.json",
        "step2g": PROFILE_ROOT / "evaluations" / "step2g" / "technical-validation.json",
        "step2h": PROFILE_ROOT / "evaluations" / "step2h" / "technical-validation.json",
    }
    suite_checks = {}
    for name, path in suite_paths.items():
        value = load(path)
        counts = {key: get_path(value, key) for key in EXPECTED_COUNTS[name]}
        expected = EXPECTED_COUNTS[name]
        passed = value.get("pass") is True and value.get("approval_state") == "promoted_in_step_2i" and counts == expected
        suite_checks[name] = {
            "path": str(path.relative_to(PROFILE_ROOT)),
            "sha256": sha256(path),
            "approval_state": value.get("approval_state"),
            "counts": counts,
            "expected": expected,
            "passed": passed,
        }

    upstream_paths = {
        "step1b": PROFILE_ROOT / "evaluations" / "step1b" / "contract-validation.json",
        "step2a": PROFILE_ROOT / "evaluations" / "step2a" / "design-validation.json",
        "step2b": PROFILE_ROOT / "evaluations" / "step2b" / "technical-validation.json",
        "step2c": PROFILE_ROOT / "evaluations" / "step2c" / "technical-validation.json",
    }
    upstream_checks = {
        name: {"path": str(path.relative_to(PROFILE_ROOT)), "sha256": sha256(path), "passed": load(path).get("pass") is True}
        for name, path in upstream_paths.items()
    }

    record_roots = [
        PROFILE_ROOT / "foundations" / "contracts" / "canonical" / "examples",
        PROFILE_ROOT / "evaluations" / "step2e" / "fixtures",
        PROFILE_ROOT / "evaluations" / "step2f" / "fixtures",
        PROFILE_ROOT / "evaluations" / "step2g" / "fixtures" / "valid",
        PROFILE_ROOT / "evaluations" / "step2h" / "fixtures",
    ]
    record_versions = [item for root in record_roots for item in iter_record_versions(root)]
    version_failures = [item for item in record_versions if item["version"] != "1.0.0"]
    # The dedicated negative smoke fixture must intentionally carry an invalid version.
    version_failures = [
        item for item in version_failures
        if item["path"] != "foundations/contracts/canonical/examples/invalid/invalid-schema-version.json"
    ]

    soul = (PROFILE_ROOT / "SOUL.md").read_text(encoding="utf-8")
    roadmap = (PROFILE_ROOT / "deliverables" / "A2-DELIVERY-STATUS-AND-ROADMAP.md").read_text(encoding="utf-8")
    active_state_checks = {
        "soul_schema": "A2 Canonical JSON Schema `1.0.0` — promoted" in soul,
        "soul_next_gate": "The current next delivery gate is Step 3A Business Field Catalogue." in soul,
        "roadmap_next_gate": "**Next delivery gate:** `Step 3A — Business Field Catalogue`" in roadmap,
        "profile_not_pilot_ready": "FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY" in soul,
        "hubspot_not_connected": "HubSpot: not connected" in soul,
        "live_enrichment_prohibited": "run live prospect enrichment" in soul,
        "crm_write_prohibited": "access, create, update, merge or delete HubSpot records" in soul,
    }

    language = load(PROFILE_ROOT / "evaluations" / "foundation-clarifications" / "language-audit.json")
    snapshot_checks = {
        "archive_exists": SNAPSHOT.exists(),
        "archive_sha256": sha256(SNAPSHOT) == EXPECTED_SNAPSHOT_SHA256,
        "legacy_schema_hash": sha256(ROOT / "pre-promotion-evidence" / "a2-enrichment-record-1.0.0-draft.2.schema.json") == "f3549e91487571f44ef59cf92e85354af450bbaecd426895548d2b7052f784ee",
        "legacy_step2f_manifest_hash": sha256(ROOT / "pre-promotion-evidence" / "step2f-package-manifest.json") == "5d5dc6a8c14a9f1af6c9f4c0d4b0dad37322eb378dcb709ed73208da86b49514",
        "legacy_step2g_manifest_hash": sha256(ROOT / "pre-promotion-evidence" / "step2g-package-manifest.json") == "786ee42e513bfa3ae11ce2d354a519e7d710e7b1ae17db957e8392b98a1cb31b",
        "legacy_step2h_manifest_hash": sha256(ROOT / "pre-promotion-evidence" / "step2h-package-manifest.json") == "61a6ea643866c6dc806bf41803c355d27e55e905cc569a03412ee405a67b4613",
    }

    check_groups = [approval_checks, schema_checks, active_state_checks, snapshot_checks]
    if not all(all(group.values()) for group in check_groups):
        failures.append("one or more promotion control checks failed")
    if not semantic_promotion_check:
        failures.append(f"final schema differs unexpectedly from approved proposal: {schema_difference_paths}")
    if not all(item["passed"] for item in suite_checks.values()):
        failures.append("one or more Step 2D–2H post-promotion suites failed")
    if not all(item["passed"] for item in upstream_checks.values()):
        failures.append("one or more upstream foundation regressions failed")
    if version_failures:
        failures.append("active synthetic records retain a non-final schema version")
    if not language.get("pass"):
        failures.append("deployment-language audit failed")
    if get_path(load(suite_paths["step2f"]), "coverage.recorded_external_action_claims") != 0:
        failures.append("Step 2F contains an external-action claim")
    if load(suite_paths["step2h"]).get("external_actions") != 0:
        failures.append("Step 2H recorded an external action")

    result = {
        "step": "2I",
        "stage": "post_promotion_validation",
        "approval_state": "approved_and_promoted",
        "schema_version": "1.0.0",
        "schema_path": str(SCHEMA.relative_to(PROFILE_ROOT)),
        "schema_sha256": sha256(SCHEMA),
        "approval_checks": approval_checks,
        "schema_checks": schema_checks,
        "semantic_promotion": {
            "approved_proposal_path": str(PROPOSED_SCHEMA.relative_to(PROFILE_ROOT)),
            "only_expected_status_change_after_approval": semantic_promotion_check,
            "unexpected_difference_paths": schema_difference_paths,
        },
        "post_promotion_suites": suite_checks,
        "upstream_regressions": upstream_checks,
        "active_record_versions": {
            "records_checked": len(record_versions),
            "unexpected_versions": version_failures,
            "passed": not version_failures,
        },
        "active_state_checks": active_state_checks,
        "snapshot_checks": snapshot_checks,
        "language_audit": {
            "files_checked": language.get("files_checked"),
            "findings": len(language.get("findings", [])),
            "passed": language.get("pass") is True,
        },
        "external_actions": 0,
        "integrations_activated": [],
        "profile_status": "FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY",
        "next_gate": "Step 3A — Business Field Catalogue",
        "failures": failures,
        "pass": not failures,
    }
    write_json(OUTPUT, result)

    package_paths = [
        APPROVAL,
        SNAPSHOT,
        ROOT / "pre-promotion-evidence" / "a2-enrichment-record-1.0.0-draft.2.schema.json",
        ROOT / "pre-promotion-evidence" / "a2-enrichment-record.dependency-manifest.json",
        ROOT / "pre-promotion-evidence" / "a2-cross-field-validator.manifest.json",
        ROOT / "pre-promotion-evidence" / "step2f-package-manifest.json",
        ROOT / "pre-promotion-evidence" / "step2g-package-manifest.json",
        ROOT / "pre-promotion-evidence" / "step2h-package-manifest.json",
        SCHEMA,
        DEPENDENCY_MANIFEST,
        VALIDATOR_MANIFEST,
        SPEC,
        PROFILE_ROOT / "foundations" / "A2-CANONICAL-JSON-SCHEMA-CONTRACT.md",
        PROFILE_ROOT / "foundations" / "A2-CROSS-FIELD-VALIDATOR-CONTRACT.md",
        PROFILE_ROOT / "foundations" / "A2-FIXTURES-AND-REGRESSION-CONTRACT.md",
        PROFILE_ROOT / "foundations" / "A2-HANDOFF-TO-RECORD-INITIALISATION-CONTRACT.md",
        PROFILE_ROOT / "foundations" / "A2-REVIEW-VIEW-SPECIFICATION.md",
        PROFILE_ROOT / "scripts" / "build_step2d_schema.py",
        PROFILE_ROOT / "scripts" / "validate_step2d_schema.py",
        PROFILE_ROOT / "scripts" / "validate_a2_enrichment_record.py",
        PROFILE_ROOT / "scripts" / "initialize_a2_record.py",
        PROFILE_ROOT / "scripts" / "render_a2_review_views.py",
        PROFILE_ROOT / "scripts" / "run_step2e_tests.py",
        PROFILE_ROOT / "scripts" / "run_step2f_tests.py",
        PROFILE_ROOT / "scripts" / "run_step2g_tests.py",
        PROFILE_ROOT / "scripts" / "validate_step2h_review_views.py",
        *suite_paths.values(),
        PROFILE_ROOT / "evaluations" / "step2f" / "step2f-package-manifest.json",
        PROFILE_ROOT / "evaluations" / "step2g" / "step2g-package-manifest.json",
        PROFILE_ROOT / "evaluations" / "step2h" / "step2h-package-manifest.json",
        PROFILE_ROOT / "evaluations" / "foundation-clarifications" / "language-audit.json",
        PROFILE_ROOT / "SOUL.md",
        PROFILE_ROOT / "deliverables" / "A2-DELIVERY-STATUS-AND-ROADMAP.md",
        OUTPUT,
    ]
    unique_paths = sorted(set(package_paths))
    manifest = {
        "manifest_id": "equinet-a2-step2i-promotion",
        "schema_version": "1.0.0",
        "approval_state": "approved_and_promoted",
        "files": [
            {"path": str(path.relative_to(PROFILE_ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in unique_paths
        ],
        "file_count": len(unique_paths),
        "external_actions": 0,
        "integrations_activated": [],
        "next_gate": "Step 3A — Business Field Catalogue",
    }
    write_json(MANIFEST, manifest)

    print(json.dumps({
        "pass": result["pass"],
        "approval_state": result["approval_state"],
        "schema_version": result["schema_version"],
        "schema_sha256": result["schema_sha256"],
        "suite_results": {name: item["passed"] for name, item in suite_checks.items()},
        "active_records_checked": len(record_versions),
        "language_audit": result["language_audit"],
        "snapshot_sha256": sha256(SNAPSHOT),
        "manifest": str(MANIFEST),
        "manifest_file_count": len(unique_paths),
        "next_gate": result["next_gate"],
        "failures": failures,
    }, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
