# Equinet A1 — Step 7 Runtime Configuration Review

**Profile:** `equinet-a1-icp-discovery`  
**Review completed at:** `2026-08-15T16:51:21Z`  
**Scope:** model, fallback, tools, permissions, quotas, usage controls and deterministic execution  
**Status:** `Approved by Séverine for the controlled A1 V1 pilot`  
**Approval recorded at:** `2026-08-15T17:30:08Z`

## Model routing

| Role | Logical model | Profile provider | Gateway | Upstream | Region | Training with Mustad Data |
|---|---|---|---|---|---|---|
| Primary | `deepseek-v4-flash` | `openai-api` | `litellm-unitalk` | Microsoft Azure | Europe | No |
| Fallback | `Gemini 3.6 Flash` | `openai-api` | `litellm-unitalk` | Google | Pending gateway confirmation | No |

Mustad does not provide API keys. Unitalk controls credentials and routing through the Unitalk AI Gateway and LiteLLM.

The fallback route was tested directly and returned `FALLBACK_ROUTE_OK` using `Gemini 3.6 Flash` through `openai-api` in one API call.

## Native runtime controls

```text
model.max_tokens: ***
agent.max_turns: 15
agent.api_max_retries: 1
agent.reasoning_effort: medium
```

Hermes fallback is configured with one entry only and activates at most once per turn after primary technical failure. Fallback resets prompt cache and may increase token consumption.

## Default CLI tool allowlist

Enabled:

```text
web
terminal
file
code_execution
skills
todo
clarify
```

Disabled by default:

```text
browser
vision
session_search
memory
cronjob
computer_use
delegation
image_gen
bfl
tts
```

Browser, vision and session search remain conditionally available through an explicit future configuration change for an authorised task. They are not loaded during normal A1 processing.

## Tool-context reduction

| Metric | Before | After | Reduction |
|---|---:|---:|---:|
| Exposed tools | 30 | 14 | 53.33% |
| Tool-schema bytes | 58,887 | 27,043 | 54.08% |
| System-prompt bytes | 32,989 | 31,576 | 4.28% |

## Pilot quotas

| Limit | Warning | Hard |
|---|---:|---:|
| Tokens per candidate | 105,000 | 150,000 |
| Tokens per run | 245,000 | 350,000 |
| Tokens per day | 700,000 | 1,000,000 |
| Model calls per candidate | 5 | 6 maximum |
| Model calls per run | — | 15 maximum |

Additional controls:

- maximum three live candidates per run;
- concurrency one;
- one tool retry per failed call;
- no automatic full-run retry;
- no browser fallback in the default research plan;
- six search queries per single-segment run;
- three page reads per candidate;
- ten total research tool calls per candidate.

## Enforcement status

| Control | Enforcement |
|---|---|
| Output tokens per model call | Native Hermes |
| Model iterations per turn | Native Hermes |
| Provider retries | Native Hermes |
| One fallback activation per turn | Native Hermes |
| Maximum candidates | Deterministic input validation |
| Research tool budget | Deterministic search plan |
| Concurrency for combined review/export | Non-blocking runtime lock |
| Candidate cumulative tokens | Post-run guard pending gateway-level budget enforcement |
| Run cumulative tokens | Post-run guard pending gateway-level budget enforcement |
| Daily cumulative tokens | Date-filtered usage ledger |
| USD cost | Deferred by Séverine |

A cumulative token cap cannot currently interrupt Hermes in the middle of a turn. Native `max_turns` and `max_tokens` limit the main drivers, then the usage guard marks the run warning/exceeded. A true token hard stop before completion requires Unitalk Gateway or future n8n enforcement.

## Consumption optimisation

### Historical behavioural run

```text
Model: deepseek-v4-flash
Tokens: ***
API calls: 12
Quota result: exceeded
```

### Selected optimised run

```text
Model: deepseek-v4-flash
Tokens: ***
API calls: 5
Quota result: warning (call threshold), below all token hard limits
```

Reduction:

- 455,562 fewer tokens;
- 91.67% token reduction;
- seven fewer API calls;
- 58.33% call reduction.

The selected path preloads the two relevant Wave 3 skills, exposes only the terminal tool and runs one deterministic orchestration command.

A second variant without preloaded skills and with lower reasoning was rejected because it increased usage to 68,024 tokens and eight calls, exceeding the call cap.

## Daily usage ledger

The date-filtered ledger for 15 August 2026 records the three Step 7 model tests only:

```text
Total tokens: 117,019
API calls: 14
Daily status: pass
Warning threshold: 700,000
Hard threshold: 1,000,000
```

## Action boundaries

Confirmed during the optimised run:

- human decision remains pending;
- HubSpot remains unavailable;
- Twenty remains unavailable;
- A2 remains not triggered;
- no A2 handoff is authorised;
- no outreach or CRM write occurs;
- JSON, Markdown, CSV and Excel validations pass.

## Test results

All passed:

- Step 7 runtime and quota suite;
- primary model and fallback configuration validation;
- fallback gateway route test;
- minimal tool allowlist validation;
- candidate-count cap;
- research-plan cap;
- duplicate-run concurrency lock;
- daily ledger date filtering;
- usage warning/exceeded classification;
- Wave 1 regression suite;
- Wave 2 regression suite;
- Wave 3 regression suite;
- Python compilation;
- Hermes config check.

## Pending governance items

```text
Gemini processing region: pending gateway confirmation
Retention policy: pending DPA confirmation
Equinet administrator visibility: pending Equinet policy
Named A1 reviewer and backup: pending Equinet confirmation
USD cost conversion: deferred
Gateway-level cumulative token hard stop: future implementation
```

These do not block Step 8 synthetic profile tests. They remain open before production and, where applicable, before unsupervised real-data processing.

## Proposed decision

Step 7 is approved as complete for the controlled A1 V1 pilot configuration. Proceed to Step 8 — representative synthetic profile tests.
