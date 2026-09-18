#!/usr/bin/env python3
"""Apply the approved SOC-1 to SOC-8 A2 foundation clarification."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TS = "2026-08-27T11:40:17Z"
OLD = "0.1.0-draft.1"
NEW = "0.1.1-draft.1"
CLAR = ROOT / "evaluations" / "foundation-clarifications" / "official-site-social-profile-url-capture"
BACKUP = CLAR / "pre-amendment"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def backup(path: Path) -> None:
    target = BACKUP / path.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(path, target)


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"Expected text not found: {old[:100]}")
    return text.replace(old, new, 1)


def csv_from_objects(path: Path, rows: list[dict[str, Any]], headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for item in rows:
            row = {}
            for key in headers:
                value = item.get(key)
                if isinstance(value, (list, dict)) or value is None or isinstance(value, bool):
                    row[key] = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                else:
                    row[key] = value
            writer.writerow(row)


# Preserve the active pre-amendment documents and SOUL.
for rel in [
    "SOUL.md",
    "deliverables/A2-DELIVERY-STATUS-AND-ROADMAP.md",
    "foundations/A2-BUSINESS-FIELD-CATALOGUE.md",
    "foundations/A2-MINIMUM-DATA-PACKAGES.md",
    "foundations/A2-SOURCE-REGISTER.md",
    "foundations/A2-EVIDENCE-VERIFICATION-CONFIDENCE-FRESHNESS-POLICY.md",
    "foundations/A2-PROTECTED-FIELDS-AND-CONFLICT-POLICY.md",
    "foundations/A2-PROVIDER-AND-COST-POLICY.md",
    "foundations/A2-PRELIMINARY-HUBSPOT-MAPPING.md",
]:
    backup(ROOT / rel)

# 1. Business Field Catalogue.
cat_old = ROOT / f"foundations/contracts/business/a2-business-field-catalogue-{OLD}.json"
cat_new = ROOT / f"foundations/contracts/business/a2-business-field-catalogue-{NEW}.json"
cat = load(cat_old)
cat["version"] = NEW
cat["decision_basis"]["authority"] = "Unitalk working baseline approved by Séverine, including SOC-1 through SOC-8 official-site social-profile URL clarification"
cat["decision_basis"]["unitalk_approved_at"] = TS
cat["decision_basis"]["clarification_ids"] = [f"SOC-{n}" for n in range(1, 9)]
cat["collection_boundaries"].update({
    "official_site_explicit_professional_social_links_permitted": True,
    "social_profile_content_extraction_requires_separate_approval": True,
    "public_profile_urls_do_not_create_consent_outreach_or_buying_influence": True,
})
fields = cat["fields"]
person = next(x for x in fields if x["field_key"] == "person.public_profile_urls")
person["description"] = (
    "Role-relevant public professional profile URLs explicitly linked from the official website, "
    "recorded by an authorised human, or returned through a separately approved official API. "
    "The link may be retained without opening or extracting the social profile."
)
org_key="organi...urls"
if not any(x["field_key"] == org_key for x in fields):
    new_field = {
        "field_key": org_key,
        "label": "Organisation public professional profile URLs",
        "description": (
            "Public business social-profile URLs explicitly linked from the organisation's official website, "
            "recorded by an authorised human, or returned through a separately approved official API. "
            "The link may be retained without opening or extracting the social profile."
        ),
        "scope": "organisation",
        "value_type": "string_array",
        "allowed_segments": ["farrier", "horse_owner"],
        "priority_by_segment": {"farrier": "optional", "horse_owner": "optional"},
        "collection_policy": "permitted_for_proposal",
        "data_category": "professional_business_data",
        "inference_policy": "not_permitted",
        "paid_lookup_allowed": False,
        "enum_values": None,
        "source_text_preserved": True,
        "a1_requalification_criterion_ids": [],
        "approval_rule": "human_review_required_during_pilot",
        "unknown_behaviour": "preserve_unknown_and_record_gap_when_required",
        "mapping_candidates": [],
    }
    idx = next(i for i, x in enumerate(fields) if x["field_key"] == "organisation.website_domain") + 1
    fields.insert(idx, new_field)
write_json(cat_new, cat)
cat_csv = ROOT / f"foundations/contracts/business/a2-business-field-catalogue-{NEW}.csv"
csv_from_objects(cat_csv, fields, [
    "field_key", "label", "scope", "value_type", "allowed_segments", "farrier_priority", "horse_owner_priority",
    "collection_policy", "data_category", "inference_policy", "paid_lookup_allowed", "enum_values",
    "a1_requalification_criterion_ids", "approval_rule", "unknown_behaviour", "mapping_candidates", "description",
])
# Correct the two projection-only priority columns.
with cat_csv.open(encoding="utf-8", newline="") as handle:
    cat_rows = list(csv.DictReader(handle))
for row, item in zip(cat_rows, fields):
    row["farrier_priority"] = item["priority_by_segment"].get("farrier", "not_applicable")
    row["horse_owner_priority"] = item["priority_by_segment"].get("horse_owner", "not_applicable")
with cat_csv.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(cat_rows[0]))
    writer.writeheader(); writer.writerows(cat_rows)

# 2. Minimum Data Packages dependency-only patch; social URLs stay optional.
min_old = ROOT / f"foundations/contracts/business/a2-minimum-data-packages-{OLD}.json"
min_new = ROOT / f"foundations/contracts/business/a2-minimum-data-packages-{NEW}.json"
minimum = load(min_old)
minimum["version"] = NEW
minimum["business_field_catalogue"].update(path=str(cat_new.relative_to(ROOT)), version=NEW, sha256=sha(cat_new))
minimum["clarification"] = {
    "approved_at": TS,
    "decision_ids": [f"SOC-{n}" for n in range(1, 9)],
    "public_profile_urls_optional": True,
    "minimum_package_requirements_changed": False,
}
write_json(min_new, minimum)

# 3. Source Register.
src_old = ROOT / f"foundations/contracts/sources/a2-source-register-{OLD}.json"
src_new = ROOT / f"foundations/contracts/sources/a2-source-register-{NEW}.json"
src = load(src_old)
src["version"] = NEW
src["global_rules"].update({
    "capture_explicit_official_site_professional_social_links": True,
    "do_not_open_or_extract_social_profiles_without_separate_approval": True,
    "social_links_do_not_create_consent_outreach_or_buying_influence": True,
})
by_source = {x["source_id"]: x for x in src["sources"]}
website = by_source["prospect_official_website"]
website["limits"].update({
    "capture_explicit_outbound_professional_social_links": True,
    "open_or_extract_linked_social_profiles": False,
})
website["notes"].extend([
    "Capture explicit outbound LinkedIn, Facebook, Instagram, YouTube and other clearly professional social-profile URLs found on approved official-site pages.",
    "Classify a link as person or organisation only when the official-page context supports that attribution; otherwise hold it as ambiguous.",
    "Retaining the URL does not authorise opening, crawling or extracting the linked social profile.",
])
actor = by_source["apify_harvestapi_linkedin_profile_search"]
actor["limits"].update({
    "input_preference": ["exact_linkedin_company_url", "verified_company_name_plus_target_role"],
    "individual_linkedin_profile_url_route": "manual_review_or_separately_approved_profile_scraper",
})
actor["notes"].extend([
    "Prefer an exact LinkedIn company URL explicitly published on the official website over company-name resolution.",
    "An individual LinkedIn profile URL is not routed to this search Actor; retain it for authorised human review or a separately approved profile-scraper action.",
])
write_json(src_new, src)
src_csv = ROOT / f"foundations/contracts/sources/a2-source-register-{NEW}.csv"
csv_from_objects(src_csv, src["sources"], [
    "source_id", "name", "source_type", "canonical_url", "business_approval", "source_rights_preflight",
    "runtime_readiness", "register_status", "purpose", "allowed_access_modes", "permitted_fields",
    "prohibited_fields", "limits", "notes",
])

# 4. Evidence policy.
ev_old = ROOT / f"foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-{OLD}.json"
ev_new = ROOT / f"foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-{NEW}.json"
ev = load(ev_old)
ev["version"] = NEW
ev["unitalk_approval"].update(approved_at=TS, scope="decisions_3D_1_through_3D_10_plus_SOC_1_through_SOC_8")
for dep in ev["dependencies"]:
    if "source-register" in dep["path"]:
        dep.update(path=str(src_new.relative_to(ROOT)), sha256=sha(src_new))
    elif "business-field-catalogue" in dep["path"]:
        dep.update(path=str(cat_new.relative_to(ROOT)), sha256=sha(cat_new))
ev["principles"].update({
    "official_site_outbound_professional_social_link_is_a_url_claim_not_social_profile_content": True,
    "public_profile_url_does_not_create_consent_outreach_or_buying_influence": True,
})
ev["field_freshness_days"][org_key] = 365
write_json(ev_new, ev)

# 5. Protected fields policy dependency refresh only.
prot_old = ROOT / f"foundations/contracts/governance/a2-protected-fields-and-conflict-policy-{OLD}.json"
prot_new = ROOT / f"foundations/contracts/governance/a2-protected-fields-and-conflict-policy-{NEW}.json"
prot = load(prot_old)
prot["version"] = NEW
prot["unitalk_approval"].update(approved_at=TS, scope="decisions_3E_1_through_3E_10_plus_SOC_1_through_SOC_8_dependency_refresh")
for dep in prot["dependencies"]:
    if "business-field-catalogue" in dep["path"]:
        dep.update(path=str(cat_new.relative_to(ROOT)), sha256=sha(cat_new))
    elif "evidence-verification-confidence" in dep["path"]:
        dep.update(path=str(ev_new.relative_to(ROOT)), sha256=sha(ev_new))
write_json(prot_new, prot)

# 6. Provider policy.
provider_old = ROOT / f"foundations/contracts/governance/a2-provider-and-cost-policy-{OLD}.json"
provider_new = ROOT / f"foundations/contracts/governance/a2-provider-and-cost-policy-{NEW}.json"
provider = load(provider_old)
provider["version"] = NEW
provider["unitalk_approval"].update(approved_at=TS, scope="decisions_3F_1_through_3F_10_plus_SOC_1_through_SOC_8")
for dep in provider["dependencies"]:
    if "source-register" in dep["path"]:
        dep.update(path=str(src_new.relative_to(ROOT)), sha256=sha(src_new))
psearch = provider["providers"]["apify_linkedin_profile_search"]
psearch["input_strategy"] = {
    "preferred": "exact_linkedin_company_url_from_official_website",
    "fallback": "verified_company_name_plus_target_role",
    "individual_profile_url": "manual_review_or_separately_approved_harvestapi_linkedin_profile_scraper",
    "no_broad_search_without_named_role_gap": True,
}
write_json(provider_new, provider)

# 7. Preliminary HubSpot mapping.
map_old = ROOT / f"foundations/contracts/mappings/a2-hubspot-preliminary-mapping-{OLD}.json"
map_new = ROOT / f"foundations/contracts/mappings/a2-hubspot-preliminary-mapping-{NEW}.json"
mapping = load(map_old)
mapping["version"] = NEW
mapping["unitalk_approval"].update(approved_at=TS, scope="decisions_3G_1_through_3G_10_plus_SOC_1_through_SOC_8")
for dep in mapping["dependencies"]:
    if "business-field-catalogue" in dep["path"]:
        dep.update(path=str(cat_new.relative_to(ROOT)), sha256=sha(cat_new))
if not any(x["canonical_field"] == org_key for x in mapping["mappings"]):
    entry = {
        "canonical_field": org_key,
        "scope": "organisation",
        "value_type": "string_array",
        "allowed_segments": ["farrier", "horse_owner"],
        "mapping_status": "canonical_only_no_hubspot_mapping",
        "direction": "canonical_only",
        "hubspot_destinations": [],
        "conversion": "enum_or_multivalue_conversion_pending",
        "baseline_authority": "hubspot_when_connected_else_validated_input",
        "populated_manual_value": "preserve_and_hold_on_difference",
        "workflow_dependency_status": "not_applicable",
        "write_authorized": False,
    }
    idx = next(i for i, x in enumerate(mapping["mappings"]) if x["canonical_field"] == "organisation.website_domain") + 1
    mapping["mappings"].insert(idx, entry)
write_json(map_new, mapping)
map_csv = ROOT / f"foundations/contracts/mappings/a2-hubspot-preliminary-mapping-{NEW}.csv"
csv_from_objects(map_csv, mapping["mappings"], [
    "canonical_field", "scope", "value_type", "allowed_segments", "mapping_status", "direction",
    "hubspot_destinations", "conversion", "baseline_authority", "populated_manual_value",
    "workflow_dependency_status", "write_authorized",
])

# 8. Active human-readable foundation documents.
md = ROOT / "foundations/A2-BUSINESS-FIELD-CATALOGUE.md"
text = md.read_text(encoding="utf-8")
text = replace_once(text, f"**Version:** `{OLD}`", f"**Version:** `{NEW}`")
text = replace_once(text, "Role-relevant public profile URLs collected manually or through an approved official API.", "Role-relevant public profile URLs explicitly linked from the official website, recorded by an authorised human or returned through a separately approved official API. Retaining a link does not authorise social-profile extraction.") if "Role-relevant public profile URLs collected manually or through an approved official API." in text else text
text = replace_once(text, "| `organisation.website_domain` | Official website domain | string | optional | optional | permitted_for_proposal |", "| `organisation.website_domain` | Official website domain | string | optional | optional | permitted_for_proposal |\n| `organisation.public_profile_urls` | Organisation public professional profile URLs | string_array | optional | optional | permitted_for_proposal |")
text = replace_once(text, "| Farrier | 7 | 5 | 11 | 5 |", "| Farrier | 7 | 5 | 12 | 5 |")
text = replace_once(text, "| Horse Owner | 3 | 7 | 12 | 3 |", "| Horse Owner | 3 | 7 | 13 | 3 |")
text += "\n## 13. SOC-1 to SOC-8 clarification\n\nExplicit professional social-profile links published on an approved official website may be retained as optional person or organisation URLs. The linked social profile is not opened or extracted automatically. These URLs do not create consent, outreach eligibility or buying influence.\n"
md.write_text(text, encoding="utf-8")

md = ROOT / "foundations/A2-MINIMUM-DATA-PACKAGES.md"
text = replace_once(md.read_text(encoding="utf-8"), f"**Version:** `{OLD}`", f"**Version:** `{NEW}`")
text += "\n## 7. SOC clarification\n\nPerson and organisation public professional profile URLs remain optional and do not change either segment's minimum review-ready package.\n"
md.write_text(text, encoding="utf-8")

md = ROOT / "foundations/A2-SOURCE-REGISTER.md"
text = replace_once(md.read_text(encoding="utf-8"), f"**Version:** `{OLD}`", f"**Version:** `{NEW}`")
text = replace_once(text, "For each retained Farrier or Horse Owner candidate, check the official site when it exists. Use at most five pages: primary page, About/Team, Services, Contact/Location and one relevant dated page when available. Allow at most one targeted retry per failed URL. Stop on terms/robots denial, login/paywall, CAPTCHA, 403, 429, unexpected personal data or scope/budget limit.", "For each retained Farrier or Horse Owner candidate, check the official site when it exists. Use at most five pages: primary page, About/Team, Services, Contact/Location and one relevant dated page when available. Capture explicit outbound LinkedIn, Facebook, Instagram, YouTube and other clearly professional social-profile URLs shown on those pages. Attribute a URL to a person or organisation only when the page context supports it; otherwise hold it as ambiguous. Retaining a URL does not authorise opening, crawling or extracting the linked social profile. Allow at most one targeted retry per failed URL. Stop on terms/robots denial, login/paywall, CAPTCHA, 403, 429, unexpected personal data or scope/budget limit.")
text = replace_once(text, "- Confirmed trigger: only for a named role/contact gap after the official-site check.", "- Confirmed trigger: only for a named role/contact gap after the official-site check.\n- Preferred input: exact LinkedIn company URL explicitly published on the official website; fallback: verified company name plus target role.\n- An individual LinkedIn profile URL is retained for human review or a separately approved profile-scraper action; it is not routed to the profile-search Actor.")
md.write_text(text, encoding="utf-8")

md = ROOT / "foundations/A2-EVIDENCE-VERIFICATION-CONFIDENCE-FRESHNESS-POLICY.md"
text = replace_once(md.read_text(encoding="utf-8"), f"**Version:** `{OLD}`", f"**Version:** `{NEW}`")
text = replace_once(text, "- A current official website can confirm explicit facts controlled by the business without a visible publication date.", "- A current official website can confirm explicit facts controlled by the business without a visible publication date.\n- An explicit outbound professional social-profile link on the official site verifies the existence of that published URL only; it does not verify the linked profile's contents, consent, outreach eligibility or buying influence.")
text = replace_once(text, "| `person.public_profile_urls` | 365 days |", "| `person.public_profile_urls` | 365 days |\n| `organisation.public_profile_urls` | 365 days |")
md.write_text(text, encoding="utf-8")

md = ROOT / "foundations/A2-PROTECTED-FIELDS-AND-CONFLICT-POLICY.md"
text = replace_once(md.read_text(encoding="utf-8"), f"**Version:** `{OLD}`", f"**Version:** `{NEW}`")
text += "\n## 9. SOC dependency clarification\n\nThe addition of optional organisation public-profile URLs does not weaken protected-field, consent, suppression, owner, lifecycle, Deal, sequence or manual-value controls.\n"
md.write_text(text, encoding="utf-8")

md = ROOT / "foundations/A2-PROVIDER-AND-COST-POLICY.md"
text = replace_once(md.read_text(encoding="utf-8"), f"**Version:** `{OLD}`", f"**Version:** `{NEW}`")
text = replace_once(text, "- Apify `harvestapi/linkedin-profile-search` for bounded role/company matching after an official-site gap.", "- Apify `harvestapi/linkedin-profile-search` for bounded role/company matching after an official-site gap. Prefer an exact LinkedIn company URL explicitly published on the official website; use verified company name plus target role only as fallback.\n- An individual LinkedIn profile URL is reserved for authorised human review or a separately approved `harvestapi/linkedin-profile-scraper` action; it is not an input to the selected profile-search route.")
md.write_text(text, encoding="utf-8")

md = ROOT / "foundations/A2-PRELIMINARY-HUBSPOT-MAPPING.md"
text = replace_once(md.read_text(encoding="utf-8"), f"**Version:** `{OLD}`", f"**Version:** `{NEW}`")
text = replace_once(text, "| `organisation.website_domain` | `proposed_unverified` | Company.domain | `direct_string` |", "| `organisation.website_domain` | `proposed_unverified` | Company.domain | `direct_string` |\n| `organisation.public_profile_urls` | `canonical_only_no_hubspot_mapping` | None | `enum_or_multivalue_conversion_pending` |")
text = replace_once(text, '"canonical_only_no_hubspot_mapping": 5', '"canonical_only_no_hubspot_mapping": 6')
md.write_text(text, encoding="utf-8")

# 9. Active SOUL patch; the Step 4 accepted snapshot remains untouched.
soul = ROOT / "SOUL.md"
text = soul.read_text(encoding="utf-8")
for label in [
    "Business Field Catalogue", "Minimum Data Packages", "A2 Source Register",
    "Evidence, Verification, Confidence and Freshness Policy", "Protected Fields and Conflict Policy",
    "Provider and Cost Policy", "Preliminary A2-to-HubSpot Mapping",
]:
    text = text.replace(f"{label} `{OLD}`", f"{label} `{NEW}`")
text = replace_once(text, "Check the official website for each retained prospect when one exists. Use bounded public pages, stop on terms/robots denial, login, paywall, CAPTCHA, `403`, `429`, unexpected personal data or a scope limit, and never guess blocked content.", "Check the official website for each retained prospect when one exists. Use bounded public pages, stop on terms/robots denial, login, paywall, CAPTCHA, `403`, `429`, unexpected personal data or a scope limit, and never guess blocked content. Capture explicit outbound LinkedIn, Facebook, Instagram, YouTube and other clearly professional social-profile URLs shown on those approved pages. Attribute them to a person or organisation only when the page context supports it; otherwise hold the attribution for review. Retaining a URL does not authorise opening or extracting the linked social profile and does not establish consent, outreach eligibility or buying influence.")
text = replace_once(text, "`harvestapi/linkedin-profile-search` is business-approved for the A2 purpose but not runtime-active. Trigger it only for a named role or contact gap after the official-site check. Keep the current minimum field allowlist and bounded limits. Do not use it until LinkedIn rights, HarvestAPI vendor review, account, pinned build, budget, retention, audit and connector gates pass.", "`harvestapi/linkedin-profile-search` is business-approved for the A2 purpose but not runtime-active. Trigger it only for a named role or contact gap after the official-site check. Prefer an exact LinkedIn company URL explicitly published on the official website; otherwise use a verified company name plus target role. Keep an individual LinkedIn profile URL for authorised human review or a separately approved profile-scraper route rather than passing it to the selected profile-search Actor. Keep the current minimum field allowlist and bounded limits. Do not use the Actor until LinkedIn rights, HarvestAPI vendor review, account, pinned build, budget, retention, audit and connector gates pass.")
soul.write_text(text, encoding="utf-8")

# 10. Roadmap synchronisation.
road = ROOT / "deliverables/A2-DELIVERY-STATUS-AND-ROADMAP.md"
text = road.read_text(encoding="utf-8")
text = replace_once(text, "**Version:** `1.1.0`", "**Version:** `1.1.1`")
text = replace_once(text, "**Updated:** `2026-08-26T15:15:50Z`", f"**Updated:** `{TS}`")
text = replace_once(text, "**Current status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`", "**Current status:** `FOUNDATION CONFIGURED — NOT PILOT-READY`")
text = replace_once(text, "**Next delivery gate:** `Step 4 — Final Specialist SOUL review`", "**Next delivery gate:** `Step 5 — Operational Skills and Scripts`")
text = replace_once(text, "### Step 4 — Final Specialist SOUL — DRAFT READY / NOT ACTIVE", "### Step 4 — Final Specialist SOUL — COMPLETED / APPROVED AND ACTIVE")
text = replace_once(text, "- Active `SOUL.md` replacement requires explicit Séverine approval.", "- Active `SOUL.md` replacement was approved by Séverine and completed on `2026-08-27T11:02:47Z`.")
insert = """
### Foundation clarification — Official-Site Social Profile URL Capture — COMPLETED / APPROVED

