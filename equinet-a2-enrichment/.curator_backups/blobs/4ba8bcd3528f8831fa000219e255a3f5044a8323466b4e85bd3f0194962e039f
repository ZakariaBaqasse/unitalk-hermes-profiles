---
name: a2-fullenrich-connector
description: "Use when A2 calls FullEnrich Lookup, Search, or Enrich."
version: 0.1.0
author: Unitalk
license: Proprietary
metadata:
  hermes:
    tags: [equinet, a2, fullenrich]
    related_skills: [a2-twenty-fullenrich-workflow, a2-contact-resolution-and-selection]
---

# A2 FullEnrich Connector

## When to Use

Use for approved People Lookup, People Search and selected-contact enrichment.

## Status

`IMPLEMENTED — ACCOUNT AND CREDIT CAPS VERIFIED; LIVE ENRICHMENT ACCEPTANCE PENDING`

## Commands

```bash
python scripts/fullenrich_people_lookup.py <requests.json> --output <results.json>
python scripts/fullenrich_people_search.py <requests.json> --output <results.json>
python scripts/fullenrich_contact_enrichment.py <selected.json> --output <results.json>
```

Search and Lookup are synchronous. Contact Enrichment submits `/contact/enrich/bulk` and polls `GET /contact/enrich/bulk/{enrichment_id}`. Search is staged and always role-bounded: approved primary titles excluding generic `Owner`, exact `Owner`, then paid secondary titles only when neither higher-priority Search nor zero-call linked-secondary reuse produced a selection. The internal `linked_secondary` stage performs no provider Search call. A later stage runs only when the validated prior stage retained nobody. At most two People are retained across the sequence. Domainless Search uses exact Company name plus available headquarters filters. Lookup requires a professional-network identifier or name plus Company domain/network identifier. Request exactly work email and phone; never request personal email.

Credit limits are 50 per run, 100 per UTC day and 250 for the controlled pilot. Every paid request must reserve its maximum estimated credits in the atomic ledger before execution and settle against provider-reported actual credits afterward. Existing reservations block duplicate paid calls. Use `python scripts/fullenrich_credit_status.py` to inspect consumption. No spend approver or consumption owner is required under decision `A2-FULLENRICH-CREDIT-CAPS-20260915`.