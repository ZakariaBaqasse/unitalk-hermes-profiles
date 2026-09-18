#!/usr/bin/env python3
"""Build the provisional Step 3D evidence and confidence policy."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROFILE_ROOT / "foundations" / "contracts" / "evidence"
POLICY = ROOT / "a2-evidence-verification-confidence-freshness-policy-0.1.0-draft.1.json"
FIXTURES = PROFILE_ROOT / "evaluations" / "step3d" / "fixtures"
SOURCE_REGISTER = PROFILE_ROOT / "foundations" / "contracts" / "sources" / "a2-source-register-0.1.0-draft.1.json"
FIELD_CATALOGUE = PROFILE_ROOT / "foundations" / "contracts" / "business" / "a2-business-field-catalogue-0.1.0-draft.1.json"
STATE_MODEL = PROFILE_ROOT / "foundations" / "contracts" / "a2-state-model-0.1.0.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_policy() -> dict:
    return {
        "policy_id": "equinet-a2-evidence-verification-confidence-freshness",
        "version": "0.1.0-draft.1",
        "status": "approved_by_unitalk_as_working_baseline_pending_equinet_confirmation",
        "profile": "equinet-a2-enrichment",
        "unitalk_approval": {
            "approver": "Séverine, Unitalk Operations",
            "approved_at": "2026-08-26T18:53:52Z",
            "scope": "decisions_3D_1_through_3D_10_and_protected_SOUL_sync"
        },
        "dependencies": [
            {"path": str(SOURCE_REGISTER.relative_to(PROFILE_ROOT)), "sha256": sha256(SOURCE_REGISTER)},
            {"path": str(FIELD_CATALOGUE.relative_to(PROFILE_ROOT)), "sha256": sha256(FIELD_CATALOGUE)},
            {"path": str(STATE_MODEL.relative_to(PROFILE_ROOT)), "sha256": sha256(STATE_MODEL)},
        ],
        "principles": {
            "confidence_is_not_icp_score": True,
            "a2_never_calculates_a1_score": True,
            "unknown_is_not_negative_or_fact": True,
            "blocked_source_cannot_support_a_claim": True,
            "search_snippet_is_discovery_only": True,
            "professional_contact_does_not_create_outreach_consent": True,
            "a1_evidence_keeps_original_provenance_and_confidence": True,
            "official_website_can_confirm_explicit_self_controlled_fact_without_visible_date": True,
        },
        "confidence_dimensions": {
            "identity_match": {"maximum": 20, "levels": {"exact": 20, "probable": 10, "unresolved": 0}},
            "source_authority": {"maximum": 20, "levels": {"authoritative_system": 20, "authorised_first_party": 20, "official_business_website": 18, "official_registry": 18, "apify_linkedin_profile": 12, "apify_email_search": 12, "reused_a1_directory_evidence": 10, "search_discovery": 0, "blocked_or_unverified": 0}},
            "claim_directness": {"maximum": 20, "levels": {"direct_fact": 20, "reasonable_inference": 10, "contradictory_evidence": 0}},
            "freshness": {"maximum": 20, "levels": {"current": 20, "current_official_undated": 18, "undated_external": 8, "stale": 0, "not_applicable": 20, "error": 0}},
            "corroboration": {"maximum": 10, "levels": {"authoritative_or_primary_sufficient": 10, "two_independent_sources": 10, "one_secondary_source": 5, "none": 0}},
            "consistency": {"maximum": 10, "levels": {"no_conflict": 10, "possible_conflict": 5, "material_conflict": 0}},
        },
        "confidence_bands": [
            {"level": "high", "minimum": 80, "maximum": 100},
            {"level": "medium", "minimum": 60, "maximum": 79},
            {"level": "low", "minimum": 0, "maximum": 59},
        ],
        "caps": [
            {"condition": "identity_match_unresolved", "maximum_score": 39},
            {"condition": "material_conflict", "maximum_score": 39},
            {"condition": "required_claim_supported_only_by_reasonable_inference", "maximum_score": 59},
            {"condition": "time_sensitive_claim_is_stale", "maximum_score": 59},
            {"condition": "source_rights_or_runtime_gate_not_passed", "maximum_score": 0},
        ],
        "verification_rules": {
            "verified": "High confidence, direct fact, exact identity, permitted source, applicable freshness passed and no material conflict.",
            "partially_verified": "Medium confidence or a usable direct fact with a documented freshness, corroboration or identity limitation.",
            "unverified": "Low confidence or evidence insufficient for the proposed value.",
            "contradicted": "Material permitted evidence conflicts with the proposed or baseline value.",
            "not_applicable": "The field does not apply under the approved package or documented fallback.",
            "error": "Deterministic verification failed technically.",
        },
        "source_rules": {
            "a1_approved_handoff": {"authority": "preserve_inherited", "freshness": "preserve_inherited", "usable_when": "handoff validation passes"},
            "hubspot_authoritative_records": {"authority": "authoritative_system", "usable_when": "read-only connection and source permissions pass"},
            "equinet_authorized_first_party_data": {"authority": "authorised_first_party", "usable_when": "asset approval and actor are recorded"},
            "prospect_official_website": {"authority": "official_business_website", "usable_when": "per-domain preflight passes", "undated_self_controlled_fact": "current_official_undated"},
            "a1_directory_evidence_reuse": {"authority": "reused_a1_directory_evidence", "usable_when": "original evidence remains approved and applicable"},
            "apify_harvestapi_linkedin_profile_search": {"authority": "apify_linkedin_profile", "usable_when": "all rights, vendor and runtime gates pass", "current_status": "blocked"},
            "apify_harvestapi_email_search": {"authority": "apify_email_search", "usable_when": "all rights, vendor, privacy, budget and runtime gates pass", "current_status": "blocked", "email_provenance": "independent_provider_search_not_linkedin"},
            "search_engine_discovery": {"authority": "search_discovery", "usable_when": "destination discovery only", "retained_evidence": False},
        },
        "field_freshness_days": {
            "person.role_title": 180,
            "person.business_email": 180,
            "person.personal_email_candidate": 180,
            "person.business_phone": 180,
            "organisation.business_email": 180,
            "organisation.business_phone": 180,
            "person.professional_status": 365,
            "person.certifications": 365,
            "person.professional_credential": 365,
            "organisation.public_business_location": 365,
            "organisation.service_area": 365,
            "organisation.horse_count": 365,
            "organisation.stable_type": 730,
            "organisation.disciplines": 730,
            "organisation.breeds": 730,
            "person.recent_professional_activity": 365,
            "person.public_profile_urls": 365
        },
        "conflict_policy": {
            "authoritative_system_overrides_non_authoritative_source": "propose_authoritative_value_but_preserve_conflict_and_require_review_if_material",
            "official_website_vs_linkedin_current_role": "material_conflict_hold",
            "same_domain_pages_are_independent": False,
            "syndicated_or_copied_content_is_independent": False,
            "material_conflict_blocks_verified_status": True,
            "resolved_conflict_requires_reviewer_and_reason": True,
        },
        "email_specific_rules": {
            "officially_published_professional_email": "may_be_verified_from_one_exact_official_source",
            "apify_email_search": "requires_exact_identity_and_company_match_plus_provider_verification",
            "personal_email": "held_for_human_privacy_review_no_operational_use_before_approval",
            "deliverability_does_not_create_consent": True,
            "email_source_must_not_be_mislabeled_as_linkedin": True,
        },
        "outcomes": {
            "required_field_unsatisfied": {"field_quality": "gap", "record_quality": "incomplete", "automatic_rejection": False},
            "optional_field_unsatisfied": {"field_quality": "gap", "record_quality_change": "none_by_itself"},
            "material_conflict": {"field_quality": "conflict", "record_quality": "conflict", "workflow": "held"},
            "verified_new_a1_material_evidence": {"action": "create_requalification_signal", "a2_score_calculation": False},
        },
        "open_confirmations": [
            "Approve or correct the proposed field freshness windows.",
            "Confirm whether personal email must always be discarded; Unitalk default is discard.",
            "Confirm which dated professional activities are commercially relevant.",
            "Complete source-specific rights and runtime gates before evidence from a conditional source is usable.",
        ],
    }


def evidence_fixture(name: str, source_id: str, claim_key: str, identity: str, directness: str, freshness: str, corroboration: str, consistency: str, source_gate_passed: bool, required_claim: bool, expected_level: str, expected_verification: str, expected_score: int) -> dict:
    return {
        "name": name, "source_id": source_id, "claim_key": claim_key, "identity_match": identity,
        "claim_directness": directness, "freshness": freshness, "corroboration": corroboration,
        "consistency": consistency, "source_gate_passed": source_gate_passed, "required_claim": required_claim,
        "expected": {"confidence_score": expected_score, "confidence_level": expected_level, "verification_status": expected_verification},
    }


def build_fixtures() -> None:
    cases = [
        evidence_fixture("official_site_current_role", "prospect_official_website", "person.role_title", "exact", "direct_fact", "current_official_undated", "authoritative_or_primary_sufficient", "no_conflict", True, True, "high", "verified", 96),
        evidence_fixture("official_site_business_email", "prospect_official_website", "person.business_email", "exact", "direct_fact", "current", "authoritative_or_primary_sufficient", "no_conflict", True, True, "high", "verified", 98),
        evidence_fixture("apify_profile_runtime_blocked", "apify_harvestapi_linkedin_profile_search", "person.role_title", "exact", "direct_fact", "current", "one_secondary_source", "no_conflict", False, True, "low", "unverified", 0),
        evidence_fixture("apify_email_verified_after_future_gate", "apify_harvestapi_email_search", "person.business_email", "exact", "direct_fact", "current", "one_secondary_source", "no_conflict", True, True, "high", "verified", 87),
        evidence_fixture("undated_secondary_role", "a1_directory_evidence_reuse", "person.role_title", "probable", "direct_fact", "undated_external", "one_secondary_source", "no_conflict", True, True, "medium", "partially_verified", 63),
        evidence_fixture("inference_only_required", "prospect_official_website", "organisation.service_area", "exact", "reasonable_inference", "current_official_undated", "authoritative_or_primary_sufficient", "no_conflict", True, True, "low", "unverified", 59),
        evidence_fixture("material_role_conflict", "prospect_official_website", "person.role_title", "exact", "direct_fact", "current", "two_independent_sources", "material_conflict", True, True, "low", "contradicted", 39),
        evidence_fixture("stale_professional_status", "prospect_official_website", "person.professional_status", "exact", "direct_fact", "stale", "authoritative_or_primary_sufficient", "no_conflict", True, True, "low", "unverified", 59),
        evidence_fixture("search_snippet_discovery_only", "search_engine_discovery", "organisation.website", "probable", "direct_fact", "current", "none", "no_conflict", True, False, "low", "unverified", 0),
        evidence_fixture("unresolved_identity", "prospect_official_website", "organisation.business_name", "unresolved", "direct_fact", "current", "authoritative_or_primary_sufficient", "no_conflict", True, True, "low", "unverified", 39),
    ]
    FIXTURES.mkdir(parents=True, exist_ok=True)
    write(FIXTURES / "evidence-cases.json", {"version": "0.1.0-draft.1", "cases": cases})


def main() -> None:
    policy = build_policy()
    write(POLICY, policy)
    build_fixtures()
    print(json.dumps({"policy": str(POLICY), "version": policy["version"], "fixture_count": len(json.loads((FIXTURES / "evidence-cases.json").read_text())["cases"])}, indent=2))


if __name__ == "__main__":
    main()
