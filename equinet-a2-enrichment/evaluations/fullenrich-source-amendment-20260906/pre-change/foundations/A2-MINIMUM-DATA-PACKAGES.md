# Equinet A2 Minimum Data Packages

**Version:** `0.2.0`  
**Status:** `EQUINET-CONFIRMED BUSINESS CONFIGURATION — NO INTEGRATION ACTIVATION`

## Shared rules

- Only a `verified` field satisfies a required field.
- Missing required data creates a visible `gap` and keeps data quality `incomplete`.
- Missing information never rejects the prospect or changes the A1 score.
- Research that can continue uses `enrichment_in_progress`.
- When reasonable research is exhausted, produce the consolidated human review rather than silently stopping.
- Use `held` only for a named dependency that truly prevents progression.
- The reviewer may record `approved_collect_during_discovery`; gaps remain visible and no outreach or CRM write is authorised.
- Human review remains mandatory.

## Farrier package

Required core fields:

- `person.professional_status`
- `organisation.business_name`
- `organisation.public_business_location`
- `organisation.service_area`
- `organisation.disciplines`

Named-contact path:

- `person.full_name`
- `person.role_title`
- `relationship.target_role_priority`
- attempt both `person.business_email` and `person.business_phone`; at least one verified channel satisfies the minimum when the other is unavailable.

If no suitable role is found, preserve organisation information, set `target_role_not_found`, show `Contact Needed / Needs Review` and carry the case to final human review. A general organisation contact does not satisfy the target-contact requirement.

## Horse Owner package

Required core fields:

- `organisation.business_name`
- `organisation.public_business_location`
- `organisation.stable_type`
- `organisation.horse_count`
- `organisation.breeds`

Named-contact path:

- `person.full_name`
- `person.role_title`
- `relationship.target_role_priority`
- attempt both `person.business_email` and `person.business_phone`; at least one verified channel satisfies the minimum when the other is unavailable.

Location rule:

- attempt the complete public business address;
- `state_region` and `country_code` are the minimum verified components.

Breed rule:

- at least one verified value is required;
- preserve verified `Mixed` or `Other` values explicitly.

Horse-count rule:

- use existing matched HubSpot `Contact.owner_horse_count` as authoritative;
- otherwise accept an exact value only from explicit approved evidence for a net-new prospect or empty HubSpot value;
- never infer;
- ignore `horse_count_range` and do not derive `horse_count_band`.

## Outreach boundary

A2 review, including approval with open gaps, does not establish consent or outreach eligibility. HubSpot consent, suppression, customer, Deal, sequence, owner and business-unit checks remain separate authoritative gates.
