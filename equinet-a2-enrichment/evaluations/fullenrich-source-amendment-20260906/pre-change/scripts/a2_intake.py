#!/usr/bin/env python3
"""Stable Wave 1 intake command for Equinet A2."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from initialize_a2_record import (
    build_record,
    canonical_hash,
    load_json,
    reserve_idempotency,
    write_idempotent,
)

VERSION = "0.1.0"


def intake(handoff: dict, output: Path | None = None, ledger: Path | None = None) -> tuple[dict, dict | None]:
    record = build_record(handoff)
    summary = {
        "valid": True,
        "command": "a2-intake",
        "version": VERSION,
        "handoff_id": handoff["handoff_id"],
        "handoff_sha256": canonical_hash(handoff),
        "a2_record_id": record["record_metadata"]["a2_record_id"],
        "record_revision_id": record["record_metadata"]["record_revision_id"],
        "record_sha256": canonical_hash(record),
        "operating_scope": record["enrichment_scope"]["operating_scope"],
        "workflow_state": record["workflow"]["state"],
        "external_actions": 0,
    }
    if output is not None:
        ledger_path = ledger or output.parent / ".a2-initialisation-ledger.json"
        summary["ledger_status"] = reserve_idempotency(ledger_path, handoff, record)
        summary["write_status"] = write_idempotent(output, record)
        summary["output"] = str(output)
    return summary, record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handoff", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--include-record", action="store_true")
    args = parser.parse_args()
    try:
        handoff = load_json(args.handoff)
        summary, record = intake(handoff, args.output, args.ledger)
        if args.include_record:
            summary["record"] = record
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"valid": False, "command": "a2-intake", "version": VERSION, "error": str(exc), "external_actions": 0}, indent=2, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
