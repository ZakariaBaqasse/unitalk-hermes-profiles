#!/usr/bin/env python3
"""Independently verify the Step 9 release-candidate ZIP archive."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import zipfile
from pathlib import Path, PurePosixPath
import yaml

ROOT = Path(__file__).resolve().parents[1]
STEP9 = ROOT / "evaluations/step9"
PACKAGE_DIR = STEP9 / "package"
ARCHIVE = PACKAGE_DIR / "equinet-a2-no-integration-1.0.0-rc.1.zip"
SOURCE_MANIFEST = PACKAGE_DIR / "PACKAGE-MANIFEST.json"
EXTRACT = Path("/opt/data/tmp/equinet-a2-step9d-verify")
OUTPUT = STEP9 / "safe-archive-validation.json"
MEMBER_LIST = STEP9 / "archive-member-list.txt"
PLAN = STEP9 / "step9-plan.json"
ENV = ROOT / ".env"
PREFIX = "equinet-a2-no-integration-1.0.0-rc.1/"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def secret_values() -> list[bytes]:
    values = []
    if not ENV.exists():
        return values
    for line in ENV.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        _, value = stripped.split("=", 1)
        value = value.strip().strip('"').strip("'")
        if len(value) >= 8:
            values.append(value.encode())
    return values


def main() -> int:
    source_manifest = load(SOURCE_MANIFEST)
    shutil.rmtree(EXTRACT, ignore_errors=True)
    EXTRACT.mkdir(parents=True)
    with zipfile.ZipFile(ARCHIVE) as bundle:
        names = bundle.namelist()
        bad_member = bundle.testzip()
        unsafe = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts]
        bundle.extractall(EXTRACT)
    MEMBER_LIST.write_text("\n".join(names) + "\n", encoding="utf-8")

    expected = {item["archive_path"]: item for item in source_manifest["members"]}
    member_set = set(names)
    expected_special = {PREFIX + "README.md", PREFIX + "PACKAGE-MANIFEST.json"}
    member_match = member_set == set(expected) | expected_special
    hash_mismatches = []
    for archive_path, item in expected.items():
        extracted = EXTRACT / archive_path
        if not extracted.exists() or extracted.stat().st_size != item["bytes"] or sha(extracted) != item["sha256"]:
            hash_mismatches.append(archive_path)

    forbidden_names = [
        name
        for name in names
        if any(part.lower() in {".env", "auth.json", "credentials", "cache", "logs", "__pycache__"} or part.lower().endswith((".pem", ".key")) for part in PurePosixPath(name).parts)
    ]
    secret_hits = []
    secrets = secret_values()
    for name in names:
        data = (EXTRACT / name).read_bytes()
        if any(secret in data for secret in secrets):
            secret_hits.append(name)

    parse_errors = []
    parsed_counts = {"json": 0, "yaml": 0, "csv": 0, "markdown": 0, "python": 0}
    for name in names:
        path = EXTRACT / name
        suffix = path.suffix.lower()
        try:
            if suffix == ".json":
                json.loads(path.read_text(encoding="utf-8")); parsed_counts["json"] += 1
            elif suffix in {".yaml", ".yml"}:
                yaml.safe_load(path.read_text(encoding="utf-8")); parsed_counts["yaml"] += 1
            elif suffix == ".csv":
                with path.open(encoding="utf-8-sig", newline="") as handle:
                    list(csv.reader(handle)); parsed_counts["csv"] += 1
            elif suffix == ".md":
                if not path.read_text(encoding="utf-8").strip():
                    raise ValueError("empty Markdown")
                parsed_counts["markdown"] += 1
            elif suffix == ".py":
                compile(path.read_text(encoding="utf-8"), name, "exec"); parsed_counts["python"] += 1
        except Exception as error:
            parse_errors.append({"member": name, "error": str(error)})

    embedded_manifest = load(EXTRACT / (PREFIX + "PACKAGE-MANIFEST.json"))
    release_manifest_path = EXTRACT / (PREFIX + "evaluations/step9/release-candidate/release-candidate-manifest-1.0.0-rc.1.json")
    release_manifest = load(release_manifest_path)
    checks = {
        "archive_readable": bad_member is None,
        "safe_member_paths": not unsafe,
        "member_set_exact": member_match,
        "payload_hashes": not hash_mismatches,
        "forbidden_names_absent": not forbidden_names,
        "profile_secret_values_absent": not secret_hits,
        "formats_parse": not parse_errors,
        "embedded_manifest_matches_source": sha(EXTRACT / (PREFIX + "PACKAGE-MANIFEST.json")) == sha(SOURCE_MANIFEST),
        "manifest_non_recursive": embedded_manifest.get("manifest_self_hash_included") is False and embedded_manifest.get("archive_hash_included") is False,
        "release_candidate_not_promoted": release_manifest.get("promotion_performed") is False and release_manifest.get("approval_recorded") is False,
        "release_manifest_ready_for_step9d": release_manifest.get("status") == "ready_for_step9d_safe_packaging_not_approved",
    }
    result = {
        "record_type": "step9d_safe_archive_validation",
        "profile": "equinet-a2-enrichment",
        "release_id": "equinet-a2-no-integration-1.0.0-rc.1",
        "status": "pass_ready_for_step9e_review" if all(checks.values()) else "failed",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "archive": str(ARCHIVE.relative_to(ROOT)),
        "archive_bytes": ARCHIVE.stat().st_size,
        "archive_sha256": sha(ARCHIVE),
        "archive_member_count": len(names),
        "payload_member_count": source_manifest["payload_member_count"],
        "parsed_counts": parsed_counts,
        "hash_mismatches": hash_mismatches,
        "forbidden_names": forbidden_names,
        "secret_hits": secret_hits,
        "parse_errors": parse_errors,
        "promotion_performed": False,
        "approval_recorded": False,
        "external_actions": 0,
        "errors": [name for name, passed in checks.items() if not passed],
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    plan = load(PLAN)
    for phase in plan["phases"]:
        if phase["id"] == "9D":
            phase["status"] = "completed" if all(checks.values()) else "blocked"
        elif phase["id"] == "9E" and all(checks.values()):
            phase["status"] = "ready_for_severine_review"
    plan["status"] = "step9d_completed_ready_for_step9e_review" if all(checks.values()) else "step9d_blocked"
    PLAN.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": f"{result['checks_passed']}/{result['checks_total']}", "archive_members": len(names), "archive_bytes": result["archive_bytes"], "archive_sha256": result["archive_sha256"], "forbidden_names": len(forbidden_names), "secret_hits": len(secret_hits), "external_actions": 0}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
