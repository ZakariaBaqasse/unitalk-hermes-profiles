#!/usr/bin/env python3
"""Build a review decision packet containing only evidenced website observations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_official_site_plan import load_json, sha256_json, utc_now, write_json_atomic


class PacketError(ValueError):
    pass


def _validate_evidence(item: dict[str, Any], source_urls: set[str], label: str) -> None:
    evidence = item.get("page_evidence")
    if not isinstance(evidence, list) or not evidence:
        raise PacketError(f"{label} lacks page evidence")
    for row in evidence:
        if not isinstance(row, dict) or row.get("page_url") not in source_urls:
            raise PacketError(f"{label} cites a page not present in the observed source pages")
        if not isinstance(row.get("evidence_text"), str) or not row["evidence_text"].strip():
            raise PacketError(f"{label} lacks visible evidence text")


def _validate_unique(items: list[dict[str, Any]], label: str) -> None:
    ids = [item.get("observation_id") for item in items]
    if any(not isinstance(value, str) or not value for value in ids) or len(ids) != len(set(ids)):
        raise PacketError(f"{label} observation IDs must be present and unique")


def build_packet(observations: dict[str, Any]) -> dict[str, Any]:
    if observations.get("schema_id") != "a2-official-site-observations" or observations.get("status") != "observed":
        raise PacketError("input is not a usable official-site observation artifact")
    expected_hash = sha256_json({key: value for key, value in observations.items() if key != "artifact_sha256"})
    if observations.get("artifact_sha256") != expected_hash:
        raise PacketError("observation artifact hash is missing or invalid")
    if observations.get("business_decisions_made") is not False:
        raise PacketError("observation artifact must not contain business decisions")
    run_id, company_id = observations.get("run_id"), observations.get("company_id")
    if not isinstance(run_id, str) or not run_id or not isinstance(company_id, str) or not company_id:
        raise PacketError("observations must identify the run and Company")
    source_pages = observations.get("source_pages")
    if not isinstance(source_pages, list) or not source_pages:
        raise PacketError("observations must retain source pages")
    source_urls = {row.get("resolved_url") for row in source_pages if isinstance(row, dict) and isinstance(row.get("resolved_url"), str)}
    if len(source_urls) != len(source_pages):
        raise PacketError("source pages must have unique resolved URLs")
    contacts = observations.get("contacts")
    socials = observations.get("social_links")
    people = observations.get("candidate_people")
    person_blocks = observations.get("person_evidence_blocks") or []
    coverage = observations.get("person_extraction_coverage") or {}
    if not all(isinstance(items, list) for items in (contacts, socials, people)):
        raise PacketError("observation collections must be arrays")
    if not isinstance(person_blocks, list) or any(not isinstance(item, dict) for item in person_blocks):
        raise PacketError("person evidence blocks must be an array of objects")
    _validate_unique(contacts, "contact")
    _validate_unique(socials, "social link")
    _validate_unique(people, "candidate person")
    all_ids: list[str] = []
    for label, items in (("contact", contacts), ("social link", socials), ("candidate person", people)):
        for item in items:
            if not isinstance(item, dict):
                raise PacketError(f"{label} observation must be an object")
            _validate_evidence(item, source_urls, f"{label} {item.get('observation_id')}")
            all_ids.append(item["observation_id"])
    if len(all_ids) != len(set(all_ids)):
        raise PacketError("observation IDs must be unique across the packet")
    for item in contacts:
        if item.get("contact_type") not in {"email", "phone"} or not isinstance(item.get("observed_value"), str) or not item["observed_value"]:
            raise PacketError("contact observation is malformed")
    for item in socials:
        if item.get("platform") not in {"facebook", "instagram", "youtube", "linkedin", "tiktok", "x"} or not isinstance(item.get("observed_url"), str):
            raise PacketError("social-link observation is malformed")
    for item in people:
        if not isinstance(item.get("observed_name"), str) or not item["observed_name"].strip():
            raise PacketError("candidate person name is missing")
        if item.get("observed_role") is not None and (not isinstance(item.get("observed_role"), str) or not item["observed_role"].strip()):
            raise PacketError("candidate person role must be null or a non-empty exact source value")
    block_ids: set[str] = set()
    page_hashes = {row.get("resolved_url"): row.get("content_sha256") for row in source_pages}
    for block in person_blocks:
        block_id, page_url, text = block.get("block_id"), block.get("page_url"), block.get("text")
        if not isinstance(block_id, str) or not block_id or block_id in block_ids:
            raise PacketError("person evidence block IDs must be present and unique")
        block_ids.add(block_id)
        if page_url not in source_urls or block.get("page_content_sha256") != page_hashes.get(page_url):
            raise PacketError(f"person evidence block {block_id} has invalid page provenance")
        if not isinstance(text, str) or not 20 <= len(text) <= 2000:
            raise PacketError(f"person evidence block {block_id} has invalid bounded text")
        if block.get("untrusted_source_content") is not True:
            raise PacketError(f"person evidence block {block_id} must be marked untrusted")
    packet_status = "ready_for_person_observation_proposals" if person_blocks and coverage.get("llm_observation_proposals_validated") is not True else "ready_for_decision"
    packet: dict[str, Any] = {
        "schema_id": "a2-website-decision-packet",
        "schema_version": "0.1.0",
        "created_at": utc_now(),
        "status": packet_status,
        "run_id": run_id,
        "company_id": company_id,
        "company": observations.get("company"),
        "official_url": observations.get("official_url"),
        "source_id": "prospect_official_website",
        "observations_sha256": observations.get("artifact_sha256"),
        "source_pages": source_pages,
        "contacts": contacts,
        "social_links": socials,
        "candidate_people": people,
        "person_evidence_blocks": person_blocks,
        "person_extraction_coverage": coverage,
        "decision_contract": {
            "retained_people_maximum": 2,
            "candidate_people_are_eligible_regardless_of_observed_role": True,
            "person_name_and_role_must_match_the_observation_exactly": True,
            "retained_contacts_require_attribution_type": ["Company", "Person"],
            "person_contact_requires_retained_person_observation_id": True,
            "decisions_may_not_introduce_unobserved_values": True,
            "llm_person_proposals_require_exact_block_spans": True,
            "all_person_evidence_blocks_must_be_reviewed_before_no_target": True,
        },
        "external_calls": 0,
        "external_actions": 0,
        "errors": [],
    }
    packet["artifact_sha256"] = sha256_json({key: value for key, value in packet.items() if key != "artifact_sha256"})
    return packet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build_packet(load_json(args.observations))
        code = 0
    except Exception as exc:
        result = {"schema_id": "a2-website-decision-packet", "status": "invalid", "errors": [str(exc)], "external_calls": 0, "external_actions": 0}
        code = 1
    write_json_atomic(args.output, result)
    print(json.dumps({"status": result["status"], "output": str(args.output), "errors": result.get("errors", [])}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
