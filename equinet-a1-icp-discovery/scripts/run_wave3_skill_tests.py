#!/usr/bin/env python3
"""Static, deterministic and cross-format tests for Equinet A1 Wave 3 skills."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[1]
REVIEW_SKILL = PROFILE / "skills" / "ranked-prospect-review-package"
EXPORT_SKILL = PROFILE / "skills" / "prospect-export"
sys.path.insert(0, str(REVIEW_SKILL / "scripts"))
sys.path.insert(0, str(EXPORT_SKILL / "scripts"))
sys.path.insert(0, str(PROFILE / "skills" / "a1-prospect-data-contract" / "scripts"))
from build_review_package import build  # noqa: E402
from export_review_package import export  # noqa: E402
from validate_candidate import cross_reference_errors  # noqa: E402


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS: {label}")


def renamed_james_bundle(bundle: dict, candidate_id: str, suffix: str, keep_domain: bool = False) -> dict:
    value = copy.deepcopy(bundle)
    value["candidate_id"] = candidate_id
    value["record_kind"] = "synthetic_test"
    value["model"] = None
    value["tools_used"] = []
    seed = value["research_seed"]
    seed["run_id"] = f"RUN-{suffix}"
    seed["seed_id"] = f"SEED-{suffix}"
    seed["identity_hint"]["display_name"] = f"Synthetic {suffix} Farrier"
    seed["identity_hint"]["person_name"] = f"Synthetic {suffix}"
    seed["identity_hint"]["organisation_name"] = f"Synthetic {suffix} Farrier Services"
    if not keep_domain:
        seed["website"] = f"https://{suffix.lower()}.example.com"
        for evidence in seed["source_candidates"]:
            path = Path(evidence["source_url"]).name
            evidence["source_url"] = f"https://{suffix.lower()}.example.com/{path}" if path else f"https://{suffix.lower()}.example.com"
    for contact in seed.get("public_contacts", []):
        if contact["contact_type"] == "email":
            contact["value"] = f"{suffix.lower()}@example.com"
        elif contact["contact_type"] == "phone":
            contact["value"] = f"+1-555-{len(suffix):03d}-0000"
    return value


def owner_bundle() -> dict:
    source = load(PROFILE / "skills" / "icp-scoring-and-rationale" / "test_data" / "synthetic_horse_owner_unknown_count.json")
    scoring = load(PROFILE / "evaluations" / "wave2" / "validation-simplified" / "corroboration" / "scoring-owner-unknown-count.json")
    id_map = {f"ev-{index:03d}": f"EV-OWNER-{index:03d}" for index in range(1, 9)}
    categories = {
        "horse_owner.commercial_operation": "fit",
        "horse_owner.more_than_three_horses": "fit",
        "horse_owner.purchasing_influence": "priority",
        "horse_owner.product_fit": "fit",
        "horse_owner.performance_discipline": "priority",
        "horse_owner.breeding_activity": "priority",
        "horse_owner.professional_network": "priority",
        "horse_owner.high_equine_activity_location": "priority",
        "horse_owner.buying_signal": "priority",
    }
    criteria = []
    for criterion in source["qualification"]["criteria"]:
        item = copy.deepcopy(criterion)
        item["criterion_label"] = item["criterion_id"].split(".", 1)[1].replace("_", " ").title()
        item["category"] = categories[item["criterion_id"]]
        item["evidence_ids"] = [id_map[evidence_id] for evidence_id in item["evidence_ids"]]
        criteria.append(item)
    scoring = copy.deepcopy(scoring)
    for component in scoring["scoring"]["components"]:
        component["evidence_ids"] = [id_map[evidence_id] for evidence_id in component["evidence_ids"]]
    for component in scoring["explanation"]["confirmed_criteria"]:
        component["evidence_ids"] = [id_map[evidence_id] for evidence_id in component["evidence_ids"]]
    research_evidence = []
    for entry in source["source_evidence"]:
        research_evidence.append({
            "evidence_id": id_map[entry["evidence_id"]],
            "source_url": entry["source_url"],
            "source_name": "Synthetic Horse Farm",
            "source_type": "business_website",
            "retrieved_at": entry["retrieval_date"] + "T00:00:00Z",
            "evidence_excerpt": entry["claim"],
            "fact_or_inference": entry["classification"],
        })
    return {
        "candidate_id": "A1-OWNER-UNKNOWN-001",
        "record_kind": "synthetic_test",
        "research_seed": {
            "run_id": "RUN-OWNER-UNKNOWN-001",
            "seed_id": "SEED-OWNER-UNKNOWN-001",
            "discovered_at": "2026-08-14T00:00:00Z",
            "identity_hint": {
                "display_name": "Synthetic Horse Farm / Jane Doe",
                "person_name": "Jane Doe",
                "organisation_name": "Synthetic Horse Farm LLC",
                "role_title": "Farm Manager",
            },
            "website": "https://example.com/synthetic-farm",
            "location_hint": {
                "country_code": "US", "state_region": "KY", "city": "Lexington",
                "postal_code": None, "public_address": None,
            },
            "public_contacts": [],
            "source_candidates": research_evidence,
            "missing_information": ["Horse count is not published."],
            "conflicts": [],
        },
        "classification_decision": {
            "segment": "horse_owner", "prospect_type": "farm", "identity_type": "person_and_organisation",
        },
        "qualification_package": {
            "qualification": {
                "icp_config_version": "1.0.0", "criteria": criteria, "minimum_data_status": "pass",
                "missing_minimum_fields": [], "exclusion_status": "eligible", "exclusion_reasons": [],
            }
        },
        "confidence_package": {
            "assessment": {"gates": {"unresolved_identity_conflict": {"value": False}, "critical_evidence_conflict": {"value": False}}},
            "confidence": {
                "score": 92, "level": "high", "method_version": "evidence-confidence-1.0.0",
                "reasons": ["Synthetic evidence is traceable for the controlled test."],
                "limitations": ["Horse count remains unknown."],
            },
        },
        "scoring_package": scoring,
        "source_policy_status": "approved",
        "access_method": "client_provided_file",
        "model": None,
        "tools_used": [],
        "provided_exclusion_file_status": "unavailable",
    }


def reject_bundle() -> dict:
    exclusion_input = load(PROFILE / "evaluations" / "wave2" / "iteration-1" / "scoring-farrier-exclusion" / "artifacts" / "candidate-input.json")
    exclusion_scoring = load(PROFILE / "evaluations" / "wave2" / "validation-simplified" / "scoring-farrier-exclusion" / "scoring-package.json")
    return {
        "candidate_id": "A1-FARRIER-REJECT-001",
        "record_kind": "synthetic_test",
        "research_seed": {
            "run_id": "RUN-FARRIER-REJECT-001",
            "seed_id": "SEED-FARRIER-REJECT-001",
            "discovered_at": "2026-08-14T00:00:00Z",
            "identity_hint": {
                "display_name": "Synthetic Unverified Farrier",
                "person_name": "Synthetic Unverified Farrier",
                "organisation_name": None,
            },
            "website": "https://example.com/unverified-farrier",
            "location_hint": {
                "country_code": "US", "state_region": "KY", "city": "Lexington",
                "postal_code": None, "public_address": None,
            },
            "public_contacts": [],
            "source_candidates": [{
                "evidence_id": "EV-NO-PRO-001", "source_url": "https://example.com/unverified-farrier",
                "source_name": "Synthetic identity-only page", "source_type": "business_website",
                "retrieved_at": "2026-08-14T00:00:00Z",
                "evidence_excerpt": "A name and location are present, but no professional hoof-care activity is stated.",
                "fact_or_inference": "direct_fact",
            }],
            "missing_information": ["No professional hoof-care activity is evidenced."],
            "conflicts": [],
        },
        "classification_decision": {
            "segment": "farrier", "prospect_type": "farrier_independent", "identity_type": "person",
        },
        "qualification_package": {"qualification": exclusion_input["qualification"]},
        "confidence_package": {
            "assessment": {"gates": {"unresolved_identity_conflict": {"value": False}, "critical_evidence_conflict": {"value": False}}},
            "confidence": {
                "score": 90, "level": "high", "method_version": "evidence-confidence-1.0.0",
                "reasons": ["The exclusion evidence is traceable."],
                "limitations": ["Synthetic exclusion test candidate."],
            },
        },
        "scoring_package": exclusion_scoring,
        "source_policy_status": "approved",
        "access_method": "client_provided_file",
        "model": None,
        "tools_used": [],
        "provided_exclusion_file_status": "unavailable",
    }


def request(package_id: str, bundles: list[dict]) -> dict:
    return {
        "schema_version": "1.0.0", "package_id": package_id, "run_id": f"RUN-{package_id}",
        "generated_at": "2026-08-14T16:40:40Z", "initiated_by": "Séverine", "candidates": bundles,
    }


def main() -> None:
    for skill in [REVIEW_SKILL, EXPORT_SKILL]:
        check((skill / "SKILL.md").exists(), f"{skill.name} exists")
        check(len((skill / "SKILL.md").read_text(encoding="utf-8").splitlines()) < 500, f"{skill.name} under 500 lines")
        evals = load(skill / "evals" / "evals.json")
        check(len(evals["evals"]) == 3, f"{skill.name} has three evals")
        text = (skill / "SKILL.md").read_text(encoding="utf-8").lower()
        check("hubspot" in text and "a2" in text and "outreach" in text, f"{skill.name} states action boundaries")

    james_request = load(PROFILE / "evaluations" / "wave3" / "fixtures" / "james-review-input.json")
    james_package = build(james_request)
    james = james_package["candidates"][0]
    check(james_package["summary"]["total"] == 1, "James review package contains one candidate")
    check(james["recommended_review_status"] == "accept", "James recommendation is Accept for human review")
    check(james["prospect_candidate"]["scoring"]["score"] == 86, "James score remains 86")
    check(james["prospect_candidate"]["confidence"]["score"] == 84, "James confidence remains 84")
    check(james["prospect_candidate"]["duplicate_check"]["hubspot"]["status"] == "unavailable", "HubSpot remains unavailable")
    check("metadata is available" in james["prospect_candidate"]["duplicate_check"]["hubspot"]["notes"], "HubSpot metadata availability is distinguished from live record access")
    check(james["prospect_candidate"]["recommendation"]["suggested_territory"] is None, "state is not mapped directly to HubSpot Sales Territory")
    check(james["prospect_candidate"]["recommendation"]["suggested_owner"] is None, "owner remains unassigned without an approved rule")
    check(james["a2_handoff"]["status"] == "not_authorised", "A2 handoff remains unauthorised")

    hubspot_check = {
        "status": "possible_match",
        "checked_at": "2026-08-14T16:35:00Z",
        "method_version": "n8n-hubspot-dedup-1.0.0",
        "matches": [{
            "system": "hubspot",
            "record_id": "123456789",
            "record_url": "https://app.hubspot.com/contacts/123456/record/0-1/123456789",
            "match_level": "exact",
            "matched_fields": ["email"],
        }],
        "notes": "n8n completed the live HubSpot duplicate check.",
    }
    checked_request = copy.deepcopy(james_request)
    checked_request["package_id"] = "A1-RP-WAVE3-HUBSPOT"
    checked_request["candidates"][0]["hubspot_check"] = hubspot_check
    checked_package = build(checked_request)
    checked = checked_package["candidates"][0]
    check(
        checked["prospect_candidate"]["duplicate_check"]["hubspot"] == hubspot_check,
        "n8n HubSpot check result passes through unchanged",
    )
    check(checked_package["integration_status"]["hubspot"] == "checked", "Review package reports completed HubSpot checks")
    check(checked["recommended_review_status"] == "needs_research", "Possible HubSpot match requires human review")
    check(
        not any("hubspot" in value.lower() and "unavailable" in value.lower() for value in checked["integration_limitations"]),
        "Completed HubSpot checks are not described as unavailable",
    )
    check(
        not any("hubspot checks are unavailable" in value.lower() for value in checked["a2_handoff"]["blockers"]),
        "Completed HubSpot checks do not leave a false A2 blocker",
    )
    check(checked["prospect_candidate"]["data_governance"]["a1_outreach_prohibited"] is True, "HubSpot checks do not permit outreach")
    check(checked["prospect_candidate"]["workflow"]["review_decision"] == "none", "HubSpot checks do not bypass human review")

    no_domain_request = copy.deepcopy(james_request)
    no_domain_request["package_id"] = "A1-RP-WAVE3-HUBSPOT-NO-DOMAIN"
    no_domain_request["candidates"][0]["hubspot_check"] = {
        "status": "not_checked_no_domain",
        "checked_at": "2026-08-14T16:35:00Z",
        "method_version": "n8n-hubspot-domain-1.0.0",
        "matches": [],
        "notes": "No canonical company domain was available for the native domain check.",
    }
    no_domain_package = build(no_domain_request)
    check(no_domain_package["integration_status"]["hubspot"] == "partial", "No-domain HubSpot state remains explicit and partial")

    possible_duplicate_request = copy.deepcopy(james_request)
    possible_duplicate_request["package_id"] = "A1-RP-WAVE3-HUBSPOT-POSSIBLE"
    possible_duplicate_request["candidates"][0]["hubspot_check"] = {
        "status": "possible_duplicate",
        "checked_at": "2026-08-14T16:35:00Z",
        "method_version": "n8n-hubspot-domain-1.0.0",
        "matches": [{
            "system": "hubspot",
            "record_id": "987654321",
            "record_url": None,
            "match_level": "probable",
            "matched_fields": ["domain"],
        }],
        "notes": "Ambiguous domain evidence requires human review.",
    }
    possible_duplicate_package = build(possible_duplicate_request)
    check(possible_duplicate_package["candidates"][0]["recommended_review_status"] == "needs_research", "n8n possible_duplicate requires human review")

    named_contact_candidate = copy.deepcopy(james["prospect_candidate"])
    named_contact_candidate["public_contacts"][1]["label"] = "Primary named contact — J.T. Holub — Farrier"
    check(not cross_reference_errors(named_contact_candidate), "one primary named contact validates")
    check(named_contact_candidate["scoring"]["score"] == 86, "named contact availability does not change ICP score")

    too_many_primary = copy.deepcopy(named_contact_candidate)
    too_many_primary["public_contacts"].append({
        "contact_type": "email",
        "value": "second.primary@example.com",
        "label": "Primary named contact — Second Person — Manager",
        "evidence_ids": ["EV-CONTACT-001"],
    })
    check(any("at most one primary named contact" in error for error in cross_reference_errors(too_many_primary)), "second primary named contact is rejected")

    too_many_secondary = copy.deepcopy(named_contact_candidate)
    too_many_secondary["public_contacts"].extend([
        {"contact_type": "email", "value": "secondary.one@example.com", "label": "Secondary named contact — Secondary One — Manager", "evidence_ids": ["EV-CONTACT-001"]},
        {"contact_type": "email", "value": "secondary.two@example.com", "label": "Secondary named contact — Secondary Two — Director", "evidence_ids": ["EV-CONTACT-001"]},
    ])
    check(any("at most one secondary named contact" in error for error in cross_reference_errors(too_many_secondary)), "second secondary named contact is rejected")

    contract_schema = load(PROFILE / "skills" / "a1-prospect-data-contract" / "references" / "prospect-candidate.schema.json")
    check("associated_people" not in contract_schema["properties"], "associated_people is intentionally absent from A1 V1 schema")

    mixed_request = request("A1-RP-WAVE3-MIXED", [copy.deepcopy(james_request["candidates"][0]), owner_bundle(), reject_bundle()])
    mixed_package = build(mixed_request)
    statuses = [item["recommended_review_status"] for item in mixed_package["candidates"]]
    check(statuses == ["accept", "needs_research", "reject"], "Mixed batch ranks Accept, Needs Research, Reject")
    check(mixed_package["summary"]["farrier"] == 2 and mixed_package["summary"]["horse_owner"] == 1, "Mixed batch reports Farrier and Horse Owner separately")
    owner = next(item for item in mixed_package["candidates"] if item["candidate_id"] == "A1-OWNER-UNKNOWN-001")
    check(owner["prospect_candidate"]["scoring"]["score"] == 80, "Unknown-count owner numeric score remains 80")
    check(owner["prospect_candidate"]["scoring"]["band"] == "medium", "Unknown-count owner final band remains Medium")
    check(owner["scoring_outcome"] == "horse_count_unknown_human_review", "Unknown-count owner review outcome preserved")

    original = james_request["candidates"][0]
    duplicate = renamed_james_bundle(original, "A1-JHOLUB-DUPLICATE", "DUPLICATE", keep_domain=True)
    duplicate_request = request("A1-RP-WAVE3-DUPLICATE", [copy.deepcopy(original), duplicate])
    duplicate_package = build(duplicate_request)
    check(all(item["recommended_review_status"] == "needs_research" for item in duplicate_package["candidates"]), "Shared domain forces Needs Research")
    check(all(item["prospect_candidate"]["duplicate_check"]["batch"]["status"] == "possible_match" for item in duplicate_package["candidates"]), "Shared domain is recorded as possible batch duplicate")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        package_path = temp / "mixed.json"
        package_path.write_text(json.dumps(mixed_package, indent=2, ensure_ascii=False), encoding="utf-8")
        manifest = export(package_path, temp / "exports", "mixed-review")
        check(manifest["candidate_count"] == 3, "Export manifest candidate count matches mixed package")
        check(all(value == "passed" for value in manifest["validation"].values()), "All cross-format export validations pass")
        check({entry["format"] for entry in manifest["files"]} == {"json", "markdown", "csv", "xlsx"}, "All four export formats are generated")

        invalid = copy.deepcopy(james_package)
        invalid["candidates"][0]["prospect_candidate"]["scoring"]["score"] = 85
        invalid_path = temp / "invalid.json"
        invalid_path.write_text(json.dumps(invalid), encoding="utf-8")
        rejected = False
        try:
            export(invalid_path, temp / "invalid-exports", "invalid")
        except ValueError as error:
            rejected = "component total" in str(error)
        check(rejected, "Export rejects score/component drift")

    print("ALL WAVE 3 SKILL TESTS PASSED")


if __name__ == "__main__":
    main()
