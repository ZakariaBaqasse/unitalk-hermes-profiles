#!/usr/bin/env python3
"""Validate LLM person proposals against bounded official-site evidence blocks."""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any

from build_official_site_plan import load_json, sha256_json, utc_now, write_json_atomic
from extract_official_site_observations import FULL_NAME_PAIR_RE, SHARED_SURNAME_RE, observation_id

ALLOWED_DERIVATIONS = {"exact", "shared_surname_split", "multiple_full_names"}
ALLOWED_RELATIONSHIPS = {"current", "ambiguous", "unrelated"}


class ProposalError(ValueError):
    pass


def _allowed_names(mention: str, derivation: str) -> set[str]:
    if derivation == "exact":
        return {mention.strip()}
    if derivation == "shared_surname_split":
        names: set[str] = set()
        for match in SHARED_SURNAME_RE.finditer(mention):
            names.add(f"{match.group('first1')} {match.group('last')}")
            names.add(f"{match.group('first2')} {match.group('last')}")
        return names
    names = set()
    for match in FULL_NAME_PAIR_RE.finditer(mention):
        names.update({match.group("name1"), match.group("name2")})
    return names


def validate_proposals(packet: dict[str, Any], proposals: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if packet.get("schema_id") != "a2-website-decision-packet" or packet.get("status") not in {"ready_for_person_observation_proposals", "ready_for_decision"}:
        raise ProposalError("packet is not ready for person-observation proposal validation")
    expected_hash = sha256_json({key: value for key, value in packet.items() if key != "artifact_sha256"})
    if packet.get("artifact_sha256") != expected_hash:
        raise ProposalError("decision packet hash is missing or invalid")
    for key in ("run_id", "company_id"):
        if proposals.get(key) != packet.get(key):
            errors.append(f"proposal {key} must match the packet exactly")
    blocks = packet.get("person_evidence_blocks") or []
    block_index = {row.get("block_id"): row for row in blocks if isinstance(row, dict) and isinstance(row.get("block_id"), str)}
    if len(block_index) != len(blocks):
        raise ProposalError("packet person evidence blocks are invalid")
    reviewed = proposals.get("reviewed_block_ids")
    if not isinstance(reviewed, list) or any(not isinstance(value, str) for value in reviewed):
        errors.append("reviewed_block_ids must be an array of block IDs")
        reviewed = []
    if set(reviewed) != set(block_index) or len(reviewed) != len(set(reviewed)):
        errors.append("all and only packet person evidence blocks must be reviewed exactly once")
    rows = proposals.get("proposals")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        errors.append("proposals must be an array of objects")
        rows = []
    if len(rows) > 20:
        errors.append("at most twenty evidence-backed person proposals may be submitted")
    accepted: list[dict[str, Any]] = []
    ignored: list[dict[str, Any]] = []
    proposal_ids: set[str] = set()
    for index, row in enumerate(rows):
        label = f"proposal[{index}]"
        proposal_id = row.get("proposal_id")
        if not isinstance(proposal_id, str) or not proposal_id or proposal_id in proposal_ids:
            errors.append(f"{label}: proposal_id must be present and unique")
            continue
        proposal_ids.add(proposal_id)
        block = block_index.get(row.get("block_id"))
        if not block:
            errors.append(f"{label}: unknown block_id")
            continue
        text = block.get("text") or ""
        mention = row.get("source_mention")
        name = row.get("person_name")
        derivation = row.get("derivation")
        relationship = row.get("relationship_to_company")
        relationship_evidence = row.get("company_relationship_evidence")
        role = row.get("role_text")
        if not isinstance(mention, str) or not mention.strip() or mention not in text:
            errors.append(f"{label}: source_mention must be an exact substring of the cited block")
            continue
        if not isinstance(name, str) or not 2 <= len(name.strip()) <= 100:
            errors.append(f"{label}: person_name is invalid")
            continue
        if derivation not in ALLOWED_DERIVATIONS:
            errors.append(f"{label}: unsupported name derivation")
            continue
        if name.strip() not in _allowed_names(mention, derivation):
            errors.append(f"{label}: person_name is not supported by source_mention and derivation")
            continue
        if relationship not in ALLOWED_RELATIONSHIPS:
            errors.append(f"{label}: relationship_to_company is invalid")
            continue
        if not isinstance(relationship_evidence, str) or not relationship_evidence.strip() or relationship_evidence not in text:
            errors.append(f"{label}: company_relationship_evidence must be an exact substring of the cited block")
            continue
        if role is not None and (not isinstance(role, str) or not role.strip() or role not in text):
            errors.append(f"{label}: role_text must be null or an exact substring of the cited block")
            continue
        evidence = {
            "page_index": block.get("page_index"),
            "page_url": block.get("page_url"),
            "page_title": block.get("page_title"),
            "evidence_text": relationship_evidence,
            "page_content_sha256": block.get("page_content_sha256"),
            "source_block_id": block.get("block_id"),
        }
        validated = {
            "proposal_id": proposal_id,
            "block_id": block.get("block_id"),
            "person_name": name.strip(),
            "source_mention": mention,
            "derivation": derivation,
            "role_text": role.strip() if isinstance(role, str) else None,
            "relationship_to_company": relationship,
            "page_evidence": [evidence],
        }
        if relationship == "current":
            accepted.append(validated)
        else:
            ignored.append(validated)
    output = copy.deepcopy(packet)
    if errors:
        output.update({"status": "invalid", "proposal_errors": errors, "external_calls": 0, "external_actions": 0})
    else:
        people_by_name = {row["observed_name"].casefold(): copy.deepcopy(row) for row in output.get("candidate_people", [])}
        for row in accepted:
            key = row["person_name"].casefold()
            existing = people_by_name.get(key)
            if existing:
                existing.setdefault("page_evidence", []).extend(item for item in row["page_evidence"] if item not in existing["page_evidence"])
                existing.setdefault("source_mentions", [])
                if row["source_mention"] not in existing["source_mentions"]:
                    existing["source_mentions"].append(row["source_mention"])
                existing.setdefault("llm_proposal_ids", []).append(row["proposal_id"])
                if not existing.get("observed_role") and row.get("role_text"):
                    existing["observed_role"] = row["role_text"]
            else:
                value = {"name": row["person_name"], "role": row.get("role_text"), "proposal_id": row["proposal_id"]}
                people_by_name[key] = {
                    "observation_id": observation_id("person", value, row["page_evidence"][0]["page_url"]),
                    "observation_type": "candidate_person",
                    "observed_name": row["person_name"],
                    "observed_role": row.get("role_text"),
                    "observed_role_candidates": [row["role_text"]] if row.get("role_text") else [],
                    "source_mentions": [row["source_mention"]],
                    "extraction_method": "llm_exact_span_validated",
                    "source_block_id": row["block_id"],
                    "llm_proposal_ids": [row["proposal_id"]],
                    "page_evidence": row["page_evidence"],
                }
        output["candidate_people"] = sorted(people_by_name.values(), key=lambda row: row["observation_id"])
        output["status"] = "ready_for_decision"
        output["person_extraction_coverage"] = {
            **(output.get("person_extraction_coverage") or {}),
            "status": "complete",
            "llm_observation_proposals_validated": True,
            "reviewed_block_count": len(reviewed),
            "accepted_proposal_count": len(accepted),
            "ignored_proposal_count": len(ignored),
        }
        output["person_observation_proposal_validation"] = {
            "validated_at": utc_now(),
            "proposal_input_sha256": sha256_json(proposals),
            "accepted": accepted,
            "ignored": ignored,
            "errors": [],
        }
        output["proposal_errors"] = []
    output["artifact_sha256"] = sha256_json({key: value for key, value in output.items() if key != "artifact_sha256"})
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("proposals", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate_proposals(load_json(args.packet), load_json(args.proposals))
        code = 0 if result.get("status") == "ready_for_decision" else 1
    except Exception as exc:
        result = {"schema_id": "a2-website-decision-packet", "status": "invalid", "proposal_errors": [str(exc)], "external_calls": 0, "external_actions": 0}
        code = 1
    write_json_atomic(args.output, result)
    print(json.dumps({"status": result.get("status"), "candidate_people": len(result.get("candidate_people", [])), "errors": result.get("proposal_errors", []), "output": str(args.output)}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
