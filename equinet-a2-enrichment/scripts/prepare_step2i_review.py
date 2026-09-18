#!/usr/bin/env python3
"""Prepare and validate the Step 2I canonical contract promotion review."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

PROFILE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROFILE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_a2_enrichment_record import (  # noqa: E402
    check_current_record,
    check_previous_revision,
    make_registry,
    schema_errors,
)

ROOT = PROFILE_ROOT / "evaluations" / "step2i"
PROPOSED = ROOT / "proposed"
PROPOSED_RECORDS = PROPOSED / "records"
ACTIVE_SCHEMA = PROFILE_ROOT / "foundations" / "contracts" / "canonical" / "a2-enrichment-record.schema.json"
PROPOSED_SCHEMA = PROPOSED / "a2-enrichment-record-1.0.0.schema.json"
REVIEW = ROOT / "A2-CANONICAL-DATA-CONTRACT-PROMOTION-REVIEW.md"
VALIDATION = ROOT / "technical-validation.json"
MANIFEST = ROOT / "review-package-manifest.json"

DRAFT_VERSION = "1.0.0-draft.2"
FINAL_VERSION = "1.0.0"
DRAFT_SCHEMA_ID = f"https://unitalk.ai/schemas/equinet/a2/enrichment-record/{DRAFT_VERSION}"
FINAL_SCHEMA_ID = f"https://unitalk.ai/schemas/equinet/a2/enrichment-record/{FINAL_VERSION}"

PREREQUISITE_VALIDATIONS = {
    "Step 1B": PROFILE_ROOT / "evaluations" / "step1b" / "contract-validation.json",
    "Step 2A": PROFILE_ROOT / "evaluations" / "step2a" / "design-validation.json",
    "Step 2B": PROFILE_ROOT / "evaluations" / "step2b" / "technical-validation.json",
    "Step 2C": PROFILE_ROOT / "evaluations" / "step2c" / "technical-validation.json",
    "Step 2D": PROFILE_ROOT / "evaluations" / "step2d" / "technical-validation.json",
    "Step 2E": PROFILE_ROOT / "evaluations" / "step2e" / "technical-validation.json",
    "Step 2F": PROFILE_ROOT / "evaluations" / "step2f" / "technical-validation.json",
    "Step 2G": PROFILE_ROOT / "evaluations" / "step2g" / "technical-validation.json",
    "Step 2H": PROFILE_ROOT / "evaluations" / "step2h" / "technical-validation.json",
}

PREREQUISITE_ACCEPTANCES = {
    "Step 2A": PROFILE_ROOT / "evaluations" / "step2a" / "acceptance-record.json",
    "Step 2B": PROFILE_ROOT / "evaluations" / "step2b" / "acceptance-record.json",
    "Step 2C": PROFILE_ROOT / "evaluations" / "step2c" / "acceptance-record.json",
    "Step 2D": PROFILE_ROOT / "evaluations" / "step2d" / "acceptance-record.json",
    "Step 2E": PROFILE_ROOT / "evaluations" / "step2e" / "acceptance-record.json",
    "Step 2F": PROFILE_ROOT / "evaluations" / "step2f" / "acceptance-record.json",
    "Step 2G": PROFILE_ROOT / "evaluations" / "step2g" / "acceptance-record.json",
    "Step 2H": PROFILE_ROOT / "evaluations" / "step2h" / "acceptance-record.json",
}

REPRESENTATIVE_RECORDS = {
    "farrier_review_required": (
        PROFILE_ROOT / "evaluations" / "step2f" / "fixtures" / "valid" / "farrier-review-required.json",
        PROFILE_ROOT / "evaluations" / "step2f" / "fixtures" / "valid" / "farrier-review-required-previous.json",
    ),
    "farrier_conflict_held": (
        PROFILE_ROOT / "evaluations" / "step2f" / "fixtures" / "valid" / "farrier-conflict-held.json",
        PROFILE_ROOT / "evaluations" / "step2f" / "fixtures" / "valid" / "farrier-conflict-held-previous.json",
    ),
    "horse_owner_gap_held": (
        PROFILE_ROOT / "evaluations" / "step2f" / "fixtures" / "valid" / "horse-owner-gap-held.json",
        PROFILE_ROOT / "evaluations" / "step2f" / "fixtures" / "valid" / "horse-owner-gap-held-previous.json",
    ),
    "horse_owner_requalification": (
        PROFILE_ROOT / "evaluations" / "step2f" / "fixtures" / "valid" / "horse-owner-complete-requalification.json",
        PROFILE_ROOT / "evaluations" / "step2f" / "fixtures" / "valid" / "horse-owner-complete-requalification-previous.json",
    ),
    "farrier_protected_update": (
        PROFILE_ROOT / "evaluations" / "step2f" / "fixtures" / "valid" / "farrier-protected-update-awaiting-review.json",
        PROFILE_ROOT / "evaluations" / "step2f" / "fixtures" / "valid" / "farrier-protected-update-awaiting-review-previous.json",
    ),
    "farrier_confirmed_duplicate": (
        PROFILE_ROOT / "evaluations" / "step2f" / "fixtures" / "valid" / "farrier-confirmed-duplicate-blocked.json",
        PROFILE_ROOT / "evaluations" / "step2f" / "fixtures" / "valid" / "farrier-confirmed-duplicate-blocked-previous.json",
    ),
}

DECISIONS = {
    "I1": "Promote the unchanged approved canonical structure from 1.0.0-draft.2 to 1.0.0.",
    "I2": "Keep exactly fourteen required top-level sections and strict locally defined objects.",
    "I3": "Keep the Field Catalogue, minimum packages, source/provider policy, confidence/freshness rules, protected-field catalogue, approval matrix, CRM mapping and retention policy outside the stable schema.",
    "I4": "Preserve the complete A1 handoff and A1-only numeric scoring boundary; A2 may create evidence-backed requalification signals but cannot calculate scores.",
    "I5": "Keep canonical JSON as the sole lossless record and Markdown, CSV and Excel as read-only derived views.",
    "I6": "Promote dependent active tooling and synthetic test assets together, while preserving a hashed pre-promotion evidence snapshot.",
    "I7": "Require all Step 2D–2H regression suites and the deployment-language audit to pass after promotion.",
    "I8": "Keep all external integrations and actions disabled; schema promotion does not authorise enrichment, provider use, CRM access, writeback, outreach or pilot use.",
    "I9": "Create a Step 2I acceptance record that pins the final schema, dependency manifest, validation and promotion evidence hashes.",
    "I10": "After successful promotion, advance the next foundation gate to Step 3A — Business Field Catalogue.",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def promote_schema(schema: dict) -> dict:
    proposed = copy.deepcopy(schema)
    proposed["$id"] = FINAL_SCHEMA_ID
    proposed["description"] = proposed["description"].replace("Strict draft canonical record", "Strict canonical record")
    proposed["properties"]["record_metadata"]["properties"]["schema_version"]["const"] = FINAL_VERSION
    proposed["x-unitalk-contract"]["status"] = "proposed_for_step_2i_promotion_review"
    return proposed


def promote_record(record: dict) -> dict:
    proposed = copy.deepcopy(record)
    proposed["record_metadata"]["schema_version"] = FINAL_VERSION
    return proposed


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


def record_summary(record: dict) -> dict:
    candidate = record["source_handoff"]["handoff_snapshot"]["candidate_snapshot"]
    return {
        "segment": candidate["segment"],
        "workflow_state": record["workflow"]["state"],
        "data_quality": record["data_quality"]["status"],
        "a2_eligibility": record["duplicate_and_eligibility"]["a2_eligibility_status"],
        "record_decision": record["review"]["record_decision"],
        "field_assessments": len(record["field_assessments"]),
        "evidence_items": len(record["evidence_registry"]),
        "requalification_signals": len(record["requalification"]["signals"]),
        "requalification_returns": len(record["requalification"]["returns"]),
        "score_revision_references": len(record["requalification"]["score_revision_references"]),
        "recorded_external_actions": sum(
            event["external_action"] is not None
            for event in record["audit_and_consumption"]["events"]
        ),
    }


def impact_inventory() -> dict:
    suffixes = {".md", ".json", ".py", ".yaml", ".yml", ".csv", ".txt"}
    groups: dict[str, list[str]] = {
        "active_foundations": [],
        "active_scripts": [],
        "synthetic_and_generated_evaluations": [],
        "historical_acceptance_and_review_evidence": [],
        "other": [],
    }
    for path in sorted(PROFILE_ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        if ".venv" in path.parts or "__pycache__" in path.parts or ROOT in path.parents:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if DRAFT_VERSION not in text:
            continue
        relative = str(path.relative_to(PROFILE_ROOT))
        if relative.startswith("foundations/"):
            groups["active_foundations"].append(relative)
        elif relative.startswith("scripts/"):
            groups["active_scripts"].append(relative)
        elif relative.startswith("evaluations/") and ("acceptance-record" in relative or "REVIEW" in relative or "correction" in relative):
            groups["historical_acceptance_and_review_evidence"].append(relative)
        elif relative.startswith("evaluations/"):
            groups["synthetic_and_generated_evaluations"].append(relative)
        else:
            groups["other"].append(relative)
    return {
        "draft_reference_file_count": sum(len(paths) for paths in groups.values()),
        "groups": {name: {"count": len(paths), "paths": paths} for name, paths in groups.items()},
        "promotion_rule": "Update active foundations, active scripts, active synthetic fixtures and generated outputs. Preserve historical acceptance/review evidence in a hashed pre-promotion snapshot and do not reinterpret prior approval as approval of 1.0.0.",
    }


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []

    validations = {}
    for name, path in PREREQUISITE_VALIDATIONS.items():
        value = load(path)
        passed = value.get("pass") is True
        validations[name] = {"path": str(path.relative_to(PROFILE_ROOT)), "sha256": sha256(path), "passed": passed}
        if not passed:
            failures.append(f"prerequisite validation failed: {name}")

    acceptances = {}
    for name, path in PREREQUISITE_ACCEPTANCES.items():
        value = load(path)
        passed = value.get("decision") in {"approved_as_drafted", "approved"}
        acceptances[name] = {"path": str(path.relative_to(PROFILE_ROOT)), "sha256": sha256(path), "decision": value.get("decision"), "passed": passed}
        if not passed:
            failures.append(f"prerequisite acceptance missing: {name}")

    step2h_acceptance = load(PREREQUISITE_ACCEPTANCES["Step 2H"])
    if step2h_acceptance.get("next_gate") != "Step 2I — Canonical Data Contract Review and Promotion":
        failures.append("Step 2H does not point to Step 2I")

    soul = (PROFILE_ROOT / "SOUL.md").read_text(encoding="utf-8")
    roadmap = (PROFILE_ROOT / "deliverables" / "A2-DELIVERY-STATUS-AND-ROADMAP.md").read_text(encoding="utf-8")
    state_alignment = {
        "soul_points_to_step2i": "The current next delivery gate is Step 2I Canonical Data Contract Review and Promotion." in soul,
        "roadmap_points_to_step2i": "**Next delivery gate:** `Step 2I — Canonical Data Contract Review and Promotion`" in roadmap,
        "profile_not_pilot_ready": "FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY" in soul,
    }
    for name, passed in state_alignment.items():
        if not passed:
            failures.append(f"profile state alignment failed: {name}")

    active_schema = load(ACTIVE_SCHEMA)
    proposed_schema = promote_schema(active_schema)
    write_json(PROPOSED_SCHEMA, proposed_schema)
    schema_differences = differing_paths(active_schema, proposed_schema)
    expected_schema_differences = sorted([
        "$/description",
        "$/properties/record_metadata/properties/schema_version/const",
        "$/x-unitalk-contract/status",
        "$/$id",
    ])
    schema_change_is_version_only = sorted(schema_differences) == expected_schema_differences
    if not schema_change_is_version_only:
        failures.append(f"proposed schema contains unexpected changes: {schema_differences}")

    proposed_registry = make_registry(proposed_schema)
    representative = {}
    for name, (record_path, previous_path) in REPRESENTATIVE_RECORDS.items():
        record = load(record_path)
        previous = load(previous_path)
        proposed_record = promote_record(record)
        proposed_previous = promote_record(previous)
        output_dir = PROPOSED_RECORDS / name
        current_output = output_dir / "record.json"
        previous_output = output_dir / "previous-record.json"
        write_json(current_output, proposed_record)
        write_json(previous_output, proposed_previous)
        errors = schema_errors(proposed_record, proposed_schema, proposed_registry)
        errors.extend(check_current_record(proposed_record, None))
        prior_errors = schema_errors(proposed_previous, proposed_schema, proposed_registry)
        if prior_errors:
            errors.extend(f"previous:{item}" for item in prior_errors)
        else:
            errors.extend(f"previous:{item}" for item in check_current_record(proposed_previous, None))
            errors.extend(check_previous_revision(proposed_record, proposed_previous))
        changed_record_paths = differing_paths(record, proposed_record)
        changed_previous_paths = differing_paths(previous, proposed_previous)
        version_only = changed_record_paths == ["$/record_metadata/schema_version"] and changed_previous_paths == ["$/record_metadata/schema_version"]
        if not version_only:
            errors.append("record migration changed more than record_metadata.schema_version")
        representative[name] = {
            "source_record": str(record_path.relative_to(PROFILE_ROOT)),
            "source_sha256": sha256(record_path),
            "proposed_record": str(current_output.relative_to(PROFILE_ROOT)),
            "proposed_sha256": sha256(current_output),
            "proposed_previous_record": str(previous_output.relative_to(PROFILE_ROOT)),
            "summary": record_summary(proposed_record),
            "changed_paths": changed_record_paths,
            "valid": not errors,
            "errors": errors,
        }
        if errors:
            failures.append(f"proposed representative record failed: {name}")

    impact = impact_inventory()
    validation = {
        "step": "2I",
        "stage": "pre_promotion_review",
        "approval_state": "ready_for_severine_review_not_promoted",
        "active_schema": {
            "version": DRAFT_VERSION,
            "id": DRAFT_SCHEMA_ID,
            "path": str(ACTIVE_SCHEMA.relative_to(PROFILE_ROOT)),
            "sha256": sha256(ACTIVE_SCHEMA),
        },
        "proposed_schema": {
            "version": FINAL_VERSION,
            "id": FINAL_SCHEMA_ID,
            "path": str(PROPOSED_SCHEMA.relative_to(PROFILE_ROOT)),
            "sha256": sha256(PROPOSED_SCHEMA),
            "changed_paths": schema_differences,
            "version_only_change": schema_change_is_version_only,
            "canonical_structure_hash": canonical_hash({
                "properties": proposed_schema["properties"],
                "required": proposed_schema["required"],
                "$defs": proposed_schema["$defs"],
                "allOf": proposed_schema.get("allOf", []),
            }),
        },
        "prerequisite_validations": validations,
        "prerequisite_acceptances": acceptances,
        "profile_state_alignment": state_alignment,
        "representative_records": representative,
        "representative_summary": {
            "expected": len(REPRESENTATIVE_RECORDS),
            "passed": sum(item["valid"] for item in representative.values()),
            "failed": sum(not item["valid"] for item in representative.values()),
            "segments": sorted({item["summary"]["segment"] for item in representative.values()}),
            "recorded_external_actions": sum(item["summary"]["recorded_external_actions"] for item in representative.values()),
        },
        "promotion_impact": impact,
        "decisions_for_review": DECISIONS,
        "promotion_performed": False,
        "external_actions": 0,
        "failures": failures,
        "pass": not failures,
    }
    write_json(VALIDATION, validation)

    rows = []
    for name, item in representative.items():
        summary = item["summary"]
        rows.append(
            f"| `{name}` | {summary['segment']} | {summary['workflow_state']} | {summary['data_quality']} | "
            f"{summary['a2_eligibility']} | {summary['record_decision']} | "
            f"{summary['field_assessments']} / {summary['evidence_items']} | "
            f"{summary['requalification_signals']} / {summary['requalification_returns']} / {summary['score_revision_references']} | PASS |"
        )
    decision_rows = [f"| {key} | {value} |" for key, value in DECISIONS.items()]
    prerequisite_rows = [f"| {name} | PASS | `{item['sha256']}` |" for name, item in validations.items()]

    review = f"""# Step 2I — Canonical Data Contract Review and Promotion\n\n**Profile:** `equinet-a2-enrichment`  \n**Review status:** `READY FOR SÉVERINE REVIEW — NOT PROMOTED`  \n**Current schema:** `{DRAFT_VERSION}`  \n**Proposed schema:** `{FINAL_VERSION}`  \n**Profile status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`  \n\n## 1. Decision requested\n\nApprove or request changes to decisions I1–I10. No active schema, runtime artifact, integration or profile status has been promoted by preparing this package.\n\n## 2. Verified prerequisite chain\n\n| Gate | Result | Validation SHA-256 |\n|---|---:|---|\n{chr(10).join(prerequisite_rows)}\n\nAll approved foundation gates from Step 1B through Step 2H were rerun before this review. All passed. Step 2H explicitly authorises review at Step 2I.\n\n## 3. Proposed promotion\n\nThe proposed `1.0.0` schema changes only four metadata paths from the approved `1.0.0-draft.2` schema:\n\n- `$id`;\n- schema description, removing the word `draft`;\n- `record_metadata.schema_version.const`;\n- `x-unitalk-contract.status`.\n\nNo canonical section, field, type, required rule, state vocabulary, external schema reference, no-integration ceiling or conditional rule changes.\n\n## 4. Representative synthetic records\n\n| Record | Segment | Workflow | Data quality | A2 eligibility | Review | Fields / evidence | Signals / returns / score refs | Proposed 1.0.0 validation |\n|---|---|---|---|---|---|---:|---:|---:|\n{chr(10).join(rows)}\n\nThe review set covers normal human review, conflict hold, gap hold, complete requalification, protected update and confirmed duplicate blocking. Each proposed copy differs from its approved synthetic source only at `record_metadata.schema_version`. Recorded external actions across the set: **0**.\n\n## 5. Stable contract being promoted\n\n- Fourteen required canonical sections.\n- Immutable A1 handoff and immutable A2 revision lineage.\n- Field flow: baseline → observations → proposal → human decision → application state.\n- Separate A1 and A2 evidence namespaces.\n- A1-only numeric scoring; A2 can only initiate evidence-backed requalification.\n- Canonical JSON as the only lossless record.\n- Read-only Markdown, CSV and Excel projections.\n- Strict no-integration, approval, provider, CRM-write and outreach ceilings.\n\n## 6. Configuration deliberately not promoted into the schema\n\nThe Business Field Catalogue, minimum data packages, source/provider policy, confidence/freshness rules, protected-field catalogue, approval matrix, CRM mapping, retention policy and operating quotas remain separate versioned configurations. They continue in Step 3 and later gates.\n\n## 7. Atomic promotion plan after approval\n\n1. Create a hashed pre-promotion evidence snapshot.\n2. Promote the schema and active dependency manifest to `1.0.0`.\n3. Update active validator, initialiser, review-view compatibility and synthetic fixtures together.\n4. Regenerate all active manifests and review projections.\n5. Run all Step 2D–2H deterministic suites plus the language audit.\n6. Search active artifacts for stale draft references and unresolved pending-promotion markers.\n7. Create the final Step 2I acceptance and promotion records with hashes.\n8. Update the temporary SOUL and roadmap to Step 3A.\n\nFiles containing the draft identifier before promotion: **{impact['draft_reference_file_count']}**. Historical acceptance and review evidence will be preserved in the pre-promotion snapshot rather than silently reinterpreted.\n\n## 8. Decisions for Séverine\n\n| ID | Proposed decision |\n|---|---|\n{chr(10).join(decision_rows)}\n\n## 9. What this approval does not approve\n\n- live prospect enrichment;\n- source activation or paid-provider use;\n- A1/A2 production delivery;\n- HubSpot, Twenty or n8n access;\n- CRM writeback;\n- outreach;\n- pilot readiness;\n- production readiness;\n- contractual acceptance.\n\n## 10. Current technical conclusion\n\n**PASS — ready for Séverine's Step 2I decision.** The active schema remains `{DRAFT_VERSION}` until explicit approval is recorded.\n"""
    REVIEW.write_text(review, encoding="utf-8")

    package_files = [PROPOSED_SCHEMA, VALIDATION, REVIEW]
    for directory in sorted(PROPOSED_RECORDS.iterdir()):
        package_files.extend([directory / "record.json", directory / "previous-record.json"])
    manifest = {
        "manifest_id": "equinet-a2-step2i-review-package",
        "stage": "pre_promotion_review",
        "approval_state": "ready_for_severine_review_not_promoted",
        "files": [
            {
                "path": str(path.relative_to(PROFILE_ROOT)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in package_files
        ],
        "file_count": len(package_files),
        "promotion_performed": False,
        "external_actions": 0,
    }
    write_json(MANIFEST, manifest)

    print(json.dumps({
        "pass": not failures,
        "approval_state": validation["approval_state"],
        "active_schema": validation["active_schema"],
        "proposed_schema": validation["proposed_schema"],
        "prerequisite_validations": len(validations),
        "prerequisite_acceptances": len(acceptances),
        "representative_records": validation["representative_summary"],
        "draft_reference_file_count": impact["draft_reference_file_count"],
        "review": str(REVIEW),
        "manifest": str(MANIFEST),
        "promotion_performed": False,
        "failures": failures,
    }, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
