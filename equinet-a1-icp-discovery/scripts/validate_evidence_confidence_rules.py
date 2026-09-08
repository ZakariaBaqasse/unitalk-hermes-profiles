#!/usr/bin/env python3
"""Validate the Equinet A1 Evidence and Confidence Rules."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


PROFILE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = PROFILE_DIR / "configurations" / "evidence" / "evidence-confidence-rules-v1.yaml"
REQUIRED_DIMENSIONS = {
    "identity_certainty",
    "source_quality",
    "evidence_directness",
    "corroboration",
    "freshness",
    "completeness",
}
REQUIRED_CLAIMS = {
    "identity",
    "location",
    "public_professional_contact",
    "professional_activity",
    "certification_or_membership",
    "specialisation_or_discipline",
    "horse_count",
    "client_base_size",
    "purchasing_influence",
    "business_size",
    "recent_activity",
    "commercial_operation",
    "crm_status_or_exclusion",
}
REQUIRED_INVALIDATING_GATES = {
    "blocked_source_used",
    "no_evidence",
    "fabricated_or_untraceable_evidence",
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("Policy root must be a mapping.")
    return data


def validate_policy(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "policy_id", "policy_version", "status", "applies_to_profile", "candidate_schema_version",
        "icp_config_version", "enrichment_source_policy_version", "approval_record", "principles", "freshness_policy",
        "evidence_states",
        "source_tiers", "source_independence_rules", "claim_rules", "high_impact_claims",
        "corroboration_rules", "confidence_model", "confidence_stage_minimum_data", "confidence_assessment_input", "review_rules"
    }
    missing = sorted(required - set(data))
    if missing:
        errors.append(f"Missing top-level keys: {', '.join(missing)}")

    if data.get("policy_version") != "1.2.0":
        errors.append("policy_version must be 1.2.0.")
    if data.get("status") != "approved_for_production":
        errors.append("status must record production approval.")
    if data.get("applies_to_profile") != "equinet-a1-icp-discovery":
        errors.append("Policy must apply to equinet-a1-icp-discovery.")
    expected_versions = {
        "candidate_schema_version": "1.0.0",
        "icp_config_version": "2.0.0",
        "enrichment_source_policy_version": "1.3.0",
    }
    if any(data.get(key) != value for key, value in expected_versions.items()):
        errors.append("Policy must target Candidate Schema 1.0.0, ICP Configuration 2.0.0 and Enrichment Source Policy 1.3.0.")
    approval = data.get("approval_record", {})
    if approval.get("approved_by") != "Séverine" or len(approval.get("approved_decisions", [])) != 5:
        errors.append("approval_record must preserve Séverine's five retained evidence decisions.")
    freshness = data.get("freshness_policy", {})
    if freshness.get("current_official_business_website", {}).get("visible_publication_date_required") is not False:
        errors.append("Current official business websites must not require a visible publication date.")
    if freshness.get("undated_external_source", {}).get("time_sensitive_claim_treatment") is None:
        errors.append("Undated external sources must define time-sensitive claim treatment.")

    evidence_states = data.get("evidence_states", {})
    for state in ("direct_fact", "reasonable_inference", "contradictory_evidence", "unknown"):
        if state not in evidence_states:
            errors.append(f"Missing evidence state {state}.")
    if evidence_states.get("reasonable_inference", {}).get("may_confirm_mandatory_criterion") is not False:
        errors.append("Reasonable inference must not confirm a mandatory criterion.")

    claims = data.get("claim_rules", {})
    missing_claims = sorted(REQUIRED_CLAIMS - set(claims))
    if missing_claims:
        errors.append(f"Missing claim rules: {', '.join(missing_claims)}")
    for claim_name, rule in claims.items():
        if not rule.get("acceptable_tiers") or not rule.get("minimum_standard"):
            errors.append(f"Claim {claim_name} must define acceptable tiers and a minimum standard.")
        if not any(key in rule for key in ("max_age_days", "freshness")):
            errors.append(f"Claim {claim_name} must define max_age_days or freshness.")

    primary = data.get("source_tiers", {}).get("primary_business_source", {})
    if not primary.get("no_corroboration_required_for") or "authoritative" not in str(primary.get("default_reliability", "")):
        errors.append("Primary business websites must remain authoritative for explicitly published self-controlled facts.")
    purchasing = claims.get("purchasing_influence", {})
    title_policy = purchasing.get("job_title_policy", {})
    if purchasing.get("inference_allowed") != "role_based" or not title_policy.get("strong_decision_roles"):
        errors.append("Purchasing influence must preserve the approved role-title policy.")
    one_source_rule = data.get("corroboration_rules", {}).get("one_source_rule", {})
    if one_source_rule.get("confidence_cap_applies") is not False:
        errors.append("A single authoritative or primary business source must not be automatically capped at Medium.")
    stage_minimum = data.get("confidence_stage_minimum_data", {})
    not_required = set(stage_minimum.get("not_required_yet", []))
    if "scoring.status" not in not_required or "recommendation.next_action" not in not_required:
        errors.append("Confidence-stage minimum data must not require downstream scoring or recommendation fields.")
    if not stage_minimum.get("gate_rule"):
        errors.append("Confidence-stage minimum data must define its gate rule.")

    model = data.get("confidence_model", {})
    if model.get("method_version") != "evidence-confidence-1.0.0":
        errors.append("confidence method_version must be evidence-confidence-1.0.0.")
    dimensions = model.get("dimensions", {})
    if set(dimensions) != REQUIRED_DIMENSIONS:
        errors.append("Confidence model must contain exactly the six required dimensions.")
    max_total = 0
    for name, dimension in dimensions.items():
        maximum = dimension.get("max_points")
        levels = dimension.get("levels", {})
        if not isinstance(maximum, int) or maximum <= 0:
            errors.append(f"Dimension {name} has invalid max_points.")
            continue
        max_total += maximum
        if not levels or max(levels.values(), default=-1) != maximum or min(levels.values(), default=1) != 0:
            errors.append(f"Dimension {name} levels must include zero and its configured maximum.")
        if any(not isinstance(value, int) or value < 0 or value > maximum for value in levels.values()):
            errors.append(f"Dimension {name} contains out-of-range points.")
    if max_total != 100:
        errors.append(f"Confidence dimension maxima must total 100, received {max_total}.")

    bands = model.get("bands", {})
    expected_bands = {
        "high": {"minimum": 80, "maximum": 100},
        "medium": {"minimum": 60, "maximum": 79},
        "low": {"minimum": 0, "maximum": 59},
    }
    if bands != expected_bands:
        errors.append("Confidence bands must be High 80-100, Medium 60-79 and Low 0-59.")

    expected_caps = {
        "mandatory_claim_inference_only": 59,
        "unresolved_identity_conflict": 39,
        "critical_evidence_conflict": 39,
        "minimum_data_failed": 39,
    }
    caps = model.get("score_caps", {})
    if set(caps) != set(expected_caps):
        errors.append("Confidence caps must contain the four configured safety caps.")
    else:
        for key, expected in expected_caps.items():
            if caps[key].get("maximum_score") != expected:
                errors.append(f"Confidence cap {key} must be {expected}.")

    if set(model.get("invalidating_gates", {})) != REQUIRED_INVALIDATING_GATES:
        errors.append("Confidence invalidating gates are incomplete or unexpected.")

    assessment = data.get("confidence_assessment_input", {})
    if set(assessment.get("required_dimensions", [])) != REQUIRED_DIMENSIONS:
        errors.append("Assessment input dimensions do not match the confidence model.")
    required_gate_names = set(caps) | REQUIRED_INVALIDATING_GATES
    if set(assessment.get("required_gates", [])) != required_gate_names:
        errors.append("Assessment input gates do not match caps and invalidating gates.")

    principles_text = " ".join(str(item).lower() for item in data.get("principles", []))
    if "search snippets" not in principles_text or "discovery context" not in principles_text:
        errors.append("Search snippets and upstream discovery fields must remain context, not retained evidence.")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("policy", nargs="?", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args()
    try:
        data = load_yaml(args.policy)
    except Exception as exc:
        print(f"INVALID: {args.policy}\n- {exc}")
        return 1
    errors = validate_policy(data)
    if errors:
        print(f"INVALID: {args.policy}")
        for error in errors:
            print(f"- {error}")
        return 1
    model = data["confidence_model"]
    total = sum(item["max_points"] for item in model["dimensions"].values())
    print(f"VALID: {args.policy}")
    print(f"Claim rules: {len(data['claim_rules'])}")
    print(f"Confidence dimensions: {len(model['dimensions'])}")
    print(f"Maximum score: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
