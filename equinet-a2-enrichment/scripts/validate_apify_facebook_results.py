#!/usr/bin/env python3
"""Validate/minimise official-Facebook Apify results into Company candidates.

Only page identity, Company contact, website, and error fields are accepted.
Personal-profile or otherwise unexpected data is rejected.  This script emits
append-only Company candidates and never emits Person fields or performs a
write.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ACTOR_ID = "apify~facebook-page-contact-information"
ALLOWED_ITEM_FIELDS = {
    "facebookUrl", "pageUrl",                 # page URL
    "pageName", "title",                       # page name/title
    "email", "phone", "website",             # bounded contact fields
    "error", "errorDescription",              # bounded error fields
}
URL_FIELDS = ("facebookUrl", "pageUrl")
PERSONAL_PROFILE_FIELD = "personalProfileData"
LEGAL_SUFFIXES = {"llc", "inc", "incorporated", "ltd", "limited", "corp", "corporation", "company", "co"}


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


def canonical_facebook_url(value: Any) -> str | None:
    url = clean(value)
    if not url:
        return None
    try:
        parsed = urlsplit(url)
    except ValueError:
        return None
    host = (parsed.hostname or "").casefold()
    for prefix in ("www.", "m."):
        if host.startswith(prefix):
            host = host[len(prefix):]
    if parsed.scheme.casefold() != "https" or host != "facebook.com" or not parsed.path.strip("/"):
        return None
    path = re.sub(r"/+", "/", parsed.path).rstrip("/").casefold()
    query = f"?{parsed.query}" if parsed.query else ""
    return f"https://facebook.com{path}{query}"


def _name_tokens(value: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", value.casefold())
    while tokens and tokens[-1] in LEGAL_SUFFIXES:
        tokens.pop()
    return tokens


def company_name_matches(expected: str, observed: str) -> bool:
    left, right = _name_tokens(expected), _name_tokens(observed)
    if not left or not right:
        return False
    if left == right:
        return True
    # Allow a short descriptor around the exact Company name, but not a wholly
    # different page title.
    left_text, right_text = " ".join(left), " ".join(right)
    return (left_text in right_text or right_text in left_text) and min(len(left), len(right)) >= 2


def _normalise_email(value: str) -> str | None:
    value = value.strip().casefold()
    if value.count("@") != 1 or any(ch.isspace() for ch in value):
        return None
    local, domain = value.split("@")
    if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        return None
    return value


def _normalise_phone(value: str) -> str | None:
    value = value.strip()
    digits = re.sub(r"\D", "", value)
    if not 7 <= len(digits) <= 15:
        return None
    return value


def _duplicate(value: str, current: list[Any], field_key: str) -> bool:
    if field_key.endswith("email"):
        marker = value.casefold()
        return any(isinstance(item, str) and item.strip().casefold() == marker for item in current)
    marker = re.sub(r"\D", "", value)
    return any(isinstance(item, str) and re.sub(r"\D", "", item) == marker for item in current)


def _candidate(row: dict[str, Any], field_key: str, value: str) -> dict[str, Any]:
    evidence = row.get("official_site_evidence") if isinstance(row.get("official_site_evidence"), dict) else {}
    provider_audit = row.get("audit") if isinstance(row.get("audit"), dict) else {}
    identity = {"company_id": row["company_id"], "field_key": field_key, "value": value, "dataset_sha256": provider_audit.get("dataset_sha256")}
    return {
        "candidate_id": "apify-fb-" + sha256_json(identity)[:24],
        "entity_type": "Company",
        "company_id": row["company_id"],
        "field_key": field_key,
        "value": value,
        "operation": "append_candidate",
        "source_id": "apify_facebook_page_contact_information",
        "source_url": (row.get("facebook_url") or row["exact_facebook_url"]),
        "official_site_evidence_id": evidence.get("evidence_id"),
        "provider_run_id": provider_audit.get("provider_run_id"),
        "default_dataset_id": provider_audit.get("default_dataset_id"),
        "provider_output_sha256": provider_audit.get("output_sha256"),
        "verification_status": "present_unverified",
        "write_authorized": False,
        "outreach_authorized": False,
    }


def validate_item(row: dict[str, Any]) -> tuple[str, list[dict[str, Any]], list[str]]:
    if row.get("entity_type") != "Company":
        return "rejected", [], ["result entity_type must be Company"]
    if row.get("terminal_status") != "succeeded":
        return "provider_failed", [], [clean(row.get("error")) or "provider run failed"]
    items = row.get("dataset_items")
    if not isinstance(items, list):
        return "rejected", [], ["dataset_items must be an array"]
    if len(items) > 1:
        return "rejected", [], ["dataset must contain at most one item for one Company"]
    if not items:
        return "no_change", [], []
    item = items[0]
    if not isinstance(item, dict):
        return "rejected", [], ["dataset item must be an object"]
    if PERSONAL_PROFILE_FIELD in item:
        return "rejected", [], ["personalProfileData is prohibited"]
    unexpected = sorted(set(item) - ALLOWED_ITEM_FIELDS)
    if unexpected:
        return "rejected", [], ["unexpected dataset fields: " + ", ".join(unexpected)]
    scalar_fields = set(ALLOWED_ITEM_FIELDS) - {"website"}
    malformed = sorted(key for key in scalar_fields if key in item and item[key] is not None and not isinstance(item[key], str))
    website = item.get("website")
    website_malformed = website is not None and not isinstance(website, str) and not (
        isinstance(website, list) and all(isinstance(value, str) for value in website)
    )
    if malformed or website_malformed:
        names = malformed + (["website"] if website_malformed else [])
        return "rejected", [], ["unexpected data type for: " + ", ".join(names)]
    expected_url = canonical_facebook_url((row.get("facebook_url") or row.get("exact_facebook_url")))
    observed_urls = [clean(item.get(key)) for key in URL_FIELDS if clean(item.get(key))]
    if not expected_url:
        return "rejected", [], ["request exact_facebook_url is invalid"]
    if not observed_urls and not (clean(item.get("error")) or clean(item.get("errorDescription"))):
        return "rejected", [], ["dataset item omitted page URL"]
    mismatched = [value for value in observed_urls if canonical_facebook_url(value) != expected_url]
    if mismatched:
        return "rejected", [], ["dataset page URL does not match the exact official-site Facebook URL"]
    expected_name = clean(row.get("company_name"))
    observed_names = [clean(item.get(key)) for key in ("title",) if clean(item.get(key))]
    if expected_name and observed_names and not any(company_name_matches(expected_name, name) for name in observed_names):
        return "rejected", [], ["dataset page name/title does not match the Company"]
    if clean(item.get("error")) or clean(item.get("errorDescription")):
        return "provider_error", [], [clean(item.get("error")) or clean(item.get("errorDescription")) or "provider item error"]
    missing = row.get("missing_fields")
    current = row.get("current_values")
    if not isinstance(missing, list) or not isinstance(current, dict):
        return "rejected", [], ["result omitted field eligibility context"]
    candidates: list[dict[str, Any]] = []
    email = clean(item.get("email"))
    if email and "company.company_email" in missing:
        normal = _normalise_email(email)
        if not normal:
            return "rejected", [], ["invalid Company email returned"]
        if not _duplicate(normal, current.get("company.company_email") or [], "company.company_email"):
            candidates.append(_candidate(row, "company.company_email", normal))
    phone = clean(item.get("phone"))
    if phone and "company.company_phone" in missing:
        normal_phone = _normalise_phone(phone)
        if not normal_phone:
            return "rejected", [], ["invalid Company phone returned"]
        if not _duplicate(normal_phone, current.get("company.company_phone") or [], "company.company_phone"):
            candidates.append(_candidate(row, "company.company_phone", normal_phone))
    return ("candidates_ready" if candidates else "no_change"), candidates, []


def validate_results(document: dict[str, Any]) -> dict[str, Any]:
    if document.get("actor_id") != ACTOR_ID:
        raise ValueError(f"actor_id must be exactly {ACTOR_ID}")
    rows = document.get("results")
    if not isinstance(rows, list):
        raise ValueError("results must be an array")
    companies: list[dict[str, Any]] = []
    all_candidates: list[dict[str, Any]] = []
    rejection_count = 0
    for row in rows:
        if not isinstance(row, dict):
            rejection_count += 1
            companies.append({"status": "rejected", "errors": ["result must be an object"], "append_candidates": []})
            continue
        status, candidates, errors = validate_item(row)
        if status == "rejected":
            rejection_count += 1
        all_candidates.extend(candidates)
        values = {"email": None, "phone": None}
        for candidate in candidates:
            if candidate.get("field_key") == "company.company_email":
                values["email"] = candidate.get("value")
            elif candidate.get("field_key") == "company.company_phone":
                values["phone"] = candidate.get("value")
        if status == "rejected":
            terminal_status = "blocked" if any("personalProfileData" in error or "unexpected" in error for error in errors) else "output_mismatch"
        elif status in {"provider_failed", "provider_error"}:
            terminal_status = "failed"
        else:
            terminal_status = "succeeded"
        companies.append({
            "request_id": row.get("request_id"),
            "company_id": row.get("company_id"),
            "company_name": row.get("company_name"),
            "facebook_url": row.get("facebook_url") or row.get("exact_facebook_url"),
            "entity_type": "Company",
            "terminal_status": terminal_status,
            "company_candidates": values,
            "status": status,
            "errors": errors,
            "append_candidates": candidates,
            "audit": row.get("audit"),
        })
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "kind": "a2-apify-official-facebook-company-candidates",
        "status": "invalid" if rejection_count else "valid",
        "run_id": document.get("run_id", "unknown"),
        "actor_id": ACTOR_ID,
        "company_count": len(companies),
        "candidate_count": len(all_candidates),
        "rejection_count": rejection_count,
        "results": companies,
        "companies": companies,
        "append_candidates": all_candidates,
        "controls": {"company_only": True, "append_only": True, "writes": 0, "external_calls": 0},
        "audit": {
            "validation_input_sha256": sha256_json(document),
            "validator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "provider_artifact_sha256": document.get("artifact_sha256"),
        },
    }
    body["audit"]["validation_output_sha256"] = sha256_json(body)
    body["artifact_sha256"] = sha256_json(body)
    return body


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        document = load_json(args.results)
        if not isinstance(document, dict):
            raise ValueError("input must be a JSON object")
        result = validate_results(document)
        write_json_atomic(args.output, result)
        print(json.dumps({"status": result["status"], "companies": result["company_count"], "candidates": result["candidate_count"], "rejections": result["rejection_count"], "output": str(args.output)}, indent=2))
        return 0 if result["status"] == "valid" else 1
    except Exception as exc:
        error = {"status": "error", "error": str(exc)}
        write_json_atomic(args.output, error)
        print(json.dumps(error, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
