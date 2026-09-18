#!/usr/bin/env python3
"""Validate the Step 3C draft A2 source register."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROFILE_ROOT / "foundations" / "contracts" / "sources"
REGISTER = ROOT / "a2-source-register-0.1.0-draft.1.json"
CSV_PATH = ROOT / "a2-source-register-0.1.0-draft.1.csv"
CONTRACT = PROFILE_ROOT / "foundations" / "A2-SOURCE-REGISTER.md"
EVAL = PROFILE_ROOT / "evaluations" / "step3c"
REVIEW = EVAL / "A2-SOURCE-REGISTER-REVIEW.md"
OUTPUT = EVAL / "technical-validation.json"
MANIFEST = EVAL / "step3c-draft-package-manifest.json"
LANGUAGE = PROFILE_ROOT / "evaluations" / "foundation-clarifications" / "language-audit.json"
EXPECTED_IDS = {
    "a1_approved_handoff", "hubspot_authoritative_records", "equinet_authorized_first_party_data",
    "prospect_official_website", "equinet_representative_confirmation", "official_professional_registry",
    "a1_directory_evidence_reuse", "apify_harvestapi_linkedin_profile_search", "apify_harvestapi_email_search", "search_engine_discovery",
    "commercial_enrichment_provider", "other_social_platform_automation",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(register: dict) -> list[str]:
    errors = []
    sources = register.get("sources", [])
    ids = [item.get("source_id") for item in sources]
    if set(ids) != EXPECTED_IDS or len(ids) != len(set(ids)):
        errors.append("source inventory mismatch or duplicate source_id")
    by_id = {item["source_id"]: item for item in sources}
    website = by_id.get("prospect_official_website", {})
    if website.get("business_approval") != "approved_by_equinet":
        errors.append("official website business approval is not recorded")
    if website.get("limits", {}).get("max_pages_per_candidate") != 5 or website.get("limits", {}).get("max_retry_per_failed_url") != 1:
        errors.append("official website bounded limits mismatch")
    if "terms_or_robots_denial" not in website.get("stop_conditions", []) or "login_or_paywall" not in website.get("stop_conditions", []):
        errors.append("official website stop conditions incomplete")

    actor = by_id.get("apify_harvestapi_linkedin_profile_search", {})
    if actor.get("canonical_url") != "https://apify.com/harvestapi/linkedin-profile-search":
        errors.append("Apify Actor URL mismatch")
    if actor.get("business_approval") != "approved_by_equinet_for_a2_business_purpose":
        errors.append("Apify business approval is not recorded")
    if actor.get("source_rights_preflight") != "blocked_pending_linkedin_rights_and_harvestapi_vendor_review":
        errors.append("Apify rights gate was weakened")
    if actor.get("runtime_readiness") != "account_connector_budget_and_build_pending" or actor.get("register_status") != "conditional":
        errors.append("Apify runtime status is overstated")
    prohibited = set(actor.get("prohibited_fields", []))
    for value in ["personal email", "phone or mobile", "posts", "followers or connections counts"]:
        if value not in prohibited:
            errors.append(f"Apify prohibited field missing: {value}")
    limits = actor.get("limits", {})
    expected_limits = {"take_pages": 1, "max_items_per_candidate": 5, "max_retained_contacts_per_candidate": 3, "automatic_query_segmentation": False, "concurrency": 1}
    for key, expected in expected_limits.items():
        if limits.get(key) != expected:
            errors.append(f"Apify limit mismatch: {key}")
    if limits.get("daily_cost_cap_usd") is not None:
        errors.append("Apify daily cost cap must remain pending rather than invented")

    email_search = by_id.get("apify_harvestapi_email_search", {})
    if email_search.get("business_approval") != "approved_by_equinet_for_a2_business_purpose":
        errors.append("Apify email-search business approval is not recorded")
    if email_search.get("register_status") != "conditional" or not str(email_search.get("source_rights_preflight", "")).startswith("blocked_pending_"):
        errors.append("Apify email-search activation gate was weakened")
    if set(email_search.get("permitted_fields", [])) != {"professional email", "email verification result", "provider provenance", "verification timestamp"}:
        errors.append("Apify email-search permitted fields mismatch")
    for value in ["personal email retention", "mislabeling the email as LinkedIn-sourced", "outreach consent inference", "automatic send"]:
        if value not in email_search.get("prohibited_fields", []):
            errors.append(f"Apify email-search prohibition missing: {value}")
    if email_search.get("limits", {}).get("daily_cost_cap_usd") is not None:
        errors.append("Apify email-search cost cap must remain pending rather than invented")

    registry = by_id.get("official_professional_registry", {})
    if registry.get("register_status") != "not_selected" or registry.get("limits", {}).get("new_source_calls") != 0:
        errors.append("additional professional registries must remain not selected")
    search = by_id.get("search_engine_discovery", {})
    if search.get("business_approval") != "approved_by_equinet_for_official_site_discovery":
        errors.append("search-engine official-site discovery approval is not recorded")

    provider = by_id.get("commercial_enrichment_provider", {})
    if provider.get("business_approval") != "not_selected" or provider.get("runtime_readiness") != "not_connected":
        errors.append("commercial provider status is overstated")
    if set(provider.get("limits", {}).get("providers_under_consideration", [])) != {"Apollo", "Clay"}:
        errors.append("commercial-provider pending list mismatch")
    if by_id.get("a1_directory_evidence_reuse", {}).get("limits", {}).get("new_source_calls") != 0:
        errors.append("A1 directory reuse source permits a new crawl")
    if by_id.get("other_social_platform_automation", {}).get("register_status") != "blocked":
        errors.append("other social-platform automation must remain blocked")
    rules = register.get("global_rules", {})
    for key in ["a2_is_not_second_discovery_crawl", "reuse_a1_evidence_before_new_access", "new_access_requires_named_gap_conflict_verification_or_freshness_need", "website_check_required_for_each_candidate_when_an_official_site_exists", "business_approval_does_not_equal_source_rights_or_runtime_readiness", "public_professional_data_does_not_create_outreach_eligibility", "no_crm_write", "no_outreach", "no_additional_commercial_enrichment_provider_selected"]:
        if rules.get(key) is not True:
            errors.append(f"global source rule missing: {key}")
    for item in sources:
        if not item.get("stop_conditions") or not item.get("audit_requirements"):
            errors.append(f"source lacks stop/audit controls: {item.get('source_id')}")
    return errors


def negatives(register: dict) -> list[dict]:
    cases = []
    def run(name, expected, fn):
        value = copy.deepcopy(register); fn(value); errs = validate(value)
        cases.append({"name": name, "expected_error": expected, "errors": errs, "passed": any(expected in e for e in errs)})
    def src(value, sid): return next(item for item in value["sources"] if item["source_id"] == sid)
    run("duplicate_source", "inventory mismatch", lambda v: v["sources"].append(copy.deepcopy(v["sources"][0])))
    run("website_not_approved", "website business approval", lambda v: src(v, "prospect_official_website").update(business_approval="not_approved"))
    run("website_unbounded", "website bounded limits", lambda v: src(v, "prospect_official_website")["limits"].update(max_pages_per_candidate=1000))
    run("apify_url_changed", "Actor URL mismatch", lambda v: src(v, "apify_harvestapi_linkedin_profile_search").update(canonical_url="https://example.com/actor"))
    run("apify_rights_bypassed", "rights gate was weakened", lambda v: src(v, "apify_harvestapi_linkedin_profile_search").update(source_rights_preflight="approved"))
    run("apify_runtime_overstated", "runtime status is overstated", lambda v: src(v, "apify_harvestapi_linkedin_profile_search").update(runtime_readiness="active"))
    run("profile_personal_email_enabled", "prohibited field missing", lambda v: src(v, "apify_harvestapi_linkedin_profile_search")["prohibited_fields"].remove("personal email"))
    run("apify_segmentation_enabled", "Apify limit mismatch", lambda v: src(v, "apify_harvestapi_linkedin_profile_search")["limits"].update(automatic_query_segmentation=True))
    run("provider_selected_early", "provider status is overstated", lambda v: src(v, "commercial_enrichment_provider").update(business_approval="approved"))
    run("a1_directory_recrawl", "permits a new crawl", lambda v: src(v, "a1_directory_evidence_reuse")["limits"].update(new_source_calls=1))
    run("email_source_removed", "inventory mismatch", lambda v: v["sources"].remove(src(v, "apify_harvestapi_email_search")))
    run("personal_email_retention_enabled", "email-search prohibition missing", lambda v: src(v, "apify_harvestapi_email_search")["prohibited_fields"].remove("personal email retention"))
    run("extra_registry_enabled", "registries must remain not selected", lambda v: src(v, "official_professional_registry").update(register_status="conditional"))
    return cases


def render(register: dict) -> None:
    rows = "\n".join(f"| `{s['source_id']}` | {s['business_approval']} | {s['source_rights_preflight']} | {s['runtime_readiness']} | {s['register_status']} |" for s in register["sources"])
    contract = f"""# Equinet A2 Source Register

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED UNITALK WORKING BASELINE — RUNTIME ACTIVATION PENDING`  
**Decision timestamp:** `2026-08-26T17:58:25Z`  
**Profile:** `equinet-a2-enrichment`  
**Step:** `3C — A2 Source Register`

## 1. Operating sequence

A2 reuses the approved A1 handoff first. It checks the prospect's official website when one exists. New external access is limited to a named gap, conflict, verification requirement or freshness issue. A2 is not a second discovery crawl.

## 2. Source status matrix

| Source ID | Business approval | Rights preflight | Runtime readiness | Register status |
|---|---|---|---|---|
{rows}

## 3. Official website profile

For each retained Farrier or Horse Owner candidate, check the official site when it exists. Use at most five pages: primary page, About/Team, Services, Contact/Location and one relevant dated page when available. Allow at most one targeted retry per failed URL. Stop on terms/robots denial, login/paywall, CAPTCHA, 403, 429, unexpected personal data or scope/budget limit.

## 4. Apify LinkedIn Profile Search profile

- Actor: `harvestapi/linkedin-profile-search`.
- Equinet business approval: recorded.
- Confirmed trigger: only for a named role/contact gap after the official-site check.
- Starting retained fields: name, current title, current company, location and profile URL; review the bounded test output before expanding the allowlist.
- Independent email-search mode: approved for professional-email search, subject to the separate rights, vendor, budget, retention and runtime gates.
- Full history, education, skills, posts, counts, photos and personal interests: prohibited.
- Proposed technical cap: one page, five returned profiles and three retained contacts per candidate; concurrency one; no automatic query segmentation.
- Spend cap: pending.

The Actor remains `blocked_pending_linkedin_rights_and_harvestapi_vendor_review`. Equinet business approval does not by itself establish LinkedIn automated-use rights, approve HarvestAPI as a data processor or activate the runtime connector.

## 5. Paid-provider boundary

Apollo, Clay and other commercial enrichment providers remain unselected and unconnected. No live Equinet data or spend is authorised.

## 6. Information still required before activation

1. Provide the authorised Apify workspace/account, credential route and pinned Actor build.
2. Approve an Apify cost/event cap and consumption owner.
3. Provide approved LinkedIn automated-use rights, API route or documented legal/commercial exception.
4. Complete HarvestAPI privacy, security, retention, deletion and subprocessor review.
5. Confirm raw Actor dataset retention/deletion handling.
6. Confirm whether a personal email returned by the independent search must always be discarded; the Unitalk default is discard.
7. Review a bounded Actor sample output before expanding the minimum profile field allowlist.

## 7. Current conclusion

The source register can be reviewed as a draft. Runtime activation is not approved. No source call, provider call, CRM action or outreach action is authorised by this document.
"""
    CONTRACT.write_text(contract, encoding="utf-8")
    review = """# Decision Review — Step 3C A2 Source Register

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED AS UNITALK WORKING BASELINE — RUNTIME ACTIVATION PENDING`
**Decision timestamp:** `2026-08-26T17:58:25Z`

