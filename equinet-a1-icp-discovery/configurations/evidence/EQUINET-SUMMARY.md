# Equinet A1 — Evidence and Confidence Rules: V1 Summary

**Status:** Approved by Séverine for Unitalk A1 V1 — subject to later Equinet review and agreed updates  
**Applies to:** A1 ICP Discovery  
**Related documents:** Prospect Candidate Schema V1, ICP Configuration V1, Approved Source Register V1

## Purpose

A1 identifies potential Farriers and professional/commercial Horse Owners from permitted sources. These rules ensure that every qualification decision is supported by traceable evidence and that the quality of the evidence is visible to the reviewer.

The rules distinguish two separate measures:

- **ICP score:** commercial fit with the Equinet target profile.
- **Confidence score:** reliability, clarity and completeness of the evidence supporting the candidate.

A high ICP score does not compensate for weak evidence, and high confidence does not make a prospect commercially relevant by itself.

## Core evidence principles

1. A1 records the source URL, date accessed and a relevant evidence excerpt for each material claim.
2. A1 distinguishes:
   - **Direct fact** — explicitly stated by the source;
   - **Role-based conclusion** — a reasonable conclusion from a current decision-role title;
   - **Reasonable inference** — plausible but not explicitly stated;
   - **Unknown** — not established by available evidence;
   - **Contradictory evidence** — material sources conflict and require review.
3. Search results, Google Maps and manually selected directory records are discovery inputs. They are not retained as the primary evidence for a candidate.
4. A1 may retain publicly displayed professional contact details when the page and evidence reference are recorded. Public information does not create outreach consent.
5. A1 never invents or infers private contact details, horse count, client-base size or purchasing authority without the required evidence.
6. Blocked, unavailable or untraceable sources cannot support a confirmed claim.

## Business website as a primary source

The current official website of a Farrier, farm, stable or equine business is treated as authoritative for facts that the business controls and explicitly publishes. A second source is not required for:

- business identity and organisation name;
- public business location and service area;
- publicly displayed professional contact details;
- stated services and specialisations;
- current team roles and job titles;
- business type and explicitly stated operation details;
- explicitly stated horse count, team size or facility scale, when current and unambiguous.

A separate authoritative source is required for external facts, including current certification or membership validity, third-party awards, official competition results and CRM status.

## Purchasing influence

A current decision-role title from a reliable source can establish **likely purchasing influence**.

Examples of strong decision roles include:

```text
Owner · Founder · CEO · General Manager · Farm Manager · Stable Manager
Barn Manager · Operations Manager · Purchasing Manager · Head Trainer
Owner/Operator · Self-employed Farrier · Farrier Business Owner
```

A1 will describe this accurately, for example:

> “Likely purchasing influence based on the current role of Farm Manager.”

A1 will not claim proven budget authority unless that authority is explicitly stated.

## When corroboration is needed

Corroboration means that an independent source confirms the same material fact. It strengthens confidence, but it is not required for every claim.

A1 starts with one permitted primary source, normally the prospect's business website. It seeks a second source only when a claim is:

- external to the business;
- unclear, vague or stale;
- material to high-priority qualification but not directly supported;
- a certification, membership, official result or CRM status;
- contradicted by another source.

A third source is needed only if a material conflict remains unresolved.

Two pages from the same website, copied directory descriptions, multiple search results pointing to the same page or syndicated copies of one release do not count as independent corroboration.

## Important evidence rules

| Claim | Evidence required |
|---|---|
| Professional activity | Current services, professional listing or dated recent activity |
| Public contact details | Explicitly displayed business contact detail on the cited page |
| Horse count | Explicit current number or reliable current record; never inferred from photos, acreage or facility size |
| Client-base size | Explicit statement or direct quantitative evidence; never inferred from reviews, followers or years in business |
| Purchasing influence | Explicit responsibility or current approved decision-role title |
| Certification / membership | Official issuer or association source where current validity matters |
| CRM customer / opportunity / opt-out status | Live HubSpot or approved authoritative CRM source only |

## Confidence model

A deterministic calculation produces a score out of 100 using six dimensions:

| Dimension | Maximum points |
|---|---:|
| Identity certainty | 20 |
| Source quality | 20 |
| Evidence directness | 20 |
| Corroboration | 20 |
| Freshness | 10 |
| Completeness | 10 |
| **Total** | **100** |

| Confidence level | Score |
|---|---:|
| High | 80–100 |
| Medium | 60–79 |
| Low | 0–59 |

A current, complete and explicit official business website can produce High confidence even when it is the only source. The absence of a second source is reflected through a lower corroboration component, rather than an automatic Medium cap.

## Safety controls

The confidence score is capped when:

| Condition | Maximum final score |
|---|---:|
| A mandatory ICP claim is supported only by inference | 59 |
| Candidate identity remains unresolved | 39 |
| Material evidence conflicts | 39 |
| Minimum review package is incomplete | 39 |

The assessment is invalid if it relies on a blocked source, lacks permitted evidence or contains fabricated/untraceable evidence.

## Freshness

A current official business website does not need a visible publication date for facts that the business explicitly publishes and controls. When the page is available and no stale or contradictory signal exists, A1 treats those facts as current.

The same principle applies to an official registry or association record that presents an active or current status.

Freshness windows apply to dated external sources:

| Information | Maximum age |
|---|---:|
| Public professional contact details | 180 days |
| Location, business operation, horse count, client-base size and purchasing influence | 365 days |
| Certification or membership | 365 days unless the official source confirms current validity |
| Specialisation or discipline | 730 days |
| CRM status or exclusions | Live at the time of the run |

An undated external source may provide historical or secondary context, but it does not alone establish a current time-sensitive claim. A closed website, broken contact, archived content, explicit retirement or conflicting current detail triggers review or lower confidence.

## Future Google Business Profile integration

Google Maps remains discovery-only in A1 V1. A Google Business Profile may become a primary source after an approved official Google Business Profile or GoogleLocations API integration can confirm owner-management, verification status or another approved equivalent signal.

When activated, it may support business-controlled facts such as business name, address, public phone, website, opening hours, category and explicitly displayed services. It does not alone establish horse count, client-base size, certification, CRM status or purchasing influence beyond an explicit approved role.

## A1 V1 workflow

```text
Permitted web search or human-selected directory seed
→ identify the prospect's own business website
→ collect direct, current business facts
→ assess whether material claims are sufficiently supported
→ seek targeted additional evidence only when needed
→ calculate confidence and ICP score separately
→ produce an evidence-backed Prospect Candidate for human review
```

A1 does not initiate outreach, create CRM records or remove human review based on confidence.

## How changes will be managed

These rules are versioned. If Equinet wishes to change a rule, Unitalk will:

1. record the requested change and business reason;
2. assess its impact on current candidate outputs, scoring, source use and review;
3. propose the exact policy change for approval;
4. update and test the deterministic rules;
5. publish a new version with an approval record;
6. retain the prior version for auditability.

Typical versioning approach:

| Change | Version impact |
|---|---|
| Clarification or correction with no behavioural impact | Patch version, e.g. `1.0.1` |
| New claim type, source tier or compatible rule | Minor version, e.g. `1.1.0` |
| Material change to confidence calculation, evidence standard or review outcome | Major version, e.g. `2.0.0` |

A candidate always records the evidence-confidence method version used for its assessment. This makes it possible to distinguish candidates evaluated under earlier versus later rules.

## Items for Equinet review

Unitalk applies the current confidence dimensions, score bands, safety caps and freshness windows in production under the approved scope. Equinet may request adjustments at any time. Changes will be documented, tested and versioned rather than applied silently.
