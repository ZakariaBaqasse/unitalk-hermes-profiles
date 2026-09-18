# Equinet A2 Minimum Data Packages

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING`  
**Decision timestamp:** `2026-08-26T17:37:05Z`  
**Profile:** `equinet-a2-enrichment`  
**Step:** `3B — Minimum Data Packages`  
**Business Field Catalogue:** `0.1.0-draft.1` Unitalk working baseline

## 1. Purpose

This contract defines the minimum information combinations for an A2 record to become ready for human review. It does not define outreach eligibility and does not authorise any external action.

## 2. Shared rules

- Every field that satisfies a minimum requirement must be `verified`.
- A missing Required field becomes `gap`; the record remains `incomplete`.
- Missing information never automatically rejects the prospect or changes the A1 score.
- Optional fields never block review readiness.
- A material conflict produces `conflict` and a `held` recommendation.
- If research is not exhausted, an incomplete record remains `enrichment_in_progress`.
- If research is exhausted and a required gap remains, the record moves to `held` for human resolution.
- Human review remains mandatory during the pilot.

## 3. Farrier review-ready package

### Core verified fields

1. `person.professional_status`
2. `organisation.business_name`
3. `organisation.public_business_location`
4. `organisation.service_area`
5. `organisation.disciplines`

### Contact path A — named target

- `person.full_name`;
- `person.role_title`;
- `relationship.target_role_priority`;
- at least one of `person.business_email` or `person.business_phone`.

### Contact path B — organisation fallback

- `target_role_not_found = true`;
- at least one of `organisation.business_email` or `organisation.business_phone`.

The missing named-person fields are documented as non-applicable under the approved fallback rather than invented.

## 4. Horse Owner review-ready package

### Core verified fields

1. `organisation.business_name`
2. `organisation.public_business_location`
3. `organisation.stable_type`

The same named-target and organisation-fallback contact paths apply. Exact horse count, horse-count band, discipline and breeds remain optional for A2 review readiness. Their absence does not block review.

## 5. Outreach boundary

A2 review readiness is not outreach readiness. Outreach status remains `unavailable` until HubSpot can authoritatively check consent, suppression, customer, Deal, sequence, owner and business-unit access. Public contact data alone never permits sending.

## 6. Decision status

Séverine approved decisions 3B-1 through 3B-7 as the Unitalk working baseline. Step 3C may begin in draft form. Equinet confirmation remains pending and no live action is enabled.
