#!/usr/bin/env python3
"""Build the promoted Step 2I canonical A2 schema and smoke fixtures."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = PROFILE_ROOT / "foundations" / "contracts"
SCHEMA_DIR = CONTRACTS / "canonical"
EXAMPLES = SCHEMA_DIR / "examples"
VALID = EXAMPLES / "valid"
INVALID = EXAMPLES / "invalid"
STATE_MODEL_PATH = CONTRACTS / "a2-state-model-0.1.0.json"
HANDOFF_SCHEMA_PATH = CONTRACTS / "a1-to-a2-handoff.schema.json"
HANDOFF_FIXTURE_PATH = CONTRACTS / "examples" / "valid" / "valid-horse-owner-handoff.json"
REQUALIFICATION_DIR = CONTRACTS / "requalification"

VERSION = "1.0.0"
SCHEMA_ID = f"https://unitalk.ai/schemas/equinet/a2/enrichment-record/{VERSION}"
HANDOFF_SCHEMA_ID = "https://unitalk.ai/schemas/equinet/a1-a2/handoff/1.0.1"
SIGNAL_SCHEMA_ID = "https://unitalk.ai/schemas/equinet/a2/requalification-signal/0.1.0"
RETURN_SCHEMA_ID = "https://unitalk.ai/schemas/equinet/a2/requalification-return/0.1.0"
REVISION_SCHEMA_ID = "https://unitalk.ai/schemas/equinet/a2/a1-score-revision-reference/0.1.0"


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def obj(properties: dict, required: list[str] | None = None, **extra) -> dict:
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
    }
    if required is not None:
        schema["required"] = required
    schema.update(extra)
    return schema


def nullable(schema: dict) -> dict:
    return {"anyOf": [schema, {"type": "null"}]}


def text(min_length: int = 1, max_length: int = 1000) -> dict:
    return {"type": "string", "minLength": min_length, "maxLength": max_length}


def nullable_text(max_length: int = 1000) -> dict:
    return {"type": ["string", "null"], "maxLength": max_length}


def string_array(pattern: str | None = None, min_items: int = 0, nullable_array: bool = False) -> dict:
    item = {"type": "string", "minLength": 1, "maxLength": 500}
    if pattern:
        item["pattern"] = pattern
        item.pop("minLength", None)
    array = {"type": "array", "minItems": min_items, "items": item, "uniqueItems": True}
    return nullable(array) if nullable_array else array


def values(state_model: dict, vocabulary: str) -> list[str]:
    return [entry["value"] for entry in state_model["canonical_vocabularies"][vocabulary]["values"]]


def enum_schema(state_model: dict, vocabulary: str) -> dict:
    return {"type": "string", "enum": values(state_model, vocabulary)}


def build_schema(state_model: dict) -> dict:
    e = lambda name: enum_schema(state_model, name)
    dt = {"type": "string", "format": "date-time"}
    ndt = {"type": ["string", "null"], "format": "date-time"}
    identifier = {"type": "string", "pattern": "^[A-Z0-9][A-Z0-9_.:-]{5,199}$"}
    a2_record_id = {"type": "string", "pattern": "^A2-[A-Z0-9][A-Z0-9_-]{5,79}$"}
    a2_revision_id = {"type": "string", "pattern": "^A2-REV-[A-Z0-9][A-Z0-9_-]{5,79}$"}
    evidence_id = {"type": "string", "pattern": "^A2-EV-[A-Z0-9_-]{3,80}$"}
    assessment_id = {"type": "string", "pattern": "^A2-FLD-[A-Z0-9_-]{3,80}$"}

    actor = obj(
        {
            "actor_id": text(max_length=200),
            "actor_role": text(max_length=200),
            "display_name": nullable_text(200),
            "profile_id": nullable_text(200),
            "workflow_id": nullable_text(200),
        },
        ["actor_id", "actor_role", "display_name", "profile_id", "workflow_id"],
    )
    error = obj(
        {
            "code": text(max_length=100),
            "message": text(max_length=2000),
            "retryable": {"type": "boolean"},
            "occurred_at": dt,
            "details": string_array(min_items=0),
        },
        ["code", "message", "retryable", "occurred_at", "details"],
    )
    canonical_value = {
        "description": "Generic value shape. Permitted type, units and component keys are controlled by the separate Field Catalogue.",
        "oneOf": [
            {"type": "string", "maxLength": 10000},
            {"type": "number"},
            {"type": "boolean"},
            {
                "type": "array",
                "maxItems": 200,
                "items": {"type": ["string", "number", "boolean", "null"]},
            },
            obj(
                {
                    "components": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 100,
                        "items": obj(
                            {
                                "key": {"type": "string", "pattern": "^[a-z][a-z0-9_.-]{1,99}$"},
                                "value": {"type": ["string", "number", "boolean", "null"]},
                            },
                            ["key", "value"],
                        ),
                    }
                },
                ["components"],
            ),
        ],
    }
    value_or_null = nullable({"$ref": "#/$defs/canonicalValue"})

    external_match = obj(
        {
            "match_id": identifier,
            "system": text(max_length=100),
            "object_type": nullable_text(100),
            "external_record_id": nullable_text(300),
            "status": e("entity_match_status"),
            "checked_at": ndt,
            "evidence_ids": string_array(),
            "reason": nullable_text(1000),
        },
        ["match_id", "system", "object_type", "external_record_id", "status", "checked_at", "evidence_ids", "reason"],
    )
    entity = obj(
        {
            "entity_id": {"type": "string", "pattern": "^A2-ENT-[A-Z0-9_-]{3,80}$"},
            "entity_type": e("entity_type"),
            "source_identity_reference": nullable_text(500),
            "display_name": text(max_length=500),
            "aliases": string_array(),
            "match_status": e("entity_match_status"),
            "external_matches": {"type": "array", "items": external_match},
        },
        ["entity_id", "entity_type", "source_identity_reference", "display_name", "aliases", "match_status", "external_matches"],
    )
    relationship = obj(
        {
            "relationship_id": {"type": "string", "pattern": "^A2-REL-[A-Z0-9_-]{3,80}$"},
            "from_entity_id": {"type": "string", "pattern": "^A2-ENT-[A-Z0-9_-]{3,80}$"},
            "to_entity_id": {"type": "string", "pattern": "^A2-ENT-[A-Z0-9_-]{3,80}$"},
            "relationship_type": {"type": "string", "pattern": "^[a-z][a-z0-9_.-]{1,99}$"},
            "evidence_ids": string_array(min_items=1),
        },
        ["relationship_id", "from_entity_id", "to_entity_id", "relationship_type", "evidence_ids"],
    )
    origin = obj(
        {
            "system": text(max_length=100),
            "record_reference": nullable_text(500),
            "field_reference": nullable_text(500),
            "source_kind": {"type": "string", "enum": ["a1_handoff", "hubspot", "twenty", "prior_a2_revision", "human_correction", "approved_file", "other_authorised_source"]},
        },
        ["system", "record_reference", "field_reference", "source_kind"],
    )
    baseline = obj(
        {
            "value": value_or_null,
            "normalised_value": value_or_null,
            "origin": origin,
            "observed_at": ndt,
            "evidence_ids": string_array(),
            "protected_status": e("protected_field_status"),
        },
        ["value", "normalised_value", "origin", "observed_at", "evidence_ids", "protected_status"],
    )
    observation = obj(
        {
            "observation_id": {"type": "string", "pattern": "^A2-OBS-[A-Z0-9_-]{3,80}$"},
            "raw_value": value_or_null,
            "normalised_value": value_or_null,
            "evidence_ids": string_array(min_items=1),
            "verification_status": e("verification_status"),
            "confidence_level": e("confidence_level"),
            "freshness_status": e("freshness_status"),
            "claim_type": e("claim_type"),
            "error": nullable({"$ref": "#/$defs/error"}),
        },
        ["observation_id", "raw_value", "normalised_value", "evidence_ids", "verification_status", "confidence_level", "freshness_status", "claim_type", "error"],
    )
    proposal = obj(
        {
            "action": e("proposal_action"),
            "value": value_or_null,
            "normalised_value": value_or_null,
            "evidence_ids": string_array(),
            "rationale": text(max_length=3000),
            "verification_status": e("verification_status"),
            "confidence_level": e("confidence_level"),
            "freshness_status": e("freshness_status"),
            "conflict_status": e("conflict_status"),
            "protected_status": e("protected_field_status"),
        },
        ["action", "value", "normalised_value", "evidence_ids", "rationale", "verification_status", "confidence_level", "freshness_status", "conflict_status", "protected_status"],
    )
    field_review = obj(
        {
            "decision": e("field_review_decision"),
            "reviewer": nullable({"$ref": "#/$defs/actor"}),
            "decided_at": ndt,
            "reason": nullable_text(2000),
            "corrected_value": value_or_null,
        },
        ["decision", "reviewer", "decided_at", "reason", "corrected_value"],
        allOf=[
            {
                "if": {"properties": {"decision": {"enum": ["approved", "rejected", "needs_changes", "held"]}}, "required": ["decision"]},
                "then": {"properties": {"reviewer": {"$ref": "#/$defs/actor"}, "decided_at": dt, "reason": text(max_length=2000)}},
            },
            {
                "if": {"properties": {"decision": {"enum": ["pending", "not_required"]}}, "required": ["decision"]},
                "then": {"properties": {"reviewer": {"type": "null"}, "decided_at": {"type": "null"}}},
            },
        ],
    )
    application = obj(
        {
            "status": e("application_status"),
            "destination": nullable_text(500),
            "external_action_reference": nullable_text(500),
            "workflow_dependency_status": e("workflow_dependency_status"),
            "applied_at": ndt,
            "error": nullable({"$ref": "#/$defs/error"}),
        },
        ["status", "destination", "external_action_reference", "workflow_dependency_status", "applied_at", "error"],
        allOf=[
            {
                "if": {"properties": {"status": {"enum": ["applied", "reconciled"]}}, "required": ["status"]},
                "then": {"properties": {"destination": text(max_length=500), "external_action_reference": text(max_length=500), "applied_at": dt, "workflow_dependency_status": {"enum": ["verified_no_side_effect", "verified_managed_side_effect"]}}},
            }
        ],
    )
    field_assessment = obj(
        {
            "field_assessment_id": assessment_id,
            "field_key": {"type": "string", "pattern": "^[a-z][a-z0-9_.-]{2,199}$"},
            "entity_id": {
                "description": "Target entity ID, relationship ID, or null for record scope. The field name is retained for compatibility with the approved Step 2B dictionary.",
                "anyOf": [
                    {"type": "string", "pattern": "^A2-ENT-[A-Z0-9_-]{3,80}$"},
                    {"type": "string", "pattern": "^A2-REL-[A-Z0-9_-]{3,80}$"},
                    {"type": "null"},
                ],
            },
            "scope": e("field_scope"),
            "field_catalogue_version": text(max_length=100),
            "value_type": text(max_length=100),
            "sensitivity_classification": text(max_length=100),
            "presence_status": e("value_presence_status"),
            "availability_status": e("availability_status"),
            "field_quality_status": e("field_quality_status"),
            "baseline": nullable({"$ref": "#/$defs/baseline"}),
            "observations": {"type": "array", "items": {"$ref": "#/$defs/observation"}},
            "proposed_resolution": nullable({"$ref": "#/$defs/proposal"}),
            "field_review": {"$ref": "#/$defs/fieldReview"},
            "application": {"$ref": "#/$defs/application"},
        },
        ["field_assessment_id", "field_key", "entity_id", "scope", "field_catalogue_version", "value_type", "sensitivity_classification", "presence_status", "availability_status", "field_quality_status", "baseline", "observations", "proposed_resolution", "field_review", "application"],
        allOf=[
            {
                "if": {"properties": {"scope": {"const": "record"}}, "required": ["scope"]},
                "then": {"properties": {"entity_id": {"type": "null"}}},
            },
            {
                "if": {"properties": {"scope": {"enum": ["person", "organisation"]}}, "required": ["scope"]},
                "then": {"properties": {"entity_id": {"type": "string", "pattern": "^A2-ENT-[A-Z0-9_-]{3,80}$"}}},
            },
            {
                "if": {"properties": {"scope": {"const": "relationship"}}, "required": ["scope"]},
                "then": {"properties": {"entity_id": {"type": "string", "pattern": "^A2-REL-[A-Z0-9_-]{3,80}$"}}},
            },
        ],
    )
    provider_cost = obj(
        {
            "currency": {"type": ["string", "null"], "pattern": "^[A-Z]{3}$"},
            "amount": {"type": ["number", "null"], "minimum": 0},
            "credits": {"type": ["number", "null"], "minimum": 0},
            "cost_status": {"type": "string", "enum": ["known", "estimated", "unknown", "not_applicable"]},
        },
        ["currency", "amount", "credits", "cost_status"],
    )
    evidence = obj(
        {
            "evidence_id": evidence_id,
            "namespace": e("evidence_namespace"),
            "source_id": text(max_length=200),
            "source_type": text(max_length=100),
            "source_policy_status": e("source_policy_status"),
            "source_url": {"type": ["string", "null"], "format": "uri", "maxLength": 2000},
            "provider_reference": nullable_text(500),
            "access_method": text(max_length=100),
            "retrieved_at": dt,
            "source_date": {"type": ["string", "null"], "anyOf": [{"format": "date"}, {"format": "date-time"}, {"type": "null"}]},
            "title": nullable_text(500),
            "excerpt_or_result_summary": text(max_length=5000),
            "claim_type": e("claim_type"),
            "supports_field_assessment_ids": string_array(pattern="^A2-FLD-[A-Z0-9_-]{3,80}$"),
            "supports_requalification_signal_ids": string_array(pattern="^A2-RQ-SIG-[A-Z0-9][A-Z0-9_-]{5,79}$"),
            "reliability_level": e("reliability_level"),
            "independence_group_id": nullable_text(200),
            "provider_cost": nullable({"$ref": "#/$defs/providerCost"}),
            "supersedes_evidence_id": {"type": ["string", "null"], "pattern": "^A2-EV-[A-Z0-9_-]{3,80}$"},
            "data_minimisation_notes": nullable_text(2000),
        },
        ["evidence_id", "namespace", "source_id", "source_type", "source_policy_status", "source_url", "provider_reference", "access_method", "retrieved_at", "source_date", "title", "excerpt_or_result_summary", "claim_type", "supports_field_assessment_ids", "supports_requalification_signal_ids", "reliability_level", "independence_group_id", "provider_cost", "supersedes_evidence_id", "data_minimisation_notes"],
    )
    match_reference = obj(
        {
            "reference_type": text(max_length=100),
            "reference_id": text(max_length=500),
            "system": text(max_length=100),
            "object_type": nullable_text(100),
        },
        ["reference_type", "reference_id", "system", "object_type"],
    )
    eligibility_check = obj(
        {
            "check_id": identifier,
            "check_type": text(max_length=100),
            "system": text(max_length=100),
            "status": e("duplicate_status"),
            "checked_at": ndt,
            "matches_or_references": {"type": "array", "items": match_reference},
            "reason": nullable_text(2000),
        },
        ["check_id", "check_type", "system", "status", "checked_at", "matches_or_references", "reason"],
    )
    record_review = obj(
        {
            "record_decision": e("record_review_decision"),
            "reviewer": nullable({"$ref": "#/$defs/actor"}),
            "decided_at": ndt,
            "reason": nullable_text(2000),
            "required_field_decisions_complete": {"type": "boolean"},
            "requested_changes": string_array(),
        },
        ["record_decision", "reviewer", "decided_at", "reason", "required_field_decisions_complete", "requested_changes"],
        allOf=[
            {
                "if": {"properties": {"record_decision": {"enum": ["approved", "rejected", "needs_changes", "held", "blocked"]}}, "required": ["record_decision"]},
                "then": {"properties": {"reviewer": {"$ref": "#/$defs/actor"}, "decided_at": dt, "reason": text(max_length=2000)}},
            },
            {
                "if": {"properties": {"record_decision": {"const": "pending"}}, "required": ["record_decision"]},
                "then": {"properties": {"reviewer": {"type": "null"}, "decided_at": {"type": "null"}}},
            },
        ],
    )
    audit_usage = obj(
        {
            "input_tokens": {"type": ["integer", "null"], "minimum": 0},
            "output_tokens": {"type": ["integer", "null"], "minimum": 0},
            "total_tokens": {"type": ["integer", "null"], "minimum": 0},
            "api_calls": {"type": ["integer", "null"], "minimum": 0},
            "credits": {"type": ["number", "null"], "minimum": 0},
            "cost_amount": {"type": ["number", "null"], "minimum": 0},
            "currency": {"type": ["string", "null"], "pattern": "^[A-Z]{3}$"},
            "cost_status": {"type": "string", "enum": ["known", "estimated", "unknown", "not_applicable"]},
        },
        ["input_tokens", "output_tokens", "total_tokens", "api_calls", "credits", "cost_amount", "currency", "cost_status"],
    )
    external_action = obj(
        {
            "action_type": text(max_length=100),
            "destination": text(max_length=200),
            "approval_reference": nullable_text(500),
            "external_reference": nullable_text(500),
            "state": {"type": "string", "enum": ["not_requested", "pending", "succeeded", "failed", "blocked"]},
            "attempt": {"type": "integer", "minimum": 0, "maximum": 100},
        },
        ["action_type", "destination", "approval_reference", "external_reference", "state", "attempt"],
    )
    audit_event = obj(
        {
            "event_id": identifier,
            "event_type": text(max_length=100),
            "actor": {"$ref": "#/$defs/actor"},
            "timestamp": dt,
            "input_references": string_array(),
            "output_references": string_array(),
            "model": nullable_text(300),
            "tools": string_array(),
            "usage": nullable({"$ref": "#/$defs/usage"}),
            "external_action": nullable({"$ref": "#/$defs/externalAction"}),
        },
        ["event_id", "event_type", "actor", "timestamp", "input_references", "output_references", "model", "tools", "usage", "external_action"],
    )
    total_usage = obj(
        {
            "input_tokens": {"type": ["integer", "null"], "minimum": 0},
            "output_tokens": {"type": ["integer", "null"], "minimum": 0},
            "total_tokens": {"type": ["integer", "null"], "minimum": 0},
            "api_calls": {"type": "integer", "minimum": 0},
            "provider_calls": {"type": "integer", "minimum": 0},
            "credits": {"type": ["number", "null"], "minimum": 0},
            "cost_amount": {"type": ["number", "null"], "minimum": 0},
            "currency": {"type": ["string", "null"], "pattern": "^[A-Z]{3}$"},
            "cost_status": {"type": "string", "enum": ["known", "estimated", "unknown", "not_applicable"]},
        },
        ["input_tokens", "output_tokens", "total_tokens", "api_calls", "provider_calls", "credits", "cost_amount", "currency", "cost_status"],
    )
    limits = obj(
        {
            "max_records": {"type": ["integer", "null"], "minimum": 1},
            "max_source_calls": {"type": ["integer", "null"], "minimum": 0},
            "max_provider_calls": {"type": ["integer", "null"], "minimum": 0},
            "max_retries": {"type": ["integer", "null"], "minimum": 0},
            "max_concurrency": {"type": ["integer", "null"], "minimum": 1},
            "max_cost_usd": {"type": ["number", "null"], "minimum": 0},
            "policy_version": nullable_text(100),
        },
        ["max_records", "max_source_calls", "max_provider_calls", "max_retries", "max_concurrency", "max_cost_usd", "policy_version"],
    )

    top_properties = {
        "record_metadata": obj(
            {
                "schema_version": {"const": VERSION},
                "record_kind": e("record_kind"),
                "a2_record_id": a2_record_id,
                "record_revision_id": a2_revision_id,
                "revision_number": {"type": "integer", "minimum": 1},
                "supersedes_revision_id": nullable(a2_revision_id),
                "supersedes_a2_record_id": nullable(a2_record_id),
                "run_id": identifier,
                "audit_correlation_id": text(min_length=6, max_length=200),
                "created_at": dt,
                "created_by": {"$ref": "#/$defs/actor"},
                "change_reason": e("change_reason"),
            },
            ["schema_version", "record_kind", "a2_record_id", "record_revision_id", "revision_number", "supersedes_revision_id", "supersedes_a2_record_id", "run_id", "audit_correlation_id", "created_at", "created_by", "change_reason"],
            allOf=[
                {"if": {"properties": {"revision_number": {"const": 1}}, "required": ["revision_number"]}, "then": {"properties": {"supersedes_revision_id": {"type": "null"}}}},
                {"if": {"properties": {"revision_number": {"minimum": 2}}, "required": ["revision_number"]}, "then": {"properties": {"supersedes_revision_id": a2_revision_id}}},
            ],
        ),
        "source_handoff": obj(
            {
                "handoff_schema_version": {"const": "1.0.1"},
                "handoff_id": {"type": "string", "pattern": "^A1A2-[A-Z0-9][A-Z0-9_-]{5,79}$"},
                "idempotency_key": {"type": "string", "pattern": "^A1A2-IDEMP-[A-Z0-9_-]{6,100}$"},
                "operating_scope": e("operating_scope"),
                "eligibility_status": e("eligibility_status"),
                "accepted_at": dt,
                "accepted_by": {"$ref": "#/$defs/actor"},
                "candidate_snapshot_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                "handoff_snapshot": {"$ref": HANDOFF_SCHEMA_ID},
            },
            ["handoff_schema_version", "handoff_id", "idempotency_key", "operating_scope", "eligibility_status", "accepted_at", "accepted_by", "candidate_snapshot_sha256", "handoff_snapshot"],
        ),
        "subject": obj(
            {
                "identity_resolution_status": e("identity_resolution_status"),
                "entities": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/entity"}},
                "relationships": {"type": "array", "items": {"$ref": "#/$defs/relationship"}},
                "material_conflicts": string_array(),
            },
            ["identity_resolution_status", "entities", "relationships", "material_conflicts"],
        ),
        "enrichment_scope": obj(
            {
                "mode": e("enrichment_mode"),
                "requested_field_keys": string_array(pattern="^[a-z][a-z0-9_.-]{2,199}$"),
                "field_catalogue_version": text(max_length=100),
                "source_register_version": nullable_text(100),
                "operating_scope": e("operating_scope"),
                "limits": {"$ref": "#/$defs/limits"},
                "initiated_by": {"$ref": "#/$defs/actor"},
            },
            ["mode", "requested_field_keys", "field_catalogue_version", "source_register_version", "operating_scope", "limits", "initiated_by"],
            allOf=[
                {"if": {"properties": {"mode": {"const": "default_minimum_package"}}, "required": ["mode"]}, "then": {"properties": {"requested_field_keys": {"maxItems": 0}}}},
                {"if": {"properties": {"mode": {"const": "targeted_fields"}}, "required": ["mode"]}, "then": {"properties": {"requested_field_keys": {"minItems": 1}}}},
            ],
        ),
        "field_assessments": {"type": "array", "items": {"$ref": "#/$defs/fieldAssessment"}},
        "evidence_registry": {"type": "array", "items": {"$ref": "#/$defs/evidence"}},
        "data_quality": obj(
            {
                "status": e("data_quality_status"),
                "method_version": nullable_text(100),
                "calculated_at": ndt,
                "required_field_keys": string_array(pattern="^[a-z][a-z0-9_.-]{2,199}$"),
                "missing_field_keys": string_array(pattern="^[a-z][a-z0-9_.-]{2,199}$"),
                "unverified_field_keys": string_array(pattern="^[a-z][a-z0-9_.-]{2,199}$"),
                "conflict_field_keys": string_array(pattern="^[a-z][a-z0-9_.-]{2,199}$"),
                "stale_field_keys": string_array(pattern="^[a-z][a-z0-9_.-]{2,199}$"),
                "invalid_field_keys": string_array(pattern="^[a-z][a-z0-9_.-]{2,199}$"),
                "limitations": string_array(),
            },
            ["status", "method_version", "calculated_at", "required_field_keys", "missing_field_keys", "unverified_field_keys", "conflict_field_keys", "stale_field_keys", "invalid_field_keys", "limitations"],
        ),
        "duplicate_and_eligibility": obj(
            {
                "checks": {"type": "array", "items": {"$ref": "#/$defs/eligibilityCheck"}},
                "a2_eligibility_status": e("eligibility_status"),
                "outreach_eligibility_status": e("outreach_eligibility_status"),
                "owner_routing_status": e("owner_routing_status"),
                "reasons": string_array(),
                "evaluated_at": ndt,
                "method_version": nullable_text(100),
            },
            ["checks", "a2_eligibility_status", "outreach_eligibility_status", "owner_routing_status", "reasons", "evaluated_at", "method_version"],
        ),
        "requalification": obj(
            {
                "signals": {"type": "array", "items": {"$ref": SIGNAL_SCHEMA_ID}},
                "returns": {"type": "array", "items": {"$ref": RETURN_SCHEMA_ID}},
                "score_revision_references": {"type": "array", "items": {"$ref": REVISION_SCHEMA_ID}},
            },
            ["signals", "returns", "score_revision_references"],
        ),
        "review": record_review,
        "workflow": obj(
            {
                "state": e("workflow_state"),
                "previous_state": nullable(e("workflow_state")),
                "transitioned_at": dt,
                "triggered_by": {"$ref": "#/$defs/actor"},
                "hold_reasons": string_array(),
                "block_reasons": string_array(),
                "failure": nullable({"$ref": "#/$defs/error"}),
            },
            ["state", "previous_state", "transitioned_at", "triggered_by", "hold_reasons", "block_reasons", "failure"],
            allOf=[
                {"if": {"properties": {"state": {"const": "held"}}, "required": ["state"]}, "then": {"properties": {"hold_reasons": {"minItems": 1}}}},
                {"if": {"properties": {"state": {"const": "blocked"}}, "required": ["state"]}, "then": {"properties": {"block_reasons": {"minItems": 1}}}},
                {"if": {"properties": {"state": {"enum": ["processing_failed", "sync_failed"]}}, "required": ["state"]}, "then": {"properties": {"failure": {"$ref": "#/$defs/error"}}}},
            ],
        ),
        "system_references": obj(
            {
                "a1_candidate_id": {"type": "string", "pattern": "^A1-[A-Z0-9][A-Z0-9_-]{5,79}$"},
                "a1_handoff_id": {"type": "string", "pattern": "^A1A2-[A-Z0-9][A-Z0-9_-]{5,79}$"},
                "twenty_record_id": nullable_text(300),
                "hubspot_contact_id": nullable_text(300),
                "hubspot_company_id": nullable_text(300),
                "hubspot_deal_ids": string_array(nullable_array=True),
                "hubspot_proposed_patch_id": nullable_text(300),
                "hubspot_sync_id": nullable_text(300),
                "n8n_work_item_id": nullable_text(300),
                "n8n_execution_id": nullable_text(300),
                "provider_request_ids": string_array(nullable_array=True),
                "a3_handoff_id": nullable_text(300),
                "a14_handoff_id": nullable_text(300),
                "requalification_return_id": nullable_text(300),
                "a1_score_revision_id": nullable_text(300),
            },
            ["a1_candidate_id", "a1_handoff_id", "twenty_record_id", "hubspot_contact_id", "hubspot_company_id", "hubspot_deal_ids", "hubspot_proposed_patch_id", "hubspot_sync_id", "n8n_work_item_id", "n8n_execution_id", "provider_request_ids", "a3_handoff_id", "a14_handoff_id", "requalification_return_id", "a1_score_revision_id"],
        ),
        "governance": obj(
            {
                "processing_purpose": text(max_length=1000),
                "contains_personal_data": {"type": "boolean"},
                "data_categories": string_array(),
                "source_register_version": nullable_text(100),
                "source_terms_review_status": e("source_policy_status"),
                "retention_policy_version": nullable_text(100),
                "approval_matrix_version": nullable_text(100),
                "consent_check_status": e("outreach_eligibility_status"),
                "outreach_authorized": {"type": "boolean"},
                "crm_write_authorized": {"type": "boolean"},
                "provider_use_authorized": {"type": "boolean"},
                "policy_limitations": string_array(),
            },
            ["processing_purpose", "contains_personal_data", "data_categories", "source_register_version", "source_terms_review_status", "retention_policy_version", "approval_matrix_version", "consent_check_status", "outreach_authorized", "crm_write_authorized", "provider_use_authorized", "policy_limitations"],
        ),
        "audit_and_consumption": obj(
            {
                "events": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/auditEvent"}},
                "total_usage": {"$ref": "#/$defs/totalUsage"},
                "errors": {"type": "array", "items": {"$ref": "#/$defs/error"}},
            },
            ["events", "total_usage", "errors"],
        ),
    }

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_ID,
        "title": "Equinet A2 Canonical Enrichment Record",
        "description": "Strict canonical record for immutable Equinet A2 Enrichment revisions. Business field catalogue, source policy and CRM mappings are external versioned configurations.",
        "type": "object",
        "additionalProperties": False,
        "required": list(top_properties.keys()),
        "properties": top_properties,
        "allOf": [
            {
                "if": {"properties": {"record_metadata": {"properties": {"record_kind": {"const": "synthetic_test"}}}}, "required": ["record_metadata"]},
                "then": {"properties": {"source_handoff": {"properties": {"operating_scope": {"const": "synthetic_test"}}}, "enrichment_scope": {"properties": {"operating_scope": {"const": "synthetic_test"}}}}},
            },
            {
                "if": {"properties": {"source_handoff": {"properties": {"operating_scope": {"const": "manual_no_integration_pilot"}}}}, "required": ["source_handoff"]},
                "then": {
                    "properties": {
                        "enrichment_scope": {"properties": {"operating_scope": {"const": "manual_no_integration_pilot"}}},
                        "workflow": {"properties": {"state": {"not": {"enum": ["ready_for_sync", "sync_pending", "synced", "reconciled"]}}}},
                        "governance": {"properties": {"outreach_authorized": {"const": False}, "crm_write_authorized": {"const": False}, "provider_use_authorized": {"const": False}}},
                        "system_references": {"properties": {
                            "twenty_record_id": {"type": "null"}, "hubspot_contact_id": {"type": "null"}, "hubspot_company_id": {"type": "null"},
                            "hubspot_deal_ids": {"type": "null"}, "hubspot_proposed_patch_id": {"type": "null"}, "hubspot_sync_id": {"type": "null"},
                            "n8n_work_item_id": {"type": "null"}, "n8n_execution_id": {"type": "null"}, "provider_request_ids": {"type": "null"},
                            "a3_handoff_id": {"type": "null"}, "a14_handoff_id": {"type": "null"}, "requalification_return_id": {"type": "null"}, "a1_score_revision_id": {"type": "null"}
                        }},
                    }
                },
            },
            {
                "if": {"properties": {"workflow": {"properties": {"state": {"enum": ["synced", "reconciled"]}}}}, "required": ["workflow"]},
                "then": {"properties": {"system_references": {"properties": {"hubspot_sync_id": text(max_length=300)}}, "governance": {"properties": {"crm_write_authorized": {"const": True}}}}},
            },
            {
                "if": {"properties": {"workflow": {"properties": {"state": {"const": "record_approved"}}}}, "required": ["workflow"]},
                "then": {"properties": {"review": {"properties": {"record_decision": {"const": "approved"}, "required_field_decisions_complete": {"const": True}}}}},
            },
        ],
        "$defs": {
            "actor": actor,
            "error": error,
            "canonicalValue": canonical_value,
            "entity": entity,
            "relationship": relationship,
            "baseline": baseline,
            "observation": observation,
            "proposal": proposal,
            "fieldReview": field_review,
            "application": application,
            "fieldAssessment": field_assessment,
            "providerCost": provider_cost,
            "evidence": evidence,
            "eligibilityCheck": eligibility_check,
            "usage": audit_usage,
            "externalAction": external_action,
            "auditEvent": audit_event,
            "totalUsage": total_usage,
            "limits": limits,
        },
        "x-unitalk-contract": {
            "status": "promoted_by_unitalk_in_step_2i",
            "canonical_sections": list(top_properties.keys()),
            "external_configurations": [
                "business_field_catalogue",
                "minimum_data_packages",
                "source_and_provider_policy",
                "confidence_and_freshness_rules",
                "protected_field_catalogue",
                "approval_matrix",
                "hubspot_twenty_crm_mapping",
                "retention_and_deletion_policy",
            ],
            "cross_field_validator_step": "2E",
        },
    }
    return schema


def base_record(handoff: dict) -> dict:
    candidate = handoff["candidate_snapshot"]
    actor = {
        "actor_id": "UNITALK-A2-SCHEMA-TEST",
        "actor_role": "A2 Contract Test Runtime",
        "display_name": "Synthetic A2 Runtime",
        "profile_id": "equinet-a2-enrichment",
        "workflow_id": None,
    }
    entity_type = "organisation" if candidate["identity"]["organisation"] else "person"
    return {
        "record_metadata": {
            "schema_version": VERSION,
            "record_kind": "synthetic_test",
            "a2_record_id": "A2-SYNTH_OWNER_001",
            "record_revision_id": "A2-REV-SYNTH_OWNER_001",
            "revision_number": 1,
            "supersedes_revision_id": None,
            "supersedes_a2_record_id": None,
            "run_id": "A2-RUN-SCHEMA-001",
            "audit_correlation_id": handoff["provenance"]["audit_correlation_id"],
            "created_at": "2026-08-26T10:00:00Z",
            "created_by": actor,
            "change_reason": "initialisation",
        },
        "source_handoff": {
            "handoff_schema_version": handoff["handoff_schema_version"],
            "handoff_id": handoff["handoff_id"],
            "idempotency_key": handoff["idempotency_key"],
            "operating_scope": handoff["operating_scope"],
            "eligibility_status": handoff["eligibility"]["status"],
            "accepted_at": handoff["a2_receipt"]["received_at"],
            "accepted_by": actor,
            "candidate_snapshot_sha256": handoff["snapshot_integrity"]["candidate_snapshot_sha256"],
            "handoff_snapshot": handoff,
        },
        "subject": {
            "identity_resolution_status": "resolved",
            "entities": [{
                "entity_id": "A2-ENT-OWNER_ORG_001",
                "entity_type": entity_type,
                "source_identity_reference": "candidate_snapshot.identity.organisation",
                "display_name": candidate["identity"]["display_name"],
                "aliases": [],
                "match_status": "not_checked",
                "external_matches": [],
            }],
            "relationships": [],
            "material_conflicts": [],
        },
        "enrichment_scope": {
            "mode": "default_minimum_package",
            "requested_field_keys": [],
            "field_catalogue_version": "unitalk-placeholder-0.0.0",
            "source_register_version": None,
            "operating_scope": "synthetic_test",
            "limits": {"max_records": 1, "max_source_calls": 0, "max_provider_calls": 0, "max_retries": 0, "max_concurrency": 1, "max_cost_usd": 0, "policy_version": None},
            "initiated_by": actor,
        },
        "field_assessments": [],
        "evidence_registry": [],
        "data_quality": {
            "status": "unassessed", "method_version": None, "calculated_at": None,
            "required_field_keys": [], "missing_field_keys": [], "unverified_field_keys": [],
            "conflict_field_keys": [], "stale_field_keys": [], "invalid_field_keys": [],
            "limitations": ["Business Field Catalogue and quality method are not yet approved."],
        },
        "duplicate_and_eligibility": {
            "checks": [], "a2_eligibility_status": "not_checked", "outreach_eligibility_status": "unavailable",
            "owner_routing_status": "needs_owner_review", "reasons": ["HubSpot is not connected."],
            "evaluated_at": None, "method_version": None,
        },
        "requalification": {"signals": [], "returns": [], "score_revision_references": []},
        "review": {"record_decision": "pending", "reviewer": None, "decided_at": None, "reason": None, "required_field_decisions_complete": False, "requested_changes": []},
        "workflow": {"state": "initialised", "previous_state": None, "transitioned_at": "2026-08-26T10:00:00Z", "triggered_by": actor, "hold_reasons": [], "block_reasons": [], "failure": None},
        "system_references": {
            "a1_candidate_id": candidate["candidate_id"], "a1_handoff_id": handoff["handoff_id"],
            "twenty_record_id": None, "hubspot_contact_id": None, "hubspot_company_id": None,
            "hubspot_deal_ids": None, "hubspot_proposed_patch_id": None, "hubspot_sync_id": None,
            "n8n_work_item_id": None, "n8n_execution_id": None, "provider_request_ids": None,
            "a3_handoff_id": None, "a14_handoff_id": None, "requalification_return_id": None,
            "a1_score_revision_id": None,
        },
        "governance": {
            "processing_purpose": "Synthetic schema validation only.", "contains_personal_data": False,
            "data_categories": ["synthetic_business_information"], "source_register_version": None,
            "source_terms_review_status": "unavailable", "retention_policy_version": None,
            "approval_matrix_version": None, "consent_check_status": "unavailable",
            "outreach_authorized": False, "crm_write_authorized": False,
            "provider_use_authorized": False,
            "policy_limitations": ["No live source, provider, CRM or workflow connection is authorised."],
        },
        "audit_and_consumption": {
            "events": [{
                "event_id": "A2-EVENT-SCHEMA-001", "event_type": "canonical_record_initialised",
                "actor": actor, "timestamp": "2026-08-26T10:00:00Z",
                "input_references": [handoff["handoff_id"]], "output_references": ["A2-REV-SYNTH_OWNER_001"],
                "model": None, "tools": ["deterministic-schema-fixture-builder"], "usage": None,
                "external_action": None,
            }],
            "total_usage": {"input_tokens": None, "output_tokens": None, "total_tokens": None, "api_calls": 0, "provider_calls": 0, "credits": 0, "cost_amount": 0, "currency": "USD", "cost_status": "known"},
            "errors": [],
        },
    }


def build_fixtures() -> None:
    handoff = json.loads(HANDOFF_FIXTURE_PATH.read_text(encoding="utf-8"))
    minimal = base_record(handoff)
    write(VALID / "valid-synthetic-initialised-record.json", minimal)

    enriched = copy.deepcopy(minimal)
    enriched["record_metadata"].update({"record_revision_id": "A2-REV-SYNTH_OWNER_002", "revision_number": 2, "supersedes_revision_id": "A2-REV-SYNTH_OWNER_001", "change_reason": "enrichment"})
    enriched["workflow"].update({"state": "review_required", "previous_state": "enrichment_in_progress", "transitioned_at": "2026-08-26T10:10:00Z"})
    enriched["field_assessments"] = [{
        "field_assessment_id": "A2-FLD-HORSE-COUNT",
        "field_key": "organisation.horse_count",
        "entity_id": "A2-ENT-OWNER_ORG_001",
        "scope": "organisation",
        "field_catalogue_version": "unitalk-placeholder-0.0.0",
        "value_type": "integer",
        "sensitivity_classification": "professional_business_data",
        "presence_status": "known",
        "availability_status": "available",
        "field_quality_status": "partial",
        "baseline": None,
        "observations": [{
            "observation_id": "A2-OBS-HORSE-COUNT-001", "raw_value": "More than three horses",
            "normalised_value": 4, "evidence_ids": ["A2-EV-HORSE-COUNT"],
            "verification_status": "partially_verified", "confidence_level": "medium",
            "freshness_status": "undated", "claim_type": "direct_fact", "error": None,
        }],
        "proposed_resolution": {
            "action": "add", "value": 4, "normalised_value": 4,
            "evidence_ids": ["A2-EV-HORSE-COUNT"],
            "rationale": "Synthetic direct evidence supports a minimum value pending the approved horse-count taxonomy.",
            "verification_status": "partially_verified", "confidence_level": "medium",
            "freshness_status": "undated", "conflict_status": "none", "protected_status": "not_protected",
        },
        "field_review": {"decision": "pending", "reviewer": None, "decided_at": None, "reason": None, "corrected_value": None},
        "application": {"status": "not_requested", "destination": None, "external_action_reference": None, "workflow_dependency_status": "not_checked", "applied_at": None, "error": None},
    }]
    enriched["evidence_registry"] = [{
        "evidence_id": "A2-EV-HORSE-COUNT", "namespace": "a2", "source_id": "synthetic_fixture_source",
        "source_type": "synthetic_business_website", "source_policy_status": "approved",
        "source_url": "https://example.com/lexington-breeding-farm", "provider_reference": None,
        "access_method": "synthetic_fixture", "retrieved_at": "2026-08-26T10:05:00Z", "source_date": None,
        "title": "Synthetic Horse Count Evidence", "excerpt_or_result_summary": "Synthetic fixture states more than three horses.",
        "claim_type": "direct_fact", "supports_field_assessment_ids": ["A2-FLD-HORSE-COUNT"],
        "supports_requalification_signal_ids": [], "reliability_level": "medium",
        "independence_group_id": None, "provider_cost": None, "supersedes_evidence_id": None,
        "data_minimisation_notes": "Synthetic fixture only.",
    }]
    enriched["data_quality"].update({"status": "needs_review", "calculated_at": "2026-08-26T10:10:00Z", "unverified_field_keys": ["organisation.horse_count"], "limitations": ["Horse-count taxonomy remains unapproved."]})
    write(VALID / "valid-synthetic-enriched-record.json", enriched)

    extra_root = copy.deepcopy(minimal)
    extra_root["unexpected"] = True
    write(INVALID / "invalid-extra-root-property.json", extra_root)

    extra_nested = copy.deepcopy(minimal)
    extra_nested["record_metadata"]["current"] = True
    write(INVALID / "invalid-extra-nested-property.json", extra_nested)

    wrong_version = copy.deepcopy(minimal)
    wrong_version["record_metadata"]["schema_version"] = "9.9.9-invalid"
    write(INVALID / "invalid-schema-version.json", wrong_version)

    manual_sync = copy.deepcopy(minimal)
    manual_sync["record_metadata"]["record_kind"] = "production"
    manual_sync["source_handoff"]["operating_scope"] = "manual_no_integration_pilot"
    manual_sync["source_handoff"]["handoff_snapshot"]["operating_scope"] = "manual_no_integration_pilot"
    manual_sync["source_handoff"]["handoff_snapshot"]["delivery_state"] = "ready_for_delivery"
    manual_sync["source_handoff"]["handoff_snapshot"]["a2_receipt"] = None
    manual_sync["enrichment_scope"]["operating_scope"] = "manual_no_integration_pilot"
    manual_sync["workflow"]["state"] = "synced"
    manual_sync["system_references"]["hubspot_sync_id"] = "FAKE-SYNC"
    manual_sync["governance"]["crm_write_authorized"] = True
    write(INVALID / "invalid-no-integration-sync.json", manual_sync)

    bad_score = copy.deepcopy(enriched)
    signal = json.loads((REQUALIFICATION_DIR / "examples" / "valid" / "valid-horse-owner-signal.json").read_text(encoding="utf-8"))
    signal["a2_record_revision_id"] = enriched["record_metadata"]["record_revision_id"]
    signal["points_awarded"] = 20
    bad_score["requalification"]["signals"] = [signal]
    write(INVALID / "invalid-a2-score-field.json", bad_score)


def build_manifest(schema_path: Path) -> dict:
    dependencies = [
        PROFILE_ROOT / "foundations" / "A2-CANONICAL-RECORD-DESIGN.md",
        CONTRACTS / "a2-field-dictionary-0.1.0.csv",
        STATE_MODEL_PATH,
        HANDOFF_SCHEMA_PATH,
        REQUALIFICATION_DIR / "a2-requalification-signal.schema.json",
        REQUALIFICATION_DIR / "a2-requalification-return.schema.json",
        REQUALIFICATION_DIR / "a1-score-revision-reference.schema.json",
        CONTRACTS / "dependencies" / "a1-prospect-candidate.schema.json",
    ]
    return {
        "manifest_id": "equinet-a2-canonical-schema-dependencies",
        "schema_version": VERSION,
        "status": "promoted_by_unitalk_in_step_2i",
        "schema_path": str(schema_path.relative_to(PROFILE_ROOT)),
        "schema_sha256": sha256(schema_path),
        "dependencies": [
            {"path": str(path.relative_to(PROFILE_ROOT)), "sha256": sha256(path)} for path in dependencies
        ],
    }


def main() -> None:
    state_model = json.loads(STATE_MODEL_PATH.read_text(encoding="utf-8"))
    schema_path = SCHEMA_DIR / "a2-enrichment-record.schema.json"
    write(schema_path, build_schema(state_model))
    build_fixtures()
    write(SCHEMA_DIR / "a2-enrichment-record.dependency-manifest.json", build_manifest(schema_path))
    print(json.dumps({
        "schema": str(schema_path),
        "version": VERSION,
        "valid_smoke_fixtures": len(list(VALID.glob("*.json"))),
        "invalid_smoke_fixtures": len(list(INVALID.glob("*.json"))),
        "manifest": str(SCHEMA_DIR / "a2-enrichment-record.dependency-manifest.json"),
    }, indent=2))


if __name__ == "__main__":
    main()
