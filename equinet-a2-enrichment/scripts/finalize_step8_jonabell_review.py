#!/usr/bin/env python3
"""Record Séverine's final Jonabell Step 8 approval and validate the new revision."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_a2_enrichment_record import validate

BASE = ROOT / "evaluations/step8/pilot/A1-DARLEY-JONABELL-001"
PREVIOUS_PATH = BASE / "canonical/revision-004-review-required.json"
OUTPUT_PATH = BASE / "canonical/revision-005-record-approved.json"
MANIFEST_PATH = BASE / "canonical/manifest.json"
DECISION_PATH = BASE / "final-review-decision.json"
DECIDED_AT = "2026-08-30T13:10:32Z"
FIELD_ID = "A2-FLD-STEP8-JONABELL-ROLE-PRIORITY"


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
        raise RuntimeError("Jonabell revision 004 is not awaiting final review")

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

    matched = 0
    for assessment in record["field_assessments"]:
        if assessment["field_assessment_id"] == FIELD_ID:
            assessment["field_review"] = {
                "decision": "approved",
                "reviewer": actor(),
                "decided_at": DECIDED_AT,
                "reason": "Approved as a reviewed target-role classification: Kate Galvin is the selected named contact, while her Operations Manager-equivalent role remains secondary and does not establish purchasing authority.",
                "corrected_value": None,
            }
            matched += 1
    if matched != 1:
        raise RuntimeError(f"Expected one target-role assessment, found {matched}")

    record["data_quality"]["status"] = "review_ready"
    record["data_quality"]["calculated_at"] = DECIDED_AT
    record["data_quality"]["unverified_field_keys"] = []
    record["data_quality"]["limitations"] = [
        "Kate Galvin is the selected named contact; target-role priority secondary is a reviewed classification, not a sourced fact or proof of purchasing authority.",
        "HubSpot customer, Deal, consent, suppression and owner checks are unavailable.",
    ]
    record["review"] = {
        "record_decision": "approved",
        "reviewer": actor(),
        "decided_at": DECIDED_AT,
        "reason": "Séverine accepted the secondary target-role classification and accepted the Jonabell package as a Step 8 test result. Approval is limited to the bounded no-integration pilot and authorises no CRM write or outreach.",
        "required_field_decisions_complete": True,
        "requested_changes": [],
    }
    record["workflow"].update(
        {
            "state": "record_approved",
            "previous_state": "review_required",
            "transitioned_at": DECIDED_AT,
            "triggered_by": actor(),
            "hold_reasons": [],
            "block_reasons": [],
            "failure": None,
        }
    )
    record["audit_and_consumption"]["events"].append(
        {
            "event_id": "A2-EVENT-STEP8-JONABELL-005",
            "event_type": "workflow_record_approved",
            "actor": actor(),
            "timestamp": DECIDED_AT,
            "input_references": [previous_revision, "user_decision_2026-08-30T13:10:32Z"],
            "output_references": [revision_id, str(DECISION_PATH.relative_to(ROOT))],
            "model": None,
            "tools": ["deterministic-final-review-recorder"],
            "usage": None,
            "external_action": None,
        }
    )

    OUTPUT_PATH.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    result = validate(record, previous=previous)
    if not result["valid"]:
        OUTPUT_PATH.unlink(missing_ok=True)
        raise RuntimeError("; ".join(result["errors"]))

    decision = {
        "record_type": "step8_final_review_decision",
        "profile": "equinet-a2-enrichment",
        "candidate_id": "A1-DARLEY-JONABELL-001",
        "decision": "approved_as_step8_test_result",
        "field_decisions": [
            {
                "field_assessment_id": FIELD_ID,
                "field_key": "relationship.target_role_priority",
                "decision": "approved",
                "approved_value": "secondary",
                "decision_type": "human_reviewed_classification_not_sourced_fact",
            }
        ],
        "reviewer": {"name": "Séverine", "role": "Unitalk Operations"},
        "decided_at": DECIDED_AT,
        "scope": "bounded_manual_no_integration_pilot_test_only",
        "limitations": [
            "No purchasing authority is inferred.",
            "No outreach, CRM write, downstream delivery or production acceptance is authorised.",
            "HubSpot authoritative eligibility checks remain unavailable.",
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
            "workflow": "record_approved",
            "valid": True,
            "errors": [],
        }
    )
    manifest.update(
        {
            "status": "jonabell_accepted_as_step8_test_result",
            "final_record": str(OUTPUT_PATH.relative_to(ROOT)),
            "final_review_decision": "approved",
            "final_review_decision_record": str(DECISION_PATH.relative_to(ROOT)),
            "rood_and_riddle_processed": False,
            "hubspot_write": False,
            "outreach": False,
            "external_actions": 0,
        }
    )
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "approved",
                "candidate_id": "A1-DARLEY-JONABELL-001",
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
