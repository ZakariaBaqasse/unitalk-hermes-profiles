#!/usr/bin/env python3
"""Generate coherent synthetic candidate bundles for Step 8 representative profile tests."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[1]
SCORING_SCRIPTS = PROFILE / "skills" / "icp-scoring-and-rationale" / "scripts"
if str(SCORING_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCORING_SCRIPTS))
if str(PROFILE / "scripts") not in sys.path:
    sys.path.insert(0, str(PROFILE / "scripts"))
from build_scoring_package import build as build_scoring  # noqa: E402
from run_wave3_skill_tests import owner_bundle, reject_bundle  # noqa: E402

GENERATED_AT = "2026-08-15T17:46:29Z"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def high_farrier_bundle(candidate_id: str = "A1-SYN-FARRIER-HIGH", person_name: str = "Alex Morgan") -> dict:
    template = load(PROFILE / "evaluations" / "wave1" / "iteration-8" / "accepted-artifacts" / "qualification-output.json")["qualification"]
    status_map = {
        "farrier.professional_activity": ("confirmed", ["EV-SYN-PRO-001"]),
        "farrier.product_usage_or_influence": ("confirmed", ["EV-SYN-SERVICE-001"]),
        "farrier.established_client_base": ("unknown", []),
        "farrier.regular_business_activity": ("confirmed", ["EV-SYN-PRO-001"]),
        "farrier.high_value_service_area": ("confirmed", ["EV-SYN-AREA-001"]),
        "farrier.advanced_specialisation": ("confirmed", ["EV-SYN-SERVICE-001"]),
        "farrier.certified_or_experienced": ("confirmed", ["EV-SYN-ROLE-001"]),
        "farrier.sport_horse_focus": ("confirmed", ["EV-SYN-AREA-001"]),
        "farrier.multi_farrier_business": ("not_confirmed", []),
        "farrier.buying_influence": ("confirmed", ["EV-SYN-ROLE-001"]),
        "farrier.product_fit": ("confirmed", ["EV-SYN-SERVICE-001"]),
        "farrier.engagement_signal": ("confirmed", ["EV-SYN-ROLE-001"]),
        "farrier.apprentice_future_potential": ("not_confirmed", []),
        "farrier.inactive_or_hobbyist": ("not_confirmed", []),
        "farrier.no_professional_evidence": ("not_confirmed", []),
    }
    qualification = copy.deepcopy(template)
    for criterion in qualification["criteria"]:
        status, evidence_ids = status_map[criterion["criterion_id"]]
        criterion["status"] = status
        criterion["evidence_ids"] = evidence_ids
        criterion["notes"] = f"Synthetic Step 8 evidence state for {criterion['criterion_id']}."
    qualification["minimum_data_status"] = "pass"
    qualification["missing_minimum_fields"] = []
    qualification["exclusion_status"] = "eligible"
    qualification["exclusion_reasons"] = []

    confidence = {
        "level": "high",
        "score": 84,
        "method_version": "evidence-confidence-1.0.0",
        "reasons": ["Synthetic direct evidence is internally traceable and sufficient for the controlled test."],
        "limitations": ["Synthetic candidate created only for Step 8 validation."],
    }
    scoring_package = build_scoring({"segment": "farrier", "qualification": qualification, "confidence": confidence})
    return {
        "candidate_id": candidate_id,
        "record_kind": "synthetic_test",
        "research_seed": {
            "schema_version": "1.0.0",
            "run_id": f"RUN-{candidate_id}",
            "seed_id": f"SEED-{candidate_id}",
            "discovered_at": GENERATED_AT,
            "identity_hint": {
                "display_name": f"{person_name} / Bluegrass Performance Farriery",
                "person_name": person_name,
                "organisation_name": "Bluegrass Performance Farriery",
                "role_title": "Farrier",
            },
            "website": "https://bluegrass-farriery.example.test",
            "location_hint": {
                "country_code": "US",
                "state_region": "Kentucky",
                "city": "Lexington",
                "postal_code": "40502",
                "public_address": "100 Synthetic Lane, Lexington, KY 40502",
            },
            "public_contacts": [
                {"contact_type": "email", "value": "alex.morgan@example.com", "label": "Synthetic business email", "evidence_ids": ["EV-SYN-ROLE-001"]},
                {"contact_type": "phone", "value": "+1-555-010-8000", "label": "Synthetic business phone", "evidence_ids": ["EV-SYN-ROLE-001"]},
            ],
            "source_candidates": [
                {
                    "evidence_id": "EV-SYN-PRO-001",
                    "source_url": "https://bluegrass-farriery.example.test",
                    "source_name": "Synthetic Farrier Homepage",
                    "source_type": "business_website",
                    "retrieved_at": GENERATED_AT,
                    "evidence_excerpt": "Bluegrass Performance Farriery provides active professional hoof-care appointments throughout Lexington.",
                    "fact_or_inference": "direct_fact",
                },
                {
                    "evidence_id": "EV-SYN-SERVICE-001",
                    "source_url": "https://bluegrass-farriery.example.test/services",
                    "source_name": "Synthetic Farrier Services",
                    "source_type": "business_website",
                    "retrieved_at": GENERATED_AT,
                    "evidence_excerpt": "Services include performance shoeing, therapeutic applications and selection of professional horseshoes and hoof-care products.",
                    "fact_or_inference": "direct_fact",
                },
                {
                    "evidence_id": "EV-SYN-AREA-001",
                    "source_url": "https://bluegrass-farriery.example.test/service-area",
                    "source_name": "Synthetic Service Area",
                    "source_type": "business_website",
                    "retrieved_at": GENERATED_AT,
                    "evidence_excerpt": "The practice serves sport and competition horses in Lexington and the surrounding Kentucky equine community.",
                    "fact_or_inference": "direct_fact",
                },
                {
                    "evidence_id": "EV-SYN-ROLE-001",
                    "source_url": "https://bluegrass-farriery.example.test/contact",
                    "source_name": "Synthetic Farrier Contact",
                    "source_type": "business_website",
                    "retrieved_at": GENERATED_AT,
                    "evidence_excerpt": f"{person_name}, Farrier and owner, selects products for the practice. alex.morgan@example.com | +1-555-010-8000.",
                    "fact_or_inference": "direct_fact",
                },
            ],
            "missing_information": ["Exact client-base size is not published."],
            "conflicts": [],
            "status": "ready_for_classification",
        },
        "classification_decision": {
            "schema_version": "1.0.0",
            "seed_id": f"SEED-{candidate_id}",
            "segment": "farrier",
            "prospect_type": "farrier_independent",
            "identity_type": "person_and_organisation",
            "classification_status": "confirmed",
            "evidence_references": ["EV-SYN-PRO-001", "EV-SYN-ROLE-001"],
            "rationale": "Synthetic professional Farrier and associated business are explicitly identified.",
            "unresolved_questions": [],
        },
        "qualification_package": {"qualification": qualification},
        "confidence_package": {
            "assessment": {
                "gates": {
                    "unresolved_identity_conflict": {"value": False},
                    "critical_evidence_conflict": {"value": False},
                }
            },
            "confidence": confidence,
        },
        "scoring_package": scoring_package,
        "source_policy_status": "approved",
        "access_method": "client_provided_file",
        "model": None,
        "tools_used": [],
        "provided_exclusion_file_status": "unavailable",
    }


def replace_base_url(bundle: dict, old: str, new: str) -> None:
    seed = bundle["research_seed"]
    if seed.get("website"):
        seed["website"] = seed["website"].replace(old, new)
    for source in seed.get("source_candidates", []):
        source["source_url"] = source["source_url"].replace(old, new)


def request(package_id: str, bundles: list[dict]) -> dict:
    return {
        "schema_version": "1.0.0",
        "package_id": package_id,
        "run_id": f"RUN-{package_id}",
        "generated_at": GENERATED_AT,
        "initiated_by": "Step 8 synthetic suite",
        "candidates": bundles,
    }


def main() -> None:
    output = PROFILE / "evaluations" / "step8" / "fixtures"
    output.mkdir(parents=True, exist_ok=True)
    high = high_farrier_bundle()
    owner = owner_bundle()
    excluded = reject_bundle()
    replace_base_url(owner, "https://example.com/synthetic-farm", "https://synthetic-horse-farm.example.test")
    replace_base_url(excluded, "https://example.com/unverified-farrier", "https://synthetic-unverified-farrier.example.test")
    batch_one = request("A1-RP-STEP8-MIXED", [high, owner, excluded])

    duplicate_one = high_farrier_bundle("A1-SYN-DUPLICATE-001", "Alex Morgan")
    duplicate_two = high_farrier_bundle("A1-SYN-DUPLICATE-002", "Alex M. Morgan")
    duplicate_two["research_seed"]["run_id"] = "RUN-A1-SYN-DUPLICATE-002"
    duplicate_two["research_seed"]["seed_id"] = "SEED-A1-SYN-DUPLICATE-002"
    duplicate_two["classification_decision"]["seed_id"] = "SEED-A1-SYN-DUPLICATE-002"
    batch_two = request("A1-RP-STEP8-DUPLICATES", [duplicate_one, duplicate_two])

    (output / "mixed-batch-input.json").write_text(json.dumps(batch_one, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "duplicate-batch-input.json").write_text(json.dumps(batch_two, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "passed",
        "fixtures": ["mixed-batch-input.json", "duplicate-batch-input.json"],
        "mixed_candidates": 3,
        "duplicate_candidates": 2,
        "all_record_kind": "synthetic_test",
    }))


if __name__ == "__main__":
    main()
