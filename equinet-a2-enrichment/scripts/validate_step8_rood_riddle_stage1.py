#!/usr/bin/env python3
"""Validate Rood & Riddle stored-page profile outputs before canonical promotion."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evaluations/step8/pilot/A1-RR-PODIATRY-001"
OUTPUT = BASE / "stage1-validation.json"
EXPECTED_ACCEPTED = {"person.role_title", "organisation.disciplines"}
EXPECTED_GAPS = {
    "person.professional_status",
    "organisation.service_area",
    "person.business_email",
    "person.business_phone",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    analysis = load(BASE / "stage1-analysis.json")
    audit = load(BASE / "stage1-audit.json")
    batch = load(BASE / "observation-batch.json")
    validated = load(BASE / "validated-observations.json")
    usage = load(BASE / "profile-usage.json") if (BASE / "profile-usage.json").exists() else {}
    checks: dict[str, bool] = {}
    findings: list[str] = []

    checks["candidate"] = all(
        item.get("candidate_id") == "A1-RR-PODIATRY-001" for item in (analysis, audit, batch, validated)
    )
    valid_by_key={item[...y"]: item for item in validated.get("observations", [])}
    accepted = {key for key, item in valid_by_key.items() if item.get("action") == "accept_for_wave3_evidence_assessment"}
    gaps = {
        key
        for key, item in valid_by_key.items()
        if item.get("action") == "retain_state_only" and item.get("field_state") in {"unknown", "not_found", "unavailable"}
    }
    checks["required_direct_observations"] = EXPECTED_ACCEPTED.issubset(accepted)
    checks["required_gaps_explicit"] = EXPECTED_GAPS.issubset(gaps)
    checks["no_unexpected_contact_value"] = all(
        not (
            item.get("field_key") in {"person.business_email", "person.business_phone"}
            and item.get("normalised_value") not in {None, ""}
        )
        for item in validated.get("observations", [])
    )
    combined = json.dumps({"analysis": analysis, "batch": batch, "validated": validated}, ensure_ascii=False).lower()
    checks["contact_form_placeholder_excluded"] = "example@example.com" not in combined
    checks["zero_external_actions"] = (
        analysis.get("external_actions", 0) == 0
        and audit.get("external_actions") == 0
        and validated.get("external_actions") == 0
    )
    checks["no_external_runtime_calls"] = all(
        audit.get(key, 0) == 0
        for key in ["external_calls", "firecrawl_calls", "exa_calls", "apify_calls", "hubspot_calls", "twenty_calls", "n8n_calls", "outreach_actions", "crm_writes"]
    )
    checks["role_priority_is_reviewable"] = (
        analysis.get("target_role_priority_recommendation", {}).get("recommendation") == "primary"
        and analysis.get("target_role_priority_recommendation", {}).get("not_a_sourced_fact") is True
        and analysis.get("target_role_priority_recommendation", {}).get("human_review_required") is True
    )
    checks["minimum_package_incomplete"] = (
        analysis.get("minimum_package", {}).get("status") == "incomplete"
        and analysis.get("minimum_package", {}).get("recommended_record_decision") == "held"
    )

    receipt_hashes = True
    source_hashes = True
    for item in batch.get("observations", []):
        receipt = item.get("source_preflight")
        if not isinstance(receipt, dict):
            receipt_hashes = False
            continue
        receipt_hashes &= receipt.get("preflight_sha256") == canonical_hash({k: value for k, value in receipt.items() if k != "preflight_sha256"})
        output_reference = receipt.get("audit", {}).get("output_reference")
        if output_reference:
            path = ROOT / output_reference
            source_hashes &= path.exists() and sha(path) == receipt.get("source_content_sha256")
    checks["receipt_hashes"] = receipt_hashes
    checks["source_content_hashes"] = source_hashes

    declared_hashes = audit.get("source_file_hashes", {})
    audit_hashes = True
    for key, relative_path in audit.get("source_files", {}).items():
        path = ROOT / relative_path
        audit_hashes &= path.exists() and declared_hashes.get(key) == sha(path)
    checks["audit_file_hashes"] = bool(declared_hashes) and audit_hashes
    checks["execution_identity"] = (
        audit.get("entity", {}).get("profile") == "equinet-a2-enrichment"
        and audit.get("entity", {}).get("intended_model") == "deepseek-v4-flash"
        and audit.get("entity", {}).get("actual_model") is None
        and audit.get("execution_kind") == "deterministic_recovery"
        and analysis.get("model_execution", {}).get("status") == "blocked_before_model_call"
    )
    checks["usage_file_present"] = bool(usage)

    if not checks["required_direct_observations"]:
        findings.append(f"Missing accepted direct observations: {sorted(EXPECTED_ACCEPTED - accepted)}")
    if not checks["required_gaps_explicit"]:
        findings.append(f"Missing explicit gap states: {sorted(EXPECTED_GAPS - gaps)}")
    if not checks["contact_form_placeholder_excluded"]:
        findings.append("The form placeholder example@example.com was retained.")
    if not checks["minimum_package_incomplete"]:
        findings.append("The analysis must classify the package as incomplete with a held recommendation.")

    result = {
        "record_type": "step8_rood_riddle_stage1_validation",
        "status": "accepted_for_canonical_review_build" if all(checks.values()) else "changes_required",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "accepted_field_keys": sorted(accepted),
        "gap_field_keys": sorted(gaps),
        "required_corrections": findings,
        "canonical_revision_authorized": all(checks.values()),
        "external_actions": 0,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
