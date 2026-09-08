#!/usr/bin/env python3
"""Resolve an explicit Equinet discovery country/region/city to canonical codes.

The user must supply all three names. This script never infers a country or
region from a city. Optional supplied codes are validated for consistency.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configurations/geography/location-resolution-v1.json"


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def token(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", clean(value))
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).casefold()


def slug(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", clean(value))
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()))


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("status") != "approved_for_production":
        raise ValueError("Location mapping is not approved for production")
    return data


def resolve(
    config: dict[str, Any],
    country: str,
    region: str,
    city: str,
    supplied_country_code: str | None = None,
    supplied_region_code: str | None = None,
) -> dict[str, Any]:
    country = clean(country)
    region = clean(region)
    city = clean(city)
    if not country or not region or not city:
        missing = [name for name, value in (("country", country), ("region", region), ("city", city)) if not value]
        raise ValueError("Missing required location field(s): " + ", ".join(missing))

    country_matches: list[tuple[str, dict[str, Any]]] = []
    for code, entry in config["countries"].items():
        aliases = [entry.get("name", ""), *entry.get("aliases", [])]
        if token(country) in {token(alias) for alias in aliases}:
            country_matches.append((code, entry))
    if len(country_matches) != 1:
        raise ValueError(f"Country is unsupported or ambiguous: {country!r}")
    country_code, country_entry = country_matches[0]

    if supplied_country_code and clean(supplied_country_code).upper() != country_code:
        raise ValueError(
            f"Supplied country_code {supplied_country_code!r} conflicts with country {country_entry['name']!r} ({country_code})"
        )

    region_matches: list[tuple[str, str]] = []
    for code, aliases in country_entry["subdivisions"].items():
        if token(region) in {token(alias) for alias in aliases}:
            canonical_name = next((alias for alias in aliases if token(alias) != token(code) and not token(alias).startswith(token(country_code))), aliases[-1])
            region_matches.append((code, canonical_name))
    if len(region_matches) != 1:
        raise ValueError(
            f"Region/state is unsupported or ambiguous for {country_entry['name']}: {region!r}"
        )
    region_code, region_name = region_matches[0]

    normalized_supplied_region_code = clean(supplied_region_code).upper()
    if normalized_supplied_region_code.startswith(country_code + "-"):
        normalized_supplied_region_code = normalized_supplied_region_code.split("-", 1)[1]
    if supplied_region_code and normalized_supplied_region_code != region_code:
        raise ValueError(
            f"Supplied region_code {supplied_region_code!r} conflicts with region {region_name!r} ({region_code})"
        )

    return {
        "city": city,
        "city_slug": slug(city),
        "city_aliases": [],
        "region": region_name,
        "region_code": region_code,
        "region_slug": slug(region_name),
        "state": region_name,
        "state_code": region_code,
        "country": country_entry["name"],
        "country_code": country_code,
        "country_slug": slug(country_entry["name"]),
        "location_display": f"{city}, {region_name}, {country_entry['name']}",
        "location_key": f"{country_code}|{region_code}|{slug(city)}",
        "mapping_version": config["version"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--country", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--city", required=True)
    parser.add_argument("--country-code")
    parser.add_argument("--region-code")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    try:
        result = resolve(
            load_config(args.config),
            args.country,
            args.region,
            args.city,
            args.country_code,
            args.region_code,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "blocked", "error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "resolved", "location": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
