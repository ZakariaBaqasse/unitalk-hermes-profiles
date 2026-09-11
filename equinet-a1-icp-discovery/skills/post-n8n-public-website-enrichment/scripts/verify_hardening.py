#!/usr/bin/env python3
"""Offline verification runner for A1 enrichment hardening.

Uses only local files, local subprocesses and loopback mock servers. It performs
no n8n, Twenty, HubSpot, A2, outreach or public-network writes.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PYTHON = ROOT / ".venv" / "bin" / "python"

core_files = [
    ROOT / "skills/post-n8n-public-website-enrichment/scripts/manage_enrichment.py",
    ROOT / "skills/post-n8n-public-website-enrichment/scripts/route_and_overlay.py",
    ROOT / "skills/post-n8n-public-website-enrichment/scripts/migrate_state_v1_to_v2.py",
    ROOT / "skills/post-n8n-public-website-enrichment/scripts/test_enrichment_state_v2.py",
    ROOT / "skills/post-n8n-public-website-enrichment/scripts/test_hardening_acceptance.py",
    ROOT / "skills/post-n8n-public-website-enrichment/scripts/test_migrate_state_v1_to_v2.py",
    ROOT / "skills/post-n8n-public-website-enrichment/tests/test_manage_enrichment.py",
    ROOT / "skills/post-n8n-public-website-enrichment/tests/test_route_and_overlay.py",
    ROOT / "skills/system-operations/equinet-n8n-discovery-control/scripts/poll_ticket.py",
    ROOT / "skills/system-operations/equinet-n8n-discovery-control/scripts/build_configuration_snapshot.py",
    ROOT / "skills/system-operations/equinet-n8n-discovery-control/tests/test_poll_ticket.py",
    ROOT / "skills/crm/evidence-aware-crm-staging/scripts/stage_twenty_company.py",
    ROOT / "skills/crm/evidence-aware-crm-staging/scripts/stage_twenty_rest.py",
    ROOT / "skills/crm/evidence-aware-crm-staging/scripts/test_overlay_admission_v2.py",
    ROOT / "scripts/validate_source_execution_policy.py",
]

commands = [
    [str(PYTHON), "-m", "py_compile", *map(str, core_files)],
    [str(PYTHON), "-m", "unittest", "-v",
     "skills/post-n8n-public-website-enrichment/tests/test_manage_enrichment.py",
     "skills/post-n8n-public-website-enrichment/tests/test_route_and_overlay.py"],
    [str(PYTHON), str(ROOT / "skills/post-n8n-public-website-enrichment/scripts/test_enrichment_state_v2.py")],
    [str(PYTHON), str(ROOT / "skills/post-n8n-public-website-enrichment/scripts/test_hardening_acceptance.py")],
    [str(PYTHON), str(ROOT / "skills/post-n8n-public-website-enrichment/scripts/test_migrate_state_v1_to_v2.py")],
    [str(PYTHON), "-m", "unittest", "-v",
     "skills/system-operations/equinet-n8n-discovery-control/tests/test_poll_ticket.py"],
    [str(PYTHON), "-m", "unittest", "-v",
     "skills/crm/evidence-aware-crm-staging/tests/test_stage_twenty_company.py",
     "skills/crm/evidence-aware-crm-staging/tests/test_stage_twenty_rest.py"],
    [str(PYTHON), str(ROOT / "skills/crm/evidence-aware-crm-staging/scripts/test_overlay_admission_v2.py")],
    [str(PYTHON), str(ROOT / "scripts/validate_source_execution_policy.py")],
]
for directory in [
    ROOT / "skills/prospect-segment-classification/tests",
    ROOT / "skills/equinet-icp-qualification/tests",
    ROOT / "skills/prospect-evidence-and-confidence/tests",
    ROOT / "skills/icp-scoring-and-rationale/tests",
    ROOT / "skills/a1-prospect-data-contract/tests",
]:
    if directory.is_dir():
        commands.append([str(PYTHON), "-m", "unittest", "discover", "-v", "-s", str(directory), "-p", "test_*.py"])

results = []
failed = False
test_count = 0
for command in commands:
    run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    combined = run.stdout + "\n" + run.stderr
    counts = [int(value) for value in re.findall(r"Ran (\d+) tests?", combined)]
    command_tests = sum(counts)
    test_count += command_tests
    results.append({
        "command": " ".join(command),
        "exit_code": run.returncode,
        "tests_run": command_tests,
        "stdout_tail": run.stdout[-5000:],
        "stderr_tail": run.stderr[-5000:],
    })
    failed = failed or run.returncode != 0

schema_count = 0
schema_errors = []
yaml_count = 0
policy_errors = []
try:
    from jsonschema import Draft202012Validator
    for path in sorted(ROOT.glob("skills/**/references/*.schema.json")):
        try:
            Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
            schema_count += 1
        except Exception as exc:
            schema_errors.append({"path": str(path), "error": str(exc)})
except Exception as exc:
    schema_errors.append({"path": "jsonschema_import", "error": str(exc)})

try:
    import yaml
    runtime_path = ROOT / "configurations/operations/a1-runtime-policy-v1.yaml"
    website_path = ROOT / "configurations/evidence/public-website-enrichment-policy-v1.yaml"
    runtime = yaml.safe_load(runtime_path.read_text(encoding="utf-8"))
    website = yaml.safe_load(website_path.read_text(encoding="utf-8"))
    yaml_count = 2
    if runtime.get("policy_version") != "4.3.0":
        policy_errors.append("runtime policy_version must be 4.3.0")
    post = runtime.get("post_discovery", {})
    if post.get("verified_official_site_without_assessment_inputs") != "assessment_pending_block_staging":
        policy_errors.append("runtime missing-assessment staging gate is absent")
    if post.get("automatic_missing_pipeline_input_fallback") != "prohibited":
        policy_errors.append("runtime automatic fallback prohibition is absent")
    if website.get("policy_version") != "1.5.0":
        policy_errors.append("website policy_version must be 1.5.0")
    verified = website.get("website_requirement", {}).get("verified_site_assessment_state", {})
    if verified.get("missing_assessment_inputs_may_stage") is not False:
        policy_errors.append("website policy must block missing assessments from staging")
    failure = website.get("website_requirement", {}).get("verified_site_unscored_failure_completion", {})
    if failure.get("required_provenance", {}).get("persisted_failure_history") != "required":
        policy_errors.append("website policy must require persisted failure history")
    soul = (ROOT / "SOUL.md").read_text(encoding="utf-8")
    for phrase in (
        "missing assessment inputs remains non-terminal",
        "Missing classification, qualification or confidence objects mean incomplete work",
        "verified-unscored overlay only after a structured non-retryable assessment failure",
    ):
        if phrase not in soul:
            policy_errors.append(f"SOUL missing hardening clause: {phrase}")
except Exception as exc:
    policy_errors.append(f"policy validation failed: {exc}")

failed = failed or bool(schema_errors) or bool(policy_errors)
report = {
    "status": "failed" if failed else "passed",
    "commands": results,
    "tests_run": test_count,
    "json_schemas_validated": schema_count,
    "json_schema_errors": schema_errors,
    "yaml_documents_validated": yaml_count,
    "policy_errors": policy_errors,
    "no_write_fixture_coverage": [
        "no_website", "scored", "out_of_scope", "explicit_exhausted_assessment_failure",
        "pending_blocked", "provenance_merge", "ticket_consumption", "existing_score_preservation",
    ],
    "external_writes_performed": False,
}
report_path = Path(__file__).resolve().parents[1] / "references" / "hardening-verification-report.json"
report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "status": report["status"], "report": str(report_path),
    "command_count": len(results), "tests_run": test_count,
    "json_schemas_validated": schema_count, "schema_error_count": len(schema_errors),
    "yaml_documents_validated": yaml_count, "policy_error_count": len(policy_errors),
    "external_writes_performed": False,
}, sort_keys=True))
raise SystemExit(1 if failed else 0)
