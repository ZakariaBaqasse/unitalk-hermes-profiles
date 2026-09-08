# Equinet A1 — V1 No-Integration Configuration Package

## 1. Profile identity

**Profile:** `equinet-a1-icp-discovery`  
**Capability:** ICP Discovery  
**Type:** Shared Equinet Sales and Marketing AI Collaborator  
**Owner:** Unitalk Operations  
**Deployment state:** `pilot_ready_no_integration`

A1 discovers, documents, qualifies, scores and ranks prospective professional Farriers and professional/commercial Horse Owners. It never performs outreach.

## 2. Users and access

The final Equinet roster and role-to-profile access matrix remain unconfirmed. Access should initially be limited to Unitalk Operations and the approved pilot cohort. The business reviewer role remains `A1 Business Reviewer` until Equinet names the primary and backup reviewer.

## 3. Business scope

- Market: United States.
- Pilot geography: Kentucky, prioritising Lexington.
- Primary segment: professional Farriers.
- Secondary segment: professional/commercial Horse Owners and equine operations.
- Maximum live candidates per run: 3.
- Concurrency: 1.

## 4. SOUL

Authoritative profile behaviour is stored in `SOUL.md`.

Core boundaries:

- DRAFT FOR APPROVAL;
- public professional research only;
- approved-source evidence required;
- no outreach;
- no HubSpot or Twenty write;
- no automatic A2 handoff;
- human review required.

## 5. Installed packages

| Package | Version | Status |
|---|---:|---|
| `a1-prospect-data-contract` | 1.1.0 | validated for A1 V1 pilot |
| `public-prospect-research` | 1.2.0 | validated for A1 V1 pilot |
| `prospect-segment-classification` | 1.1.0 | validated for A1 V1 pilot |
| `equinet-icp-qualification` | 1.0.0 | validated for A1 V1 pilot |
| `prospect-evidence-and-confidence` | 1.0.0 | validated for A1 V1 pilot |
| `icp-scoring-and-rationale` | 1.0.0 | validated for A1 V1 pilot |
| `ranked-prospect-review-package` | 1.0.0 | validated for A1 V1 pilot |
| `prospect-export` | 1.0.0 | validated for A1 V1 pilot |

## 6. Authoritative configurations

| Configuration | Version |
|---|---:|
| Prospect Candidate Schema | 1.0.0 |
| Field Dictionary | 1.1.0 |
| ICP Configuration | 1.0.0 |
| Approved Source Register | 1.0.0 |
| Evidence and Confidence Rules | 1.0.0 |
| ICP Scoring Model | 1.0.0 |
| Runtime Policy | 1.4.0 |

The release-candidate hashes are stored in `evaluations/step10/release-manifest.json`.

## 7. Model and tools

### Model route

- Primary: `deepseek-v4-flash`.
- Fallback: `Gemini 3.6 Flash`.
- Profile provider: `openai-api`.
- Gateway: `litellm-unitalk`.
- Mustad API key required: no.

### Default tools

- web;
- terminal;
- file;
- code execution;
- skills;
- todo;
- clarify.

Browser, vision and session search are conditional and disabled by default. Memory, cron, computer use, delegation and media-generation tools are disabled for normal A1 processing.

## 8. Research and source policy

Default research path:

```text
Exa discovery
→ official destination website
→ Firecrawl page extraction
→ About/Team/Services check
→ Contact/Location check
→ optional material-claim page
```

Limits:

- 6 search queries per single-segment run;
- 4 successful page reads per candidate;
- 10 total research tool calls per candidate;
- 0 default browser fallbacks;
- 1 targeted retry for a missing expected page.

Blocked or unavailable for retained evidence include Yellow Pages, Yelp, Mad Barn, EquineProFinder, Google Maps scraping, Apify Google Maps, Clay and Apollo.

## 9. Public contacts and A1/A2 boundary

A1 retains when officially published:

- full address and postal code;
- organisation general email/phone;
- one primary named contact;
- one optional justified secondary named contact.

Storage:

- primary contact → `identity.person`;
- organisation → `identity.organisation`;
- general/primary/secondary details → labelled `public_contacts[]`;
- all other people → A2 Enrichment.

Contact availability is non-scoring. It creates no consent or outreach permission.

## 10. Usage monitoring and circuit breaker

| Scope | Warning | Escalation | Local token hard stop |
|---|---:|---:|---|
| Candidate tokens | 1,000,000 | 3,000,000 | None |
| Run tokens | 1,000,000 | 3,000,000 | None |
| Daily tokens | 5,000,000 | 10,000,000 | None |

The technical model-iteration circuit breaker is 50 calls per turn. Native controls include `model.max_tokens: 4000`, one provider retry and one fallback activation maximum per turn. The economic hard stop is the Unitalk Gateway prepaid balance; no run may make the balance negative. Usage warnings inform optimisation and review but do not abandon an otherwise valid approved run.

Research defaults to four successful pages and ten tool calls per candidate, with monitored escalation up to eight pages and twenty calls when About/Team/Contact completion or a material claim requires it.

## 11. Acceptance evidence

Passed:

- foundation and configuration validation;
- Waves 1–3 skill tests;
- Step 7 runtime tests;
- Step 8 representative synthetic tests;
- Step 9 real-prospect pilot;
- Step 10 full regression and no-Web canonical replay;
- JSON, Markdown, CSV and Excel consistency;
- named-contact cardinality and non-scoring rules;
- no-action boundaries.

Reference real candidates:

- Rood & Riddle Lexington Podiatry — `80 / High`, confidence `84 / High`;
- Jonabell Farm / Darley — `75 / High`, confidence `84 / High`.

## 12. Current limitations

Unavailable:

- HubSpot duplicate/customer/opportunity/consent/exclusion checks;
- Twenty staging and review state;
- durable A2 handoff;
- n8n scheduling/orchestration;
- authoritative named Equinet reviewer;
- USD cost conversion.

The profile must not be described as fully integrated, autonomous, production-accepted or contractually accepted.

## 13. Approved pilot status

```text
pilot_ready_no_integration
```

This means the profile may be used in a controlled manual pilot with approved public sources, strict quotas, validated exports and mandatory human review. It does not authorise production writes or customer communications.
