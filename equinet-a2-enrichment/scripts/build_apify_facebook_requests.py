#!/usr/bin/env python3
"""Build one governed official-Facebook Apify request per eligible Company.

This builder is local-only.  It accepts an A2 Company batch, proves that the
exact Facebook URL came from validated official-site evidence, and emits an
Apify request only while Company email and/or Company phone is absent from all
of A1, Twenty, and the official website.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

ACTOR_ID = "apify~facebook-page-contact-information"
SOURCE_NAMES = ("a1", "twenty", "website")
FIELD_KEYS = {
    "email": "company.company_email",
    "phone": "company.company_phone",
}
FIELD_ALIASES = {
    "email": ("company_email", "companyEmail", "email", "business_email", "businessEmail"),
    "phone": ("company_phone", "companyPhone", "phone", "business_phone", "businessPhone"),
}
VALID_EVIDENCE_STATES = {"validated", "verified", "accepted"}


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


def clean(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _walk_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        if value.strip():
            yield value.strip()
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _walk_values(item)
    elif isinstance(value, dict):
        for key in ("value", "raw_value", "normalised_value", "normalized_value"):
            if key in value:
                yield from _walk_values(value[key])


def _source_objects(company: dict[str, Any], source: str) -> list[dict[str, Any]]:
    aliases = {
        "a1": ("a1", "a1_handoff", "A1"),
        "twenty": ("twenty", "twenty_company", "Twenty"),
        "website": ("website", "official_website", "official_site", "website_fields"),
    }[source]
    found: list[dict[str, Any]] = []
    for alias in aliases:
        value = company.get(alias)
        if isinstance(value, dict):
            found.append(value)
    for container_name in ("contact_fields", "contact_coverage", "field_values", "sources"):
        container = company.get(container_name)
        if not isinstance(container, dict):
            continue
        for alias in aliases:
            value = container.get(alias)
            if isinstance(value, dict):
                found.append(value)
    return found


def source_field_values(company: dict[str, Any], source: str, field: str) -> list[str]:
    values: list[str] = []
    for obj in _source_objects(company, source):
        candidates = [obj]
        if isinstance(obj.get("fields"), dict):
            candidates.append(obj["fields"])
        for candidate in candidates:
            for key in FIELD_ALIASES[field] + (FIELD_KEYS[field],):
                values.extend(_walk_values(candidate.get(key)))
    explicit = company.get(f"{field}_values") or company.get(f"company_{field}_values")
    if isinstance(explicit, dict):
        values.extend(_walk_values(explicit.get(source)))
    # Stable de-duplication is useful both for audit and no-change checks.
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        marker = value.casefold()
        if marker not in seen:
            seen.add(marker)
            unique.append(value)
    return unique


def is_facebook_page_url(value: Any) -> bool:
    url = clean(value)
    if not url:
        return False
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    host = (parsed.hostname or "").casefold().removeprefix("www.").removeprefix("m.")
    return parsed.scheme.casefold() == "https" and host == "facebook.com" and bool(parsed.path.strip("/"))


def _evidence_rows(company: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ("official_site_evidence", "validated_official_site_evidence", "website_evidence"):
        raw = company.get(key)
        if isinstance(raw, list):
            rows.extend(item for item in raw if isinstance(item, dict))
        elif isinstance(raw, dict):
            rows.append(raw)
            observations = raw.get("observations")
            if isinstance(observations, list):
                rows.extend(item for item in observations if isinstance(item, dict))
            fields = raw.get("fields")
            if isinstance(fields, dict):
                for field_key, value in fields.items():
                    rows.append({
                        "evidence_id": raw.get("evidence_id"),
                        "source_type": raw.get("source_type") or raw.get("source_kind"),
                        "source_url": raw.get("source_url"),
                        "status": raw.get("status") or raw.get("validation_status"),
                        "field_key": field_key,
                        "value": value,
                    })
    return rows


def _official_site_source(row: dict[str, Any]) -> bool:
    source = clean(row.get("source_type") or row.get("source_kind") or row.get("source_id"))
    if not source:
        return False
    compact = "".join(ch for ch in source.casefold() if ch.isalnum())
    return "official" in compact and ("site" in compact or "website" in compact)


def find_validated_official_facebook_urls(company: dict[str, Any]) -> list[dict[str, Any]]:
    accepted: list[dict[str, Any]] = []
    for row in _evidence_rows(company):
        status = clean(row.get("validation_status") or row.get("verification_status") or row.get("status"))
        if not status or status.casefold() not in VALID_EVIDENCE_STATES or not _official_site_source(row):
            continue
        field_key = clean(row.get("field_key") or row.get("claim_key") or row.get("key"))
        value = row.get("value") or row.get("raw_value") or row.get("normalised_value") or row.get("normalized_value")
        if not value:
            for key in ("facebook_url", "facebook_page_url", "company_facebook_url"):
                if row.get(key):
                    field_key, value = key, row[key]
                    break
        if not field_key or "facebook" not in field_key.casefold() or not is_facebook_page_url(value):
            continue
        accepted.append({
            "facebook_url": clean(value),
            "evidence_id": clean(row.get("evidence_id") or row.get("id")),
            "source_url": clean(row.get("source_url") or row.get("official_site_url")),
            "status": status.casefold(),
            "source_type": clean(row.get("source_type") or row.get("source_kind") or row.get("source_id")),
            "field_key": field_key,
        })
    # Preserve exact URLs.  Do not silently canonicalise a conflicting official-site observation.
    deduped: dict[str, dict[str, Any]] = {}
    for item in accepted:
        deduped.setdefault(item["facebook_url"], item)
    return list(deduped.values())


def company_identity(company: dict[str, Any]) -> tuple[str | None, str | None]:
    company_id = clean(company.get("company_id") or company.get("twenty_company_id") or company.get("id"))
    name = clean(company.get("company_name") or company.get("name"))
    return company_id, name


def eligibility(company: dict[str, Any]) -> dict[str, Any]:
    values = {
        FIELD_KEYS[field]: [
            value
            for source in SOURCE_NAMES
            for value in source_field_values(company, source, field)
        ]
        for field in FIELD_KEYS
    }
    missing = [key for key, current in values.items() if not current]
    evidence = find_validated_official_facebook_urls(company)
    reasons: list[str] = []
    if not missing:
        reasons.append("company_email_and_phone_already_present_across_a1_twenty_and_website")
    if not evidence:
        reasons.append("no_validated_official_site_facebook_url")
    elif len(evidence) > 1:
        reasons.append("conflicting_validated_official_site_facebook_urls")
    return {"eligible": not reasons, "missing_fields": missing, "current_values": values, "evidence": evidence, "reasons": reasons}


def build_requests(document: dict[str, Any]) -> dict[str, Any]:
    companies = document.get("companies")
    if not isinstance(companies, list):
        raise ValueError("companies must be an array")
    run_id = clean(document.get("run_id")) or "unknown"
    requests: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    seen_company_ids: set[str] = set()
    for index, company in enumerate(companies):
        if not isinstance(company, dict):
            blocked.append({"company_index": index, "reason": "company_must_be_an_object"})
            continue
        company_id, name = company_identity(company)
        if not company_id or not name:
            blocked.append({"company_index": index, "company_id": company_id, "reason": "company_id_and_company_name_are_required"})
            continue
        if company_id in seen_company_ids:
            blocked.append({"company_id": company_id, "reason": "duplicate_company_suppressed_one_actor_run_per_company"})
            continue
        seen_company_ids.add(company_id)
        gate = eligibility(company)
        if not gate["eligible"]:
            blocked.append({"company_id": company_id, "company_name": name, "reasons": gate["reasons"], "missing_fields": gate["missing_fields"]})
            continue
        evidence = gate["evidence"][0]
        actor_input = {"pages": [evidence["facebook_url"]], "language": "en-US"}
        requests.append({
            "request_id": f"apify-facebook-{company_id}",
            "company_id": company_id,
            "company_name": name,
            "entity_type": "Company",
            "actor_id": ACTOR_ID,
            "actor_input": actor_input,
            "actor_input_sha256": sha256_json(actor_input),
            "facebook_url": evidence["facebook_url"],
            "exact_facebook_url": evidence["facebook_url"],
            "official_site_evidence": evidence,
            "missing_channels": [field.rsplit("_", 1)[-1] for field in gate["missing_fields"]],
            "missing_fields": gate["missing_fields"],
            "current_values": gate["current_values"],
            "retry_policy": {"max_retries": 0, "resurrection": False, "fallback_actor": None},
        })
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "kind": "a2-apify-official-facebook-requests",
        "run_id": run_id,
        "actor_id": ACTOR_ID,
        "request_count": len(requests),
        "requests": requests,
        "blocked_requests": blocked,
        "controls": {
            "one_actor_run_per_company": True,
            "company_count_max": None,
            "max_retries": 0,
            "resurrection": False,
            "fallback_actor": None,
            "external_calls": 0,
            "writes": 0,
        },
        "audit": {
            "build_input_sha256": sha256_json(document),
            "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    body["artifact_sha256"] = sha256_json(body)
    return body


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("companies", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        document = load_json(args.companies)
        if not isinstance(document, dict):
            raise ValueError("input must be a JSON object")
        result = build_requests(document)
        write_json_atomic(args.output, result)
        print(json.dumps({"status": "valid", "requests": result["request_count"], "blocked": len(result["blocked_requests"]), "output": str(args.output)}, indent=2))
        return 0
    except Exception as exc:
        error = {"status": "error", "error": str(exc)}
        write_json_atomic(args.output, error)
        print(json.dumps(error, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
