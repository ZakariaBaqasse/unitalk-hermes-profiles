#!/usr/bin/env python3
"""Validate official-site decisions against exact, evidenced packet observations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_official_site_plan import load_json, sha256_json, utc_now, write_json_atomic


class DecisionError(ValueError):
    pass


def _decision_rows(decisions: dict[str, Any], primary: str, alias: str) -> list[dict[str, Any]]:
    rows = decisions.get(primary)
    if rows is None:
        rows = decisions.get(alias, [])
    if not isinstance(rows, list) or any(not isinstance(item, dict) for item in rows):
        raise DecisionError(f"{primary} decisions must be an array of objects")
    return rows


def _index(packet: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    rows = packet.get(key)
    if not isinstance(rows, list):
        raise DecisionError(f"packet {key} must be an array")
    result: dict[str, dict[str, Any]] = {}
    for item in rows:
        if not isinstance(item, dict) or not isinstance(item.get("observation_id"), str) or item["observation_id"] in result:
            raise DecisionError(f"packet {key} contains invalid observation IDs")
        evidence = item.get("page_evidence")
        if not isinstance(evidence, list) or not evidence:
            raise DecisionError(f"packet {key} contains an unevidenced observation")
        result[item["observation_id"]] = item
    return result


def validate_decisions(packet: dict[str, Any], decisions: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if packet.get("schema_id") != "a2-website-decision-packet" or packet.get("status") != "ready_for_decision":
        raise DecisionError("packet is not ready for website decisions")
    expected_hash = sha256_json({key: value for key, value in packet.items() if key != "artifact_sha256"})
    if packet.get("artifact_sha256") != expected_hash:
        raise DecisionError("decision packet hash is missing or invalid")
    for key in ("run_id", "company_id"):
        if decisions.get(key) != packet.get(key):
            errors.append(f"decision {key} must match the packet exactly")
    people_index = _index(packet, "candidate_people")
    contacts_index = _index(packet, "contacts")
    socials_index = _index(packet, "social_links")
    people_rows = _decision_rows(decisions, "people", "person_decisions")
    contact_rows = _decision_rows(decisions, "contacts", "contact_decisions")
    social_rows = _decision_rows(decisions, "social_links", "social_decisions")
    all_decision_ids: list[str] = []
    retained_people: list[dict[str, Any]] = []
    retained_person_ids: set[str] = set()
    company=packet.get("company") if isinstance(packet.get("company"),dict) else {}
    existing_ids={x.get("twenty_person_id") or x.get("id") for x in company.get("linked_people",[]) if isinstance(x,dict)}
    for row in people_rows:
        oid = row.get("observation_id")
        all_decision_ids.append(oid)
        source = people_index.get(oid)
        if not source:
            errors.append(f"unknown or unobserved candidate person: {oid}")
            continue
        if not isinstance(row.get("retain"), bool):
            errors.append(f"{oid}: retain must be boolean")
            continue
        if row.get("name") != source.get("observed_name"):
            errors.append(f"{oid}: person name must preserve the exact observed name")
        if row.get("role") != source.get("observed_role"):
            errors.append(f"{oid}: person role must preserve the exact observed role")
        identity=row.get("identity_status") or "VERIFIED"
        company_match=row.get("company_match_status") or "CONFIRMED"
        relationship=row.get("role_status") or "CURRENT_AT_COMPANY"
        if identity not in {"VERIFIED","AMBIGUOUS","CONFLICT","NOT_FOUND"}:errors.append(f"{oid}: invalid identity_status")
        if company_match not in {"CONFIRMED","PROBABLE","AMBIGUOUS","MISMATCH"}:errors.append(f"{oid}: invalid company_match_status")
        if relationship not in {"CURRENT_AT_COMPANY","NOT_CURRENT_AT_COMPANY","UNVERIFIED"}:errors.append(f"{oid}: invalid role_status")
        if row.get("retain") and not (identity=="VERIFIED" and company_match=="CONFIRMED" and relationship=="CURRENT_AT_COMPANY"):errors.append(f"{oid}: retained website Person must be verified and current at the Company")
        priority=row.get("role_priority") or "UNKNOWN"
        if priority not in {"PRIMARY","SECONDARY","REVIEW_ONLY","EXCLUDED","UNKNOWN"}:
            errors.append(f"{oid}: invalid role_priority")
        comparison=row.get("provider_comparison_name") or source["observed_name"]
        if not isinstance(comparison,str) or not comparison.strip():errors.append(f"{oid}: provider_comparison_name must be non-empty")
        if comparison != source["observed_name"] and not isinstance(row.get("name_normalization_reason"),str):errors.append(f"{oid}: normalized provider name requires a reason")
        duplicate=row.get("duplicate_of_twenty_person_id")
        if duplicate is not None and duplicate not in existing_ids:errors.append(f"{oid}: duplicate_of_twenty_person_id is not linked to the Company")
        if row["retain"]:
            retained_person_ids.add(oid)
            retained_people.append({
                "observation_id": oid,
                "name": source["observed_name"],
                "provider_comparison_name": comparison,
                "name_normalization_reason": row.get("name_normalization_reason"),
                "role": source.get("observed_role"),
                "role_priority": priority,
                "identity_status": identity,
                "company_match_status": company_match,
                "role_status": relationship,
                "duplicate_of_twenty_person_id": row.get("duplicate_of_twenty_person_id"),
                "page_evidence": source["page_evidence"],
            })
    if len(retained_people) > 2:
        errors.append("at most two website candidate people may be retained")
    retained_contacts: list[dict[str, Any]] = []
    for row in contact_rows:
        oid = row.get("observation_id")
        all_decision_ids.append(oid)
        source = contacts_index.get(oid)
        if not source:
            errors.append(f"unknown or unobserved contact: {oid}")
            continue
        if not isinstance(row.get("retain"), bool):
            errors.append(f"{oid}: retain must be boolean")
            continue
        if "value" in row and row.get("value") != source.get("observed_value"):
            errors.append(f"{oid}: contact value must preserve the exact observation")
        if not row["retain"]:
            continue
        attribution = row.get("attribution")
        if not isinstance(attribution, dict):
            errors.append(f"{oid}: retained contact requires attribution")
            continue
        entity_type = attribution.get("entity_type")
        entity_id = attribution.get("entity_id")
        if entity_type == "Company":
            if entity_id not in {None, packet.get("company_id")}:
                errors.append(f"{oid}: Company contact attribution must identify the packet Company")
                continue
            attributed_id = packet.get("company_id")
        elif entity_type == "Person":
            person_id = attribution.get("person_observation_id") or entity_id
            if person_id not in people_index:
                errors.append(f"{oid}: Person contact attribution must reference an observed person")
                continue
            if person_id not in retained_person_ids:
                errors.append(f"{oid}: Person contact attribution must reference a retained person")
                continue
            attributed_id = person_id
        else:
            errors.append(f"{oid}: contact attribution entity_type must be Company or Person")
            continue
        retained_contacts.append({
            "observation_id": oid,
            "contact_type": source["contact_type"],
            "value": source["observed_value"],
            "attribution": {"entity_type": entity_type, "entity_id": attributed_id},
            "page_evidence": source["page_evidence"],
        })
    retained_socials: list[dict[str, Any]] = []
    for row in social_rows:
        oid = row.get("observation_id")
        all_decision_ids.append(oid)
        source = socials_index.get(oid)
        if not source:
            errors.append(f"unknown or unobserved social link: {oid}")
            continue
        if not isinstance(row.get("retain"), bool):
            errors.append(f"{oid}: retain must be boolean")
            continue
        if "url" in row and row.get("url") != source.get("observed_url"):
            errors.append(f"{oid}: social URL must preserve the exact observation")
        if row["retain"]:
            retained_socials.append({
                "observation_id": oid,
                "platform": source["platform"],
                "url": source["observed_url"],
                "page_evidence": source["page_evidence"],
            })
    string_ids = [value for value in all_decision_ids if isinstance(value, str)]
    if len(string_ids) != len(all_decision_ids) or len(string_ids) != len(set(string_ids)):
        errors.append("decision observation IDs must be present and unique across all decision arrays")
    result: dict[str, Any] = {
        "schema_id": "a2-validated-website-decisions",
        "schema_version": "0.1.0",
        "created_at": utc_now(),
        "status": "valid" if not errors else "invalid",
        "run_id": packet.get("run_id"),
        "company_id": packet.get("company_id"),
        "packet_sha256": packet.get("artifact_sha256"),
        "retained_people": retained_people if not errors else [],
        "retained_contacts": retained_contacts if not errors else [],
        "retained_social_links": retained_socials if not errors else [],
        "retained_people_count": len(retained_people) if not errors else 0,
        "person_extraction_coverage": packet.get("person_extraction_coverage"),
        "website_no_target_coverage_complete": not errors and (packet.get("person_extraction_coverage") or {}).get("status") in {"complete", "complete_no_relevant_blocks"},
        "role_based_eligibility_filter_applied": False,
        "external_calls": 0,
        "external_actions": 0,
        "errors": errors,
    }
    result["artifact_sha256"] = sha256_json({key: value for key, value in result.items() if key != "artifact_sha256"})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("decisions", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate_decisions(load_json(args.packet), load_json(args.decisions))
        code = 0 if result["status"] == "valid" else 1
    except Exception as exc:
        result = {"schema_id": "a2-validated-website-decisions", "status": "invalid", "errors": [str(exc)], "external_calls": 0, "external_actions": 0}
        code = 1
    write_json_atomic(args.output, result)
    print(json.dumps({"status": result["status"], "retained_people": result.get("retained_people_count", 0), "errors": result.get("errors", []), "output": str(args.output)}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
