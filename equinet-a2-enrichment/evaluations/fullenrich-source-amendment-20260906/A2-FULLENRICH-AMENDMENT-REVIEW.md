# A2 FullEnrich Source-Routing Amendment Review

**Profile:** `equinet-a2-enrichment`  
**Decision:** `A2-FULLENRICH-SOURCE-ROUTING-20260906`  
**Status:** `APPROVED BUSINESS CONFIGURATION — RUNTIME INTEGRATION PENDING`  
**Approved by:** Séverine, Unitalk Operations  
**Approved at:** `2026-09-06T13:07:00Z`

## Implemented business rules

1. Equinet has no separate first-party enrichment dataset.
2. New external enrichment follows prospect official website, FullEnrich and then separately gated Apify/HarvestAPI fallback.
3. FullEnrich People Search requires the exact organisation domain and approved target roles.
4. People Search returns one result by default. A later role-specific search is allowed when no suitable person is returned.
5. No more than two unique people may be returned and retained per prospect. A second retained contact requires a large organisation or shared purchasing or operational responsibility.
6. People Lookup is limited to one known person whose identity, organisation or current role remains uncertain.
7. Contact Enrichment runs only for selected contacts and requests work email and mobile phone.
8. Personal email is not requested and is discarded if unexpectedly returned.
9. FullEnrich mobile is stored as `person.mobile_phone`; it is not relabelled as `person.business_phone`.
10. Mobile is actively sought, can satisfy the verified contact-channel alternative, and does not by itself block review when absent.
11. n8n is the approved target orchestrator but is not connected.
12. Apify fallback is not automatic and requires a separate source preflight.

## Verification completed

- FullEnrich amendment deterministic validation: **44/44 passed**.
- Existing no-integration Farrier workflow: **14/14 operators passed**.
- Existing no-integration Horse Owner workflow: **14/14 operators passed**.
- Language audit: **1,472 files checked, zero findings**.
- Final manifest, dependency and release-integrity verification: **17/17 passed**.
- External provider calls: **0**.
- External business actions: **0**.

## Runtime limitations

- No FullEnrich API key is installed.
- No n8n workflow is deployed or connected.
- FullEnrich Premium-plan rates and credit balance are not verified.
- FullEnrich vendor, DPA/subprocessor, data-route, retention and deletion review remains pending.
- FullEnrich, Apify, Twenty and HubSpot integrations remain disabled.
- No CRM write, outreach or production action is authorised.

## Next gate

Receive and store the FullEnrich API key in n8n, verify the account and Premium-plan rates, deploy the bounded workflow, verify signed webhooks and run a bounded connector acceptance test.
