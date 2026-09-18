# Equinet A2 Preliminary HubSpot Mapping

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED UNITALK WORKING BASELINE — LIVE READ VERIFICATION PENDING`  
**Decision timestamp:** `2026-08-27T09:09:39Z`  
**Step:** `3G — Preliminary A2-to-HubSpot Mapping`

## Boundary

This mapping is based on supplied metadata only. HubSpot is not connected. It proves candidate property names and metadata types, not live values, associations, permissions, workflow safety or write readiness. Every write remains blocked.

## Mapping table

| Canonical field | Status | HubSpot candidate(s) | Conversion |
|---|---|---|---|
| `person.full_name` | `proposed_unverified` | Contact.firstname, Contact.lastname | `split_first_last_requires_human_review` |
| `person.role_title` | `proposed_unverified` | Contact.jobtitle | `direct_string` |
| `person.business_email` | `proposed_unverified` | Contact.work_email, Contact.email | `direct_string` |
| `person.personal_email_candidate` | `review_only_no_hubspot_mapping` | None | `direct_string` |
| `person.business_phone` | `proposed_unverified` | Contact.phone | `direct_string` |
| `person.mobile_phone` | `prohibited` | Contact.mobilephone | `direct_string` |
| `person.secondary_email` | `proposed_unverified` | Contact.secondary_email | `direct_string` |
| `person.professional_status` | `proposed_unverified` | Contact.farrier_active_flag | `explicit_enum_mapping_required` |
| `person.professional_credential` | `canonical_only_compatibility_field` | None | `direct_string` |
| `person.certifications` | `proposed_unverified` | Contact.farrier_certifications | `enum_or_multivalue_conversion_pending` |
| `person.years_experience` | `proposed_unverified` | Contact.years_experience | `direct_string` |
| `person.public_profile_urls` | `canonical_only_no_hubspot_mapping` | None | `enum_or_multivalue_conversion_pending` |
| `person.recent_professional_activity` | `canonical_only_no_hubspot_mapping` | None | `multi_property_mapping_required` |
| `person.social_signals` | `prohibited` | None | `multi_property_mapping_required` |
| `organisation.business_name` | `proposed_unverified` | Company.name, Company.trade_name | `direct_string` |
| `organisation.website` | `proposed_unverified` | Company.website | `direct_string` |
| `organisation.website_domain` | `proposed_unverified` | Company.domain | `direct_string` |
| `organisation.business_phone` | `proposed_unverified` | Company.phone | `direct_string` |
| `organisation.business_email` | `proposed_unverified` | Company.company_email | `direct_string` |
| `organisation.public_business_location` | `proposed_unverified` | Company.address, Company.city, Company.state, Company.zip, Company.country | `multi_property_mapping_required` |
| `organisation.service_area` | `canonical_only_no_hubspot_mapping` | None | `enum_or_multivalue_conversion_pending` |
| `organisation.disciplines` | `proposed_segment_specific` | Contact.disciplines_worked_with, Contact.owner_primary_discipline | `enum_or_multivalue_conversion_pending` |
| `organisation.horse_count` | `proposed_unverified` | Contact.owner_horse_count | `direct_string` |
| `organisation.horse_count_band` | `mapping_blocked_taxonomy_conflict` | Contact.horse_count_range | `explicit_enum_mapping_required` |
| `organisation.stable_type` | `mapping_blocked_enum_mismatch` | Contact.stable_type | `explicit_enum_mapping_required` |
| `organisation.breeds` | `proposed_unverified` | Contact.owner_breeds | `enum_or_multivalue_conversion_pending` |
| `organisation.horses_served_per_month` | `prohibited` | Contact.farrier_horses_served | `direct_string` |
| `organisation.client_base_summary` | `prohibited` | None | `multi_property_mapping_required` |
| `relationship.role` | `canonical_only_no_hubspot_mapping` | None | `direct_string` |
| `relationship.target_role_priority` | `canonical_only_no_hubspot_mapping` | None | `explicit_enum_mapping_required` |
| `relationship.buying_role_recommendation` | `proposed_unverified` | Contact.hs_buying_role | `explicit_enum_mapping_required` |
| `network.mutual_connections` | `prohibited` | None | `multi_property_mapping_required` |

## Known blocks

- `horse_count_range` has overlapping options and cannot receive deterministic A2 bands.
- `stable_type` lacks the complete proposed A2 taxonomy.
- Full-name splitting requires human review.
- Farrier credential/certification representation needs one approved model.
- Personal-email candidates remain canonical review-only with no HubSpot mapping.
- Workflow and list dependencies remain unverified.

## Object routing

Person fields target Contact. Organisation fields prefer Company, but several existing Horse Owner/Farrier fields exist only on Contact and are marked for scope review. Relationship mappings and exact associations remain pending live read-only verification.

## Current result

Mapping status counts: `{"canonical_only_compatibility_field": 1, "canonical_only_no_hubspot_mapping": 5, "mapping_blocked_enum_mismatch": 1, "mapping_blocked_taxonomy_conflict": 1, "prohibited": 5, "proposed_segment_specific": 1, "proposed_unverified": 17, "review_only_no_hubspot_mapping": 1}`. Global write authority is false.
