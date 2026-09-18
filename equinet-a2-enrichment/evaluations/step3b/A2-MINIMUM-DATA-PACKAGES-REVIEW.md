# Decision Review — Step 3B Minimum Data Packages

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED AS UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING`  
**Decision timestamp:** `2026-08-26T17:37:05Z`  
**Profile status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`

## 1. Decisions approved as the Unitalk working baseline

| ID | Proposed decision |
|---|---|
| 3B-1 | Require five verified Farrier core fields plus one valid contact path. |
| 3B-2 | Require three verified Horse Owner organisation fields plus one valid contact path. |
| 3B-3 | Accept either a named-target contact path or a documented organisation-general fallback. |
| 3B-4 | Let one verified professional email or business phone satisfy the selected contact path. |
| 3B-5 | Treat a missing Required field as a visible gap and incomplete record, never as automatic rejection. |
| 3B-6 | Keep exact horse count, horse-count band, discipline and breeds optional for Horse Owner review readiness. |
| 3B-7 | Keep outreach readiness unavailable and separate until authoritative HubSpot checks are connected. |

## 2. Expected outcomes exercised

| Scenario | Segment | Package result | Workflow recommendation | Test |
|---|---|---|---|---:|
| `farrier_named_email_ready` | farrier | review_ready | review_required | PASS |
| `farrier_named_phone_ready` | farrier | review_ready | review_required | PASS |
| `farrier_general_fallback_ready` | farrier | review_ready | review_required | PASS |
| `horse_owner_named_ready_without_horse_count` | horse_owner | review_ready | review_required | PASS |
| `horse_owner_general_fallback_ready` | horse_owner | review_ready | review_required | PASS |
| `farrier_missing_service_area` | farrier | incomplete | enrichment_in_progress | PASS |
| `farrier_exhausted_missing_service_area` | farrier | incomplete | held | PASS |
| `farrier_missing_all_contact_channels` | farrier | incomplete | enrichment_in_progress | PASS |
| `horse_owner_optional_fields_missing` | horse_owner | review_ready | review_required | PASS |
| `horse_owner_material_conflict` | horse_owner | needs_review | held | PASS |
| `general_fallback_without_marker` | horse_owner | incomplete | enrichment_in_progress | PASS |
| `invalid_unknown_segment` | unknown_segment | invalid | processing_failed | PASS |

## 3. Approval scope

This approval authorises preparation of Step 3C in draft form. Final client confirmation remains pending. It does not authorise source access, enrichment execution, provider calls, CRM access/write, outreach, pilot or production use.
