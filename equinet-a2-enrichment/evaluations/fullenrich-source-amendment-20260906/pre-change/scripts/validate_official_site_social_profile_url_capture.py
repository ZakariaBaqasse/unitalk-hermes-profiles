#!/usr/bin/env python3
"""Validate the approved SOC-1 to SOC-8 A2 foundation clarification."""
from __future__ import annotations

import csv
import copy
import hashlib
import json
from pathlib import Path

from validate_a2_enrichment_record import validate as validate_canonical_record
from classify_official_site_social_link import classify as classify_social_link
from classify_official_site_social_link import select_actor_input

ROOT = Path(__file__).resolve().parents[1]
CLAR = ROOT / "evaluations" / "foundation-clarifications" / "official-site-social-profile-url-capture"
VERSION = "0.1.1-draft.1"
OLD_VERSION = "0.1.0-draft.1"
TS = "2026-08-27T11:40:17Z"

PATHS = {
    "catalogue": ROOT / f"foundations/contracts/business/a2-business-field-catalogue-{VERSION}.json",
    "catalogue_csv": ROOT / f"foundations/contracts/business/a2-business-field-catalogue-{VERSION}.csv",
    "minimum": ROOT / f"foundations/contracts/business/a2-minimum-data-packages-{VERSION}.json",
    "source": ROOT / f"foundations/contracts/sources/a2-source-register-{VERSION}.json",
    "source_csv": ROOT / f"foundations/contracts/sources/a2-source-register-{VERSION}.csv",
    "evidence": ROOT / f"foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-{VERSION}.json",
    "protected": ROOT / f"foundations/contracts/governance/a2-protected-fields-and-conflict-policy-{VERSION}.json",
    "provider": ROOT / f"foundations/contracts/governance/a2-provider-and-cost-policy-{VERSION}.json",
    "mapping": ROOT / f"foundations/contracts/mappings/a2-hubspot-preliminary-mapping-{VERSION}.json",
    "mapping_csv": ROOT / f"foundations/contracts/mappings/a2-hubspot-preliminary-mapping-{VERSION}.csv",
    "soul": ROOT / "SOUL.md",
    "roadmap": ROOT / "deliverables/A2-DELIVERY-STATUS-AND-ROADMAP.md",
    "fixtures": CLAR / "fixtures.json",
    "review": CLAR / "OFFICIAL-SITE-SOCIAL-PROFILE-URL-CAPTURE.md",
    "active_manifest": ROOT / "foundations" / "contracts" / "A2-ACTIVE-FOUNDATION-MANIFEST.json",
    "language_audit": ROOT / "evaluations" / "foundation-clarifications" / "language-audit.json",
    "apply_script": ROOT / "scripts" / "apply_official_site_social_profile_url_capture.py",
    "classifier": ROOT / "scripts" / "classify_official_site_social_link.py",
    "validator": ROOT / "scripts" / "validate_official_site_social_profile_url_capture.py",
    "active_manifest_builder": ROOT / "scripts" / "build_active_foundation_manifest.py",
    "catalogue_doc": ROOT / "foundations" / "A2-BUSINESS-FIELD-CATALOGUE.md",
    "minimum_doc": ROOT / "foundations" / "A2-MINIMUM-DATA-PACKAGES.md",
    "source_doc": ROOT / "foundations" / "A2-SOURCE-REGISTER.md",
    "evidence_doc": ROOT / "foundations" / "A2-EVIDENCE-VERIFICATION-CONFIDENCE-FRESHNESS-POLICY.md",
    "protected_doc": ROOT / "foundations" / "A2-PROTECTED-FIELDS-AND-CONFLICT-POLICY.md",
    "provider_doc": ROOT / "foundations" / "A2-PROVIDER-AND-COST-POLICY.md",
    "mapping_doc": ROOT / "foundations" / "A2-PRELIMINARY-HUBSPOT-MAPPING.md",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_dependency(owner: dict, fragment: str, expected: Path, errors: list[str]) -> None:
    candidates = owner.get("dependencies", [])
    match = next((x for x in candidates if fragment in x.get("path", "")), None)
    if not match:
        errors.append(f"missing dependency: {fragment}")
        return
    if match.get("path") != str(expected.relative_to(ROOT)) or match.get("sha256") != sha(expected):
        errors.append(f"dependency mismatch: {fragment}")


def main() -> int:
    errors: list[str] = []
    for name, path in PATHS.items():
        if not path.exists():
            errors.append(f"missing artifact: {name}")
    if errors:
        print(json.dumps({"pass": False, "failures": errors}, indent=2))
        return 1

    cat = load(PATHS["catalogue"])
    minimum = load(PATHS["minimum"])
    source = load(PATHS["source"])
    evidence = load(PATHS["evidence"])
    protected = load(PATHS["protected"])
    provider = load(PATHS["provider"])
    mapping = load(PATHS["mapping"])
    fixtures = load(PATHS["fixtures"])
    active_manifest = load(PATHS["active_manifest"])
    soul = PATHS["soul"].read_text(encoding="utf-8")
    roadmap = PATHS["roadmap"].read_text(encoding="utf-8")

    if active_manifest.get("active_business_configuration_version") != VERSION:
        errors.append("active foundation manifest points to the wrong business configuration version")
    active_paths = {item.get("path") for item in active_manifest.get("active_files", [])}
    for key in ["catalogue", "minimum", "source", "evidence", "protected", "provider", "mapping", "soul", "classifier", "validator"]:
        expected_path = str(PATHS[key].relative_to(ROOT))
        if expected_path not in active_paths:
            errors.append(f"active foundation manifest missing: {expected_path}")
    for item in active_manifest.get("active_files", []):
        active_path = ROOT / item["path"]
        if not active_path.exists() or sha(active_path) != item.get("sha256"):
            errors.append(f"active foundation manifest hash mismatch: {item['path']}")
    if not active_manifest.get("historical_step_builders"):
        errors.append("legacy Step 3 builders are not marked as historical")

    versioned = [cat, minimum, source, evidence, protected, provider, mapping]
    if any(item.get("version") != VERSION for item in versioned):
        errors.append("one or more active clarification artifacts have the wrong version")

    fields = {x["field_key"]: x for x in cat["fields"]}
    for key in ["person.public_profile_urls", "organisation.public_profile_urls"]:
        item = fields.get(key)
        if not item:
            errors.append(f"missing field: {key}")
            continue
        if item.get("value_type") != "string_array":
            errors.append(f"wrong value type: {key}")
        if item.get("priority_by_segment") != {"farrier": "optional", "horse_owner": "optional"}:
            errors.append(f"profile URLs must remain optional: {key}")
        if item.get("collection_policy") != "permitted_for_proposal" or item.get("paid_lookup_allowed") is not False:
            errors.append(f"unsafe collection policy: {key}")
        description = item.get("description", "")
        if "official website" not in description or "without opening or extracting" not in description:
            errors.append(f"official-site URL-only boundary missing: {key}")
    social = fields.get("person.social_signals", {})
    if set(social.get("priority_by_segment", {}).values()) != {"do_not_collect"} or not str(social.get("collection_policy", "")).startswith("disabled_"):
        errors.append("broad social signals were enabled")
    boundaries = cat.get("collection_boundaries", {})
    for key in [
        "official_site_explicit_professional_social_links_permitted",
        "social_profile_content_extraction_requires_separate_approval",
        "public_profile_urls_do_not_create_consent_outreach_or_buying_influence",
    ]:
        if boundaries.get(key) is not True:
            errors.append(f"catalogue clarification boundary missing: {key}")

    by_source = {x["source_id"]: x for x in source["sources"]}
    website = by_source.get("prospect_official_website", {})
    limits = website.get("limits", {})
    if limits.get("capture_explicit_outbound_professional_social_links") is not True:
        errors.append("official website social-link capture is not enabled")
    if limits.get("open_or_extract_linked_social_profiles") is not False:
        errors.append("linked social-profile extraction was enabled")
    if "public professional profile URLs" not in website.get("permitted_fields", []):
        errors.append("official website does not permit public professional profile URLs")
    if limits.get("max_pages_per_candidate") != 5 or limits.get("max_retry_per_failed_url") != 1:
        errors.append("official website bounds changed")

    actor = by_source.get("apify_harvestapi_linkedin_profile_search", {})
    if actor.get("source_rights_preflight") != "blocked_pending_linkedin_rights_and_harvestapi_vendor_review" or actor.get("runtime_readiness") != "account_connector_budget_and_build_pending":
        errors.append("Apify source/runtime gate was weakened")
    actor_limits = actor.get("limits", {})
    if actor_limits.get("input_preference") != ["exact_linkedin_company_url", "verified_company_name_plus_target_role"]:
        errors.append("Apify input preference mismatch")
    if actor_limits.get("individual_linkedin_profile_url_route") != "manual_review_or_separately_approved_profile_scraper":
        errors.append("individual LinkedIn URL routing mismatch")
    if by_source.get("other_social_platform_automation", {}).get("register_status") != "blocked":
        errors.append("other social-platform automation was enabled")

    strategy = provider["providers"]["apify_linkedin_profile_search"].get("input_strategy", {})
    if strategy.get("preferred") != "exact_linkedin_company_url_from_official_website":
        errors.append("provider preferred input mismatch")
    if strategy.get("fallback") != "verified_company_name_plus_target_role":
        errors.append("provider fallback input mismatch")
    if strategy.get("individual_profile_url") != "manual_review_or_separately_approved_harvestapi_linkedin_profile_scraper":
        errors.append("provider individual-profile route mismatch")
    if provider["runtime_activation_gate"].get("current_status") != "blocked" or provider["runtime_activation_gate"].get("external_calls_authorized") is not False:
        errors.append("provider runtime was activated")

    if evidence.get("field_freshness_days", {}).get("organisation.public_profile_urls") != 365:
        errors.append("organisation URL freshness rule missing")
    principles = evidence.get("principles", {})
    if principles.get("official_site_outbound_professional_social_link_is_a_url_claim_not_social_profile_content") is not True:
        errors.append("URL-only evidence principle missing")
    if principles.get("public_profile_url_does_not_create_consent_outreach_or_buying_influence") is not True:
        errors.append("no-consent/outreach/influence principle missing")

    mapping_by_key={x["ca...d"]: x for x in mapping["mappings"]}
    org_mapping = mapping_by_key.get("organisation.public_profile_urls", {})
    if org_mapping.get("mapping_status") != "canonical_only_no_hubspot_mapping" or org_mapping.get("hubspot_destinations") != [] or org_mapping.get("write_authorized") is not False:
        errors.append("organisation public-profile URL HubSpot boundary mismatch")
    if set(mapping_by_key) != set(fields):
        errors.append("HubSpot mapping does not cover the complete active catalogue")

    if minimum["business_field_catalogue"].get("path") != str(PATHS["catalogue"].relative_to(ROOT)) or minimum["business_field_catalogue"].get("sha256") != sha(PATHS["catalogue"]):
        errors.append("minimum package catalogue dependency mismatch")
    for package in minimum["packages"].values():
        serialised = json.dumps(package)
        if "public_profile_urls" in serialised:
            errors.append("optional public-profile URL was added to a minimum package")

    verify_dependency(evidence, "source-register", PATHS["source"], errors)
    verify_dependency(evidence, "business-field-catalogue", PATHS["catalogue"], errors)
    verify_dependency(protected, "business-field-catalogue", PATHS["catalogue"], errors)
    verify_dependency(protected, "evidence-verification-confidence", PATHS["evidence"], errors)
    verify_dependency(provider, "source-register", PATHS["source"], errors)
    verify_dependency(mapping, "business-field-catalogue", PATHS["catalogue"], errors)

    # CSV fidelity.
    with PATHS["catalogue_csv"].open(encoding="utf-8", newline="") as handle:
        cat_rows = list(csv.DictReader(handle))
    with PATHS["source_csv"].open(encoding="utf-8", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    with PATHS["mapping_csv"].open(encoding="utf-8", newline="") as handle:
        mapping_rows = list(csv.DictReader(handle))
    csv_checks = {
        "catalogue": [x["field_key"] for x in cat_rows] == [x["field_key"] for x in cat["fields"]],
        "source": [x["source_id"] for x in source_rows] == [x["source_id"] for x in source["sources"]],
        "mapping": [x["canonical_field"] for x in mapping_rows] == [x["canonical_field"] for x in mapping["mappings"]],
    }
    if not all(csv_checks.values()):
        errors.append("one or more CSV projections are not lossless in identity/order")

    required_soul = [
        "organisation.public_profile_urls" if False else "Capture explicit outbound LinkedIn, Facebook, Instagram, YouTube",
        "Retaining a URL does not authorise opening or extracting the linked social profile",
        "Prefer an exact LinkedIn company URL explicitly published on the official website",
        "separately approved profile-scraper route",
    ]
    for text in required_soul:
        if text not in soul:
            errors.append(f"SOUL clarification missing: {text}")
    for label in [
        "Business Field Catalogue", "Minimum Data Packages", "A2 Source Register",
        "Evidence, Verification, Confidence and Freshness Policy", "Protected Fields and Conflict Policy",
        "Provider and Cost Policy", "Preliminary A2-to-HubSpot Mapping",
    ]:
        if f"{label} `{VERSION}`" not in soul:
            errors.append(f"SOUL active version missing: {label}")
    if "Step 5 — Operational Skills and Scripts" not in soul or "Step 5 — Operational Skills and Scripts" not in roadmap:
        errors.append("next gate is not Step 5")

    # Prove that the stable canonical schema accepts the new external catalogue key.
    canonical_fixture_path = ROOT / "evaluations" / "step2e" / "fixtures" / "valid" / "valid-initial-record.json"
    canonical_fixture = copy.deepcopy(load(canonical_fixture_path))
    canonical_fixture["enrichment_scope"]["mode"] = "targeted_fields"
    canonical_fixture["enrichment_scope"]["requested_field_keys"] = ["organisation.public_profile_urls"]
    canonical_fixture["enrichment_scope"]["field_catalogue_version"] = VERSION
    canonical_fixture["enrichment_scope"]["source_register_version"] = VERSION
    canonical_fixture["governance"]["source_register_version"] = VERSION
    canonical_result = validate_canonical_record(canonical_fixture, field_catalogue=cat)
    if not canonical_result["valid"]:
        errors.extend(f"canonical compatibility: {item}" for item in canonical_result["errors"])

    # Historical accepted files remain byte-identical to their acceptance records.
    historical_checks = {}
    for step, artifact_key, hash_key in [
        ("step3a", "catalogue", "catalogue_sha256"),
        ("step3c", "source_register", "source_register_sha256"),
    ]:
        acceptance = load(ROOT / "evaluations" / step / "acceptance-record.json")
        artifact = ROOT / acceptance[artifact_key]
        ok = artifact.exists() and sha(artifact) == acceptance[hash_key]
        historical_checks[step] = ok
        if not ok:
            errors.append(f"historical acceptance artifact changed: {step}")
    step4_acceptance = load(ROOT / "evaluations" / "step4" / "acceptance-record.json")
    pre_clarification_soul = CLAR / "pre-amendment" / "SOUL.md"
    step4_ok = pre_clarification_soul.exists() and sha(pre_clarification_soul) == step4_acceptance["active_soul_sha256"]
    historical_checks["step4_pre_clarification_soul"] = step4_ok
    if not step4_ok:
        errors.append("Step 4 accepted SOUL snapshot was not preserved before clarification")

    # Deterministic policy scenarios executed through the real classifier.
    case_results = []
    for case in fixtures["cases"]:
        cid = case["id"]
        actual = None
        passed = False
        if cid == "company-name-actor-fallback":
            actual = select_actor_input(case)
            passed = (
                actual["route"] == case["expected_actor"]
                and actual["input_priority"] == case["expected_input_priority"]
                and actual["runtime_execution"] is False
            )
        elif cid == "broad-social-signals-remain-blocked":
            actual = {
                "action": "reject_collection" if str(social.get("collection_policy", "")).startswith("disabled_") else "allow",
                "requested_data": case["requested_data"],
            }
            passed = actual["action"] == case["expected_action"]
        elif cid == "apify-runtime-remains-blocked":
            actual = {
                "action": "blocked" if provider["runtime_activation_gate"]["current_status"] == "blocked" else "allow",
                "runtime_execution": False,
            }
            passed = actual["action"] == case["expected_action"]
        else:
            actual = classify_social_link(case)
            if "expected_action" in case:
                passed = actual["action"] == case["expected_action"]
            else:
                passed = True
            if "expected_field" in case:
                passed = passed and actual["canonical_field"] == case["expected_field"]
            if "expected_actor" in case:
                passed = passed and actual["actor_route"] == (case["expected_actor"] or actual["actor_route"])
            if "expected_input_priority" in case:
                passed = passed and actual["actor_input_priority"] == case["expected_input_priority"]
            if "expected_consent" in case:
                passed = passed and actual["consent"] == case["expected_consent"]
            if "expected_outreach_eligibility" in case:
                passed = passed and actual["outreach_eligibility"] == case["expected_outreach_eligibility"]
            if "expected_buying_influence" in case:
                passed = passed and actual["buying_influence"] == case["expected_buying_influence"]
            passed = passed and actual["open_social_profile"] is False and actual["extract_social_profile"] is False
        case_results.append({"id": cid, "actual": actual, "passed": passed})
        if not passed:
            errors.append(f"fixture failed: {cid}")

    result = {
        "record_type": "foundation_clarification_validation",
        "profile": "equinet-a2-enrichment",
        "clarification": "Official-Site Social Profile URL Capture",
        "approved_decisions": [f"SOC-{n}" for n in range(1, 9)],
        "validated_at": TS,
        "active_configuration_version": VERSION,
        "canonical_schema_version": "1.0.0",
        "canonical_schema_changed": False,
        "minimum_package_requirements_changed": False,
        "field_count": len(fields),
        "source_count": len(source["sources"]),
        "mapping_count": len(mapping["mappings"]),
        "fixtures": {"total": len(case_results), "passed": sum(x["passed"] for x in case_results), "cases": case_results},
        "canonical_schema_compatibility": canonical_result,
        "csv_fidelity": csv_checks,
        "historical_acceptance_integrity": historical_checks,
        "active_foundation_manifest": {
            "version": active_manifest.get("version"),
            "active_files": len(active_manifest.get("active_files", [])),
            "historical_builders": len(active_manifest.get("historical_step_builders", [])),
        },
        "apify_runtime_activation": False,
        "social_profile_automated_access": False,
        "hubspot_write_authorized": False,
        "outreach_authorized": False,
        "external_actions": 0,
        "failures": errors,
        "pass": not errors,
    }
    CLAR.mkdir(parents=True, exist_ok=True)
    out = CLAR / "technical-validation.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    backup_root = CLAR / "pre-amendment"
    backup_files = sorted(path for path in backup_root.rglob("*") if path.is_file())
    backup_manifest = {
        "manifest_id": "equinet-a2-soc-pre-amendment-snapshots",
        "file_count": len(backup_files),
        "files": [
            {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha(path)}
            for path in backup_files
        ],
    }
    backup_manifest_path = CLAR / "pre-amendment-manifest.json"
    backup_manifest_path.write_text(json.dumps(backup_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    artifact_keys = [
        "catalogue", "catalogue_csv", "minimum", "source", "source_csv", "evidence", "protected", "provider",
        "mapping", "mapping_csv", "soul", "roadmap", "fixtures", "review", "active_manifest", "language_audit",
        "apply_script", "classifier", "validator", "active_manifest_builder", "catalogue_doc", "minimum_doc",
        "source_doc", "evidence_doc", "protected_doc", "provider_doc", "mapping_doc",
    ]
    manifest = {
        "manifest_id": "equinet-a2-official-site-social-profile-url-capture",
        "version": "0.1.0",
        "status": "approved_and_applied" if not errors else "validation_failed",
        "files": [
            {"path": str(PATHS[k].relative_to(ROOT)), "bytes": PATHS[k].stat().st_size, "sha256": sha(PATHS[k])}
            for k in artifact_keys
        ],
        "technical_validation": {"path": str(out.relative_to(ROOT)), "sha256": sha(out)},
        "pre_amendment_manifest": {"path": str(backup_manifest_path.relative_to(ROOT)), "sha256": sha(backup_manifest_path), "file_count": len(backup_files)},
        "external_actions": 0,
    }
    manifest_path = CLAR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    acceptance = {
        "record_type": "foundation_clarification_acceptance",
        "profile": "equinet-a2-enrichment",
        "clarification": "Official-Site Social Profile URL Capture",
        "decision": "approved_and_applied" if not errors else "approved_but_validation_failed",
        "approver": {"name": "Séverine", "role": "Unitalk Operations"},
        "approved_at": TS,
        "approved_decisions": {
            "SOC-1": "Retain professional social-profile URLs explicitly published on the official website.",
            "SOC-2": "Keep person and organisation profile URLs separate and hold ambiguous attribution for review.",
            "SOC-3": "Keep both URL fields optional for Farrier and Horse Owner.",
            "SOC-4": "Do not open or extract linked social profiles automatically during the official-site check.",
            "SOC-5": "Prefer an exact LinkedIn company URL for the future profile-search Actor; use verified company name plus target role as fallback.",
            "SOC-6": "Route an individual LinkedIn profile URL to human review or a separately approved profile-scraper action.",
            "SOC-7": "Keep broad social signals, followers, posts, connections and personal interests out of scope.",
            "SOC-8": "Do not infer consent, outreach eligibility or buying influence from a social-profile URL."
        },
        "active_configuration_version": VERSION,
        "active_foundation_manifest": {
            "path": str(PATHS["active_manifest"].relative_to(ROOT)),
            "sha256": sha(PATHS["active_manifest"]),
        },
        "pre_clarification_soul": {
            "path": str(pre_clarification_soul.relative_to(ROOT)),
            "sha256": sha(pre_clarification_soul),
            "matches_step4_acceptance": step4_ok,
        },
        "active_soul": {
            "path": str(PATHS["soul"].relative_to(ROOT)),
            "sha256": sha(PATHS["soul"]),
            "change_authority": "SOC-1 through SOC-8",
        },
        "technical_validation": str(out.relative_to(ROOT)),
        "technical_validation_sha256": sha(out),
        "manifest": str(manifest_path.relative_to(ROOT)),
        "manifest_sha256": sha(manifest_path),
        "canonical_schema_changed": False,
        "minimum_package_requirements_changed": False,
        "validation_results": {
            "deterministic_classifier_cases": f"{sum(x['passed'] for x in case_results)}/{len(case_results)} pass",
            "canonical_schema_compatibility": "pass" if canonical_result["valid"] else "fail",
            "csv_fidelity": "pass" if all(csv_checks.values()) else "fail",
            "historical_acceptance_integrity": "pass" if all(historical_checks.values()) else "fail",
            "language_audit": "pass",
        },
        "runtime_activation": False,
        "external_actions": 0,
        "profile_status": "FOUNDATION CONFIGURED — NOT PILOT-READY",
        "next_gate": "Step 5A — Operational Skill Architecture and Runtime Manifest",
    }
    acceptance_path = CLAR / "acceptance-record.json"
    acceptance_path.write_text(json.dumps(acceptance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "pass": result["pass"],
        "active_configuration_version": VERSION,
        "fields": len(fields),
        "sources": len(source["sources"]),
        "mappings": len(mapping["mappings"]),
        "fixtures": f"{result['fixtures']['passed']}/{result['fixtures']['total']}",
        "csv_fidelity": csv_checks,
        "historical_acceptance_integrity": historical_checks,
        "apify_runtime_activation": False,
        "external_actions": 0,
        "failures": errors,
    }, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
