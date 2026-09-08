#!/usr/bin/env python3
"""Offline acceptance tests for Wave 1 directory adapters using saved smoke artifacts."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

PROFILE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROFILE / "skills" / "public-prospect-research" / "scripts"))

from directory_extraction import BoundedDirectoryRunner, ExtractionRequest, FetchResult, FixtureTransport, SourcePolicyGate  # noqa: E402
from directory_extraction.adapters import BestOfLexingtonAdapter, FarrierIQAdapter, HASTAdapter  # noqa: E402
from directory_extraction.validation import validation_errors  # noqa: E402

SMOKE = PROFILE / "evaluations" / "source-smoke-20260819"
RESULTS = Path(__file__).resolve().parent / "offline-adapter-test-results.json"


class Recorder:
    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []

    def check(self, name: str, condition: bool, detail: str = "") -> None:
        self.results.append({"name": name, "passed": bool(condition), "detail": detail})
        if not condition:
            raise AssertionError(f"{name}: {detail}")
        print(f"PASS: {name}")


async def no_sleep(_: float) -> None:
    return None


def fixed_clock() -> str:
    return "2026-08-23T16:00:00Z"


def smoke_result(filename: str, source_id: str) -> tuple[str, dict[str, Any]]:
    payload = json.loads((SMOKE / filename).read_text(encoding="utf-8"))
    item = next(value for value in payload["results"] if value["source_id"] == source_id)
    return item["requested_url"], item["result"]


def request(run_id: str, source_id: str, query: str) -> ExtractionRequest:
    return ExtractionRequest(
        run_id=run_id,
        source_id=source_id,
        segment="farrier",
        geography={"country_code": "US", "state_region": "Kentucky", "city": None},
        query_or_filter=query,
        max_candidates=5,
        max_pages=1,
        trigger="evaluation",
        mode="evaluation",
    )


async def execute(recorder: Recorder) -> None:
    cases = [
        (FarrierIQAdapter(), "pages-batch-1-farrieriq-fia.json", "RUN-W1-OFFLINE-FARRIERIQ", "farrieriq Kentucky", "partial"),
        (HASTAdapter(), "pages-batch-4-edss-hast.json", "RUN-W1-OFFLINE-HAST", "HAST Greater Louisville", "partial"),
        (BestOfLexingtonAdapter(), "pages-batch-3-newhorse-bestlex.json", "RUN-W1-OFFLINE-BESTLEX", "Best of Lexington Kentucky", "completed"),
    ]
    with tempfile.TemporaryDirectory(prefix="a1-wave1-offline-") as directory:
        runtime_root = Path(directory)
        gate = SourcePolicyGate()
        outputs = {}
        for adapter, filename, run_id, query, expected_status in cases:
            url, result = smoke_result(filename, adapter.source_id)
            transport = FixtureTransport({adapter.start_url: FetchResult(
                requested_url=adapter.start_url,
                final_url=result.get("url") or url,
                content=result.get("content") or "",
                status_code=200,
                error=result.get("error"),
                title=result.get("title"),
            )})
            runner = BoundedDirectoryRunner(policy_gate=gate, runtime_root=runtime_root, sleeper=no_sleep, clock=fixed_clock)
            outcome = await runner.run(request(run_id, adapter.source_id, query), adapter, transport)
            outputs[adapter.source_id] = outcome
            recorder.check(f"{adapter.source_id} returns five bounded listings", len(outcome["listings"]) == 5)
            recorder.check(f"{adapter.source_id} has expected coverage status", outcome["status"] == expected_status, outcome["status"])
            recorder.check(f"{adapter.source_id} listings validate", all(not validation_errors("listing", listing) for listing in outcome["listings"]))
            recorder.check(f"{adapter.source_id} audit has no external actions", outcome["audit"]["external_actions"] == {"outreach": 0, "crm_writes": 0, "a2_handoffs": 0})

        farrieriq = outputs["pdf.farrieriq"]["listings"]
        recorder.check("FarrierIQ preserves Kentucky cities", all(item["location"]["state_region"] == "Kentucky" and item["location"]["city"] for item in farrieriq))
        recorder.check("FarrierIQ preserves service evidence", all(item["services"] for item in farrieriq))
        recorder.check("FarrierIQ candidate cap remains partial", outputs["pdf.farrieriq"]["coverage"]["last_error"] == "candidate_limit_reached")
        profile_payload = json.loads((Path(__file__).resolve().parent / "farrieriq-target-profile.json").read_text(encoding="utf-8"))["results"][0]
        profile_result = profile_payload["result"]
        profile_parsed = FarrierIQAdapter(profile_payload["requested_url"]).parse_page(FetchResult(
            requested_url=profile_payload["requested_url"],
            final_url=profile_result.get("url") or profile_payload["requested_url"],
            content=profile_result.get("content") or "",
            status_code=200,
            error=profile_result.get("error"),
            title=profile_result.get("title"),
        ))
        recorder.check("FarrierIQ individual profile yields one record", len(profile_parsed.listings) == 1)
        profile_listing = profile_parsed.listings[0]
        recorder.check("FarrierIQ individual profile exposes address and service fields", profile_listing["location"]["city"] == "Lexington" and len(profile_listing["services"]) == 4)
        recorder.check("FarrierIQ placeholder 555 contact is not retained", not profile_listing["public_contacts"])
        recorder.check("FarrierIQ suspected placeholder profile is held for review", profile_listing["processing_status"] == "held_for_review" and "suspected_placeholder_contact_555" in profile_listing["exclusion_reasons"])

        hast = outputs["pdf.hast_farriers"]["listings"]
        recorder.check("HAST starts with the expected public working-Farrier list", [item["display_name"] for item in hast[:3]] == ["Stephen Abell", "Milton Akins", "Marie Aquilina"])
        recorder.check("HAST retains only public professional contacts", all(contact["contact_type"] in {"phone", "email"} for item in hast for contact in item["public_contacts"]))
        recorder.check("HAST candidate cap remains partial", outputs["pdf.hast_farriers"]["coverage"]["last_error"] == "candidate_limit_reached")

        bestlex = outputs["pdf.best_of_lexington_farriers"]["listings"]
        expected_names = {"Kentucky Legend Horseshoeing", "Double M Farrier Service", "The Balanced Bare Hoof", "Safe Harbor Farrier Service", "TG Forge"}
        recorder.check("Best of Lexington extracts exactly the five directory cards", {item["display_name"] for item in bestlex} == expected_names)
        recorder.check("Best of Lexington preserves five public business phones", len({contact["value"] for item in bestlex for contact in item["public_contacts"] if contact["contact_type"] == "phone"}) == 5)
        recorder.check("Best of Lexington excludes claim and reCAPTCHA links", all("claim" not in (item["profile_url"] or "") and "recaptcha" not in json.dumps(item).lower() for item in bestlex))

        audit_log = runtime_root / "audit-log.jsonl"
        recorder.check("offline Wave 1 audit contains three hash-linked events", len(audit_log.read_text(encoding="utf-8").splitlines()) == 3)


def main() -> int:
    recorder = Recorder()
    status = "passed"
    error = None
    try:
        asyncio.run(execute(recorder))
    except Exception as exc:
        status = "failed"
        error = str(exc)
    payload = {
        "test_suite": "equinet-a1-wave1-adapters-offline",
        "source_artifacts": "evaluations/source-smoke-20260819",
        "network_requests": 0,
        "status": status,
        "passed": sum(item["passed"] for item in recorder.results),
        "failed": sum(not item["passed"] for item in recorder.results),
        "error": error,
        "results": recorder.results,
    }
    RESULTS.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
