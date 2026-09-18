# A2 Enrichment Review

**Canonical record:** `A2-INIT_D21BC65DDC16BB6B66F3`  
**Revision:** `A2-REV-STEP8_D21BC65DDC16BB6B66F3_005`  
**Canonical SHA-256:** `f125a7354e5b4635cfd352bc51ff3bed16ff5a0e0485189275685e8bdaa1ad6d`  
**Projection status:** `READ-ONLY — NOT A DECISION OR EXTERNAL ACTION`

## Decision Summary

| Segment | Subject | Workflow | Record decision | Data quality | A2 eligibility | A1 score/band | Review items |
|---|---|---|---|---|---|---|---|
| horse_owner | Kate Galvin \| Jonabell Farm | record_approved | approved | review_ready | not_checked | 75 / high | 1 |

## Review Queue

| Priority | Field | Current | Observations | Proposed action | Proposed | Evidence | Confidence | Freshness | Conflict | Protected | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| change | relationship.target_role_priority | null | [] | add | "secondary" | ["A2-EV-STEP8-JONABELL-ROLE"] | medium | not_applicable | none | not_protected | approved |

## Gaps, Conflicts and Limitations

| Missing | Unverified | Conflicts | Stale | Invalid | Limitations |
|---|---|---|---|---|---|
| [] | [] | [] | [] | [] | ["Kate Galvin is the selected named contact; target-role priority secondary is a reviewed classification, not a sourced fact or proof of purchasing authority.","HubSpot customer, Deal, consent, suppression and owner checks are unavailable.","No HubSpot, Twenty, n8n, Apify, outreach or downstream delivery.","Every record requires one final consolidated human review."] |

## Requalification

No requalification item is recorded in this revision.

## Evidence Summary

| ID | Namespace | Source | Policy | Reliability | URL | Summary |
|---|---|---|---|---|---|---|
| EV-DARLEY-JONABELL-001 | a1_reference | business_website | approved | high | https://www.darleyamerica.com/about-us/kentucky-thoroughbred-horse-farm-tours | Jonabell Farm in Lexington, Kentucky is described as one of the leading horse farms in the USA, the American headquarters of the global Godolphin operation, and home to the Darley thoroughbred stallions in the United States. The current roster names Cody’s Wish, Nyquist, Street Sense, Essential Quality, Frosted, Maxfield, and Medaglia d’Oro. The page describes Jonabell as a privately-owned, working thoroughbred horse farm and references its breeding shed. |
| EV-DARLEY-CONTACT-001 | a1_reference | business_website | approved | high | https://www.darleyamerica.com/contact-us/united-states/jonabell-farm | The official Jonabell Farm contact page lists General Enquiries telephone +1 859 255 8537 and email us-hello@godolphin.com; Kate Galvin as Nominations Sales and Operating Manager, Jonabell Farm, with email kgalvin@godolphin.com and mobile +1 859 519 5223; and address 3333 Bowman Mill Road, Lexington, Kentucky 40513, USA. |
| A2-EV-STEP8-JONABELL-STABLE | a2 | prospect_owned_website | approved | high | https://www.darleyamerica.com/about-us/kentucky-thoroughbred-horse-farm-tours | Official page describes a privately-owned working thoroughbred farm and breeding shed. |
| A2-EV-STEP8-JONABELL-ROLE | a2 | prospect_owned_website | approved | high | https://www.darleyamerica.com/contact-us/united-states/jonabell-farm | Official contact page identifies Kate Galvin as Nominations Sales and Operating Manager, Jonabell Farm. |
| A2-EV-STEP8-JONABELL-EMAIL | a2 | prospect_owned_website | approved | high | https://www.darleyamerica.com/contact-us/united-states/jonabell-farm | Official contact page publishes kgalvin@godolphin.com for Kate Galvin. |

## Action Boundaries

- This view is derived from canonical JSON and is not authoritative data storage.
- It does not approve a field, record, score revision, CRM write or outreach action.
- A1 remains the only numeric score-revision producer.
- External actions require the separately authorised workflow and receipt.
