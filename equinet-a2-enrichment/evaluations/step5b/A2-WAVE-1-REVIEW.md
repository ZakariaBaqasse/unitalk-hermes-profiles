# Decision Review — Step 5B Wave 1 Intake and Identity

**Status:** `APPROVED AND PROMOTED`  
**Approved by:** Séverine, Unitalk Operations  
**Approved at:** `2026-08-27T12:34:34Z`  
**Profile:** `equinet-a2-enrichment`  
**Wave:** `1 — Intake and Identity`

## Delivered skill packages

1. `a2-handoff-intake-and-initialisation`;
2. `a2-entity-resolution-and-normalisation`;
3. `a2-duplicate-and-eligibility-review`.

## Decisions proposed

| ID | Decision |
|---|---|
| W1-1 | Require the complete approved A1-to-A2 handoff gate before creating an A2 record. |
| W1-2 | Preserve the complete A1 snapshot and create the first A2 revision deterministically and idempotently. |
| W1-3 | Keep entity normalisation separate from external record merging or CRM mutation. |
| W1-4 | Treat a matching domain as one identity signal, never as a unique key by itself. |
| W1-5 | Require a matching name plus a strong identifier, or multiple strong identifiers, for a deterministic confirmed match. |
| W1-6 | Route one weak match to `possible_match` and mixed matching/conflicting signals to `conflict`. |
| W1-7 | Block confirmed duplicates and invalid identities; hold unresolved material identity conflicts. |
| W1-8 | Hold possible duplicates, unresolved identities and failed required duplicate checks. |
| W1-9 | Permit synthetic or manual no-integration progression when HubSpot checks are unavailable, while keeping outreach eligibility unavailable. |
| W1-10 | Keep all Wave 1 commands local, read-only with respect to source systems, and at zero external actions. |

## Technical result

- Skill packages: **3/3 present**.
- Deterministic cases: **14/14 PASS**.
- Targeted behavioural scenarios: **3/3 PASS**.
- External calls: **0**.
- External actions: **0**.
- HubSpot and Apify access: **not used**.

## Approval effect

Approval promotes the three Wave 1 skills and authorises Step 5C Wave 2 construction. It does not activate Web, Apify, Twenty, HubSpot, n8n, outreach, CRM writes, pilot or production status.
