#!/usr/bin/env python3
"""Build the deterministic final Equinet A2 no-integration release archive."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP9 = ROOT / "evaluations/step9"
PACKAGE_DIR = STEP9 / "package"
ARCHIVE = PACKAGE_DIR / "equinet-a2-no-integration-1.0.0.zip"
MANIFEST = PACKAGE_DIR / "PACKAGE-MANIFEST-1.0.0.json"
README = PACKAGE_DIR / "README-1.0.0.md"
ACTIVE = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"
FINAL_RELEASE = ROOT / "foundations/contracts/runtime/a2-no-integration-release-manifest-1.0.0.json"
ACCEPTANCE = STEP9 / "acceptance-record.json"
PREFIX = "equinet-a2-no-integration-1.0.0/"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    active = load(ACTIVE)
    release = load(FINAL_RELEASE)
    acceptance = load(ACCEPTANCE)
    if active.get("status") != "pilot_ready_no_integration" or release.get("status") != "pilot_ready_no_integration":
        raise RuntimeError("Final release status mismatch")
    if acceptance.get("decision") != "approved_pilot_ready_no_integration":
        raise RuntimeError("Final Step 9 approval is missing")
    paths = {item["path"] for item in active["active_files"]}
    paths.update(
        {
            str(FINAL_RELEASE.relative_to(ROOT)),
            str(ACCEPTANCE.relative_to(ROOT)),
            "evaluations/step8/acceptance-record.json",
            "evaluations/step8/final-closure-validation.json",
            "evaluations/step8/STEP-8-FINAL-ACCEPTANCE.md",
            "evaluations/step9/phase9a-validation.json",
            "evaluations/step9/regression/phase9b-regression.json",
            "evaluations/step9/phase9c-validation.json",
            "evaluations/step9/safe-archive-validation.json",
            "evaluations/step9/replay/replay-manifest.json",
            "evaluations/step9/STEP-9A-CORRECTION-PROPAGATION-REVIEW.md",
            "evaluations/step9/STEP-9B-OFFLINE-REGRESSION-REVIEW.md",
            "evaluations/step9/STEP-8-CLOSURE-READINESS.md",
            "evaluations/step9/delivery/A2-NO-INTEGRATION-CONFIGURATION-PACKAGE.md",
            "evaluations/step9/delivery/A2-MANUAL-NO-INTEGRATION-RUNBOOK.md",
            "evaluations/step9/delivery/A2-STEP9-EVALUATION-REPORT.md",
            "evaluations/step9/delivery/A2-OPEN-ITEMS-REGISTER.md",
            "evaluations/step9/delivery/A2-STEP9-ACCEPTANCE-REVIEW.md",
            "deliverables/A2-DELIVERY-STATUS-AND-ROADMAP.md",
        }
    )
    # One historical review path has a different directory name; keep only files that exist.
    paths.discard("evaluations/step9/STEP-8-CLOSURE-READINESS.md")
    forbidden = {".env", "auth.json", "credentials", "cache", "logs", "__pycache__"}
    entries = []
    for rel in sorted(paths):
        path = ROOT / rel
        if not path.is_file():
            raise RuntimeError(f"Missing final package payload: {rel}")
        if any(part.lower() in forbidden or part.lower().endswith((".pem", ".key")) for part in Path(rel).parts):
            raise RuntimeError(f"Forbidden package payload: {rel}")
        entries.append({"source_path": rel, "archive_path": PREFIX + rel, "bytes": path.stat().st_size, "sha256": sha(path)})
    README.write_text(
        """# Equinet A2 No-Integration Release 1.0.0

Status: `PILOT_READY_NO_INTEGRATION`.

This package supports controlled, human-reviewed no-integration pilot use. It is not integrated or production acceptance and does not authorise CRM writes, outreach, publication, financial action or durable downstream delivery.

The archive excludes credentials, `.env`, authentication stores, caches and logs.
""",
        encoding="utf-8",
    )
    package_manifest = {
        "record_type": "step9_final_safe_package_manifest",
        "release_id": "equinet-a2-no-integration-1.0.0",
        "status": "pilot_ready_no_integration",
        "payload_member_count": len(entries),
        "payload_total_bytes": sum(item["bytes"] for item in entries),
        "members": entries,
        "manifest_self_hash_included": False,
        "archive_hash_included": False,
        "production_acceptance": False,
        "contractual_acceptance": False,
        "external_actions": 0,
    }
    MANIFEST.write_text(json.dumps(package_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    archive_members = [(README, PREFIX + "README.md"), (MANIFEST, PREFIX + "PACKAGE-MANIFEST.json")]
    archive_members.extend((ROOT / item["source_path"], item["archive_path"]) for item in entries)
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for source, archive_name in sorted(archive_members, key=lambda item: item[1]):
            info = zipfile.ZipInfo(archive_name, date_time=(2026, 8, 30, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, source.read_bytes())
    print(json.dumps({"status": "pilot_ready_no_integration", "archive": str(ARCHIVE.relative_to(ROOT)), "payload_members": len(entries), "archive_members": len(entries) + 2, "archive_bytes": ARCHIVE.stat().st_size, "archive_sha256": sha(ARCHIVE), "external_actions": 0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
