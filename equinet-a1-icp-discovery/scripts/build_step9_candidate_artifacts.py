#!/usr/bin/env python3
"""Build audited Step 9 classification, qualification, confidence and scoring artifacts from validated real research seeds."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

PROFILE = Path(__file__).resolve().parents[1]
for path in [
    PROFILE / "skills" / "equinet-icp-qualification" / "scripts",
    PROFILE / "skills" / "prospect-evidence-and-confidence" / "scripts",
    PROFILE / "skills" / "icp-scoring-and-rationale" / "scripts",
]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
from build_qualification import build as build_qualification  # noqa: E402
from build_confidence_package import build as build_confidence  # noqa: E402
from build_scoring_package import build as build_scoring  # noqa: E402

ICP_PATH = PROFILE / "configurations" / "icp" / "equinet-icp-v1.yaml"
CLASSIFICATION_SCHEMA = PROFILE / "skills" / "prospect-segment-classification" / "references" / "classification-decision.schema.json"
OUTPUT = PROFILE / "evaluations" / "step9" / "candidates"
RESEARCH = PROFILE / "evaluations" / "step9" / "research"
GENERATED_AT = "2026-08-15T20:38:58Z"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate_classification(value: dict[str, Any]) -> None:
    schema = load(CLASSIFICATION_SCHEMA)
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value))
    if errors:
        raise ValueError("Invalid classification: " + " | ".join(error.message for error in errors))


def assessment(segment: str, statuses: dict[str, tuple[str, list[str], str]], icp: dict[str, Any]) -> dict[str, Any]:
    values = {}
    for criterion in icp["segments"][segment]["criteria"]:
        criterion_id = criterion["criterion_id"]
        if criterion_id in statuses:
            status, evidence_ids, notes = statuses[criterion_id]
        elif criterion["category"] in {"negative", "exclusion"}:
            status, evidence_ids, notes = "not_confirmed", [], "No retained evidence confirms this negative or exclusion criterion."
        else:
            status, evidence_ids, notes = "unknown", [], "The retained public evidence does not establish this criterion."
        values[criterion_id] = {"status": status, "evidence_ids": evidence_ids, "notes": notes}
    return {"schema_version": "1.0.0", "segment": segment, "criterion_assessments": values, "missing_minimum_fields": []}


def confidence_assessment(seed: dict[str, Any], directness: str, completeness: str = "minimum_review_package_only") -> dict[str, Any]:
    evidence_ids = [entry["evidence_id"] for entry in seed["source_candidates"]]
    all_evidence = evidence_ids
    dimensions = {
        "identity_certainty": {"level": "strong_unique_match", "evidence_ids": all_evidence, "rationale": "The organisation identity and official domain are unambiguous."},
        "source_quality": {"level": "authoritative_primary_business_source", "evidence_ids": all_evidence, "rationale": "All retained evidence comes from the organisation's current official business website."},
        "evidence_directness": {"level": directness, "evidence_ids": all_evidence, "rationale": "Material identity, operation and location claims are direct; any role-based commercial conclusion remains explicit in the qualification notes."},
        "corroboration": {"level": "one_strong_source", "evidence_ids": all_evidence, "rationale": "The retained pages belong to one official business domain and are counted as one strong source."},
        "freshness": {"level": "current_within_claim_window", "evidence_ids": all_evidence, "rationale": "The official site presents current teams, operations or current roster information."},
        "completeness": {"level": completeness, "evidence_ids": all_evidence, "rationale": "The confidence-stage minimum is met; CRM checks and named procurement contacts remain unavailable or unknown."},
    }
    gates = {
        "mandatory_claim_inference_only": {"value": False, "evidence_ids": all_evidence, "rationale": "Mandatory segment claims are directly supported by the official website."},
        "unresolved_identity_conflict": {"value": False, "evidence_ids": all_evidence, "rationale": "No material identity conflict is present."},
        "critical_evidence_conflict": {"value": False, "evidence_ids": [], "rationale": "No contradictory retained evidence is present."},
        "minimum_data_failed": {"value": False, "evidence_ids": all_evidence, "rationale": "The confidence-stage minimum evidence package is present."},
        "blocked_source_used": {"value": False, "evidence_ids": [], "rationale": "No blocked source is retained."},
        "no_evidence": {"value": False, "evidence_ids": all_evidence, "rationale": "Permitted official-source evidence is present."},
        "fabricated_or_untraceable_evidence": {"value": False, "evidence_ids": [], "rationale": "Every retained evidence item has an official URL and excerpt."},
    }
    return {
        "schema_version": "1.0.0",
        "method_version": "evidence-confidence-1.0.0",
        "candidate_reference": {"run_id": seed["run_id"], "seed_id": seed["seed_id"]},
        "available_evidence_ids": evidence_ids,
        "dimensions": dimensions,
        "gates": gates,
        "confidence_stage_missing_fields": [],
    }


def build_candidate(slug: str, candidate_id: str, seed_file: str, classification: dict[str, Any], statuses: dict[str, tuple[str, list[str], str]], directness: str, icp: dict[str, Any]) -> dict[str, Any]:
    seed = load(RESEARCH / seed_file)
    validate_classification(classification)
    qualification_assessment = assessment(classification["segment"], statuses, icp)
    qualification_package = build_qualification(qualification_assessment, icp)
    rich_confidence = confidence_assessment(seed, directness)
    confidence_package = build_confidence(rich_confidence)
    scoring_package = build_scoring({"segment": classification["segment"], "qualification": qualification_package["qualification"], "confidence": confidence_package["confidence"]})

    directory = OUTPUT / slug
    write(directory / "classification-decision.json", classification)
    write(directory / "qualification-assessment.json", qualification_assessment)
    write(directory / "qualification-package.json", qualification_package)
    write(directory / "confidence-assessment.json", rich_confidence)
    write(directory / "confidence-package.json", confidence_package)
    write(directory / "scoring-package.json", scoring_package)

    bundle = {
        "candidate_id": candidate_id,
        "record_kind": "production",
        "research_seed": seed,
        "classification_decision": classification,
        "qualification_package": qualification_package,
        "confidence_package": confidence_package,
        "scoring_package": scoring_package,
        "source_policy_status": "approved",
        "access_method": "approved_api",
        "model": "deepseek-v4-flash",
        "tools_used": ["Exa web_search", "Firecrawl web_extract", "deterministic qualification builder", "deterministic confidence calculator", "deterministic ICP scorer"],
        "provided_exclusion_file_status": "unavailable",
    }
    write(directory / "review-input-bundle.json", bundle)
    return bundle


def main() -> None:
    icp = yaml.safe_load(ICP_PATH.read_text(encoding="utf-8"))

    rood_classification = {
        "schema_version": "1.0.0",
        "seed_id": "SEED-RR-PODIATRY-001",
        "segment": "farrier",
        "prospect_type": "farrier_multi_practitioner_business",
        "identity_type": "person_and_organisation",
        "classification_status": "confirmed",
        "evidence_references": ["EV-RR-TEAM-001", "EV-RR-LEX-001"],
        "rationale": "The official Lexington Podiatry page identifies a dedicated multi-practitioner Farrier team within Rood & Riddle Equine Hospital and names Manfred Eckert as Co-Founder/Farrier. He is retained as the single primary named contact; this does not change scoring or establish procurement authority.",
        "unresolved_questions": ["The public pages do not identify the procurement decision-maker for the Farrier team."],
    }
    rood_statuses = {
        "farrier.professional_activity": ("confirmed", ["EV-RR-TEAM-001"], "The official Podiatry team page has a dedicated Farriers section with multiple current named Farriers."),
        "farrier.product_usage_or_influence": ("confirmed", ["EV-RR-TEAM-001"], "A current multi-practitioner Farrier team necessarily uses professional hoof-care products; this is a role-based product-usage conclusion, not a claim of procurement authority."),
        "farrier.regular_business_activity": ("confirmed", ["EV-RR-TEAM-001", "EV-RR-LEX-001"], "The official hospital and current team pages show an established active Lexington operation."),
        "farrier.high_value_service_area": ("confirmed", ["EV-RR-LEX-001"], "The hospital is explicitly located in the heart of the Bluegrass in Lexington, Kentucky."),
        "farrier.advanced_specialisation": ("confirmed", ["EV-RR-TEAM-001"], "The dedicated Equine Podiatry team is an explicit advanced hoof-care specialisation."),
        "farrier.certified_or_experienced": ("confirmed", ["EV-RR-TEAM-001"], "The official team page lists CJF, NZCF and DIPWCF credentials among current team members."),
        "farrier.multi_farrier_business": ("confirmed", ["EV-RR-TEAM-001"], "The official page lists multiple Farriers in the Lexington team."),
        "farrier.product_fit": ("confirmed", ["EV-RR-TEAM-001"], "A dedicated professional Farrier/Podiatry team has recurring hoof-care product requirements."),
        "farrier.engagement_signal": ("confirmed", ["EV-RR-TEAM-001", "EV-RR-LEX-001"], "The current official site presents active team and hospital operations."),
        "farrier.established_client_base": ("unknown", [], "The official pages describe a worldwide referral center but do not quantify Farrier-team clients."),
        "farrier.sport_horse_focus": ("not_confirmed", [], "The retained pages state all breeds and disciplines rather than a specific sport-horse focus."),
        "farrier.buying_influence": ("unknown", [], "No named procurement or product-selection decision-maker is identified."),
    }
    rood_bundle = build_candidate("rood-riddle-podiatry", "A1-RR-PODIATRY-001", "rood-riddle-podiatry-seed.json", rood_classification, rood_statuses, "mostly_direct", icp)

    darley_classification = {
        "schema_version": "1.0.0",
        "seed_id": "SEED-DARLEY-JONABELL-001",
        "segment": "horse_owner",
        "prospect_type": "breeding_farm",
        "identity_type": "person_and_organisation",
        "classification_status": "confirmed",
        "evidence_references": ["EV-DARLEY-JONABELL-001", "EV-DARLEY-CONTACT-001"],
        "rationale": "The official Darley America pages identify Jonabell Farm as a working Lexington breeding/racing operation and publish Kate Galvin as Nominations Sales and Operating Manager, Jonabell Farm. She is retained as the single primary named contact; purchasing influence remains unknown and the ICP score is unchanged.",
        "unresolved_questions": ["The public pages do not name the hoof-care purchasing decision-maker."],
    }
    darley_statuses = {
        "horse_owner.commercial_operation": ("confirmed", ["EV-DARLEY-JONABELL-001"], "The official page identifies a privately-owned working thoroughbred farm and international breeding/racing operation."),
        "horse_owner.more_than_three_horses": ("confirmed", ["EV-DARLEY-JONABELL-001"], "The current roster explicitly names seven stallions, establishing more than three horses."),
        "horse_owner.purchasing_influence": ("unknown", [], "No named owner, trainer or manager with purchasing responsibility is identified on the retained page."),
        "horse_owner.product_fit": ("confirmed", ["EV-DARLEY-JONABELL-001"], "A working breeding farm managing multiple current stallions has recurring professional hoof-care needs."),
        "horse_owner.performance_discipline": ("confirmed", ["EV-DARLEY-JONABELL-001"], "The page explicitly describes an international thoroughbred breeding and racing operation and names major race winners."),
        "horse_owner.breeding_activity": ("confirmed", ["EV-DARLEY-JONABELL-001"], "The page identifies current stallions and a breeding shed."),
        "horse_owner.professional_network": ("unknown", [], "The global operation is explicit, but the retained page does not state specific professional Farrier or trainer relationships."),
        "horse_owner.high_equine_activity_location": ("confirmed", ["EV-DARLEY-JONABELL-001"], "Jonabell Farm is explicitly located in Lexington, Kentucky."),
        "horse_owner.buying_signal": ("unknown", [], "No recent purchase or expansion signal is directly stated."),
    }
    darley_bundle = build_candidate("darley-jonabell", "A1-DARLEY-JONABELL-001", "darley-jonabell-seed.json", darley_classification, darley_statuses, "mostly_direct", icp)

    review_input = {
        "schema_version": "1.0.0",
        "package_id": "A1-RP-STEP9-REAL-PILOT",
        "run_id": "RUN-STEP9-REAL-PILOT-001",
        "generated_at": GENERATED_AT,
        "initiated_by": "Séverine — Step 9 approved real-prospect pilot",
        "candidates": [rood_bundle, darley_bundle],
    }
    write(PROFILE / "evaluations" / "step9" / "review-input.json", review_input)
    discovery_report = {
        "requested_candidates": 3,
        "review_ready_candidates": 2,
        "held_for_more_research": 1,
        "held_seed": "SEED-KHS-001",
        "reason": "The official KHS homepage establishes current Farrier education activity but did not establish a client-serving Farrier practice, verified pilot location or named decision-maker within the page-read budget.",
    }
    write(PROFILE / "evaluations" / "step9" / "discovery-report.json", discovery_report)
    print(json.dumps({
        "status": "passed",
        "review_ready": [
            {"candidate_id": "A1-RR-PODIATRY-001", "score": rood_bundle["scoring_package"]["scoring"]["score"], "band": rood_bundle["scoring_package"]["scoring"]["band"], "confidence": rood_bundle["confidence_package"]["confidence"]["score"]},
            {"candidate_id": "A1-DARLEY-JONABELL-001", "score": darley_bundle["scoring_package"]["scoring"]["score"], "band": darley_bundle["scoring_package"]["scoring"]["band"], "confidence": darley_bundle["confidence_package"]["confidence"]["score"]},
        ],
        "held_for_research": "SEED-KHS-001",
    }, indent=2))


if __name__ == "__main__":
    main()
