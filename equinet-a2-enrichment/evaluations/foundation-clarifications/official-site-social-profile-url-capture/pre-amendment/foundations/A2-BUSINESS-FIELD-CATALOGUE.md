# Equinet A2 Business Field Catalogue

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING`  
**Profile:** `equinet-a2-enrichment`  
**Step:** `3A — Business Field Catalogue`  
**Canonical schema:** `1.0.0`

## 1. Purpose

This catalogue defines the proposed business field keys, scopes, value types, segment applicability, priority, collection boundary, A1 requalification linkage and preliminary CRM mapping candidates for A2 Enrichment. It is external to the stable canonical schema.

It does not activate a source, provider, connector, CRM read or write, outreach action, pilot or production use.

## 2. Decision status

Séverine approved decisions 3A-1 through 3A-8 as the Unitalk working baseline on `2026-08-26T16:49:28Z`. Equinet business confirmation remains pending. Final Step 3A promotion must record Equinet approval or corrections to the target-role, contact-selection, contactability, horse-count and field-priority decisions.

## 3. Proposed target roles

### Farrier

- Primary: Independent Farrier/Owner, Farrier Business Owner/Founder, Lead Farrier.
- Secondary: Business or Office Administrator where commercially relevant.
- Review-only: Student/Apprentice.

### Horse Owner organisation

- Primary: Owner/Founder, Farm or Stable Owner, Farm or Stable Manager, Trainer or Head Trainer, Breeding Manager.
- Secondary: General Manager, Operations Manager.

Source role wording is preserved. A Buying Role remains a recommendation requiring human approval.

## 4. Contact-selection proposal

- Retain one primary target-role contact and up to two additional role-relevant contacts.
- If no target-role person is found, retain the organisation general contact and set `target_role_not_found`.
- One verified professional email or one verified business phone satisfies proposed A2 review contactability.
- A general organisation contact may satisfy review readiness.
- Review readiness never proves consent or outreach eligibility.

## 5. Missing Required field policy

A missing Required field becomes a field-level `gap` and the record remains `incomplete`. It is visible in the review package and may remain `enrichment_in_progress`, move to `held` or receive `changes_requested`. It is never automatically rejected, never changes the A1 score by itself and never authorises an external action. Resolution is limited to approved targeted research, human correction or a documented exception.

## 6. Horse-count proposal

- Retain a verified exact count only when explicitly stated by an approved source or confirmed by Equinet.
- Never infer horse count from property size, facilities, photographs, followers or similar indirect signals.
- Derive an A2-only review band: `1`, `2_4`, `5_10`, `11_25`, `26_50`, `51_plus`.
- Keep HubSpot `horse_count_range` as a protected baseline with no write in the no-integration pilot.
- Do not create a new HubSpot property by default.

## 7. Field catalogue

| Field key | Label | Type | Farrier | Horse Owner | Collection policy |
|---|---|---|---|---|---|
| `person.full_name` | Full name | string | required | conditional_required | permitted_for_proposal |
| `person.role_title` | Current role title | string | required | conditional_required | permitted_for_proposal |
| `person.business_email` | Professional email | string | conditional_required | conditional_required | permitted_for_proposal |
| `person.personal_email_candidate` | Personal email candidate | string | optional | optional | review_only_pending_privacy_retention_and_human_decision |
| `person.business_phone` | Professional phone | string | conditional_required | conditional_required | permitted_for_proposal |
| `person.mobile_phone` | Mobile or direct dial | string | do_not_collect | do_not_collect | disabled_pending_equinet_privacy_decision |
| `person.secondary_email` | Secondary email | string | optional | optional | permitted_for_proposal |
| `person.professional_status` | Farrier professional status | enum | required | N/A | permitted_for_proposal |
| `person.professional_credential` | Primary professional credential | string | optional | N/A | permitted_for_proposal |
| `person.certifications` | Professional certifications | string_array | optional | N/A | permitted_for_proposal |
| `person.years_experience` | Years of experience | integer | optional | N/A | permitted_for_proposal |
| `person.public_profile_urls` | Public professional profile URLs | string_array | optional | optional | permitted_for_proposal |
| `person.recent_professional_activity` | Recent professional activity | structured | optional | optional | permitted_for_proposal |
| `person.social_signals` | Broad social signals | structured | do_not_collect | do_not_collect | disabled_pending_source_and_purpose_approval |
| `organisation.business_name` | Organisation or business name | string | required | required | permitted_for_proposal |
| `organisation.website` | Official website | string | optional | optional | permitted_for_proposal |
| `organisation.website_domain` | Official website domain | string | optional | optional | permitted_for_proposal |
| `organisation.business_phone` | Organisation general phone | string | conditional_required | conditional_required | permitted_for_proposal |
| `organisation.business_email` | Organisation general email | string | conditional_required | conditional_required | permitted_for_proposal |
| `organisation.public_business_location` | Public business location | structured | required | required | permitted_for_proposal |
| `organisation.service_area` | Farrier service area | string_array | required | N/A | permitted_for_proposal |
| `organisation.disciplines` | Equine disciplines | string_array | required | optional | permitted_for_proposal |
| `organisation.horse_count` | Verified exact horse count | integer | N/A | optional | permitted_for_proposal |
| `organisation.horse_count_band` | A2 horse-count review band | enum | N/A | optional | permitted_for_proposal |
| `organisation.stable_type` | Stable or farm type | enum | N/A | required | permitted_for_proposal |
| `organisation.breeds` | Horse breeds | string_array | N/A | optional | permitted_for_proposal |
| `organisation.horses_served_per_month` | Horses served per month | integer | do_not_collect | N/A | disabled_pending_equinet_use_case_and_source |
| `organisation.client_base_summary` | Aggregate client-base summary | structured | do_not_collect | N/A | disabled_pending_equinet_use_case_and_source |
| `relationship.role` | Person-to-organisation role | string | optional | optional | permitted_for_proposal |
| `relationship.target_role_priority` | Target-role priority | enum | conditional_required | conditional_required | permitted_for_proposal |
| `relationship.buying_role_recommendation` | Buying-role recommendation | enum | optional | optional | permitted_for_proposal |
| `network.mutual_connections` | Mutual connections | structured | do_not_collect | do_not_collect | disabled_pending_official_integration_and_storage_approval |

## 8. Priority summary

| Segment | Required | Conditional | Optional | Do not collect |
|---|---:|---:|---:|---:|
| Farrier | 7 | 5 | 11 | 5 |
| Horse Owner | 3 | 7 | 12 | 3 |

## 9. Deliberately disabled fields

- mobile/direct-dial collection until Equinet approves the category, source and purpose;
- broad social signals;
- mutual connections;
- horses served per month;
- client-base summaries.

Named Farrier client identities remain prohibited by default.

## 10. Mapping boundary

HubSpot properties in this catalogue are mapping candidates only. The operational A2-to-HubSpot mapping remains Step 3G. A mapping candidate does not prove that HubSpot is connected, that the property is writable or that a write is approved.

## 11. Remaining confirmations

1. Target-role model by segment.
2. Maximum named contacts and fallback.
3. Minimum review contactability.
4. Horse-count taxonomy and derivation.
5. Required, Conditional Required, Optional and Do Not Collect classifications.
6. Personal email and mobile/direct-dial policy before pilot.
7. Primary A2 reviewer and backup before pilot.

## 12. Next gate

Step 3B may begin in draft form under the approved Unitalk working baseline. Final Step 3A promotion to `0.1.0` remains pending the identified Equinet business confirmations.
