# Decision Review — Step 6 Model, Tools, Permissions and Quotas

**Status:** `APPROVED FOR SYNTHETIC LOCAL TESTING — REAL-DATA GATES PENDING`  
**Approved by:** Séverine, Unitalk Operations  
**Approved at:** `2026-08-29T21:10:52Z`  
**Profile:** `equinet-a2-enrichment`

## Confirmed configuration

- Primary: `deepseek-v4-flash` via Unitalk AI Gateway / LiteLLM / Microsoft Azure.
- Fallback: `Gemini 3.7 Flash` via Unitalk AI Gateway / LiteLLM / Google.
- Static checks: **14/14 PASS**.
- External calls/actions during configuration: **0/0**.

## Decisions

| ID | Decision |
|---|---|
| S6-1 | Route A2 through the Unitalk AI Gateway managed by LiteLLM; no customer API key. |
| S6-2 | Use deepseek-v4-flash as primary, routed by LiteLLM to Microsoft Azure. |
| S6-3 | Use Gemini 3.7 Flash as one-shot technical fallback, routed by LiteLLM to Google. |
| S6-4 | Use 4,000 maximum output tokens, 50 model iterations, one retry before fallback and medium reasoning. |
| S6-5 | Enable only clarify, code execution, file, skills, terminal and todo in the local baseline. |
| S6-6 | Keep Web, providers, Twenty, HubSpot, n8n, outreach and durable handoffs disabled. |
| S6-7 | Allow Sales Lead, Sales Operations/CRM and Prospecting roles; keep named reviewers pending. |
| S6-8 | Use the global Unitalk–Mustad USD 5,000 budget with 50/80/100 percent thresholds and no A2 allocation yet. |
| S6-9 | Use local audit artifacts now; keep retention, admin visibility and external audit sink pending. |
| S6-10 | Allow Step 6 promotion for synthetic local testing after a compliant primary response; keep upstream telemetry, fallback verification, provider regions and retention as mandatory gates before any real Mustad/Equinet data. |

## Remaining gate

A primary session response was observed and the V2.1 contract-bound business task and audit both passed. LiteLLM request telemetry remains unavailable, so the upstream route is configuration-confirmed but not independently verified. A controlled fallback-route test is also required. Provider region, retention and DPA evidence remain pending.
