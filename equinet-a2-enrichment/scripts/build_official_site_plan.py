#!/usr/bin/env python3
"""Build a bounded plan for reading one Company's official public website."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import socket
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit

MAX_PAGES = 5
ALLOWED_SCHEMES = {"http", "https"}
METADATA_ADDRESSES = {
    ipaddress.ip_address("169.254.169.254"),
    ipaddress.ip_address("169.254.170.2"),
    ipaddress.ip_address("100.100.100.200"),
}


class PlanError(ValueError):
    """Raised when an official-site request violates the bounded contract."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise PlanError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)
    if not isinstance(value, dict):
        raise PlanError("JSON root must be an object")
    return value


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    temporary.replace(path)


def _clean_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PlanError(f"{label} must be a non-empty string")
    cleaned = value.strip()
    if any(ord(char) < 32 for char in cleaned):
        raise PlanError(f"{label} contains a control character")
    return cleaned


def canonical_host(host: str) -> str:
    value = host.casefold().rstrip(".")
    try:
        return value.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise PlanError("URL hostname is not valid IDNA") from exc


def _literal_ip(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    candidate = host.removeprefix("[").removesuffix("]")
    try:
        return ipaddress.ip_address(candidate)
    except ValueError:
        pass
    # URL parsers and resolvers may accept legacy integer/octal/short IPv4
    # spellings.  Canonicalise those without making a DNS request.
    try:
        if re.fullmatch(r"(?:0[xX][0-9a-fA-F]+|[0-9]+)", candidate):
            return ipaddress.IPv4Address(int(candidate, 0) if candidate.casefold().startswith("0x") else int(candidate, 10))
        if re.fullmatch(r"[0-9xXa-fA-F.]+", candidate):
            return ipaddress.IPv4Address(socket.inet_ntoa(socket.inet_aton(candidate)))
    except (OSError, ValueError, OverflowError):
        pass
    return None


def _blocked_ip(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return address in METADATA_ADDRESSES or not address.is_global


def resolve_public_addresses(host: str, resolver: Callable[..., Any] | None = None) -> list[str]:
    resolver = resolver or socket.getaddrinfo
    try:
        rows = resolver(host, None, type=socket.SOCK_STREAM)
    except (OSError, socket.gaierror) as exc:
        raise PlanError(f"official-site hostname could not be resolved: {host}") from exc
    addresses: list[str] = []
    for row in rows:
        try:
            raw = row[4][0]
            address = ipaddress.ip_address(raw)
        except (IndexError, TypeError, ValueError):
            raise PlanError("DNS resolver returned an invalid address")
        if _blocked_ip(address):
            raise PlanError(f"official-site hostname resolves to a non-public address: {address}")
        if str(address) not in addresses:
            addresses.append(str(address))
    if not addresses:
        raise PlanError(f"official-site hostname returned no addresses: {host}")
    return addresses


def site_root_host(host: str) -> str:
    return host[4:] if host.startswith("www.") else host


def same_site_host(candidate_host: str, official_host: str) -> bool:
    candidate = site_root_host(canonical_host(candidate_host))
    official = site_root_host(canonical_host(official_host))
    return candidate == official or candidate.endswith("." + official)


def validate_public_url(
    value: Any,
    *,
    official_host: str | None = None,
    resolve_dns: bool = False,
    resolver: Callable[..., Any] | None = None,
) -> str:
    url = _clean_string(value, "official URL")
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise PlanError("official URL is malformed") from exc
    scheme = parsed.scheme.casefold()
    if scheme not in ALLOWED_SCHEMES:
        raise PlanError("official URL must use HTTP or HTTPS")
    if not parsed.hostname:
        raise PlanError("official URL must be absolute and include a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise PlanError("official URL must not contain credentials")
    if port is not None and port not in {80, 443}:
        raise PlanError("official URL must not use a non-standard port")
    host = canonical_host(parsed.hostname)
    literal = _literal_ip(host)
    if literal is not None and _blocked_ip(literal):
        raise PlanError("official URL must not target private, loopback, link-local, reserved, or metadata addresses")
    if official_host is not None and not same_site_host(host, official_host):
        raise PlanError("URL is outside the official-site domain")
    if resolve_dns and literal is None:
        resolve_public_addresses(host, resolver)
    netloc = f"[{host}]" if ":" in host else host
    if port is not None:
        netloc += f":{port}"
    path = parsed.path or "/"
    return urlunsplit((scheme, netloc, path, parsed.query, ""))


def extract_company(request: dict[str, Any]) -> tuple[dict[str, Any], str]:
    company = request.get("company")
    if not isinstance(company, dict):
        raise PlanError("company must be an object")
    company_id = company.get("company_id") or company.get("twenty_company_id") or company.get("id")
    company_id = _clean_string(company_id, "Company ID")
    _clean_string(company.get("name"), "Company name")
    return company, company_id


def build_plan(request: dict[str, Any], *, resolve_dns: bool = False, resolver: Callable[..., Any] | None = None) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise PlanError("request must be an object")
    run_id = _clean_string(request.get("run_id"), "run_id")
    company, company_id = extract_company(request)
    supplied_url = request.get("official_url") or request.get("official_website_url") or company.get("official_url") or company.get("website")
    official_url = validate_public_url(supplied_url, resolve_dns=resolve_dns, resolver=resolver)
    official_host = canonical_host(urlsplit(official_url).hostname or "")
    plan: dict[str, Any] = {
        "schema_id": "a2-official-site-plan",
        "schema_version": "0.1.0",
        "created_at": utc_now(),
        "status": "ready",
        "run_id": run_id,
        "company_id": company_id,
        "company": company,
        "official_url": official_url,
        "official_host": official_host,
        "page_limit": MAX_PAGES,
        "homepage_pages": 1,
        "discovered_page_limit": MAX_PAGES - 1,
        "discovery_categories": ["contact", "about", "team", "staff"],
        "allowed_schemes": sorted(ALLOWED_SCHEMES),
        "same_domain_only": True,
        "live_dns_validation_required": True,
        "firecrawl": {
            "api_version": "v2",
            "homepage_endpoint": "POST /v2/scrape",
            "discovered_pages_endpoint": "POST /v2/batch/scrape then GET /v2/batch/scrape/{id}",
            "formats": ["markdown", "html", "links"],
            "onlyMainContent": False,
            "storeInCache": False,
            "skipTlsVerification": False,
            "maxConcurrency": 1,
            "json_or_llm_formats": False,
            "credit_policy_calls": False,
        },
        "external_calls": 0,
        "external_actions": 0,
        "errors": [],
    }
    plan["artifact_sha256"] = sha256_json({key: value for key, value in plan.items() if key != "artifact_sha256"})
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resolve-dns", action="store_true", help="Resolve and validate the public hostname while building the plan")
    args = parser.parse_args()
    try:
        result = build_plan(load_json(args.request), resolve_dns=args.resolve_dns)
        code = 0
    except Exception as exc:
        result = {"schema_id": "a2-official-site-plan", "status": "invalid", "errors": [str(exc)], "external_calls": 0, "external_actions": 0}
        code = 1
    write_json_atomic(args.output, result)
    print(json.dumps({"status": result["status"], "output": str(args.output), "errors": result.get("errors", [])}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
