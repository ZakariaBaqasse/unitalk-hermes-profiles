#!/usr/bin/env python3
"""Checkpoint post-n8n website enrichment without performing research."""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:  # System Python in tests may not provide jsonschema.
    Draft202012Validator = None
    FormatChecker = None

STATE_SCHEMA = "a1.website-enrichment-state.v1"
HANDOFF_SCHEMA = "a1.discovery-result.v1"
BATCH_SCHEMA = "a1.website-enrichment-batch.v1"
RESULTS_SCHEMA = "a1.website-enrichment-results.v1"
APPROVED_WEB_TOOLS = ("web_search", "web_extract")
EVIDENCE_ID = re.compile(r"^EV-[A-Z0-9_-]{3,50}$")
PIPELINE_KEYS = ("classification_decision", "qualification_assessment", "confidence_assessment")
RESULTS_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "references" / "enrichment-results.schema.json"
PROFILE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PIPELINE_PYTHON = PROFILE_ROOT / ".venv" / "bin" / "python"


def canonical_sha256(value: Any) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _validate_results_schema(payload: dict[str, Any]) -> None:
    """Load the versioned schema and apply it when the runtime validator is available."""
    schema = json.loads(RESULTS_SCHEMA_PATH.read_text(encoding="utf-8"))
    if schema.get("properties", {}).get("schema_version", {}).get("const") != RESULTS_SCHEMA:
        raise ValueError("Enrichment results schema file has an unexpected contract version.")
    if Draft202012Validator is None:
        return
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.absolute_path))
    if errors:
        error = errors[0]
        path = "/" + "/".join(str(part) for part in error.absolute_path)
        raise ValueError(f"Enrichment results schema validation failed at {path}: {error.message}")


def initialize_state(handoff: dict[str, Any], max_retries: int = 2) -> dict[str, Any]:
    """Create a checkpoint while preserving the n8n payload verbatim."""
    contract_version = handoff.get("contract_version", handoff.get("schema_version"))
    if contract_version != HANDOFF_SCHEMA:
        raise ValueError(f"Expected contract_version {HANDOFF_SCHEMA!r}.")

    if "contract_version" in handoff:
        run_id = handoff.get("run_id")
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("Handoff run_id must be a non-empty string.")
        run = {
            "run_id": run_id,
            "status": handoff.get("status"),
            "started_at": handoff.get("started_at"),
            "finished_at": handoff.get("finished_at"),
        }
    else:
        run = handoff.get("run")
        if not isinstance(run, dict) or not isinstance(run.get("run_id"), str) or not run["run_id"].strip():
            raise ValueError("Handoff run.run_id must be a non-empty string.")

    leads = handoff.get("leads")
    if not isinstance(leads, list):
        raise ValueError("Handoff leads must be an array.")
    if not isinstance(max_retries, int) or max_retries < 0:
        raise ValueError("max_retries must be a non-negative integer.")

    records: dict[str, Any] = {}
    for lead in leads:
        if not isinstance(lead, dict):
            raise ValueError("Every lead must be an object.")
        lead_id = lead.get("lead_fingerprint", lead.get("lead_id"))
        if not isinstance(lead_id, str) or not lead_id.strip():
            raise ValueError("Every lead requires a non-empty lead_fingerprint.")
        if lead_id in records:
            raise ValueError(f"Duplicate lead identifier: {lead_id}")
        records[lead_id] = {
            "lead": copy.deepcopy(lead),
            "status": "pending",
            "attempts": 0,
            "failure_history": [],
            "enrichment": None,
            "pipeline_inputs": {},
            "artifacts": {},
        }

    return {
        "schema_version": STATE_SCHEMA,
        "source_contract_version": HANDOFF_SCHEMA,
        "source_sha256": canonical_sha256(handoff),
        "run": copy.deepcopy(run),
        "discovery_result": {
            key: copy.deepcopy(value)
            for key, value in handoff.items()
            if key != "leads"
        },
        "max_retries": max_retries,
        "leads": records,
    }


def _validate_state(state: dict[str, Any]) -> None:
    if state.get("schema_version") != STATE_SCHEMA:
        raise ValueError(f"Expected state schema_version {STATE_SCHEMA!r}.")
    source_sha = state.get("source_sha256")
    if source_sha is not None and (not isinstance(source_sha, str) or not re.fullmatch(r"[a-f0-9]{64}", source_sha)):
        raise ValueError("State source_sha256 must be a canonical SHA-256 when present.")
    if not isinstance(state.get("leads"), dict):
        raise ValueError("State leads must be an object keyed by lead_id.")


