# Equinet A2 FullEnrich Source-Routing Decision

**Decision ID:** `A2-FULLENRICH-SOURCE-ROUTING-20260906`  
**Recorded at:** `2026-09-06T13:07:00Z`  
**Recorded by:** Séverine, Unitalk Operations  
**Status:** `BUSINESS RULES CONFIRMED — INTEGRATION PENDING`

## Confirmed decisions

- Equinet has no separate first-party enrichment dataset. HubSpot remains the authoritative CRM when connected.
- New external enrichment follows: prospect official website, FullEnrich, then separately gated Apify/HarvestAPI only when needed.
- FullEnrich `/people/search` is used only when no suitable named contact remains after the official-site check.
- Search requires the exact organisation domain and an approved target role. The default result limit is one.
- A later role-specific search is allowed when no suitable person is returned. Across the search sequence, no more than two unique people may be returned and retained per prospect.
- One named contact is retained by default. A second requires a large organisation or shared purchasing or operational responsibility.
- FullEnrich `/people/lookup` is used only when a contact name exists but identity, organisation or current role still needs verification. It is skipped when those elements are already verified.
- FullEnrich `/contact/enrich/bulk` is called only for selected contacts and requests `contact.work_emails` and `contact.phones`.
- Mobile phone is approved and actively sought. Its absence does not by itself block review.
- Personal email is not requested, retained, written to CRM or used for outreach.
- n8n is the approved target orchestration layer. It is not currently connected or runtime-active.
- Apify fallback is never automatic and requires a separate preflight.

## Approval boundary

This decision approves the A2 business configuration and implementation work. It does not authorise live FullEnrich, n8n, Apify, CRM-write or outreach execution.

## Supersession

This decision supersedes only the prior decision's Equinet first-party enrichment-source availability, provider contact-channel rules, mobile-phone collection and personal-email provider-collection scopes. The approved role taxonomy, contact-count rule, Horse Owner business requirements and other unaffected decisions remain active.
