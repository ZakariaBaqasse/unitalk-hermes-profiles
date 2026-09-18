# FullEnrich API v2 implementation reference

Official sources:

- `https://docs.fullenrich.com/api/v2/reference/openapi.yaml`
- `https://docs.fullenrich.com/api/v2/people/search/post`
- `https://docs.fullenrich.com/api/v2/people/lookup/post`
- `https://docs.fullenrich.com/api/v2/contact/enrich/bulk/post`
- `https://docs.fullenrich.com/api/v2/contact/enrich/bulk/get`
- `https://docs.fullenrich.com/api/v2/general/ratelimit`

## Endpoints

- `POST /people/search` — synchronous; `limit` max 100. A2 retains at most two.
- `POST /people/lookup` — synchronous; at most one Person.
- `POST /contact/enrich/bulk?silentFail=true` — asynchronous; max 100 contacts.
- `GET /contact/enrich/bulk/{enrichment_id}` — polling result.
- `GET /account/keys/verify` and `GET /account/credits` — preflight.

## Domainless Search

Use `current_company_names` and, when available, `current_company_headquarters`, plus `current_position_titles`. Domain is not required. Values in a filter category are documented as OR and categories as AND, but the short endpoint description conflicts; validate multi-title behaviour with a low-cost live test.

## Lookup

Use Person professional-network URL/ID, or Person name plus Company domain/network URL/network ID. Company name and location are not documented Lookup inputs; use People Search when those are the only organisation signals.

## Contact Enrichment

Use `linkedin_url`, or first/last name plus `domain` or `company_name`. Request exactly `contact.work_emails` and `contact.phones`. Do not send webhook fields. Polling returns `400 error.enrichment.in_progress` while unfinished. Default polling cadence is 300 seconds because product guidance recommends no more than once every 5–10 minutes, despite the endpoint message saying 30 seconds.

Success is `FINISHED`; `CANCELED` and `CREDITS_INSUFFICIENT` are terminal failures. Treat `RATE_LIMIT` and `UNKNOWN` as indeterminate failure states requiring controlled handling.

## Limits

- 60 API requests per minute across endpoints.
- 100 contacts per bulk enrichment.
- Default queue size: 100 concurrent enrichments.
- Use no more than 10 custom keys even though one schema note mentions 20.
