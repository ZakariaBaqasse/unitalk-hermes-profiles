# A2 FullEnrich n8n Integration Specification

**Version:** `0.1.0`  
**Status:** `DESIGN APPROVED — N8N AND FULLENRICH NOT CONNECTED`  
**Decision:** `A2-FULLENRICH-SOURCE-ROUTING-20260906`

## Architecture

```text
A2 validated source request
→ narrow n8n start tool
→ FullEnrich API v2
→ synchronous Search/Lookup result or asynchronous Enrich job
→ signed FullEnrich webhook for Enrich
→ n8n verification and field minimisation
→ narrow n8n status/result tool
→ A2 evidence and human-review workflow
```

## Start tool

`start_a2_fullenrich_action` accepts one candidate-scoped operation: `people_search`, `people_lookup` or `contact_enrich`. It validates the active source policy, role/domain or selected-contact inputs, contact/result limits, idempotency key, credit balance and audit correlation ID before any provider call.

## Status/result tool

`get_a2_fullenrich_result` accepts only the Unitalk job ID. It returns `running`, `succeeded`, `not_found`, `insufficient_match`, `failed`, `blocked`, `cancelled` or `timed_out`, plus a field-minimised result and usage record.

## People Search

- Require the exact approved organisation domain and approved A2 target-role titles.
- Default `limit` is one.
- A later role-specific search is permitted only when no suitable person was returned.
- Stop at two unique returned/retained people per prospect.
- A second retained contact requires the approved reason.
- Search results contain profile data only; never treat them as email or phone results.

## People Lookup

- Use only for a known name when identity, organisation or current role needs verification.
- Prefer person professional-network URL; otherwise use full name plus exact company identifier.
- Skip Lookup when name, role and organisation are already verified.

## Contact Enrichment

- Run only for selected contacts.
- Send exactly `contact.work_emails` and `contact.phones`.
- Never request `contact.personal_emails`.
- Store returned phones as `person.mobile_phone`, not `person.business_phone`.
- Persist the `enrichment_id` and correlation fields as strings.

## Webhook and secret controls

- Store the FullEnrich API key only in the n8n credential store.
- Verify `X-Signature-SHA1` against the raw request body with constant-time comparison before parsing.
- Reject missing or invalid signatures.
- Never print or return credentials.

## Retries and fallback

- Retry one approved transient technical failure at most once.
- Do not retry `not_found`, invalid input, privacy/policy blocks or insufficient credits.
- Do not invoke Apify automatically. Return a terminal receipt so A2 can run a separate Apify preflight when the approved FullEnrich fallback condition is met.

## Activation boundary

No live workflow is deployed by this specification. Activation requires n8n access, the API key, account and balance verification, Premium-plan rate confirmation, provider governance approval, caps, signed-webhook testing and a bounded acceptance run.
