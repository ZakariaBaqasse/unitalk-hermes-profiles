#!/usr/bin/env python3
"""Build Step 2G deterministic initialisation fixtures."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROFILE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from initialize_a2_record import build_record, canonical_hash  # noqa: E402

CONTRACTS = PROFILE_ROOT / "foundations" / "contracts"
ROOT = PROFILE_ROOT / "evaluations" / "step2g"
FIXTURES = ROOT / "fixtures"
INPUTS = FIXTURES / "inputs"
VALID = FIXTURES / "valid"
INVALID = FIXTURES / "invalid"
MANIFEST = FIXTURES / "initialisation-manifest.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_candidate_hash(candidate: dict) -> str:
    return hashlib.sha256(json.dumps(candidate, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def main() -> None:
    owner = load(CONTRACTS / "examples" / "valid" / "valid-horse-owner-handoff.json")
    farrier = load(CONTRACTS / "examples" / "valid" / "valid-farrier-handoff.json")
    targeted = copy.deepcopy(owner)
    targeted.update({
        "handoff_id": "A1A2-TEST_OWNER_TARGETED_001",
        "idempotency_key": "A1A2-IDEMP-TEST_OWNER_TARGETED_001",
    })
    targeted["candidate_snapshot"]["system_references"]["a2_handoff_id"] = targeted["handoff_id"]
    targeted["requested_enrichment"] = {
        "mode": "targeted_fields",
        "requested_fields": ["organisation.horse_count"],
        "request_reason": "Synthetic targeted initialisation fixture.",
    }
    targeted["a2_receipt"]["handoff_id"] = targeted["handoff_id"]
    targeted["snapshot_integrity"]["candidate_snapshot_sha256"] = canonical_candidate_hash(targeted["candidate_snapshot"])
    targeted["a2_receipt"]["candidate_snapshot_sha256"] = targeted["snapshot_integrity"]["candidate_snapshot_sha256"]

    valid_inputs = {
        "horse-owner": owner,
        "farrier": farrier,
        "horse-owner-targeted": targeted,
    }
    cases = []
    for name, handoff in valid_inputs.items():
        input_path = INPUTS / f"{name}-handoff.json"
        output_path = VALID / f"{name}-initial-record.json"
        write(input_path, handoff)
        record = build_record(handoff)
        write(output_path, record)
        cases.append({
            "name": name,
            "kind": "valid",
            "handoff": str(input_path.relative_to(FIXTURES)),
            "record": str(output_path.relative_to(FIXTURES)),
            "handoff_sha256": canonical_hash(handoff),
            "record_sha256": canonical_hash(record),
            "expected": {
                "segment": handoff["candidate_snapshot"]["segment"],
                "entity_count": (1 if handoff["candidate_snapshot"]["identity"].get("person") else 0) + (1 if handoff["candidate_snapshot"]["identity"].get("organisation") else 0),
                "relationship_count": 0,
                "mode": handoff["requested_enrichment"]["mode"],
                "requested_field_keys": handoff["requested_enrichment"]["requested_fields"],
            },
        })

    invalids = {}

    item = copy.deepcopy(owner)
    item["unexpected"] = True
    invalids["extra-handoff-property"] = (item, "Additional properties are not allowed")

    item = copy.deepcopy(owner)
    item["snapshot_integrity"]["candidate_snapshot_sha256"] = "0" * 64
    invalids["candidate-hash-mismatch"] = (item, "snapshot hash mismatch")

    item = copy.deepcopy(owner)
    item["target_profile"] = "equinet-a3-outreach-drafter"
    invalids["wrong-target-profile"] = (item, "equinet-a2-enrichment")

    item = copy.deepcopy(owner)
    item["delivery_state"] = "prepared"
    item["a2_receipt"] = None
    item["delivery"] = {"external_event_reference": None, "attempt_count": 0, "last_attempt_at": None, "failure_reason": None}
    invalids["synthetic-not-accepted"] = (item, "requires accepted_by_a2")

    item = copy.deepcopy(owner)
    item["eligibility"]["status"] = "hold"
    invalids["handoff-not-eligible"] = (item, "handoff eligibility must be eligible")

    item = copy.deepcopy(owner)
    item["candidate_snapshot"]["recommendation"]["next_action"] = "hold"
    changed_hash = canonical_candidate_hash(item["candidate_snapshot"])
    item["snapshot_integrity"]["candidate_snapshot_sha256"] = changed_hash
    item["a2_receipt"]["candidate_snapshot_sha256"] = changed_hash
    invalids["recommendation-not-pass-to-a2"] = (item, "candidate recommendation.next_action must be pass_to_a2")

    item = copy.deepcopy(owner)
    item["constraints"]["paid_provider_authorized"] = True
    invalids["provider-authority-at-initialisation"] = (item, "scope_permissions gate must be fail")

    item = copy.deepcopy(owner)
    item["operating_scope"] = "manual_no_integration_pilot"
    item["delivery_state"] = "ready_for_delivery"
    item["a2_receipt"] = None
    item["delivery"] = {"external_event_reference": None, "attempt_count": 0, "last_attempt_at": None, "failure_reason": None}
    invalids["synthetic-manual-scope"] = (item, "non-synthetic operating scopes require a production A1 candidate")

    for name, (handoff, expected_error) in invalids.items():
        path = INVALID / f"{name}.json"
        write(path, handoff)
        cases.append({
            "name": name,
            "kind": "invalid",
            "handoff": str(path.relative_to(FIXTURES)),
            "expected_error": expected_error,
        })

    for case in cases:
        handoff_path = FIXTURES / case["handoff"]
        case["handoff_file_sha256"] = file_hash(handoff_path)
        if case.get("record"):
            case["record_file_sha256"] = file_hash(FIXTURES / case["record"])

    write(MANIFEST, {
        "step": "2G",
        "initialiser_version": "0.1.0",
        "valid_cases": 3,
        "invalid_cases": len(invalids),
        "cases": cases,
    })
    print(json.dumps({
        "valid_cases": 3,
        "invalid_cases": len(invalids),
        "total_cases": len(cases),
        "manifest": str(MANIFEST),
    }, indent=2))


if __name__ == "__main__":
    main()
