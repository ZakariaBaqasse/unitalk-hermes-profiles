#!/usr/bin/env python3
"""Validate the Equinet HubSpot object and governance confirmation register."""

from __future__ import annotations

import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
REGISTER = PROFILE_ROOT / "foundations" / "hubspot" / "HUBSPOT-GOVERNANCE-CONFIRMATIONS.json"
DOCUMENT = PROFILE_ROOT / "foundations" / "hubspot" / "HUBSPOT-OBJECT-AND-GOVERNANCE-CONFIRMATIONS.md"
OUTPUT = PROFILE_ROOT / "evaluations" / "hubspot-intake" / "governance-confirmation-validation.json"

EXPECTED = {
    "crm_business_owners": ["Tahmineh Goljan", "Lucija Batarelo"],
    "property_object_workflow_approvers": ["Tahmineh Goljan", "Lucija Batarelo"],
    "unitalk_oauth_connection_approvers": ["Tahmineh Goljan", "Faezeh Yazdani", "Lucija Batarelo"],
}
REQUIRED_BOUNDARIES = [
    "Super Admin status does not itself approve A2 business outputs",
    "service or placeholder account and cannot serve as a human approver",
    "The A2 business reviewer and backup reviewer remain to be confirmed separately",
    "no OAuth connection or scope has yet been granted or verified",
]


def main() -> int:
    errors = []
    register = json.loads(REGISTER.read_text(encoding="utf-8"))
    document = DOCUMENT.read_text(encoding="utf-8")

    objects = register["object_decisions"]
    if objects["creator"]["exists_in_hubspot"] is not False:
        errors.append("Creator must be recorded as absent")
    if objects["campaign"]["object_kind"] != "standard_hubspot_object" or objects["campaign"]["is_custom_object"] is not False:
        errors.append("Campaign must be recorded as a standard, non-custom HubSpot object")
    if register["object_decisions"]["confirmed_custom_objects"] != ["Complaints", "Sample Requests"]:
        errors.append("confirmed custom-object list mismatch")

    governance = register["hubspot_governance"]
    for key, expected in EXPECTED.items():
        if governance.get(key) != expected:
            errors.append(f"governance list mismatch: {key}")

    super_admins = governance.get("super_admins", [])
    if len(super_admins) != 4:
        errors.append("expected four Super Admin identities")
    mustad_account = [item for item in super_admins if item.get("name") == "Mustad HubSpot"]
    if not mustad_account or mustad_account[0].get("identity_type") != "service_or_placeholder_account":
        errors.append("Mustad HubSpot must be classified as a service/placeholder account")

    for phrase in REQUIRED_BOUNDARIES:
        if phrase.casefold() not in document.casefold():
            errors.append(f"required authority boundary missing: {phrase}")

    result = {
        "object_confirmations": {
            "creator_absent": objects["creator"]["exists_in_hubspot"] is False,
            "campaign_standard": objects["campaign"]["object_kind"] == "standard_hubspot_object",
            "custom_objects": objects["confirmed_custom_objects"],
        },
        "governance_lists_checked": len(EXPECTED),
        "authority_boundaries_checked": len(REQUIRED_BOUNDARIES),
        "errors": errors,
        "pass": not errors,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
