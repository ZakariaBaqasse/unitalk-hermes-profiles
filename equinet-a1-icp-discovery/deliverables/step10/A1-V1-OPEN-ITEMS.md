# Equinet A1 — Open Items After No-Integration V1 Freeze

## Step 11 integration inputs

### HubSpot

Required from Equinet/Unitalk:

- authorised OAuth account;
- approved read and write scopes;
- Contact, Company and Deal data model;
- duplicate-match rules;
- existing customer, opportunity, partner, distributor and competitor logic;
- consent, suppression and communication-preference properties;
- approved property mapping;
- write approval and idempotency policy.

Recommended sequence: read-only duplicate/exclusion checks first; production writes later.

### Twenty

Required:

- candidate staging schema;
- review queue fields;
- reviewer/decision model;
- evidence and source links;
- state transitions;
- reconciliation identifiers;
- sync direction with HubSpot.

### A2 Enrichment

Required:

- handoff payload and stable ID;
- approval trigger;
- primary/secondary/general contact mapping;
- enrichment scope;
- return payload and review status;
- retry and error behaviour;
- duplicate prevention.

### n8n

Required:

- manual/scheduled triggers;
- usage monitoring, warnings and Gateway prepaid-balance hard stop;
- waits and approvals;
- idempotency keys;
- retry limits;
- notifications;
- audit/cost collection;
- failure recovery.

## Governance pending

- Gemini fallback processing region confirmation;
- DPA and final retention rules;
- Equinet administrator visibility policy;
- named A1 Business Reviewer and backup;
- model/API cost conversion and daily consumption statement integration;
- contractual delivery and acceptance evidence;
- Equinet roster and role-based A1 access.

## Production blockers

The profile must not be declared fully integrated or production-ready until:

- source-system permissions are verified;
- HubSpot/Twenty mappings pass tests;
- A2 handoff is durable and authorised;
- n8n orchestration is idempotent;
- Gateway prepaid-balance enforcement and consumption visibility are verified;
- audit and incident processes are verified;
- Equinet records acceptance or the applicable production-use condition is met.

## Non-blockers for controlled manual pilot

The following are complete for manual use:

- ICP and source rules;
- evidence/confidence/scoring;
- seven workflow skills;
- model route and fallback;
- minimal tools, usage monitoring and loop circuit breaker;
- synthetic and real-prospect validation;
- review packages and exports;
- named-contact boundary;
- manual runbook;
- human-approval boundary.
