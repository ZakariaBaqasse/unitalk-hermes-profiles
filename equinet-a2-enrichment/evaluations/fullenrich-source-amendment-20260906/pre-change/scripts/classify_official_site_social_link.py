#!/usr/bin/env python3
"""Classify a social-profile URL explicitly linked by an official site.

This utility never fetches or opens the social URL. It only normalises the
published URL, assigns a supported platform and decides the canonical field
or review route under SOC-1 through SOC-8.
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
        "actor_route": None,
        "actor_input_priority": None,
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

    if platform == "linkedin" and request.get("named_role_gap") is True:
        if context == "organisation" and detected == "organisation":
            result["actor_route"] = "harvestapi/linkedin-profile-search"
            result["actor_input_priority"] = "exact_linkedin_company_url"
        elif context == "person" and detected == "person":
            result["actor_route"] = "manual_review_or_separately_approved_profile_scraper"
    return result


def select_actor_input(request: dict) -> dict:
    """Select a future Actor input without authorising runtime execution."""
    if request.get("named_role_gap") is not True:
        return {"route": "not_applicable", "input_priority": None, "runtime_execution": False}
    linkedin_company_url = request.get("linkedin_company_url")
    if linkedin_company_url:
        classified = classify({
            "source": "prospect_official_website",
            "explicitly_linked": request.get("explicitly_linked") is True,
            "url": linkedin_company_url,
            "page_context": "organisation",
            "named_role_gap": True,
        })
        if classified["action"] == "retain_url_only" and classified["actor_route"] == "harvestapi/linkedin-profile-search":
            return {
                "route": "harvestapi/linkedin-profile-search",
                "input_priority": "exact_linkedin_company_url",
                "input_value": classified["normalised_url"],
                "runtime_execution": False,
            }
    if request.get("verified_company_name") and request.get("target_role"):
        return {
            "route": "harvestapi/linkedin-profile-search",
            "input_priority": "verified_company_name_plus_target_role",
            "input_value": {"company_name": request["verified_company_name"], "target_role": request["target_role"]},
            "runtime_execution": False,
        }
    return {"route": "blocked_missing_approved_input", "input_priority": None, "runtime_execution": False}


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
