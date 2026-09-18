# A2 Enrichment Review

**Canonical record:** `A2-INIT_5DC8D468C11B265DA37B`  
**Revision:** `A2-REV-STEP8_5DC8D468C11B265DA37B_005`  
**Canonical SHA-256:** `6b5588934629edc1a590d91709dd40d6f9f8dcf6d59634a52d3bc0c185c4ed0e`  
**Projection status:** `READ-ONLY — NOT A DECISION OR EXTERNAL ACTION`

## Decision Summary

| Segment | Subject | Workflow | Record decision | Data quality | A2 eligibility | A1 score/band | Review items |
|---|---|---|---|---|---|---|---|
| farrier | Manfred Eckert \| Rood & Riddle Equine Hospital | held | held | incomplete | not_checked | 80 / high | 6 |

## Review Queue

| Priority | Field | Current | Observations | Proposed action | Proposed | Evidence | Confidence | Freshness | Conflict | Protected | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gap | organisation.service_area | null | [] |  | null | [] |  |  |  |  | not_required |
| gap | person.business_email | null | [] |  | null | [] |  |  |  |  | not_required |
| gap | person.business_phone | null | [] |  | null | [] |  |  |  |  | not_required |
| gap | person.professional_status | null | [] |  | null | [] |  |  |  |  | not_required |
| change | organisation.disciplines | null | [{"claim_type":"direct_fact","confidence_level":"high","error":null,"evidence_ids":["A2-EV-STEP8-RR-DISCIPLINES"],"freshness_status":"undated","normalised_value":["all breeds and disciplines"],"observation_id":"A2-OBS-RR-DISCIPLINES-001","raw_value":["all breeds and disciplines"],"verification_status":"verified"}] | add | ["all breeds and disciplines"] | ["A2-EV-STEP8-RR-DISCIPLINES"] | high | undated | none | not_protected | approved |
| change | relationship.target_role_priority | null | [] | add | "primary" | ["A2-EV-STEP8-RR-ROLE"] | medium | not_applicable | none | not_protected | approved |

## Gaps, Conflicts and Limitations

| Missing | Unverified | Conflicts | Stale | Invalid | Limitations |
|---|---|---|---|---|---|
| ["organisation.service_area","person.business_email","person.business_phone","person.professional_status"] | [] | [] | [] | [] | ["The stored official pages do not establish full-time, part-time or apprentice professional status for Manfred Eckert.","The Lexington location does not establish the Podiatry service area.","No named professional email or phone for Manfred Eckert was found in the bounded pages; form placeholders were excluded.","The organisation general phone remains available as fallback contactability but does not satisfy the named-target contact path.","The hospital-wide statement 'all breeds and disciplines' is retained as organisation-level context and is not narrowed to a specific Podiatry discipline.","HubSpot customer, Deal, consent, suppression and owner checks are unavailable.","No HubSpot, Twenty, n8n, Apify, outreach or downstream delivery.","Form placeholders are not contact data.","No employment status, service area or purchasing authority is inferred."] |

## Requalification

No requalification item is recorded in this revision.

## Evidence Summary

| ID | Namespace | Source | Policy | Reliability | URL | Summary |
|---|---|---|---|---|---|---|
| EV-RR-TEAM-001 | a1_reference | business_website | approved | high | https://roodandriddle.com/lexington-podiatry-team | Meet Your Podiatry Equine Veterinary Care Team. The Lexington page lists veterinarians and a dedicated FARRIERS team including Manfred Eckert (Co-Founder/Farrier), Benjamin Barhorst, CJF, Stuart Muir, NZCF, CJF, DIPWCF, and other named farriers. Lexington public phone: (859) 233-0371. |
| EV-RR-LEX-001 | a1_reference | business_website | approved | high | https://roodandriddle.com/lexington/ | Rood & Riddle Equine Hospital sits on 24 acres in the heart of the Bluegrass in Lexington, KY, as a horse referral center. The practice is known and respected worldwide for innovative and highly skilled treatment of horses and is run by 36 shareholders. |
| EV-RR-CONTACT-001 | a1_reference | business_website | approved | high | https://www.roodandriddle.com/contact | The official contact page footer lists the Lexington location at 2150 Georgetown Road, Lexington, KY 40511, the postal address PO Box 12070, Lexington, KY 40580, and telephone (859) 233-0371. The page provides a contact form but does not publish a general email address. |
| A2-EV-STEP8-RR-ROLE | a2 | prospect_owned_website | approved | high | https://roodandriddle.com/lexington-podiatry-team | The official Lexington Podiatry team page lists Manfred Eckert under FARRIERS with the exact title Co-Founder/Farrier. |
| A2-EV-STEP8-RR-DISCIPLINES | a2 | prospect_owned_website | approved | high | https://roodandriddle.com/lexington/ | The official Lexington hospital page states that Rood & Riddle provides ambulatory care for all breeds and disciplines. This is organisation-level context and is not narrowed to one Podiatry discipline. |

## Action Boundaries

- This view is derived from canonical JSON and is not authoritative data storage.
- It does not approve a field, record, score revision, CRM write or outreach action.
- A1 remains the only numeric score-revision producer.
- External actions require the separately authorised workflow and receipt.
