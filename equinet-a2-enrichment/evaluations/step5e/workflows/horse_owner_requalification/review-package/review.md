# A2 Enrichment Review

**Canonical record:** `A2-SYNTH_OWNER_001`  
**Revision:** `A2-REV-SYNTH_OWNER_002`  
**Canonical SHA-256:** `1936af2fc43799cfdda90121741cde56ca7f0190a8e1361ae4261aa163f75cd8`  
**Projection status:** `READ-ONLY — NOT A DECISION OR EXTERNAL ACTION`

## Decision Summary

| Segment | Subject | Workflow | Record decision | Data quality | A2 eligibility | A1 score/band | Review items |
|---|---|---|---|---|---|---|---|
| horse_owner | Lexington Breeding Farm — Synthetic Test Record | enrichment_planned | pending | needs_review | not_checked | 68 / medium | 1 |

## Review Queue

| Priority | Field | Current | Observations | Proposed action | Proposed | Evidence | Confidence | Freshness | Conflict | Protected | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| change | organisation.horse_count | null | [{"claim_type":"direct_fact","confidence_level":"medium","error":null,"evidence_ids":["A2-EV-HORSE-COUNT"],"freshness_status":"undated","normalised_value":4,"observation_id":"A2-OBS-HORSE-COUNT-001","raw_value":"More than three horses","verification_status":"partially_verified"}] | add | 4 | ["A2-EV-HORSE-COUNT"] | medium | undated | none | not_protected | pending |

## Gaps, Conflicts and Limitations

| Missing | Unverified | Conflicts | Stale | Invalid | Limitations |
|---|---|---|---|---|---|
| [] | ["organisation.horse_count"] | [] | [] | [] | ["Horse-count taxonomy remains unapproved.","No live source, provider, CRM or workflow connection is authorised."] |

## Requalification

| Kind | ID | Status | Criterion | Field assessments | Direction | Signals | Source return | Prior score | Revised score | Receipt | Review |
|---|---|---|---|---|---|---|---|---|---|---|---|
| signal | A2-RQ-SIG-HORSE_COUNT_001 | accepted_by_a1 | horse_owner.more_than_three_horses | ["A2-FLD-HORSE-COUNT"] | increase | ["A2-RQ-SIG-HORSE_COUNT_001"] |  |  |  |  | approved |
| return | A2-RQ-RET-HORSE_COUNT_001 | accepted_by_a1 |  | ["A2-FLD-HORSE-COUNT"] |  | ["A2-RQ-SIG-HORSE_COUNT_001"] |  |  |  | accepted | approved |
| score_revision | A1-SCORE-REV-HORSE_COUNT_001 | approved | ["horse_owner.more_than_three_horses"] | ["A2-FLD-HORSE-COUNT"] |  | ["A2-RQ-SIG-HORSE_COUNT_001"] | A2-RQ-RET-HORSE_COUNT_001 | 68 | 88 | accepted | approved |

## Evidence Summary

| ID | Namespace | Source | Policy | Reliability | URL | Summary |
|---|---|---|---|---|---|---|
| EV-TEST002 | a1_reference | business_website | approved | high | https://example.com/lexington-breeding-farm | Synthetic fixture: a commercial Lexington breeding farm managing more than three horses. |
| A2-EV-HORSE-COUNT | a2 | synthetic_business_website | approved | medium | https://example.com/lexington-breeding-farm | Synthetic fixture states more than three horses. |

## Action Boundaries

- This view is derived from canonical JSON and is not authoritative data storage.
- It does not approve a field, record, score revision, CRM write or outreach action.
- A1 remains the only numeric score-revision producer.
- External actions require the separately authorised workflow and receipt.
