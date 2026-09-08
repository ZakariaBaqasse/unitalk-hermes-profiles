# A1 source volume and priority policy change

- **Effective:** 2026-09-02T17:47:44Z
- **Requested by:** authorised user in the current Equinet A1 session
- **Source register:** `equinet-a1-approved-source-register` version `1.5.0`
- **Runtime policy:** `equinet-a1-runtime-policy` version `3.2.0`
- **Implementation status:** policy updated; workflow implementation and live end-to-end validation pending

## Approved changes

1. Remove the fixed 20-candidate per-source per-run cap.
2. Remove the fixed 50-candidate per-source daily cap.
3. Allow each source to supply up to the remaining discovery target, bounded by the total request ceiling.
4. Use this Farrier source order:
   1. Mad Barn
   2. Google Maps via Apify
   3. FarrierIQ
   4. NewHorse
   5. Best of Lexington
   6. HorseProFinder
5. Keep the current Horse Owner order as Google Maps followed by HorseProFinder because the Mad Barn adapter remains Farrier-only.

## Controls retained

- Maximum 200 requested candidates per discovery run.
- One active discovery run and concurrency one per source.
- Source terms, robots, access-control, CAPTCHA, login, 403, 429, rate-limit and sensitive-data stop conditions.
- Google Maps must use the approved Apify Actor and authorised Unitalk account.
- No outreach, no HubSpot writes, and mandatory human review.

## Required implementation work

The n8n orchestrator and source adapters still require the separately documented node changes. This policy update does not itself change or deploy workflow JSON.
