# Equinet A2 Evidence, Verification, Confidence and Freshness Policy

**Version:** `0.1.1-draft.1`  
**Status:** `APPROVED UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING`  
**Decision timestamp:** `2026-08-26T18:53:52Z`  
**Profile:** `equinet-a2-enrichment`  
**Step:** `3D — Evidence, Verification, Confidence and Freshness Policies`

## 1. Purpose

This policy assesses the reliability of a field-level A2 claim. It does not measure commercial attractiveness and never replaces the A1 ICP score.

## 2. Confidence calculation

| Dimension | Maximum |
|---|---:|
| Identity match | 20 |
| Source authority | 20 |
| Claim directness | 20 |
| Freshness | 20 |
| Corroboration | 10 |
| Consistency | 10 |
| **Total** | **100** |

Bands: High `80–100`, Medium `60–79`, Low `0–59`.

## 3. Caps

- unresolved identity: maximum `39`;
- material conflict: maximum `39`;
- Required claim supported only by inference: maximum `59`;
- stale time-sensitive claim: maximum `59`;
- source rights/runtime gate not passed: `0` and unusable as evidence.

## 4. Verification states

- `verified`: High confidence, exact identity, direct fact, permitted source, acceptable freshness and no material conflict;
- `partially_verified`: Medium confidence or a documented limitation;
- `unverified`: Low confidence or insufficient evidence;
- `contradicted`: material conflict;
- `not_applicable`: field not applicable under the package/fallback;
- `error`: technical validation failure.

## 5. Source treatment

- A1 evidence preserves its inherited provenance and confidence.
- HubSpot is authoritative only after the read-only connection and permissions pass.
- A current official website can confirm explicit facts controlled by the business without a visible publication date.
- An explicit outbound professional social-profile link on the official site verifies the existence of that published URL only; it does not verify the linked profile's contents, consent, outreach eligibility or buying influence.
- LinkedIn profile data through Apify remains unusable until every rights, vendor and runtime gate passes.
- Apify email search remains separate from LinkedIn provenance and requires exact identity/company match plus provider verification.
- Search snippets remain discovery-only.

## 6. Proposed freshness windows

| Field | Maximum age |
|---|---:|
| `person.role_title` | 180 days |
| `person.business_email` | 180 days |
| `person.personal_email_candidate` | 180 days |
| `person.business_phone` | 180 days |
| `organisation.business_email` | 180 days |
| `organisation.business_phone` | 180 days |
| `person.professional_status` | 365 days |
| `person.certifications` | 365 days |
| `person.professional_credential` | 365 days |
| `organisation.public_business_location` | 365 days |
| `organisation.service_area` | 365 days |
| `organisation.horse_count` | 365 days |
| `organisation.stable_type` | 730 days |
| `organisation.disciplines` | 730 days |
| `organisation.breeds` | 730 days |
| `person.recent_professional_activity` | 365 days |
| `person.public_profile_urls` | 365 days |
| `organisation.public_profile_urls` | 365 days |

A current official website statement about a fact controlled by the business is treated as current even when no publication date is displayed, unless a stale or conflicting signal exists.

## 7. Conflict handling

An authoritative source takes precedence operationally, but every material conflict remains visible. A current-role disagreement between an official website and LinkedIn produces a hold. Resolution requires a reviewer and reason; prior evidence is preserved.

## 8. Email rules

- Officially published professional email may be verified from one exact official source.
- Future Apify email results require exact identity/company match and provider verification.
- Personal email is discarded by default pending Equinet approval.
- Deliverability does not create outreach consent.
- Provider email must never be labelled as LinkedIn-sourced.

## 9. Decision boundary

Séverine approved decisions 3D-1 through 3D-10 as the Unitalk working baseline and authorised the protected SOUL synchronisation. Equinet confirmation of freshness windows, relevant activity types and personal-email policy remains pending. No source activation, provider call, CRM write or outreach is authorised.
