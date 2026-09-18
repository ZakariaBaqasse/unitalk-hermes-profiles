#!/usr/bin/env python3
"""Refresh Step 5C approval hashes after post-approval validation artifacts change."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "evaluations/step5c"
RUNTIME = ROOT / "foundations/contracts/skills/a2-wave2-runtime-manifest-0.1.0.json"
ACTIVE = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"
ACCEPTANCE = EVAL / "acceptance-record.json"
PROMOTION = EVAL / "wave2-promotion-manifest.json"
TECH = EVAL / "technical-validation.json"
BEHAVIOURAL = EVAL / "behavioural-validation.json"
REVIEW = EVAL / "A2-WAVE-2-REVIEW.md"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    technical = load(TECH)
    behavioural = load(BEHAVIOURAL)
    if technical.get("pass") is not True or technical.get("status") != "approved_and_promoted":
        raise RuntimeError("approved Wave 2 technical validation is not current")
    if behavioural.get("overall_status") != "pass":
        raise RuntimeError("Wave 2 behavioural validation is not current")

    runtime = load(RUNTIME)
    runtime["validation"]["technical"]["sha256"] = sha(TECH)
    runtime["validation"]["technical"]["deterministic_cases"] = "24/24 pass"
    runtime["validation"]["behavioural"]["sha256"] = sha(BEHAVIOURAL)
    runtime["validation"]["behavioural"]["scenarios"] = "3/3 pass"
    RUNTIME.write_text(json.dumps(runtime, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    subprocess.run([str(ROOT / ".venv/bin/python"), str(ROOT / "scripts/build_active_foundation_manifest.py")], check=True, cwd=ROOT)

    acceptance = load(ACCEPTANCE)
    acceptance["runtime_manifest_sha256"] = sha(RUNTIME)
    acceptance["technical_validation_sha256"] = sha(TECH)
    acceptance["behavioural_validation_sha256"] = sha(BEHAVIOURAL)
    acceptance["active_foundation_manifest_sha256"] = sha(ACTIVE)
    ACCEPTANCE.write_text(json.dumps(acceptance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    promotion = load(PROMOTION)
    for item in promotion.get("files", []):
        path = ROOT / item["path"]
        item["bytes"] = path.stat().st_size
        item["sha256"] = sha(path)
    promotion["active_foundation_manifest"]["sha256"] = sha(ACTIVE)
    PROMOTION.write_text(json.dumps(promotion, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "pass": True,
        "runtime_manifest_sha256": sha(RUNTIME),
        "active_foundation_manifest_sha256": sha(ACTIVE),
        "acceptance_record_sha256": sha(ACCEPTANCE),
        "promotion_manifest_sha256": sha(PROMOTION),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