def next_batch(state: dict[str, Any], batch_size: int) -> dict[str, Any]:
    """Return the next stable pending slice without mutating the checkpoint."""
    _validate_state(state)
    if not isinstance(batch_size, int) or batch_size < 1:
        raise ValueError("batch_size must be a positive integer.")
    leads = [
        copy.deepcopy(record["lead"])
        for record in state["leads"].values()
        if record.get("status") == "pending"
    ][:batch_size]
    return {
        "schema_version": BATCH_SCHEMA,
        "run_id": state["run"]["run_id"],
        "leads": leads,
        "requirements": {
            "research_owner": "Hermes agent",
            "approved_web_tools": list(APPROVED_WEB_TOOLS),
            "official_website_preferred": True,
            "no_site_completion_allowed": True,
            "no_site_completion_marker": "official_business_website_not_found",
            "destination_page_citations_required_when_website_verified": True,
            "search_results_are_discovery_only": True,
            "no_script_generated_enrichment": True,
        },
    }


def _http_url(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an HTTP(S) URL.")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field} must be an HTTP(S) URL.")
    return value


def _site_host(value: str) -> str:
    host = (urlparse(value).hostname or "").lower().rstrip(".")
    return host[4:] if host.startswith("www.") else host


def _same_official_site(source_url: str, website_url: str) -> bool:
    source_host = _site_host(source_url)
    website_host = _site_host(website_url)
    return source_host == website_host or source_host.endswith("." + website_host)


