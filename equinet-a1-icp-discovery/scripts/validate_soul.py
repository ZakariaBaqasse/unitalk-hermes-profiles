#!/usr/bin/env python3
"""Static release checks for the Equinet A1 ICP Discovery SOUL."""

from __future__ import annotations

import sys
from pathlib import Path


PROFILE_DIR = Path(__file__).resolve().parents[1]
SOUL_PATH = PROFILE_DIR / "SOUL.md"

REQUIRED_TEXT = [
    "# Equinet A1 — ICP Discovery",
    "shared Unitalk AI Collaborator",
    "You never initiate outreach.",
    "## Authoritative configuration",
    "configurations/icp/equinet-icp-v1.yaml",
    "configurations/evidence/public-website-enrichment-policy-v1.yaml",
    "configurations/evidence/evidence-confidence-rules-v1.yaml",
    "configurations/scoring/icp-scoring-model-v1.yaml",
    "skills/a1-prospect-data-contract/references/prospect-candidate.schema.json",
    "## Integrated discovery and processing method",
    "equinet-n8n-discovery-control",
    "Build Final Discovery Result",
    "finite Hermes cron job",
    "There is no inbound callback path",
    "read-only company-domain duplicate check",
    "Twenty Company staging, plus a linked Person when the n8n `name` field is present, is a mandatory part of the current post-discovery execution path",
    "complete Twenty staging index",
    "## Evidence rules",
    "## Candidate data contract",
    "## Confidence calculation",
    "## ICP scoring",
    "## Duplicate and exclusion checks",
    "## Approval and action boundary",
    "## Review and escalation",
    "## A2 handoff",
    "## Output requirements",
    "## Data governance",
    "## Audit requirements",
    "## Error behaviour",
    "## Completion standard",
    "Default to **DRAFT FOR APPROVAL**.",
]

FORBIDDEN_TEXT = [
    "You are Hermes Agent",
    "NOT READY FOR PILOT — CONFIGURATION IN PROGRESS",
    "This temporary scaffold must be replaced",
    "automatically send outreach",
    "PILOT_READY_NO_INTEGRATION",
    "HubSpot is not connected in the current V1",
    "set the HubSpot duplicate/exclusion check to `unavailable`",
    "live record checks are unavailable",
    "Twenty is not connected.",
    "Twenty, A2, n8n and production acceptance remain pending",
    "until Twenty staging is implemented, artifacts remain local",
    "Twenty is a future staging and review destination",
    "A1 may execute the complete approved workflow in one turn",
    "Company-only staging",
    "Never create People",
]

REQUIRED_FILES = [
    "configurations/icp/equinet-icp-v1.yaml",
    "configurations/evidence/public-website-enrichment-policy-v1.yaml",
    "configurations/evidence/evidence-confidence-rules-v1.yaml",
    "configurations/scoring/icp-scoring-model-v1.yaml",
    "configurations/operations/a1-runtime-policy-v1.yaml",
    "configurations/crm/twenty-person-field-manifest-v1.json",
    "configurations/sources/a1-web-blocklist.txt",
    "skills/a1-prospect-data-contract/references/prospect-candidate.schema.json",
    "skills/a1-prospect-data-contract/scripts/validate_candidate.py",
    "scripts/calculate_candidate_confidence.py",
    "scripts/calculate_icp_score.py",
]


def main() -> int:
    text = SOUL_PATH.read_text(encoding="utf-8")
    errors: list[str] = []

    for required in REQUIRED_TEXT:
        if required not in text:
            errors.append(f"Missing required SOUL text: {required}")
    for forbidden in FORBIDDEN_TEXT:
        if forbidden in text:
            errors.append(f"Forbidden or stale SOUL text present: {forbidden}")
    for relative in REQUIRED_FILES:
        if not (PROFILE_DIR / relative).is_file():
            errors.append(f"Referenced file does not exist: {relative}")

    line_count = len(text.splitlines())
    if line_count > 500:
        errors.append(f"SOUL exceeds 500 lines: {line_count}")

    if errors:
        print(f"INVALID: {SOUL_PATH}")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"VALID: {SOUL_PATH}")
    print(f"Lines: {line_count}")
    print(f"Required references: {len(REQUIRED_FILES)}")
    print("Deployment status: n8n control plane with read-only HubSpot domain checking and mandatory Company plus optional linked Person Twenty staging")
    return 0


if __name__ == "__main__":
    sys.exit(main())
