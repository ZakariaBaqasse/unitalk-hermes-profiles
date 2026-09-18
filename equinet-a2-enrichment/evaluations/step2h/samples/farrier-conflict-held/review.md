# A2 Enrichment Review

**Canonical record:** `A2-STEP2F_FARRIER_001`  
**Revision:** `A2-REV-STEP2F_FARRIER_CONFLICT_004`  
**Canonical SHA-256:** `cba702550a01c5943a58acee389f59ad25496d45a3b4f997e352f26b57f0d377`  
**Projection status:** `READ-ONLY — NOT A DECISION OR EXTERNAL ACTION`

## Decision Summary

| Segment | Subject | Workflow | Record decision | Data quality | A2 eligibility | A1 score/band | Review items |
|---|---|---|---|---|---|---|---|
| farrier | Jordan Example \| Bluegrass Hoof Care — Synthetic | held | held | conflict | not_checked | 72 / high | 2 |

## Review Queue

| Priority | Field | Current | Observations | Proposed action | Proposed | Evidence | Confidence | Freshness | Conflict | Protected | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| conflict | person.business_email | null | [{"claim_type":"direct_fact","confidence_level":"medium","error":null,"evidence_ids":["A2-EV-STEP2F-FARRIER-EMAIL"],"freshness_status":"undated","normalised_value":"farrier@example.com","observation_id":"A2-OBS-FARRIER-EMAIL","raw_value":"farrier@example.com","verification_status":"verified"},{"claim_type":"contradictory_evidence","confidence_level":"medium","error":null,"evidence_ids":["A2-EV-STEP2F-FARRIER-EMAIL-CONFLICT"],"freshness_status":"undated","normalised_value":"other@example.com","observation_id":"A2-OBS-FARRIER-EMAIL-CONFLICT","raw_value":"other@example.com","verification_status":"verified"}] | hold | null | ["A2-EV-STEP2F-FARRIER-EMAIL","A2-EV-STEP2F-FARRIER-EMAIL-CONFLICT"] | medium | undated | material | not_protected | held |
| change | person.professional_credential | null | [{"claim_type":"direct_fact","confidence_level":"medium","error":null,"evidence_ids":["A2-EV-STEP2F-FARRIER-CREDENTIAL"],"freshness_status":"undated","normalised_value":"Synthetic Certified Farrier","observation_id":"A2-OBS-FARRIER-CREDENTIAL","raw_value":"Synthetic Certified Farrier","verification_status":"verified"}] | add | "Synthetic Certified Farrier" | ["A2-EV-STEP2F-FARRIER-CREDENTIAL"] | medium | undated | none | not_protected | pending |

## Gaps, Conflicts and Limitations

| Missing | Unverified | Conflicts | Stale | Invalid | Limitations |
|---|---|---|---|---|---|
| [] | [] | ["person.business_email"] | [] | [] | ["Conflicting professional email values.","No live source, provider, CRM or workflow connection is authorised."] |

## Requalification

No requalification item is recorded in this revision.

## Evidence Summary

| ID | Namespace | Source | Policy | Reliability | URL | Summary |
|---|---|---|---|---|---|---|
| EV-TEST001 | a1_reference | business_website | approved | high | https://example.com/bluegrass-hoof-care | Synthetic fixture: professional farrier service in Lexington supporting sport-horse clients. |
| A2-EV-STEP2F-FARRIER-EMAIL | a2 | synthetic_business_website | approved | medium | https://example.com/step2f-primary | Synthetic official site publishes a professional email address. |
| A2-EV-STEP2F-FARRIER-CREDENTIAL | a2 | synthetic_business_website | approved | medium | https://example.org/step2f-registry | Synthetic official registry confirms a professional credential. |
| A2-EV-STEP2F-FARRIER-EMAIL-CONFLICT | a2 | synthetic_business_website | approved | medium | https://example.org/step2f-secondary | Synthetic second source publishes a conflicting professional email. |

## Action Boundaries

- This view is derived from canonical JSON and is not authoritative data storage.
- It does not approve a field, record, score revision, CRM write or outreach action.
- A1 remains the only numeric score-revision producer.
- External actions require the separately authorised workflow and receipt.
