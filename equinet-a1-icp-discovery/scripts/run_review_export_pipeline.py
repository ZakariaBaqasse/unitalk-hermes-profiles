#!/usr/bin/env python3
"""Run the deterministic Wave 3 review and export path with one process and one audit summary."""

from __future__ import annotations

import argparse
import fcntl
import json
import sys
from pathlib import Path

PROFILE_DIR = Path(__file__).resolve().parents[1]
REVIEW_SCRIPTS = PROFILE_DIR / "skills" / "ranked-prospect-review-package" / "scripts"
EXPORT_SCRIPTS = PROFILE_DIR / "skills" / "prospect-export" / "scripts"
for path in [REVIEW_SCRIPTS, EXPORT_SCRIPTS]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
from build_review_package import build, load_json  # noqa: E402
from export_review_package import export  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("review_input", type=Path)
    parser.add_argument("--review-output", type=Path, required=True)
    parser.add_argument("--export-dir", type=Path, required=True)
    parser.add_argument("--prefix", default="equinet-a1-review")
    parser.add_argument("--audit-output", type=Path)
    args = parser.parse_args()
    lock_path = PROFILE_DIR / "cache" / "a1-runtime.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_handle = lock_path.open("w", encoding="utf-8")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("INVALID: Another A1 deterministic run is already active (concurrency limit 1).", file=sys.stderr)
        return 1
    try:
        request = load_json(args.review_input)
        package = build(request)
        args.review_output.parent.mkdir(parents=True, exist_ok=True)
        args.review_output.write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        manifest = export(args.review_output, args.export_dir, args.prefix)
        summary = {
            "status": "passed",
            "package_id": package["package_id"],
            "candidate_count": package["summary"]["total"],
            "recommendations": {
                "accept": package["summary"]["accept"],
                "needs_research": package["summary"]["needs_research"],
                "reject": package["summary"]["reject"],
            },
            "integration_status": package["integration_status"],
            "human_decisions_pending": all(item["reviewer_decision"] == "pending" for item in package["candidates"]),
            "a2_handoffs_authorised": 0,
            "export_validation": manifest["validation"],
            "files": [entry["file_name"] for entry in manifest["files"]],
        }
        if args.audit_output:
            args.audit_output.parent.mkdir(parents=True, exist_ok=True)
            args.audit_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 0
    except Exception as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
