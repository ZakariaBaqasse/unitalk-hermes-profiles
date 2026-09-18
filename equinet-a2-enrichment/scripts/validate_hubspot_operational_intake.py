#!/usr/bin/env python3
"""Validate Equinet's HubSpot operational metadata intake artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

PROFILE_ROOT = Path(__file__).resolve().parents[1]
STATUS_DOC = Path("/opt/data/profiles/equinet/attachments/HubSpot_Status_Model_Overview (1).docx")
OWNERSHIP_DOC = Path("/opt/data/profiles/equinet/attachments/HubSpot_Users_Teams_Ownership_Model.docx")
PROCESS_CSV = Path("/opt/data/profiles/equinet/attachments/Sales_Marketing_Process_Inventory.csv")
MANIFEST = PROFILE_ROOT / "foundations" / "hubspot" / "HUBSPOT-OPERATIONAL-METADATA-MANIFEST.json"
AUDIT = PROFILE_ROOT / "foundations" / "hubspot" / "HUBSPOT-OPERATIONAL-MODEL-INTAKE-AUDIT.md"
SUMMARY = PROFILE_ROOT / "evaluations" / "hubspot-intake" / "process-inventory-summary.json"
OUTPUT = PROFILE_ROOT / "evaluations" / "hubspot-intake" / "operational-intake-validation.json"

EXPECTED_HASHES = {
    "status": "fa96082eeb69fca75caa3b5ec61723d572e5e8513377802498b109120df754b3",
    "ownership": "401f48738283c8e1e0ac013be025575893fbf6bc236b3c7c74352fabfbbdacb2",
    "process": "8212df536e1a5560861b70882fd3031c89758b41b635cf5b97ee802724536bdb",
}
STATUS_PHRASES = [
    "Contact Lifecycle Stages",
    "Marketing Qualified Lead",
    "Sales Qualified Lead",
    "Decision Maker Bought-In",
    "Sample Request Pipeline",
    "Awaiting Approval",
    "Support Pipeline",
    "Rename 1",
    "Lead Status",
    "Account Status",
]
OWNERSHIP_PHRASES = [
    "Active users (21)",
    "Inactive / deactivated users (9)",
    "EQUINET Team (6 members)",
    "Mustad USA Sales Team (12 members)",
    "No job titles/roles are currently assigned",
    "Owner-Assignment & Reassignment Rules",
    "Not Available",
    "Backup-Owner Rules",
    "no CRM property enforces ownership restrictions",
]
AUDIT_PHRASES = [
    "OPERATIONAL METADATA SNAPSHOT RECEIVED — NO LIVE HUBSPOT CONNECTION",
    "No current enrichment-review asset",
    "all A2 HubSpot writes remain blocked",
    "A2 must not auto-assign an owner or territory",
    "28",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    return "\n".join(node.text or "" for node in root.findall(".//w:t", namespace))


def main() -> int:
    errors: list[str] = []
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    audit_text = AUDIT.read_text(encoding="utf-8")
    status_text = extract_docx_text(STATUS_DOC)
    ownership_text = extract_docx_text(OWNERSHIP_DOC)

    actual_hashes = {
        "status": sha256(STATUS_DOC),
        "ownership": sha256(OWNERSHIP_DOC),
        "process": sha256(PROCESS_CSV),
    }
    for key, expected in EXPECTED_HASHES.items():
        if actual_hashes[key] != expected:
            errors.append(f"{key} source hash mismatch")

    manifest_hashes = {
        "status": manifest["inputs"]["status_model"]["sha256"],
        "ownership": manifest["inputs"]["users_teams_ownership"]["sha256"],
        "process": manifest["inputs"]["sales_marketing_process_inventory"]["sha256"],
    }
    if manifest_hashes != actual_hashes:
        errors.append("manifest hashes do not match source files")

    for phrase in STATUS_PHRASES:
        if phrase.casefold() not in status_text.casefold():
            errors.append(f"status-model phrase missing: {phrase}")
    for phrase in OWNERSHIP_PHRASES:
        if phrase.casefold() not in ownership_text.casefold():
            errors.append(f"ownership-model phrase missing: {phrase}")

    with PROCESS_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    statuses = Counter(row["Status or list type"] for row in rows)
    asset_types = Counter(row["Asset type"] for row in rows)
    if len(rows) != 68:
        errors.append(f"expected 68 process rows, found {len(rows)}")
    if asset_types != Counter({"Workflow": 33, "List": 32, "Audit finding": 3}):
        errors.append(f"unexpected asset-type counts: {dict(asset_types)}")
    if statuses.get("Enabled") != 28 or statuses.get("Disabled") != 5:
        errors.append(f"unexpected workflow status counts: {dict(statuses)}")
    if summary.get("enabled_workflow_count") != 28 or summary.get("audit_finding_count") != 3:
        errors.append("process summary counts do not match expected values")

    for phrase in AUDIT_PHRASES:
        if phrase.casefold() not in audit_text.casefold():
            errors.append(f"required audit statement missing: {phrase}")

    if "no_live_connection" not in manifest["status"]:
        errors.append("manifest must preserve no-live-connection status")

    result = {
        "source_hashes": actual_hashes,
        "status_model_checks": len(STATUS_PHRASES),
        "ownership_model_checks": len(OWNERSHIP_PHRASES),
        "process_inventory": {
            "rows": len(rows),
            "asset_types": dict(asset_types),
            "statuses": dict(statuses),
        },
        "manifest_status": manifest["status"],
        "errors": errors,
        "pass": not errors,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
