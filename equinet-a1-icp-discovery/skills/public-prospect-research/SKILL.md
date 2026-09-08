---
name: public-prospect-research
version: 3.0.0
status: deprecated_compatibility_shim
description: Redirect legacy discovery requests to n8n and Twenty staging.
compatibility: Requires equinet-n8n-discovery-control and evidence-aware-crm-staging.
---

# Public Prospect Research — compatibility shim

Do not perform discovery, directory extraction, source planning, normalisation or deduplication in Hermes.

For a new lead request:

1. Load `equinet-n8n-discovery-control`.
2. Start the exposed n8n discovery orchestrator through MCP.
3. Create its finite durable cron monitor.
4. Retrieve the compact result once.
5. Stage each named returned lead as a Twenty Company through `evidence-aware-crm-staging`.

n8n remains authoritative for sources, acquisition, normalisation, deduplication and its read-only HubSpot domain check. A website, evidence package or ICP score is not required before Twenty staging. Do not initiate outreach or write to HubSpot.
