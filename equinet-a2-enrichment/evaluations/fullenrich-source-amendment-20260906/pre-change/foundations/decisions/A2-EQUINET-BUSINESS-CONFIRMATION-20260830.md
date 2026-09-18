# Equinet A2 Business Confirmation — Roles, Contacts and Horse Owner Enrichment

**Decision ID:** `A2-EQUINET-ROLES-CONTACTS-HORSEOWNER-20260830`  
**Recorded:** `2026-08-30T17:05:11Z`  
**Recorded by:** Séverine, Unitalk Operations  
**Authority:** Equinet-confirmed requirements relayed by Séverine  
**Status:** `APPROVED FOR A2 CONFIGURATION — INTEGRATIONS REMAIN DISABLED`

## Confirmed decisions

- Use the Equinet-confirmed Farrier and Horse Owner role lists in Business Field Catalogue `0.2.0`.
- Preserve the published role title and classify it separately.
- Conditional manager roles require evidence of the stated commercial, purchasing, operational or horse-care responsibility.
- Retain one selected named contact by default and at most two when a large organisation or shared responsibility is documented.
- If no suitable target-role person is found, retain organisation information, label the record `Contact Needed / Needs Review`, continue permitted research and never substitute an unrelated role.
- For Horse Owner enrichment completeness, require current role, stable/farm type, exact horse count, at least one verified breed and public business location.
- Attempt both professional email and business phone. One verified channel satisfies the minimum when the other is unavailable.
- Attempt the complete address. Verified state and country are the minimum.
- Preserve verified `Mixed` or `Other` breed values explicitly.
- For an existing matched HubSpot record, `Contact.owner_horse_count` is authoritative. For a net-new prospect, or an empty HubSpot value, A2 may use an explicit count from approved A1 evidence, authorised Equinet first-party data, recorded Equinet confirmation or the prospect-owned official website.
- Never infer horse count. Ignore `horse_count_range` and do not create new `horse_count_band` values.
- Missing enrichment data never rejects a prospect or changes the A1 score. When research is exhausted, produce the consolidated human review and allow a documented `approved_collect_during_discovery` disposition.
- HubSpot synchronisation requires the final human review, an active guarded integration and read-back reconciliation.

## Non-authorisations

This decision does not activate HubSpot, Twenty, n8n, Web, Apify, outreach or any CRM write. It is not production or contractual acceptance.

## Audit limitation

The named Equinet approver and original source-message reference were not supplied in the implementation conversation. Attach them to this record when available; do not infer them.