## Decisions already captured

- Every retained Farrier and Horse Owner should have its official website checked when one exists.
- Equinet has approved the business use of `harvestapi/linkedin-profile-search` for A2.
- The Actor runs only after an official-site role/contact gap.
- Independent professional-email search through the Actor is included as a separately governed provider action.
- Search-engine discovery is permitted only to locate the official website.
- No additional A2 registry or association is selected beyond A1 evidence reuse.
- Apollo, Clay and other paid enrichment providers are not selected.

## Unitalk safeguards proposed

1. Reuse A1 evidence before new access.
2. Use the official website before LinkedIn.
3. Trigger the Apify Actor only for a named role/contact gap.
4. Start with name, current title, current company, location and profile URL, then review a bounded output before expanding the allowlist.
5. Treat email search as a separate provider action; retain professional email only by default and never label it as LinkedIn-sourced.
6. Limit each candidate to one search page, five returned profiles, three retained contacts and at most three email searches.
7. Keep concurrency at one and automatic query segmentation disabled.
8. Keep runtime blocked until rights, vendor, account, build, budget, retention and audit gates pass.
9. Keep Apollo, Clay and other enrichment providers unselected and unconnected.

## Decision scope

This approval establishes the Unitalk working baseline, not runtime activation. Rights, vendor, account, budget, retention and integration gates remain mandatory.
"""
    REVIEW.write_text(review, encoding="utf-8")


def main() -> int:
    register = load(REGISTER)
    errors = validate(register)
    negative = negatives(register)
    if any(not item["passed"] for item in negative):
        errors.append("one or more negative regressions failed")
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    csv_checks = {
        "row_count": len(rows) == len(register["sources"]),
        "source_order": [row["source_id"] for row in rows] == [item["source_id"] for item in register["sources"]],
        "statuses": [row["register_status"] for row in rows] == [item["register_status"] for item in register["sources"]],
    }
    if not all(csv_checks.values()):
        errors.append("CSV fidelity failed")
    EVAL.mkdir(parents=True, exist_ok=True)
    render(register)
    language = load(LANGUAGE)
    if language.get("pass") is not True:
        errors.append("language audit failed")
    result = {
        "step": "3C", "version": register["version"], "approval_state": "approved_unitalk_working_baseline_runtime_activation_pending",
        "register": {"path": str(REGISTER.relative_to(PROFILE_ROOT)), "sha256": sha256(REGISTER)},
        "source_count": len(register["sources"]),
        "status_counts": {status: sum(item["register_status"] == status for item in register["sources"]) for status in ["approved", "conditional", "proposed", "not_selected", "integration_pending", "blocked"]},
        "validation": {"errors": validate(register), "passed": not validate(register)},
        "csv_fidelity": {"checks": csv_checks, "passed": all(csv_checks.values())},
        "negative_regressions": {"total": len(negative), "passed": sum(item["passed"] for item in negative), "cases": negative},
        "language_audit": {"files_checked": language.get("files_checked"), "findings": len(language.get("findings", [])), "passed": language.get("pass") is True},
        "apify_business_approval": "approved",
        "apify_execution_status": "blocked_pending_linkedin_rights_and_harvestapi_vendor_review",
        "runtime_activation": False,
        "external_actions": 0,
        "failures": errors,
        "pass": not errors,
    }
    EVAL.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    package_paths = [REGISTER, CSV_PATH, Path(__file__), PROFILE_ROOT / "scripts" / "build_step3c_source_register.py", CONTRACT, REVIEW, OUTPUT]
    manifest = {"manifest_id": "equinet-a2-step3c-draft-package", "version": register["version"], "status": "approved_unitalk_working_baseline_runtime_activation_pending", "files": [{"path": str(path.relative_to(PROFILE_ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in package_paths], "file_count": len(package_paths), "external_actions": 0}
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pass": result["pass"], "source_count": result["source_count"], "status_counts": result["status_counts"], "negative_regressions": f"{result['negative_regressions']['passed']}/{result['negative_regressions']['total']}", "apify_execution_status": result["apify_execution_status"], "review": str(REVIEW), "failures": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
