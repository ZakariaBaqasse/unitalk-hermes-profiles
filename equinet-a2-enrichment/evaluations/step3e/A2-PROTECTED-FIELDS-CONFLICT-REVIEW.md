# Decision Review — Step 3E Protected Fields and Conflict Policy

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED AS UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING`  
**Decision timestamp:** `2026-08-26T19:39:20Z`

## Decisions approved as the Unitalk working baseline

| ID | Proposed decision |
|---|---|
| 3E-1 | Treat consent, suppression, customer, lifecycle, Deal and sequence fields as authoritative controls or system-read-only. |
| 3E-2 | Preserve all populated manual CRM values; A2 may propose but never silently overwrite. |
| 3E-3 | Preserve owner fields and route unresolved assignments to `needs_owner_review`. |
| 3E-4 | Treat `contact_verified`, `data_quality` and `mailing_verified` as protected mapping candidates until semantics are approved. |
| 3E-5 | Apply the documented conflict-precedence order while preserving every conflict in the audit trail. |
| 3E-6 | Require a complete field-level exception record for any future protected-field change. |
| 3E-7 | Block every write while workflow or list dependencies remain unverified. |
| 3E-8 | Require future approved writes to be idempotent, receipted, read back and reconcilable. |
| 3E-9 | Keep the A1 snapshot immutable and route score-related evidence through requalification. |
| 3E-10 | Keep current HubSpot write authority false. |

## Deterministic outcomes

| Case | Action | Baseline preserved | Test |
|---|---|---:|---:|
| `same_manual_value` | `no_change` | Yes | PASS |
| `empty_unprotected_add` | `propose_add` | No | PASS |
| `different_manual_value` | `preserve_and_hold` | Yes | PASS |
| `consent_conflict` | `preserve_authoritative_and_block` | Yes | PASS |
| `read_only_sequence` | `read_only_preserve` | Yes | PASS |
| `owner_without_approval` | `preserve_or_needs_owner_review` | Yes | PASS |
| `low_confidence_proposal` | `reject_proposal` | Yes | PASS |
| `approved_but_workflow_unknown` | `approved_proposal_write_blocked` | Yes | PASS |
| `prohibited_personal_data` | `reject_collection` | Yes | PASS |
| `personal_email_candidate` | `hold_for_privacy_review` | Yes | PASS |
| `score_related_evidence` | `create_requalification_signal` | Yes | PASS |

## Approval scope

This approval establishes the Unitalk working baseline and authorises Step 3F draft preparation. Equinet action-level approvers, protected-field exceptions and workflow dependencies remain pending.
