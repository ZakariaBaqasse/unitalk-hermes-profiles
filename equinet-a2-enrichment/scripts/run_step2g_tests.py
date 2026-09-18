#!/usr/bin/env python3
"""Run Step 2G deterministic handoff-to-record initialisation tests."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROFILE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from initialize_a2_record import build_record, canonical_hash, reserve_idempotency, write_idempotent  # noqa: E402
from validate_a2_enrichment_record import validate as validate_a2_record  # noqa: E402

ROOT = PROFILE_ROOT / "evaluations" / "step2g"
FIXTURES = ROOT / "fixtures"
MANIFEST_PATH = FIXTURES / "initialisation-manifest.json"
OUTPUT = ROOT / "technical-validation.json"
PACKAGE_MANIFEST = ROOT / "step2g-package-manifest.json"
INITIALISER = SCRIPTS / "initialize_a2_record.py"
SCHEMA_PATH = PROFILE_ROOT / "foundations" / "contracts" / "canonical" / "a2-enrichment-record.schema.json"
STEP2F_VALIDATION = PROFILE_ROOT / "evaluations" / "step2f" / "technical-validation.json"
STEP2E_CORRECTION = PROFILE_ROOT / "evaluations" / "step2e" / "step2g-initialisation-compatibility-correction.json"
STEP2F_CORRECTION = PROFILE_ROOT / "evaluations" / "step2f" / "step2g-compatibility-correction.json"
CONTRACT_PATH = PROFILE_ROOT / "foundations" / "A2-HANDOFF-TO-RECORD-INITIALISATION-CONTRACT.md"
REVIEW_PATH = ROOT / "A2-HANDOFF-TO-RECORD-INITIALISATION-REVIEW.md"
ACCEPTANCE_RECORD = ROOT / "acceptance-record.json"
STEP2I_APPROVAL = PROFILE_ROOT / "evaluations" / "step2i" / "approval-record.json"
LEGACY_PACKAGE_MANIFEST = PROFILE_ROOT / "evaluations" / "step2i" / "pre-promotion-evidence" / "step2g-package-manifest.json"

REQUIRED_VALID_CASES = {"horse-owner", "farrier", "horse-owner-targeted"}
REQUIRED_INVALID_CASES = {
    "extra-handoff-property", "candidate-hash-mismatch", "wrong-target-profile",
    "synthetic-not-accepted", "handoff-not-eligible", "recommendation-not-pass-to-a2",
    "provider-authority-at-initialisation", "synthetic-manual-scope",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output_invariants(handoff: dict, record: dict, expected: dict) -> list[str]:
    errors: list[str] = []
    candidate = handoff["candidate_snapshot"]
    if record["source_handoff"]["handoff_snapshot"] != handoff:
        errors.append("source handoff snapshot is not lossless")
    if record["source_handoff"]["handoff_snapshot"]["candidate_snapshot"] != candidate:
        errors.append("A1 candidate snapshot is not lossless")
    if any(entity["aliases"] for entity in record["subject"]["entities"]):
        errors.append("ambiguous candidate aliases were assigned to an entity")
    if record["record_metadata"]["revision_number"] != 1 or record["record_metadata"]["supersedes_revision_id"] is not None:
        errors.append("initial revision lineage is invalid")
    if record["workflow"]["state"] != "initialised" or record["workflow"]["previous_state"] is not None:
        errors.append("initial workflow state is invalid")
    if record["field_assessments"] or record["evidence_registry"]:
        errors.append("A2 field/evidence containers are not empty at initialisation")
    if any(record["requalification"].values()):
        errors.append("requalification containers are not empty at initialisation")
    if record["review"]["record_decision"] != "pending" or record["review"]["reviewer"] is not None:
        errors.append("initial review must remain pending")
    connector_fields = [
        "twenty_record_id", "hubspot_contact_id", "hubspot_company_id", "hubspot_deal_ids",
        "hubspot_proposed_patch_id", "hubspot_sync_id", "n8n_work_item_id", "n8n_execution_id",
        "provider_request_ids", "a3_handoff_id", "a14_handoff_id", "requalification_return_id", "a1_score_revision_id",
    ]
    if any(record["system_references"][field] is not None for field in connector_fields):
        errors.append("initial record contains an external connector reference")
    if record["governance"]["outreach_authorized"] or record["governance"]["crm_write_authorized"] or record["governance"]["provider_use_authorized"]:
        errors.append("initial record grants an external action permission")
    if any(event["external_action"] is not None for event in record["audit_and_consumption"]["events"]):
        errors.append("initial record claims an external action")
    if record["audit_and_consumption"]["total_usage"]["api_calls"] != 0 or record["audit_and_consumption"]["total_usage"]["provider_calls"] != 0:
        errors.append("initialisation consumption must record zero external calls")
    actual = {
        "segment": candidate["segment"],
        "entity_count": len(record["subject"]["entities"]),
        "relationship_count": len(record["subject"]["relationships"]),
        "mode": record["enrichment_scope"]["mode"],
        "requested_field_keys": record["enrichment_scope"]["requested_field_keys"],
    }
    for key, expected_value in expected.items():
        if actual[key] != expected_value:
            errors.append(f"expected {key}={expected_value!r}, got {actual[key]!r}")
    expected_suffix = canonical_hash(handoff)[:20].upper()
    expected_revision_suffix = canonical_hash({
        "handoff_sha256": canonical_hash(handoff),
        "initialiser_version": "0.1.0",
        "schema_version": "1.0.0",
    })[:20].upper()
    if record["record_metadata"]["a2_record_id"] != f"A2-INIT_{expected_suffix}":
        errors.append("a2_record_id is not deterministically derived from the handoff")
    if record["record_metadata"]["record_revision_id"] != f"A2-REV-INIT_{expected_revision_suffix}_001":
        errors.append("record_revision_id is not deterministically derived from the handoff and initialiser contract")
    return errors


def main() -> int:
    manifest = load(MANIFEST_PATH)
    failures: list[str] = []
    cases = []
    valid_records = []

    valid_case_names = {case["name"] for case in manifest["cases"] if case["kind"] == "valid"}
    invalid_case_names = {case["name"] for case in manifest["cases"] if case["kind"] == "invalid"}
    if manifest.get("valid_cases") != len(valid_case_names) or valid_case_names != REQUIRED_VALID_CASES:
        failures.append("valid initialisation case matrix is incomplete or inconsistent")
    if manifest.get("invalid_cases") != len(invalid_case_names) or invalid_case_names != REQUIRED_INVALID_CASES:
        failures.append("invalid initialisation case matrix is incomplete or inconsistent")

    for case in manifest["cases"]:
        handoff_path = FIXTURES / case["handoff"]
        if sha256(handoff_path) != case["handoff_file_sha256"]:
            failures.append(f"handoff fixture hash mismatch: {case['name']}")
        handoff = load(handoff_path)
        if case["kind"] == "valid":
            first = None
            record_path = FIXTURES / case["record"]
            if sha256(record_path) != case["record_file_sha256"]:
                failures.append(f"record fixture hash mismatch: {case['name']}")
            expected_record = load(record_path)
            try:
                first = build_record(handoff)
                second = build_record(handoff)
                validation = validate_a2_record(first)
                errors = output_invariants(handoff, first, case["expected"])
                if first != second:
                    errors.append("repeat initialisation is not byte-equivalent")
                if first != expected_record:
                    errors.append("generated record differs from pinned expected fixture")
                errors.extend(validation["errors"])
                passed = not errors
            except Exception as exc:
                errors = [str(exc)]
                passed = False
            valid_records.append(first)
        else:
            try:
                build_record(handoff)
                errors = []
                passed = False
            except Exception as exc:
                errors = [str(exc)]
                passed = case["expected_error"] in str(exc)
        cases.append({
            "name": case["name"],
            "kind": case["kind"],
            "passed": passed,
            "expected_error": case.get("expected_error"),
            "errors": errors,
        })
        if not passed:
            failures.append(f"case failed: {case['name']}")

    deterministic_controls = {}
    valid_outputs = [record for record in valid_records if record is not None]
    ids = [record["record_metadata"]["a2_record_id"] for record in valid_outputs]
    deterministic_controls["distinct_handoffs_have_distinct_record_ids"] = len(ids) == len(set(ids))

    owner_case = next(case for case in manifest["cases"] if case["name"] == "horse-owner")
    owner_handoff = load(FIXTURES / owner_case["handoff"])
    owner_record = build_record(owner_handoff)
    with tempfile.TemporaryDirectory(prefix="a2-step2g-") as tmp:
        tmp_path = Path(tmp)
        output_path = tmp_path / "record.json"
        created = write_idempotent(output_path, owner_record)
        unchanged = write_idempotent(output_path, owner_record)
        collision_blocked = False
        altered = json.loads(json.dumps(owner_record))
        altered["record_metadata"]["run_id"] = "A2-RUN-DIFFERENT"
        try:
            write_idempotent(output_path, altered)
        except FileExistsError:
            collision_blocked = True
        deterministic_controls["first_local_write_created"] = created == "created"
        deterministic_controls["identical_retry_unchanged"] = unchanged == "unchanged"
        deterministic_controls["different_content_collision_blocked"] = collision_blocked

        race_path = tmp_path / "race-record.json"
        race_a = json.loads(json.dumps(owner_record))
        race_b = json.loads(json.dumps(owner_record))
        race_b["record_metadata"]["run_id"] = "A2-RUN-RACE-B"

        def race_write(payload: dict) -> str:
            try:
                return write_idempotent(race_path, payload)
            except FileExistsError:
                return "collision"

        with ThreadPoolExecutor(max_workers=2) as pool:
            race_results = list(pool.map(race_write, [race_a, race_b]))
        deterministic_controls["concurrent_different_writes_single_winner"] = sorted(race_results) == ["collision", "created"]

        ledger_path = tmp_path / "idempotency-ledger.json"
        ledger_first = reserve_idempotency(ledger_path, owner_handoff, owner_record)
        ledger_repeat = reserve_idempotency(ledger_path, owner_handoff, owner_record)
        changed_handoff = json.loads(json.dumps(owner_handoff))
        changed_handoff["requested_enrichment"]["request_reason"] = "Changed payload with reused identifiers."
        changed_record = build_record(changed_handoff)
        ledger_collision = False
        try:
            reserve_idempotency(ledger_path, changed_handoff, changed_record)
        except ValueError:
            ledger_collision = True
        deterministic_controls["idempotency_ledger_first_reserved"] = ledger_first == "reserved"
        deterministic_controls["idempotency_ledger_repeat_existing"] = ledger_repeat == "existing"
        deterministic_controls["idempotency_ledger_changed_payload_blocked"] = ledger_collision

        concurrent_ledger_path = tmp_path / "concurrent-idempotency-ledger.json"

        def reserve_race(payload: tuple[dict, dict]) -> str:
            try:
                return reserve_idempotency(concurrent_ledger_path, payload[0], payload[1])
            except ValueError:
                return "collision"

        with ThreadPoolExecutor(max_workers=2) as pool:
            ledger_race_results = list(pool.map(reserve_race, [(owner_handoff, owner_record), (changed_handoff, changed_record)]))
        deterministic_controls["concurrent_idempotency_reuse_single_winner"] = sorted(ledger_race_results) == ["collision", "reserved"]

        cli_output = tmp_path / "cli-record.json"
        cli_ledger = tmp_path / "cli-ledger.json"
        cli_first = subprocess.run(
            [sys.executable, str(INITIALISER), str(FIXTURES / owner_case["handoff"]), "--output", str(cli_output), "--ledger", str(cli_ledger)],
            cwd=PROFILE_ROOT,
            capture_output=True,
            text=True,
        )
        cli_second = subprocess.run(
            [sys.executable, str(INITIALISER), str(FIXTURES / owner_case["handoff"]), "--output", str(cli_output), "--ledger", str(cli_ledger)],
            cwd=PROFILE_ROOT,
            capture_output=True,
            text=True,
        )
        deterministic_controls["cli_first_write_created"] = cli_first.returncode == 0 and json.loads(cli_first.stdout)["write_status"] == "created"
        deterministic_controls["cli_retry_unchanged"] = cli_second.returncode == 0 and json.loads(cli_second.stdout)["write_status"] == "unchanged"

        invalid_cli_results = []
        for index, invalid_case in enumerate(case for case in manifest["cases"] if case["kind"] == "invalid"):
            invalid_output = tmp_path / f"invalid-record-{index}.json"
            cli_invalid = subprocess.run(
                [sys.executable, str(INITIALISER), str(FIXTURES / invalid_case["handoff"]), "--output", str(invalid_output), "--ledger", str(tmp_path / f"invalid-ledger-{index}.json")],
                cwd=PROFILE_ROOT,
                capture_output=True,
                text=True,
            )
            invalid_cli_results.append(cli_invalid.returncode == 1 and not invalid_output.exists())
        deterministic_controls["all_invalid_handoffs_rejected_without_output"] = all(invalid_cli_results) and len(invalid_cli_results) == manifest["invalid_cases"]

        duplicate_input = tmp_path / "duplicate-key.json"
        duplicate_input.write_text('{"handoff_id":"ONE","handoff_id":"TWO"}', encoding="utf-8")
        duplicate_output = tmp_path / "duplicate-output.json"
        duplicate_cli = subprocess.run(
            [sys.executable, str(INITIALISER), str(duplicate_input), "--output", str(duplicate_output), "--ledger", str(tmp_path / "duplicate-ledger.json")],
            cwd=PROFILE_ROOT, capture_output=True, text=True,
        )
        deterministic_controls["duplicate_json_keys_rejected_without_output"] = duplicate_cli.returncode == 1 and not duplicate_output.exists()

        nan_input = tmp_path / "nan-input.json"
        nan_input.write_text('{"probe":NaN}', encoding="utf-8")
        nan_output = tmp_path / "nan-output.json"
        nan_cli = subprocess.run(
            [sys.executable, str(INITIALISER), str(nan_input), "--output", str(nan_output), "--ledger", str(tmp_path / "nan-ledger.json")],
            cwd=PROFILE_ROOT, capture_output=True, text=True,
        )
        deterministic_controls["non_finite_json_rejected_without_output"] = nan_cli.returncode == 1 and not nan_output.exists()

        canonical_input_a = tmp_path / "canonical-a.json"
        canonical_input_b = tmp_path / "canonical-b.json"
        canonical_input_a.write_text(json.dumps(owner_handoff, ensure_ascii=False), encoding="utf-8")
        canonical_input_b.write_text(json.dumps(dict(reversed(list(owner_handoff.items()))), ensure_ascii=False), encoding="utf-8")
        canonical_output_a = tmp_path / "canonical-a-output.json"
        canonical_output_b = tmp_path / "canonical-b-output.json"
        canonical_cli_a = subprocess.run(
            [sys.executable, str(INITIALISER), str(canonical_input_a), "--output", str(canonical_output_a), "--ledger", str(tmp_path / "canonical-a-ledger.json")],
            cwd=PROFILE_ROOT, capture_output=True, text=True,
        )
        canonical_cli_b = subprocess.run(
            [sys.executable, str(INITIALISER), str(canonical_input_b), "--output", str(canonical_output_b), "--ledger", str(tmp_path / "canonical-b-ledger.json")],
            cwd=PROFILE_ROOT, capture_output=True, text=True,
        )
        deterministic_controls["key_order_independent_output_bytes"] = (
            canonical_cli_a.returncode == 0
            and canonical_cli_b.returncode == 0
            and canonical_output_a.read_bytes() == canonical_output_b.read_bytes()
        )

    for name, passed in deterministic_controls.items():
        if not passed:
            failures.append(f"deterministic control failed: {name}")

    contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
    review_text = REVIEW_PATH.read_text(encoding="utf-8")
    documentation_checks = {
        "contract_version": "**Initialiser version:** `0.1.0`" in contract_text,
        "contract_approved": "**Step:** `2G — Handoff-to-Record Initialisation`" in contract_text and "APPROVED BY UNITALK OPERATIONS FOR STEP 2H" in contract_text,
        "review_version": "**Version:** `0.1.0`" in review_text,
        "decisions_g1_to_g11": all(f"| G{number} |" in review_text for number in range(1, 12)),
        "manual_limitation": "manual_no_integration" in contract_text and "approved real" in contract_text,
        "step2h_boundary": "Step 2H" in contract_text,
    }
    for name, passed in documentation_checks.items():
        if not passed:
            failures.append(f"documentation check failed: {name}")

    package_paths = [
        INITIALISER,
        SCRIPTS / "build_step2g_fixtures.py",
        SCRIPTS / "run_step2g_tests.py",
        SCHEMA_PATH,
        MANIFEST_PATH,
        STEP2F_VALIDATION,
        STEP2E_CORRECTION,
        STEP2F_CORRECTION,
        CONTRACT_PATH,
        REVIEW_PATH,
        ROOT / "INDEPENDENT-ADVERSARIAL-REVIEW-RESOLUTION.md",
    ]
    for case in manifest["cases"]:
        package_paths.append(FIXTURES / case["handoff"])
        if case.get("record"):
            package_paths.append(FIXTURES / case["record"])
    package_paths = sorted(set(package_paths))
    package_manifest = {
        "manifest_id": "equinet-a2-step2g-initialisation-package",
        "version": "0.1.0",
        "status": "approved_by_unitalk_for_step_2h",
        "files": [
            {"path": str(path.relative_to(PROFILE_ROOT)), "sha256": sha256(path)}
            for path in package_paths
        ],
    }
    PACKAGE_MANIFEST.write_text(json.dumps(package_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    acceptance = load(ACCEPTANCE_RECORD)
    step2i_approval = load(STEP2I_APPROVAL)
    acceptance_checks = {
        "decision": acceptance.get("decision") == "approved_as_drafted",
        "initialiser_version": acceptance.get("initialiser_version") == "0.1.0",
        "historical_package_manifest_hash": acceptance.get("package_manifest_sha256") == sha256(LEGACY_PACKAGE_MANIFEST),
        "next_gate": acceptance.get("next_gate") == "Step 2H — Review-View Specification",
        "step2i_promotion_approved": step2i_approval.get("decision") == "approved" and step2i_approval.get("promotion_authorized") is True,
    }
    for name, passed in acceptance_checks.items():
        if not passed:
            failures.append(f"acceptance check failed: {name}")

    result = {
        "step": "2G",
        "initialiser_version": "0.1.0",
        "approval_state": "promoted_in_step_2i",
        "summary": {
            "valid_expected": sum(case["kind"] == "valid" for case in manifest["cases"]),
            "invalid_expected": sum(case["kind"] == "invalid" for case in manifest["cases"]),
            "cases_total": len(cases),
            "cases_passed": sum(case["passed"] for case in cases),
            "cases_failed": sum(not case["passed"] for case in cases),
            "deterministic_controls": len(deterministic_controls),
            "deterministic_controls_passed": sum(deterministic_controls.values()),
        },
        "coverage": {
            "segments": sorted({load(FIXTURES / case["handoff"])["candidate_snapshot"]["segment"] for case in manifest["cases"] if case["kind"] == "valid"}),
            "manual_no_integration_positive": "pending_real_approved_handoff",
            "all_outputs_initialised": all(record and record["workflow"]["state"] == "initialised" for record in valid_outputs),
            "all_outputs_zero_external_actions": all(
                not any(event["external_action"] for event in record["audit_and_consumption"]["events"])
                for record in valid_outputs
            ),
            "independent_post_fix_review": "pass",
        },
        "deterministic_controls": deterministic_controls,
        "documentation_checks": documentation_checks,
        "acceptance_checks": acceptance_checks,
        "package_manifest": {"path": str(PACKAGE_MANIFEST), "sha256": sha256(PACKAGE_MANIFEST), "file_count": len(package_paths)},
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
