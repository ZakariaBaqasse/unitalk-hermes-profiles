#!/usr/bin/env python3
"""Validate the Equinet HubSpot metadata intake artifacts and source integrity."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
IMAGE = Path("/opt/data/profiles/equinet/attachments/data-model-objects (1).png")
CSV_SOURCE = Path("/opt/data/profiles/equinet/attachments/Property_Definitions (1).csv")
MANIFEST = PROFILE_ROOT / "foundations" / "hubspot" / "HUBSPOT-SNAPSHOT-MANIFEST.json"
AUDIT = PROFILE_ROOT / "foundations" / "hubspot" / "HUBSPOT-DATA-MODEL-INTAKE-AUDIT.md"
SUMMARY = PROFILE_ROOT / "evaluations" / "hubspot-intake" / "property-inventory-summary.json"
OUTPUT = PROFILE_ROOT / "evaluations" / "hubspot-intake" / "intake-validation.json"

EXPECTED_HASHES = {
    "image": "1aac099ce0158752e336e813dfe56728a8b7a66f28448a8d098193072bcfce39",
    "csv": "3303992627bad953e28913eaf3b19cdc998fc0c6f3f6f29ef455d788e8c9b952",
}
EXPECTED_OBJECT_COUNTS = {
    "Company": 227,
    "Complaints": 28,
    "Contact": 431,
    "Deal": 145,
    "Sample Requests": 41,
    "Ticket": 78,
}
REQUIRED_AUDIT_PHRASES = [
    "PARTIAL METADATA SNAPSHOT RECEIVED — NO LIVE HUBSPOT CONNECTION",
    "A2 mapping draft: now possible",
    "Live HubSpot read: unavailable",
    "Live HubSpot write: unavailable and unauthorised",
    "Horse-count ranges overlap",
    "Existing score fields are not the A1 score",
    "Writable does not mean authorised",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    errors: list[str] = []
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    audit_text = AUDIT.read_text(encoding="utf-8")

    image_hash = sha256(IMAGE)
    csv_hash = sha256(CSV_SOURCE)
    if image_hash != EXPECTED_HASHES["image"]:
        errors.append("data-model image hash mismatch")
    if csv_hash != EXPECTED_HASHES["csv"]:
        errors.append("property-definition CSV hash mismatch")
    if manifest["inputs"]["data_model_image"]["sha256"] != image_hash:
        errors.append("manifest image hash mismatch")
    if manifest["inputs"]["property_definitions"]["sha256"] != csv_hash:
        errors.append("manifest CSV hash mismatch")

    with CSV_SOURCE.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    counts = dict(Counter(row["Object"] for row in rows))
    if len(rows) != 950:
        errors.append(f"expected 950 property rows, found {len(rows)}")
    if counts != EXPECTED_OBJECT_COUNTS:
        errors.append(f"object counts changed: {counts}")
    if summary.get("row_count") != len(rows):
        errors.append("summary row count mismatch")

    for object_name, expected_count in EXPECTED_OBJECT_COUNTS.items():
        manifest_count = manifest["property_export_objects"][object_name]["properties"]
        if manifest_count != expected_count:
            errors.append(f"manifest property count mismatch for {object_name}")

    for phrase in REQUIRED_AUDIT_PHRASES:
        if phrase not in audit_text:
            errors.append(f"required audit statement missing: {phrase}")

    if "no_live_connection" not in manifest["status"]:
        errors.append("manifest must preserve no-live-connection status")

    result = {
        "source_hashes": {"image": image_hash, "csv": csv_hash},
        "property_rows": len(rows),
        "object_counts": counts,
        "manifest_status": manifest["status"],
        "required_audit_statements": len(REQUIRED_AUDIT_PHRASES),
        "errors": errors,
        "pass": not errors,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
