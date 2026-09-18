#!/usr/bin/env python3
"""Classify a professional-profile URL linked by an official site.

This utility never fetches the linked platform. It retains an explicitly
published URL and prepares the approved FullEnrich route without authorising
runtime execution.
"""
from __future__ import annotations

import argparse
import json
from urllib.parse import urlsplit, urlunsplit

SOCIAL_HOSTS = {
    "linkedin.com": "linkedin",
    "facebook.com": "facebook",
    "instagram.com": "instagram",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
}


def normalise_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise ValueError("social profile URL must be an absolute HTTP(S) URL")
    host = parsed.hostname.lower().rstrip(".") if parsed.hostname else ""
    for prefix in ("www.", "m."):
        if host.startswith(prefix):
            host = host[len(prefix):]
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit(("https", host + port, path, parsed.query, ""))


def platform_for(url: str) -> str | None:
    host = urlsplit(url).hostname or ""
    return next((platform for domain, platform in SOCIAL_HOSTS.items() if host == domain or host.endswith("." + domain)), None)


def linkedin_subject(url: str) -> str | None:
    if platform_for(url) != "linkedin":
        return None
    parts = [part for part in urlsplit(url).path.split("/") if part]
    if not parts:
        return None
    if parts[0].casefold() in {"company", "school", "showcase"}:
        return "organisation"
    if parts[0].casefold() in {"in", "pub"}:
        return "person"
    return None


def classify(request: dict) -> dict:
    result = {
        "action": "reject",
        "reason": None,
        "platform": None,
        "normalised_url": None,
        "canonical_field": None,
        "attribution": None,
        "open_social_profile": False,
        "extract_social_profile": False,
        "provider_route": None,
        "provider_input_priority": None,
        "runtime_execution": False,
        "consent": False,
        "outreach_eligibility": False,
        "buying_influence": False,
    }
    if request.get("source") != "prospect_official_website":
        result["reason"] = "URL was not supplied by the approved official-site check"
        return result
    if request.get("explicitly_linked") is not True:
        result["reason"] = "URL was not explicitly linked on the approved official-site page"
        return result
    try:
        url = normalise_url(request.get("url", ""))
    except (ValueError, TypeError):
        result["reason"] = "URL is invalid"
        return result
    platform = platform_for(url)
    if platform is None:
        result["reason"] = "URL is not a recognised professional social platform"
        return result
    result["platform"] = platform
    result["normalised_url"] = url

    context = request.get("page_context")
    detected = linkedin_subject(url)
    if context not in {"person", "organisation"}:
        result.update(action="hold_attribution_for_review", reason="official-page context does not support person or organisation attribution")
        return result
    if detected is not None and detected != context:
        result.update(action="hold_attribution_for_review", reason="LinkedIn URL path conflicts with official-page attribution")
        return result

    result["action"] = "retain_url_only"
    result["reason"] = "explicit professional social-profile URL published on the official website"
    result["attribution"] = context
    result["canonical_field"] = f"{context}.public_profile_urls"

    if platform == "linkedin":
        if context == "person" and detected == "person":
            result["provider_route"] = "fullenrich_people_lookup"
            result["provider_input_priority"] = "exact_person_professional_network_url"
        elif context == "organisation" and detected == "organisation" and request.get("named_role_gap") is True:
            result["provider_route"] = "fullenrich_people_search"
            result["provider_input_priority"] = "exact_organisation_domain_plus_approved_target_role"
    return result


def select_provider_input(request: dict) -> dict:
    """Select a future FullEnrich input without authorising execution."""
    if request.get("known_contact_name") and request.get("person_professional_network_url"):
        return {
            "route": "fullenrich_people_lookup",
            "input_priority": "exact_person_professional_network_url",
            "input_value": request["person_professional_network_url"],
            "runtime_execution": False,
        }
    if request.get("known_contact_name") and request.get("exact_organisation_domain"):
        return {
            "route": "fullenrich_people_lookup",
            "input_priority": "person_name_plus_exact_organisation_domain",
            "input_value": {"person_name": request["known_contact_name"], "company_domain": request["exact_organisation_domain"]},
            "runtime_execution": False,
        }
    if request.get("named_role_gap") is True and request.get("exact_organisation_domain") and request.get("approved_target_roles"):
        return {
            "route": "fullenrich_people_search",
            "input_priority": "exact_organisation_domain_plus_approved_target_role",
            "input_value": {
                "company_domain": request["exact_organisation_domain"],
                "target_roles": request["approved_target_roles"],
                "limit": request.get("result_limit", 1),
            },
            "runtime_execution": False,
        }
    return {"route": "blocked_missing_approved_input", "input_priority": None, "runtime_execution": False}


# Backwards-compatible callable name for existing local wrappers.
def select_actor_input(request: dict) -> dict:
    return select_provider_input(request)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", help="JSON request or path to a JSON file")
    args = parser.parse_args()
    value = args.request
    try:
        request = json.loads(value)
    except json.JSONDecodeError:
        request = json.loads(open(value, encoding="utf-8").read())
    print(json.dumps(classify(request), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
