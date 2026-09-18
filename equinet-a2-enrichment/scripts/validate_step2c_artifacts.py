#!/usr/bin/env python3
"""Validate Step 2C requalification contracts, fixtures, and A1 scoring ownership."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

PROFILE_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROFILE_ROOT / "foundations" / "contracts" / "requalification"
DEPENDENCIES = PROFILE_ROOT / "foundations" / "contracts" / "dependencies"
A1_SCHEMA_PATH = DEPENDENCIES / "a1-prospect-candidate.schema.json"
ICP_PATH = DEPENDENCIES / "a1-equinet-icp-v1.yaml"
EVIDENCE_PATH = DEPENDENCIES / "a1-evidence-confidence-rules-v1.yaml"
SCORING_PATH = DEPENDENCIES / "a1-icp-scoring-model-v1.yaml"
DEPENDENCY_MANIFEST = DEPENDENCIES / "a1-requalification-dependency-manifest.json"
OUTPUT = PROFILE_ROOT / "evaluations" / "step2c" / "technical-validation.json"
CONTRACT_DOCUMENT = PROFILE_ROOT / "foundations" / "A2-REQUALIFICATION-AND-SCORE-REVISION-CONTRACT.md"
REVIEW_DOCUMENT = PROFILE_ROOT / "evaluations" / "step2c" / "A2-REQUALIFICATION-SCORE-REVISION-REVIEW.md"

SCHEMA_FILES = {
    "signal": ROOT / "a2-requalification-signal.schema.json",
    "return": ROOT / "a2-requalification-return.schema.json",
    "revision": ROOT / "a1-score-revision-reference.schema.json",
    "package": ROOT / "a2-requalification-package.schema.json",
}
VALID_DIR = ROOT / "examples" / "valid"
INVALID_DIR = ROOT / "examples" / "invalid"

EXPECTED_INVALID = {
    "invalid-signal-with-points.json": "Additional properties are not allowed",
    "invalid-unknown-criterion.json": "unknown A1 criterion_id",
    "invalid-signal-missing-evidence.json": "signal requires at least one A1 or A2 evidence reference",
    "invalid-manual-return-delivered.json": "manual_no_integration_pilot return must remain prepared",
    "invalid-return-signal-hash.json": "signal snapshot hash mismatch",
    "invalid-a2-score-producer.json": "score revision must be produced by equinet-a1-icp-discovery",
    "invalid-score-component-total.json": "revised scoring score must equal component total",
    "invalid-approved-revision-no-review.json": "None is not of type 'object'",
    "invalid-package-signal-mismatch.json": "score revision source_signal_ids must equal package signal IDs",
    "invalid-rejected-signal-with-revision.json": "rejected signals cannot produce a score revision reference",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def configs() -> tuple[set[str], dict[str, int], dict]:
    scoring = load_yaml(SCORING_PATH)
    criteria = set(scoring.get("common_rules", {}).get("blocked_criteria", []))
    weights = {}
    for segment, segment_config in scoring.get("segments", {}).items():
        for criterion_id, weight in segment_config.get("positive_weights", {}).items():
            criteria.add(criterion_id)
            weights[criterion_id] = int(weight)
        criteria.update(segment_config.get("non_scoring_criteria", {}).keys())
        for gate in segment_config.get("required_gates", []):
            criteria.add(gate["criterion_id"])
    return criteria, weights, scoring


def registry_and_schemas() -> tuple[Registry, dict[str, dict]]:
    schemas = {name: load_json(path) for name, path in SCHEMA_FILES.items()}
    a1_schema = load_json(A1_SCHEMA_PATH)
    registry = Registry().with_resource(a1_schema["$id"], Resource.from_contents(a1_schema))
    for schema in schemas.values():
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return registry, schemas


def schema_errors(document: dict, schema: dict, registry: Registry) -> list[str]:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    rendered = []
    for error in errors:
        path = "/" + "/".join(str(part) for part in error.absolute_path)
        rendered.append(f"schema:{path}: {error.message}")
    return rendered


def scoring_errors(label: str, scoring: dict, criteria: set[str], weights: dict[str, int]) -> list[str]:
    errors = []
    components = scoring.get("components", [])
    total = sum(float(component.get("points_awarded", 0)) for component in components)
    score = scoring.get("score")
    if score is not None and abs(float(score) - total) > 1e-6:
        errors.append(f"{label} scoring score must equal component total")
    seen = set()
    for component in components:
        criterion_id = component.get("criterion_id")
        if criterion_id in seen:
            errors.append(f"{label} scoring has duplicate component {criterion_id}")
        seen.add(criterion_id)
        if criterion_id not in criteria:
            errors.append(f"{label} scoring references unknown criterion {criterion_id}")
        expected_weight = weights.get(criterion_id)
        if expected_weight is not None and float(component.get("max_points", 0)) != expected_weight:
            errors.append(f"{label} component {criterion_id} max_points must equal configured weight {expected_weight}")
        if float(component.get("points_awarded", 0)) > float(component.get("max_points", 0)):
            errors.append(f"{label} component {criterion_id} awards more than max_points")
    return errors


def raw_band(score: float, scoring_config: dict) -> str:
    for band_name, band in scoring_config["bands"].items():
        if band["minimum"] <= score <= band["maximum"]:
            return band_name
    raise ValueError(f"No configured band for score {score}")


def signal_errors(signal: dict, criteria: set[str]) -> list[str]:
    errors = []
    if signal.get("affected_criterion_id") not in criteria:
        errors.append(f"unknown A1 criterion_id {signal.get('affected_criterion_id')!r}")
    if not signal.get("a1_evidence_ids") and not signal.get("a2_evidence_ids"):
        errors.append("signal requires at least one A1 or A2 evidence reference")
    if signal.get("created_by_profile") != "equinet-a2-enrichment":
        errors.append("requalification signal must be created by equinet-a2-enrichment")
    if signal.get("prior_criterion_status") == signal.get("proposed_evidence_status") and signal.get("potential_score_direction") != "unchanged":
        errors.append("unchanged criterion evidence status cannot claim increase or decrease direction")
    return errors


def return_errors(return_doc: dict, criteria: set[str]) -> list[str]:
    errors = []
    signals = return_doc.get("signal_snapshots", [])
    if return_doc.get("signal_snapshot_sha256") != canonical_hash(signals):
        errors.append("signal snapshot hash mismatch")
    signal_ids = [signal.get("signal_id") for signal in signals]
    if len(signal_ids) != len(set(signal_ids)):
        errors.append("return contains duplicate signal IDs")
    for signal in signals:
        errors.extend(signal_errors(signal, criteria))
        for field in ["a2_record_id", "a1_candidate_id", "a1_handoff_id", "a1_candidate_snapshot_sha256", "audit_correlation_id", "synthetic"]:
            if signal.get(field) != return_doc.get(field):
                errors.append(f"return {field} must match every signal")
        if signal.get("status") not in {"approved_for_return", "sent_to_a1", "accepted_by_a1", "rescored"}:
            errors.append(f"signal {signal.get('signal_id')} is not approved for return")
    if return_doc.get("operating_scope") == "manual_no_integration_pilot" and return_doc.get("status") != "prepared":
        errors.append("manual_no_integration_pilot return must remain prepared")
    receipt = return_doc.get("a1_receipt")
    if isinstance(receipt, dict):
        if receipt.get("return_id") != return_doc.get("return_id"):
            errors.append("A1 receipt return_id mismatch")
        if receipt.get("signal_snapshot_sha256") != return_doc.get("signal_snapshot_sha256"):
            errors.append("A1 receipt signal hash mismatch")
        expected_receipt = "accepted" if return_doc.get("status") == "accepted_by_a1" else "rejected" if return_doc.get("status") == "rejected_by_a1" else None
        if expected_receipt and receipt.get("status") != expected_receipt:
            errors.append("A1 receipt status does not match return status")
    return errors


def revision_errors(revision: dict, criteria: set[str], weights: dict[str, int], scoring_config: dict) -> list[str]:
    errors = []
    if revision.get("produced_by_profile") != "equinet-a1-icp-discovery":
        errors.append("score revision must be produced by equinet-a1-icp-discovery")
    if revision.get("calculation_method") != "deterministic_a1_scoring":
        errors.append("score revision calculation method must be deterministic_a1_scoring")
    prior = revision.get("prior_scoring", {})
    revised = revision.get("revised_scoring", {})
    errors.extend(scoring_errors("prior", prior, criteria, weights))
    errors.extend(scoring_errors("revised", revised, criteria, weights))
    if prior.get("score") is not None and prior.get("band") != raw_band(float(prior["score"]), scoring_config):
        errors.append("prior scoring band does not match configured raw band")
    if revised.get("score") is not None and revised.get("band") != raw_band(float(revised["score"]), scoring_config):
        errors.append("revised scoring band does not match configured raw band")
    if revision.get("result_sha256") != canonical_hash(revised):
        errors.append("score revision result hash mismatch")

    revision_signal_ids = set(revision.get("source_signal_ids", []))
    validated_evidence = set(revision.get("validated_evidence_ids", []))
    expected_delta = 0
    for change in revision.get("criteria_changes", []):
        criterion_id = change.get("criterion_id")
        if criterion_id not in criteria:
            errors.append(f"criteria_changes references unknown criterion {criterion_id}")
        if not set(change.get("source_signal_ids", [])).issubset(revision_signal_ids):
            errors.append(f"criteria change {criterion_id} references signal outside revision source_signal_ids")
        if not set(change.get("after_evidence_ids", [])).issubset(validated_evidence):
            errors.append(f"criteria change {criterion_id} uses evidence not accepted by A1")
        weight = weights.get(criterion_id, 0)
        before_points = weight if change.get("before_status") == "confirmed" else 0
        after_points = weight if change.get("after_status") == "confirmed" else 0
        expected_delta += after_points - before_points
    if prior.get("score") is not None and revised.get("score") is not None:
        actual_delta = float(revised["score"]) - float(prior["score"])
        if abs(actual_delta - expected_delta) > 1e-6:
            errors.append(f"score revision delta {actual_delta:g} does not equal criterion-change delta {expected_delta:g}")
    return errors


def package_errors(package: dict, criteria: set[str], weights: dict[str, int], scoring_config: dict) -> list[str]:
    errors = []
    signals = package.get("signals", [])
    for signal in signals:
        errors.extend(signal_errors(signal, criteria))
        for field in ["a2_record_id", "a1_candidate_id", "a1_handoff_id", "a1_candidate_snapshot_sha256", "audit_correlation_id", "synthetic"]:
            if signal.get(field) != package.get(field):
                errors.append(f"package {field} must match every signal")
    if package.get("original_scoring_sha256") != canonical_hash(package.get("original_scoring", {})):
        errors.append("original scoring hash mismatch")

    signal_ids = {signal.get("signal_id") for signal in signals}
    return_doc = package.get("requalification_return")
    revision = package.get("score_revision_reference")
    if return_doc is not None:
        errors.extend(return_errors(return_doc, criteria))
        return_signal_ids = {signal.get("signal_id") for signal in return_doc.get("signal_snapshots", [])}
        if return_signal_ids != signal_ids:
            errors.append("return signal IDs must equal package signal IDs")
    if revision is not None:
        errors.extend(revision_errors(revision, criteria, weights, scoring_config))
        if set(revision.get("source_signal_ids", [])) != signal_ids:
            errors.append("score revision source_signal_ids must equal package signal IDs")
        if return_doc is None or revision.get("source_requalification_return_id") != return_doc.get("return_id"):
            errors.append("score revision must reference the package requalification return")
        if return_doc is None or return_doc.get("status") != "accepted_by_a1":
            errors.append("score revision requires an accepted_by_a1 return")
    if any(signal.get("status") == "rejected" for signal in signals) and revision is not None:
        errors.append("rejected signals cannot produce a score revision reference")
    return errors


def validate_document(path: Path, kind: str, registry: Registry, schemas: dict[str, dict], criteria: set[str], weights: dict[str, int], scoring_config: dict) -> dict:
    document = load_json(path)
    errors = schema_errors(document, schemas[kind], registry)
    if kind == "signal":
        errors.extend(signal_errors(document, criteria))
    elif kind == "return":
        errors.extend(return_errors(document, criteria))
    elif kind == "revision":
        errors.extend(revision_errors(document, criteria, weights, scoring_config))
    elif kind == "package":
        errors.extend(package_errors(document, criteria, weights, scoring_config))
    return {"path": str(path), "kind": kind, "valid": not errors, "errors": errors}


def fixture_kind(filename: str) -> str:
    if "package" in filename or "rejected-signal-with-revision" in filename:
        return "package"
    if "return" in filename:
        return "return"
    if "revision" in filename or "score-" in filename or "score_" in filename:
        return "revision"
    if "producer" in filename or "component-total" in filename or "no-review" in filename:
        return "revision"
    return "signal"


def main() -> int:
    criteria, weights, scoring_config = configs()
    registry, schemas = registry_and_schemas()
    failures = []
    cases = []

    contract_text = CONTRACT_DOCUMENT.read_text(encoding="utf-8")
    review_text = REVIEW_DOCUMENT.read_text(encoding="utf-8")
    documentation_checks = {
        "contract_version": "**Current contract version:** `0.1.1`" in contract_text,
        "contract_approved": "APPROVED BY UNITALK OPERATIONS WITH 0.1.1 LIFECYCLE CLARIFICATION" in contract_text,
        "review_version": "**Version:** `0.1.0`" in review_text,
        "review_approved": "APPROVED BY UNITALK OPERATIONS FOR STEP 2D" in review_text,
        "recorded_decision": "**Decision:** `APPROVED AS DRAFTED`" in contract_text,
        "decisions_c1_to_c10": all(f"| C{number} |" in contract_text for number in range(1, 11)),
        "a2_score_prohibition": "must not calculate points, a replacement score or a replacement band" in contract_text,
        "a1_only_scoring": "A1 is the only permitted score-revision producer" in review_text,
        "no_integration_ceiling": "maximum state is `prepared`" in contract_text,
    }
    for check_name, passed in documentation_checks.items():
        if not passed:
            failures.append(f"documentation check failed: {check_name}")

    manifest = load_json(DEPENDENCY_MANIFEST)
    dependency_hashes = {}
    for dependency in manifest["dependencies"]:
        path = PROFILE_ROOT / dependency["pinned_path"]
        actual = sha256(path)
        dependency_hashes[dependency["name"]] = actual
        if actual != dependency["sha256"]:
            failures.append(f"dependency hash mismatch: {dependency['name']}")

    valid_kinds = {
        "valid-horse-owner-signal.json": "signal",
        "valid-farrier-signal.json": "signal",
        "valid-manual-prepared-return.json": "return",
        "valid-synthetic-requalification-package.json": "package",
        "valid-rejected-signal-package.json": "package",
    }
    for filename, kind in valid_kinds.items():
        result = validate_document(VALID_DIR / filename, kind, registry, schemas, criteria, weights, scoring_config)
        passed = result["valid"]
        cases.append({"fixture": filename, "expected": "valid", "actual": "valid" if result["valid"] else "invalid", "passed": passed, "errors": result["errors"]})
        if not passed:
            failures.append(f"valid fixture failed: {filename}")

    for filename, expected_error in EXPECTED_INVALID.items():
        kind = fixture_kind(filename)
        result = validate_document(INVALID_DIR / filename, kind, registry, schemas, criteria, weights, scoring_config)
        combined = "\n".join(result["errors"])
        passed = (not result["valid"]) and expected_error in combined
        cases.append({"fixture": filename, "expected": "invalid", "kind": kind, "expected_error": expected_error, "actual": "valid" if result["valid"] else "invalid", "passed": passed, "errors": result["errors"]})
        if not passed:
            failures.append(f"invalid fixture did not fail as expected: {filename}")

    result = {
        "step": "2C",
        "version": "0.1.1",
        "approval_state": "approved_with_0.1.1_lifecycle_clarification",
        "dependencies": {
            "count": len(dependency_hashes),
            "hashes": dependency_hashes,
            "criterion_count": len(criteria),
            "weighted_criterion_count": len(weights),
        },
        "schemas": {name: str(path) for name, path in SCHEMA_FILES.items()},
        "documentation_checks": documentation_checks,
        "summary": {
            "valid_expected": len(valid_kinds),
            "invalid_expected": len(EXPECTED_INVALID),
            "cases_total": len(cases),
            "cases_passed": sum(case["passed"] for case in cases),
            "cases_failed": sum(not case["passed"] for case in cases),
        },
        "cases": cases,
        "failures": failures,
        "pass": not failures,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
