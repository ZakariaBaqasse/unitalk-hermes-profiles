#!/usr/bin/env python3
"""Independently validate the promoted A2 no-integration release and final archive."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path, PurePosixPath
import yaml

ROOT = Path(__file__).resolve().parents[1]
STEP9 = ROOT / "evaluations/step9"
ARCHIVE = STEP9 / "package/equinet-a2-no-integration-1.0.0.zip"
PACKAGE_MANIFEST = STEP9 / "package/PACKAGE-MANIFEST-1.0.0.json"
ACTIVE = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"
POLICY = ROOT / "foundations/contracts/runtime/a2-no-integration-runtime-policy-1.0.0.yaml"
RELEASE = ROOT / "foundations/contracts/runtime/a2-no-integration-release-manifest-1.0.0.json"
ACCEPTANCE = STEP9 / "acceptance-record.json"
LANGUAGE = ROOT / "evaluations/foundation-clarifications/language-audit.json"
CONFIG = ROOT / "config.yaml"
SOUL = ROOT / "SOUL.md"
PLAN = STEP9 / "step9-plan.json"
OUTPUT = STEP9 / "final-release-validation.json"
SUMMARY = STEP9 / "FINAL-RELEASE-SUMMARY.md"
MEMBERS = STEP9 / "final-archive-member-list.txt"
EXTRACT = Path("/opt/data/tmp/equinet-a2-step9e-final-verify")
PREFIX = "equinet-a2-no-integration-1.0.0/"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def secret_values() -> list[bytes]:
    env = ROOT / ".env"
    values = []
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                if len(value) >= 8:
                    values.append(value.encode())
    return values


def main() -> int:
    active = load(ACTIVE)
    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    release = load(RELEASE)
    acceptance = load(ACCEPTANCE)
    language = load(LANGUAGE)
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    package = load(PACKAGE_MANIFEST)
    soul = SOUL.read_text(encoding="utf-8")

    active_mismatches = []
    for item in active["active_files"]:
        path = ROOT / item["path"]
        if not path.exists() or path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
            active_mismatches.append(item["path"])
    skill_errors = []
    for item in active["skills"]:
        path = ROOT / item["path"]
        text = path.read_text(encoding="utf-8")
        found = re.search(r"(?im)^\*\*Version:\*\*\s*`?([^`\s]+)", text)
        actual_version = found.group(1) if found else None
        if actual_version != item["version"] or item["status"] != "pilot_ready_no_integration" or sha(path) != item["sha256"]:
            skill_errors.append(item["skill_id"])

    shutil.rmtree(EXTRACT, ignore_errors=True)
    EXTRACT.mkdir(parents=True)
    with zipfile.ZipFile(ARCHIVE) as bundle:
        names = bundle.namelist()
        bad_member = bundle.testzip()
        unsafe = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts]
        bundle.extractall(EXTRACT)
    MEMBERS.write_text("\n".join(names) + "\n", encoding="utf-8")
    expected = {item["archive_path"]: item for item in package["members"]}
    special = {PREFIX + "README.md", PREFIX + "PACKAGE-MANIFEST.json"}
    hash_mismatches = []
    for name, item in expected.items():
        path = EXTRACT / name
        if not path.exists() or path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
            hash_mismatches.append(name)
    forbidden = [name for name in names if any(part.lower() in {".env", "auth.json", "credentials", "cache", "logs", "__pycache__"} or part.lower().endswith((".pem", ".key")) for part in PurePosixPath(name).parts)]
    secret_hits = []
    secrets = secret_values()
    for name in names:
        data = (EXTRACT / name).read_bytes()
        if any(secret in data for secret in secrets):
            secret_hits.append(name)
    parse_errors = []
    parsed = {"json": 0, "yaml": 0, "csv": 0, "markdown": 0, "python": 0}
    for name in names:
        path = EXTRACT / name
        try:
            if path.suffix == ".json":
                json.loads(path.read_text(encoding="utf-8")); parsed["json"] += 1
            elif path.suffix in {".yaml", ".yml"}:
                yaml.safe_load(path.read_text(encoding="utf-8")); parsed["yaml"] += 1
            elif path.suffix == ".csv":
                with path.open(encoding="utf-8-sig", newline="") as handle:
                    list(csv.reader(handle)); parsed["csv"] += 1
            elif path.suffix == ".md":
                if not path.read_text(encoding="utf-8").strip():
                    raise ValueError("empty Markdown")
                parsed["markdown"] += 1
            elif path.suffix == ".py":
                compile(path.read_text(encoding="utf-8"), name, "exec"); parsed["python"] += 1
        except Exception as error:
            parse_errors.append({"member": name, "error": str(error)})

    checks = {
        "active_status": active.get("status") == "pilot_ready_no_integration" and active.get("version") == "1.1.0",
        "active_hashes": not active_mismatches and active.get("active_file_count") == len(active.get("active_files", [])),
        "skill_versions_and_statuses": not skill_errors and len(active.get("skills", [])) == 10,
        "runtime_policy": policy.get("policy_version") == "1.0.0" and policy.get("status") == "approved_pilot_ready_no_integration",
        "release_manifest": release.get("status") == "pilot_ready_no_integration" and release["active_foundation"]["sha256"] == sha(ACTIVE) and release["runtime_policy"]["sha256"] == sha(POLICY) and release["acceptance_record"]["sha256"] == sha(ACCEPTANCE),
        "acceptance": acceptance.get("decision") == "approved_pilot_ready_no_integration" and acceptance.get("production_acceptance") is False and acceptance.get("contractual_acceptance") is False,
        "soul_status": "**PILOT_READY_NO_INTEGRATION**" in soul and "Proceed to **Step 10 — Integrations**" in soul,
        "web_and_fallback_disabled": "web" not in config and "web" not in config.get("platform_toolsets", {}).get("cli", []) and config.get("fallback_providers") == [],
        "language_audit": language.get("pass") is True,
        "archive_readable": bad_member is None and not unsafe,
        "archive_members": set(names) == set(expected) | special,
        "archive_payload_hashes": not hash_mismatches,
        "archive_no_forbidden_files": not forbidden,
        "archive_no_profile_secrets": not secret_hits,
        "archive_formats_parse": not parse_errors,
        "archive_manifest_non_recursive": package.get("manifest_self_hash_included") is False and package.get("archive_hash_included") is False,
        "external_actions_zero": acceptance.get("authorised_external_actions") == [] and release.get("external_actions") == 0,
    }
    result = {
        "record_type": "step9_final_release_validation",
        "profile": "equinet-a2-enrichment",
        "release_id": "equinet-a2-no-integration-1.0.0",
        "status": "pass_pilot_ready_no_integration" if all(checks.values()) else "failed",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "active_file_count": active.get("active_file_count"),
        "skill_count": len(active.get("skills", [])),
        "archive": str(ARCHIVE.relative_to(ROOT)),
        "archive_bytes": ARCHIVE.stat().st_size,
        "archive_sha256": sha(ARCHIVE),
        "archive_member_count": len(names),
        "parsed_counts": parsed,
        "active_mismatches": active_mismatches,
        "skill_errors": skill_errors,
        "archive_hash_mismatches": hash_mismatches,
        "forbidden_members": forbidden,
        "secret_hits": secret_hits,
        "parse_errors": parse_errors,
        "next_gate": "Step 10 — Integrations",
        "production_acceptance": False,
        "contractual_acceptance": False,
        "external_actions": 0,
        "errors": [name for name, passed in checks.items() if not passed],
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    SUMMARY.write_text(
        f"""# Equinet A2 Final No-Integration Release

