#!/usr/bin/env python3
"""Build the Rood & Riddle stored-page recovery observations with no external access."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evaluations/step8/pilot/A1-RR-PODIATRY-001"
INITIAL = ROOT / "evaluations/step8/intake/A1-RR-PODIATRY-001/initial-record.json"
PAGE_1 = ROOT / "evaluations/step8/collection/A1-RR-PODIATRY-001/page-01.md"
PAGE_2 = ROOT / "evaluations/step8/collection/A1-RR-PODIATRY-001/page-02.md"
PAGE_3 = ROOT / "evaluations/step8/collection/A1-RR-PODIATRY-001/page-03.md"
PYTHON = ROOT / ".venv/bin/python"

URL_1 = "https://roodandriddle.com/lexington-podiatry-team"
URL_2 = "https://roodandriddle.com/lexington/"
URL_3 = "https://www.roodandriddle.com/contact"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_receipt(field_key: str, url: str, filename: str, timestamp: str) -> tuple[dict, dict]:
    output = BASE / "receipts" / filename
    command = [
        str(PYTHON),
        str(ROOT / "scripts/build_step8_collection_receipt.py"),
        "--candidate-id",
        "A1-RR-PODIATRY-001",
        "--field-key",
        field_key,
        "--source-url",
        url,
        "--requested-at",
        timestamp,
        "--output",
        str(output),
    ]
    process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if process.returncode != 0 or not output.exists():
        raise RuntimeError(f"Receipt failed for {field_key}: {process.stdout} {process.stderr}")
    return load(output), {
        "step": f"receipt_{field_key.replace('.', '_')}",
        "command": " ".join(str(part) for part in command[1:]),
        "exit_code": process.returncode,
        "result_reference": str(output.relative_to(BASE)),
    }


def main() -> int:
    BASE.mkdir(parents=True, exist_ok=True)
    initial = load(INITIAL)
    person_id = next(item["entity_id"] for item in initial["subject"]["entities"] if item["entity_type"] == "person")
    org_id = next(item["entity_id"] for item in initial["subject"]["entities"] if item["entity_type"] == "organisation")
    now = datetime.now(timezone.utc).replace(microsecond=0)

    receipt_specs = [
        ("person.role_title", URL_1, "role-title.json"),
        ("organisation.disciplines", URL_2, "disciplines.json"),
        ("person.professional_status", URL_1, "professional-status-not-found.json"),
        ("organisation.service_area", URL_2, "service-area-not-found.json"),
        ("person.business_email", URL_1, "named-email-not-found.json"),
        ("person.business_phone", URL_1, "named-phone-not-found.json"),
    ]
    receipts: dict[str, dict] = {}
    commands = []
    for index, (field_key, url, filename) in enumerate(receipt_specs):
        timestamp = (now + timedelta(seconds=index)).isoformat().replace("+00:00", "Z")
        receipt, command = run_receipt(field_key, url, filename, timestamp)
        receipts[field_key] = receipt
        commands.append(command)

    common = {
        "source_id": "prospect_official_website",
        "source_action_status": "completed",
        "explicitly_linked": True,
        "named_role_gap": False,
        "country_code": "US",
        "supporting_role_evidence_ids": [],
        "recommendation_basis_evidence_ids": [],
        "email_kind": None,
        "collection_method": "direct_extraction",
    }
    observations = [
        {
            **common,
            "observation_id": "A2-OBS-RR-ROLE-TITLE-001",
            "field_key": "person.role_title",
            "entity_id": person_id,
            "source_url": URL_1,
            "availability_status": "available",
            "fact_type": "direct_fact",
            "raw_value": "Co-Founder/Farrier",
            "page_context": "The official Lexington Podiatry team page lists Manfred Eckert under FARRIERS with the exact title Co-Founder/Farrier.",
            "evidence_id": "A2-EV-STEP8-RR-ROLE",
            "source_preflight": receipts["person.role_title"],
            "role_current": True,
        },
        {
            **common,
            "observation_id": "A2-OBS-RR-DISCIPLINES-001",
            "field_key": "organisation.disciplines",
            "entity_id": org_id,
            "source_url": URL_2,
            "availability_status": "available",
            "fact_type": "direct_fact",
            "raw_value": ["all breeds and disciplines"],
            "page_context": "The official Lexington hospital page states that Rood & Riddle provides ambulatory care for all breeds and disciplines. This is organisation-level context and is not narrowed to one Podiatry discipline.",
            "evidence_id": "A2-EV-STEP8-RR-DISCIPLINES",
            "source_preflight": receipts["organisation.disciplines"],
            "role_current": None,
        },
        {
            **common,
            "observation_id": "A2-OBS-RR-PROFESSIONAL-STATUS-GAP-001",
            "field_key": "person.professional_status",
            "entity_id": person_id,
            "source_url": URL_1,
            "availability_status": "not_found",
            "fact_type": "direct_fact",
            "raw_value": None,
            "page_context": "The team page confirms a Farrier role but does not explicitly state full-time, part-time or student/apprentice status.",
            "evidence_id": None,
            "source_preflight": receipts["person.professional_status"],
            "role_current": None,
        },
        {
            **common,
            "observation_id": "A2-OBS-RR-SERVICE-AREA-GAP-001",
            "field_key": "organisation.service_area",
            "entity_id": org_id,
            "source_url": URL_2,
            "availability_status": "not_found",
            "fact_type": "direct_fact",
            "raw_value": None,
            "page_context": "The page gives the Lexington hospital location and describes ambulatory care but does not explicitly define the Podiatry service area. Location is not treated as service area.",
            "evidence_id": None,
            "source_preflight": receipts["organisation.service_area"],
            "role_current": None,
        },
        {
            **common,
            "observation_id": "A2-OBS-RR-NAMED-EMAIL-GAP-001",
            "field_key": "person.business_email",
            "entity_id": person_id,
            "source_url": URL_1,
            "availability_status": "not_found",
            "fact_type": "direct_fact",
            "raw_value": None,
            "page_context": "No professional email is published for Manfred Eckert on the bounded team page. The contact-form placeholder is excluded.",
            "evidence_id": None,
            "source_preflight": receipts["person.business_email"],
            "role_current": None,
        },
        {
            **common,
            "observation_id": "A2-OBS-RR-NAMED-PHONE-GAP-001",
            "field_key": "person.business_phone",
            "entity_id": person_id,
            "source_url": URL_1,
            "availability_status": "not_found",
            "fact_type": "direct_fact",
            "raw_value": None,
            "page_context": "No professional phone is published for Manfred Eckert on the bounded team page. The organisation phone is not attributed to him.",
            "evidence_id": None,
            "source_preflight": receipts["person.business_phone"],
            "role_current": None,
        },
    ]
    batch = {
        "batch_version": "0.1.0-draft.1",
        "candidate_id": "A1-RR-PODIATRY-001",
        "segment": "farrier",
        "operating_scope": "manual_no_integration_pilot",
        "observations": observations,
    }
    batch_path = BASE / "observation-batch.json"
    validated_path = BASE / "validated-observations.json"
    batch_path.write_text(json.dumps(batch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    process = subprocess.run(
        [str(PYTHON), str(ROOT / "scripts/normalise_and_validate_a2_observations.py"), str(batch_path), "--output", str(validated_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    commands.append(
        {
            "step": "validate_observation_batch",
            "command": "scripts/normalise_and_validate_a2_observations.py evaluations/step8/pilot/A1-RR-PODIATRY-001/observation-batch.json --output evaluations/step8/pilot/A1-RR-PODIATRY-001/validated-observations.json",
            "exit_code": process.returncode,
            "result_reference": "validated-observations.json",
        }
    )
    if process.returncode != 0 or not validated_path.exists():
        raise RuntimeError(f"Observation validation failed: {process.stdout} {process.stderr}")
    validated = load(validated_path)

    analysis = {
        "stage": "step8_rood_riddle_stored_page_recovery",
        "candidate_id": "A1-RR-PODIATRY-001",
        "executed_at": now.isoformat().replace("+00:00", "Z"),
        "mode": "deterministic_recovery_from_collected_pages",
        "profile": "equinet-a2-enrichment",
        "model_execution": {
            "intended_model": "deepseek-v4-flash",
            "status": "blocked_before_model_call",
            "reason": "The non-interactive profile process had no usable openai-api credential. No model output is claimed.",
        },
        "accepted_direct_observations": [
            {
                "field_key": "person.role_title",
                "value": "Co-Founder/Farrier",
                "evidence_id": "A2-EV-STEP8-RR-ROLE",
                "state": "present_unverified_ready_for_evidence_assessment",
            },
            {
                "field_key": "organisation.disciplines",
                "value": ["all breeds and disciplines"],
                "evidence_id": "A2-EV-STEP8-RR-DISCIPLINES",
                "state": "present_unverified_ready_for_evidence_assessment",
                "scope_note": "Organisation-wide hospital wording; not narrowed to a Podiatry-only discipline.",
            },
        ],
        "unresolved_required_fields": [
            {"field_key": "person.professional_status", "state": "not_found", "reason": "Full-time, part-time or apprentice status is not explicitly published."},
            {"field_key": "organisation.service_area", "state": "not_found", "reason": "The Lexington location does not prove the service area."},
            {"field_key": "person.business_email", "state": "not_found", "reason": "No named professional email was published in the bounded pages."},
            {"field_key": "person.business_phone", "state": "not_found", "reason": "No named professional phone was published in the bounded pages."},
        ],
        "target_role_priority_recommendation": {
            "field_key": "relationship.target_role_priority",
            "recommendation": "primary",
            "recommendation_type": "human_reviewable_classification",
            "not_a_sourced_fact": True,
            "human_review_required": True,
            "rationale": "The verified Co-Founder/Farrier role matches the approved Farrier primary-role model; it does not prove purchasing authority.",
        },
        "contact_path": {
            "selected": "named_target",
            "status": "unsatisfied",
            "organisation_fallback_available": True,
            "organisation_phone": "(859) 233-0371",
            "note": "The organisation phone is not attributed to Manfred Eckert and therefore does not satisfy the selected named-target path.",
        },
        "minimum_package": {
            "status": "incomplete",
            "research_exhausted_for_bounded_pages": True,
            "recommended_record_decision": "held",
        },
        "boundaries_verified": [
            "No service area inferred from the location.",
            "No full-time or part-time status inferred from the role or team listing.",
            "No form placeholder retained as contact data.",
            "No organisation phone attributed to the named person.",
            "No purchasing authority inferred.",
            "No A1 score change.",
            "No Web, provider, CRM, workflow, outreach or delivery action.",
        ],
        "external_actions": 0,
    }
    (BASE / "stage1-analysis.json").write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    source_files = {
        "handoff_json": "evaluations/step8/handoffs/A1-RR-PODIATRY-001.handoff.json",
        "initial_record_json": "evaluations/step8/intake/A1-RR-PODIATRY-001/initial-record.json",
        "reuse_snapshot_json": "evaluations/step8/planning/A1-RR-PODIATRY-001.reuse-snapshot.json",
        "gap_plan_json": "evaluations/step8/planning/A1-RR-PODIATRY-001.gap-plan.json",
        "collection_manifest_json": "evaluations/step8/collection/collection-manifest.json",
        "page_01_md": "evaluations/step8/collection/A1-RR-PODIATRY-001/page-01.md",
        "page_02_md": "evaluations/step8/collection/A1-RR-PODIATRY-001/page-02.md",
        "page_03_md": "evaluations/step8/collection/A1-RR-PODIATRY-001/page-03.md",
    }
    audit = {
        "audit_id": "AUDIT-STEP8-RR-STORED-PAGE-RECOVERY",
        "candidate_id": "A1-RR-PODIATRY-001",
        "stage": "step8_rood_riddle_stored_page_recovery",
        "executed_at": now.isoformat().replace("+00:00", "Z"),
        "execution_kind": "deterministic_recovery",
        "entity": {
            "profile": "equinet-a2-enrichment",
            "intended_model": "deepseek-v4-flash",
            "actual_model": None,
            "unitalk_gateway": "litellm-unitalk",
            "upstream_provider": "microsoft_azure",
            "processing_region": "Europe",
        },
        "source_files": source_files,
        "source_file_hashes": {key: sha(ROOT / path) for key, path in source_files.items()},
        "commands_executed": commands,
        "usage_and_cost": {
            "model_calls": 0,
            "api_calls": 0,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "cost_amount": None,
            "currency": "USD",
            "cost_status": "unavailable",
            "profile_attempt_usage_record": "evaluations/step8/pilot/A1-RR-PODIATRY-001/profile-usage.json",
            "profile_attempt_status": "failed_before_model_call",
        },
        "external_calls": 0,
        "external_actions": 0,
        "firecrawl_calls": 0,
        "exa_calls": 0,
        "apify_calls": 0,
        "hubspot_calls": 0,
        "twenty_calls": 0,
        "n8n_calls": 0,
        "outreach_actions": 0,
        "crm_writes": 0,
        "stored_collection_pages_reused": 3,
        "pass": True,
    }
    (BASE / "stage1-audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "deterministic_recovery_complete",
                "candidate_id": "A1-RR-PODIATRY-001",
                "accepted_observations": validated["accepted_count"],
                "state_only_observations": sum(item["action"] == "retain_state_only" for item in validated["observations"]),
                "rejected_observations": validated["rejected_count"],
                "model_run": "blocked_before_call",
                "external_actions": 0,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