def _validate_timestamp(value: Any) -> None:
    if not isinstance(value, str):
        raise ValueError("retrieved_at must be an ISO-8601 timestamp.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("retrieved_at must be an ISO-8601 timestamp.") from exc
    if parsed.tzinfo is None:
        raise ValueError("retrieved_at must include a timezone.")


def _validate_completed_result(result: dict[str, Any]) -> None:
    if result.get("research_method") != "hermes_approved_web_tools":
        raise ValueError("Completed enrichment requires research_method 'hermes_approved_web_tools'.")
    for field in ("missing_information", "conflicts"):
        if not isinstance(result.get(field), list) or not all(isinstance(value, str) and value.strip() for value in result[field]):
            raise ValueError(f"{field} must be an array of non-empty strings.")

    website_status = result.get("website_status")
    if website_status is None:
        raise ValueError("Completed enrichment requires explicit website_status.")
    evidence = result.get("evidence")
    if website_status == "none_found":
        if result.get("official_website_url") is not None:
            raise ValueError("No-site completion requires official_website_url to be null.")
        if evidence != []:
            raise ValueError("No-site completion requires an empty evidence array.")
        if "official_business_website_not_found" not in result["missing_information"]:
            raise ValueError("No-site completion requires the official_business_website_not_found marker.")
        if any(key in result for key in PIPELINE_KEYS):
            raise ValueError("No-site completion cannot contain classification, qualification, or confidence inputs.")
        return
    if website_status != "verified":
        raise ValueError("website_status must be 'verified' or 'none_found'.")

    website = _http_url(result.get("official_website_url"), "official_website_url")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("Verified-website enrichment requires at least one cited evidence record.")
    seen: set[str] = set()
    has_extract = False
    for item in evidence:
        if not isinstance(item, dict):
            raise ValueError("Every evidence record must be an object.")
        evidence_id = item.get("evidence_id")
        if not isinstance(evidence_id, str) or not EVIDENCE_ID.fullmatch(evidence_id):
            raise ValueError("Every evidence record requires a valid evidence_id.")
        if evidence_id in seen:
            raise ValueError(f"Duplicate evidence_id: {evidence_id}")
        seen.add(evidence_id)
        source_url = _http_url(item.get("source_url"), "evidence source_url")
        if not _same_official_site(source_url, website):
            raise ValueError("Every retained evidence source_url must be on the official website domain.")
        if item.get("source_type") != "official_business_website":
            raise ValueError("Evidence source_type must be 'official_business_website'.")
        tool = item.get("retrieval_tool")
        if tool != "web_extract":
            raise ValueError("Retained website evidence requires a web_extract destination-page citation; web_search is discovery-only.")
        has_extract = True
        _validate_timestamp(item.get("retrieved_at"))
        for field in ("source_name", "evidence_excerpt", "claim"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"Evidence {field} must be a non-empty string.")
        if item.get("fact_or_inference") not in {"direct_fact", "reasonable_inference", "contradictory_evidence"}:
            raise ValueError("Invalid fact_or_inference value.")
    if not has_extract:
        raise ValueError("Verified-website enrichment requires at least one web_extract destination-page citation.")


def apply_results(state: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Validate Hermes-produced results and return an updated checkpoint copy."""
    _validate_state(state)
    _validate_results_schema(payload)
    if payload.get("schema_version") != RESULTS_SCHEMA or not isinstance(payload.get("results"), list):
        raise ValueError(f"Expected {RESULTS_SCHEMA!r} with a results array.")
    updated = copy.deepcopy(state)
    seen: set[str] = set()
    for result in payload["results"]:
        if not isinstance(result, dict):
            raise ValueError("Every result must be an object.")
        lead_id = result.get("lead_id")
        if lead_id in seen:
            raise ValueError(f"Duplicate result lead_id: {lead_id}")
        seen.add(lead_id)
        if lead_id not in updated["leads"]:
            raise ValueError(f"Unknown lead_id: {lead_id}")
        if result.get("status") != "completed":
            raise ValueError("accept supports only completed results; record failures with the fail command.")
        _validate_completed_result(result)
        record = updated["leads"][lead_id]
        if record["status"] in {"completed", "scored"}:
            raise ValueError(f"Lead {lead_id} is already completed.")
        evidence_ids = {item["evidence_id"] for item in result["evidence"]}
        classification = result.get("classification_decision")
        if classification is not None:
            if classification.get("seed_id") != lead_id:
                raise ValueError("classification_decision.seed_id must equal the source lead_fingerprint")
            unknown = set(classification.get("evidence_references", [])) - evidence_ids
            if unknown:
                raise ValueError(f"classification_decision references unknown enrichment evidence IDs: {sorted(unknown)}")
        qualification = result.get("qualification_assessment")
        if qualification is not None:
            if classification is not None and qualification.get("segment") != classification.get("segment"):
                raise ValueError("qualification_assessment.segment must match classification_decision.segment")
            qualification_ids = {
                evidence_id
                for criterion in qualification.get("criterion_assessments", {}).values()
                if isinstance(criterion, dict)
                for evidence_id in criterion.get("evidence_ids", [])
            }
            unknown = qualification_ids - evidence_ids
            if unknown:
                raise ValueError(f"qualification_assessment references unknown enrichment evidence IDs: {sorted(unknown)}")
        confidence = result.get("confidence_assessment")
        if confidence is not None:
            reference = confidence.get("candidate_reference") if isinstance(confidence.get("candidate_reference"), dict) else {}
            if reference.get("run_id") != state["run"]["run_id"] or reference.get("seed_id") != lead_id:
                raise ValueError("confidence_assessment candidate_reference must match run_id and lead_fingerprint")
            referenced = set(confidence.get("available_evidence_ids", []))
            for collection_name in ("dimensions", "gates"):
                collection = confidence.get(collection_name)
                if isinstance(collection, dict):
                    for assessment in collection.values():
                        if isinstance(assessment, dict):
                            referenced.update(assessment.get("evidence_ids", []))
            unknown = referenced - evidence_ids
            if unknown:
                raise ValueError(f"confidence_assessment references unknown enrichment evidence IDs: {sorted(unknown)}")
        record["status"] = "completed"
        record["attempts"] += 1
        record["enrichment"] = {key: copy.deepcopy(value) for key, value in result.items() if key not in PIPELINE_KEYS}
        record["pipeline_inputs"] = {
            key: copy.deepcopy(result[key]) for key in PIPELINE_KEYS if key in result
        }
    return updated


def record_failure(
    state: dict[str, Any],
    lead_id: str,
    error: str,
    recorded_at: str,
    retryable: bool,
) -> dict[str, Any]:
    """Record an explicit failure and leave retryable work pending within budget."""
    _validate_state(state)
    if lead_id not in state["leads"]:
        raise ValueError(f"Unknown lead_id: {lead_id}")
    if not isinstance(error, str) or not error.strip():
        raise ValueError("error must be a non-empty string.")
    _validate_timestamp(recorded_at)
    if not isinstance(retryable, bool):
        raise ValueError("retryable must be boolean.")
    updated = copy.deepcopy(state)
    record = updated["leads"][lead_id]
    if record["status"] in {"completed", "scored"}:
        raise ValueError(f"Lead {lead_id} is already completed.")
    record["attempts"] += 1
    record["failure_history"].append({
        "recorded_at": recorded_at,
        "error": error,
        "retryable": retryable,
    })
    record["status"] = (
        "pending"
        if retryable and record["attempts"] <= updated["max_retries"]
        else "failed"
    )
    return updated


def load_state(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("JSON document must be an object.")
    _validate_state(value)
    return value


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("JSON document must be an object.")
    return value


def save_state(path: Path, state: dict[str, Any]) -> None:
    """Atomically replace a checkpoint after validating its outer shape."""
    _validate_state(state)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(state, indent=2, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


@contextmanager
def state_lock(path: Path):
    """Serialize state transitions with a crash-safe advisory lock."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _run_checked(command: list[str]) -> None:
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise ValueError(f"Wrapper failed: {detail}")


def run_ready(
    state: dict[str, Any], output_dir: Path, python_executable: Path, lead_id: str | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Execute existing deterministic wrappers only for fully supplied inputs."""
    _validate_state(state)
    if not python_executable.is_file():
        raise ValueError(f"Python executable not found: {python_executable}")
    profile = Path(__file__).resolve().parents[3]
    scripts = {
        "classification": profile / "skills" / "prospect-segment-classification" / "scripts" / "validate_classification.py",
        "qualification": profile / "skills" / "equinet-icp-qualification" / "scripts" / "build_qualification.py",
        "confidence": profile / "skills" / "prospect-evidence-and-confidence" / "scripts" / "build_confidence_package.py",
        "scoring": profile / "skills" / "icp-scoring-and-rationale" / "scripts" / "build_scoring_package.py",
    }
    updated = copy.deepcopy(state)
    report: dict[str, Any] = {"scored": [], "skipped": {}}
    target_lead_id = lead_id
    if target_lead_id is not None and target_lead_id not in updated["leads"]:
        raise ValueError(f"Unknown lead_id: {target_lead_id}")
    for current_lead_id, record in updated["leads"].items():
        if target_lead_id is not None and current_lead_id != target_lead_id:
            continue
        lead_id = current_lead_id
        if record.get("status") == "scored":
            continue
        inputs = record.get("pipeline_inputs", {})
        missing = [key for key in PIPELINE_KEYS if key not in inputs]
        if record.get("status") != "completed" or missing:
            report["skipped"][lead_id] = missing or ["completed_enrichment"]
            continue

        safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", lead_id)
        directory = output_dir / safe_id
        classification_path = directory / "classification-decision.json"
        qualification_input = directory / "qualification-assessment.json"
        qualification_output = directory / "qualification-package.json"
        confidence_input = directory / "confidence-assessment.json"
        confidence_output = directory / "confidence-package.json"
        scoring_input = directory / "scoring-input.json"
        scoring_output = directory / "scoring-package.json"
        _write_json(classification_path, inputs["classification_decision"])
        _write_json(qualification_input, inputs["qualification_assessment"])
        _write_json(confidence_input, inputs["confidence_assessment"])

        python = str(python_executable)
        _run_checked([python, str(scripts["classification"]), str(classification_path)])
        _run_checked([python, str(scripts["qualification"]), str(qualification_input), "--output", str(qualification_output)])
        _run_checked([python, str(scripts["confidence"]), str(confidence_input), "--output", str(confidence_output)])
        qualification = load_json(qualification_output)["qualification"]
        confidence = load_json(confidence_output)["confidence"]
        scoring_candidate = {
            "segment": inputs["classification_decision"]["segment"],
            "qualification": qualification,
            "confidence": confidence,
        }
        _write_json(scoring_input, scoring_candidate)
        _run_checked([python, str(scripts["scoring"]), str(scoring_input), "--output", str(scoring_output)])

        record["status"] = "scored"
        record["artifacts"] = {
            "classification_decision": str(classification_path),
            "qualification_assessment": str(qualification_input),
            "qualification_package": str(qualification_output),
            "confidence_assessment": str(confidence_input),
            "confidence_package": str(confidence_output),
            "scoring_input": str(scoring_input),
            "scoring_package": str(scoring_output),
        }
        report["scored"].append(lead_id)
    return updated, report


def state_summary(state: dict[str, Any]) -> dict[str, Any]:
    _validate_state(state)
    counts: dict[str, int] = {}
    pending_ids: list[str] = []
    ready_ids: list[str] = []
    incomplete_ids: list[str] = []
    terminal_ids: list[str] = []
    for lead_id, record in state["leads"].items():
        status = str(record.get("status"))
        counts[status] = counts.get(status, 0) + 1
        enrichment = record.get("enrichment") if isinstance(record.get("enrichment"), dict) else {}
        inputs = record.get("pipeline_inputs") if isinstance(record.get("pipeline_inputs"), dict) else {}
        if status == "pending":
            pending_ids.append(lead_id)
        elif status == "completed" and enrichment.get("website_status") == "none_found":
            terminal_ids.append(lead_id)
        elif status == "completed" and all(key in inputs for key in PIPELINE_KEYS):
            ready_ids.append(lead_id)
        elif status == "completed" and enrichment.get("website_status") == "verified":
            terminal_ids.append(lead_id)
        elif status == "completed":
            incomplete_ids.append(lead_id)
        elif status in {"scored", "failed"}:
            terminal_ids.append(lead_id)
    total = len(state["leads"])
    terminal = len(terminal_ids) == total
    if pending_ids:
        next_action = "research_pending"
    elif ready_ids:
        next_action = "run_ready"
    elif incomplete_ids:
        next_action = "operator_repair_missing_pipeline_inputs"
    elif terminal:
        next_action = "build_overlays"
    else:
        next_action = "operator_repair"
    return {
        "schema_version": "a1.website-enrichment-summary.v1",
        "run_id": state["run"]["run_id"],
        "total": total,
        "counts": dict(sorted(counts.items())),
        "pending_count": len(pending_ids),
        "ready_count": len(ready_ids),
        "incomplete_count": len(incomplete_ids),
        "terminal_count": len(terminal_ids),
        "terminal": terminal,
        "next_action": next_action,
        "lead_rows_emitted": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init")
    init.add_argument("handoff", type=Path)
    init.add_argument("--state", required=True, type=Path)
    init.add_argument("--max-retries", type=int, default=2)
    next_command = subparsers.add_parser("next")
    next_command.add_argument("--state", required=True, type=Path)
    next_command.add_argument("--batch-size", required=True, type=int)
    accept = subparsers.add_parser("accept")
    accept.add_argument("--state", required=True, type=Path)
    accept.add_argument("--results", required=True, type=Path)
    fail = subparsers.add_parser("fail")
    fail.add_argument("--state", required=True, type=Path)
    fail.add_argument("--lead-id", required=True)
    fail.add_argument("--error", required=True)
    fail.add_argument("--recorded-at", required=True)
    fail.add_argument("--terminal", action="store_true")
    score = subparsers.add_parser("run-ready")
    score.add_argument("--state", required=True, type=Path)
    score.add_argument("--output-dir", required=True, type=Path)
    score.add_argument("--python", type=Path, default=DEFAULT_PIPELINE_PYTHON)
    score.add_argument("--lead-id")
    summary = subparsers.add_parser("summary")
    summary.add_argument("--state", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "init":
            with state_lock(args.state):
                if args.state.exists():
                    raise ValueError(f"Enrichment state already exists: {args.state}")
                state = initialize_state(load_json(args.handoff), args.max_retries)
                save_state(args.state, state)
            output: dict[str, Any] = {"state": str(args.state), "lead_count": len(state["leads"])}
        elif args.command == "next":
            output = next_batch(load_state(args.state), args.batch_size)
        elif args.command == "accept":
            results = load_json(args.results)
            with state_lock(args.state):
                state = apply_results(load_state(args.state), results)
                save_state(args.state, state)
            output = {"state": str(args.state), "accepted": len(results["results"])}
        elif args.command == "fail":
            with state_lock(args.state):
                state = record_failure(load_state(args.state), args.lead_id, args.error, args.recorded_at, not args.terminal)
                save_state(args.state, state)
            output = {"state": str(args.state), "lead_id": args.lead_id, "status": state["leads"][args.lead_id]["status"]}
        elif args.command == "summary":
            output = state_summary(load_state(args.state))
        else:
            with state_lock(args.state):
                state, output = run_ready(load_state(args.state), args.output_dir, args.python, args.lead_id)
                save_state(args.state, state)
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
