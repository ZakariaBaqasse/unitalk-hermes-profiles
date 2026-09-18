#!/usr/bin/env python3
"""Validate the provisional Step 3A A2 Business Field Catalogue."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

PROFILE_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROFILE_ROOT / "foundations" / "contracts" / "business"
CATALOGUE_PATH = ROOT / "a2-business-field-catalogue-0.1.0-draft.1.json"
CSV_PATH = ROOT / "a2-business-field-catalogue-0.1.0-draft.1.csv"
CONTRACT_PATH = PROFILE_ROOT / "foundations" / "A2-BUSINESS-FIELD-CATALOGUE.md"
EVAL_ROOT = PROFILE_ROOT / "evaluations" / "step3a"
REVIEW_PATH = EVAL_ROOT / "A2-BUSINESS-FIELD-CATALOGUE-REVIEW.md"
OUTPUT = EVAL_ROOT / "technical-validation.json"
MANIFEST = EVAL_ROOT / "step3a-draft-package-manifest.json"
A1_ICP = PROFILE_ROOT / "foundations" / "contracts" / "dependencies" / "a1-equinet-icp-v1.yaml"
BUILDER = PROFILE_ROOT / "scripts" / "build_step3a_business_field_catalogue.py"
VALIDATOR = Path(__file__).resolve()
DECISION_PACK = PROFILE_ROOT / "foundations" / "sources" / "A2-SOURCE-AND-FIELD-DECISION-PACK.md"
STEP2I_ACCEPTANCE = PROFILE_ROOT / "evaluations" / "step2i" / "acceptance-record.json"
LANGUAGE_AUDIT = PROFILE_ROOT / "evaluations" / "foundation-clarifications" / "language-audit.json"

ALLOWED_SEGMENTS = {"farrier", "horse_owner"}
ALLOWED_PRIORITIES = {"required", "conditional_required", "optional", "do_not_collect"}
ALLOWED_TYPES = {"string", "enum", "date", "datetime", "integer", "number", "boolean", "string_array", "number_array", "structured"}
ALLOWED_SCOPES = {"person", "organisation", "relationship", "network", "record"}
REQUIRED_COMPATIBILITY_FIELDS = {
    "person.full_name": "string",
    "person.role_title": "string",
    "person.business_email": "string",
    "person.personal_email_candidate": "string",
    "person.professional_credential": "string",
    "organisation.business_name": "string",
    "organisation.website": "string",
    "organisation.service_area": "string_array",
    "organisation.horse_count": "integer",
    "organisation.disciplines": "string_array",
    "relationship.role": "string",
}
EXPECTED_HORSE_BANDS = [
    ("1", 1, 1),
    ("2_4", 2, 4),
    ("5_10", 5, 10),
    ("11_25", 11, 25),
    ("26_50", 26, 50),
    ("51_plus", 51, None),
]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_catalogue(catalogue: dict) -> list[str]:
    errors: list[str] = []
    required_top = {
        "catalogue_id", "version", "status", "profile", "canonical_schema_version", "decision_basis",
        "segments", "priority_values", "target_role_model", "contact_selection_policy", "missing_required_field_policy", "horse_count_policy",
        "collection_boundaries", "fields", "open_equinet_confirmations", "next_gate_after_approval",
    }
    if set(catalogue) != required_top:
        errors.append("top-level catalogue keys mismatch")
    if catalogue.get("version") != "0.1.0-draft.1":
        errors.append("catalogue version must be 0.1.0-draft.1")
    if catalogue.get("status") != "approved_by_unitalk_as_working_baseline_pending_equinet_confirmation":
        errors.append("catalogue status must be the approved Unitalk working baseline pending Equinet confirmation")
    if catalogue.get("canonical_schema_version") != "1.0.0":
        errors.append("canonical schema version must be 1.0.0")
    decision = catalogue.get("decision_basis", {})
    if decision.get("equinet_confirmation") != "pending":
        errors.append("Equinet confirmation must remain pending")
    if any(decision.get(key) is not False for key in ["approved_for_live_collection", "approved_for_pilot", "approved_for_crm_write"]):
        errors.append("draft catalogue must not authorise live collection, pilot use or CRM write")
    if set(catalogue.get("segments", [])) != ALLOWED_SEGMENTS:
        errors.append("segment set mismatch")
    if set(catalogue.get("priority_values", [])) != ALLOWED_PRIORITIES:
        errors.append("priority vocabulary mismatch")

    fields = catalogue.get("fields", [])
    keys = [item.get("field_key") for item in fields]
    if len(keys) != len(set(keys)):
        errors.append("duplicate field_key values are not allowed")
    a1_criteria = set(re.findall(r"criterion_id:\s*([a-z0-9_.-]+)", A1_ICP.read_text(encoding="utf-8")))
    for item in fields:
        key = item.get("field_key", "")
        scope = item.get("scope")
        if not re.fullmatch(r"[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*", key):
            errors.append(f"invalid field_key format: {key}")
        if scope not in ALLOWED_SCOPES or not key.startswith(f"{scope}."):
            errors.append(f"field scope/key mismatch: {key}")
        if item.get("value_type") not in ALLOWED_TYPES:
            errors.append(f"unsupported value_type: {key}")
        segments = set(item.get("allowed_segments", []))
        priorities = item.get("priority_by_segment", {})
        if not segments or not segments.issubset(ALLOWED_SEGMENTS):
            errors.append(f"invalid allowed_segments: {key}")
        if set(priorities) != segments:
            errors.append(f"priority coverage mismatch: {key}")
        if not set(priorities.values()).issubset(ALLOWED_PRIORITIES):
            errors.append(f"invalid priority value: {key}")
        if item.get("value_type") == "enum":
            enum_values = item.get("enum_values")
            if not enum_values or len(enum_values) != len(set(enum_values)):
                errors.append(f"enum values missing or duplicated: {key}")
        elif item.get("enum_values") is not None:
            errors.append(f"non-enum field defines enum_values: {key}")
        if "do_not_collect" in priorities.values():
            if not str(item.get("collection_policy", "")).startswith("disabled_"):
                errors.append(f"do_not_collect field is not disabled: {key}")
            if item.get("paid_lookup_allowed") is not False:
                errors.append(f"do_not_collect field permits paid lookup: {key}")
        for criterion in item.get("a1_requalification_criterion_ids", []):
            if criterion not in a1_criteria:
                errors.append(f"unknown A1 criterion_id {criterion}: {key}")
        for candidate in item.get("mapping_candidates", []):
            if candidate.get("status") != "mapping_candidate_only":
                errors.append(f"mapping candidate claims operational authority: {key}")

    field_map = {item["field_key"]: item for item in fields}
    for key, expected_type in REQUIRED_COMPATIBILITY_FIELDS.items():
        if key not in field_map:
            errors.append(f"missing canonical compatibility field: {key}")
        elif field_map[key]["value_type"] != expected_type:
            errors.append(f"canonical compatibility field type mismatch: {key}")

    personal_email = field_map.get("person.personal_email_candidate")
    if not personal_email or personal_email.get("collection_policy") != "review_only_pending_privacy_retention_and_human_decision" or personal_email.get("approval_rule") != "explicit_human_privacy_review_required_no_crm_or_outreach":
        errors.append("personal email candidate boundary mismatch")

    role_model = catalogue.get("target_role_model", {})
    if "student_apprentice" not in role_model.get("farrier", {}).get("review_only", []):
        errors.append("student_apprentice must remain review_only")
    if role_model.get("source_role_title_must_be_preserved") is not True:
        errors.append("source role title preservation is required")
    if role_model.get("buying_role_is_recommendation_only") is not True:
        errors.append("buying role must remain recommendation-only")
    for segment in ALLOWED_SEGMENTS:
        values = []
        for category in ["primary", "secondary", "review_only", "excluded"]:
            values.extend(role_model.get(segment, {}).get(category, []))
        if len(values) != len(set(values)):
            errors.append(f"role appears in multiple priorities: {segment}")

    contact = catalogue.get("contact_selection_policy", {})
    if contact.get("maximum_named_contacts") != 3 or contact.get("primary_target_role_contacts") != 1 or contact.get("additional_role_relevant_contacts") != 2:
        errors.append("contact-selection limit differs from the Unitalk proposal")
    if contact.get("fallback_when_no_target_role") != "retain_general_organisation_contact_and_mark_target_role_not_found":
        errors.append("contact fallback differs from the Unitalk proposal")
    if contact.get("minimum_review_contactability") != "verified_professional_email_or_verified_business_phone":
        errors.append("minimum contactability differs from the Unitalk proposal")
    if contact.get("review_readiness_does_not_establish_outreach_eligibility") is not True:
        errors.append("review readiness must not establish outreach eligibility")

    missing_required = catalogue.get("missing_required_field_policy", {})
    expected_missing_required = {
        "field_quality_status": "gap",
        "record_data_quality_status": "incomplete",
        "automatic_rejection": False,
        "automatic_a1_score_change": False,
        "external_action_authorized": False,
        "visible_in_review_package": True,
        "permitted_workflow_outcomes": ["enrichment_in_progress", "held", "changes_requested"],
        "resolution_options": ["approved_targeted_research", "human_correction", "documented_exception"],
    }
    if missing_required != expected_missing_required:
        errors.append("missing required field policy differs from the approved Unitalk baseline")

    policy = catalogue.get("horse_count_policy", {})
    actual_bands = [(item.get("value"), item.get("minimum"), item.get("maximum")) for item in policy.get("bands", [])]
    if actual_bands != EXPECTED_HORSE_BANDS:
        errors.append("horse-count bands are missing, overlapping or changed")
    if policy.get("exact_count_authority") != "verified_explicit_value_only" or policy.get("inference_prohibited") is not True:
        errors.append("horse-count exact-value boundary is invalid")
    if policy.get("derived_band_use") != "a2_review_only" or policy.get("hubspot_horse_count_range") != "protected_baseline_no_write":
        errors.append("horse-count derived-band or HubSpot boundary is invalid")
    if policy.get("new_hubspot_property_proposed") is not False:
        errors.append("catalogue must not propose a new HubSpot horse-count property")

    boundaries = catalogue.get("collection_boundaries", {})
    required_boundaries = {
        "reuse_a1_before_new_research": True,
        "new_research_requires_named_gap_conflict_verification_or_freshness_need": True,
        "public_professional_information_does_not_create_outreach_eligibility": True,
        "personal_email_and_mobile_paid_discovery": "disabled_pending_equinet_approval",
        "automated_linkedin_or_social_extraction": "blocked_pending_rights_and_integration_approval",
        "named_client_identity_collection": "prohibited",
        "crm_mapping_candidates_are_not_write_authority": True,
    }
    for key, expected in required_boundaries.items():
        if boundaries.get(key) != expected:
            errors.append(f"collection boundary mismatch: {key}")
    return errors


def negative_regressions(catalogue: dict) -> list[dict]:
    cases: list[tuple[str, str, Any]] = []

    def mutate(name: str, expected: str, fn) -> None:
        value = copy.deepcopy(catalogue)
        fn(value)
        cases.append((name, expected, value))

    mutate("duplicate_field", "duplicate field_key", lambda value: value["fields"].append(copy.deepcopy(value["fields"][0])))
    mutate("invalid_key_format", "invalid field_key format", lambda value: value["fields"][0].update(field_key="***"))
    mutate("scope_mismatch", "field scope/key mismatch", lambda value: value["fields"][0].update(scope="organisation"))
    mutate("unknown_type", "unsupported value_type", lambda value: value["fields"][0].update(value_type="free_form_any"))
    mutate("missing_segment_priority", "priority coverage mismatch", lambda value: value["fields"][0]["priority_by_segment"].pop("horse_owner"))
    mutate("enabled_do_not_collect", "do_not_collect field is not disabled", lambda value: next(item for item in value["fields"] if item["field_key"] == "person.mobile_phone").update(collection_policy="permitted_for_proposal"))
    mutate("paid_mobile_lookup", "do_not_collect field permits paid lookup", lambda value: next(item for item in value["fields"] if item["field_key"] == "person.mobile_phone").update(paid_lookup_allowed=True))
    mutate("unknown_a1_criterion", "unknown A1 criterion_id", lambda value: value["fields"][0].update(a1_requalification_criterion_ids=["a1.unknown_criterion"]))
    mutate("overlapping_horse_bands", "horse-count bands", lambda value: value["horse_count_policy"]["bands"][2].update(minimum=4))
    mutate("bad_contact_fallback", "contact fallback", lambda value: value["contact_selection_policy"].update(fallback_when_no_target_role="invent_contact"))
    mutate("outreach_inference", "review readiness must not establish outreach eligibility", lambda value: value["contact_selection_policy"].update(review_readiness_does_not_establish_outreach_eligibility=False))
    mutate("mapping_claims_authority", "mapping candidate claims operational authority", lambda value: value["fields"][0]["mapping_candidates"][0].update(status="approved_for_write"))
    mutate("missing_required_auto_reject", "missing required field policy", lambda value: value["missing_required_field_policy"].update(automatic_rejection=True))
    mutate("personal_email_operational", "personal email candidate boundary mismatch", lambda value: next(item for item in value["fields"] if item["field_key"] == "person.personal_email_candidate").update(collection_policy="permitted_for_proposal"))

    results = []
    for name, expected, value in cases:
        errors = validate_catalogue(value)
        passed = any(expected in error for error in errors)
        results.append({"name": name, "expected_error": expected, "errors": errors, "passed": passed})
    return results


def priority_counts(catalogue: dict) -> dict:
    return {
        segment: {
            priority: sum(item["priority_by_segment"].get(segment) == priority for item in catalogue["fields"])
            for priority in ["required", "conditional_required", "optional", "do_not_collect"]
        }
        for segment in ["farrier", "horse_owner"]
    }


def render_documents(catalogue: dict, counts: dict) -> None:
    field_rows = []
    for item in catalogue["fields"]:
        field_rows.append(
            f"| `{item['field_key']}` | {item['label']} | {item['value_type']} | "
            f"{item['priority_by_segment'].get('farrier', 'N/A')} | {item['priority_by_segment'].get('horse_owner', 'N/A')} | {item['collection_policy']} |"
        )
    rows = "\n".join(field_rows)
    contract = f"""# Equinet A2 Business Field Catalogue\n\n**Version:** `0.1.0-draft.1`  \n**Status:** `APPROVED UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING`  \n**Profile:** `equinet-a2-enrichment`  \n**Step:** `3A — Business Field Catalogue`  \n**Canonical schema:** `1.0.0`\n\n## 1. Purpose\n\nThis catalogue defines the proposed business field keys, scopes, value types, segment applicability, priority, collection boundary, A1 requalification linkage and preliminary CRM mapping candidates for A2 Enrichment. It is external to the stable canonical schema.\n\nIt does not activate a source, provider, connector, CRM read or write, outreach action, pilot or production use.\n\n## 2. Decision status\n\nSéverine approved decisions 3A-1 through 3A-8 as the Unitalk working baseline on `2026-08-26T16:49:28Z`. Equinet business confirmation remains pending. Final Step 3A promotion must record Equinet approval or corrections to the target-role, contact-selection, contactability, horse-count and field-priority decisions.\n\n## 3. Proposed target roles\n\n### Farrier\n\n- Primary: Independent Farrier/Owner, Farrier Business Owner/Founder, Lead Farrier.\n- Secondary: Business or Office Administrator where commercially relevant.\n- Review-only: Student/Apprentice.\n\n### Horse Owner organisation\n\n- Primary: Owner/Founder, Farm or Stable Owner, Farm or Stable Manager, Trainer or Head Trainer, Breeding Manager.\n- Secondary: General Manager, Operations Manager.\n\nSource role wording is preserved. A Buying Role remains a recommendation requiring human approval.\n\n## 4. Contact-selection proposal\n\n- Retain one primary target-role contact and up to two additional role-relevant contacts.\n- If no target-role person is found, retain the organisation general contact and set `target_role_not_found`.\n- One verified professional email or one verified business phone satisfies proposed A2 review contactability.\n- A general organisation contact may satisfy review readiness.\n- Review readiness never proves consent or outreach eligibility.\n\n## 5. Missing Required field policy\n\nA missing Required field becomes a field-level `gap` and the record remains `incomplete`. It is visible in the review package and may remain `enrichment_in_progress`, move to `held` or receive `changes_requested`. It is never automatically rejected, never changes the A1 score by itself and never authorises an external action. Resolution is limited to approved targeted research, human correction or a documented exception.\n\n## 6. Horse-count proposal\n\n- Retain a verified exact count only when explicitly stated by an approved source or confirmed by Equinet.\n- Never infer horse count from property size, facilities, photographs, followers or similar indirect signals.\n- Derive an A2-only review band: `1`, `2_4`, `5_10`, `11_25`, `26_50`, `51_plus`.\n- Keep HubSpot `horse_count_range` as a protected baseline with no write in the no-integration pilot.\n- Do not create a new HubSpot property by default.\n\n## 7. Field catalogue\n\n| Field key | Label | Type | Farrier | Horse Owner | Collection policy |\n|---|---|---|---|---|---|\n{rows}\n\n## 8. Priority summary\n\n| Segment | Required | Conditional | Optional | Do not collect |\n|---|---:|---:|---:|---:|\n| Farrier | {counts['farrier']['required']} | {counts['farrier']['conditional_required']} | {counts['farrier']['optional']} | {counts['farrier']['do_not_collect']} |\n| Horse Owner | {counts['horse_owner']['required']} | {counts['horse_owner']['conditional_required']} | {counts['horse_owner']['optional']} | {counts['horse_owner']['do_not_collect']} |\n\n## 9. Deliberately disabled fields\n\n- mobile/direct-dial collection until Equinet approves the category, source and purpose;\n- broad social signals;\n- mutual connections;\n- horses served per month;\n- client-base summaries.\n\nNamed Farrier client identities remain prohibited by default.\n\n## 10. Mapping boundary\n\nHubSpot properties in this catalogue are mapping candidates only. The operational A2-to-HubSpot mapping remains Step 3G. A mapping candidate does not prove that HubSpot is connected, that the property is writable or that a write is approved.\n\n## 11. Remaining confirmations\n\n1. Target-role model by segment.\n2. Maximum named contacts and fallback.\n3. Minimum review contactability.\n4. Horse-count taxonomy and derivation.\n5. Required, Conditional Required, Optional and Do Not Collect classifications.\n6. Personal email and mobile/direct-dial policy before pilot.\n7. Primary A2 reviewer and backup before pilot.\n\n## 12. Next gate\n\nStep 3B may begin in draft form under the approved Unitalk working baseline. Final Step 3A promotion to `0.1.0` remains pending the identified Equinet business confirmations.\n"""
    CONTRACT_PATH.write_text(contract, encoding="utf-8")

    review = f"""# Decision Review — Step 3A Business Field Catalogue\n\n**Version:** `0.1.0-draft.1`  \n**Status:** `APPROVED AS UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING`  \n**Decision timestamp:** `2026-08-26T16:49:28Z`  \n**Profile status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`\n\n## 1. Proposal summary\n\n- Business fields: **{len(catalogue['fields'])}**.\n- Segments: Farrier and Horse Owner.\n- HubSpot references: mapping candidates only.\n- Live integrations or external actions: **none**.\n- Equinet confirmation: **pending**.\n\n## 2. Decisions approved as the Unitalk working baseline\n\n| ID | Decision |\n|---|---|\n| 3A-1 | Approve the proposed Farrier target roles and keep Student/Apprentice review-only. |\n| 3A-2 | Approve the proposed Horse Owner organisation target roles. |\n| 3A-3 | Retain one primary and up to two additional named contacts, with organisation general contact fallback. |\n| 3A-4 | Treat verified professional email OR verified business phone as sufficient for A2 review contactability. |\n| 3A-5 | Use verified exact horse count plus non-overlapping A2-only review bands; do not write the current HubSpot range. |\n| 3A-6 | A missing Required field creates a visible gap and an incomplete record; it does not automatically reject the prospect or change the A1 score. |\n| 3A-7 | Keep mobile/direct dial, broad social signals, mutual connections, horses-served volume and client-base summaries disabled. |\n| 3A-8 | Keep all HubSpot mappings proposed and non-operational until Step 3G and live read-only verification. |\n\n## 3. Priority counts\n\n| Segment | Required | Conditional | Optional | Do not collect |\n|---|---:|---:|---:|---:|\n| Farrier | {counts['farrier']['required']} | {counts['farrier']['conditional_required']} | {counts['farrier']['optional']} | {counts['farrier']['do_not_collect']} |\n| Horse Owner | {counts['horse_owner']['required']} | {counts['horse_owner']['conditional_required']} | {counts['horse_owner']['optional']} | {counts['horse_owner']['do_not_collect']} |\n\n## 4. Approval scope\n\nThis approval establishes the Unitalk working baseline and authorises preparation of Step 3B in draft form. Final promotion from `0.1.0-draft.1` to `0.1.0` remains pending the identified Equinet business confirmations. It does not authorise a source, provider, CRM access/write, outreach, pilot, production or contractual acceptance.\n"""
    EVAL_ROOT.mkdir(parents=True, exist_ok=True)
    REVIEW_PATH.write_text(review, encoding="utf-8")


