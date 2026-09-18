#!/usr/bin/env python3
"""Profile the Equinet HubSpot property export for A2 Enrichment design."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

SOURCE = Path("/opt/data/profiles/equinet/attachments/Property_Definitions (1).csv")
OUTPUT_DIR = Path("/opt/data/profiles/equinet-a2-enrichment/evaluations/hubspot-intake")
SUMMARY_PATH = OUTPUT_DIR / "property-inventory-summary.json"
RELEVANT_PATH = OUTPUT_DIR / "a2-relevant-properties.csv"

CATEGORY_PATTERNS = {
    "identity_and_contact": [
        r"\bname\b", r"email", r"phone", r"address", r"city", r"state", r"country",
        r"postal", r"zip", r"website", r"domain", r"job title", r"role", r"company type",
        r"contact type", r"trade name", r"stable / farm name", r"clinic / practice name",
    ],
    "equine_and_professional": [
        r"farrier", r"horse", r"stable", r"discipline", r"breed", r"certification",
        r"years of experience", r"association membership", r"practice type", r"speciality",
        r"aaep", r"kaep", r"dvm", r"board certified", r"primary horse relationship",
    ],
    "quality_and_enrichment": [
        r"data quality", r"verified", r"contact verified", r"has been enriched",
        r"enrichment opt out", r"invalid email", r"quarantined", r"bounce",
    ],
    "consent_and_suppression": [
        r"consent", r"opt.?in", r"opted out", r"do not contact", r"unsubscribed",
        r"legal basis", r"marketing contact status", r"communication opt",
    ],
    "customer_and_exclusion": [
        r"current customer", r"lifecycle stage", r"lead status", r"relationship stage",
        r"relationship status", r"active opportunity", r"associated deals", r"open deals",
        r"currently in sequence", r"prospecting agent enrollment", r"subscription status",
        r"account status", r"type$",
    ],
    "ownership_and_routing": [
        r"owner", r"assigned rep", r"territory", r"hubspot team", r"shared teams",
        r"shared users", r"brands", r"business unit", r"region priority",
    ],
    "qualification_and_score": [
        r"ideal customer profile", r"score", r"priority", r"buying role", r"beachhead",
        r"intent signal", r"journey stage", r"conversion stage", r"target account",
    ],
    "activity_and_freshness": [
        r"last activity", r"last contacted", r"last engagement", r"last modified",
        r"recent", r"first engagement", r"last app activity", r"date entered current stage",
    ],
    "external_ids_and_associations": [
        r"record id", r"associated", r"merged", r"erp account id", r"equinet user id",
        r"parent company", r"company domain", r"user id",
    ],
}

MATERIAL_INTERNAL_NAMES = {
    "email", "secondary_email", "work_email", "phone", "mobilephone", "secondary_phone_number",
    "firstname", "lastname", "jobtitle", "company", "website", "hs_linkedin_url", "facebook_url",
    "address", "street_address_line_2", "city", "state", "zip", "country",
    "contact_type", "farrier_active_flag", "farrier_certifications", "disciplines_worked_with",
    "farrier_primary_discipline", "farrier_horses_served", "years_experience", "farrier_school",
    "owner_horse_count", "horse_count_range", "owner_primary_discipline", "owner_breeds",
    "owner_stable_name", "stable_type", "horse_relationship", "association_member",
    "contact_verified", "data_quality", "exclude_from_data_quality", "hs_is_enriched",
    "hs_contact_enrichment_opt_out", "hs_contact_enrichment_opt_out_timestamp",
    "do_not_contact", "gdpr_consent", "hs_legal_basis", "marketing_email_opt_in_yes",
    "mailing_opt_in", "sms_opt_in", "whatsapp_opt_in", "hs_email_optout",
    "hs_marketable_status", "lifecyclestage", "hs_lead_status", "hs_current_customer",
    "hs_sequences_is_enrolled", "hs_currently_enrolled_in_prospecting_agent",
    "hubspot_owner_id", "equinet_assigned_rep", "territory", "hubspot_team_id",
    "hs_all_assigned_business_unit_ids", "hs_object_id", "hs_merged_object_ids",
    "hs_ideal_customer_profile", "hs_predictivescoringtier", "hs_predictivecontactscore_v2",
    "domain", "name", "company_type", "business_type", "company_email", "mailing_verified",
    "account_status", "active_mustad_dealer", "lead_source", "relationship_stage",
    "mustad_account_id", "num_associated_contacts", "num_associated_deals", "hs_num_open_deals",
}


def as_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def classify(row: dict) -> list[str]:
    searchable = " ".join([
        row.get("Property label", ""),
        row.get("Internal name", ""),
        row.get("Description", ""),
    ]).lower()
    categories = []
    for category, patterns in CATEGORY_PATTERNS.items():
        if any(re.search(pattern, searchable, flags=re.I) for pattern in patterns):
            categories.append(category)
    if row.get("Internal name") in MATERIAL_INTERNAL_NAMES:
        categories.append("explicit_a2_candidate")
    return sorted(set(categories))


def main() -> None:
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    object_rows = defaultdict(list)
    for row in rows:
        object_rows[row["Object"]].append(row)

    object_summary = {}
    for object_name, object_items in sorted(object_rows.items()):
        object_summary[object_name] = {
            "object_type_ids": sorted({row["Object Type ID"] for row in object_items}),
            "property_count": len(object_items),
            "read_only_count": sum(as_bool(row["Read only"]) for row in object_items),
            "writable_count": sum(not as_bool(row["Read only"]) for row in object_items),
            "aggregation_only_count": sum(as_bool(row["Aggregation only"]) for row in object_items),
            "unique_lookup_count": sum(as_bool(row["Unique lookup property"]) for row in object_items),
            "enumeration_count": sum(row["Type"] == "enumeration" for row in object_items),
            "with_options_count": sum(bool(row["Options (label [value])"].strip()) for row in object_items),
            "with_pipeline_stages_count": sum(bool(row["Pipeline stages (pipeline > stage [value])"].strip()) for row in object_items),
            "missing_description_count": sum(not row["Description"].strip() for row in object_items),
            "missing_group_count": sum(not row["Group"].strip() for row in object_items),
        }

    duplicate_internal_names = []
    duplicate_labels = []
    for object_name, object_items in sorted(object_rows.items()):
        by_internal = defaultdict(list)
        by_label = defaultdict(list)
        for row in object_items:
            by_internal[row["Internal name"]].append(row["Property label"])
            by_label[row["Property label"]].append(row["Internal name"])
        for internal_name, labels in by_internal.items():
            if len(labels) > 1:
                duplicate_internal_names.append({"object": object_name, "internal_name": internal_name, "labels": labels})
        for label, internal_names in by_label.items():
            if len(internal_names) > 1:
                duplicate_labels.append({"object": object_name, "label": label, "internal_names": internal_names})

    relevant_rows = []
    category_counts = Counter()
    for row in rows:
        categories = classify(row)
        if categories:
            category_counts.update(categories)
            output_row = {
                "Object": row["Object"],
                "Object Type ID": row["Object Type ID"],
                "Property label": row["Property label"],
                "Internal name": row["Internal name"],
                "Type": row["Type"],
                "Field type": row["Field type"],
                "Read only": row["Read only"],
                "Unique lookup property": row["Unique lookup property"],
                "Categories": ";".join(categories),
                "Options": row["Options (label [value])"],
                "Pipeline stages": row["Pipeline stages (pipeline > stage [value])"],
            }
            relevant_rows.append(output_row)

    relevant_rows.sort(key=lambda item: (item["Object"], item["Property label"].lower(), item["Internal name"]))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with RELEVANT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(relevant_rows[0]))
        writer.writeheader()
        writer.writerows(relevant_rows)

    exact_checks = {}
    index = {(row["Object"], row["Internal name"]): row for row in rows}
    for object_name, internal_name in [
        ("Contact", "email"),
        ("Contact", "contact_verified"),
        ("Contact", "data_quality"),
        ("Contact", "hs_contact_enrichment_opt_out"),
        ("Contact", "do_not_contact"),
        ("Contact", "gdpr_consent"),
        ("Contact", "hs_legal_basis"),
        ("Contact", "hs_email_optout"),
        ("Contact", "hs_current_customer"),
        ("Contact", "lifecyclestage"),
        ("Contact", "hs_sequences_is_enrolled"),
        ("Contact", "owner_horse_count"),
        ("Contact", "horse_count_range"),
        ("Contact", "farrier_horses_served"),
        ("Contact", "disciplines_worked_with"),
        ("Company", "domain"),
        ("Company", "data_quality"),
        ("Company", "do_not_contact"),
        ("Company", "hs_current_customer"),
        ("Company", "company_type"),
        ("Deal", "dealstage"),
    ]:
        row = index.get((object_name, internal_name))
        exact_checks[f"{object_name}.{internal_name}"] = None if row is None else {
            "label": row["Property label"],
            "type": row["Type"],
            "read_only": as_bool(row["Read only"]),
            "unique_lookup": as_bool(row["Unique lookup property"]),
            "options": row["Options (label [value])"],
            "pipeline_stages": row["Pipeline stages (pipeline > stage [value])"],
        }

    summary = {
        "source": str(SOURCE),
        "row_count": len(rows),
        "column_count": len(rows[0]),
        "columns": list(rows[0]),
        "objects": object_summary,
        "object_count": len(object_summary),
        "object_type_ids": sorted({(row["Object"], row["Object Type ID"]) for row in rows}),
        "property_types": dict(Counter(row["Type"] or "<blank>" for row in rows)),
        "field_types": dict(Counter(row["Field type"] or "<blank>" for row in rows)),
        "duplicate_internal_names": duplicate_internal_names,
        "duplicate_labels": duplicate_labels,
        "relevant_property_count": len(relevant_rows),
        "relevant_category_counts": dict(category_counts),
        "exact_checks": exact_checks,
        "coverage_limitations": [
            "The export contains property definitions for six objects only.",
            "The export does not include live records, fill rates, property history, workflow usage or access scopes.",
            "Descriptions, groups and data-entry instructions are mostly empty and cannot establish business meaning by themselves.",
            "The image contains additional HubSpot objects not represented in this property export.",
        ],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "rows": len(rows),
        "objects": object_summary,
        "relevant_property_count": len(relevant_rows),
        "duplicate_internal_names": len(duplicate_internal_names),
        "duplicate_labels": len(duplicate_labels),
        "summary": str(SUMMARY_PATH),
        "relevant_csv": str(RELEVANT_PATH),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
