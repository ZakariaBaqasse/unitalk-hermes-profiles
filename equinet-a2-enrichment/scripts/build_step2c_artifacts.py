#!/usr/bin/env python3
"""Build Step 2C schemas and deterministic synthetic fixtures."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = PROFILE_ROOT / "foundations" / "contracts"
SCHEMAS = CONTRACTS / "requalification"
EXAMPLES = SCHEMAS / "examples"
VALID = EXAMPLES / "valid"
INVALID = EXAMPLES / "invalid"

VERSION = "0.1.0"
SIGNAL_ID = f"https://unitalk.ai/schemas/equinet/a2/requalification-signal/{VERSION}"
RETURN_ID = f"https://unitalk.ai/schemas/equinet/a2/requalification-return/{VERSION}"
REVISION_ID = f"https://unitalk.ai/schemas/equinet/a2/a1-score-revision-reference/{VERSION}"
PACKAGE_ID = f"https://unitalk.ai/schemas/equinet/a2/requalification-package/{VERSION}"
A1_SCHEMA_ID = "https://unitalk.ai/schemas/equinet/a1/prospect-candidate/1.0.0"


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def actor_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["actor_id", "actor_role", "display_name"],
        "properties": {
            "actor_id": {"type": "string", "minLength": 1, "maxLength": 200},
            "actor_role": {"type": "string", "minLength": 1, "maxLength": 200},
            "display_name": {"type": ["string", "null"], "maxLength": 200},
        },
    }


def review_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["decision", "reviewer", "decided_at", "reason"],
        "properties": {
            "decision": {"type": "string", "enum": ["approved", "rejected", "needs_changes", "held"]},
            "reviewer": {"$ref": "#/$defs/actor"},
            "decided_at": {"type": "string", "format": "date-time"},
            "reason": {"type": "string", "minLength": 1, "maxLength": 2000},
        },
    }


def build_signal_schema() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SIGNAL_ID,
        "title": "Equinet A2 Requalification Signal",
        "description": "A2 evidence signal that may trigger A1 requalification but contains no replacement score or points.",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version", "signal_id", "a2_record_id", "a2_record_revision_id",
            "a1_candidate_id", "a1_handoff_id", "a1_candidate_snapshot_sha256",
            "affected_criterion_id", "prior_criterion_status", "proposed_evidence_status",
            "a1_evidence_ids", "a2_evidence_ids", "field_assessment_ids", "materiality",
            "potential_score_direction", "reason", "limitations", "created_by_profile",
            "created_at", "status", "review", "audit_correlation_id", "synthetic",
        ],
        "properties": {
            "schema_version": {"const": VERSION},
            "signal_id": {"type": "string", "pattern": "^A2-RQ-SIG-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "a2_record_id": {"type": "string", "pattern": "^A2-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "a2_record_revision_id": {"type": "string", "pattern": "^A2-REV-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "a1_candidate_id": {"type": "string", "pattern": "^A1-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "a1_handoff_id": {"type": "string", "pattern": "^A1A2-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "a1_candidate_snapshot_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            "affected_criterion_id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9_.-]{2,99}$"},
            "prior_criterion_status": {"type": "string", "enum": ["confirmed", "not_confirmed", "contradicted", "unknown"]},
            "proposed_evidence_status": {"type": "string", "enum": ["confirmed", "not_confirmed", "contradicted", "unknown"]},
            "a1_evidence_ids": {"type": "array", "items": {"type": "string", "minLength": 1}, "uniqueItems": True},
            "a2_evidence_ids": {"type": "array", "items": {"type": "string", "pattern": "^A2-EV-[A-Z0-9_-]{3,80}$"}, "uniqueItems": True},
            "field_assessment_ids": {"type": "array", "minItems": 1, "items": {"type": "string", "pattern": "^A2-FLD-[A-Z0-9_-]{3,80}$"}, "uniqueItems": True},
            "materiality": {"type": "string", "enum": ["low", "medium", "high"]},
            "potential_score_direction": {"type": "string", "enum": ["increase", "decrease", "unchanged", "unknown"]},
            "reason": {"type": "string", "minLength": 1, "maxLength": 3000},
            "limitations": {"type": "array", "items": {"type": "string", "minLength": 1, "maxLength": 1000}, "uniqueItems": True},
            "created_by_profile": {"const": "equinet-a2-enrichment"},
            "created_at": {"type": "string", "format": "date-time"},
            "status": {"type": "string", "enum": ["draft", "pending_review", "approved_for_return", "rejected", "sent_to_a1", "accepted_by_a1", "rejected_by_a1", "rescored", "error"]},
            "review": {"anyOf": [{"$ref": "#/$defs/review"}, {"type": "null"}]},
            "audit_correlation_id": {"type": "string", "minLength": 6, "maxLength": 200},
            "synthetic": {"type": "boolean"},
        },
        "allOf": [
            {
                "if": {"properties": {"status": {"enum": ["approved_for_return", "sent_to_a1", "accepted_by_a1", "rescored"]}}, "required": ["status"]},
                "then": {"properties": {"review": {"allOf": [{"$ref": "#/$defs/review"}, {"properties": {"decision": {"const": "approved"}}}]}}},
            },
            {
                "if": {"properties": {"status": {"const": "rejected"}}, "required": ["status"]},
                "then": {"properties": {"review": {"allOf": [{"$ref": "#/$defs/review"}, {"properties": {"decision": {"const": "rejected"}}}]}}},
            },
        ],
        "$defs": {"actor": actor_schema(), "review": review_schema()},
    }


def build_return_schema() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": RETURN_ID,
        "title": "Equinet A2-to-A1 Requalification Return",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version", "return_id", "idempotency_key", "created_at", "source_profile",
            "target_profile", "operating_scope", "a2_record_id", "a2_record_revision_id",
            "a1_candidate_id", "a1_handoff_id", "a1_candidate_snapshot_sha256",
            "target_icp_config_version", "target_evidence_policy_version", "target_scoring_model_version",
            "signal_snapshots", "signal_snapshot_sha256", "status", "approval", "delivery",
            "a1_receipt", "constraints", "audit_correlation_id", "synthetic",
        ],
        "properties": {
            "schema_version": {"const": VERSION},
            "return_id": {"type": "string", "pattern": "^A2-RQ-RET-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "idempotency_key": {"type": "string", "pattern": "^A2-RQ-IDEMP-[A-Z0-9_-]{6,100}$"},
            "created_at": {"type": "string", "format": "date-time"},
            "source_profile": {"const": "equinet-a2-enrichment"},
            "target_profile": {"const": "equinet-a1-icp-discovery"},
            "operating_scope": {"type": "string", "enum": ["synthetic_test", "manual_no_integration_pilot", "integrated_pilot", "production"]},
            "a2_record_id": {"type": "string", "pattern": "^A2-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "a2_record_revision_id": {"type": "string", "pattern": "^A2-REV-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "a1_candidate_id": {"type": "string", "pattern": "^A1-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "a1_handoff_id": {"type": "string", "pattern": "^A1A2-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "a1_candidate_snapshot_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            "target_icp_config_version": {"const": "1.0.0"},
            "target_evidence_policy_version": {"const": "1.0.0"},
            "target_scoring_model_version": {"const": "1.0.0"},
            "signal_snapshots": {"type": "array", "minItems": 1, "items": {"$ref": SIGNAL_ID}},
            "signal_snapshot_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            "status": {"type": "string", "enum": ["prepared", "delivered", "accepted_by_a1", "rejected_by_a1", "delivery_failed", "error"]},
            "approval": {"anyOf": [{"$ref": "#/$defs/review"}, {"type": "null"}]},
            "delivery": {"$ref": "#/$defs/delivery"},
            "a1_receipt": {"anyOf": [{"$ref": "#/$defs/a1Receipt"}, {"type": "null"}]},
            "constraints": {"$ref": "#/$defs/constraints"},
            "audit_correlation_id": {"type": "string", "minLength": 6, "maxLength": 200},
            "synthetic": {"type": "boolean"},
        },
        "allOf": [
            {
                "if": {"properties": {"operating_scope": {"const": "manual_no_integration_pilot"}}, "required": ["operating_scope"]},
                "then": {"properties": {"status": {"const": "prepared"}, "a1_receipt": {"type": "null"}, "delivery": {"properties": {"external_event_reference": {"type": "null"}, "attempt_count": {"const": 0}, "last_attempt_at": {"type": "null"}}}}},
            },
            {
                "if": {"properties": {"status": {"enum": ["delivered", "accepted_by_a1"]}}, "required": ["status"]},
                "then": {"properties": {"approval": {"allOf": [{"$ref": "#/$defs/review"}, {"properties": {"decision": {"const": "approved"}}}]}}},
            },
            {
                "if": {"properties": {"status": {"enum": ["accepted_by_a1", "rejected_by_a1"]}}, "required": ["status"]},
                "then": {"properties": {"a1_receipt": {"$ref": "#/$defs/a1Receipt"}}},
            },
        ],
        "$defs": {
            "actor": actor_schema(),
            "review": review_schema(),
            "delivery": {
                "type": "object", "additionalProperties": False,
                "required": ["external_event_reference", "attempt_count", "last_attempt_at", "failure_reason"],
                "properties": {
                    "external_event_reference": {"type": ["string", "null"], "maxLength": 300},
                    "attempt_count": {"type": "integer", "minimum": 0, "maximum": 20},
                    "last_attempt_at": {"type": ["string", "null"], "format": "date-time"},
                    "failure_reason": {"type": ["string", "null"], "maxLength": 1000},
                },
            },
            "a1Receipt": {
                "type": "object", "additionalProperties": False,
                "required": ["status", "receiver_profile", "receiver_id", "received_at", "return_id", "signal_snapshot_sha256", "rejection_reasons"],
                "properties": {
                    "status": {"type": "string", "enum": ["accepted", "rejected"]},
                    "receiver_profile": {"const": "equinet-a1-icp-discovery"},
                    "receiver_id": {"type": "string", "minLength": 1, "maxLength": 200},
                    "received_at": {"type": "string", "format": "date-time"},
                    "return_id": {"type": "string", "pattern": "^A2-RQ-RET-[A-Z0-9][A-Z0-9_-]{5,79}$"},
                    "signal_snapshot_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                    "rejection_reasons": {"type": "array", "items": {"type": "string", "minLength": 1, "maxLength": 1000}, "uniqueItems": True},
                },
            },
            "constraints": {
                "type": "object", "additionalProperties": False,
                "required": ["a2_replacement_score_prohibited", "a2_points_prohibited", "preserve_original_score_snapshot", "human_approval_required", "crm_write_authorized"],
                "properties": {
                    "a2_replacement_score_prohibited": {"const": True},
                    "a2_points_prohibited": {"const": True},
                    "preserve_original_score_snapshot": {"const": True},
                    "human_approval_required": {"const": True},
                    "crm_write_authorized": {"const": False},
                },
            },
        },
    }


def build_revision_schema() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": REVISION_ID,
        "title": "Equinet A1 Score Revision Reference Stored by A2",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version", "score_revision_id", "a1_candidate_id", "prior_revision_id",
            "source_requalification_return_id", "source_signal_ids", "produced_by_profile",
            "calculation_method", "scoring_model_version", "icp_config_version",
            "evidence_policy_version", "validated_evidence_ids", "criteria_changes",
            "prior_scoring", "revised_scoring", "calculated_at", "revision_status",
            "review", "result_reference", "result_sha256", "audit_correlation_id", "synthetic",
        ],
        "properties": {
            "schema_version": {"const": VERSION},
            "score_revision_id": {"type": "string", "pattern": "^A1-SCORE-REV-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "a1_candidate_id": {"type": "string", "pattern": "^A1-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "prior_revision_id": {"type": ["string", "null"], "maxLength": 100},
            "source_requalification_return_id": {"type": "string", "pattern": "^A2-RQ-RET-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "source_signal_ids": {"type": "array", "minItems": 1, "items": {"type": "string", "pattern": "^A2-RQ-SIG-[A-Z0-9][A-Z0-9_-]{5,79}$"}, "uniqueItems": True},
            "produced_by_profile": {"const": "equinet-a1-icp-discovery"},
            "calculation_method": {"const": "deterministic_a1_scoring"},
            "scoring_model_version": {"const": "1.0.0"},
            "icp_config_version": {"const": "1.0.0"},
            "evidence_policy_version": {"const": "1.0.0"},
            "validated_evidence_ids": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}, "uniqueItems": True},
            "criteria_changes": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/criterionChange"}},
            "prior_scoring": {"$ref": f"{A1_SCHEMA_ID}#/$defs/scoring"},
            "revised_scoring": {"$ref": f"{A1_SCHEMA_ID}#/$defs/scoring"},
            "calculated_at": {"type": "string", "format": "date-time"},
            "revision_status": {"type": "string", "enum": ["proposed_by_a1", "approved", "rejected", "superseded", "error"]},
            "review": {"anyOf": [{"$ref": "#/$defs/review"}, {"type": "null"}]},
            "result_reference": {"type": "string", "minLength": 1, "maxLength": 500},
            "result_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            "audit_correlation_id": {"type": "string", "minLength": 6, "maxLength": 200},
            "synthetic": {"type": "boolean"},
        },
        "allOf": [
            {
                "if": {"properties": {"revision_status": {"const": "approved"}}, "required": ["revision_status"]},
                "then": {"properties": {"review": {"allOf": [{"$ref": "#/$defs/review"}, {"properties": {"decision": {"const": "approved"}}}]}}},
            },
            {
                "if": {"properties": {"revision_status": {"const": "rejected"}}, "required": ["revision_status"]},
                "then": {"properties": {"review": {"allOf": [{"$ref": "#/$defs/review"}, {"properties": {"decision": {"const": "rejected"}}}]}}},
            },
        ],
        "$defs": {
            "actor": actor_schema(),
            "review": review_schema(),
            "criterionChange": {
                "type": "object", "additionalProperties": False,
                "required": ["criterion_id", "before_status", "after_status", "before_evidence_ids", "after_evidence_ids", "source_signal_ids", "change_reason"],
                "properties": {
                    "criterion_id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9_.-]{2,99}$"},
                    "before_status": {"type": "string", "enum": ["confirmed", "not_confirmed", "contradicted", "unknown"]},
                    "after_status": {"type": "string", "enum": ["confirmed", "not_confirmed", "contradicted", "unknown"]},
                    "before_evidence_ids": {"type": "array", "items": {"type": "string", "minLength": 1}, "uniqueItems": True},
                    "after_evidence_ids": {"type": "array", "items": {"type": "string", "minLength": 1}, "uniqueItems": True},
                    "source_signal_ids": {"type": "array", "minItems": 1, "items": {"type": "string", "pattern": "^A2-RQ-SIG-[A-Z0-9][A-Z0-9_-]{5,79}$"}, "uniqueItems": True},
                    "change_reason": {"type": "string", "minLength": 1, "maxLength": 2000},
                },
            },
        },
    }


def build_package_schema() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": PACKAGE_ID,
        "title": "Equinet A2 Requalification Contract Package",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version", "package_id", "operating_scope", "a2_record_id",
            "a2_record_revision_id", "a1_candidate_id", "a1_handoff_id",
            "a1_candidate_snapshot_sha256", "original_scoring", "original_scoring_sha256",
            "signals", "requalification_return", "score_revision_reference",
            "audit_correlation_id", "synthetic",
        ],
        "properties": {
            "schema_version": {"const": VERSION},
            "package_id": {"type": "string", "pattern": "^A2-RQ-PKG-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "operating_scope": {"type": "string", "enum": ["synthetic_test", "manual_no_integration_pilot", "integrated_pilot", "production"]},
            "a2_record_id": {"type": "string", "pattern": "^A2-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "a2_record_revision_id": {"type": "string", "pattern": "^A2-REV-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "a1_candidate_id": {"type": "string", "pattern": "^A1-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "a1_handoff_id": {"type": "string", "pattern": "^A1A2-[A-Z0-9][A-Z0-9_-]{5,79}$"},
            "a1_candidate_snapshot_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            "original_scoring": {"$ref": f"{A1_SCHEMA_ID}#/$defs/scoring"},
            "original_scoring_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            "signals": {"type": "array", "minItems": 1, "items": {"$ref": SIGNAL_ID}},
            "requalification_return": {"anyOf": [{"$ref": RETURN_ID}, {"type": "null"}]},
            "score_revision_reference": {"anyOf": [{"$ref": REVISION_ID}, {"type": "null"}]},
            "audit_correlation_id": {"type": "string", "minLength": 6, "maxLength": 200},
            "synthetic": {"type": "boolean"},
        },
    }


def prior_scoring() -> dict:
    components = [
        ("horse_owner.commercial_operation", 25, "A1-EV-COMMERCIAL"),
        ("horse_owner.purchasing_influence", 15, "A1-EV-INFLUENCE"),
        ("horse_owner.product_fit", 10, "A1-EV-PRODUCT"),
        ("horse_owner.performance_discipline", 8, "A1-EV-DISCIPLINE"),
        ("horse_owner.professional_network", 5, "A1-EV-NETWORK"),
        ("horse_owner.high_equine_activity_location", 5, "A1-EV-LOCATION"),
    ]
    score = sum(points for _, points, _ in components)
    return {
        "status": "scored", "score": score, "band": "medium", "model_version": "1.0.0",
        "components": [
            {"criterion_id": criterion, "points_awarded": points, "max_points": points, "evidence_ids": [evidence], "notes": "Synthetic confirmed component."}
            for criterion, points, evidence in components
        ],
        "rationale": "Synthetic prior score with horse count unknown and no horse-count points awarded.",
        "block_reason": None,
    }


def revised_scoring() -> dict:
    scoring = copy.deepcopy(prior_scoring())
    scoring["components"].append({
        "criterion_id": "horse_owner.more_than_three_horses",
        "points_awarded": 20,
        "max_points": 20,
        "evidence_ids": ["A2-EV-HORSE-COUNT"],
        "notes": "Full V1 weight awarded after A1 accepted returned evidence.",
    })
    scoring["score"] = sum(component["points_awarded"] for component in scoring["components"])
    scoring["band"] = "high"
    scoring["rationale"] = "Synthetic revised score after A1 confirmed more than three horses from returned A2 evidence."
    return scoring


def build_fixtures() -> None:
    reviewer = {"actor_id": "UNITALK-RQ-REVIEWER", "actor_role": "A2 Business Reviewer", "display_name": "Synthetic A2 Reviewer"}
    a1_reviewer = {"actor_id": "UNITALK-A1-REVIEWER", "actor_role": "A1 Business Reviewer", "display_name": "Synthetic A1 Reviewer"}
    snapshot_hash = "a" * 64
    signal = {
        "schema_version": VERSION,
        "signal_id": "A2-RQ-SIG-HORSE_COUNT_001",
        "a2_record_id": "A2-SYNTH_OWNER_001",
        "a2_record_revision_id": "A2-REV-SYNTH_OWNER_002",
        "a1_candidate_id": "A1-SYNTH_OWNER_001",
        "a1_handoff_id": "A1A2-SYNTH_OWNER_001",
        "a1_candidate_snapshot_sha256": snapshot_hash,
        "affected_criterion_id": "horse_owner.more_than_three_horses",
        "prior_criterion_status": "unknown",
        "proposed_evidence_status": "confirmed",
        "a1_evidence_ids": [],
        "a2_evidence_ids": ["A2-EV-HORSE-COUNT"],
        "field_assessment_ids": ["A2-FLD-HORSE-COUNT"],
        "materiality": "high",
        "potential_score_direction": "increase",
        "reason": "An approved direct source explicitly states that the synthetic commercial operation manages more than three horses.",
        "limitations": ["A1 must validate admissibility and recalculate deterministically."],
        "created_by_profile": "equinet-a2-enrichment",
        "created_at": "2026-08-25T20:00:00Z",
        "status": "approved_for_return",
        "review": {"decision": "approved", "reviewer": reviewer, "decided_at": "2026-08-25T20:05:00Z", "reason": "Synthetic signal approved for A1 requalification test."},
        "audit_correlation_id": "AUDIT-RQ-SYNTH-001",
        "synthetic": True,
    }
    farrier_signal = copy.deepcopy(signal)
    farrier_signal.update({
        "signal_id": "A2-RQ-SIG-FARRIER_CERT_001",
        "a2_record_id": "A2-SYNTH_FARRIER_001",
        "a2_record_revision_id": "A2-REV-SYNTH_FARRIER_002",
        "a1_candidate_id": "A1-SYNTH_FARRIER_001",
        "a1_handoff_id": "A1A2-SYNTH_FARRIER_001",
        "affected_criterion_id": "farrier.certified_or_experienced",
        "prior_criterion_status": "unknown",
        "a2_evidence_ids": ["A2-EV-FARRIER-CERT"],
        "field_assessment_ids": ["A2-FLD-FARRIER-CERT"],
        "materiality": "medium",
        "reason": "An approved official registry confirms a current synthetic Farrier certification.",
        "audit_correlation_id": "AUDIT-RQ-SYNTH-002",
    })

    return_doc = {
        "schema_version": VERSION,
        "return_id": "A2-RQ-RET-HORSE_COUNT_001",
        "idempotency_key": "A2-RQ-IDEMP-HORSE_COUNT_001",
        "created_at": "2026-08-25T20:06:00Z",
        "source_profile": "equinet-a2-enrichment",
        "target_profile": "equinet-a1-icp-discovery",
        "operating_scope": "synthetic_test",
        "a2_record_id": signal["a2_record_id"],
        "a2_record_revision_id": signal["a2_record_revision_id"],
        "a1_candidate_id": signal["a1_candidate_id"],
        "a1_handoff_id": signal["a1_handoff_id"],
        "a1_candidate_snapshot_sha256": snapshot_hash,
        "target_icp_config_version": "1.0.0",
        "target_evidence_policy_version": "1.0.0",
        "target_scoring_model_version": "1.0.0",
        "signal_snapshots": [signal],
        "signal_snapshot_sha256": canonical_hash([signal]),
        "status": "accepted_by_a1",
        "approval": {"decision": "approved", "reviewer": reviewer, "decided_at": "2026-08-25T20:05:00Z", "reason": "Synthetic return approved."},
        "delivery": {"external_event_reference": "synthetic://a2-a1/horse-count-001", "attempt_count": 1, "last_attempt_at": "2026-08-25T20:07:00Z", "failure_reason": None},
        "a1_receipt": {"status": "accepted", "receiver_profile": "equinet-a1-icp-discovery", "receiver_id": "A1-SYNTHETIC-RECEIVER", "received_at": "2026-08-25T20:08:00Z", "return_id": "A2-RQ-RET-HORSE_COUNT_001", "signal_snapshot_sha256": canonical_hash([signal]), "rejection_reasons": []},
        "constraints": {"a2_replacement_score_prohibited": True, "a2_points_prohibited": True, "preserve_original_score_snapshot": True, "human_approval_required": True, "crm_write_authorized": False},
        "audit_correlation_id": signal["audit_correlation_id"],
        "synthetic": True,
    }
    prepared_return = copy.deepcopy(return_doc)
    prepared_return.update({"return_id": "A2-RQ-RET-HORSE_COUNT_MANUAL", "idempotency_key": "A2-RQ-IDEMP-HORSE_COUNT_MANUAL", "operating_scope": "manual_no_integration_pilot", "status": "prepared", "a1_receipt": None})
    prepared_return["delivery"] = {"external_event_reference": None, "attempt_count": 0, "last_attempt_at": None, "failure_reason": None}

    prior = prior_scoring()
    revised = revised_scoring()
    revision = {
        "schema_version": VERSION,
        "score_revision_id": "A1-SCORE-REV-HORSE_COUNT_001",
        "a1_candidate_id": signal["a1_candidate_id"],
        "prior_revision_id": "A1-SCORE-ORIGINAL-HORSE_COUNT_001",
        "source_requalification_return_id": return_doc["return_id"],
        "source_signal_ids": [signal["signal_id"]],
        "produced_by_profile": "equinet-a1-icp-discovery",
        "calculation_method": "deterministic_a1_scoring",
        "scoring_model_version": "1.0.0",
        "icp_config_version": "1.0.0",
        "evidence_policy_version": "1.0.0",
        "validated_evidence_ids": ["A2-EV-HORSE-COUNT"],
        "criteria_changes": [{
            "criterion_id": "horse_owner.more_than_three_horses",
            "before_status": "unknown",
            "after_status": "confirmed",
            "before_evidence_ids": [],
            "after_evidence_ids": ["A2-EV-HORSE-COUNT"],
            "source_signal_ids": [signal["signal_id"]],
            "change_reason": "A1 accepted returned direct evidence that the synthetic operation manages more than three horses.",
        }],
        "prior_scoring": prior,
        "revised_scoring": revised,
        "calculated_at": "2026-08-25T20:10:00Z",
        "revision_status": "approved",
        "review": {"decision": "approved", "reviewer": a1_reviewer, "decided_at": "2026-08-25T20:12:00Z", "reason": "Synthetic deterministic score revision approved."},
        "result_reference": "synthetic://a1-score-revision/horse-count-001",
        "result_sha256": canonical_hash(revised),
        "audit_correlation_id": signal["audit_correlation_id"],
        "synthetic": True,
    }

    package = {
        "schema_version": VERSION,
        "package_id": "A2-RQ-PKG-HORSE_COUNT_001",
        "operating_scope": "synthetic_test",
        "a2_record_id": signal["a2_record_id"],
        "a2_record_revision_id": signal["a2_record_revision_id"],
        "a1_candidate_id": signal["a1_candidate_id"],
        "a1_handoff_id": signal["a1_handoff_id"],
        "a1_candidate_snapshot_sha256": snapshot_hash,
        "original_scoring": prior,
        "original_scoring_sha256": canonical_hash(prior),
        "signals": [signal],
        "requalification_return": return_doc,
        "score_revision_reference": revision,
        "audit_correlation_id": signal["audit_correlation_id"],
        "synthetic": True,
    }

    write(VALID / "valid-horse-owner-signal.json", signal)
    write(VALID / "valid-farrier-signal.json", farrier_signal)
    write(VALID / "valid-manual-prepared-return.json", prepared_return)
    write(VALID / "valid-synthetic-requalification-package.json", package)

    rejected_package = copy.deepcopy(package)
    rejected_package["package_id"] = "A2-RQ-PKG-REJECTED_SIGNAL_001"
    rejected_signal = rejected_package["signals"][0]
    rejected_signal["status"] = "rejected"
    rejected_signal["review"] = {"decision": "rejected", "reviewer": reviewer, "decided_at": "2026-08-25T20:05:00Z", "reason": "Synthetic evidence rejected."}
    rejected_package["requalification_return"] = None
    rejected_package["score_revision_reference"] = None
    write(VALID / "valid-rejected-signal-package.json", rejected_package)

    invalids = {}
    with_points = copy.deepcopy(signal)
    with_points["points_awarded"] = 20
    invalids["invalid-signal-with-points.json"] = with_points

    unknown_criterion = copy.deepcopy(signal)
    unknown_criterion["affected_criterion_id"] = "horse_owner.nonexistent_criterion"
    invalids["invalid-unknown-criterion.json"] = unknown_criterion

    missing_evidence = copy.deepcopy(signal)
    missing_evidence["a2_evidence_ids"] = []
    invalids["invalid-signal-missing-evidence.json"] = missing_evidence

    delivered_manual = copy.deepcopy(prepared_return)
    delivered_manual["status"] = "delivered"
    delivered_manual["delivery"] = {"external_event_reference": "fake://delivery", "attempt_count": 1, "last_attempt_at": "2026-08-25T20:07:00Z", "failure_reason": None}
    invalids["invalid-manual-return-delivered.json"] = delivered_manual

    bad_hash_return = copy.deepcopy(return_doc)
    bad_hash_return["signal_snapshot_sha256"] = "0" * 64
    invalids["invalid-return-signal-hash.json"] = bad_hash_return

    a2_revision = copy.deepcopy(revision)
    a2_revision["produced_by_profile"] = "equinet-a2-enrichment"
    invalids["invalid-a2-score-producer.json"] = a2_revision

    score_mismatch = copy.deepcopy(revision)
    score_mismatch["revised_scoring"]["score"] = 99
    score_mismatch["result_sha256"] = canonical_hash(score_mismatch["revised_scoring"])
    invalids["invalid-score-component-total.json"] = score_mismatch

    missing_review = copy.deepcopy(revision)
    missing_review["review"] = None
    invalids["invalid-approved-revision-no-review.json"] = missing_review

    signal_mismatch_package = copy.deepcopy(package)
    signal_mismatch_package["score_revision_reference"]["source_signal_ids"] = ["A2-RQ-SIG-OTHER_001"]
    invalids["invalid-package-signal-mismatch.json"] = signal_mismatch_package

    rejected_with_revision = copy.deepcopy(rejected_package)
    rejected_with_revision["score_revision_reference"] = copy.deepcopy(revision)
    invalids["invalid-rejected-signal-with-revision.json"] = rejected_with_revision

    for filename, document in invalids.items():
        write(INVALID / filename, document)


def main() -> None:
    SCHEMAS.mkdir(parents=True, exist_ok=True)
    write(SCHEMAS / "a2-requalification-signal.schema.json", build_signal_schema())
    write(SCHEMAS / "a2-requalification-return.schema.json", build_return_schema())
    write(SCHEMAS / "a1-score-revision-reference.schema.json", build_revision_schema())
    write(SCHEMAS / "a2-requalification-package.schema.json", build_package_schema())
    build_fixtures()
    print(json.dumps({
        "version": VERSION,
        "schemas": 4,
        "valid_fixtures": len(list(VALID.glob("*.json"))),
        "invalid_fixtures": len(list(INVALID.glob("*.json"))),
        "output": str(SCHEMAS),
    }, indent=2))


if __name__ == "__main__":
    main()
