#!/usr/bin/env python3
"""Run the official Facebook contact Actor once per eligible Company.

Live mode requires APIFY_API_KEY (with APIFY_TOKEN retained as a legacy alias).
``--fixture`` is fully local. Runs are
started asynchronously, status is polled a bounded number of times, and the
single default dataset is retrieved only after SUCCEEDED.  There are no
retries, run resurrection attempts, or fallback actors.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from a2_twenty_fullenrich_common import env_value

ACTOR_ID = "apify~facebook-page-contact-information"
API_BASE = "https://api.apify.com/v2"
PENDING = {"READY", "RUNNING"}
SUCCESS = {"SUCCEEDED"}
FAILURE = {"FAILED", "TIMED-OUT", "ABORTED"}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def _unwrap(response: Any) -> dict[str, Any]:
    if isinstance(response, dict) and isinstance(response.get("data"), dict):
        return response["data"]
    if isinstance(response, dict):
        return response
    raise ValueError("Apify run response must be an object")


def http_json(method: str, url: str, token: str, body: Any = None, timeout: float = 30.0) -> Any:
    """Perform exactly one HTTP attempt; retry belongs nowhere in this connector."""
    payload = None if body is None else canonical_json(body)
    request = Request(
        url,
        data=payload,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json", "Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"Apify HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Apify transport error: {exc.reason}") from exc
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Apify returned non-JSON data") from exc


def _cost(run: dict[str, Any]) -> dict[str, Any] | None:
    cost: dict[str, Any] = {}
    for key in ("usageTotalUsd", "usageUsd", "usage", "chargedEventCounts", "pricingInfo"):
        if key in run and run[key] is not None:
            cost[key] = run[key]
    return cost or None


def _fixture_case(fixture: dict[str, Any], request_id: str) -> dict[str, Any]:
    cases = fixture.get("requests")
    if not isinstance(cases, dict) or not isinstance(cases.get(request_id), dict):
        raise ValueError(f"fixture has no case for {request_id}")
    return cases[request_id]


def validate_batch(batch: dict[str, Any]) -> list[dict[str, Any]]:
    if batch.get("actor_id") != ACTOR_ID:
        raise ValueError(f"actor_id must be exactly {ACTOR_ID}")
    requests = batch.get("requests")
    if not isinstance(requests, list):
        raise ValueError("requests must be an array")
    seen_companies: set[str] = set()
    seen_requests: set[str] = set()
    for item in requests:
        if not isinstance(item, dict):
            raise ValueError("every request must be an object")
        request_id = item.get("request_id")
        company_id = item.get("company_id")
        if not isinstance(request_id, str) or not request_id or request_id in seen_requests:
            raise ValueError("request_id must be present and unique")
        if not isinstance(company_id, str) or not company_id or company_id in seen_companies:
            raise ValueError("one actor run per Company requires unique company_id values")
        seen_requests.add(request_id)
        seen_companies.add(company_id)
        if item.get("entity_type") != "Company" or item.get("actor_id") != ACTOR_ID:
            raise ValueError("only Company requests for the approved actor are allowed")
        actor_input = item.get("actor_input")
        if not isinstance(actor_input, dict) or set(actor_input) != {"pages", "language"}:
            raise ValueError("actor_input must contain only pages and language")
        if actor_input.get("language") != "en-US" or actor_input.get("pages") != [item.get("facebook_url") or item.get("exact_facebook_url")]:
            raise ValueError("actor_input must contain the single exact official-site Facebook URL")
        retry = item.get("retry_policy")
        if retry != {"max_retries": 0, "resurrection": False, "fallback_actor": None}:
            raise ValueError("request retry/fallback policy is not the required no-retry policy")
    return requests


def execute_one(
    item: dict[str, Any],
    *,
    token: str | None,
    fixture: dict[str, Any] | None,
    max_polls: int,
    poll_interval: float,
    timeout: float,
    transport: Callable[[str, str, str, Any, float], Any] = http_json,
) -> dict[str, Any]:
    request_id = item["request_id"]
    counts = {"actor_run_posts": 0, "status_polls": 0, "dataset_gets": 0}
    snapshots: list[Any] = []
    dataset: list[Any] | None = None
    provider_run_id: str | None = None
    dataset_id: str | None = None
    case = _fixture_case(fixture, request_id) if fixture is not None else None
    try:
        counts["actor_run_posts"] += 1
        if case is not None:
            if "start" not in case:
                raise ValueError(f"fixture case {request_id} has no start response")
            start = case["start"]
        else:
            assert token is not None
            start = transport("POST", f"{API_BASE}/actors/{quote(ACTOR_ID, safe='~')}/runs", token, item["actor_input"], timeout)
        snapshots.append(start)
        run = _unwrap(start)
        provider_run_id = run.get("id")
        status = str(run.get("status") or "").upper()
        poll_responses: list[Any] = []
        fixture_polls = list(case.get("polls") or []) if case is not None else None
        while status in PENDING and counts["status_polls"] < max_polls:
            if not provider_run_id:
                raise ValueError("Apify start response omitted run id")
            if case is None:
                time.sleep(poll_interval)
                assert token is not None
                polled = transport("GET", f"{API_BASE}/actor-runs/{quote(str(provider_run_id), safe='')}", token, None, timeout)
            else:
                if counts["status_polls"] >= len(fixture_polls or []):
                    break
                polled = fixture_polls[counts["status_polls"]]
            counts["status_polls"] += 1
            poll_responses.append(polled)
            snapshots.append(polled)
            run = _unwrap(polled)
            status = str(run.get("status") or "").upper()
        if status in PENDING:
            raise RuntimeError(f"bounded polling exhausted after {counts['status_polls']} polls")
        if status in FAILURE:
            raise RuntimeError(f"Apify run reached terminal failure status {status}")
        if status not in SUCCESS:
            raise RuntimeError(f"Apify run returned unsupported status {status or '<missing>'}")
        dataset_id = run.get("defaultDatasetId") or run.get("default_dataset_id")
        if not dataset_id:
            raise ValueError("successful Apify run omitted defaultDatasetId")
        counts["dataset_gets"] += 1
        if case is not None:
            if "dataset" not in case:
                raise ValueError(f"fixture case {request_id} has no dataset")
            dataset = case["dataset"]
        else:
            assert token is not None
            dataset = transport("GET", f"{API_BASE}/datasets/{quote(str(dataset_id), safe='')}/items?clean=true&format=json", token, None, timeout)
        if not isinstance(dataset, list):
            raise ValueError("Apify dataset response must be an array")
        build_id = run.get("buildId") or run.get("build_id")
        audit: dict[str, Any] = {
            "actor_id": ACTOR_ID,
            "provider_run_id": provider_run_id,
            "default_dataset_id": dataset_id,
            "build_id": build_id,
            "build_sha256": sha256_json({"actor_id": ACTOR_ID, "build_id": build_id}),
            "input_sha256": sha256_json(item["actor_input"]),
            "start_response_sha256": sha256_json(snapshots[0]),
            "run_response_sha256": sha256_json(snapshots[-1]),
            "status_responses_sha256": sha256_json(snapshots[1:]),
            "dataset_sha256": sha256_json(dataset),
            "output_sha256": sha256_json(dataset),
            "operation_counts": counts,
            "cost": _cost(run),
        }
        return {
            "request_id": request_id,
            "company_id": item["company_id"],
            "company_name": item["company_name"],
            "entity_type": "Company",
            "facebook_url": item.get("facebook_url") or item["exact_facebook_url"],
            "exact_facebook_url": item.get("facebook_url") or item["exact_facebook_url"],
            "official_site_evidence": item["official_site_evidence"],
            "missing_channels": item.get("missing_channels") or [field.rsplit("_", 1)[-1] for field in item["missing_fields"]],
            "missing_fields": item["missing_fields"],
            "current_values": item["current_values"],
            "terminal_status": "succeeded",
            "company_candidates": {"email": None, "phone": None},
            "dataset_items": dataset,
            "audit": audit,
        }
    except Exception as exc:
        last_run: dict[str, Any] = {}
        if snapshots:
            try:
                last_run = _unwrap(snapshots[-1])
            except Exception:
                pass
        build_id = last_run.get("buildId") or last_run.get("build_id")
        audit = {
            "actor_id": ACTOR_ID,
            "provider_run_id": provider_run_id,
            "default_dataset_id": dataset_id,
            "build_id": build_id,
            "build_sha256": sha256_json({"actor_id": ACTOR_ID, "build_id": build_id}),
            "input_sha256": sha256_json(item["actor_input"]),
            "start_response_sha256": sha256_json(snapshots[0]) if snapshots else None,
            "run_response_sha256": sha256_json(snapshots[-1]) if snapshots else None,
            "status_responses_sha256": sha256_json(snapshots[1:]),
            "dataset_sha256": None,
            "output_sha256": None,
            "operation_counts": counts,
            "cost": _cost(last_run),
        }
        return {
            "request_id": request_id,
            "company_id": item["company_id"],
            "company_name": item["company_name"],
            "entity_type": "Company",
            "facebook_url": item.get("facebook_url") or item["exact_facebook_url"],
            "exact_facebook_url": item.get("facebook_url") or item["exact_facebook_url"],
            "official_site_evidence": item["official_site_evidence"],
            "missing_channels": item.get("missing_channels") or [field.rsplit("_", 1)[-1] for field in item["missing_fields"]],
            "missing_fields": item["missing_fields"],
            "current_values": item["current_values"],
            "terminal_status": "failed",
            "company_candidates": {"email": None, "phone": None},
            "error": str(exc),
            "dataset_items": None,
            "audit": audit,
        }


def run_batch(batch: dict[str, Any], fixture: dict[str, Any] | None, max_polls: int, poll_interval: float, timeout: float) -> dict[str, Any]:
    requests = validate_batch(batch)
    token: str | None = None
    if fixture is None:
        token = env_value("APIFY_API_KEY") or env_value("APIFY_TOKEN")
        if not token:
            raise ValueError("APIFY_API_KEY is required in live mode")
    results = [
        execute_one(item, token=token, fixture=fixture, max_polls=max_polls, poll_interval=poll_interval, timeout=timeout)
        for item in requests
    ]
    operation_counts = {
        key: sum(int(result["audit"]["operation_counts"][key]) for result in results)
        for key in ("actor_run_posts", "status_polls", "dataset_gets")
    }
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "kind": "a2-apify-official-facebook-results",
        "run_id": batch.get("run_id", "unknown"),
        "actor_id": ACTOR_ID,
        "mode": "fixture" if fixture is not None else "live",
        "result_count": len(results),
        "results": results,
        "external_calls": 0 if fixture is not None else sum(operation_counts.values()),
        "writes": 0,
        "controls": {"max_retries": 0, "resurrection": False, "fallback_actor": None, "max_polls": max_polls},
        "audit": {
            "request_batch_sha256": sha256_json(batch),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "operation_counts": operation_counts,
        },
    }
    body["artifact_sha256"] = sha256_json(body)
    return body


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("requests", type=Path)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--max-polls", type=int, default=60)
    parser.add_argument("--poll-interval", type=float, default=5.0)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if not 1 <= args.max_polls <= 120:
            raise ValueError("max-polls must be between 1 and 120")
        if args.poll_interval < 0 or args.poll_interval > 60:
            raise ValueError("poll-interval must be between 0 and 60 seconds")
        if args.timeout <= 0 or args.timeout > 120:
            raise ValueError("timeout must be between 0 and 120 seconds")
        batch = load_json(args.requests)
        fixture = load_json(args.fixture) if args.fixture else None
        if not isinstance(batch, dict) or (fixture is not None and not isinstance(fixture, dict)):
            raise ValueError("request and fixture inputs must be JSON objects")
        if args.output.exists():
            existing=load_json(args.output);expected=sha256_json(batch);observed=(existing.get("audit") or {}).get("request_batch_sha256") if isinstance(existing,dict) else None
            if observed==expected:
                failures=sum(row.get("terminal_status")!="succeeded" for row in existing.get("results",[]));print(json.dumps({"status":"idempotent_reuse_required","results":existing.get("result_count",0),"failures":failures,"output":str(args.output)},indent=2));return 0 if not failures else 1
            raise ValueError("output already exists for a different request batch")
        result = run_batch(batch, fixture, args.max_polls, args.poll_interval, args.timeout)
        write_json_atomic(args.output, result)
        failures = sum(row["terminal_status"] != "succeeded" for row in result["results"])
        print(json.dumps({"status": "valid" if not failures else "failed", "results": result["result_count"], "failures": failures, "output": str(args.output)}, indent=2))
        return 0 if not failures else 1
    except Exception as exc:
        error = {"status": "error", "error": str(exc)}
        write_json_atomic(args.output, error)
        print(json.dumps(error, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
