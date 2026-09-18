#!/usr/bin/env python3
"""Record Séverine's final Rood & Riddle Step 8 decisions and validate the held revision."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_a2_enrichment_record import validate

BASE = ROOT / "evaluations/step8/pilot/A1-RR-PODIATRY-001"
PREVIOUS_PATH = BASE / "canonical/revision-004-review-required.json"
OUTPUT_PATH = BASE / "canonical/revision-005-held.json"
MANIFEST_PATH = BASE / "canonical/manifest.json"
DECISION_PATH = BASE / "final-review-decision.json"
DECIDED_AT = "2026-08-30T13:50:40Z"
DISCIPLINES_ID = "A2-FLD-559EE482F011D31A"
ROLE_PRIORITY_ID = "A2-FLD-STEP8-RR-ROLE-PRIORITY"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def actor() -> dict:
    return {
        "actor_id": "UNITALK-SEVERINE-STEP8",
        "actor_role": "Unitalk Operations A2 Pilot Reviewer",
        "display_name": "Séverine",
        "profile_id": "equinet-a2-enrichment",
        "workflow_id": None,
    }


def main() -> int:
    previous = load(PREVIOUS_PATH)
    if previous["workflow"]["state"] != "review_required" or previous["review"]["record_decision"] != "pending":
        raise RuntimeError("Rood & Riddle revision 004 is not awaiting final review")

    by_key={item[...y"]: item for item in previous["field_assessments"]}
    if by_key["organisation.disciplines"]["field_assessment_id"] != DISCIPLINES_ID:
        raise RuntimeError("Unexpected organisation.disciplines assessment ID")
    if by_key["relationship.target_role_priority"]["field_assessment_id"] != ROLE_PRIORITY_ID:
        raise RuntimeError("Unexpected target-role assessment ID")

    record = copy.deepcopy(previous)
    previous_revision = previous["record_metadata"]["record_revision_id"]
    revision_id = previous_revision.rsplit("_", 1)[0] + "_005"
    record["record_metadata"].update(
        {
            "record_revision_id": revision_id,
            "revision_number": 5,
            "supersedes_revision_id": previous_revision,
            "created_at": DECIDED_AT,
            "created_by": actor(),
            "change_reason": "human_review",
        }
    )

    decisions = {
        "organisation.disciplines": (
            "Approved as organisation-level context using the exact official wording 'all breeds and disciplines'; it is not treated as a Podiatry-specific discipline claim."
        ),
        "relationship.target_role_priority": (
            "Approved as a reviewed primary target-role classification because the verified role is Co-Founder/Farrier; it is not a sourced fact or proof of purchasing authority."
        ),
    }
    matched = set()
    for assessment in record["field_assessments"]:
        reason = decisions.get(assessment["field_key"])
        if reason:
            assessment["field_review"] = {
                "decision": "approved",
                "reviewer": actor(),
                "decided_at": DECIDED_AT,
                "reason": reason,
                "corrected_value": None,
            }
            matched.add(assessment["field_key"])
    if matched != set(decisions):
        raise RuntimeError(f"Missing reviewed fields: {sorted(set(decisions) - matched)}")

    record["data_quality"]["calculated_at"] = DECIDED_AT
    record["data_quality"]["unverified_field_keys"] = []
    record["data_quality"]["status"] = "incomplete"
    record["review"] = {
        "record_decision": "held",
        "reviewer": actor(),
        "decided_at": DECIDED_AT,
        "reason": "Séverine accepted the Rood & Riddle package as a Step 8 test result and approved holding the record because the bounded evidence does not satisfy professional-status, service-area or named-contact requirements.",
        "required_field_decisions_complete": True,
        "requested_changes": [
            "Obtain approved evidence for Manfred Eckert's professional status if operational processing is required.",
            "Obtain an explicit Podiatry service-area statement from an approved source.",
            "Obtain a verified named professional email or phone, or approve a documented contact-path exception.",
        ],
    }
    record["workflow"].update(
        {
            "state": "held",
            "previous_state": "review_required",
            "transitioned_at": DECIDED_AT,
            "triggered_by": actor(),
            "hold_reasons": [
                "Required professional status is not established.",
                "Required service area is not established.",
                "The named-target contact path has no verified named email or phone.",
            ],
            "block_reasons": [],
            "failure": None,
        }
    )
    record["audit_and_consumption"]["events"].append(
        {
            "event_id": "A2-EVENT-STEP8-RR-005",
            "event_type": "workflow_record_held",
            "actor": actor(),
            "timestamp": DECIDED_AT,
            "input_references": [previous_revision, "user_decision_2026-08-30T13:50:40Z"],
            "output_references": [revision_id, str(DECISION_PATH.relative_to(ROOT))],
            "model": None,
            "tools": ["deterministic-final-review-recorder"],
            "usage": None,
            "external_action": None,
        }
    )

    OUTPUT_PATH.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    validation = validate(record, previous=previous)
    if not validation["valid"]:
        OUTPUT_PATH.unlink(missing_ok=True)
        raise RuntimeError("; ".join(validation["errors"]))

    decision = {
        "record_type": "step8_final_review_decision",
        "profile": "equinet-a2-enrichment",
        "candidate_id": "A1-RR-PODIATRY-001",
        "decision": "held_as_accepted_step8_test_result",
        "field_decisions": [
            {
                "field_assessment_id": ROLE_PRIORITY_ID,
                "field_key": "relationship.target_role_priority",
                "decision": "approved",
                "approved_value": "primary",
                "decision_type": "human_reviewed_classification_not_sourced_fact",
            },
            {
                "field_assessment_id": DISCIPLINES_ID,
                "field_key": "organisation.disciplines",
                "decision": "approved",
                "approved_value": ["all breeds and disciplines"],
                "decision_type": "organisation_level_context_not_podiatry_specific",
            },
        ],
        "reviewer": {"name": "Séverine", "role": "Unitalk Operations"},
        "decided_at": DECIDED_AT,
        "scope": "bounded_manual_no_integration_pilot_test_only",
        "hold_reasons": record["workflow"]["hold_reasons"],
        "limitations": [
            "No purchasing authority is inferred.",
            "The organisation-wide disciplines wording is not narrowed to a Podiatry-specific claim.",
            "No outreach, CRM write, downstream delivery or production acceptance is authorised.",
            "The DeepSeek behavioural replay remains blocked before model invocation by unavailable non-interactive gateway credentials.",
        ],
        "approved_revision": str(OUTPUT_PATH.relative_to(ROOT)),
        "approved_revision_sha256": sha(OUTPUT_PATH),
        "external_actions": 0,
    }
    DECISION_PATH.write_text(json.dumps(decision, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    manifest = load(MANIFEST_PATH)
    manifest["records"] = [item for item in manifest["records"] if item["revision_id"] != revision_id]
    manifest["records"].append(
        {
            "path": str(OUTPUT_PATH.relative_to(ROOT)),
            "sha256": sha(OUTPUT_PATH),
            "revision_id": revision_id,
            "workflow": "held",
            "valid": True,
            "errors": [],
        }
    )
    manifest.update(
        {
            "status": "rood_riddle_accepted_as_held_step8_test_result",
            "final_record": str(OUTPUT_PATH.relative_to(ROOT)),
            "final_review_decision": "held",
            "final_review_decision_record": str(DECISION_PATH.relative_to(ROOT)),
            "recommended_record_decision": "held",
            "deepseek_behavioral_replay": "blocked_before_model_call",
            "hubspot_write": False,
            "outreach": False,
            "external_actions": 0,
        }
    )
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "held_as_accepted_step8_test_result",
                "candidate_id": "A1-RR-PODIATRY-001",
                "revision": revision_id,
                "revision_valid": True,
                "revision_sha256": sha(OUTPUT_PATH),
                "decision_path": str(DECISION_PATH.relative_to(ROOT)),
                "decision_sha256": sha(DECISION_PATH),
                "external_actions": 0,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
