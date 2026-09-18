# Equinet A2 Step 9 Evaluation Report

## Scope

Evaluation covers the accepted two-candidate Step 8 no-integration pilot, current offline regressions and exact no-Web replay. The sample is too small to establish production-level precision or commercial uplift.

## Candidate outcomes

| Candidate | A1 score/band | A2 outcome | Material result |
|---|---:|---|---|
| Jonabell Farm / Kate Galvin | 75 / High | Approved | Complete review package; selected named contact classified `secondary` |
| Rood & Riddle / Manfred Eckert | 80 / High | Held | Role and organisation-level disciplines verified; required status, service area and named contactability remain incomplete |

## Quality findings

- Canonical identity and A1 score lineage were preserved for both candidates.
- No candidate was forced to pass an A2 package because of a High A1 score.
- No purchasing authority, service area, employment status or contact detail was invented.
- The contact-form placeholder was excluded.
- One official-site contact-field allowlist mismatch was found and corrected.
- Review views remained lossless and consistent across Markdown, CSV and Excel.

## Regression and replay

- Step 9A: 15/15 controls passed.
- Step 9B: 10/10 controls passed.
- Offline suites and workflows: 11/11 passed.
- Operator compilation: 14/14 passed.
- Canonical byte equality: 2/2 passed.
- Derived export equality: passed.
- Web/provider/external actions during replay: 0/0/0.

## Consumption

The Rood & Riddle behavioural replay used 232,286 input tokens, 2,247 output tokens and 234,533 total tokens across 9 model API calls. The reported cost value was 0.0 but `cost_status` was `unknown`; cost is therefore undetermined.

The main optimisation opportunity is to avoid failed relative-path discovery and reduce repeated context loading. The release candidate requires absolute paths and records warning/escalation thresholds without imposing an arbitrary local token hard stop.

## Limitations

- Two candidates are insufficient for production quality claims.
- No live HubSpot, Twenty, n8n or Apify integration was tested.
- No CRM duplicate/customer/Deal/consent/suppression/owner state was authoritatively checked.
- No write, outreach, downstream delivery or production rollback was tested.
- Time saved and commercial impact were not measured against an Equinet baseline.
