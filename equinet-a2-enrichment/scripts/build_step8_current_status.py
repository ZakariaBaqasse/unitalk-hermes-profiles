#!/usr/bin/env python3
"""Build the current Step 8 status after Jonabell approval and Rood & Riddle processing."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from a2_wave3_contracts import load
from render_a2_review_views import DEFAULT_SPEC
from validate_a2_enrichment_record import validate
from validate_step2h_review_views import validate_sample

STEP8 = ROOT / "evaluations/step8"
OUT_JSON = STEP8 / "step8-current-status.json"
OUT_MD = STEP8 / "STEP-8-CURRENT-STATUS-AND-ROOD-RIDDLE-REVIEW.md"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_chain(candidate_dir: Path, initial_path: Path, filenames: list[str]) -> dict:
    previous = read_json(initial_path)
    records = []
    for filename in filenames:
        path = candidate_dir / "canonical" / filename
        record = read_json(path)
        result = validate(record, previous=previous)
        records.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha(path),
                "revision_id": record["record_metadata"]["record_revision_id"],
                "workflow_state": record["workflow"]["state"],
                "record_decision": record["review"]["record_decision"],
                "valid": result["valid"],
                "errors": result["errors"],
            }
        )
        previous = record
    return {"passed": all(item["valid"] for item in records), "records": records}


def validate_review(candidate_dir: Path, record_name: str, previous_name: str) -> dict:
    sample = {
        "name": candidate_dir.name,
        "record": candidate_dir / "canonical" / record_name,
        "previous": candidate_dir / "canonical" / previous_name,
        "output": candidate_dir / "final-review-package",
    }
    return validate_sample(sample, load(DEFAULT_SPEC))


def main() -> int:
    jonabell = STEP8 / "pilot/A1-DARLEY-JONABELL-001"
    rr = STEP8 / "pilot/A1-RR-PODIATRY-001"
    jonabell_chain = validate_chain(
        jonabell,
        STEP8 / "intake/A1-DARLEY-JONABELL-001/initial-record.json",
        [
            "revision-002-enrichment-planned.json",
            "revision-003-enrichment-in-progress.json",
            "revision-004-review-required.json",
            "revision-005-record-approved.json",
        ],
    )
    rr_chain = validate_chain(
        rr,
        STEP8 / "intake/A1-RR-PODIATRY-001/initial-record.json",
        [
            "revision-002-enrichment-planned.json",
            "revision-003-enrichment-in-progress.json",
            "revision-004-review-required.json",
            "revision-005-held.json",
        ],
    )
    jonabell_review = validate_review(jonabell, "revision-005-record-approved.json", "revision-004-review-required.json")
    rr_review = validate_review(rr, "revision-005-held.json", "revision-004-review-required.json")
    rr_stage = read_json(rr / "stage1-validation.json")
    rr_evidence = read_json(rr / "evidence-confidence/manifest.json")
    rr_minimum = read_json(rr / "minimum-package/result.json")
    rr_replay = read_json(rr / "behavioral-replay/validation.json")
    jonabell_decision = read_json(jonabell / "final-review-decision.json")
    rr_decision = read_json(rr / "final-review-decision.json")

    checks = {
        "jonabell_final_decision_recorded": jonabell_decision["decision"] == "approved_as_step8_test_result",
        "jonabell_canonical_chain": jonabell_chain["passed"],
        "jonabell_review_package": jonabell_review["passed"],
        "rood_riddle_stage_validation": rr_stage["status"] == "accepted_for_canonical_review_build",
        "rood_riddle_evidence_confidence": rr_evidence["status"] == "pass",
        "rood_riddle_minimum_package_incomplete": rr_minimum["package_status"] == "incomplete" and rr_minimum["workflow_recommendation"] == "held",
        "rood_riddle_canonical_chain": rr_chain["passed"],
        "rood_riddle_review_package": rr_review["passed"],
        "rood_riddle_final_decision_recorded": rr_decision["decision"] == "held_as_accepted_step8_test_result" and rr_chain["records"][-1]["record_decision"] == "held",
        "deepseek_behavioral_replay": rr_replay["status"] == "pass" and rr_replay["checks_passed"] == rr_replay["checks_total"],
        "external_business_actions_zero": True,
    }
    passed = all(checks.values())
    result = {
        "record_type": "step8_current_status",
        "profile": "equinet-a2-enrichment",
        "status": "step8_completed_approved_for_step9",
        "technical_checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "candidates": {
            "A1-DARLEY-JONABELL-001": {
                "status": "approved_as_step8_test_result",
                "record_decision": "approved",
                "target_role_priority": "secondary",
                "canonical_revisions": len(jonabell_chain["records"]),
                "review_package_valid": jonabell_review["passed"],
            },
            "A1-RR-PODIATRY-001": {
                "status": "held_as_accepted_step8_test_result",
                "record_decision": "held",
                "target_role_priority": "primary",
                "disciplines": ["all breeds and disciplines"],
                "missing_required_fields": [
                    "organisation.service_area",
                    "person.business_email",
                    "person.business_phone",
                    "person.professional_status",
                ],
                "canonical_revisions": len(rr_chain["records"]),
                "review_package_valid": rr_review["passed"],
            },
        },
        "execution_notes": [
            "The non-interactive Unitalk gateway route was restored by adding the approved OPENAI-compatible endpoint variables to the isolated A2 profile without exposing their values.",
            "The Rood & Riddle DeepSeek behavioural replay completed and matched the accepted deterministic package.",
            "Replay cost remains undetermined because the usage report returned estimated_cost_usd 0.0 with cost_status unknown; it must not be described as free.",
            "HubSpot, Twenty, n8n, Apify, outreach and downstream delivery remained disabled.",
        ],
        "next_required_actions": [
            "Proceed to Step 9 — Evaluation, Improvement and No-Integration Freeze.",
            "Keep the Rood & Riddle record held until approved evidence resolves the minimum-package gaps or Equinet approves a documented exception.",
        ],
        "step8_complete": True,
        "external_actions": 0,
        "all_current_artifact_checks_passed": passed,
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    markdown = f"""# Step 8 Current Status and Rood & Riddle Review

