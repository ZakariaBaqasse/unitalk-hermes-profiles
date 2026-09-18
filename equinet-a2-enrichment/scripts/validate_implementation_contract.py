#!/usr/bin/env python3
"""Deterministic static validator for the Equinet A2 implementation contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
CONTRACT = PROFILE_ROOT / "foundations" / "A2-IMPLEMENTATION-CONTRACT.md"
EXPECTED_VERSION = "0.1.4"
EXPECTED_STATUS = "FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY"

REQUIRED_HEADINGS = [
    "## 1. Purpose and authority",
    "## 2. Mission",
    "## 3. Intended users and ownership",
    "## 4. Business outcome",
    "## 5. Scope",
    "## 6. Trigger and eligibility contract",
    "## 7. Authoritative source and decision precedence",
    "## 8. Protected fields and conflict handling",
    "## 9. Evidence, verification and data-quality boundary",
    "## 10. Privacy, consent and data minimisation",
    "## 11. Action and approval matrix",
    "## 12. Target workflow",
    "## 13. Inputs",
    "## 14. Outputs",
    "## 15. Systems of record and supporting systems",
    "## 16. Integration status",
    "## 17. Cost and consumption controls",
    "## 18. Error, retry and fallback behaviour",
    "## 19. Audit requirements",
    "## 20. Acceptance ladder",
    "## 21. Open items register",
    "## 22. Step 1B decision",
]

REQUIRED_BOUNDARIES = [
    "Default action mode is **DRAFT FOR APPROVAL**.",
    "HubSpot as Equinet's customer-facing source of truth",
    "A1 owns scoring",
    "every enriched record requires human review during the pilot",
    "Write to HubSpot | Prohibited | Prohibited | Guarded action after recorded approval only",
    "Send outreach or enrol in a sequence | Prohibited | Prohibited | Outside A2 scope",
    "No CRM updates",
    "No automated access; mutual connections unavailable",
    "It does not approve the final A2 schema",
]

REQUIRED_INTEGRATION_STATES = [
    "A1 durable handoff | Not connected",
    "HubSpot read | Not connected; object/property, lifecycle/pipeline, users/teams/owners and process snapshots received; live verification pending",
    "HubSpot write | Not connected and not authorised; workflow trigger/action dependencies are not verified",
    "Twenty or alternative review staging | Not selected; no existing HubSpot enrichment-review asset identified",
    "n8n | Not connected",
    "Paid enrichment provider | None approved or connected",
    "A3 and A14 handoffs | Not connected",
]

FORBIDDEN_ACTIVE_CLAIMS = [
    "HubSpot integration is active",
    "Twenty is connected",
    "n8n is connected",
    "production-ready",
    "contractually accepted",
    "automatic CRM write is authorised",
]


def main() -> int:
    errors: list[str] = []

    if not CONTRACT.exists():
        errors.append(f"missing contract: {CONTRACT}")
        text = ""
    else:
        text = CONTRACT.read_text(encoding="utf-8")

    if f"**Contract version:** `{EXPECTED_VERSION}`" not in text:
        errors.append("contract version missing or incorrect")
    if f"**Profile status:** `{EXPECTED_STATUS}`" not in text:
        errors.append("profile status missing or incorrect")
    if "**Approval state:** `APPROVED BY UNITALK OPERATIONS FOR STEP 1C`" not in text:
        errors.append("approved Step 1B state missing or incorrect")
    if "**Decision:** `APPROVED AS DRAFTED`" not in text:
        errors.append("recorded human decision missing")
    if "**Approver:** Séverine, Unitalk Operations" not in text:
        errors.append("recorded approver missing")
    if "A1 remains the owner of scoring" not in text:
        errors.append("score ownership clarification missing")
    if "new A1-generated, human-approved revision" not in text:
        errors.append("score revision clarification missing")
    if "HubSpot data-model image and property definitions for Company, Contact, Deal, Ticket, Complaints and Sample Requests" not in text:
        errors.append("HubSpot metadata intake status missing")
    if "Lifecycle and pipeline models, users/teams/owners snapshot, territories and relevant Sales/Marketing process inventory" not in text:
        errors.append("HubSpot operational metadata intake status missing")
    if "block any proposed HubSpot write when the mapped property, list-membership effect or enabled workflow dependency has not been verified" not in text:
        errors.append("workflow dependency write block missing")
    if "Creator does not exist; Campaign is a standard HubSpot object" not in text:
        errors.append("HubSpot Creator/Campaign confirmation missing")
    if "Tahmineh Goljan and Lucija Batarelo" not in text:
        errors.append("HubSpot CRM/configuration approvers missing")
    if "Tahmineh Goljan, Faezeh Yazdani and Lucija Batarelo" not in text:
        errors.append("HubSpot OAuth approvers missing")
    if "No OAuth connection or A2 action approval is implied" not in text:
        errors.append("HubSpot approval boundary missing")

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing heading: {heading}")

    for boundary in REQUIRED_BOUNDARIES:
        if boundary.casefold() not in text.casefold():
            errors.append(f"missing safety or decision boundary: {boundary}")

    for state in REQUIRED_INTEGRATION_STATES:
        if state not in text:
            errors.append(f"missing integration state: {state}")

    lower_text = text.lower()
    for claim in FORBIDDEN_ACTIVE_CLAIMS:
        if claim.lower() in lower_text:
            errors.append(f"forbidden readiness/integration claim found: {claim}")

    result = {
        "artifact": str(CONTRACT),
        "contract_version": EXPECTED_VERSION,
        "expected_status": EXPECTED_STATUS,
        "approval_state": "approved_for_step_1c",
        "checks": {
            "required_headings": len(REQUIRED_HEADINGS),
            "required_boundaries": len(REQUIRED_BOUNDARIES),
            "required_integration_states": len(REQUIRED_INTEGRATION_STATES),
            "forbidden_active_claims": len(FORBIDDEN_ACTIVE_CLAIMS),
        },
        "errors": errors,
        "pass": not errors,
    }
    output_path = PROFILE_ROOT / "evaluations" / "step1b" / "contract-validation.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    result["validation_output"] = str(output_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
