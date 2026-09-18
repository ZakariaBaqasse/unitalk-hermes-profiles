#!/usr/bin/env python3
"""Deterministic static validator for the Equinet A2 Step 2A design."""

from __future__ import annotations

import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
DESIGN = PROFILE_ROOT / "foundations" / "A2-CANONICAL-RECORD-DESIGN.md"
OUTPUT = PROFILE_ROOT / "evaluations" / "step2a" / "design-validation.json"
EXPECTED_VERSION = "0.1.0"
EXPECTED_STATUS = "APPROVED BY UNITALK OPERATIONS FOR STEP 2B"

REQUIRED_HEADINGS = [
    "## 1. Purpose",
    "## 2. Approved dependencies",
    "## 3. Design principles",
    "## 4. Record identity and revision model",
    "## 5. Canonical record sections",
    "## 6. Source handoff ownership",
    "## 7. Subject and entity model",
    "## 8. Generic field-assessment model",
    "## 9. Evidence registry ownership",
    "## 10. Data-quality ownership",
    "## 11. Duplicate and eligibility ownership",
    "## 12. Requalification and score-revision ownership",
    "## 13. Human review ownership",
    "## 14. Workflow state ownership",
    "## 15. System-reference ownership",
    "## 16. Governance ownership",
    "## 17. Audit and consumption ownership",
    "## 18. Mutability classes",
    "## 19. Source-of-truth precedence",
    "## 20. Stable schema versus later configuration",
    "## 21. Information deliberately nullable until integration",
    "## 22. Open items not blocking Step 2A",
    "## 23. Step 2A acceptance criteria",
    "## 24. Decisions confirmed by Séverine",
]

REQUIRED_SECTIONS = [
    "`record_metadata`",
    "`source_handoff`",
    "`subject`",
    "`enrichment_scope`",
    "`field_assessments`",
    "`evidence_registry`",
    "`data_quality`",
    "`duplicate_and_eligibility`",
    "`requalification`",
    "`review`",
    "`workflow`",
    "`system_references`",
    "`governance`",
    "`audit_and_consumption`",
]

REQUIRED_BOUNDARIES = [
    "One A2 record lineage per accepted A1 handoff version",
    "Every accepted change creates a new A2 record revision",
    "A2 must never modify this section",
    "generic `field_assessments[]`",
    "baseline + observations + one proposed resolution + human decision + separate application state",
    "A2-specific evidence namespace",
    "both field-level and record-level review",
    "A1 owns evidence acceptance and deterministic rescoring",
    "null never means checked, absent or eligible",
    "Exact HubSpot object and property mappings remain outside the canonical schema",
]

FORBIDDEN_CLAIMS = [
    "production-ready",
    "contractually accepted",
    "HubSpot is connected",
    "Twenty is connected",
    "A2 calculates the revised score",
    "A2 may overwrite the A1 score",
]


def main() -> int:
    errors: list[str] = []
    text = DESIGN.read_text(encoding="utf-8") if DESIGN.exists() else ""

    if f"**Design version:** `{EXPECTED_VERSION}`" not in text:
        errors.append("design version missing or incorrect")
    if f"**Status:** `{EXPECTED_STATUS}`" not in text:
        errors.append("design status missing or incorrect")
    if "**Decision:** `APPROVED AS DRAFTED`" not in text:
        errors.append("recorded Step 2A decision missing")
    if "**Approver:** Séverine, Unitalk Operations" not in text:
        errors.append("recorded Step 2A approver missing")

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing heading: {heading}")

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"missing canonical section: {section}")

    for boundary in REQUIRED_BOUNDARIES:
        if boundary.casefold() not in text.casefold():
            errors.append(f"missing ownership/design boundary: {boundary}")

    for decision_number in range(1, 10):
        if f"| R{decision_number} |" not in text:
            errors.append(f"missing decision R{decision_number}")

    lower_text = text.casefold()
    for claim in FORBIDDEN_CLAIMS:
        if claim.casefold() in lower_text:
            errors.append(f"forbidden readiness or ownership claim found: {claim}")

    result = {
        "step": "2A",
        "artifact": str(DESIGN),
        "design_version": EXPECTED_VERSION,
        "approval_state": "approved_for_step_2b",
        "checks": {
            "required_headings": len(REQUIRED_HEADINGS),
            "canonical_sections": len(REQUIRED_SECTIONS),
            "ownership_boundaries": len(REQUIRED_BOUNDARIES),
            "decisions": 9,
            "forbidden_claims": len(FORBIDDEN_CLAIMS),
        },
        "errors": errors,
        "pass": not errors,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
