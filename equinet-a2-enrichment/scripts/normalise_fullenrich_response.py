#!/usr/bin/env python3
"""Minimise and validate FullEnrich A2 responses without external access."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ALLOWED_OPERATIONS = {"people_search", "people_lookup", "contact_enrichment"}
SECOND_CONTACT_REASONS = {"large_organisation", "shared_purchasing_or_operational_responsibility"}
ACCEPTED_EMAIL_STATUSES = {"DELIVERABLE", "HIGH_PROBABILITY", "CATCH_ALL", "CATCH_All"}


def nested(value: dict[str, Any], *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def clean_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def professional_url(profile: dict[str, Any]) -> str | None:
    return clean_string(nested(profile, "social_profiles", "professional_network", "url"))


def current_employment(profile: dict[str, Any]) -> dict[str, Any]:
    value = nested(profile, "employment", "current")
    return value if isinstance(value, dict) else {}


def minimise_person(profile: dict[str, Any]) -> dict[str, Any]:
    employment = current_employment(profile)
    company = employment.get("company") if isinstance(employment.get("company"), dict) else {}
    location = profile.get("location") if isinstance(profile.get("location"), dict) else {}
    return {
        "provider_person_id": clean_string(profile.get("id")),
        "full_name": clean_string(profile.get("full_name")),
        "current_role": clean_string(employment.get("title")),
        "organisation_name": clean_string(company.get("name")),
        "organisation_domain": clean_string(company.get("domain")),
        "location": {
            key: clean_string(location.get(key))
            for key in ("city", "region", "country", "country_code")
            if clean_string(location.get(key)) is not None
        },
        "professional_network_url": professional_url(profile),
    }


def select_work_email(contact_info: dict[str, Any]) -> tuple[str | None, str | None]:
    values = []
    best = contact_info.get("most_probable_work_email")
    if isinstance(best, dict):
        values.append(best)
    values.extend(item for item in (contact_info.get("work_emails") or []) if isinstance(item, dict))
    for item in values:
        email = clean_string(item.get("email"))
        status = clean_string(item.get("status"))
        if email and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            return email.casefold(), status or "unknown"
    return None, None


def select_mobile(contact_info: dict[str, Any]) -> tuple[str | None, str | None]:
    best = contact_info.get("most_probable_phone")
    if isinstance(best, dict) and clean_string(best.get("number")):
        return clean_string(best.get("number")), clean_string(best.get("region"))
    for item in contact_info.get("phones") or []:
        if isinstance(item, dict) and clean_string(item.get("number")):
            return clean_string(item.get("number")), clean_string(item.get("region"))
    return None, None


def select_personal_email(contact_info: dict[str, Any]) -> tuple[str | None, str | None]:
    best = contact_info.get("most_probable_personal_email")
    if isinstance(best, dict):
        email = clean_string(best.get("email"))
        status = clean_string(best.get("status"))
        if email and status in ACCEPTED_EMAIL_STATUSES and status != "INVALID":
            return email.casefold(), status
    for item in contact_info.get("personal_emails") or []:
        if not isinstance(item, dict):
            continue
        email = clean_string(item.get("email"))
        status = clean_string(item.get("status"))
        if email and status in ACCEPTED_EMAIL_STATUSES and status != "INVALID":
            return email.casefold(), status
    return None, None


def normalise(request: dict[str, Any]) -> dict[str, Any]:
    operation = request.get("operation")
    if operation not in ALLOWED_OPERATIONS:
        raise ValueError("unsupported FullEnrich operation")
    candidate_id = clean_string(request.get("candidate_id"))
    if not candidate_id:
        raise ValueError("candidate_id is required")
    payload = request.get("provider_payload")
    if not isinstance(payload, dict):
        raise ValueError("provider_payload must be an object")

    result: dict[str, Any] = {
        "adapter_version": "0.1.1",
        "provider": "fullenrich",
        "operation": operation,
        "candidate_id": candidate_id,
        "provider_request_id": clean_string(payload.get("enrichment_id") or payload.get("id")),
        "status": clean_string(payload.get("status")) or "completed",
        "contacts": [],
        "usage": {
            "credits": nested(payload, "metadata", "credits") if isinstance(payload.get("metadata"), dict) else nested(payload, "cost", "credits"),
            "currency": "FullEnrich credits",
            "rate_verification": "premium_plan_rate_pending",
        },
        "discarded_fields": ["personal_emails", "education", "skills", "full_employment_history", "connection_counts", "personal_description"],
        "personal_email_requested": False,
        "personal_email_retained": False,
        "crm_write_authorized": False,
        "outreach_authorized": False,
    }

    if operation in {"people_search", "people_lookup"}:
        people = payload.get("people")
        if not isinstance(people, list):
            raise ValueError("people response must contain a people array")
        expected_limit = 1 if operation == "people_lookup" else int(request.get("result_limit", 1))
        if expected_limit < 1 or expected_limit > (1 if operation == "people_lookup" else 2):
            raise ValueError("result limit exceeds the approved operation limit")
        prior_unique = int(request.get("prior_unique_people_returned", 0))
        if prior_unique + len(people) > 2:
            raise ValueError("maximum two unique people returned per prospect exceeded")
        if len(people) > expected_limit:
            raise ValueError("provider returned more people than requested")
        if len(people) > 1 and request.get("second_contact_reason") not in SECOND_CONTACT_REASONS:
            raise ValueError("second contact requires an approved reason")
        seen: set[str] = set()
        for person in people:
            if not isinstance(person, dict):
                continue
            item = minimise_person(person)
            identity = item["provider_person_id"] or item["professional_network_url"] or f"{item['full_name']}|{item['organisation_domain']}"
            if identity in seen:
                continue
            seen.add(identity)
            result["contacts"].append(item)
        result["contact_information_returned"] = False
        result["result_count"] = len(result["contacts"])
        return result

    requested_fields = set(request.get("requested_enrich_fields") or [])
    if requested_fields != {"contact.work_emails", "contact.phones"}:
        raise ValueError("contact enrichment must request exactly work email and phone")
    data = payload.get("data")
    if not isinstance(data, list):
        raise ValueError("contact enrichment response must contain a data array")
    if len(data) > 2:
        raise ValueError("maximum two selected contacts per prospect exceeded")
    if len(data) > 1 and request.get("second_contact_reason") not in SECOND_CONTACT_REASONS:
        raise ValueError("second contact requires an approved reason")
    incidental_personal_email_retained_count = 0
    for raw in data:
        if not isinstance(raw, dict):
            continue
        profile = raw.get("profile") if isinstance(raw.get("profile"), dict) else {}
        input_data = raw.get("input") if isinstance(raw.get("input"), dict) else {}
        contact_info = raw.get("contact_info") if isinstance(raw.get("contact_info"), dict) else {}
        person = minimise_person(profile)
        if person["full_name"] is None:
            person["full_name"] = clean_string(input_data.get("full_name")) or " ".join(filter(None, [clean_string(input_data.get("first_name")), clean_string(input_data.get("last_name"))])) or None
        if person["professional_network_url"] is None:
            person["professional_network_url"] = clean_string(input_data.get("professional_network_url") or input_data.get("linkedin_url"))
        email, email_status = select_work_email(contact_info)
        mobile, mobile_region = select_mobile(contact_info)
        personal_email, personal_email_status = select_personal_email(contact_info)
        if personal_email:
            incidental_personal_email_retained_count += 1
        result["contacts"].append({
            **person,
            "business_email": email,
            "business_email_status": email_status,
            "mobile_phone": mobile,
            "mobile_region": mobile_region,
            "personal_email_candidate": personal_email,
            "personal_email_status": personal_email_status,
            "personal_email_collection_mode": "incidental_provider_return" if personal_email else None,
            "provider_custom": raw.get("custom") if isinstance(raw.get("custom"), dict) else {},
        })
    result["contact_information_returned"] = True
    result["result_count"] = len(result["contacts"])
    result["incidental_personal_email_retained_count"] = incidental_personal_email_retained_count
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        request = json.loads(args.request.read_text(encoding="utf-8"))
        result = normalise(request)
        result["validation_status"] = "pass"
        code = 0
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        result = {"validation_status": "fail", "error": str(exc)}
        code = 1
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