**Release:** `equinet-a2-no-integration-1.0.0`  
**Status:** `{'PILOT_READY_NO_INTEGRATION' if all(checks.values()) else 'VALIDATION FAILED'}`  
**Final validation:** `{sum(checks.values())}/{len(checks)} PASS`

- Active files: **{active.get('active_file_count')}**.
- Skills: **{len(active.get('skills', []))}**.
- Archive members: **{len(names)}**.
- Archive bytes: **{ARCHIVE.stat().st_size}**.
- Archive SHA-256: `{sha(ARCHIVE)}`.
- Forbidden members: **{len(forbidden)}**.
- Profile secret matches: **{len(secret_hits)}**.
- External business actions: **0**.

This is a controlled no-integration pilot release. It is not production or contractual acceptance. Proceed to **Step 10 — Integrations**.
""",
        encoding="utf-8",
    )
    plan = load(PLAN)
    for phase in plan["phases"]:
        if phase["id"] == "9E":
            phase["status"] = "completed" if all(checks.values()) else "blocked"
    plan["status"] = "completed_pilot_ready_no_integration" if all(checks.values()) else "step9e_failed"
    plan["final_release_id"] = "equinet-a2-no-integration-1.0.0"
    plan["approved_at"] = acceptance.get("approved_at")
    PLAN.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": f"{result['checks_passed']}/{result['checks_total']}", "active_files": result["active_file_count"], "skills": result["skill_count"], "archive_members": result["archive_member_count"], "archive_bytes": result["archive_bytes"], "archive_sha256": result["archive_sha256"], "external_actions": 0}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
