#!/usr/bin/env python3
"""Build deterministic synthetic fixtures for the Equinet A1-to-A2 handoff contract."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_EXAMPLES = Path("/opt/data/profiles/equinet-a1-icp-discovery/skills/a1-prospect-data-contract/references/examples")
OUTPUT_ROOT = PROFILE_ROOT / "foundations" / "contracts" / "examples"
VALID_DIR = OUTPUT_ROOT / "valid"
INVALID_DIR = OUTPUT_ROOT / "invalid"

APPROVAL_TIME = "2026-08-16T15:30:00Z"
TRIGGER_TIME = "2026-08-16T15:30:05Z"
CREATED_TIME = "2026-08-16T15:30:10Z"
RECEIVED_TIME = "2026-08-16T15:30:20Z"
REVIEWER = {
    "actor_id": "UNITALK-A1-REVIEWER-TEST",
    "actor_role": "A1 Business Reviewer",
    "display_name": "Synthetic A1 Reviewer",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def approve_candidate(candidate: dict, handoff_id: str) -> dict:
    candidate = copy.deepcopy(candidate)
    candidate["updated_at"] = APPROVAL_TIME
    candidate["recommendation"]["next_action"] = "pass_to_a2"
    candidate["recommendation"]["notes"] = "Synthetic candidate approved for A2 handoff contract testing."
    candidate["workflow"] = {
        "stage": "approved_for_a2",
        "review_decision": "approved",
        "reviewer": copy.deepcopy(REVIEWER),
        "decision_at": APPROVAL_TIME,
        "rejection_reason": None,
    }
    candidate["system_references"]["a2_handoff_id"] = handoff_id
    return candidate


def gate(gate_id: str, status: str, reason: str, source_path: str | None) -> dict:
    return {
        "gate_id": gate_id,
        "status": status,
        "reason": reason,
        "source_path": source_path,
    }


def eligibility_gates() -> list[dict]:
    return [
        gate("candidate_schema", "pass", "Pinned A1 schema and cross-field validation passed.", "candidate_snapshot"),
        gate("human_approval", "pass", "A1 human approval is recorded and consistent.", "candidate_snapshot.workflow"),
        gate("recommendation", "pass", "A1 recommends pass_to_a2.", "candidate_snapshot.recommendation.next_action"),
        gate("exclusion", "pass", "Candidate is eligible and not excluded.", "candidate_snapshot.qualification.exclusion_status"),
        gate("minimum_data", "pass", "A1 minimum data status passed.", "candidate_snapshot.qualification.minimum_data_status"),
        gate("identity_quality", "pass", "A1 data quality is validated.", "candidate_snapshot.data_quality.validation_status"),
        gate("duplicate_batch", "pass", "No current-batch duplicate was found.", "candidate_snapshot.duplicate_check.batch"),
        gate("duplicate_exclusion_file", "unavailable", "No exclusion file was supplied for the synthetic fixture.", "candidate_snapshot.duplicate_check.provided_exclusion_file"),
        gate("source_policy", "pass", "No blocked source supports the candidate.", "candidate_snapshot.source_evidence"),
        gate("scoring_state", "pass", "A1 deterministic scoring completed.", "candidate_snapshot.scoring.status"),
        gate("audit_identity", "pass", "A1 audit correlation ID is present.", "candidate_snapshot.provenance.audit_correlation_id"),
        gate("scope_permissions", "pass", "Synthetic scope prohibits every external action.", "constraints"),
        gate("hubspot_duplicate", "unavailable", "HubSpot is not connected for the synthetic fixture.", "candidate_snapshot.duplicate_check.hubspot"),
        gate("hubspot_eligibility", "unavailable", "Authoritative HubSpot eligibility checks are unavailable and not required for synthetic contract validation.", None),
    ]


def build_envelope(candidate: dict, handoff_id: str, suffix: str) -> dict:
    snapshot_hash = canonical_hash(candidate)
    return {
        "handoff_schema_version": "1.0.1",
        "handoff_id": handoff_id,
        "idempotency_key": f"A1A2-IDEMP-{suffix}",
        "created_at": CREATED_TIME,
        "source_profile": "equinet-a1-icp-discovery",
        "target_profile": "equinet-a2-enrichment",
        "operating_scope": "synthetic_test",
        "delivery_state": "accepted_by_a2",
        "trigger_event": {
            "event_type": "a1_candidate_approved_for_a2",
            "event_id": f"EVENT-{suffix}",
            "occurred_at": TRIGGER_TIME,
            "source_layer": "manual_review_package",
            "source_record_id": f"REVIEW-{suffix}",
        },
        "approval_event": {
            "decision": "approved_for_enrichment",
            "scope": "a2_enrichment",
            "reviewer": copy.deepcopy(REVIEWER),
            "decision_at": APPROVAL_TIME,
            "source_layer": "manual_review_package",
            "source_record_id": f"REVIEW-{suffix}",
        },
        "eligibility": {
            "status": "eligible",
            "evaluated_at": CREATED_TIME,
            "method_version": "a1-a2-eligibility-1.0.1",
            "gates": eligibility_gates(),
            "reasons": [
                "Core A1 approval and quality gates passed.",
                "Unavailable HubSpot checks are permitted only for synthetic contract validation."
            ],
        },
        "requested_enrichment": {
            "mode": "default_minimum_package",
            "requested_fields": [],
            "request_reason": "Synthetic end-to-end handoff validation."
        },
        "candidate_snapshot": candidate,
        "snapshot_integrity": {
            "algorithm": "sha256",
            "canonicalization": "json_sorted_utf8_v1",
            "candidate_snapshot_sha256": snapshot_hash,
        },
        "integration_availability": {
            "hubspot_read": "unavailable",
            "staging": "unavailable",
            "workflow": "unavailable",
            "enrichment_provider": "unavailable",
            "email_verification": "unavailable",
            "phone_verification": "unavailable",
        },
        "constraints": {
            "a1_score_mutation_authorized": False,
            "human_review_required": True,
            "outreach_authorized": False,
            "crm_write_authorized": False,
            "downstream_delivery_authorized": False,
            "paid_provider_authorized": False,
            "public_information_creates_consent": False,
            "external_action_approval_reference": None,
        },
        "delivery": {
            "external_event_reference": f"synthetic://a1-a2/{suffix}",
            "attempt_count": 1,
            "last_attempt_at": RECEIVED_TIME,
            "failure_reason": None,
        },
        "a2_receipt": {
            "status": "accepted",
            "receiver_profile": "equinet-a2-enrichment",
            "receiver_id": "A2-SYNTHETIC-VALIDATOR",
            "received_at": RECEIVED_TIME,
            "handoff_id": handoff_id,
            "candidate_snapshot_sha256": snapshot_hash,
            "rejection_reasons": [],
        },
        "provenance": {
            "created_by": "unitalk-a1-a2-handoff-builder",
            "initiated_by": "unitalk-step1c-test",
            "audit_correlation_id": candidate["provenance"]["audit_correlation_id"],
            "synthetic": True,
            "tools_used": ["deterministic-fixture-builder"],
        },
    }


def refresh_integrity(envelope: dict) -> None:
    digest = canonical_hash(envelope["candidate_snapshot"])
    envelope["snapshot_integrity"]["candidate_snapshot_sha256"] = digest
    if isinstance(envelope.get("a2_receipt"), dict):
        envelope["a2_receipt"]["candidate_snapshot_sha256"] = digest


def main() -> None:
    farrier_id = "A1A2-TEST_FARRIER_001"
    owner_id = "A1A2-TEST_OWNER_001"
    farrier_candidate = approve_candidate(load(SOURCE_EXAMPLES / "valid-farrier-synthetic.json"), farrier_id)
    owner_candidate = approve_candidate(load(SOURCE_EXAMPLES / "valid-horse-owner-synthetic.json"), owner_id)

    farrier = build_envelope(farrier_candidate, farrier_id, "TEST_FARRIER_001")
    owner = build_envelope(owner_candidate, owner_id, "TEST_OWNER_001")

    write(VALID_DIR / "valid-farrier-handoff.json", farrier)
    write(VALID_DIR / "valid-horse-owner-handoff.json", owner)

    invalid_cases: dict[str, dict] = {}

    missing_approval = copy.deepcopy(farrier)
    missing_approval["candidate_snapshot"]["workflow"] = {
        "stage": "needs_review",
        "review_decision": "none",
        "reviewer": None,
        "decision_at": None,
        "rejection_reason": None,
    }
    refresh_integrity(missing_approval)
    invalid_cases["invalid-missing-human-approval.json"] = missing_approval

    wrong_recommendation = copy.deepcopy(farrier)
    wrong_recommendation["candidate_snapshot"]["recommendation"]["next_action"] = "review"
    refresh_integrity(wrong_recommendation)
    invalid_cases["invalid-recommendation-not-pass-to-a2.json"] = wrong_recommendation

    possible_duplicate = copy.deepcopy(farrier)
    possible_duplicate["candidate_snapshot"]["duplicate_check"]["batch"] = {
        "status": "possible_match",
        "checked_at": CREATED_TIME,
        "method_version": "local-dedup-0.1",
        "matches": [{
            "system": "current_batch",
            "record_id": "A1-OTHER_SYNTHETIC",
            "record_url": None,
            "match_level": "probable",
            "matched_fields": ["identity.organisation.domain"],
        }],
        "notes": "Synthetic possible duplicate."
    }
    refresh_integrity(possible_duplicate)
    invalid_cases["invalid-possible-duplicate-declared-eligible.json"] = possible_duplicate

    hash_mismatch = copy.deepcopy(farrier)
    hash_mismatch["snapshot_integrity"]["candidate_snapshot_sha256"] = "0" * 64
    invalid_cases["invalid-snapshot-hash.json"] = hash_mismatch

    manual_claims_delivered = copy.deepcopy(farrier)
    manual_claims_delivered["operating_scope"] = "manual_no_integration_pilot"
    manual_claims_delivered["delivery_state"] = "delivered"
    manual_claims_delivered["a2_receipt"] = None
    invalid_cases["invalid-no-integration-claims-delivered.json"] = manual_claims_delivered

    crm_write = copy.deepcopy(farrier)
    crm_write["constraints"]["crm_write_authorized"] = True
    crm_write["constraints"]["external_action_approval_reference"] = "UNAPPROVED-TEST-REFERENCE"
    invalid_cases["invalid-synthetic-crm-write-authorized.json"] = crm_write

    receipt_mismatch = copy.deepcopy(farrier)
    receipt_mismatch["a2_receipt"]["handoff_id"] = "A1A2-WRONG_RECEIPT_ID"
    invalid_cases["invalid-receipt-handoff-id.json"] = receipt_mismatch

    duplicate_gates = copy.deepcopy(farrier)
    duplicate_gates["eligibility"]["gates"][-1] = copy.deepcopy(duplicate_gates["eligibility"]["gates"][0])
    invalid_cases["invalid-duplicate-gate-id.json"] = duplicate_gates

    excluded = copy.deepcopy(farrier)
    excluded["candidate_snapshot"]["qualification"]["exclusion_status"] = "excluded"
    excluded["candidate_snapshot"]["qualification"]["exclusion_reasons"] = ["Synthetic confirmed exclusion."]
    excluded["candidate_snapshot"]["recommendation"]["next_action"] = "exclude"
    excluded["candidate_snapshot"]["workflow"] = {
        "stage": "rejected",
        "review_decision": "rejected",
        "reviewer": copy.deepcopy(REVIEWER),
        "decision_at": APPROVAL_TIME,
        "rejection_reason": "Synthetic confirmed exclusion."
    }
    refresh_integrity(excluded)
    invalid_cases["invalid-excluded-candidate.json"] = excluded

    for filename, document in invalid_cases.items():
        write(INVALID_DIR / filename, document)

    print(json.dumps({
        "valid_fixtures": 2,
        "invalid_fixtures": len(invalid_cases),
        "output_root": str(OUTPUT_ROOT),
    }, indent=2))


if __name__ == "__main__":
    main()
