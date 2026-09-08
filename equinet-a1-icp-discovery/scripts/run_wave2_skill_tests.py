#!/usr/bin/env python3
"""Static and deterministic integration tests for A1 Wave 2 skills."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


PROFILE_DIR = Path(__file__).resolve().parents[1]
SKILLS_DIR = PROFILE_DIR / "skills"
ACCEPTED = PROFILE_DIR / "evaluations" / "wave1" / "iteration-8" / "accepted-artifacts"
WAVE2_SKILLS = ["prospect-evidence-and-confidence", "icp-scoring-and-rationale"]


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


confidence_builder = import_module(
    "confidence_package_builder",
    SKILLS_DIR / "prospect-evidence-and-confidence" / "scripts" / "build_confidence_package.py",
)
scoring_builder = import_module(
    "scoring_package_builder",
    SKILLS_DIR / "icp-scoring-and-rationale" / "scripts" / "build_scoring_package.py",
)
evidence_validator = import_module(
    "evidence_policy_validator",
    PROFILE_DIR / "scripts" / "validate_evidence_confidence_rules.py",
)


def assert_true(label: str, condition: bool, detail: str = "") -> None:
    if not condition:
        raise AssertionError(f"{label}: {detail}")
    print(f"PASS: {label}")


def test_skill_packages() -> None:
    for skill_name in WAVE2_SKILLS:
        skill_dir = SKILLS_DIR / skill_name
        text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        assert_true(f"{skill_name} exists", bool(text))
        assert_true(f"{skill_name} under 500 lines", len(text.splitlines()) < 500)
        assert_true(f"{skill_name} frontmatter", f"name: {skill_name}" in text and "description:" in text[:1000])
        assert_true(f"{skill_name} has three evals", len(json.loads((skill_dir / "evals" / "evals.json").read_text())["evals"]) == 3)
        assert_true(f"{skill_name} prohibits outreach", "outreach" in text.lower())


def gate(value: bool, rationale: str, evidence_ids: list[str] | None = None) -> dict:
    return {"value": value, "evidence_ids": evidence_ids or [], "rationale": rationale}


def dimension(level: str, rationale: str, evidence_ids: list[str] | None = None) -> dict:
    return {"level": level, "evidence_ids": evidence_ids or [], "rationale": rationale}


def james_assessment() -> dict:
    evidence_ids = ["EV-HOME-001", "EV-TRAVEL-001", "EV-LAMENESS-001", "EV-GLUE-001", "EV-ABOUT-001", "EV-CONTACT-001"]
    return {
        "schema_version": "1.0.0",
        "method_version": "evidence-confidence-1.0.0",
        "candidate_reference": {"run_id": "RUN-20260812T190824Z-890880", "seed_id": "SEED-JHOLUB-001"},
        "available_evidence_ids": evidence_ids,
        "dimensions": {
            "identity_certainty": dimension("good_multi_field_match", "Official site links J.T. Holub and James Holub Equine Services; minor name-form variation remains.", ["EV-HOME-001", "EV-CONTACT-001"]),
            "source_quality": dimension("authoritative_primary_business_source", "Current official business website is authoritative for self-controlled facts.", ["EV-HOME-001"]),
            "evidence_directness": dimension("all_material_claims_direct", "Material qualification claims are explicitly stated on the official website.", ["EV-HOME-001", "EV-ABOUT-001", "EV-GLUE-001"]),
            "corroboration": dimension("one_strong_source", "One official business domain supports the candidate; pages on the same domain are one source.", ["EV-HOME-001"]),
            "freshness": dimension("current_within_claim_window", "Current official business website requires no visible publication date for self-controlled facts.", ["EV-HOME-001", "EV-CONTACT-001"]),
            "completeness": dimension("minimum_review_package_only", "Confidence-stage minimum is complete, while noncritical ICP details such as client-base size remain unknown.", evidence_ids),
        },
        "gates": {
            "mandatory_claim_inference_only": gate(False, "Mandatory professional-activity claim is directly supported."),
            "unresolved_identity_conflict": gate(False, "Minor J.T./James variation is resolved within the same official website."),
            "critical_evidence_conflict": gate(False, "No material evidence conflict remains."),
            "minimum_data_failed": gate(False, "Confidence-stage minimum evidence package is complete."),
            "blocked_source_used": gate(False, "Only permitted official business website evidence is retained."),
            "no_evidence": gate(False, "Six traceable evidence records are available."),
            "fabricated_or_untraceable_evidence": gate(False, "All evidence IDs map to retained source excerpts."),
        },
        "confidence_stage_missing_fields": [],
    }


def test_confidence() -> dict:
    policy = evidence_validator.load_yaml(PROFILE_DIR / "configurations" / "evidence" / "evidence-confidence-rules-v1.yaml")
    assert_true("evidence policy remains valid", not evidence_validator.validate_policy(policy))

    assessment = james_assessment()
    package = confidence_builder.build(assessment)
    assert_true("James confidence score is 84", package["confidence"]["score"] == 84, str(package["confidence"]))
    assert_true("James confidence is High", package["confidence"]["level"] == "high")
    assert_true("single-source limitation is visible", any("one strong primary source" in item for item in package["confidence"]["limitations"]))

    inference = copy.deepcopy(assessment)
    inference["gates"]["mandatory_claim_inference_only"] = gate(True, "Mandatory claim is inference-only.", ["EV-HOME-001"])
    inference_package = confidence_builder.build(inference)
    assert_true("mandatory inference capped at 59", inference_package["confidence"]["score"] == 59)
    assert_true("mandatory inference confidence Low", inference_package["confidence"]["level"] == "low")

    blocked = copy.deepcopy(assessment)
    blocked["gates"]["blocked_source_used"] = gate(True, "Blocked source supports a claim.", ["EV-HOME-001"])
    try:
        confidence_builder.build(blocked)
    except ValueError as exc:
        assert_true("blocked source invalidates confidence", "blocked source" in str(exc).lower())
    else:
        raise AssertionError("Blocked source should invalidate confidence assessment")

    mismatch = copy.deepcopy(assessment)
    mismatch["confidence_stage_missing_fields"] = ["identity"]
    try:
        confidence_builder.build(mismatch)
    except ValueError as exc:
        assert_true("stage minimum gate mismatch rejected", "minimum_data_failed" in str(exc))
    else:
        raise AssertionError("Stage minimum mismatch should fail")
    return package


def criterion(criterion_id: str, status: str, evidence_ids: list[str] | None = None) -> dict:
    return {
        "criterion_id": criterion_id,
        "criterion_label": criterion_id,
        "category": "fit",
        "status": status,
        "evidence_ids": evidence_ids or [],
        "notes": None,
    }


def test_scoring(confidence_package: dict) -> None:
    qualification_artifact = json.loads((ACCEPTED / "qualification-output.json").read_text(encoding="utf-8"))
    candidate = {
        "segment": "farrier",
        "qualification": qualification_artifact["qualification"],
        "confidence": confidence_package["confidence"],
    }
    package = scoring_builder.build(candidate)
    assert_true("James ICP score is 86", package["scoring"]["score"] == 86, str(package["scoring"]))
    assert_true("James final band is High", package["scoring"]["band"] == "high")
    assert_true("James scoring outcome is high-priority Farrier", package["audit"]["outcome"] == "high_priority_farrier")
    assert_true("scoring explanation includes confidence", "High evidence confidence" in package["explanation"]["confidence_interpretation"])
    assert_true("scoring components sum to score", sum(item["points_awarded"] for item in package["scoring"]["components"]) == 86)

    owner_criteria = [
        criterion("horse_owner.commercial_operation", "confirmed", ["EV-H"]),
        criterion("horse_owner.more_than_three_horses", "unknown"),
        criterion("horse_owner.purchasing_influence", "confirmed", ["EV-H"]),
        criterion("horse_owner.product_fit", "confirmed", ["EV-H"]),
        criterion("horse_owner.performance_discipline", "confirmed", ["EV-H"]),
        criterion("horse_owner.breeding_activity", "confirmed", ["EV-H"]),
        criterion("horse_owner.professional_network", "confirmed", ["EV-H"]),
        criterion("horse_owner.high_equine_activity_location", "confirmed", ["EV-H"]),
        criterion("horse_owner.buying_signal", "confirmed", ["EV-H"]),
        criterion("horse_owner.single_horse_recreational", "not_confirmed"),
        criterion("horse_owner.no_commercial_evidence", "not_confirmed"),
    ]
    owner_candidate = {
        "segment": "horse_owner",
        "qualification": {
            "icp_config_version": "1.0.0",
            "criteria": owner_criteria,
            "minimum_data_status": "pass",
            "missing_minimum_fields": [],
            "exclusion_status": "eligible",
            "exclusion_reasons": [],
        },
        "confidence": confidence_package["confidence"],
    }
    owner_package = scoring_builder.build(owner_candidate)
    assert_true("unknown horse count keeps numeric score 80", owner_package["scoring"]["score"] == 80)
    assert_true("unknown horse count caps final band Medium", owner_package["scoring"]["band"] == "medium")
    assert_true("unknown horse count outcome review", owner_package["audit"]["outcome"] == "horse_count_unknown_human_review")

    excluded_candidate = {
        "segment": "farrier",
        "qualification": {
            "icp_config_version": "1.0.0",
            "criteria": [criterion("farrier.no_professional_evidence", "confirmed", ["EV-X"])],
            "minimum_data_status": "pass",
            "missing_minimum_fields": [],
            "exclusion_status": "excluded",
            "exclusion_reasons": ["No professional evidence"],
        },
        "confidence": confidence_package["confidence"],
    }
    excluded_package = scoring_builder.build(excluded_candidate)
    assert_true("excluded Farrier blocks scoring", excluded_package["scoring"]["status"] == "blocked")
    assert_true("specific Farrier exclusion outcome preserved", excluded_package["audit"]["outcome"] == "excluded_no_professional_evidence")
    assert_true("blocked scoring has no unearned criteria list", excluded_package["explanation"]["unearned_weighted_criteria"] == [])
    assert_true("confidence cannot override blocked scoring", "does not override the exclusion" in excluded_package["explanation"]["confidence_interpretation"])


def main() -> int:
    test_skill_packages()
    confidence_package = test_confidence()
    test_scoring(confidence_package)
    print("ALL WAVE 2 SKILL TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
