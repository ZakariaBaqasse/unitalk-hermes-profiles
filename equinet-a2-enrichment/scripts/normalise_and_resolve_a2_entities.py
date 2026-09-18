#!/usr/bin/env python3
"""Deterministically normalise and compare A2 person or organisation entities."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

VERSION = "0.1.0"
BUSINESS_SUFFIXES = {"inc", "incorporated", "llc", "ltd", "limited", "corp", "corporation", "company", "co"}


def normalise_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = unicodedata.normalize("NFKC", value).casefold().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split()) or None


def normalise_name(value: str | None, entity_type: str) -> str | None:
    value = normalise_text(value)
    if value is None or entity_type != "organisation":
        return value
    parts = value.split()
    while parts and parts[-1] in BUSINESS_SUFFIXES:
        parts.pop()
    return " ".join(parts) or value


def normalise_domain(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    if "://" not in candidate:
        candidate = "https://" + candidate
    parsed = urlsplit(candidate)
    host = (parsed.hostname or "").casefold().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    return host or None


def normalise_email(value: str | None) -> str | None:
    return value.strip().casefold() if value and "@" in value else None


def normalise_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    return digits if len(digits) >= 7 else None


def normalise_profile_urls(values: list[str] | None) -> list[str]:
    result = []
    for value in values or []:
        try:
            parsed = urlsplit(value.strip())
            if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
                continue
            host = parsed.hostname.casefold().rstrip(".")
            if host.startswith("www."):
                host = host[4:]
            normalised = f"https://{host}{parsed.path.rstrip('/') or '/'}"
            if normalised not in result:
                result.append(normalised)
        except Exception:
            continue
    return sorted(result)


def normalise_entity(entity: dict) -> dict:
    entity_type = entity.get("entity_type")
    if entity_type not in {"person", "organisation"}:
        raise ValueError("entity_type must be person or organisation")
    return {
        "entity_id": entity.get("entity_id"),
        "entity_type": entity_type,
        "display_name": entity.get("display_name"),
        "normalised_name": normalise_name(entity.get("display_name"), entity_type),
        "domain": normalise_domain(entity.get("domain") or entity.get("website")),
        "business_email": normalise_email(entity.get("business_email")),
        "business_phone": normalise_phone(entity.get("business_phone")),
        "organisation_name": normalise_name(entity.get("organisation_name"), "organisation"),
        "public_profile_urls": normalise_profile_urls(entity.get("public_profile_urls")),
    }


def compare(source: dict, candidate: dict) -> dict:
    left = normalise_entity(source)
    right = normalise_entity(candidate)
    if left["entity_type"] != right["entity_type"]:
        return {"status": "conflict", "signals": [], "reason": "entity types differ"}
    signals = []
    for key in ["normalised_name", "domain", "business_email", "business_phone", "organisation_name"]:
        if left.get(key) and right.get(key):
            signals.append({"signal": key, "match": left[key] == right[key]})
    shared_profiles = sorted(set(left["public_profile_urls"]) & set(right["public_profile_urls"]))
    if shared_profiles:
        signals.append({"signal": "public_profile_url", "match": True, "values": shared_profiles})
    positive = [x for x in signals if x["match"]]
    negative = [x for x in signals if not x["match"]]
    strong_positive = [x for x in positive if x["signal"] in {"domain", "business_email", "business_phone", "public_profile_url"}]
    name_positive = any(x["signal"] == "normalised_name" and x["match"] for x in signals)
    if strong_positive and name_positive and not negative:
        status, reason = "confirmed_match", "matching name and strong identifier with no conflicting compared field"
    elif len(strong_positive) >= 2 and not negative:
        status, reason = "confirmed_match", "multiple strong identifiers match with no conflicting compared field"
    elif positive and negative:
        status, reason = "conflict", "matching and conflicting identity signals coexist"
    elif name_positive or strong_positive:
        status, reason = "possible_match", "one identity basis matches but confirmation is insufficient"
    elif len(negative) >= 2:
        status, reason = "no_match", "multiple compared identity fields differ"
    else:
        status, reason = "unavailable", "insufficient comparable identity evidence"
    return {"status": status, "signals": signals, "reason": reason}


def resolve(request: dict) -> dict:
    source = request.get("source_entity")
    candidates = request.get("candidate_matches", [])
    if not isinstance(source, dict) or not isinstance(candidates, list):
        raise ValueError("source_entity must be an object and candidate_matches must be an array")
    source_normalised = normalise_entity(source)
    results = []
    for candidate in candidates:
        comparison = compare(source, candidate)
        results.append({"candidate_id": candidate.get("entity_id"), **comparison})
    confirmed = [x for x in results if x["status"] == "confirmed_match"]
    conflicts = [x for x in results if x["status"] == "conflict"]
    possible = [x for x in results if x["status"] == "possible_match"]
    if conflicts or len(confirmed) > 1:
        overall = "conflict"
    elif len(confirmed) == 1:
        overall = "resolved"
    elif possible:
        overall = "possible_match"
    elif results and all(x["status"] == "no_match" for x in results):
        overall = "resolved"
    else:
        overall = "unresolved"
    return {
        "command": "a2-normalise-resolve-entities",
        "version": VERSION,
        "source_entity": source_normalised,
        "candidate_results": results,
        "identity_resolution_status": overall,
        "human_review_required": overall in {"possible_match", "conflict", "unresolved"},
        "canonical_record_mutated": False,
        "external_actions": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = resolve(json.loads(args.request.read_text(encoding="utf-8")))
        rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except Exception as exc:
        print(json.dumps({"valid": False, "command": "a2-normalise-resolve-entities", "error": str(exc), "external_actions": 0}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
