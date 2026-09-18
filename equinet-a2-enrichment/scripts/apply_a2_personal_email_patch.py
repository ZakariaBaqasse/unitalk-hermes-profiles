#!/usr/bin/env python3
"""Apply the approved incidental-personal-email correction to A2 FullEnrich."""
from __future__ import annotations

import copy
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STAMP = "2026-09-06T13:38:10Z"
DECISION_ID = "A2-FULLENRICH-INCIDENTAL-PERSONAL-EMAIL-20260906"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_csv(register: dict[str, Any], path: Path) -> None:
    fields = ["source_id", "name", "source_type", "canonical_url", "business_approval", "source_rights_preflight", "runtime_readiness", "register_status", "purpose", "allowed_access_modes", "permitted_fields", "prohibited_fields", "limits", "notes"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for source in register["sources"]:
            row = {}
            for key in fields:
                value = source.get(key)
                row[key] = json.dumps(value, ensure_ascii=False, separators=(",", ":")) if isinstance(value, (list, dict)) or value is None else value
            writer.writerow(row)


def catalogue_csv(catalogue: dict[str, Any], path: Path) -> None:
    fields = ["field_key", "label", "scope", "value_type", "allowed_segments", "farrier_priority", "horse_owner_priority", "collection_policy", "data_category", "inference_policy", "paid_lookup_allowed", "enum_values", "a1_requalification_criterion_ids", "approval_rule", "unknown_behaviour", "mapping_candidates", "description"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for item in catalogue["fields"]:
            priority = item.get("priority_by_segment", {})
            writer.writerow({
                "field_key": item.get("field_key"), "label": item.get("label"), "scope": item.get("scope"), "value_type": item.get("value_type"),
                "allowed_segments": json.dumps(item.get("allowed_segments"), ensure_ascii=False, separators=(",", ":")),
                "farrier_priority": priority.get("farrier", "not_applicable"), "horse_owner_priority": priority.get("horse_owner", "not_applicable"),
                "collection_policy": item.get("collection_policy"), "data_category": item.get("data_category"), "inference_policy": item.get("inference_policy"),
                "paid_lookup_allowed": str(bool(item.get("paid_lookup_allowed"))).lower(), "enum_values": json.dumps(item.get("enum_values"), ensure_ascii=False, separators=(",", ":")),
                "a1_requalification_criterion_ids": json.dumps(item.get("a1_requalification_criterion_ids", []), ensure_ascii=False, separators=(",", ":")),
                "approval_rule": item.get("approval_rule"), "unknown_behaviour": item.get("unknown_behaviour"),
                "mapping_candidates": json.dumps(item.get("mapping_candidates", []), ensure_ascii=False, separators=(",", ":")), "description": item.get("description"),
            })


def mapping_csv(mapping: dict[str, Any], path: Path) -> None:
    fields = ["canonical_field", "scope", "value_type", "allowed_segments", "mapping_status", "direction", "hubspot_destinations", "conversion", "baseline_authority", "populated_manual_value", "workflow_dependency_status", "write_authorized"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for item in mapping["mappings"]:
            row = {key: item.get(key) for key in fields}
            for key in ["allowed_segments", "hubspot_destinations"]:
                row[key] = json.dumps(row[key], ensure_ascii=False, separators=(",", ":"))
            row["write_authorized"] = str(bool(row["write_authorized"])).lower()
            writer.writerow(row)


def update_dep(items: list[dict[str, Any]], old_fragment: str, new_rel: str) -> None:
    found = False
    for item in items:
        if old_fragment in item.get("path", ""):
            item.update(path=new_rel, sha256=sha(ROOT / new_rel)); found = True
    if not found:
        raise ValueError(f"dependency not found: {old_fragment}")


def main() -> int:
    decision = {
        "record_type": "equinet_a2_fullenrich_personal_email_correction",
        "decision_id": DECISION_ID,
        "recorded_at": STAMP,
        "recorded_by": {"name": "Séverine", "role": "Unitalk Operations"},
        "client_authority": "Equinet-confirmed requirement relayed by Séverine",
        "decision": {
            "personal_email_requested_by_default": False,
            "incidental_personal_email_retained": True,
            "canonical_field": "person.personal_email_candidate",
            "retain_provider_provenance_and_verification_status": True,
            "distinct_from_professional_email": True,
            "satisfies_professional_contactability": False,
            "creates_consent_or_outreach_authority": False,
            "automatic_hubspot_write": False,
            "human_review_required": True
        },
        "supersedes": {
            "decision_id": "A2-FULLENRICH-SOURCE-ROUTING-20260906",
            "scope": ["unexpected_personal_email_handling"]
        },
        "external_actions_authorized": False,
        "production_acceptance": False
    }
    decision_json = ROOT / f"foundations/decisions/{DECISION_ID}.json"
    decision_md = ROOT / f"foundations/decisions/{DECISION_ID}.md"
    dump(decision_json, decision)
    decision_md.write_text(f"""# Equinet A2 Incidental Personal-Email Decision\n\n**Decision ID:** `{DECISION_ID}`  \n**Recorded at:** `{STAMP}`  \n**Recorded by:** Séverine, Unitalk Operations  \n**Status:** `BUSINESS RULE CONFIRMED — INTEGRATION PENDING`\n\n## Confirmed rule\n\nPersonal email is not requested by default from FullEnrich. If FullEnrich returns a personal email incidentally, A2 retains it as `person.personal_email_candidate` on the A2 contact with exact provider provenance and verification status. It remains distinct from professional email, requires human review, does not satisfy professional contactability by itself, does not create consent or outreach authority and is not written automatically to HubSpot.\n\nThis decision supersedes only the unexpected-personal-email handling in `A2-FULLENRICH-SOURCE-ROUTING-20260906`. All other FullEnrich routing and contact-limit rules remain unchanged.\n""", encoding="utf-8")

    cat = copy.deepcopy(load(ROOT / "foundations/contracts/business/a2-business-field-catalogue-0.3.0.json"))
    cat["version"] = "0.3.1"; cat["status"] = "equinet_confirmed_fullenrich_personal_email_correction_integration_pending"
    cat["decision_record"] = {"path": str(decision_json.relative_to(ROOT)), "sha256": sha(decision_json)}
    cat["source_handling_boundaries"]["personal_email_and_mobile_paid_discovery"] = "personal_email_not_requested_but_retained_if_incidental_mobile_approved_for_selected_contacts"
    personal = next(x for x in cat["fields"] if x["field_key"] == "person.personal_email_candidate")
    personal["priority_by_segment"] = {"farrier": "optional", "horse_owner": "optional"}
    personal["collection_policy"] = "retain_if_incidentally_returned_by_approved_contact_enrichment"
    personal["paid_lookup_allowed"] = False
    personal["description"] = "Personal email not requested by default; if returned incidentally by approved FullEnrich contact enrichment, retain it as a separate personal-email candidate with provider provenance and verification status."
    personal["approval_rule"] = "human_privacy_review_required_no_consent_outreach_or_automatic_crm_write"
    cat_json = ROOT / "foundations/contracts/business/a2-business-field-catalogue-0.3.1.json"; cat_csv = ROOT / "foundations/contracts/business/a2-business-field-catalogue-0.3.1.csv"
    dump(cat_json, cat); catalogue_csv(cat, cat_csv)

    minimum = copy.deepcopy(load(ROOT / "foundations/contracts/business/a2-minimum-data-packages-0.3.0.json"))
    minimum["version"] = "0.3.1"; minimum["status"] = cat["status"]
    minimum["business_field_catalogue"] = {"path": str(cat_json.relative_to(ROOT)), "version": "0.3.1", "sha256": sha(cat_json), "status": cat["status"]}
    minimum["global_rules"]["incidental_personal_email_satisfies_professional_contactability"] = False
    minimum["global_rules"]["incidental_personal_email_requires_human_review"] = True
    min_json = ROOT / "foundations/contracts/business/a2-minimum-data-packages-0.3.1.json"; dump(min_json, minimum)

    source = copy.deepcopy(load(ROOT / "foundations/contracts/sources/a2-source-register-0.3.0.json"))
    source["version"] = "0.3.1"; source["status"] = "equinet_confirmed_fullenrich_personal_email_correction_runtime_pending"
    source["global_rules"]["fullenrich_personal_email_requested"] = False
    source["global_rules"]["fullenrich_incidental_personal_email_retained"] = True
    enrich = next(x for x in source["sources"] if x["source_id"] == "fullenrich_contact_enrichment")
    for field in ["person.personal_email_candidate", "personal-email verification status", "incidental-return provenance"]:
        if field not in enrich["permitted_fields"]: enrich["permitted_fields"].append(field)
    enrich["prohibited_fields"] = [x for x in enrich["prohibited_fields"] if x != "personal email retention"]
    if "dedicated personal-email request by default" not in enrich["prohibited_fields"]: enrich["prohibited_fields"].append("dedicated personal-email request by default")
    enrich["limits"]["personal_email_requested"] = False
    enrich["limits"]["incidental_personal_email_retained"] = True
    enrich["notes"] = [x.replace("The API request must omit contact.personal_emails.", "The API request omits contact.personal_emails by default. If a personal email is nevertheless returned, retain it separately with provenance and verification status for human review.") for x in enrich["notes"]]
    source["decision_record"] = {"path": str(decision_json.relative_to(ROOT)), "sha256": sha(decision_json)}
    source_json = ROOT / "foundations/contracts/sources/a2-source-register-0.3.1.json"; source_csv_path = ROOT / "foundations/contracts/sources/a2-source-register-0.3.1.csv"
    dump(source_json, source); source_csv(source, source_csv_path)

    evidence = copy.deepcopy(load(ROOT / "foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.3.0.json"))
    evidence["version"] = "0.3.1"; evidence["status"] = "equinet_confirmed_fullenrich_personal_email_correction_integration_pending"
    evidence["unitalk_approval"] = {"approver": "Séverine, Unitalk Operations", "approved_at": STAMP, "scope": "Incidental FullEnrich personal-email retention with provenance, review and no operational authority"}
    evidence["dependencies"] = [
        {"path": str(source_json.relative_to(ROOT)), "sha256": sha(source_json)},
        {"path": str(cat_json.relative_to(ROOT)), "sha256": sha(cat_json)},
        {"path": "foundations/contracts/a2-state-model-0.1.0.json", "sha256": sha(ROOT / "foundations/contracts/a2-state-model-0.1.0.json")},
        {"path": str(decision_json.relative_to(ROOT)), "sha256": sha(decision_json)}
    ]
    evidence["principles"]["fullenrich_personal_email_is_not_requested"] = True
    evidence["principles"]["fullenrich_incidental_personal_email_is_retained_separately"] = True
    evidence["email_specific_rules"]["personal_email"] = "not_requested_by_default_but_retained_if_incidentally_returned_with_provider_provenance_verification_status_and_human_review"
    evidence["source_rules"]["fullenrich_contact_enrichment"]["personal_email_requested"] = False
    evidence["source_rules"]["fullenrich_contact_enrichment"]["incidental_personal_email_retained"] = True
    evidence_json = ROOT / "foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.3.1.json"; dump(evidence_json, evidence)

    provider = copy.deepcopy(load(ROOT / "foundations/contracts/governance/a2-provider-and-cost-policy-0.3.0.json"))
    provider["version"] = "0.3.1"; provider["status"] = "equinet_confirmed_fullenrich_personal_email_correction_runtime_pending"
    provider["unitalk_approval"] = {"approver": "Séverine, Unitalk Operations", "approved_at": STAMP, "scope": "Incidental FullEnrich personal-email retention; no default personal-email request"}
    provider["dependencies"] = [{"path": str(source_json.relative_to(ROOT)), "sha256": sha(source_json)}, {"path": str(decision_json.relative_to(ROOT)), "sha256": sha(decision_json)}]
    p_enrich = provider["providers"]["fullenrich_contact_enrichment"]
    p_enrich["billing_model"]["personal_email_not_requested"] = True
    p_enrich["allowed_incidental_fields"] = ["most_probable_personal_email.email", "most_probable_personal_email.status", "personal_emails[].email", "personal_emails[].status"]
    p_enrich["prohibited_fields"] = [x for x in p_enrich["prohibited_fields"] if x != "personal email retention"]
    p_enrich["prohibited_fields"].append("dedicated personal-email request by default")
    provider["data_governance"]["personal_email_requested"] = False
    provider["data_governance"]["incidental_personal_email"] = "retain_separately_with_provenance_verification_status_and_human_review"
    provider_json = ROOT / "foundations/contracts/governance/a2-provider-and-cost-policy-0.3.1.json"; dump(provider_json, provider)

    protected = copy.deepcopy(load(ROOT / "foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.3.0.json"))
    protected["version"] = "0.3.1"; protected["status"] = "equinet_confirmed_fullenrich_personal_email_correction_integration_pending"
    for item in protected["dependencies"]:
        if "business-field-catalogue" in item["path"]: item.update(path=str(cat_json.relative_to(ROOT)), sha256=sha(cat_json))
        elif "evidence-verification-confidence" in item["path"]: item.update(path=str(evidence_json.relative_to(ROOT)), sha256=sha(evidence_json))
    protected["fullenrich_contact_rules"]["personal_email"] = "retain_as_person.personal_email_candidate_with_human_review_no_automatic_crm_write_or_outreach"
    protected_json = ROOT / "foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.3.1.json"; dump(protected_json, protected)

    mapping = copy.deepcopy(load(ROOT / "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.3.0.json"))
    mapping["version"] = "0.3.1"; mapping["status"] = "equinet_confirmed_fullenrich_personal_email_mapping_pending"
    for item in mapping["dependencies"]:
        if "business-field-catalogue" in item["path"]: item.update(path=str(cat_json.relative_to(ROOT)), sha256=sha(cat_json))
    personal_map = next(x for x in mapping["mappings"] if x["canonical_field"] == "person.personal_email_candidate")
    personal_map["mapping_status"] = "canonical_only_hubspot_mapping_pending"
    personal_map["direction"] = "canonical_only"
    personal_map["hubspot_destinations"] = []
    personal_map["workflow_dependency_status"] = "not_applicable"
    personal_map["write_authorized"] = False
    mapping_json = ROOT / "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.3.1.json"; mapping_csv_path = ROOT / "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.3.1.csv"
    dump(mapping_json, mapping); mapping_csv(mapping, mapping_csv_path)

    integration = copy.deepcopy(load(ROOT / "foundations/contracts/integrations/a2-fullenrich-n8n-integration-0.1.0.json"))
    integration["version"] = "0.1.1"; integration["status"] = "design_approved_runtime_not_connected"
    integration["decision_record"] = {"path": str(decision_json.relative_to(ROOT)), "sha256": sha(decision_json)}
    integration["operations"]["contact_enrich"]["prohibited_enrich_fields"] = ["contact.personal_emails"]
    integration["operations"]["contact_enrich"]["incidental_personal_email"] = "retain_as_person.personal_email_candidate_with_provenance_status_and_human_review"
    integration["output_minimisation"]["contact"].extend(["personal_email_candidate", "personal_email_status"])
    integration["output_minimisation"]["discard"] = [x for x in integration["output_minimisation"]["discard"] if x != "personal_emails"]
    integration["output_minimisation"]["personal_email_rule"] = "not_requested_by_default_retain_if_incidentally_returned"
    integration["dependencies"] = [
        {"path": str(source_json.relative_to(ROOT)), "sha256": sha(source_json)},
        {"path": str(provider_json.relative_to(ROOT)), "sha256": sha(provider_json)},
        {"path": str(cat_json.relative_to(ROOT)), "sha256": sha(cat_json)},
        {"path": str(decision_json.relative_to(ROOT)), "sha256": sha(decision_json)}
    ]
    integration_json = ROOT / "foundations/contracts/integrations/a2-fullenrich-n8n-integration-0.1.1.json"; dump(integration_json, integration)

    print(json.dumps({"status": "personal_email_patch_written", "business_configuration_version": "0.3.1", "decision": str(decision_json.relative_to(ROOT)), "integration_contract_version": "0.1.1"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
