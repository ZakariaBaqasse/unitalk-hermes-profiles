#!/usr/bin/env python3
"""Build targeted Step 2E cross-field validation fixtures."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = PROFILE_ROOT / "foundations" / "contracts" / "canonical"
STEP2C = PROFILE_ROOT / "foundations" / "contracts" / "requalification" / "examples" / "valid"
ROOT = PROFILE_ROOT / "evaluations" / "step2e" / "fixtures"
VALID = ROOT / "valid"
INVALID = ROOT / "invalid"
CATALOGUES = ROOT / "catalogues"
MANIFEST = ROOT / "test-manifest.json"
VALIDATOR_MANIFEST = PROFILE_ROOT / "foundations" / "contracts" / "canonical" / "a2-cross-field-validator.manifest.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    package = load(STEP2C / "valid-synthetic-requalification-package.json")
    previous = load(CANONICAL / "examples" / "valid" / "valid-synthetic-initialised-record.json")
    current = load(CANONICAL / "examples" / "valid" / "valid-synthetic-enriched-record.json")
    for record in (previous, current):
        candidate = record["source_handoff"]["handoff_snapshot"]["candidate_snapshot"]
        current_scoring = copy.deepcopy(package["original_scoring"])
        for component in current_scoring["components"]:
            component["evidence_ids"] = ["EV-TEST002"]
        candidate["scoring"] = current_scoring
        candidate["qualification"]["icp_config_version"] = "1.0.0"
        candidate["qualification"]["criteria"] = [
            {
                "criterion_id": component["criterion_id"],
                "criterion_label": component["criterion_id"].replace("_", " ").replace(".", " — "),
                "category": "fit",
                "status": "confirmed",
                "evidence_ids": ["EV-TEST002"],
                "notes": "Synthetic current-model Step 2E fixture.",
            }
            for component in current_scoring["components"]
        ]
        candidate["source_evidence"][0]["supports_claims"] = [component["criterion_id"] for component in current_scoring["components"]]
        snapshot_hash = canonical_hash(candidate)
        embedded = record["source_handoff"]["handoff_snapshot"]
        embedded["snapshot_integrity"]["candidate_snapshot_sha256"] = snapshot_hash
        embedded["a2_receipt"]["candidate_snapshot_sha256"] = snapshot_hash
        record["source_handoff"]["candidate_snapshot_sha256"] = snapshot_hash
    current["workflow"]["state"] = "enrichment_planned"
    current["workflow"]["previous_state"] = "initialised"

    catalogue = {
        "catalogue_id": "synthetic-step2e-field-catalogue",
        "version": "unitalk-placeholder-0.0.0",
        "status": "synthetic_validator_fixture_only",
        "fields": [
            {"field_key": "organisation.horse_count", "value_type": "integer"},
            {"field_key": "relationship.role", "value_type": "string"}
        ],
    }
    write(CATALOGUES / "synthetic-field-catalogue.json", catalogue)
    write(VALID / "valid-initial-record.json", previous)
    write(VALID / "valid-enriched-revision.json", current)

    rq_record = copy.deepcopy(current)
    signal = load(STEP2C / "valid-horse-owner-signal.json")
    signal.update({
        "a2_record_id": rq_record["record_metadata"]["a2_record_id"],
        "a2_record_revision_id": rq_record["record_metadata"]["record_revision_id"],
        "a1_candidate_id": rq_record["system_references"]["a1_candidate_id"],
        "a1_handoff_id": rq_record["system_references"]["a1_handoff_id"],
        "a1_candidate_snapshot_sha256": rq_record["source_handoff"]["candidate_snapshot_sha256"],
        "audit_correlation_id": rq_record["record_metadata"]["audit_correlation_id"],
        "synthetic": True,
    })
    rq_record["requalification"]["signals"] = [signal]
    rq_record["evidence_registry"][0]["supports_requalification_signal_ids"] = [signal["signal_id"]]
    write(VALID / "valid-requalification-signal-record.json", rq_record)

    full_rq_record = copy.deepcopy(rq_record)
    full_signal = full_rq_record["requalification"]["signals"][0]
    full_signal["status"] = "accepted_by_a1"
    returned = copy.deepcopy(package["requalification_return"])
    returned.update({
        "a2_record_id": full_rq_record["record_metadata"]["a2_record_id"],
        "a2_record_revision_id": full_rq_record["record_metadata"]["record_revision_id"],
        "a1_candidate_id": full_rq_record["system_references"]["a1_candidate_id"],
        "a1_handoff_id": full_rq_record["system_references"]["a1_handoff_id"],
        "a1_candidate_snapshot_sha256": full_rq_record["source_handoff"]["candidate_snapshot_sha256"],
        "audit_correlation_id": full_rq_record["record_metadata"]["audit_correlation_id"],
        "synthetic": True,
    })
    returned["signal_snapshots"] = [copy.deepcopy(full_signal)]
    returned["signal_snapshot_sha256"] = canonical_hash(returned["signal_snapshots"])
    returned["a1_receipt"].update({
        "return_id": returned["return_id"],
        "signal_snapshot_sha256": returned["signal_snapshot_sha256"],
    })
    revision = copy.deepcopy(package["score_revision_reference"])
    revision.update({
        "a1_candidate_id": full_rq_record["system_references"]["a1_candidate_id"],
        "prior_revision_id": None,
        "source_requalification_return_id": returned["return_id"],
        "source_signal_ids": [full_signal["signal_id"]],
        "audit_correlation_id": full_rq_record["record_metadata"]["audit_correlation_id"],
        "synthetic": True,
    })
    revision["prior_scoring"] = copy.deepcopy(
        full_rq_record["source_handoff"]["handoff_snapshot"]["candidate_snapshot"]["scoring"]
    )
    full_rq_record["requalification"]["returns"] = [returned]
    full_rq_record["requalification"]["score_revision_references"] = [revision]
    full_rq_record["system_references"]["requalification_return_id"] = returned["return_id"]
    full_rq_record["system_references"]["a1_score_revision_id"] = revision["score_revision_id"]
    write(VALID / "valid-complete-requalification-record.json", full_rq_record)

    lifecycle_record = copy.deepcopy(rq_record)
    lifecycle_record["record_metadata"].update({
        "record_revision_id": "A2-REV-SYNTH_OWNER_003",
        "revision_number": 3,
        "supersedes_revision_id": rq_record["record_metadata"]["record_revision_id"],
    })
    lifecycle_record["workflow"].update({"state": "enrichment_in_progress", "previous_state": "enrichment_planned"})
    lifecycle_signal = lifecycle_record["requalification"]["signals"][0]
    lifecycle_signal["status"] = "sent_to_a1"
    lifecycle_return = copy.deepcopy(package["requalification_return"])
    lifecycle_return.update({
        "a2_record_id": lifecycle_record["record_metadata"]["a2_record_id"],
        "a2_record_revision_id": lifecycle_record["record_metadata"]["record_revision_id"],
        "a1_candidate_id": lifecycle_record["system_references"]["a1_candidate_id"],
        "a1_handoff_id": lifecycle_record["system_references"]["a1_handoff_id"],
        "a1_candidate_snapshot_sha256": lifecycle_record["source_handoff"]["candidate_snapshot_sha256"],
        "audit_correlation_id": lifecycle_record["record_metadata"]["audit_correlation_id"],
        "status": "delivered",
        "a1_receipt": None,
        "synthetic": True,
    })
    lifecycle_return["signal_snapshots"] = [copy.deepcopy(lifecycle_signal)]
    lifecycle_return["signal_snapshot_sha256"] = canonical_hash(lifecycle_return["signal_snapshots"])
    lifecycle_record["requalification"]["returns"] = [lifecycle_return]
    lifecycle_record["system_references"]["requalification_return_id"] = lifecycle_return["return_id"]
    write(VALID / "valid-requalification-lifecycle-revision.json", lifecycle_record)

    relationship_record = copy.deepcopy(current)
    relationship_record["subject"]["entities"].append({
        "entity_id": "A2-ENT-OWNER_PERSON_001", "entity_type": "person",
        "source_identity_reference": None, "display_name": "Synthetic Owner Contact",
        "aliases": [], "match_status": "not_checked", "external_matches": []
    })
    relationship_record["subject"]["relationships"].append({
        "relationship_id": "A2-REL-OWNER_ROLE_001", "from_entity_id": "A2-ENT-OWNER_PERSON_001",
        "to_entity_id": "A2-ENT-OWNER_ORG_001", "relationship_type": "owns",
        "evidence_ids": ["A2-EV-HORSE-COUNT"]
    })
    relationship_assessment = copy.deepcopy(relationship_record["field_assessments"][0])
    relationship_assessment.update({
        "field_assessment_id": "A2-FLD-RELATIONSHIP-ROLE",
        "field_key": "relationship.role",
        "entity_id": "A2-REL-OWNER_ROLE_001",
        "scope": "relationship",
        "value_type": "string",
    })
    relationship_assessment["observations"][0].update({
        "observation_id": "A2-OBS-RELATIONSHIP-ROLE-001",
        "raw_value": "Owner",
        "normalised_value": "owner",
    })
    relationship_assessment["proposed_resolution"].update({"value": "owner", "normalised_value": "owner"})
    relationship_record["field_assessments"].append(relationship_assessment)
    relationship_record["evidence_registry"][0]["supports_field_assessment_ids"].append("A2-FLD-RELATIONSHIP-ROLE")
    relationship_record["data_quality"]["unverified_field_keys"].append("relationship.role")
    write(VALID / "valid-relationship-scoped-assessment.json", relationship_record)

    cases: list[dict] = [
        {"name": "valid_initial_record", "record": "valid/valid-initial-record.json", "expected_valid": True},
        {"name": "valid_enriched_revision", "record": "valid/valid-enriched-revision.json", "previous_record": "valid/valid-initial-record.json", "field_catalogue": "catalogues/synthetic-field-catalogue.json", "expected_valid": True},
        {"name": "valid_requalification_signal", "record": "valid/valid-requalification-signal-record.json", "previous_record": "valid/valid-initial-record.json", "field_catalogue": "catalogues/synthetic-field-catalogue.json", "expected_valid": True},
        {"name": "valid_complete_requalification", "record": "valid/valid-complete-requalification-record.json", "previous_record": "valid/valid-initial-record.json", "field_catalogue": "catalogues/synthetic-field-catalogue.json", "expected_valid": True},
        {"name": "valid_requalification_lifecycle_revision", "record": "valid/valid-requalification-lifecycle-revision.json", "previous_record": "valid/valid-requalification-signal-record.json", "field_catalogue": "catalogues/synthetic-field-catalogue.json", "expected_valid": True},
        {"name": "valid_relationship_scoped_assessment", "record": "valid/valid-relationship-scoped-assessment.json", "previous_record": "valid/valid-initial-record.json", "field_catalogue": "catalogues/synthetic-field-catalogue.json", "expected_valid": True},
    ]

    def invalid(name: str, record: dict, expected_error: str, previous_record: str | None = None, field_catalogue: str | None = None) -> None:
        filename = f"{name}.json"
        write(INVALID / filename, record)
        case = {"name": name, "record": f"invalid/{filename}", "expected_valid": False, "expected_error": expected_error}
        if previous_record:
            case["previous_record"] = previous_record
        if field_catalogue:
            case["field_catalogue"] = field_catalogue
        cases.append(case)

    item = copy.deepcopy(previous)
    item["source_handoff"]["handoff_id"] = "A1A2-OTHER_OWNER_001"
    invalid("invalid-handoff-mirror", item, "source_handoff.handoff_id does not match its authoritative source")

    item = copy.deepcopy(previous)
    item["source_handoff"]["candidate_snapshot_sha256"] = "0" * 64
    invalid("invalid-candidate-hash", item, "source_handoff candidate snapshot hash mismatch")

    item = copy.deepcopy(previous)
    item["system_references"]["a1_candidate_id"] = "A1-OTHER_OWNER_001"
    invalid("invalid-system-candidate-reference", item, "system_references.a1_candidate_id does not match its authoritative source")

    item = copy.deepcopy(previous)
    duplicate_entity = copy.deepcopy(item["subject"]["entities"][0])
    duplicate_entity["display_name"] = "Duplicate synthetic entity"
    item["subject"]["entities"].append(duplicate_entity)
    invalid("invalid-duplicate-entity-id", item, "duplicate entity_id")

    item = copy.deepcopy(previous)
    item["subject"]["relationships"].append({
        "relationship_id": "A2-REL-UNKNOWN_001",
        "from_entity_id": "A2-ENT-OWNER_ORG_001",
        "to_entity_id": "A2-ENT-MISSING_001",
        "relationship_type": "works_for",
        "evidence_ids": ["EV-TEST002"],
    })
    invalid("invalid-relationship-reference", item, "references unknown to_entity_id")

    item = copy.deepcopy(current)
    item["field_assessments"][0]["entity_id"] = "A2-ENT-MISSING_001"
    invalid("invalid-assessment-entity-reference", item, "references unknown entity")

    item = copy.deepcopy(current)
    duplicate_assessment = copy.deepcopy(item["field_assessments"][0])
    duplicate_assessment["field_assessment_id"] = "A2-FLD-HORSE-COUNT-DUP"
    item["field_assessments"].append(duplicate_assessment)
    invalid("invalid-duplicate-assessment-target", item, "duplicate field assessment target")

    item = copy.deepcopy(current)
    item["field_assessments"][0]["observations"][0]["evidence_ids"] = ["A2-EV-MISSING"]
    invalid("invalid-observation-evidence-reference", item, "references unknown evidence ID A2-EV-MISSING")

    item = copy.deepcopy(current)
    item["evidence_registry"][0]["supports_field_assessment_ids"] = ["A2-FLD-MISSING"]
    invalid("invalid-evidence-assessment-reference", item, "supports unknown field assessment A2-FLD-MISSING")

    item = copy.deepcopy(current)
    item["field_assessments"][0]["proposed_resolution"]["evidence_ids"] = []
    invalid("invalid-update-without-evidence", item, "add/update proposal requires evidence")

    item = copy.deepcopy(current)
    item["field_assessments"][0]["proposed_resolution"]["action"] = "update"
    item["field_assessments"][0]["proposed_resolution"]["protected_status"] = "protected_manual"
    item["field_assessments"][0]["application"]["status"] = "pending"
    invalid("invalid-protected-update-without-approval", item, "requires explicit approved review and approval matrix")

    item = copy.deepcopy(current)
    item["field_assessments"][0]["application"]["status"] = "pending"
    invalid("invalid-application-without-approval", item, "application requires approved field review")

    item = copy.deepcopy(current)
    item["workflow"]["state"] = "review_required"
    item["workflow"]["previous_state"] = "initialised"
    invalid("invalid-workflow-transition", item, "invalid workflow transition initialised -> review_required", previous_record="valid/valid-initial-record.json")

    item = copy.deepcopy(current)
    item["workflow"]["state"] = "changes_requested"
    item["review"]["record_decision"] = "pending"
    invalid("invalid-workflow-review-mismatch", item, "workflow state changes_requested requires record review decision needs_changes")

    item = copy.deepcopy(current)
    item["duplicate_and_eligibility"]["checks"] = [{
        "check_id": "A2-CHECK-DUPLICATE-001", "check_type": "duplicate", "system": "a2_local",
        "status": "possible_match", "checked_at": "2026-08-26T10:09:00Z",
        "matches_or_references": [], "reason": "Synthetic possible duplicate."
    }]
    item["duplicate_and_eligibility"]["a2_eligibility_status"] = "eligible"
    invalid("invalid-possible-duplicate-eligible", item, "possible duplicate requires hold or blocked A2 eligibility")

    item = copy.deepcopy(current)
    item["data_quality"]["missing_field_keys"] = ["organisation.unknown_required_field"]
    item["data_quality"]["required_field_keys"] = ["organisation.unknown_required_field"]
    invalid("invalid-quality-field-reference", item, "references field key without an assessment")

    item = copy.deepcopy(current)
    item["data_quality"]["required_field_keys"] = ["organisation.horse_count"]
    item["data_quality"]["missing_field_keys"] = ["organisation.horse_count"]
    invalid("invalid-known-field-marked-missing", item, "marks known usable field as missing")

    item = copy.deepcopy(current)
    item["data_quality"]["status"] = "review_ready"
    item["data_quality"]["conflict_field_keys"] = ["organisation.horse_count"]
    invalid("invalid-review-ready-with-conflict", item, "review_ready cannot contain missing, conflict or invalid fields")

    item = copy.deepcopy(rq_record)
    item["requalification"]["signals"][0]["a1_candidate_id"] = "A1-OTHER_OWNER_001"
    invalid("invalid-requalification-candidate-link", item, "a1_candidate_id mismatch")

    item = copy.deepcopy(rq_record)
    returned = load(STEP2C / "valid-manual-prepared-return.json")
    returned.update({
        "operating_scope": "synthetic_test",
        "a2_record_id": item["record_metadata"]["a2_record_id"],
        "a2_record_revision_id": item["record_metadata"]["record_revision_id"],
        "a1_candidate_id": item["system_references"]["a1_candidate_id"],
        "a1_handoff_id": item["system_references"]["a1_handoff_id"],
        "a1_candidate_snapshot_sha256": item["source_handoff"]["candidate_snapshot_sha256"],
        "audit_correlation_id": item["record_metadata"]["audit_correlation_id"],
        "status": "prepared",
        "a1_receipt": None,
    })
    returned["signal_snapshots"] = [copy.deepcopy(item["requalification"]["signals"][0])]
    returned["signal_snapshots"][0]["reason"] = "Changed snapshot text that is not present in the canonical signal."
    returned["signal_snapshot_sha256"] = canonical_hash(returned["signal_snapshots"])
    returned["delivery"] = {"external_event_reference": None, "attempt_count": 0, "last_attempt_at": None, "failure_reason": None}
    item["requalification"]["returns"] = [returned]
    invalid("invalid-return-signal-snapshot", item, "signal snapshot differs from canonical signal")

    item = copy.deepcopy(rq_record)
    item["requalification"]["signals"][0]["status"] = "accepted_by_a1"
    revision = load(STEP2C / "valid-synthetic-requalification-package.json")["score_revision_reference"]
    revision.update({
        "a1_candidate_id": item["system_references"]["a1_candidate_id"],
        "source_signal_ids": [item["requalification"]["signals"][0]["signal_id"]],
        "audit_correlation_id": item["record_metadata"]["audit_correlation_id"],
        "synthetic": True,
    })
    item["requalification"]["score_revision_references"] = [revision]
    invalid("invalid-score-revision-return-link", item, "references unknown requalification return")

    item = copy.deepcopy(current)
    item["audit_and_consumption"]["events"][0]["usage"] = {
        "input_tokens": 10, "output_tokens": 5, "total_tokens": 15, "api_calls": 1,
        "credits": 1, "cost_amount": 0.01, "currency": "USD", "cost_status": "known"
    }
    item["audit_and_consumption"]["total_usage"].update({"input_tokens": 10, "output_tokens": 5, "total_tokens": 99, "api_calls": 1, "credits": 1, "cost_amount": 0.01})
    invalid("invalid-usage-total", item, "audit total_usage.total_tokens does not equal event usage total")

    item = copy.deepcopy(current)
    item["field_assessments"][0]["field_key"] = "organisation.unapproved_field"
    invalid("invalid-field-catalogue-key", item, "uses unknown Field Catalogue key", field_catalogue="catalogues/synthetic-field-catalogue.json")

    item = copy.deepcopy(current)
    item["field_assessments"][0]["value_type"] = "string"
    invalid("invalid-field-catalogue-type", item, "value_type does not match Field Catalogue", field_catalogue="catalogues/synthetic-field-catalogue.json")

    item = copy.deepcopy(current)
    item["field_assessments"][0]["observations"][0]["normalised_value"] = "four"
    invalid("invalid-field-catalogue-value", item, "normalised_value does not match Field Catalogue type integer", field_catalogue="catalogues/synthetic-field-catalogue.json")

    item = copy.deepcopy(current)
    item["governance"]["source_register_version"] = "source-register-other"
    invalid("invalid-source-register-version", item, "source_register_version values must match")

    item = copy.deepcopy(current)
    item["evidence_registry"][0]["supports_field_assessment_ids"] = []
    invalid("invalid-nonreciprocal-evidence-link", item, "without reciprocal field-assessment support")

    item = copy.deepcopy(current)
    item["evidence_registry"][0]["source_policy_status"] = "blocked"
    invalid("invalid-blocked-evidence-use", item, "not approved for evidentiary use")

    item = copy.deepcopy(full_rq_record)
    item["requalification"]["returns"][0]["status"] = "prepared"
    item["requalification"]["returns"][0]["a1_receipt"] = None
    item["requalification"]["returns"][0]["delivery"] = {"external_event_reference": None, "attempt_count": 0, "last_attempt_at": None, "failure_reason": None}
    invalid("invalid-score-revision-unaccepted-return", item, "requires an accepted_by_a1 return")

    item = copy.deepcopy(full_rq_record)
    item["requalification"]["score_revision_references"][0]["revised_scoring"]["score"] = 99
    item["requalification"]["score_revision_references"][0]["result_sha256"] = canonical_hash(item["requalification"]["score_revision_references"][0]["revised_scoring"])
    invalid("invalid-score-revision-arithmetic", item, "revised scoring score must equal component total")

    item = copy.deepcopy(full_rq_record)
    item["requalification"]["score_revision_references"][0]["prior_scoring"]["rationale"] = "Mutated prior scoring snapshot."
    invalid("invalid-score-revision-prior-scoring", item, "prior_scoring does not match immutable A1 handoff scoring")

    item = copy.deepcopy(full_rq_record)
    second_signal = copy.deepcopy(item["requalification"]["signals"][0])
    second_signal["signal_id"] = "A2-RQ-SIG-HORSE_COUNT_002"
    item["requalification"]["signals"].append(second_signal)
    item["evidence_registry"][0]["supports_requalification_signal_ids"].append(second_signal["signal_id"])
    revision_item = item["requalification"]["score_revision_references"][0]
    revision_item["source_signal_ids"] = [second_signal["signal_id"]]
    revision_item["criteria_changes"][0]["source_signal_ids"] = [second_signal["signal_id"]]
    invalid("invalid-score-revision-signal-outside-return", item, "uses signals outside its referenced return")

    item = copy.deepcopy(current)
    item["audit_and_consumption"]["events"][0]["usage"] = {
        "input_tokens": 10, "output_tokens": 5, "total_tokens": 14, "api_calls": 1,
        "credits": 1, "cost_amount": 0.01, "currency": "USD", "cost_status": "known"
    }
    item["audit_and_consumption"]["total_usage"].update({"input_tokens": 10, "output_tokens": 5, "total_tokens": 14, "api_calls": 1, "credits": 1, "cost_amount": 0.01})
    invalid("invalid-event-token-arithmetic", item, "total_tokens does not equal input_tokens plus output_tokens")

    item = copy.deepcopy(current)
    item["governance"]["outreach_authorized"] = True
    invalid("invalid-a2-outreach-authorisation", item, "A2 must not authorise outreach")

    item = copy.deepcopy(current)
    invalid("invalid-later-revision-without-previous", item, "later revision requires the previous record")

    item = copy.deepcopy(current)
    item["record_metadata"]["record_revision_id"] = previous["record_metadata"]["record_revision_id"]
    item["record_metadata"]["supersedes_revision_id"] = previous["record_metadata"]["record_revision_id"]
    invalid("invalid-reused-revision-id", item, "record_revision_id must be new", previous_record="valid/valid-initial-record.json")

    item = copy.deepcopy(previous)
    item["source_handoff"]["handoff_snapshot"]["candidate_snapshot"]["recommendation"]["next_action"] = "review"
    revised_candidate = item["source_handoff"]["handoff_snapshot"]["candidate_snapshot"]
    revised_hash = canonical_hash(revised_candidate)
    item["source_handoff"]["handoff_snapshot"]["snapshot_integrity"]["candidate_snapshot_sha256"] = revised_hash
    item["source_handoff"]["handoff_snapshot"]["a2_receipt"]["candidate_snapshot_sha256"] = revised_hash
    item["source_handoff"]["candidate_snapshot_sha256"] = revised_hash
    invalid("invalid-embedded-handoff-gate", item, "embedded handoff invalid: candidate recommendation.next_action must be pass_to_a2")

    item = copy.deepcopy(current)
    item["subject"]["entities"][0]["external_matches"] = [{
        "match_id": "A2-MATCH-UNKNOWN-001", "system": "synthetic", "object_type": "company",
        "external_record_id": None, "status": "possible_match", "checked_at": "2026-08-26T10:05:00Z",
        "evidence_ids": ["A2-EV-MISSING"], "reason": "Synthetic negative case."
    }]
    invalid("invalid-external-match-evidence", item, "external match A2-MATCH-UNKNOWN-001 references unknown evidence ID")

    item = copy.deepcopy(current)
    item["evidence_registry"][0]["supersedes_evidence_id"] = "A2-EV-MISSING"
    invalid("invalid-superseded-evidence-reference", item, "supersedes unknown A2 evidence")

    item = copy.deepcopy(current)
    item["evidence_registry"][0]["supersedes_evidence_id"] = item["evidence_registry"][0]["evidence_id"]
    invalid("invalid-evidence-self-cycle", item, "evidence supersession cycle detected")

    item = copy.deepcopy(current)
    item["evidence_registry"][0]["provider_reference"] = "provider-request-unapproved"
    invalid("invalid-provider-use-without-authorisation", item, "claims provider use without authorisation")

    item = copy.deepcopy(current)
    item["field_assessments"][0]["baseline"] = {
        "value": 3, "normalised_value": 3,
        "origin": {"system": "hubspot", "record_reference": "synthetic-contact", "field_reference": "synthetic-field", "source_kind": "hubspot"},
        "observed_at": "2026-08-26T10:00:00Z", "evidence_ids": [], "protected_status": "protected_manual"
    }
    item["field_assessments"][0]["proposed_resolution"]["action"] = "update"
    item["field_assessments"][0]["proposed_resolution"]["protected_status"] = "not_protected"
    invalid("invalid-protected-baseline-downgrade", item, "cannot downgrade a protected baseline")

    item = copy.deepcopy(current)
    item["field_assessments"][0]["proposed_resolution"]["action"] = "clear_request"
    item["field_assessments"][0]["proposed_resolution"]["value"] = None
    item["field_assessments"][0]["proposed_resolution"]["normalised_value"] = 4
    invalid("invalid-clear-request-normalised-value", item, "clear_request proposal must not contain a normalised replacement value")

    item = copy.deepcopy(current)
    item["field_assessments"][0]["application"]["status"] = "failed"
    item["field_assessments"][0]["application"]["error"] = {
        "code": "SYNTHETIC_FAILURE", "message": "Synthetic failed write attempt.",
        "retryable": False, "occurred_at": "2026-08-26T10:11:00Z", "details": []
    }
    invalid("invalid-failed-application-without-approval", item, "application requires approved field review")

    item = copy.deepcopy(current)
    item["duplicate_and_eligibility"]["owner_routing_status"] = "approved_reassignment"
    invalid("invalid-owner-reassignment-without-approval", item, "approved owner reassignment requires approved record review and approval matrix")

    item = copy.deepcopy(current)
    item["review"].update({
        "record_decision": "approved",
        "reviewer": {"actor_id": "UNITALK-A2-REVIEWER", "actor_role": "A2 Business Reviewer", "display_name": "Synthetic Reviewer", "profile_id": None, "workflow_id": None},
        "decided_at": "2026-08-26T10:20:00Z",
        "reason": "Synthetic approval.",
        "required_field_decisions_complete": True,
    })
    item["workflow"]["state"] = "record_approved"
    item["workflow"]["previous_state"] = "review_required"
    invalid("invalid-record-approved-with-pending-field", item, "required_field_decisions_complete is true while field reviews remain unresolved")

    item = copy.deepcopy(current)
    item["workflow"]["state"] = "blocked"
    item["workflow"]["previous_state"] = "enrichment_planned"
    item["workflow"]["block_reasons"] = ["Synthetic policy block."]
    invalid("invalid-blocked-workflow-pending-review", item, "workflow state blocked requires record review decision blocked")

    item = copy.deepcopy(current)
    item["field_assessments"][0]["field_review"] = {
        "decision": "approved",
        "reviewer": {"actor_id": "UNITALK-A2-REVIEWER", "actor_role": "A2 Business Reviewer", "display_name": "Synthetic Reviewer", "profile_id": None, "workflow_id": None},
        "decided_at": "2026-08-26T10:20:00Z", "reason": "Synthetic approval.", "corrected_value": None
    }
    item["review"].update({
        "record_decision": "approved",
        "reviewer": {"actor_id": "UNITALK-A2-REVIEWER", "actor_role": "A2 Business Reviewer", "display_name": "Synthetic Reviewer", "profile_id": None, "workflow_id": None},
        "decided_at": "2026-08-26T10:20:00Z", "reason": "Synthetic approval.",
        "required_field_decisions_complete": True,
    })
    item["field_assessments"][0]["application"].update({
        "status": "applied", "destination": "synthetic-hubspot-field",
        "external_action_reference": "SYNTHETIC-ACTION-001",
        "workflow_dependency_status": "verified_no_side_effect", "applied_at": "2026-08-26T10:21:00Z"
    })
    item["governance"]["crm_write_authorized"] = True
    invalid("invalid-application-without-audit-receipt", item, "application lacks a matching successful audit action")

    item = copy.deepcopy(current)
    invalid("invalid-cross-field-previous-record", item, "previous:source_handoff.handoff_id does not match its authoritative source", previous_record="invalid/invalid-handoff-mirror.json")

    item = copy.deepcopy(lifecycle_record)
    item["requalification"]["signals"][0]["status"] = "rescored"
    item["requalification"]["returns"] = []
    item["system_references"]["requalification_return_id"] = None
    invalid("invalid-requalification-lifecycle-jump", item, "invalid signals lifecycle transition approved_for_return -> rescored", previous_record="valid/valid-requalification-signal-record.json")

    item = copy.deepcopy(lifecycle_record)
    item["requalification"]["signals"][0]["reason"] = "Mutated immutable signal payload."
    item["requalification"]["returns"][0]["signal_snapshots"] = [copy.deepcopy(item["requalification"]["signals"][0])]
    item["requalification"]["returns"][0]["signal_snapshot_sha256"] = canonical_hash(item["requalification"]["returns"][0]["signal_snapshots"])
    invalid("invalid-requalification-payload-mutation", item, "requalification signals immutable payload mutated", previous_record="valid/valid-requalification-signal-record.json")

    prior_with_evidence = copy.deepcopy(current)
    write(VALID / "valid-prior-with-evidence.json", prior_with_evidence)
    cases.append({"name": "valid_prior_with_evidence", "record": "valid/valid-prior-with-evidence.json", "previous_record": "valid/valid-initial-record.json", "expected_valid": True})
    current_mutated = copy.deepcopy(current)
    current_mutated["record_metadata"].update({"record_revision_id": "A2-REV-SYNTH_OWNER_003", "revision_number": 3, "supersedes_revision_id": "A2-REV-SYNTH_OWNER_002"})
    current_mutated["workflow"].update({"state": "enrichment_in_progress", "previous_state": "enrichment_planned"})
    current_mutated["evidence_registry"][0]["excerpt_or_result_summary"] = "Mutated historical evidence."
    invalid("invalid-append-only-evidence-mutation", current_mutated, "append-only collection evidence_registry mutated", previous_record="valid/valid-prior-with-evidence.json")

    write(MANIFEST, {"step": "2E", "validator_version": "0.1.0", "cases": cases})
    runtime_dependencies = [
        PROFILE_ROOT / "scripts" / "validate_a2_enrichment_record.py",
        PROFILE_ROOT / "scripts" / "validate_step2c_artifacts.py",
        PROFILE_ROOT / "scripts" / "validate_a1_to_a2_handoff.py",
        PROFILE_ROOT / "foundations" / "contracts" / "canonical" / "a2-enrichment-record.schema.json",
        PROFILE_ROOT / "foundations" / "contracts" / "a2-state-model-0.1.0.json",
        PROFILE_ROOT / "foundations" / "contracts" / "a2-field-dictionary-0.1.0.csv",
        PROFILE_ROOT / "foundations" / "contracts" / "a1-to-a2-handoff.schema.json",
        PROFILE_ROOT / "foundations" / "contracts" / "dependencies" / "a1_validate_candidate.py",
        PROFILE_ROOT / "foundations" / "contracts" / "dependencies" / "a1-equinet-icp-v1.yaml",
        PROFILE_ROOT / "foundations" / "contracts" / "dependencies" / "a1-evidence-confidence-rules-v1.yaml",
        PROFILE_ROOT / "foundations" / "contracts" / "dependencies" / "a1-icp-scoring-model-v1.yaml",
        PROFILE_ROOT / "foundations" / "contracts" / "requalification" / "a2-requalification-signal.schema.json",
        PROFILE_ROOT / "foundations" / "contracts" / "requalification" / "a2-requalification-return.schema.json",
        PROFILE_ROOT / "foundations" / "contracts" / "requalification" / "a1-score-revision-reference.schema.json",
        MANIFEST,
    ]
    write(VALIDATOR_MANIFEST, {
        "manifest_id": "equinet-a2-cross-field-validator",
        "validator_version": "0.1.0",
        "status": "promoted_by_unitalk_in_step_2i",
        "entrypoint": "scripts/validate_a2_enrichment_record.py",
        "dependencies": [
            {"path": str(path.relative_to(PROFILE_ROOT)), "sha256": file_hash(path)}
            for path in runtime_dependencies
        ],
    })
    print(json.dumps({
        "valid_fixtures": len(list(VALID.glob("*.json"))),
        "invalid_fixtures": len(list(INVALID.glob("*.json"))),
        "cases": len(cases),
        "manifest": str(MANIFEST),
        "validator_manifest": str(VALIDATOR_MANIFEST),
    }, indent=2))


if __name__ == "__main__":
    main()
