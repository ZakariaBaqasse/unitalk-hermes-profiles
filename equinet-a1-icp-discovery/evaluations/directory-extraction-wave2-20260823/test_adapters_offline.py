#!/usr/bin/env python3
"""Offline acceptance tests for Wave 2 directory adapters."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

PROFILE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROFILE / "skills" / "public-prospect-research" / "scripts"))

from directory_extraction import (  # noqa: E402
    AuditLog,
    BoundedDirectoryRunner,
    ExtractionRequest,
    FetchResult,
    FixtureTransport,
    SourcePolicyGate,
    listing_to_research_seed,
    normalise_listing,
)
from directory_extraction.adapters import HorseProFinderAdapter, MadBarnAdapter, NewHorseAdapter  # noqa: E402
from directory_extraction.validation import validation_errors  # noqa: E402
from validate_research_seed import validate as validate_research_seed  # noqa: E402

EVALUATION = Path(__file__).resolve().parent
RESULTS = EVALUATION / "offline-adapter-test-results.json"


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
    return "2026-08-23T17:00:00Z"


def payload(filename: str) -> dict[str, Any]:
    return json.loads((EVALUATION / filename).read_text(encoding="utf-8"))["results"][0]


def fetch_result(item: dict[str, Any]) -> FetchResult:
    result = item["result"]
    return FetchResult(
        requested_url=item["requested_url"],
        final_url=result.get("url") or item["requested_url"],
        content=result.get("content") or "",
        status_code=200,
        error=result.get("error"),
        title=result.get("title"),
    )


def request(run_id: str, source_id: str, query: str, city: str | None) -> ExtractionRequest:
    return ExtractionRequest(
        run_id=run_id,
        source_id=source_id,
        segment="farrier",
        geography={"country_code": "US", "state_region": "Kentucky", "city": city},
        query_or_filter=query,
        max_candidates=5,
        max_pages=1,
        trigger="evaluation",
        mode="evaluation",
    )


async def execute(recorder: Recorder) -> None:
    cases = [
        (HorseProFinderAdapter(), "horseprofinder-kentucky-listing.json", "RUN-W2-OFFLINE-HORSEPRO", "Kentucky farriers", None),
        (NewHorseAdapter(), "newhorse-kentucky-listing.json", "RUN-W2-OFFLINE-NEWHORSE", "Kentucky farriers", None),
        (MadBarnAdapter(), "madbarn-lexington-listing.json", "RUN-W2-OFFLINE-MADBARN", "Lexington Kentucky farriers", "Lexington"),
    ]
    profile_cases = [
        (HorseProFinderAdapter(), "horseprofinder-target-profile.json"),
        (NewHorseAdapter(), "newhorse-target-profile.json"),
        (MadBarnAdapter(), "madbarn-target-profile.json"),
    ]
    with tempfile.TemporaryDirectory(prefix="a1-wave2-offline-") as directory:
        runtime_root = Path(directory)
        gate = SourcePolicyGate()
        outcomes = {}
        for adapter, filename, run_id, query, city in cases:
            item = payload(filename)
            transport = FixtureTransport({adapter.start_url: fetch_result(item)})
            runner = BoundedDirectoryRunner(policy_gate=gate, runtime_root=runtime_root, sleeper=no_sleep, clock=fixed_clock)
            outcome = await runner.run(request(run_id, adapter.source_id, query, city), adapter, transport)
            outcomes[adapter.source_id] = outcome
            recorder.check(f"{adapter.source_id} returns five bounded Kentucky listings", len(outcome["listings"]) == 5)
            recorder.check(f"{adapter.source_id} candidate cap remains partial", outcome["coverage"]["status"] == "partial" and outcome["coverage"]["last_error"] == "candidate_limit_reached")
            recorder.check(f"{adapter.source_id} listings validate", all(not validation_errors("listing", listing) for listing in outcome["listings"]))
            recorder.check(f"{adapter.source_id} audit records no external actions", outcome["audit"]["external_actions"] == {"outreach": 0, "crm_writes": 0, "a2_handoffs": 0})
            for listing in outcome["listings"]:
                seed = listing_to_research_seed(listing, run_id=run_id, discovery_query=query)
                recorder.check(f"{adapter.source_id} listing maps to A1 Research Seed", not validate_research_seed(seed))

        horse = outcomes["pdf.horseprofinder"]["listings"]
        recorder.check("HorseProFinder retains Kentucky path geography", all(item["location"]["state_region"] == "Kentucky" and item["location"]["city"] for item in horse))
        recorder.check("HorseProFinder retains profile URLs and categories", all(item["profile_url"] and item["services"] for item in horse))

        newhorse = outcomes["pdf.newhorse"]["listings"]
        recorder.check("NewHorse retains Kentucky listing cities", all(item["location"]["state_region"] == "Kentucky" and item["location"]["city"] for item in newhorse))
        recorder.check("NewHorse retains the server page-two cursor after internal offsets", outcomes["pdf.newhorse"]["coverage"]["next_cursor"].endswith("#offset=5"))

        madbarn = outcomes["pdf.mad_barn_directory"]["listings"]
        recorder.check("Mad Barn returns Lexington profile links", all(item["location"]["city"] == "Lexington" and item["profile_url"] for item in madbarn))
        recorder.check("Mad Barn separates street address from city", all("RoadLexington" not in (item["location"]["public_address"] or "") for item in madbarn))

        for adapter, filename in profile_cases:
            item = payload(filename)
            parsed = adapter.parse_page(fetch_result(item))
            recorder.check(f"{adapter.source_id} targeted profile yields one record", len(parsed.listings) == 1)
            normalised = normalise_listing(
                parsed.listings[0],
                source_id=adapter.source_id,
                adapter_id=adapter.adapter_id,
                adapter_version=adapter.version,
                retrieved_at=fixed_clock(),
                raw_artifact_path=f"profiles/{filename}",
                segment_hint="farrier",
            )
            recorder.check(f"{adapter.source_id} targeted profile validates", not validation_errors("listing", normalised))

        horse_profile = HorseProFinderAdapter().parse_page(fetch_result(payload("horseprofinder-target-profile.json"))).listings[0]
        recorder.check("HorseProFinder profile exposes category and URL geography but no invented contact", horse_profile["services"] == ["Barefoot Trimming"] and not horse_profile["public_contacts"])
        newhorse_profile = NewHorseAdapter().parse_page(fetch_result(payload("newhorse-target-profile.json"))).listings[0]
        recorder.check("NewHorse profile exposes a public phone and bounded specialties", len(newhorse_profile["public_contacts"]) == 1 and 1 < len(newhorse_profile["services"]) <= 30)
        recorder.check("NewHorse excludes contact-form labels from specialties", not any(value.lower() in {"your name", "email", "how can we help you?"} for value in newhorse_profile["services"]))
        madbarn_profile = MadBarnAdapter().parse_page(fetch_result(payload("madbarn-target-profile.json"))).listings[0]
        recorder.check("Mad Barn profile exposes public phone, email and Lexington address", len(madbarn_profile["public_contacts"]) == 2 and madbarn_profile["location"]["city"] == "Lexington")

        audit_log = AuditLog(runtime_root / "audit-log.jsonl")
        recorder.check("Wave 2 offline audit has three events", len(audit_log.read_all()) == 3)
        recorder.check("Wave 2 offline audit hash chain validates", not audit_log.verify())


def main() -> int:
    recorder = Recorder()
    status = "passed"
    error = None
    try:
        asyncio.run(execute(recorder))
    except Exception as exc:
        status = "failed"
        error = str(exc)
    result = {
        "test_suite": "equinet-a1-wave2-adapters-offline",
        "test_mode": "saved_live_payloads_no_network",
        "network_requests": 0,
        "status": status,
        "passed": sum(item["passed"] for item in recorder.results),
        "failed": sum(not item["passed"] for item in recorder.results),
        "error": error,
        "results": recorder.results,
    }
    RESULTS.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
