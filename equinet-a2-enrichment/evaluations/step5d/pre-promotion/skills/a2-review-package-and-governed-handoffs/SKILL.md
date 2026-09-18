---
name: a2-review-package-and-governed-handoffs
description: Use when Equinet A2 prepares review views or handoffs.
---

# A2 Review Package and Governed Handoffs

## Delivery status

**Version:** `0.1.0-draft.1`  
**Status:** `WAVE 3 DRAFT — NOT APPROVED`

## Mission

Render lossless read-only review views and prepare or validate strictly gated Twenty, A1, HubSpot, A3 and A14 payloads without claiming delivery or write execution.

## Commands

```bash
python scripts/render_and_validate_a2_review_package.py <record.json> --previous-record <previous.json> --output-dir <dir>
python scripts/build_and_validate_a2_twenty_review.py prepare <record.json>
python scripts/build_and_validate_a2_twenty_review.py validate-receipt <receipt.json> <record.json>
python scripts/build_and_validate_a2_handoff.py <record.json> --destination <destination>
```

## Review package

Canonical JSON remains authoritative. Markdown, six CSV views and Excel are deterministic projections. Every package carries the canonical hash, exact outputs, row counts, file hashes and zero-action status. Formula-like content is handled safely and fidelity is validated independently.

## Twenty review boundary

Before integration, only prepare a payload with null workspace IDs. A valid receipt must match candidate, record, revision and canonical hash. Approval authorises proposed HubSpot patch preparation only; it never authorises a write or outreach.

## Governed destinations

- A1: prepare verified requalification signals without points or a replacement score.
- HubSpot: blocked until a strict proposed-patch schema and verified mapped destinations exist; write remains false.
- A3 and A14: blocked until destination-specific handoff contracts and durable receipt schemas exist.

## Boundaries

No destination is marked delivered without a durable receipt. No score is calculated by A2. No CRM write, outreach, Twenty call, n8n call or external action occurs in Step 5D.

## Handoff

Outputs remain `prepared_not_delivered` or `blocked`. Integration activation belongs to later approved steps.
