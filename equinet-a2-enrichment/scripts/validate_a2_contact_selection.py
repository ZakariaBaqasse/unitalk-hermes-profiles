#!/usr/bin/env python3
"""Validate Equinet A2 selected-contact limits and review routing."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ALLOWED_SECOND_REASONS = {"large_organisation", "shared_purchasing_or_operational_responsibility"}
ALLOWED_PRIORITIES = {"primary", "secondary", "review_only"}


def validate(request: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    contacts = request.get("selected_contacts")
    if not isinstance(contacts, list):
        contacts = []
        errors.append("selected_contacts must be an array")
    if len(contacts) > 2:
        errors.append("at most two named contacts may be selected")
    ids = [item.get("contact_id") for item in contacts if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        errors.append("selected contact IDs must be unique")
    for index, contact in enumerate(contacts):
        if not isinstance(contact, dict) or not contact.get("contact_id") or not contact.get("source_role_title"):
            errors.append(f"selected_contacts[{index}] requires contact_id and source_role_title")
            continue
        if contact.get("target_role_priority") not in ALLOWED_PRIORITIES:
            errors.append(f"selected_contacts[{index}] is not an approved target-role priority")
        if contact.get("unrelated_role") is True:
            errors.append(f"selected_contacts[{index}] cannot be an unrelated role")
    reason = request.get("second_contact_reason")
    if len(contacts) == 2 and reason not in ALLOWED_SECOND_REASONS:
        errors.append("a second selected contact requires an approved reason")
    if len(contacts) < 2 and reason is not None:
        errors.append("second_contact_reason requires exactly two selected contacts")
    target_role_not_found = request.get("target_role_not_found") is True
    if target_role_not_found and contacts:
        errors.append("target_role_not_found cannot coexist with selected contacts")
    status = "valid"
    label = None
    workflow = "continue_enrichment"
    if not errors and not contacts:
        if not target_role_not_found:
            errors.append("zero selected contacts requires target_role_not_found")
        else:
            status = "contact_needed"
            label = "Contact Needed / Needs Review"
            workflow = "review_required" if request.get("research_exhausted") is True else "enrichment_in_progress"
    if errors:
        status = "invalid"
        workflow = "processing_failed"
    return {
        "status": status,
        "selected_contact_count": len(contacts),
        "review_queue_label": label,
        "workflow_recommendation": workflow,
        "outreach_authorized": False,
        "crm_write_authorized": False,
        "external_actions": 0,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(json.loads(args.request.read_text(encoding="utf-8")))
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 1 if result["status"] == "invalid" else 0


if __name__ == "__main__":
    raise SystemExit(main())
