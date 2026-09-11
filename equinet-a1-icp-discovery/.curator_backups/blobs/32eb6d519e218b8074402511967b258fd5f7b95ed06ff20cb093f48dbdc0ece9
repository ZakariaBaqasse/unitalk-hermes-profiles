---
name: a1-staged-live-run
version: 3.0.0
status: deprecated_compatibility_shim
description: Redirect legacy A1 runs to retrieval and Twenty staging.
compatibility: Requires equinet-n8n-discovery-control and evidence-aware-crm-staging.
---

# A1 Staged Live Run — compatibility shim

The legacy enrichment-first stage gate is retired for new retrieval requests.

Use:

```text
equinet-n8n-discovery-control
→ n8n discovery and compact result retrieval
→ evidence-aware-crm-staging
→ one Twenty Company per named lead
→ human review in Twenty
```

A website, evidence package, ICP score or review package is not required before Company staging. Leads without a usable Company name are recorded as `blocked_missing_company_name`; never invent a name. Enrichment, scoring, exports and A2 are optional later workflows. HubSpot remains read-only and outreach is prohibited.
