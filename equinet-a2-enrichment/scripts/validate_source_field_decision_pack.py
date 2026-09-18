#!/usr/bin/env python3
"""Validate the draft A2 source and field decision pack."""

from __future__ import annotations

import csv
import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
PACK = PROFILE_ROOT / "foundations" / "sources" / "A2-SOURCE-AND-FIELD-DECISION-PACK.md"
TEMPLATE = PROFILE_ROOT / "foundations" / "sources" / "A2-EQUINET-FIELD-DECISION-TEMPLATE.csv"
SLIM_TEMPLATE = PROFILE_ROOT / "foundations" / "sources" / "A2-EQUINET-CLIENT-DECISION-TEMPLATE-SLIM.csv"
OUTPUT = PROFILE_ROOT / "evaluations" / "sources" / "source-field-decision-pack-validation.json"

REQUIRED_PHRASES = [
    "A source approved for A1 is not automatically approved for new A2 collection",
    "Prospect's official business website",
    "Consent, opt-out, customer, Deal and sequence status",
    "A1 owns scoring",
    "A2 business field catalogue: incomplete",
    "Commercial enrichment provider: none approved or connected",
    "LinkedIn/Social automation: prohibited without approved official access",
    "Unitalk and Equinet must jointly approve",
]
FORBIDDEN_CLAIMS = [
    "A2 source register: approved",
    "commercial enrichment provider: connected",
    "LinkedIn automation: approved",
    "HubSpot live records: available",
]
REQUIRED_TEMPLATE_FIELDS = {
    "professional_email",
    "business_phone",
    "mobile_phone",
    "current_role_title",
    "buying_role",
    "exact_horse_count",
    "horse_count_range",
    "professional_status",
    "certifications",
    "service_area",
    "client_base_summary",
    "recent_professional_activity",
    "social_signals",
    "mutual_connections",
    "contact_verification",
    "record_data_quality",
    "outreach_eligibility",
    "record_owner",
}
REQUIRED_SLIM_DECISIONS = {
    "Target job roles — Farrier",
    "Target job roles — Horse Owner",
    "Contact-selection limit",
    "Minimum contactability",
    "Personal email and mobile/direct dial",
    "Farrier enrichment priorities",
    "Horse Owner enrichment priorities",
    "Horse-count range taxonomy",
    "LinkedIn and social use",
    "A2 reviewer and backup",
    "Paid provider and budget",
    "Owner and territory assignment",
}


def main() -> int:
    errors = []
    text = PACK.read_text(encoding="utf-8")
    for phrase in REQUIRED_PHRASES:
        if phrase.casefold() not in text.casefold():
            errors.append(f"required decision boundary missing: {phrase}")
    for claim in FORBIDDEN_CLAIMS:
        if claim.casefold() in text.casefold():
            errors.append(f"forbidden activation claim found: {claim}")

    with TEMPLATE.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fields = {row["Canonical field candidate"] for row in rows}
    missing_fields = sorted(REQUIRED_TEMPLATE_FIELDS - fields)
    if missing_fields:
        errors.append("missing decision-template fields: " + ", ".join(missing_fields))
    if len(rows) < 25:
        errors.append(f"expected at least 25 field-decision rows, found {len(rows)}")

    with SLIM_TEMPLATE.open("r", encoding="utf-8", newline="") as handle:
        slim_rows = list(csv.DictReader(handle))
    slim_decisions = {row["Decision area"] for row in slim_rows}
    missing_slim = sorted(REQUIRED_SLIM_DECISIONS - slim_decisions)
    if missing_slim:
        errors.append("missing slim client decisions: " + ", ".join(missing_slim))
    if len(slim_rows) != 12:
        errors.append(f"expected 12 slim client-decision rows, found {len(slim_rows)}")

    result = {
        "pack": str(PACK),
        "template": str(TEMPLATE),
        "slim_client_template": str(SLIM_TEMPLATE),
        "required_boundaries_checked": len(REQUIRED_PHRASES),
        "forbidden_claims_checked": len(FORBIDDEN_CLAIMS),
        "field_decision_rows": len(rows),
        "slim_client_decision_rows": len(slim_rows),
        "required_field_candidates": len(REQUIRED_TEMPLATE_FIELDS),
        "errors": errors,
        "pass": not errors,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
