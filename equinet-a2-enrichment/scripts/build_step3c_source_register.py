#!/usr/bin/env python3
"""Build the provisional Step 3C A2 source register."""

from __future__ import annotations

import csv
import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROFILE_ROOT / "foundations" / "contracts" / "sources"
JSON_PATH = ROOT / "a2-source-register-0.1.0-draft.1.json"
CSV_PATH = ROOT / "a2-source-register-0.1.0-draft.1.csv"

COMMON_AUDIT = ["actor_profile", "trigger", "timestamp", "source_id", "input_scope", "source_urls", "output_reference", "approval_state", "status", "retries", "usage_and_cost"]
COMMON_STOP = ["terms_or_robots_denial", "login_or_paywall", "captcha", "http_403", "http_429", "unexpected_personal_data", "scope_or_budget_limit"]


def source(source_id: str, name: str, source_type: str, url: str | None, purpose: str, business: str, rights: str, runtime: str, register: str, access: list[str], fields: list[str], prohibited: list[str], limits: dict, notes: list[str]) -> dict:
    return {
        "source_id": source_id,
        "name": name,
        "source_type": source_type,
        "canonical_url": url,
        "purpose": purpose,
        "business_approval": business,
        "source_rights_preflight": rights,
        "runtime_readiness": runtime,
        "register_status": register,
        "allowed_access_modes": access,
        "permitted_fields": fields,
        "prohibited_fields": prohibited,
        "limits": limits,
        "stop_conditions": COMMON_STOP,
        "audit_requirements": COMMON_AUDIT,
        "notes": notes,
    }


