#!/usr/bin/env python3
"""Evaluate evidence/confidence for accepted Rood & Riddle Step 8 observations."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evaluations/step8/pilot/A1-RR-PODIATRY-001"
RAW_PATH = BASE / "observation-batch.json"
VALID_PATH = BASE / "validated-observations.json"
OUT = BASE / "evidence-confidence"
PYTHON = ROOT / ".venv/bin/python"
REQUIRED_ACCEPTED = {"person.role_title", "organisation.disciplines"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    raw = load(RAW_PATH)
    validated = load(VALID_PATH)
    raw_by_id = {item["observation_id"]: item for item in raw["observations"]}
    accepted = [item for item in validated["observations"] if item["action"] == "accept_for_wave3_evidence_assessment"]
    accepted_keys = {item["field_key"] for item in accepted}
    missing = sorted(REQUIRED_ACCEPTED - accepted_keys)
    OUT.mkdir(parents=True, exist_ok=True)
    results = []

    for item in accepted:
        source = raw_by_id[item["observation_id"]]
        field = item["field_key"]
        request = {
            "evidence_id": item["evidence_id"],
            "field_assessment_id": item["field_assessment_candidate"]["field_assessment_id"],
            "source_id": "prospect_official_website",
            "claim_key": field,
            "normalised_value": item["normalised_value"],
            "source_references": [source["source_url"], source["source_preflight"]["audit"]["output_reference"]],
            "source_preflight": source["source_preflight"],
            "identity_match": "exact",
            "claim_directness": "direct_fact",
            "freshness": "current_official_undated",
            "corroboration": "authoritative_or_primary_sufficient",
            "consistency": "no_conflict",
            "required_claim": field in REQUIRED_ACCEPTED,
        }
        slug = field.replace(".", "-")
        request_path = OUT / f"{slug}.request.json"
        result_path = OUT / f"{slug}.result.json"
        request_path.write_text(json.dumps(request, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        process = subprocess.run(
            [str(PYTHON), str(ROOT / "scripts/evaluate_a2_evidence_confidence.py"), str(request_path), "--output", str(result_path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        result = load(result_path) if result_path.exists() else {"errors": [process.stdout, process.stderr]}
        passed = (
            process.returncode == 0
            and result.get("verification_status") == "verified"
            and result.get("confidence_level") == "high"
            and result.get("external_actions") == 0
        )
        results.append(
            {
                "field_key": field,
                "request_path": str(request_path.relative_to(ROOT)),
                "request_sha256": sha(request_path),
                "result_path": str(result_path.relative_to(ROOT)),
                "result_sha256": sha(result_path) if result_path.exists() else None,
                "confidence_score": result.get("confidence_score"),
                "confidence_level": result.get("confidence_level"),
                "verification_status": result.get("verification_status"),
                "freshness_status": result.get("freshness_status"),
                "passed": passed,
                "errors": result.get("errors", []),
            }
        )

    passed = bool(results) and not missing and all(item["passed"] for item in results)
    manifest = {
        "record_type": "step8_rood_riddle_evidence_confidence",
        "candidate_id": "A1-RR-PODIATRY-001",
        "status": "pass" if passed else "failed",
        "validated_observations_sha256": sha(VALID_PATH),
        "accepted_field_keys": sorted(accepted_keys),
        "required_accepted_field_keys": sorted(REQUIRED_ACCEPTED),
        "missing_required_accepted_field_keys": missing,
        "results": results,
        "a1_score_changed": False,
        "canonical_record_mutated": False,
        "external_actions": 0,
    }
    manifest_path = OUT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
