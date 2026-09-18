# Equinet A2 Twenty Review Layer Contract and Mapping

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED UNITALK WORKING BASELINE — TWENTY WORKSPACE VERIFICATION PENDING`  
**Decision timestamp:** `2026-08-27T10:19:34Z`  
**Step:** `3H — Twenty Review Layer Contract and Mapping`

## Operating model

A1 keeps the main prospect record in Twenty. A2 creates a linked, versioned enrichment-review record and field-level decisions or an equivalent workspace-supported structure. Canonical A2 JSON remains the only lossless source of truth. Twenty is the staging and human-review layer; HubSpot remains the final CRM system of record.

## Review states

`pending → in_review → approved | needs_changes | held | rejected`

`needs_changes → pending` after A2 creates a new canonical revision. `held → in_review` after the named dependency is resolved. Approved and rejected decisions are terminal for that review revision.

## Review capabilities

The reviewer may approve, reject, hold or request changes per field, provide corrected values and comments, then take a record-level decision. Final decisions require reviewer identity, role, timestamp, reason and an idempotent review receipt.

## Approval effect

Twenty approval authorises preparation of a proposed HubSpot patch only. It never authorises HubSpot write or outreach. Corrections create a new A2 revision and retain the prior revision.

## Proposed Twenty model

- Existing A1 prospect record: retained.
- Linked `A2 Enrichment Review` logical object: proposed.
- Linked `A2 Field Decision` logical object or safe structured equivalent: proposed.
- Exact object names, fields and relations: pending workspace metadata.

## API and workflow boundary

Twenty provides workspace-generated REST/GraphQL APIs and webhooks, but the Equinet workspace schema, API key, role scopes and event configuration are not connected. n8n must filter, deduplicate and reconcile events. No integration is activated by this contract.