def build() -> dict:
    minimal_profile = ["person.full_name", "person.role_title", "organisation.business_name", "organisation.public_business_location", "person.public_profile_urls"]
    return {
        "register_id": "equinet-a2-source-register",
        "version": "0.1.0-draft.1",
        "status": "approved_unitalk_working_baseline_runtime_activation_pending",
        "profile": "equinet-a2-enrichment",
        "market_scope": "United States; pilot emphasis inherited from approved A1 handoff",
        "source_sequence": [
            "a1_approved_handoff",
            "hubspot_authoritative_records_when_connected",
            "equinet_authorized_first_party_data",
            "prospect_official_website",
            "linkedin_profile_search_actor_only_after_all_gates",
            "apify_email_search_provider_action_only_after_all_gates",
            "search_engine_discovery_only",
        ],
        "global_rules": {
            "a2_is_not_second_discovery_crawl": True,
            "reuse_a1_evidence_before_new_access": True,
            "new_access_requires_named_gap_conflict_verification_or_freshness_need": True,
            "website_check_required_for_each_candidate_when_an_official_site_exists": True,
            "business_approval_does_not_equal_source_rights_or_runtime_readiness": True,
            "public_professional_data_does_not_create_outreach_eligibility": True,
            "no_crm_write": True,
            "no_outreach": True,
            "no_additional_commercial_enrichment_provider_selected": True,
        },
        "sources": [
            source("a1_approved_handoff", "Approved A1-to-A2 handoff", "internal_structured_handoff", None, "Reuse approved identity, contacts, evidence and limitations.", "approved", "approved_internal_contract", "manual_fixture_ready_durable_integration_pending", "approved", ["structured_read"], ["all approved handoff fields"], ["mutation of A1 snapshot", "recollection without a named gap"], {"max_handoffs_per_record": 1}, ["Primary starting source for every A2 record."]),
            source("hubspot_authoritative_records", "HubSpot authoritative records", "crm", "https://www.hubspot.com/", "Read authoritative customer, Deal, consent, suppression, owner and lifecycle state.", "approved_system_of_record", "oauth_and_source_permissions_required", "integration_pending", "conditional", ["approved_read_only_api"], ["approved Contact, Company and Deal properties"], ["write", "unscoped export", "cross-business-unit access"], {"read_scope": "least_privilege", "writes": 0}, ["Metadata snapshots received; live OAuth and records unavailable."]),
            source("equinet_authorized_first_party_data", "Equinet-authorised files or app records", "first_party", None, "Use client-supplied business facts for named fields.", "conditional_per_asset", "asset_owner_permission_required", "manual_intake_available", "conditional", ["approved_file_or_export"], ["explicitly authorised fields"], ["unapproved files", "unscoped Mustad-global data"], {"approval_per_asset": True}, ["Record asset owner, approval and extraction scope."]),
            source("prospect_official_website", "Prospect official business website", "prospect_owned_website", None, "Check every retained candidate for identity, role, professional contacts and approved field gaps.", "approved_by_equinet", "per_domain_terms_and_robots_preflight", "runtime_policy_pending", "conditional", ["bounded_public_web_read"], ["business name", "current professional role", "published professional email", "published business phone", "business location", "services", "disciplines", "service area", "credentials claimed by the business", "stable or farm type", "explicit horse count", "dated professional activity", "public professional profile URLs"], ["login-gated data", "private personal data", "inferred email patterns", "inferred horse count", "named client identities"], {"max_pages_per_candidate": 5, "max_retry_per_failed_url": 1, "concurrency": 1, "required_pages": ["home_or_primary", "about_or_team_when_available", "services_when_available", "contact_or_location_when_available"]}, ["If no official site is located, record not_found; do not substitute an unverified directory as the official site."]),
            source("equinet_representative_confirmation", "Recorded Equinet representative confirmation", "first_party_human", None, "Record authorised corrections and business context.", "approved_for_recorded_review", "authorised_reviewer_required", "manual_available", "approved", ["recorded_human_confirmation"], ["confirmed business facts", "documented correction"], ["unattributed statement", "outreach consent inference"], {"reviewer_required": True}, ["Must include actor and timestamp."]),
            source("official_professional_registry", "Additional official professional associations and registries", "official_registry", None, "No additional direct A2 registry access is required beyond evidence already collected by A1.", "not_in_scope_except_a1_handoff_reuse", "not_applicable_until_scope_changes", "not_configured", "not_selected", [], [], ["new registry access", "member-only data", "bulk extraction"], {"new_source_calls": 0}, ["Séverine confirmed that A2 has no additional registry or association to visit at this stage."]),
            source("a1_directory_evidence_reuse", "A1 directory evidence reuse", "upstream_evidence", None, "Reuse approved A1 directory evidence already carried in the handoff.", "approved_for_reuse_only", "inherits_original_evidence_scope", "available_through_handoff", "approved", ["handoff_evidence_reuse"], ["fields already present in the A1 evidence item"], ["new directory crawl", "broader A2 extraction purpose"], {"new_source_calls": 0}, ["A1 source approval does not authorise new A2 access."]),
            source("apify_harvestapi_linkedin_profile_search", "HarvestAPI LinkedIn Profile Search Scraper", "apify_community_actor", "https://apify.com/harvestapi/linkedin-profile-search", "Find or verify a minimum current professional role and company match after the official-site check.", "approved_by_equinet_for_a2_business_purpose", "blocked_pending_linkedin_rights_and_harvestapi_vendor_review", "account_connector_budget_and_build_pending", "conditional", ["apify_actor_api_after_all_gates"], minimal_profile, ["personal email", "phone or mobile", "full career history", "education", "skills", "recommendations", "posts", "followers or connections counts", "photos", "personal interests"], {"trigger": "named_role_gap_after_official_website_check", "profile_scraper_mode": "minimum_fields_only_then_output_review", "take_pages": 1, "max_items_per_candidate": 5, "max_retained_contacts_per_candidate": 3, "automatic_query_segmentation": False, "concurrency": 1, "daily_cost_cap_usd": None}, ["Séverine confirmed the gap-only trigger.", "The minimum profile field allowlist is approved as a starting point and will be reviewed against actual Actor output.", "Apify currently lists pay-per-event pricing.", "The Actor is maintained by HarvestAPI and is treated as a Community Actor.", "Business approval does not resolve target-platform rights, vendor governance, retention or runtime readiness."]),
            source("apify_harvestapi_email_search", "HarvestAPI independent email search via LinkedIn Profile Search Actor", "commercial_email_search", "https://apify.com/harvestapi/linkedin-profile-search", "Search for a professional email for a selected matched profile after the role/company match.", "approved_by_equinet_for_a2_business_purpose", "blocked_pending_linkedin_rights_email_data_rights_and_harvestapi_vendor_review", "account_connector_budget_and_build_pending", "conditional", ["apify_actor_full_plus_email_after_all_gates"], ["professional email", "email verification result", "provider provenance", "verification timestamp"], ["personal email retention", "mislabeling the email as LinkedIn-sourced", "outreach consent inference", "automatic send"], {"trigger": "selected_profile_after_role_company_match", "max_email_searches_per_candidate": 3, "daily_cost_cap_usd": None, "concurrency": 1}, ["The Actor documentation states that email search is independent from LinkedIn profile extraction.", "Email provenance must identify the independent search method.", "Only professional email is retained by default.", "Deliverability verification does not create consent."]),
            source("search_engine_discovery", "Search index", "search_discovery", None, "Locate an official website when the A1 handoff lacks a usable URL.", "approved_by_equinet_for_official_site_discovery", "standard_search_terms_apply", "tool_available_not_profile_activated", "conditional", ["search_results_discovery_only"], ["destination URL", "page title"], ["search snippet as retained evidence", "bulk person data"], {"max_queries_per_candidate": 3}, ["Only destination pages may become evidence."]),
            source("commercial_enrichment_provider", "Commercial enrichment provider", "commercial_provider", None, "Future field-specific enrichment or verification after Equinet completes testing.", "not_selected", "provider_dpa_and_data_rights_pending", "not_connected", "integration_pending", [], [], ["all live Mustad or Equinet data until approval"], {"providers_under_consideration": ["Apollo", "Clay"], "budget_cap_usd": None}, ["No paid enrichment provider is currently confirmed."]),
            source("other_social_platform_automation", "Other social-platform automation", "social_platform", None, "No approved A2 purpose at this stage.", "not_approved", "platform_permission_required", "not_connected", "blocked", [], [], ["automated Facebook access", "automated Instagram access", "social graph extraction", "private profile data"], {"calls": 0}, ["Manual or official API proposals require a later explicit decision."]),
        ],
        "open_activation_inputs": [
            "Provide the authorised Apify workspace/account, credential route, pinned Actor build and runtime owner.",
            "Approve an Apify spend or event cap and consumption owner.",
            "Provide LinkedIn automated-use permission, an approved API route or a documented legal/commercial exception.",
            "Complete HarvestAPI Community Actor privacy, security, retention, deletion and subprocessor due diligence.",
            "Confirm raw Actor dataset retention/deletion handling.",
            "Confirm whether a personal email returned by the independent email-search process must always be discarded; Unitalk default is discard.",
            "Review a bounded Actor sample output before expanding the minimum profile field allowlist.",
        ],
    }


def main() -> None:
    register = build()
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    columns = ["source_id", "name", "source_type", "canonical_url", "business_approval", "source_rights_preflight", "runtime_readiness", "register_status", "purpose", "allowed_access_modes", "permitted_fields", "prohibited_fields", "limits", "notes"]
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for item in register["sources"]:
            row = dict(item)
            for key in ["allowed_access_modes", "permitted_fields", "prohibited_fields", "limits", "notes"]:
                row[key] = json.dumps(row[key], ensure_ascii=False, separators=(",", ":"))
            row.pop("stop_conditions")
            row.pop("audit_requirements")
            writer.writerow({key: row.get(key) for key in columns})
    print(json.dumps({"register": str(JSON_PATH), "csv": str(CSV_PATH), "version": register["version"], "source_count": len(register["sources"])}, indent=2))


if __name__ == "__main__":
    main()
