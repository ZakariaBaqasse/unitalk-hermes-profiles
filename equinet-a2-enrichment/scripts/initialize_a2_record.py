#!/usr/bin/env python3
"""Deterministically initialise an Equinet A2 record from an approved A1 handoff."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import tempfile
from pathlib import Path

from validate_a1_to_a2_handoff import (
    A1_SCHEMA_PATH,
    DEFAULT_SCHEMA as HANDOFF_SCHEMA_PATH,
    cross_field_errors as handoff_cross_field_errors,
    schema_errors as handoff_schema_errors,
)
from validate_a2_enrichment_record import validate as validate_a2_record

PROFILE_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "1.0.0"
PROFILE_ID = "equinet-a2-enrichment"
INITIALISER_VERSION = "0.1.0"


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key is not allowed: {key}")
        result[key] = value
    return result


def reject_non_finite(value: str):
    raise ValueError(f"Non-finite JSON number is not allowed: {value}")


def load_json(path: Path) -> dict:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_non_finite,
    )


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def canonical_hash(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def canonical_file_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def system_actor(actor_id: str = "UNITALK-A2-INITIALISER", role: str = "A2 Deterministic Initialiser") -> dict:
    return {
        "actor_id": actor_id,
        "actor_role": role,
        "display_name": None,
        "profile_id": PROFILE_ID,
        "workflow_id": None,
    }


def validate_handoff(handoff: dict) -> list[str]:
    schema = load_json(HANDOFF_SCHEMA_PATH)
    a1_schema = load_json(A1_SCHEMA_PATH)
    errors = handoff_schema_errors(handoff, schema, a1_schema)
    errors.extend(handoff_cross_field_errors(handoff, a1_schema))
    if handoff.get("target_profile") != PROFILE_ID:
        errors.append("handoff target_profile must be equinet-a2-enrichment")
    if handoff.get("eligibility", {}).get("status") != "eligible":
        errors.append("handoff eligibility must be eligible")
    scope = handoff.get("operating_scope")
    state = handoff.get("delivery_state")
    if scope == "manual_no_integration_pilot":
        if state != "ready_for_delivery":
            errors.append("manual_no_integration_pilot initialisation requires ready_for_delivery")
    elif state != "accepted_by_a2":
        errors.append("synthetic or connected initialisation requires accepted_by_a2")
    return errors


def entity_id(record_suffix: str, entity_type: str) -> str:
    return f"A2-ENT-{record_suffix}_{entity_type.upper()}"


def build_subject(handoff: dict, record_suffix: str) -> dict:
    identity = handoff["candidate_snapshot"]["identity"]
    entities = []
    relationships = []

    if identity.get("person") is not None:
        entities.append({
            "entity_id": entity_id(record_suffix, "person"),
            "entity_type": "person",
            "source_identity_reference": "candidate_snapshot.identity.person",
            "display_name": identity["person"]["full_name"],
            "aliases": [],
            "match_status": "not_checked",
            "external_matches": [],
        })
    if identity.get("organisation") is not None:
        entities.append({
            "entity_id": entity_id(record_suffix, "organisation"),
            "entity_type": "organisation",
            "source_identity_reference": "candidate_snapshot.identity.organisation",
            "display_name": identity["organisation"]["name"],
            "aliases": [],
            "match_status": "not_checked",
            "external_matches": [],
        })
    # Candidate-level aliases and evidence do not prove entity-specific aliases
    # or a person-to-organisation relationship. Those remain unresolved until a
    # later evidence-backed entity-resolution revision.

    return {
        "identity_resolution_status": "resolved",
        "entities": entities,
        "relationships": relationships,
        "material_conflicts": [],
    }


def build_record(handoff: dict) -> dict:
    handoff_errors = validate_handoff(handoff)
    if handoff_errors:
        raise ValueError("Invalid A1-to-A2 handoff: " + " | ".join(handoff_errors))

    full_handoff_hash = canonical_hash(handoff)
    suffix = full_handoff_hash[:20].upper()
    revision_basis_hash = canonical_hash({
        "handoff_sha256": full_handoff_hash,
        "initialiser_version": INITIALISER_VERSION,
        "schema_version": SCHEMA_VERSION,
    })
    revision_suffix = revision_basis_hash[:20].upper()
    record_id = f"A2-INIT_{suffix}"
    revision_id = f"A2-REV-INIT_{revision_suffix}_001"
    run_id = f"A2-RUN-INIT_{revision_suffix}"
    candidate = handoff["candidate_snapshot"]
    receipt = handoff.get("a2_receipt")
    accepted_at = receipt["received_at"] if isinstance(receipt, dict) else handoff["created_at"]
    accepted_actor = system_actor(
        receipt["receiver_id"] if isinstance(receipt, dict) else "UNITALK-A2-MANUAL-INITIALISER",
        "A2 Handoff Receiver" if isinstance(receipt, dict) else "A2 Manual Initialiser",
    )
    runtime_actor = system_actor()
    audit_id = handoff["provenance"]["audit_correlation_id"]
    contains_personal = bool(candidate["data_governance"]["contains_personal_data"])

    record = {
        "record_metadata": {
            "schema_version": SCHEMA_VERSION,
            "record_kind": candidate["record_kind"],
            "a2_record_id": record_id,
            "record_revision_id": revision_id,
            "revision_number": 1,
            "supersedes_revision_id": None,
            "supersedes_a2_record_id": None,
            "run_id": run_id,
            "audit_correlation_id": audit_id,
            "created_at": accepted_at,
            "created_by": runtime_actor,
            "change_reason": "initialisation",
        },
        "source_handoff": {
            "handoff_schema_version": handoff["handoff_schema_version"],
            "handoff_id": handoff["handoff_id"],
            "idempotency_key": handoff["idempotency_key"],
            "operating_scope": handoff["operating_scope"],
            "eligibility_status": handoff["eligibility"]["status"],
            "accepted_at": accepted_at,
            "accepted_by": accepted_actor,
            "candidate_snapshot_sha256": handoff["snapshot_integrity"]["candidate_snapshot_sha256"],
            "handoff_snapshot": copy_json(handoff),
        },
        "subject": build_subject(handoff, suffix),
        "enrichment_scope": {
            "mode": handoff["requested_enrichment"]["mode"],
            "requested_field_keys": list(handoff["requested_enrichment"]["requested_fields"]),
            "field_catalogue_version": "not_configured",
            "source_register_version": None,
            "operating_scope": handoff["operating_scope"],
            "limits": {
                "max_records": 1,
                "max_source_calls": 0,
                "max_provider_calls": 0,
                "max_retries": 0,
                "max_concurrency": 1,
                "max_cost_usd": 0,
                "policy_version": None,
            },
            "initiated_by": runtime_actor,
        },
        "field_assessments": [],
        "evidence_registry": [],
        "data_quality": {
            "status": "unassessed",
            "method_version": None,
            "calculated_at": None,
            "required_field_keys": [],
            "missing_field_keys": [],
            "unverified_field_keys": [],
            "conflict_field_keys": [],
            "stale_field_keys": [],
            "invalid_field_keys": [],
            "limitations": ["Field Catalogue and minimum data package are not applied during initialisation."],
        },
        "duplicate_and_eligibility": {
            "checks": [],
            "a2_eligibility_status": "not_checked",
            "outreach_eligibility_status": "unavailable",
            "owner_routing_status": "needs_owner_review",
            "reasons": ["A2 duplicate, CRM eligibility and owner-routing checks have not run."],
            "evaluated_at": None,
            "method_version": None,
        },
        "requalification": {
            "signals": [],
            "returns": [],
            "score_revision_references": [],
        },
        "review": {
            "record_decision": "pending",
            "reviewer": None,
            "decided_at": None,
            "reason": None,
            "required_field_decisions_complete": False,
            "requested_changes": [],
        },
        "workflow": {
            "state": "initialised",
            "previous_state": None,
            "transitioned_at": accepted_at,
            "triggered_by": accepted_actor,
            "hold_reasons": [],
            "block_reasons": [],
            "failure": None,
        },
        "system_references": {
            "a1_candidate_id": candidate["candidate_id"],
            "a1_handoff_id": handoff["handoff_id"],
            "twenty_record_id": None,
            "hubspot_contact_id": None,
            "hubspot_company_id": None,
            "hubspot_deal_ids": None,
            "hubspot_proposed_patch_id": None,
            "hubspot_sync_id": None,
            "n8n_work_item_id": None,
            "n8n_execution_id": None,
            "provider_request_ids": None,
            "a3_handoff_id": None,
            "a14_handoff_id": None,
            "requalification_return_id": None,
            "a1_score_revision_id": None,
        },
        "governance": {
            "processing_purpose": "Initialise a controlled A2 enrichment record from an approved A1 handoff.",
            "contains_personal_data": contains_personal,
            "data_categories": ["professional_personal_data"] if contains_personal else ["business_information"],
            "source_register_version": None,
            "source_terms_review_status": "unavailable",
            "retention_policy_version": None,
            "approval_matrix_version": None,
            "consent_check_status": "unavailable",
            "outreach_authorized": False,
            "crm_write_authorized": False,
            "provider_use_authorized": False,
            "policy_limitations": [
                "No A2 source research, provider use, CRM write, outreach or downstream delivery is authorised during initialisation."
            ],
        },
        "audit_and_consumption": {
            "events": [{
                "event_id": f"A2-EVENT-INIT_{suffix}_001",
                "event_type": "canonical_record_initialised",
                "actor": runtime_actor,
                "timestamp": accepted_at,
                "input_references": [handoff["handoff_id"], full_handoff_hash],
                "output_references": [revision_id],
                "model": None,
                "tools": ["initialize_a2_record.py"],
                "usage": None,
                "external_action": None,
            }],
            "total_usage": {
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "api_calls": 0,
                "provider_calls": 0,
                "credits": 0,
                "cost_amount": 0,
                "currency": "USD",
                "cost_status": "known",
            },
            "errors": [],
        },
    }

    validation = validate_a2_record(record)
    if not validation["valid"]:
        raise ValueError("Initialised record failed canonical validation: " + " | ".join(validation["errors"]))
    return record


def copy_json(value: object) -> object:
    return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))


def write_idempotent(path: Path, record: dict) -> str:
    payload = canonical_file_bytes(record)
    if path.exists():
        existing = load_json(path)
        if existing == record:
            return "unchanged"
        raise FileExistsError(f"Refusing to overwrite different content at {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temporary_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary_path, path)
            return "created"
        except FileExistsError:
            existing = load_json(path)
            if existing == record:
                return "unchanged"
            raise FileExistsError(f"Refusing to overwrite different content at {path}")
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def reserve_idempotency(ledger_path: Path, handoff: dict, record: dict) -> str:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = ledger_path.with_name(f".{ledger_path.name}.lock")
    handoff_digest = canonical_hash(handoff)
    handoff_id = handoff["handoff_id"]
    idempotency_key = handoff["idempotency_key"]
    entry = {
        "handoff_sha256": handoff_digest,
        "a2_record_id": record["record_metadata"]["a2_record_id"],
        "record_revision_id": record["record_metadata"]["record_revision_id"],
    }
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        ledger = load_json(ledger_path) if ledger_path.exists() else {
            "version": INITIALISER_VERSION,
            "handoff_ids": {},
            "idempotency_keys": {},
        }
        for namespace, key in (("handoff_ids", handoff_id), ("idempotency_keys", idempotency_key)):
            existing = ledger[namespace].get(key)
            if existing is not None and existing != entry:
                raise ValueError(f"Idempotency collision for {namespace}.{key}")
        already_present = handoff_id in ledger["handoff_ids"] and idempotency_key in ledger["idempotency_keys"]
        if not already_present:
            ledger["handoff_ids"][handoff_id] = entry
            ledger["idempotency_keys"][idempotency_key] = entry
            temporary_path = None
            try:
                with tempfile.NamedTemporaryFile(dir=ledger_path.parent, prefix=f".{ledger_path.name}.", suffix=".tmp", delete=False) as handle:
                    temporary_path = Path(handle.name)
                    handle.write(canonical_file_bytes(ledger))
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary_path, ledger_path)
            finally:
                if temporary_path is not None:
                    temporary_path.unlink(missing_ok=True)
        return "existing" if already_present else "reserved"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handoff", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ledger", type=Path)
    args = parser.parse_args()

    try:
        handoff = load_json(args.handoff)
        record = build_record(handoff)
        if args.output.exists() and load_json(args.output) != record:
            raise FileExistsError(f"Refusing to overwrite different content at {args.output}")
        ledger_path = args.ledger or args.output.parent / ".a2-initialisation-ledger.json"
        ledger_status = reserve_idempotency(ledger_path, handoff, record)
        write_status = write_idempotent(args.output, record)
        result = {
            "valid": True,
            "initialiser_version": INITIALISER_VERSION,
            "write_status": write_status,
            "ledger_status": ledger_status,
            "a2_record_id": record["record_metadata"]["a2_record_id"],
            "record_revision_id": record["record_metadata"]["record_revision_id"],
            "handoff_id": handoff["handoff_id"],
            "handoff_sha256": canonical_hash(handoff),
            "record_sha256": canonical_hash(record),
            "external_actions": 0,
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({
            "valid": False,
            "initialiser_version": INITIALISER_VERSION,
            "error": str(exc),
            "external_actions": 0,
        }, indent=2, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
