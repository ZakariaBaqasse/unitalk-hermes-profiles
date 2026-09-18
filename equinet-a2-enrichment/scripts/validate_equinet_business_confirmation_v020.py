#!/usr/bin/env python3
"""Validate the Equinet-confirmed A2 business configuration release 0.2.0."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluations/equinet-business-confirmation-20260830/technical-validation.json"


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    if spec is None or spec.loader is None:
        raise RuntimeError(rel)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def check(name: str, condition: bool, detail: str, checks: list[dict]) -> None:
    checks.append({"name": name, "passed": bool(condition), "detail": detail})


def main() -> int:
    checks: list[dict] = []
    cat_rel = "foundations/contracts/business/a2-business-field-catalogue-0.2.0.json"
    pkg_rel = "foundations/contracts/business/a2-minimum-data-packages-0.2.0.json"
    src_rel = "foundations/contracts/sources/a2-source-register-0.2.0.json"
    provider_rel = "foundations/contracts/governance/a2-provider-and-cost-policy-0.2.0.json"
    map_rel = "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.2.0.json"
    evidence_rel = "foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.2.0.json"
    protected_rel = "foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.2.0.json"
    decision_rel = "foundations/decisions/A2-EQUINET-BUSINESS-CONFIRMATION-20260830.json"
    cat, pkg, src, provider, mapping, evidence, protected, decision = map(load, [cat_rel, pkg_rel, src_rel, provider_rel, map_rel, evidence_rel, protected_rel, decision_rel])
    fields = {item["field_key"]: item for item in cat["fields"]}
    sources = {item["source_id"]: item for item in src["sources"]}
    mappings = {item["canonical_field"]: item for item in mapping["mappings"]}

    check("catalogue version", cat["version"] == "0.2.0", cat["version"], checks)
    check("client confirmation status", cat["decision_basis"]["equinet_confirmation"] == "confirmed_via_unitalk_operations", cat["status"], checks)
    check("field inventory preserved", len(cat["fields"]) == 33 and len(fields) == 33, f"fields={len(fields)}", checks)
    check("contact limit", cat["contact_selection_policy"]["default_named_contacts"] == 1 and cat["contact_selection_policy"]["maximum_named_contacts"] == 2 and cat["contact_selection_policy"]["additional_role_relevant_contacts"] == 1, json.dumps(cat["contact_selection_policy"]), checks)
    check("general contact does not satisfy target contact", cat["contact_selection_policy"]["general_organisation_contact_can_satisfy_review_readiness"] is False, cat["contact_selection_policy"]["fallback_when_no_target_role"], checks)
    check("owner priorities", all(fields[key]["priority_by_segment"]["horse_owner"] == "required" for key in ["person.role_title", "organisation.stable_type", "organisation.horse_count", "organisation.breeds", "organisation.public_business_location"]), "five confirmed priority fields", checks)
    check("horse band deprecated", fields["organisation.horse_count_band"]["priority_by_segment"]["horse_owner"] == "do_not_collect" and fields["organisation.horse_count_band"]["collection_policy"].startswith("disabled"), fields["organisation.horse_count_band"]["collection_policy"], checks)
    check("horse count policy", cat["horse_count_policy"]["existing_hubspot_value_is_authoritative"] is True and cat["horse_count_policy"]["derived_band_use"] == "disabled" and cat["horse_count_policy"]["horse_count_range"].startswith("ignored"), json.dumps(cat["horse_count_policy"]), checks)
    check("location minimum", fields["organisation.public_business_location"]["structured_requirements"]["minimum_verified_components"] == ["state", "country"], json.dumps(fields["organisation.public_business_location"]["structured_requirements"]), checks)
    check("breed rule", "Mixed" in fields["organisation.breeds"]["description"] and fields["organisation.breeds"]["priority_by_segment"]["horse_owner"] == "required", fields["organisation.breeds"]["description"], checks)

    role = module("role_classifier_v020", "scripts/classify_a2_target_role.py")
    alias_total = 0
    alias_pass=***
    for segment, priorities in role.ALIASES.items():
        for priority, groups in priorities.items():
            for role_id, aliases in groups.items():
                for alias in aliases:
                    flags = [role.CONDITIONS[role_id]] if role_id in role.CONDITIONS else []
                    result = role.classify({"segment": segment, "source_role_title": alias, "evidence_flags": flags})
                    alias_total += 1
                    alias_pass=*** and result["status"] == "classified" and result["priority"] == priority and result["canonical_role"] == role_id
    check("all confirmed role aliases", alias_pass, f"aliases_tested={alias_total}", checks)
    conditional_pass=all(ro...nt": "farrier" if key.startswith("business_") or key.startswith("farrier_") or key.startswith("retired_") else "horse_owner", "source_role_title": aliases[0], "evidence_flags": []})["status"] == "needs_review" for priority_map in role.ALIASES.values() for groups in priority_map.values() for key, aliases in groups.items() if key in role.CONDITIONS)
    check("conditional roles require evidence", conditional_pass, "all conditional roles held without the required evidence flag", checks)

    contact = module("contact_selection_v020", "scripts/validate_a2_contact_selection.py")
    one = contact.validate({"selected_contacts": [{"contact_id": "C1", "source_role_title": "Farm Owner", "target_role_priority": "primary", "unrelated_role": False}], "second_contact_reason": None, "target_role_not_found": False})
    two = contact.validate({"selected_contacts": [{"contact_id": "C1", "source_role_title": "Farm Owner", "target_role_priority": "primary", "unrelated_role": False}, {"contact_id": "C2", "source_role_title": "Purchasing Manager", "target_role_priority": "secondary", "unrelated_role": False}], "second_contact_reason": "shared_purchasing_or_operational_responsibility", "target_role_not_found": False})
    three = contact.validate({"selected_contacts": [{"contact_id": f"C{i}", "source_role_title": "Owner", "target_role_priority": "primary", "unrelated_role": False} for i in range(3)], "second_contact_reason": "large_organisation", "target_role_not_found": False})
    none = contact.validate({"selected_contacts": [], "second_contact_reason": None, "target_role_not_found": True, "research_exhausted": True})
    check("contact selection paths", one["status"] == "valid" and two["status"] == "valid" and three["status"] == "invalid" and none["status"] == "contact_needed" and none["workflow_recommendation"] == "review_required", json.dumps({"one": one["status"], "two": two["status"], "three": three["status"], "none": none["status"]}), checks)

    minimum = module("minimum_v020", "scripts/evaluate_a2_minimum_package.py")
    owner_required = pkg["packages"]["horse_owner_review_ready"]["required_verified_fields"]
    base_states = {key: "verified" for key in owner_required + ["person.full_name", "person.role_title", "relationship.target_role_priority", "person.business_email"]}
    base_states["person.business_phone"] = "not_found"
    complete = minimum.evaluate({"fixture_id": "owner-email-only", "segment": "horse_owner", "contact_path": "named_target", "target_role_not_found": False, "research_exhausted": True, "field_states": base_states}, pkg)
    missing = dict(base_states); missing["organisation.horse_count"] = "not_found"
    incomplete = minimum.evaluate({"fixture_id": "owner-open-gap", "segment": "horse_owner", "contact_path": "named_target", "target_role_not_found": False, "research_exhausted": True, "field_states": missing}, pkg)
    contact_needed = minimum.evaluate({"fixture_id": "owner-contact-needed", "segment": "horse_owner", "contact_path": "contact_needed", "target_role_not_found": True, "research_exhausted": True, "field_states": {key: "verified" for key in owner_required}}, pkg)
    check("email and phone preference", complete["package_status"] == "review_ready" and complete["preferred_missing_fields"] == ["person.business_phone"], json.dumps(complete), checks)
    check("open gaps reach human review", incomplete["package_status"] == "incomplete" and incomplete["workflow_recommendation"] == "review_required" and incomplete["human_review_required"] is True, json.dumps(incomplete), checks)
    check("contact-needed reaches human review", contact_needed["package_status"] == "incomplete" and contact_needed["workflow_recommendation"] == "review_required" and contact_needed["review_queue_label"] == "Contact Needed / Needs Review", json.dumps(contact_needed), checks)

    observations = module("observations_v020", "scripts/normalise_and_validate_a2_observations.py")
    location_field = fields["organisation.public_business_location"]
    valid_location = observations.normalise_value(location_field, {"raw_value": {"components": [{"key": "country_code", "value": "US"}, {"key": "state_region", "value": "Kentucky"}]}})
    invalid_location = False
    try:
        observations.normalise_value(location_field, {"raw_value": {"components": [{"key": "state_region", "value": "Kentucky"}]}})
    except ValueError:
        invalid_location = True
    band_rejected = False
    try:
        observations.normalise_value(fields["organisation.horse_count_band"], {"raw_value": "5_10"})
    except ValueError:
        band_rejected = True
    mixed = observations.normalise_value(fields["organisation.breeds"], {"raw_value": ["Mixed"]})
    check("location component validation", bool(valid_location) and invalid_location, json.dumps(valid_location), checks)
    check("horse band rejected", band_rejected, "new horse_count_band values are rejected", checks)
    check("Mixed breed preserved", mixed == ["Mixed"], json.dumps(mixed), checks)

    check("source policy", "explicit horse count" in sources["prospect_official_website"]["permitted_fields"] and "explicit horse breeds" in sources["prospect_official_website"]["permitted_fields"] and sources["apify_harvestapi_linkedin_profile_search"]["limits"]["max_retained_contacts_per_candidate"] == 2, "official-site explicit values and contact cap", checks)
    check("provider contact cap", provider["providers"]["apify_linkedin_profile_search"]["limits"]["max_retained_contacts"] == 2, "max_retained_contacts=2", checks)
    check("HubSpot count mapping", mappings["organisation.horse_count"]["hubspot_destinations"][0]["property"] == "owner_horse_count" and mappings["organisation.horse_count"]["mapping_status"].startswith("equinet_confirmed"), mappings["organisation.horse_count"]["mapping_status"], checks)
    check("horse range ignored", mappings["organisation.horse_count_band"]["mapping_status"] == "deprecated_ignored" and mappings["organisation.horse_count_band"]["hubspot_destinations"] == [], mappings["organisation.horse_count_band"]["mapping_status"], checks)
    evidence_dependencies = {item["path"]: item["sha256"] for item in evidence["dependencies"]}
    check("evidence dependencies current", evidence_dependencies.get(src_rel) == hashlib.sha256((ROOT / src_rel).read_bytes()).hexdigest() and evidence_dependencies.get(cat_rel) == hashlib.sha256((ROOT / cat_rel).read_bytes()).hexdigest(), json.dumps(evidence_dependencies), checks)
    protected_dependencies = {item["path"]: item["sha256"] for item in protected["dependencies"]}
    check("protected dependencies current", protected_dependencies.get(cat_rel) == hashlib.sha256((ROOT / cat_rel).read_bytes()).hexdigest() and protected_dependencies.get(evidence_rel) == hashlib.sha256((ROOT / evidence_rel).read_bytes()).hexdigest(), json.dumps(protected_dependencies), checks)
    owner_protection = next((item for item in protected["hubspot_protected_fields"] if item.get("property") == "owner_horse_count"), None)
    check("owner_horse_count conflict policy", bool(owner_protection) and owner_protection["class"] == "a2_enrichment_candidate" and protected["owner_horse_count_rule"]["horse_count_range"] == "ignored", json.dumps(owner_protection), checks)

    for rel, expected_rows in [("foundations/contracts/business/a2-business-field-catalogue-0.2.0.csv", 33), ("foundations/contracts/sources/a2-source-register-0.2.0.csv", 12), ("foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.2.0.csv", 33)]:
        with (ROOT / rel).open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        check(f"CSV fidelity {Path(rel).name}", len(rows) == expected_rows, f"rows={len(rows)}", checks)

    text_targets = [
        "SOUL.md",
        "skills/a2-gap-analysis-and-enrichment-planning/SKILL.md",
        "skills/a2-permitted-enrichment-research/SKILL.md",
        "skills/a2-field-verification/SKILL.md",
        "skills/a2-data-quality-and-review-readiness/SKILL.md",
        "skills/a2-review-package-and-governed-handoffs/SKILL.md",
    ]
    text = "\n".join((ROOT / rel).read_text(encoding="utf-8") for rel in text_targets)
    check("active guidance propagated", all(token in text for token in ["Contact Needed / Needs Review", "owner_horse_count", "approved_collect_during_discovery", "at most two"]), "required guidance markers found", checks)
    check("decision non-authorisation", decision["external_actions_authorized"] is False and decision["hubspot_write_authorized"] is False, "zero external action authority", checks)
    active = load("foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json")
    old_names = ["a2-business-field-catalogue-0.1.1-draft.1", "a2-minimum-data-packages-0.1.1-draft.1", "a2-source-register-0.1.1-draft.1", "a2-provider-and-cost-policy-0.1.1-draft.1", "a2-hubspot-preliminary-mapping-0.1.1-draft.1"]
    active_paths = [item["path"] for item in active["active_files"]]
    stale = [path for path in active_paths if any(name in path for name in old_names)]
    check("active manifest has no superseded business contracts", not stale, json.dumps(stale), checks)

    result = {
        "record_type": "a2_equinet_business_confirmation_technical_validation",
        "version": VERSION if (VERSION := "0.2.0") else "0.2.0",
        "validated_at": "2026-08-30T17:05:11Z",
        "status": "pass" if all(item["passed"] for item in checks) else "fail",
        "checks_passed": sum(item["passed"] for item in checks),
        "checks_total": len(checks),
        "checks": checks,
        "external_actions": 0,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
