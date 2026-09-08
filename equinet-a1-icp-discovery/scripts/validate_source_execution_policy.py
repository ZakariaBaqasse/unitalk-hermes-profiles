#!/usr/bin/env python3
"""Dependency-free validation for the active A1 production source policy."""
from __future__ import annotations

import json
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[1]
SOURCE_PATH = PROFILE / "configurations/sources/approved-source-register-v1.yaml"
RUNTIME_PATH = PROFILE / "configurations/operations/a1-runtime-policy-v1.yaml"
ICP_PATH = PROFILE / "configurations/icp/equinet-icp-v1.yaml"
SCORING_PATH = PROFILE / "configurations/scoring/icp-scoring-model-v1.yaml"
ENRICHMENT_PATH = PROFILE / "configurations/evidence/public-website-enrichment-policy-v1.yaml"
LOCATION_PATH = PROFILE / "configurations/geography/location-resolution-v1.json"
PERSON_MANIFEST_PATH = PROFILE / "configurations/crm/twenty-person-field-manifest-v1.json"
POLL_TICKET = PROFILE / "runtime/n8n-poll-tickets/A1-20260902182623-B0A7B5.json"
STAGING_INDEX = PROFILE / "runtime/n8n-poll-tickets/two-lane-v1/final-staging-index.json"

SOURCE_PRIORITY_BLOCK = """  discovery_priority:
    farrier:
      - pdf.mad_barn_directory
      - integration.apify_google_maps_scraper
      - pdf.farrieriq
      - pdf.newhorse
      - pdf.best_of_lexington_farriers
      - pdf.horseprofinder
    horse_owner:
      - integration.apify_google_maps_scraper
      - pdf.horseprofinder
"""