def main() -> int:
    catalogue = load(CATALOGUE_PATH)
    counts = priority_counts(catalogue)
    render_documents(catalogue, counts)
    failures = validate_catalogue(catalogue)

    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    csv_keys = [row["field_key"] for row in rows]
    json_keys = [item["field_key"] for item in catalogue["fields"]]
    csv_checks = {
        "row_count": len(rows) == len(catalogue["fields"]),
        "field_order": csv_keys == json_keys,
        "value_types": [row["value_type"] for row in rows] == [item["value_type"] for item in catalogue["fields"]],
        "farrier_priorities": [row["farrier_priority"] for row in rows] == [item["priority_by_segment"].get("farrier", "not_applicable") for item in catalogue["fields"]],
        "horse_owner_priorities": [row["horse_owner_priority"] for row in rows] == [item["priority_by_segment"].get("horse_owner", "not_applicable") for item in catalogue["fields"]],
    }
    for name, passed in csv_checks.items():
        if not passed:
            failures.append(f"CSV fidelity check failed: {name}")

    negative = negative_regressions(catalogue)
    for case in negative:
        if not case["passed"]:
            failures.append(f"negative regression failed: {case['name']}")

    documentation_checks = {
        "contract_version": "**Version:** `0.1.0-draft.1`" in CONTRACT_PATH.read_text(encoding="utf-8"),
        "contract_pending": "EQUINET CONFIRMATION PENDING" in CONTRACT_PATH.read_text(encoding="utf-8"),
        "review_pending": "APPROVED AS UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING" in REVIEW_PATH.read_text(encoding="utf-8"),
        "decisions_3a1_to_3a8": all(f"| 3A-{number} |" in REVIEW_PATH.read_text(encoding="utf-8") for number in range(1, 9)),
        "step3b_boundary": "Step 3B" in CONTRACT_PATH.read_text(encoding="utf-8"),
    }
    for name, passed in documentation_checks.items():
        if not passed:
            failures.append(f"documentation check failed: {name}")

    language_audit = load(LANGUAGE_AUDIT)
    if language_audit.get("pass") is not True:
        failures.append("deployment-language audit failed")

    result = {
        "step": "3A",
        "catalogue_version": catalogue["version"],
        "approval_state": "approved_unitalk_working_baseline_pending_equinet_confirmation",
        "catalogue": {"path": str(CATALOGUE_PATH.relative_to(PROFILE_ROOT)), "sha256": sha256(CATALOGUE_PATH)},
        "csv": {"path": str(CSV_PATH.relative_to(PROFILE_ROOT)), "sha256": sha256(CSV_PATH)},
        "coverage": {
            "field_count": len(catalogue["fields"]),
            "segments": catalogue["segments"],
            "priority_counts": counts,
            "a1_requalification_linked_fields": sum(bool(item["a1_requalification_criterion_ids"]) for item in catalogue["fields"]),
            "mapping_candidate_fields": sum(bool(item["mapping_candidates"]) for item in catalogue["fields"]),
            "disabled_fields": sum(str(item["collection_policy"]).startswith("disabled_") for item in catalogue["fields"]),
        },
        "catalogue_validation": {"errors": validate_catalogue(catalogue), "passed": not validate_catalogue(catalogue)},
        "csv_fidelity": {"checks": csv_checks, "passed": all(csv_checks.values())},
        "negative_regressions": {
            "total": len(negative),
            "passed": sum(case["passed"] for case in negative),
            "failed": sum(not case["passed"] for case in negative),
            "cases": negative,
        },
        "documentation_checks": documentation_checks,
        "language_audit": {
            "files_checked": language_audit.get("files_checked"),
            "findings": len(language_audit.get("findings", [])),
            "passed": language_audit.get("pass") is True,
        },
        "equinet_confirmation": "pending",
        "live_collection_authorized": False,
        "external_actions": 0,
        "next_gate_after_approval": "Step 3B — Minimum Data Packages",
        "failures": failures,
        "pass": not failures,
    }
    EVAL_ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    package_paths = [
        CATALOGUE_PATH, CSV_PATH, CONTRACT_PATH, REVIEW_PATH, BUILDER, VALIDATOR,
        DECISION_PACK, STEP2I_ACCEPTANCE, OUTPUT,
    ]
    package_manifest = {
        "manifest_id": "equinet-a2-step3a-draft-package",
        "version": "0.1.0-draft.1",
        "status": "approved_unitalk_working_baseline_pending_equinet_confirmation",
        "files": [
            {"path": str(path.relative_to(PROFILE_ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in package_paths
        ],
        "file_count": len(package_paths),
        "external_actions": 0,
    }
    MANIFEST.write_text(json.dumps(package_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "pass": result["pass"],
        "approval_state": result["approval_state"],
        "field_count": result["coverage"]["field_count"],
        "priority_counts": counts,
        "negative_regressions": f"{result['negative_regressions']['passed']}/{result['negative_regressions']['total']}",
        "equinet_confirmation": result["equinet_confirmation"],
        "review": str(REVIEW_PATH),
        "manifest": str(MANIFEST),
        "failures": failures,
    }, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
