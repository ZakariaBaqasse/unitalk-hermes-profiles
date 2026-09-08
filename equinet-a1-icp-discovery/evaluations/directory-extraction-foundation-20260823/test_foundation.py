#!/usr/bin/env python3
"""Deterministic acceptance tests for the shared directory extraction foundation."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Callable

import yaml

PROFILE = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROFILE / "skills" / "public-prospect-research" / "scripts"
sys.path.insert(0, str(PACKAGE_ROOT))

from directory_extraction import (  # noqa: E402
    AuditLog,
    BoundedDirectoryRunner,
    ExtractionRequest,
    FetchResult,
    FixtureTransport,
    ParsedPage,
    PolicyError,
    SourcePolicyGate,
    listing_to_research_seed,
)
from directory_extraction.storage import exclusive_lock  # noqa: E402
from directory_extraction.validation import require_valid, validation_errors  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "synthetic-farrieriq-pages.json"
RESULTS = Path(__file__).resolve().parent / "test-results.json"
SOURCE_PROFILES = PROFILE / "configurations" / "directory-extraction" / "source-runtime-profiles-v1.yaml"


class SyntheticFarrierIQAdapter:
    source_id = "pdf.farrieriq"
    adapter_id = "farrieriq"
    version = "1.1.0"

    def __init__(self, start_url: str = "https://farrieriq.com/directory/kentucky") -> None:
        self.start_url = start_url

    def initial_url(self, request: ExtractionRequest, next_cursor: str | None) -> str:
        return next_cursor or self.start_url

    def parse_page(self, response: FetchResult) -> ParsedPage:
        payload = json.loads(response.content)
        return ParsedPage(
            listings=payload["listings"],
            next_url=payload.get("next_url"),
            terminal=bool(payload.get("terminal")),
        )


class FailingAdapter(SyntheticFarrierIQAdapter):
    def parse_page(self, response: FetchResult) -> ParsedPage:
        raise ValueError("synthetic parser failure")


class TestRecorder:
    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []

    def check(self, name: str, condition: bool, detail: str = "") -> None:
        self.results.append({"name": name, "passed": bool(condition), "detail": detail})
        if not condition:
            raise AssertionError(f"{name}: {detail}")
        print(f"PASS: {name}")

    def raises(self, name: str, expected: type[BaseException], callback: Callable[[], Any], contains: str | None = None) -> None:
        try:
            callback()
        except expected as exc:
            if contains and contains not in str(exc):
                self.check(name, False, f"Expected {contains!r} in {exc!r}")
            self.check(name, True, str(exc))
        else:
            self.check(name, False, f"Expected {expected.__name__}")


async def no_sleep(_: float) -> None:
    return None


def fixed_clock() -> str:
    return "2026-08-23T15:00:00Z"


def request(run_id: str, query: str, *, max_candidates: int = 3, max_pages: int = 2, mode: str = "evaluation", daily_count_before: int = 0) -> ExtractionRequest:
    return ExtractionRequest(
        run_id=run_id,
        source_id="pdf.farrieriq",
        segment="farrier",
        geography={"country_code": "US", "state_region": "Kentucky", "city": None},
        query_or_filter=query,
        max_candidates=max_candidates,
        max_pages=max_pages,
        trigger="evaluation",
        mode=mode,
        daily_count_before=daily_count_before,
    )


def transport_from_fixture() -> FixtureTransport:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))["pages"]
    return FixtureTransport({
        url: FetchResult(requested_url=url, final_url=url, content=json.dumps(page), status_code=200)
        for url, page in payload.items()
    })


def one_page_content() -> str:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))["pages"]["https://farrieriq.com/directory/kentucky"]
    terminal = dict(payload)
    terminal["next_url"] = None
    terminal["terminal"] = True
    return json.dumps(terminal)


async def run_tests(recorder: TestRecorder, runtime_root: Path) -> None:
    profiles = yaml.safe_load(SOURCE_PROFILES.read_text(encoding="utf-8"))
    recorder.check("six source runtime profiles are configured", len(profiles["sources"]) == 6)
    for profile in profiles["sources"]:
        recorder.check(f"source runtime profile validates: {profile['source_id']}", not validation_errors("source_profile", profile))

    test_profiles = json.loads(json.dumps(profiles))
    synthetic_farrieriq = next(item for item in test_profiles["sources"] if item["source_id"] == "pdf.farrieriq")
    synthetic_farrieriq["limits"]["max_candidates_per_run"] = 20
    synthetic_farrieriq["limits"]["max_pages_per_run"] = 2
    synthetic_horseprofinder = next(item for item in test_profiles["sources"] if item["source_id"] == "pdf.horseprofinder")
    synthetic_horseprofinder["implementation_status"] = "pending_profile_test"
    synthetic_horseprofinder["operational_status"] = "pending_validation"
    synthetic_horseprofinder["technical_validation_status"] = "pending"
    test_profiles_path = runtime_root / "synthetic-source-runtime-profiles.yaml"
    test_profiles_path.write_text(yaml.safe_dump(test_profiles, sort_keys=False), encoding="utf-8")
    gate = SourcePolicyGate(profiles_path=test_profiles_path)

    runner = BoundedDirectoryRunner(policy_gate=gate, runtime_root=runtime_root, sleeper=no_sleep)
    adapter = SyntheticFarrierIQAdapter()
    success_transport = transport_from_fixture()
    outcome = await runner.run(request("RUN-FOUNDATION-SUCCESS", "synthetic success", max_candidates=5), adapter, success_transport)
    recorder.check("bounded two-page run completes", outcome["status"] == "completed")
    recorder.check("three unique listings are returned", len(outcome["listings"]) == 3)
    recorder.check("duplicate listing is recorded", outcome["audit"]["result"]["duplicates"] == 1)
    recorder.check("raw listing count is four", outcome["audit"]["result"]["raw_listings"] == 4)
    recorder.check("coverage reaches complete snapshot", outcome["coverage"]["status"] == "complete_snapshot")
    recorder.check("coverage records two pages", outcome["coverage"]["pages_completed"] == 2)
    recorder.check("no external actions are recorded", outcome["audit"]["external_actions"] == {"outreach": 0, "crm_writes": 0, "a2_handoffs": 0})
    for listing in outcome["listings"]:
        require_valid("listing", listing)
    from validate_research_seed import validate as validate_research_seed
    handoff_seed = listing_to_research_seed(outcome["listings"][0], run_id="RUN-FOUNDATION-HANDOFF", discovery_query="synthetic Kentucky farrier directory")
    recorder.check("normalised listing maps to the existing A1 Research Seed contract", not validate_research_seed(handoff_seed))
    recorder.check("directory handoff remains needs_research", handoff_seed["status"] == "needs_research")
    require_valid("coverage", outcome["coverage"])
    require_valid("audit", outcome["audit"])
    recorder.check("raw page artifacts exist", len(list((runtime_root / "runs" / "RUN-FOUNDATION-SUCCESS" / "raw").glob("*.json"))) == 2)

    skipped_transport = FixtureTransport({})
    skipped = await runner.run(request("RUN-FOUNDATION-SKIP", "synthetic success", max_candidates=5), adapter, skipped_transport)
    recorder.check("fresh complete coverage suppresses refetch", skipped["status"] == "skipped_fresh_coverage" and not skipped_transport.calls)
    audit_log = AuditLog(runtime_root / "audit-log.jsonl")
    audit_events = audit_log.read_all()
    recorder.check("append-only audit log records both runs", len(audit_events) == 2)
    recorder.check("audit events form a valid hash chain", not audit_log.verify())
    recorder.check("second audit event links to the first", audit_events[1]["previous_event_hash"] == audit_events[0]["event_hash"])

    partial_root = runtime_root / "partial-case"
    partial_runner = BoundedDirectoryRunner(policy_gate=gate, runtime_root=partial_root, sleeper=no_sleep)
    partial = await partial_runner.run(request("RUN-FOUNDATION-PARTIAL", "synthetic partial", max_pages=1), adapter, transport_from_fixture())
    recorder.check("page cap produces partial coverage", partial["status"] == "partial" and partial["coverage"]["status"] == "partial")
    recorder.check("partial coverage preserves next cursor", partial["coverage"]["next_cursor"] == "https://farrieriq.com/directory/kentucky?page=2")

    candidate_cap_root = runtime_root / "candidate-cap-case"
    candidate_cap_runner = BoundedDirectoryRunner(policy_gate=gate, runtime_root=candidate_cap_root, sleeper=no_sleep)
    candidate_cap = await candidate_cap_runner.run(request("RUN-FOUNDATION-CAP", "synthetic cap", max_candidates=2), adapter, transport_from_fixture())
    recorder.check("candidate cap never implies complete coverage", candidate_cap["coverage"]["status"] == "partial")
    recorder.check("candidate cap records an explicit stop reason", candidate_cap["coverage"]["last_error"] == "candidate_limit_reached")

    blocked_root = runtime_root / "blocked-case"
    blocked_runner = BoundedDirectoryRunner(policy_gate=gate, runtime_root=blocked_root, sleeper=no_sleep)
    blocked_transport = FixtureTransport({adapter.start_url: FetchResult(adapter.start_url, adapter.start_url, "", status_code=429, error="Rate Limit Exceeded")})
    blocked = await blocked_runner.run(request("RUN-FOUNDATION-429", "synthetic 429", max_pages=1), adapter, blocked_transport)
    recorder.check("HTTP 429 stops the source", blocked["status"] == "blocked")
    recorder.check("HTTP 429 is not retried", len(blocked_transport.calls) == 1)

    retry_root = runtime_root / "retry-case"
    retry_runner = BoundedDirectoryRunner(policy_gate=gate, runtime_root=retry_root, sleeper=no_sleep)
    retry_transport = FixtureTransport({adapter.start_url: [
        FetchResult(adapter.start_url, adapter.start_url, "", status_code=503, error="Temporary upstream failure"),
        FetchResult(adapter.start_url, adapter.start_url, one_page_content(), status_code=200),
    ]})
    retry = await retry_runner.run(request("RUN-FOUNDATION-RETRY", "synthetic retry", max_pages=1), adapter, retry_transport)
    recorder.check("one transient retry can recover", retry["status"] == "completed")
    recorder.check("transient retry occurs exactly once", len(retry_transport.calls) == 2)

    parser_failure_root = runtime_root / "parser-failure-case"
    parser_failure_runner = BoundedDirectoryRunner(policy_gate=gate, runtime_root=parser_failure_root, sleeper=no_sleep)
    parser_failure = await parser_failure_runner.run(
        request("RUN-PARSER-FAILURE", "synthetic parser failure", max_pages=1),
        FailingAdapter(),
        FixtureTransport({adapter.start_url: FetchResult(adapter.start_url, adapter.start_url, one_page_content(), status_code=200)}),
    )
    recorder.check("adapter parser failure is audited instead of escaping", parser_failure["status"] == "failed" and parser_failure["coverage"]["last_error"].startswith("adapter_parse_error"))

    recorder.raises(
        "per-run candidate limit is enforced",
        PolicyError,
        lambda: gate.authorise(request("RUN-OVER-LIMIT", "limit", max_candidates=21), adapter.start_url, transport_kind="fixture"),
        "per-run limit",
    )
    recorder.raises(
        "daily candidate limit is enforced",
        PolicyError,
        lambda: gate.authorise(request("RUN-DAILY-LIMIT", "daily", max_candidates=20, daily_count_before=40), adapter.start_url, transport_kind="fixture"),
        "daily limit",
    )
    recorder.raises(
        "wrong host is rejected",
        PolicyError,
        lambda: gate.authorise(request("RUN-WRONG-HOST", "host"), "https://example.com/listings", transport_kind="fixture"),
        "not approved",
    )
    live_profile = gate.authorise(request("RUN-LIVE-APPROVED", "live approved", mode="live"), adapter.start_url, transport_kind="firecrawl")
    recorder.check("approved Wave 1 adapter passes the live policy gate", live_profile["operational_status"] == "validated_for_bounded_pilot")
    pending_live_request = ExtractionRequest(
        run_id="RUN-LIVE-PENDING",
        source_id="pdf.horseprofinder",
        segment="farrier",
        geography={"country_code": "US", "state_region": "Kentucky", "city": None},
        query_or_filter="pending live adapter",
        max_candidates=3,
        max_pages=1,
        trigger="evaluation",
        mode="live",
    )
    recorder.raises(
        "Wave 2 live run is rejected before adapter validation",
        PolicyError,
        lambda: gate.authorise(pending_live_request, "https://horseprofinder.com/farriers/", transport_kind="firecrawl"),
        "not live-ready",
    )
    recorder.raises(
        "unsafe run identifier is rejected",
        PolicyError,
        lambda: gate.authorise(request("../../unsafe", "unsafe"), adapter.start_url, transport_kind="fixture"),
        "safe uppercase identifier",
    )
    non_us_request = ExtractionRequest(
        run_id="RUN-NON-US",
        source_id="pdf.farrieriq",
        segment="farrier",
        geography={"country_code": "CA", "state_region": "Ontario", "city": None},
        query_or_filter="non-US",
        max_candidates=3,
        max_pages=1,
    )
    recorder.raises(
        "non-US directory run is rejected",
        PolicyError,
        lambda: gate.authorise(non_us_request, adapter.start_url, transport_kind="fixture"),
        "outside the configured directory scope",
    )
    recorder.raises(
        "blocked source has no executable runtime profile",
        PolicyError,
        lambda: gate.profile_for("pdf.ohorse"),
        "no directory runtime profile",
    )

    lock_path = runtime_root / "locks" / "lock-test.lock"
    with exclusive_lock(lock_path):
        recorder.raises("concurrency lock prevents a second worker", RuntimeError, lambda: exclusive_lock(lock_path).__enter__(), "already exists")

    index = json.loads((runtime_root / "listing-index.json").read_text(encoding="utf-8"))
    recorder.check("listing index stores three unique identities", len(index["listings"]) == 3)
    recorder.check("audit artifact validates from disk", not validation_errors("audit", json.loads((runtime_root / "runs" / "RUN-FOUNDATION-SUCCESS" / "audit.json").read_text(encoding="utf-8"))))
    pacing_state = json.loads((runtime_root / "request-pacing.json").read_text(encoding="utf-8"))
    recorder.check("request pacing persists across runs", "pdf.farrieriq" in pacing_state["last_request_at"])

    replay_a = runtime_root / "deterministic-a"
    replay_b = runtime_root / "deterministic-b"
    fixed_request = request("RUN-FIXED-REPLAY", "fixed replay")
    fixed_runner_a = BoundedDirectoryRunner(policy_gate=gate, runtime_root=replay_a, sleeper=no_sleep, clock=fixed_clock)
    fixed_runner_b = BoundedDirectoryRunner(policy_gate=gate, runtime_root=replay_b, sleeper=no_sleep, clock=fixed_clock)
    await fixed_runner_a.run(fixed_request, adapter, transport_from_fixture())
    await fixed_runner_b.run(fixed_request, adapter, transport_from_fixture())
    deterministic_files = [
        "coverage-ledger.json",
        "listing-index.json",
        "audit-log.jsonl",
        "request-pacing.json",
        "runs/RUN-FIXED-REPLAY/normalised-listings.json",
        "runs/RUN-FIXED-REPLAY/rejected-listings.json",
        "runs/RUN-FIXED-REPLAY/audit.json",
    ]
    recorder.check(
        "fixed clock and identical fixtures produce byte-identical state",
        all((replay_a / name).read_bytes() == (replay_b / name).read_bytes() for name in deterministic_files),
    )


def main() -> int:
    recorder = TestRecorder()
    status = "passed"
    error = None
    try:
        with tempfile.TemporaryDirectory(prefix="a1-directory-foundation-") as directory:
            asyncio.run(run_tests(recorder, Path(directory)))
    except Exception as exc:
        status = "failed"
        error = str(exc)
    payload = {
        "test_suite": "equinet-a1-shared-directory-extraction-foundation",
        "test_mode": "synthetic_fixture_only",
        "network_requests": 0,
        "status": status,
        "passed": sum(1 for item in recorder.results if item["passed"]),
        "failed": sum(1 for item in recorder.results if not item["passed"]),
        "error": error,
        "results": recorder.results,
    }
    RESULTS.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
