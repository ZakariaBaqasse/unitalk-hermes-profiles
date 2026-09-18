#!/usr/bin/env python3
"""Build a deterministic, non-secret Step 9 release-candidate ZIP archive."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP9 = ROOT / "evaluations/step9"
PACKAGE_DIR = STEP9 / "package"
ARCHIVE = PACKAGE_DIR / "equinet-a2-no-integration-1.0.0-rc.1.zip"
PACKAGE_MANIFEST = PACKAGE_DIR / "PACKAGE-MANIFEST.json"
README = PACKAGE_DIR / "README.md"
INVENTORY = STEP9 / "release-candidate-inventory.json"
RC_MANIFEST = STEP9 / "release-candidate/release-candidate-manifest-1.0.0-rc.1.json"
PHASE9C = STEP9 / "phase9c-validation.json"
PLAN = STEP9 / "step9-plan.json"
DELIVERY = STEP9 / "delivery"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def main() -> int:
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    inventory = load(INVENTORY)
    phase9c = load(PHASE9C)
    if phase9c.get("status") != "pass_ready_for_step9d":
        raise RuntimeError("Step 9C is not ready for safe packaging")
    payload_paths = {item["path"] for item in inventory["items"]}
    payload_paths.update(
        {
            str((DELIVERY / "A2-NO-INTEGRATION-CONFIGURATION-PACKAGE.md").relative_to(ROOT)),
            str((DELIVERY / "A2-MANUAL-NO-INTEGRATION-RUNBOOK.md").relative_to(ROOT)),
            str((DELIVERY / "A2-STEP9-EVALUATION-REPORT.md").relative_to(ROOT)),
            str((DELIVERY / "A2-OPEN-ITEMS-REGISTER.md").relative_to(ROOT)),
            str((DELIVERY / "A2-STEP9-ACCEPTANCE-REVIEW.md").relative_to(ROOT)),
            str(RC_MANIFEST.relative_to(ROOT)),
            str(PHASE9C.relative_to(ROOT)),
            str(PLAN.relative_to(ROOT)),
            "evaluations/step9/phase9a-validation.json",
            "evaluations/step9/regression/phase9b-regression.json",
            "evaluations/step9/STEP-9A-CORRECTION-PROPAGATION-REVIEW.md",
            "evaluations/step9/STEP-9B-OFFLINE-REGRESSION-REVIEW.md",
        }
    )
    forbidden_parts = {".env", "auth.json", "credentials", "cache", "logs", "__pycache__"}
    entries = []
    for rel in sorted(payload_paths):
        path = ROOT / rel
        if not path.is_file():
            raise RuntimeError(f"Missing package payload: {rel}")
        lowered = rel.lower().split("/")
        if any(part in forbidden_parts or part.endswith(".key") or part.endswith(".pem") for part in lowered):
            raise RuntimeError(f"Forbidden package member: {rel}")
        entries.append(
            {
                "source_path": rel,
                "archive_path": f"equinet-a2-no-integration-1.0.0-rc.1/{rel}",
                "bytes": path.stat().st_size,
                "sha256": sha(path),
            }
        )
    readme_text = """# Equinet A2 No-Integration Release Candidate

This archive is an internal Equinet/Unitalk release-candidate package. It contains configuration, skills, deterministic operators, validation evidence and delivery documentation. It contains no credentials, `.env` files, authentication stores or runtime logs.

Status: `READY FOR STEP 9E REVIEW — NOT APPROVED OR ACTIVE`.

This package does not constitute production acceptance, contractual delivery acceptance, CRM-write authority or outreach permission.
"""
    README.write_text(readme_text, encoding="utf-8")
    package_manifest = {
        "record_type": "step9_safe_package_manifest",
        "release_id": "equinet-a2-no-integration-1.0.0-rc.1",
        "status": "ready_for_step9e_review_not_approved",
        "payload_member_count": len(entries),
        "payload_total_bytes": sum(item["bytes"] for item in entries),
        "members": entries,
        "manifest_self_hash_included": False,
        "archive_hash_included": False,
        "forbidden_content_policy": ["no .env", "no credentials", "no auth stores", "no cache", "no logs", "no private keys"],
        "promotion_performed": False,
        "external_actions": 0,
    }
    PACKAGE_MANIFEST.write_text(json.dumps(package_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    archive_members = [(README, "equinet-a2-no-integration-1.0.0-rc.1/README.md"), (PACKAGE_MANIFEST, "equinet-a2-no-integration-1.0.0-rc.1/PACKAGE-MANIFEST.json")]
    archive_members.extend((ROOT / item["source_path"], item["archive_path"]) for item in entries)
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for source, archive_name in sorted(archive_members, key=lambda item: item[1]):
            info = zipfile.ZipInfo(archive_name, date_time=(2026, 8, 30, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, source.read_bytes())
    print(json.dumps({"status": package_manifest["status"], "archive": str(ARCHIVE.relative_to(ROOT)), "payload_members": len(entries), "archive_members": len(entries) + 2, "archive_bytes": ARCHIVE.stat().st_size, "archive_sha256": sha(ARCHIVE), "promotion_performed": False, "external_actions": 0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
