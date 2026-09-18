# Equinet A2 No-Integration Configuration Package

**Release:** `equinet-a2-no-integration-1.0.0`  
**Status:** `PILOT_READY_NO_INTEGRATION`  
**Profile:** `equinet-a2-enrichment`

## Mission and scope

Prepare evidence-backed, human-reviewable enrichment records from an approved A1 handoff. Preserve the A1 snapshot and score, use authorised evidence only, expose gaps and conflicts, and never infer consent or purchasing authority.

## Runtime

| Control | Release-candidate value |
|---|---|
| Primary model | `deepseek-v4-flash` |
| Gateway | Unitalk LiteLLM |
| Upstream | Microsoft Azure, Europe |
| Fallback | Disabled |
| Default Web | Disabled |
| Candidate concurrency | 1 |
| Max model iterations | 50 circuit breaker |
| API retries | 1 |
| Token warning | 300,000 per candidate |
| Token escalation | 600,000 per candidate |
| Local token hard stop | None |
| Economic hard stop | Unitalk–Mustad prepaid balance; negative balance prohibited |

Credential values remain only in the isolated profile `.env` with mode `0600`; they are excluded from manifests and delivery packages.

## Skills

| Skill | Version | Release status |
|---|---|---|
| `a2-handoff-intake-and-initialisation` | `0.1.0` | `pilot_ready_no_integration` |
| `a2-entity-resolution-and-normalisation` | `0.1.0` | `pilot_ready_no_integration` |
| `a2-duplicate-and-eligibility-review` | `0.1.0` | `pilot_ready_no_integration` |
| `a2-gap-analysis-and-enrichment-planning` | `0.1.1` | `pilot_ready_no_integration` |
| `a2-permitted-enrichment-research` | `0.1.0` | `pilot_ready_no_integration` |
| `a2-field-verification` | `0.1.0` | `pilot_ready_no_integration` |
| `a2-evidence-confidence-and-freshness` | `0.1.0` | `pilot_ready_no_integration` |
| `a2-protected-field-conflict-resolution` | `0.1.0` | `pilot_ready_no_integration` |
| `a2-data-quality-and-review-readiness` | `0.1.1` | `pilot_ready_no_integration` |
| `a2-review-package-and-governed-handoffs` | `0.1.1` | `pilot_ready_no_integration` |

## Operating rules

- One consolidated final human review after all permitted processing.
- `selected_named_contact` is separate from `relationship.target_role_priority`.
- An A1 High score may coexist with an A2 `held` state.
- Missing required evidence creates a visible gap, never an invented value or automatic ICP downgrade.
- Official-site Web access is disabled by default and requires candidate-specific activation.
- HubSpot, Twenty, n8n, Apify, outreach and durable downstream delivery remain disabled.

## Validation baseline

- Step 9A correction propagation: **15/15 PASS**.
- Step 9B offline regression: **10/10 PASS**.
- Offline suites/workflows: **11/11 PASS**.
- Operator compilation: **14/14 PASS**.
- Exact accepted-record replay: **2/2 PASS**.
- External actions: **0**.

## Status boundary

This package is approved as `PILOT_READY_NO_INTEGRATION`. It is not integrated, production acceptance or contractual acceptance. All listed source, CRM, workflow, outreach and delivery limitations remain active.