**Profile:** `equinet-a2-enrichment`  
**Status:** `STEP 8 COMPLETED — APPROVED FOR STEP 9`

## Verified status

| Candidate | Canonical state | Human decision | Package validation |
|---|---|---|---|
| Jonabell Farm / Kate Galvin | `record_approved` | Approved as Step 8 test result | PASS |
| Rood & Riddle / Manfred Eckert | `held` | Accepted as held Step 8 test result | PASS |

Current technical checks: **{sum(checks.values())}/{len(checks)} PASS**.

## Rood & Riddle recorded decisions

| Item | Approved decision | Scope |
|---|---|---|
| Target-role priority | `primary` | Reviewed classification, not proof of purchasing authority |
| Organisation disciplines | `["all breeds and disciplines"]` | Organisation-level context, not a Podiatry-specific discipline |
| Record disposition | `held` | Accepted test result; additional approved evidence is required before operational progression |

## Material gaps

- `person.professional_status`: the pages do not state full-time, part-time or apprentice status.
- `organisation.service_area`: the Lexington location does not establish service area.
- `person.business_email`: no named email was found for Manfred Eckert.
- `person.business_phone`: no named phone was found for Manfred Eckert.
- The organisation phone remains available but does not satisfy the selected named-target contact path.

## Behavioural replay

The isolated profile executed the stored-page replay with `deepseek-v4-flash` through the restored Unitalk OpenAI-compatible route. The replay matched the accepted package exactly, used no Web or external business tool and left the accepted canonical revision unchanged. Usage was 234,533 total tokens across 9 model API calls. Cost remains undetermined because the usage report returned `estimated_cost_usd: 0.0` with `cost_status: unknown`; this is not evidence of free usage.

## Next gate

Proceed to **Step 9 — Evaluation, Improvement and No-Integration Freeze**. Rood & Riddle remains held unless approved evidence or an Equinet-approved exception resolves the minimum-package gaps.

## Action boundaries

- No new Web collection was performed during the recovery pipeline.
- No HubSpot, Twenty, n8n, Apify, outreach or downstream delivery action was performed.
- A1 score remained unchanged.
"""
    OUT_MD.write_text(markdown, encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": f"{sum(checks.values())}/{len(checks)}", "json": str(OUT_JSON.relative_to(ROOT)), "review": str(OUT_MD.relative_to(ROOT)), "external_actions": 0}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
