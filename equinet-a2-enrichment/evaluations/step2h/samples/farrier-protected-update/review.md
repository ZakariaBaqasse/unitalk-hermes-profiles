# A2 Enrichment Review

**Canonical record:** `A2-STEP2F_FARRIER_001`  
**Revision:** `A2-REV-STEP2F_FARRIER_PROTECTED_004`  
**Canonical SHA-256:** `d30fb039ffba81dd1e13e6f7e04f2ec0c7b83c0da60254bf1b1a13562ce7d02b`  
**Projection status:** `READ-ONLY — NOT A DECISION OR EXTERNAL ACTION`

## Decision Summary

| Segment | Subject | Workflow | Record decision | Data quality | A2 eligibility | A1 score/band | Review items |
|---|---|---|---|---|---|---|---|
| farrier | Jordan Example \| Bluegrass Hoof Care — Synthetic | review_required | pending | review_ready | not_checked | 72 / high | 3 |

## Review Queue

| Priority | Field | Current | Observations | Proposed action | Proposed | Evidence | Confidence | Freshness | Conflict | Protected | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| protected | organisation.website | "https://example.com/bluegrass-hoof-care" | [{"claim_type":"direct_fact","confidence_level":"medium","error":null,"evidence_ids":["A2-EV-STEP2F-FARRIER-WEBSITE-NEW"],"freshness_status":"undated","normalised_value":"https://example.org/bluegrass-hoof-care-new","observation_id":"A2-OBS-FARRIER-WEBSITE-NEW","raw_value":"https://example.org/bluegrass-hoof-care-new","verification_status":"verified"}] | update | "https://example.org/bluegrass-hoof-care-new" | ["EV-TEST001","A2-EV-STEP2F-FARRIER-WEBSITE-NEW"] | medium | undated | none | protected_manual | pending |
| change | person.business_email | null | [{"claim_type":"direct_fact","confidence_level":"medium","error":null,"evidence_ids":["A2-EV-STEP2F-FARRIER-EMAIL"],"freshness_status":"undated","normalised_value":"farrier@example.com","observation_id":"A2-OBS-FARRIER-EMAIL","raw_value":"farrier@example.com","verification_status":"verified"}] | add | "farrier@example.com" | ["A2-EV-STEP2F-FARRIER-EMAIL"] | medium | undated | none | not_protected | pending |
| change | person.professional_credential | null | [{"claim_type":"direct_fact","confidence_level":"medium","error":null,"evidence_ids":["A2-EV-STEP2F-FARRIER-CREDENTIAL"],"freshness_status":"undated","normalised_value":"Synthetic Certified Farrier","observation_id":"A2-OBS-FARRIER-CREDENTIAL","raw_value":"Synthetic Certified Farrier","verification_status":"verified"}] | add | "Synthetic Certified Farrier" | ["A2-EV-STEP2F-FARRIER-CREDENTIAL"] | medium | undated | none | not_protected | pending |

## Gaps, Conflicts and Limitations

| Missing | Unverified | Conflicts | Stale | Invalid | Limitations |
|---|---|---|---|---|---|
| [] | [] | [] | [] | [] | ["No live source, provider, CRM or workflow connection is authorised."] |

## Requalification

No requalification item is recorded in this revision.

## Evidence Summary

| ID | Namespace | Source | Policy | Reliability | URL | Summary |
|---|---|---|---|---|---|---|
| EV-TEST001 | a1_reference | business_website | approved | high | https://example.com/bluegrass-hoof-care | Synthetic fixture: professional farrier service in Lexington supporting sport-horse clients. |
| A2-EV-STEP2F-FARRIER-EMAIL | a2 | synthetic_business_website | approved | medium | https://example.com/step2f-primary | Synthetic official site publishes a professional email address. |
| A2-EV-STEP2F-FARRIER-CREDENTIAL | a2 | synthetic_business_website | approved | medium | https://example.org/step2f-registry | Synthetic official registry confirms a professional credential. |
| A2-EV-STEP2F-FARRIER-WEBSITE-NEW | a2 | synthetic_business_website | approved | medium | https://example.org/bluegrass-hoof-care-new | A distinct synthetic source publishes the proposed replacement website. |

## Action Boundaries

- This view is derived from canonical JSON and is not authoritative data storage.
- It does not approve a field, record, score revision, CRM write or outreach action.
- A1 remains the only numeric score-revision producer.
- External actions require the separately authorised workflow and receipt.