- Séverine approved SOC-1 through SOC-8.
- Explicit professional social-profile URLs published on approved official-site pages may be retained without opening or extracting the linked social profile.
- Person and organisation URLs are separated; ambiguous attribution is held for review.
- LinkedIn, Facebook, Instagram, YouTube and other clearly professional profile links are optional enrichment fields.
- An exact LinkedIn company URL is the preferred future input for `harvestapi/linkedin-profile-search`; verified company name plus target role is the fallback.
- An individual LinkedIn profile URL is reserved for human review or a separately approved profile-scraper route.
- Broad social signals, automated social extraction, consent inference, outreach eligibility and buying-influence inference remain prohibited.
- Apify runtime remains blocked and no external action was authorised.

"""
text = replace_once(text, "### Step 5 — Operational Skills and Scripts\n", insert + "### Step 5 — Operational Skills and Scripts\n")
text = replace_once(text, "Review the proposed **Step 4 Final Specialist SOUL** and approve, request corrections or decline activation.", "Begin **Step 5A — Operational Skill Architecture and Runtime Manifest**, then build Wave 1 — Intake and Identity.")
road.write_text(text, encoding="utf-8")

print(json.dumps({
    "status": "applied",
    "new_versions": {
        "business_field_catalogue": NEW,
        "minimum_data_packages": NEW,
        "source_register": NEW,
        "evidence_policy": NEW,
        "protected_fields_policy": NEW,
        "provider_cost_policy": NEW,
        "hubspot_mapping": NEW,
    },
    "canonical_schema_changed": False,
    "minimum_package_requirements_changed": False,
    "external_actions": 0,
}, indent=2))