RUNTIME_PRIORITY_BLOCK = """  farrier_priority:
    - pdf.mad_barn_directory
    - integration.apify_google_maps_scraper
    - pdf.farrieriq
    - pdf.newhorse
    - pdf.best_of_lexington_farriers
    - pdf.horseprofinder
  horse_owner_priority:
    - integration.apify_google_maps_scraper
    - pdf.horseprofinder
"""


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    source = SOURCE_PATH.read_text(encoding="utf-8")
    runtime = RUNTIME_PATH.read_text(encoding="utf-8")
    icp = ICP_PATH.read_text(encoding="utf-8")
    scoring = SCORING_PATH.read_text(encoding="utf-8")
    enrichment = ENRICHMENT_PATH.read_text(encoding="utf-8")
    location = json.loads(LOCATION_PATH.read_text(encoding="utf-8"))
    person_manifest = json.loads(PERSON_MANIFEST_PATH.read_text(encoding="utf-8"))
    ticket = json.loads(POLL_TICKET.read_text(encoding="utf-8"))
    staging = json.loads(STAGING_INDEX.read_text(encoding="utf-8"))

    require("registry_version: 2.0.0" in source, "source registry version must be 2.0.0", errors)
    require("policy_version: 4.2.0" in runtime, "runtime policy version must be 4.2.0", errors)
    require("verified_official_site_without_scoring_inputs: stage_domain_with_explicit_not_scored_assessment" in runtime, "runtime policy must retain verified domains for unscored staging", errors)
    require("config_version: 2.0.0" in icp, "ICP configuration version must be 2.0.0", errors)
    require("model_version: 1.1.0" in scoring, "scoring model version must be 1.1.0", errors)
    require("policy_version: 1.4.0" in enrichment, "website enrichment policy version must be 1.4.0", errors)
    require("website_verified_but_unscored: unscored_company_staging_with_verified_domain" in enrichment, "website enrichment handoff must retain verified unscored domains", errors)
    require("status: production_active_e2e_validated" in runtime, "runtime must be production active", errors)
    require("status: approved_for_production_configuration" in icp, "ICP configuration must be production approved", errors)
    require("status: approved_for_request_bounded_production_discovery" in source, "source register must be production approved", errors)

    require(location.get("approved_country_codes") == ["US", "AU", "NZ"], "location policy country order must be US, AU, NZ", errors)
    require(location.get("required_user_fields") == ["country", "region", "city"], "location policy must require country, region and city", errors)
    rules = location.get("rules", {})
    require(rules.get("defaults_allowed") is False, "location defaults must be prohibited", errors)
    require(rules.get("infer_country_from_city") is False, "country inference from city must be prohibited", errors)
    require(rules.get("infer_region_from_city") is False, "region inference from city must be prohibited", errors)
    require(rules.get("complete_unambiguous_input_requires_additional_confirmation") is False,
            "complete unambiguous location must not require redundant confirmation", errors)
    require("required_user_fields: [country, region, city]" in runtime, "runtime location preflight is incomplete", errors)
    require("approved_country_codes: [US, AU, NZ]" in runtime, "runtime country scope is incorrect", errors)
    require("included_country_codes: [US, AU, NZ]" in icp, "ICP country scope is incorrect", errors)

    require("max_candidates_per_source_per_run: null" in source, "source register still has a per-run cap", errors)
    require("max_candidates_per_source_per_day: null" in source, "source register still has a daily cap", errors)
    require("maximum_candidates_per_source_per_run: null" in runtime, "runtime still has a per-run cap", errors)
    require("maximum_candidates_per_source_per_day: null" in runtime, "runtime still has a daily cap", errors)
    require("source_request_limit: remaining_discovery_target" in source, "source register lacks remaining-target control", errors)
    require("source_request_limit: remaining_discovery_target" in runtime, "runtime lacks remaining-target control", errors)
    require("maximum_total_requested_candidates: 200" in source, "source total request ceiling must remain 200", errors)
    require("maximum_requested_candidates: 200" in runtime, "runtime total request ceiling must remain 200", errors)
    require("concurrency_per_source: 1" in source, "source concurrency must remain 1", errors)
    require("concurrency_per_source: 1" in runtime, "runtime source concurrency must remain 1", errors)
    require(SOURCE_PRIORITY_BLOCK in source, "source-register discovery priority is incorrect", errors)
    require(RUNTIME_PRIORITY_BLOCK in runtime, "runtime discovery priority is incorrect", errors)
    require("source_register_version: 2.0.0" in runtime, "runtime/source-register versions disagree", errors)
    require("maximum_active_discovery_runs: 1" in runtime, "single active discovery run control must remain", errors)
    require("allowed_objects: [companies,people]" in runtime, "runtime must permit Company plus linked Person staging", errors)
    require("people_write: permitted_when_linked_to_staged_company" in runtime, "linked Person write permission is missing", errors)
    require("uncertain_write_retry: prohibited" in runtime, "Person uncertain-write retry must be prohibited", errors)
    require(person_manifest.get("schema_version") == "a1.twenty-person-field-manifest.v1", "Person field manifest is invalid", errors)
    require("production_geography_capabilities:" in source, "source geography capability matrix is missing", errors)
    require("unsupported_source_action: skip_before_network_access" in source, "unsupported sources must skip before network access", errors)

    require(ticket.get("n8n_execution_status") == "success", "production acceptance ticket is not successful", errors)
    require(all(ticket.get(name) for name in ("result_claimed_at", "result_retrieved_at", "consumed_at", "delivered_at")),
            "production acceptance ticket lacks exactly-once markers", errors)
    require(staging.get("complete") is True, "production staging index is incomplete", errors)
    require(staging.get("total") == len(staging.get("dispositions", [])), "staging index total does not cover dispositions", errors)
    require(all(item.get("status") in {"staged", "possible_match", "sync_failed", "blocked_missing_company_name"}
                for item in staging.get("dispositions", [])), "staging index has a non-terminal disposition", errors)

    if errors:
        print("FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: A1 ICP 2.0.0, source policy 2.0.0, enrichment policy 1.4.0, scoring 1.1.0 and runtime policy 4.2.0 are consistent.")
    print("PASS: Company plus optional linked Person staging policy and verified field manifest are enabled.")
    print("PASS: production countries are US, Australia and New Zealand with no location defaults.")
    print("PASS: country, region and city are mandatory; codes resolve deterministically.")
    print("PASS: historical production acceptance evidence and its complete terminal staging coverage are present; this evidence predates the Person extension.")
    print("PASS: total request ceiling 200, concurrency 1 and access safeguards remain.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
