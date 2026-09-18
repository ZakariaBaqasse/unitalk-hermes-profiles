# Decision Review — A2 Implementation Contract

**Step:** 1B  
**Current contract version:** `0.1.4`  
**Original approval version:** `0.1.0`  
**Profile status:** `FOUNDATION DESIGN IN PROGRESS — NOT PILOT-READY`  
**Static validation:** PASS  
**Decision:** APPROVED AS DRAFTED  
**Approver:** Séverine, Unitalk Operations  
**Original decision date:** `2026-08-16T15:43:31Z`  
**Clarification date:** `2026-08-16T16:10:17Z`

**HubSpot metadata intake:** `2026-08-25T09:51:49Z` — data-model image and six-object property export received; no live connection.

**HubSpot operational metadata intake:** `2026-08-25T09:51:49Z` — lifecycle/pipeline, users/teams/owners and process snapshots received. No enrichment-review asset or owner/backup assignment rules were identified; enabled workflow dependencies remain unverified.

**HubSpot governance confirmation:** `2026-08-25T10:28:44Z` — Creator absent; Campaign confirmed as a standard object; technical, CRM/configuration and OAuth approvers recorded. OAuth and A2 action approval remain pending.

## What the contract establishes

- A2 enriches only eligible prospects after the required A1 review.
- HubSpot remains Equinet's customer-facing source of truth.
- A2 preserves the A1 candidate, evidence, original score and approval.
- A1 remains the owner of ICP scoring.
- A2 may trigger requalification when verified enrichment materially affects an A1 criterion.
- A2 does not award points or calculate a replacement score.
- A1 applies its approved evidence and scoring rules to create a proposed new score revision.
- During the pilot, a human reviewer approves or rejects the revision.
- An approved revision may become the current operational score, but the original score and history remain immutable.
- Every proposed enriched value preserves the existing value, source, date, confidence and any conflict.
- Every enriched record remains subject to human review during the pilot.
- No CRM write, outreach, A3/A14 delivery or paid-provider call is authorised at this stage.
- Unavailable integrations remain explicitly identified as unavailable.

## Approved decisions

| ID | Approved decision | Consequence |
|---|---|---|
| D1 | The primary trigger is a recorded human A1 decision leading to `approved_for_a2`. | A2 does not start from a simple HubSpot Contact creation. |
| D2 | A1 owns scoring. A2 preserves the original score and may trigger requalification with verified new evidence. Any change is a new A1-generated, human-approved revision. | Scoring ownership remains deterministic and auditable while allowing the score to evolve. |
| D3 | Every enriched record requires human review during the pilot. | No enriched record is used automatically. |
| D4 | During the no-integration pilot, A2 cannot write to HubSpot or deliver a record to A3/A14. | Outputs remain review packages and draft handoffs. |

## Items not approved by this decision

This approval does not approve:

- the canonical A2 schema;
- the final field catalogue;
- Horse Owner and Farrier minimum data packages;
- confidence and data-quality definitions;
- sources, providers or budgets;
- models or tools;
- HubSpot or Twenty mappings;
- pilot or production use.

## Validation result

The validator checks:

- 22 required sections;
- 9 business and safety boundaries;
- 7 integration states;
- 6 prohibited availability or production claims;
- the clarified A1 scoring ownership and score-revision rule.

Current result: no validation errors.

## Recorded decision

**Approved as drafted**, with the later score-revision clarification recorded in version `0.1.1`.

Version `0.1.2` records the received HubSpot metadata snapshot without authorising live access or changing the approved action boundary.

Version `0.1.3` records the operational metadata and adds a hard block on any future HubSpot write until mapped property, list-membership and enabled-workflow dependencies are verified.

Version `0.1.4` records the confirmed HubSpot object and technical-governance decisions without changing the A2 business-review or production-approval boundaries.

This is not Equinet client sign-off, pilot approval, production approval or contractual acceptance.
