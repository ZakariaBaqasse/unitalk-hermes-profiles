#!/usr/bin/env python3
"""Fetch one official site with Firecrawl v2 under a hard five-page boundary."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin, urlsplit

from a2_twenty_fullenrich_common import env_value
from build_official_site_plan import (
    MAX_PAGES,
    PlanError,
    canonical_bytes,
    load_json,
    sha256_json,
    utc_now,
    validate_public_url,
    write_json_atomic,
)

API_BASE = "https://api.firecrawl.dev/v2"
FORMATS = ["markdown", "html", "links"]
DISCOVERED_PAGE_LIMIT = MAX_PAGES - 1
MAX_POLLS = 8
CATEGORY_PATTERNS = {
    "contact": re.compile(r"(?:^|[\W_])(contact|contact us|get in touch|locations?)(?:$|[\W_])", re.I),
    "about": re.compile(r"(?:^|[\W_])(about|about us|our story|who we are)(?:$|[\W_])", re.I),
    "team": re.compile(r"(?:^|[\W_])(team|our team|meet the team|people|leadership)(?:$|[\W_])", re.I),
    "staff": re.compile(r"(?:^|[\W_])(staff|our staff|directory|professionals?)(?:$|[\W_])", re.I),
}




def robots_allows_text(text: str, url: str, user_agent: str = "EquinetA2") -> bool:
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(url)
    parser.parse(text.splitlines())
    return parser.can_fetch(user_agent, url)

def robots_preflight(url: str, user_agent: str = "EquinetA2", timeout: int = 15) -> dict[str, Any]:
    parsed = urlsplit(url);robots_url=f"{parsed.scheme}://{parsed.netloc}/robots.txt";request=urllib.request.Request(robots_url,headers={"User-Agent":user_agent,"Accept":"text/plain"})
    started=utc_now()
    try:
        with urllib.request.urlopen(request,timeout=timeout) as response:
            raw=response.read(512*1024);status=response.status;text=raw.decode("utf-8","replace")
    except urllib.error.HTTPError as exc:
        status=exc.code;text=""
        if status==404:return {"url":robots_url,"http_status":404,"allowed":True,"requested_at":started,"received_at":utc_now()}
        raise FetchError(f"robots preflight blocked with HTTP {status}",state="blocked",status=status) from exc
    except urllib.error.URLError as exc:
        raise FetchError(f"robots preflight unavailable: {exc}",state="unavailable") from exc
    allowed=robots_allows_text(text,url,user_agent)
    return {"url":robots_url,"http_status":status,"allowed":allowed,"robots_sha256":hashlib.sha256(text.encode()).hexdigest(),"requested_at":started,"received_at":utc_now()}

class FetchError(RuntimeError):
    def __init__(self, message: str, *, state: str = "error", status: int | None = None):
        super().__init__(message)
        self.state = state
        self.status = status


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() == "a":
            self._href = next((value for key, value in attrs if key.casefold() == "href"), None)
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = None
            self._text = []


def urllib_transport(method: str, url: str, headers: dict[str, str], body: dict[str, Any] | None, timeout: int) -> tuple[int, dict[str, Any]]:
    data = canonical_bytes(body) if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(8 * 1024 * 1024)
            payload = json.loads(raw.decode("utf-8")) if raw else {}
            return response.status, payload
    except urllib.error.HTTPError as exc:
        raw = exc.read(1024 * 1024)
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeError, json.JSONDecodeError):
            payload = {"error": raw.decode("utf-8", "replace")[:1000]}
        return exc.code, payload


class FixtureTransport:
    """Deterministic request/response transport used only by --fixture and tests."""
    def __init__(self, fixture: dict[str, Any]):
        calls = fixture.get("calls")
        if not isinstance(calls, list):
            raise FetchError("fixture must contain a calls array")
        self.calls = list(calls)
        self.index = 0
        self.requests: list[dict[str, Any]] = []

    def __call__(self, method: str, url: str, headers: dict[str, str], body: dict[str, Any] | None, timeout: int) -> tuple[int, dict[str, Any]]:
        if self.index >= len(self.calls):
            raise FetchError("fixture has no response for the next Firecrawl request")
        expected = self.calls[self.index]
        self.index += 1
        path = urlsplit(url).path
        if expected.get("method") and expected["method"].upper() != method.upper():
            raise FetchError(f"fixture expected {expected['method']} but received {method}")
        expected_path = expected.get("path")
        if expected_path and expected_path != path:
            raise FetchError(f"fixture expected {expected_path} but received {path}")
        self.requests.append({"method": method, "url": url, "body": body})
        response = expected.get("response")
        if not isinstance(response, dict):
            raise FetchError("fixture response must be an object")
        status = expected.get("http_status", 200)
        if not isinstance(status, int):
            raise FetchError("fixture http_status must be an integer")
        return status, response


def _response_hash(payload: Any) -> str:
    try:
        return sha256_json(payload)
    except (TypeError, ValueError):
        return hashlib.sha256(repr(payload).encode("utf-8")).hexdigest()


def _call(
    transport: Callable[..., Any],
    method: str,
    url: str,
    token: str,
    body: dict[str, Any] | None,
    receipts: list[dict[str, Any]],
    *,
    external: bool,
) -> tuple[int, dict[str, Any]]:
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    started = utc_now()
    try:
        raw_result = transport(method, url, headers, body, 60)
        if isinstance(raw_result, tuple) and len(raw_result) == 2:
            status, payload = raw_result
        elif isinstance(raw_result, dict) and "body" in raw_result:
            status, payload = raw_result.get("status", 200), raw_result["body"]
        else:
            raise FetchError("transport must return (status, JSON object)")
        if not isinstance(status, int) or not isinstance(payload, dict):
            raise FetchError("transport returned an invalid status or non-object JSON")
        receipts.append({
            "method": method,
            "endpoint": urlsplit(url).path,
            "http_status": status,
            "requested_at": started,
            "received_at": utc_now(),
            "request_sha256": sha256_json(body) if body is not None else None,
            "response_sha256": _response_hash(payload),
            "external": external,
        })
        return status, payload
    except Exception as exc:
        receipts.append({
            "method": method,
            "endpoint": urlsplit(url).path,
            "http_status": None,
            "requested_at": started,
            "received_at": utc_now(),
            "request_sha256": sha256_json(body) if body is not None else None,
            "response_sha256": None,
            "external": external,
            "error": f"{type(exc).__name__}: {exc}",
        })
        raise


def _blocked_http(status: int) -> bool:
    return status in {401, 403, 407, 429, 451}


def _firecrawl_data(status: int, payload: dict[str, Any], operation: str) -> dict[str, Any]:
    if _blocked_http(status):
        raise FetchError(f"Firecrawl {operation} blocked with HTTP {status}", state="blocked", status=status)
    if status < 200 or status >= 300:
        raise FetchError(f"Firecrawl {operation} failed with HTTP {status}", status=status)
    if payload.get("success") is False:
        message = payload.get("error") or payload.get("message") or f"Firecrawl {operation} reported failure"
        raise FetchError(str(message), state="blocked" if any(word in str(message).casefold() for word in ("robots", "captcha", "forbidden", "paywall")) else "error")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise FetchError(f"Firecrawl {operation} response is missing data")
    return data


def _candidate_links(homepage: dict[str, Any], official_url: str, official_host: str) -> list[dict[str, str]]:
    candidates: list[tuple[str, str]] = []
    raw_links = homepage.get("links")
    if isinstance(raw_links, list):
        for item in raw_links:
            if isinstance(item, str):
                candidates.append((item, item))
            elif isinstance(item, dict) and isinstance(item.get("url") or item.get("href"), str):
                candidates.append((item.get("url") or item.get("href"), str(item.get("text") or item.get("title") or "")))
    html = homepage.get("html")
    if isinstance(html, str) and html:
        parser = LinkParser()
        parser.feed(html)
        candidates.extend(parser.links)
    best: dict[str, tuple[int, str]] = {}
    seen_urls: set[str] = {homepage_url_key(official_url)}
    for href, text in candidates:
        if not isinstance(href, str) or not href.strip():
            continue
        absolute = urljoin(official_url, href.strip())
        try:
            safe = validate_public_url(absolute, official_host=official_host, resolve_dns=False)
        except PlanError:
            continue
        key = homepage_url_key(safe)
        if key in seen_urls:
            continue
        haystack = " ".join((text, urlsplit(safe).path.replace("-", " ").replace("_", " ")))
        matches = [category for category, pattern in CATEGORY_PATTERNS.items() if pattern.search(haystack)]
        if not matches:
            continue
        score = 0 if text else 1
        for category in matches:
            current = best.get(category)
            proposal = (score, safe)
            if current is None or proposal < current:
                best[category] = proposal
    result: list[dict[str, str]] = []
    selected: set[str] = set()
    for category in ("contact", "about", "team", "staff"):
        if category not in best:
            continue
        url = best[category][1]
        key = homepage_url_key(url)
        if key in selected:
            continue
        selected.add(key)
        result.append({"category": category, "url": url})
        if len(result) == DISCOVERED_PAGE_LIMIT:
            break
    return result


def homepage_url_key(url: str) -> str:
    parsed = urlsplit(url)
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme.casefold()}://{(parsed.hostname or '').casefold()}{path}?{parsed.query}"


def _page_from_data(
    data: dict[str, Any],
    requested_url: str,
    category: str,
    official_host: str,
    page_index: int,
    *,
    resolve_dns: bool = False,
    resolver: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    resolved = metadata.get("sourceURL") or metadata.get("url") or requested_url
    resolved = validate_public_url(resolved, official_host=official_host, resolve_dns=resolve_dns, resolver=resolver)
    status_code = metadata.get("statusCode")
    if status_code in {403, 429}:
        raise FetchError(f"collected page returned blocked HTTP {status_code}", state="blocked", status=status_code)
    return {
        "page_index": page_index,
        "category": category,
        "requested_url": requested_url,
        "resolved_url": resolved,
        "title": metadata.get("title"),
        "status": "collected",
        "markdown": data.get("markdown") if isinstance(data.get("markdown"), str) else "",
        "html": data.get("html") if isinstance(data.get("html"), str) else "",
        "links": data.get("links") if isinstance(data.get("links"), list) else [],
        "content_sha256": sha256_json({
            "markdown": data.get("markdown") if isinstance(data.get("markdown"), str) else "",
            "html": data.get("html") if isinstance(data.get("html"), str) else "",
            "links": data.get("links") if isinstance(data.get("links"), list) else [],
        }),
    }


def validate_plan(plan: dict[str, Any], *, resolve_dns: bool, resolver: Callable[..., Any] | None = None) -> tuple[str, str]:
    if plan.get("status") != "ready":
        raise FetchError("official-site plan is not ready", state="blocked")
    if not isinstance(plan.get("run_id"), str) or not plan["run_id"].strip():
        raise FetchError("plan run_id is missing")
    if not isinstance(plan.get("company_id"), str) or not plan["company_id"].strip():
        raise FetchError("plan Company ID is missing")
    if plan.get("page_limit") != MAX_PAGES:
        raise FetchError("plan page_limit must equal five", state="blocked")
    official_url = validate_public_url(plan.get("official_url"), resolve_dns=resolve_dns, resolver=resolver)
    official_host = urlsplit(official_url).hostname or ""
    if plan.get("official_host") != official_host:
        raise FetchError("plan official_host does not match official_url", state="blocked")
    return official_url, official_host


def fetch_official_site(
    plan: dict[str, Any],
    *,
    transport: Callable[..., Any] | None = None,
    fixture: dict[str, Any] | None = None,
    resolver: Callable[..., Any] | None = None,
    resolve_dns: bool | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    receipts: list[dict[str, Any]] = []
    robots_receipt: dict[str, Any] | None = None
    pages: list[dict[str, Any]] = []
    errors: list[str] = []
    discovered: list[dict[str, str]] = []
    fixture_mode = fixture is not None
    if fixture_mode and transport is not None:
        raise FetchError("use fixture or transport, not both")
    if fixture_mode:
        transport = FixtureTransport(fixture)
    live_mode = transport is None and not fixture_mode
    transport = transport or urllib_transport
    resolve_dns = live_mode if resolve_dns is None else resolve_dns
    token = env_value("FIRECRAWL_API_KEY") if live_mode else "non-live-transport-token"
    status_name = "succeeded"
    try:
        if not token:
            raise FetchError("FIRECRAWL_API_KEY is required for live mode", state="blocked")
        official_url, official_host = validate_plan(plan, resolve_dns=resolve_dns, resolver=resolver)
        if live_mode:
            robots_receipt=robots_preflight(official_url)
            if not robots_receipt.get("allowed"):raise FetchError("robots.txt denies the official-site URL",state="blocked")
        scrape_body = {"url": official_url, "formats": FORMATS, "onlyMainContent": False, "storeInCache": False, "skipTlsVerification": False, "removeBase64Images": True, "proxy": "auto"}
        http_status, payload = _call(transport, "POST", API_BASE + "/scrape", token, scrape_body, receipts, external=live_mode)
        homepage = _firecrawl_data(http_status, payload, "homepage scrape")
        pages.append(_page_from_data(homepage, official_url, "homepage", official_host, 1, resolve_dns=resolve_dns, resolver=resolver))
        discovered = _candidate_links(homepage, official_url, official_host)[:DISCOVERED_PAGE_LIMIT]
        # In live mode each selected subdomain is independently resolved before
        # it can enter a provider request, preventing private-address pivots.
        for item in discovered:
            item["url"] = validate_public_url(
                item["url"], official_host=official_host, resolve_dns=resolve_dns, resolver=resolver
            )
        if discovered:
            batch_urls = [item["url"] for item in discovered]
            batch_body = {"urls": batch_urls, "maxConcurrency": 1, "formats": FORMATS, "onlyMainContent": False, "storeInCache": False, "skipTlsVerification": False, "removeBase64Images": True, "proxy": "auto"}
            http_status, payload = _call(transport, "POST", API_BASE + "/batch/scrape", token, batch_body, receipts, external=live_mode)
            if _blocked_http(http_status):
                raise FetchError(f"Firecrawl batch start blocked with HTTP {http_status}", state="blocked", status=http_status)
            if http_status < 200 or http_status >= 300 or payload.get("success") is False:
                raise FetchError(str(payload.get("error") or payload.get("message") or f"Firecrawl batch start failed with HTTP {http_status}"))
            batch_id = payload.get("id")
            if not isinstance(batch_id, str) or not batch_id.strip() or "/" in batch_id:
                raise FetchError("Firecrawl batch response is missing a valid id")
            completed: dict[str, Any] | None = None
            for poll_index in range(MAX_POLLS):
                http_status, polled = _call(transport, "GET", API_BASE + "/batch/scrape/" + batch_id, token, None, receipts, external=live_mode)
                if _blocked_http(http_status):
                    raise FetchError(f"Firecrawl batch poll blocked with HTTP {http_status}", state="blocked", status=http_status)
                if http_status < 200 or http_status >= 300 or polled.get("success") is False:
                    raise FetchError(str(polled.get("error") or polled.get("message") or f"Firecrawl batch poll failed with HTTP {http_status}"))
                poll_status = str(polled.get("status") or "").casefold()
                if poll_status in {"completed", "complete"}:
                    completed = polled
                    break
                if poll_status in {"failed", "cancelled"}:
                    raise FetchError(f"Firecrawl batch ended in {poll_status}")
                if poll_index + 1 < MAX_POLLS:
                    sleeper(min(2 ** poll_index, 8))
            if completed is None:
                raise FetchError("Firecrawl batch did not complete within the polling bound")
            batch_data = completed.get("data")
            if not isinstance(batch_data, list):
                raise FetchError("Firecrawl completed batch is missing its data array")
            if len(batch_data) > DISCOVERED_PAGE_LIMIT:
                raise FetchError("Firecrawl returned more than four discovered pages", state="blocked")
            by_key: dict[str, dict[str, Any]] = {}
            for item in batch_data:
                if not isinstance(item, dict):
                    raise FetchError("Firecrawl batch contains a non-object page")
                metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
                source = metadata.get("sourceURL") or metadata.get("url")
                if isinstance(source, str):
                    safe = validate_public_url(source, official_host=official_host, resolve_dns=False)
                    by_key[homepage_url_key(safe)] = item
            for discovered_item in discovered:
                item = by_key.get(homepage_url_key(discovered_item["url"]))
                if item is None:
                    index = len(pages) - 1
                    item = batch_data[index] if index < len(batch_data) else None
                if not isinstance(item, dict):
                    errors.append(f"no Firecrawl result for {discovered_item['url']}")
                    continue
                pages.append(_page_from_data(item, discovered_item["url"], discovered_item["category"], official_host, len(pages) + 1, resolve_dns=resolve_dns, resolver=resolver))
        if len(pages) > MAX_PAGES:
            raise FetchError("page bound exceeded", state="blocked")
        if errors:
            status_name = "partial"
    except (FetchError, PlanError, OSError, ValueError) as exc:
        status_name = exc.state if isinstance(exc, FetchError) else "blocked" if isinstance(exc, PlanError) else "error"
        errors.append(str(exc))
    result: dict[str, Any] = {
        "schema_id": "a2-firecrawl-official-site-fetch",
        "schema_version": "0.1.0",
        "created_at": utc_now(),
        "status": status_name,
        "run_id": plan.get("run_id"),
        "company_id": plan.get("company_id"),
        "company": plan.get("company"),
        "official_url": plan.get("official_url"),
        "official_host": plan.get("official_host"),
        "plan_sha256": plan.get("artifact_sha256"),
        "page_limit": MAX_PAGES,
        "discovered_links": discovered,
        "page_count": len(pages),
        "pages": pages,
        "provider_receipts": receipts,
        "robots_receipt": robots_receipt,
        "external_calls": sum(1 for item in receipts if item.get("external") is True) + (1 if robots_receipt else 0),
        "fixture_calls": sum(1 for item in receipts if item.get("external") is False),
        "external_actions": 0,
        "browser_fallback": False,
        "web_extract_fallback": False,
        "credit_policy_calls": 0,
        "llm_or_json_extraction": False,
        "errors": errors,
    }
    result["artifact_sha256"] = sha256_json({key: value for key, value in result.items() if key != "artifact_sha256"})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--fixture", type=Path, help="offline Firecrawl transport fixture")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fixture = load_json(args.fixture) if args.fixture else None
    plan=load_json(args.plan)
    if args.output.exists():
        existing=load_json(args.output)
        if existing.get("plan_sha256")==plan.get("artifact_sha256") and existing.get("status") in {"succeeded","partial"}:
            print(json.dumps({"status":"idempotent_reuse_required","pages":existing.get("page_count",0),"external_calls":0,"output":str(args.output),"errors":[]},indent=2));return 0
        print(json.dumps({"status":"error","errors":["output already exists for a different or unsuccessful request"],"external_calls":0},indent=2));return 1
    result = fetch_official_site(plan, fixture=fixture)
    write_json_atomic(args.output, result)
    print(json.dumps({"status": result["status"], "pages": result["page_count"], "external_calls": result["external_calls"], "output": str(args.output), "errors": result["errors"]}, indent=2))
    return 0 if result["status"] in {"succeeded", "partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
