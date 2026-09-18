# Equinet A2 Protected Fields and Conflict Policy

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING`  
**Decision timestamp:** `2026-08-26T19:39:20Z`  
**Profile:** `equinet-a2-enrichment`  
**Step:** `3E — Protected Fields and Conflict Policy`

## 1. Core boundary

A2 may observe and propose. It does not silently overwrite an existing manual value, an authoritative control, a system-managed field, an owner or an A1 snapshot. HubSpot write authority remains false.

## 2. Protection classes

| Class | Default action | Exception possible |
|---|---|---:|
| `authoritative_control` | `read_only_preserve` | No |
| `system_read_only` | `read_only_preserve` | No |
| `owner_and_routing` | `preserve_or_needs_owner_review` | Yes |
| `manual_business_value` | `preserve_and_propose_with_review` | Yes |
| `a2_enrichment_candidate` | `propose_only` | Yes |
| `review_only_personal_data` | `hold_for_privacy_review` | Yes |
| `prohibited_personal_or_sensitive` | `reject_collection` | No |

## 3. Confirmed HubSpot protected-field candidates

| Object | Internal property | Class | Reason |
|---|---|---|---|
| Contact | `do_not_contact` | `authoritative_control` | contact prohibition |
| Company | `do_not_contact` | `authoritative_control` | company prohibition |
| Contact | `gdpr_consent` | `authoritative_control` | consent |
| Company | `gdpr_consent` | `authoritative_control` | consent |
| Contact | `hs_legal_basis` | `authoritative_control` | legal basis |
| Contact | `hs_marketable_status` | `system_read_only` | marketing-contact status |
| Contact | `hs_current_customer` | `authoritative_control` | customer status |
| Company | `hs_current_customer` | `authoritative_control` | customer status |
| Contact | `lifecyclestage` | `authoritative_control` | lifecycle |
| Company | `lifecyclestage` | `authoritative_control` | lifecycle |
| Contact | `hs_lead_status` | `authoritative_control` | lead status |
| Company | `hs_lead_status` | `authoritative_control` | lead status |
| Contact | `hubspot_owner_id` | `owner_and_routing` | record owner |
| Company | `hubspot_owner_id` | `owner_and_routing` | record owner |
| Deal | `hubspot_owner_id` | `owner_and_routing` | deal owner |
| Deal | `dealstage` | `authoritative_control` | deal state |
| Contact | `hs_sequences_is_enrolled` | `system_read_only` | sequence state |
| Contact | `hs_sequences_enrolled_count` | `system_read_only` | sequence state |
| Contact | `hs_latest_sequence_enrolled` | `system_read_only` | sequence state |
| Contact | `hs_latest_sequence_enrolled_date` | `system_read_only` | sequence state |
| Contact | `hs_latest_sequence_ended_date` | `system_read_only` | sequence state |
| Contact | `hs_contact_enrichment_opt_out` | `system_read_only` | enrichment opt-out |
| Contact | `hs_contact_enrichment_opt_out_timestamp` | `system_read_only` | enrichment opt-out timestamp |
| Contact | `business_unit_optout_18640656` | `system_read_only` | Mustad USA email opt-out |
| Contact | `hs_email_optout_2431422236` | `system_read_only` | Customer Service Communication opt-out |
| Contact | `hs_email_optout_2585761664` | `system_read_only` | Marketing Information opt-out; duplicate label exists |
| Contact | `hs_email_optout_627076427` | `system_read_only` | Marketing Information opt-out; duplicate label exists |
| Contact | `hs_email_optout_627076428` | `system_read_only` | One-to-One opt-out |
| Contact | `contact_verified` | `manual_business_value` | semantics not yet aligned with A2 verification |
| Contact | `data_quality` | `manual_business_value` | semantics not yet aligned with A2 quality |
| Company | `data_quality` | `manual_business_value` | semantics not yet aligned with A2 quality |
| Company | `mailing_verified` | `manual_business_value` | verification semantics require approval |

These fields were found in the supplied HubSpot metadata. Their presence does not prove live values, permissions or write safety.

## 4. Manual value policy

- Same value: no change.
- Empty unprotected baseline plus verified proposal: propose an addition for human review.
- Different manual or protected baseline: preserve the baseline, record the conflict and hold.
- No silent overwrite or clear.

## 5. Conflict precedence

Consent, suppression, customer, lifecycle, Deal, sequence and system-read-only states remain authoritative. Authorised first-party records and existing manual CRM values take precedence over non-authoritative enrichment. Official business-site facts may support a proposal, but a material disagreement remains visible and requires review.

## 6. Future exception record

A field-level exception must record the field, current and proposed values, evidence, reason, approval-matrix version, reviewer identity and role, time, approved action, scope, expiry or single-use state, and workflow-dependency status.

## 7. Workflow-side-effect gate

The supplied inventory contains 28 enabled workflows and 32 lists. Exact trigger/action and membership effects have not been verified. Every future write remains blocked until dependencies, approval, idempotency, receipt, read-back and rollback are validated.

## 8. Decision boundary

Séverine approved decisions 3E-1 through 3E-10 as the Unitalk working baseline. Step 3F may begin in draft form. This approval does not authorise a CRM connection, write, owner reassignment, consent change, outreach, pilot or production action.
