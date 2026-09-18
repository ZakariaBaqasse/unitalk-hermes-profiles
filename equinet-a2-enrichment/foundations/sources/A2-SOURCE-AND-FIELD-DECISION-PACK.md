# Equinet A2 Enrichment — Source Strategy and Field Decision Pack

> **Historical discovery artifact.** For current profile-URL collection rules, use the active foundation manifest and the approved SOC-1 through SOC-8 clarification. Where this document says manual/API-only collection, the later clarification also permits retaining explicit professional social-profile links published on the approved official website without opening or extracting the linked profile.

**Version:** `0.1.0-draft.2`  
**Status:** `UNITALK PROPOSAL — EQUINET DECISIONS REQUIRED BEFORE SOURCE ACTIVATION`  
**Profile:** `equinet-a2-enrichment`

## 1. Purpose

This pack defines the recommended source strategy for A2 Enrichment and explains which business-field decisions remain incomplete.

It does not activate a source, provider, account, connector or automated extraction method. A source approved for A1 is not automatically approved for new A2 collection. A2 may reuse evidence lawfully received in the approved A1 handoff, but new A2 access requires an A2 source-policy decision covering the enrichment purpose and fields.

## 1.1 A1 versus A2 collection boundary

A2 is not a second discovery crawl. It enriches fields and relationships for a candidate already approved after A1.

| A1 responsibility | A2 additional responsibility |
|---|---|
| Discover candidate names and official destinations | Accept only the approved candidate and preserve the source handoff |
| Resolve person, organisation or linked identity sufficiently for ICP review | Resolve remaining operational identity ambiguity and additional role-relevant stakeholders |
| Capture organisation general contact, one primary named contact and at most one justified secondary contact when publicly available | Verify or supplement only missing/uncertain contact channels needed for the approved A2 package |
| Capture public business address, email, phone and official-profile URLs encountered during research | Normalise, verify, compare against CRM baselines and prepare field-level proposals |
| Collect enough services, disciplines, professional activity and scale evidence for ICP qualification | Fill approved post-qualification gaps such as current role, credentials, service area, horses served, exact/range horse count and recent activity |
| Calculate ICP score and confidence | Create requalification signals when new verified evidence may change an A1 criterion; never rescore directly |
| Run permitted directory discovery under the A1 source register | Reuse A1 directory evidence; do not revisit or broaden directory extraction by default |

A2 must perform a field-level gap analysis before any new source call. If the A1 value is valid, fresh enough and sufficient for the approved A2 purpose, A2 reuses it. New research is permitted only for a named gap, conflict, verification requirement or freshness issue.

## 2. Recommended source hierarchy

| Tier | Source | Recommended A2 use | Current readiness |
|---|---|---|---|
| 0 | Immutable A1 handoff | Reuse existing identity, public contacts, qualification evidence and limitations without recollection | Available for fixtures/manual packages; durable handoff not connected |
| 0 | HubSpot live records | Authoritative current Contact, Company, Deal, consent, suppression, owner, lifecycle and customer state | Metadata received; live read unavailable |
| 1 | Equinet-authorised internal files or app records | Authoritative client-supplied professional/business facts within explicit permissions | Per-file approval required |
| 1 | Prospect's official business website | Primary source for self-published role, business identity, location, professional contacts, services, disciplines, service area and dated activity | Recommended for no-integration pilot under per-site checks |
| 2 | Official professional associations and registries | Credentials, memberships, registration and dated professional facts | Manual/API-controlled; exact source rights required |
| 2 | Equinet sales-representative confirmation | Human-confirmed corrections or business context with actor and timestamp | Permitted through recorded review; not a substitute for outreach consent |
| 3 | Approved public business/professional directories | Reuse evidence already present in the A1 handoff; new A2 access only for an approved named gap | A1 register exists; no default A2 revisit or extraction; A2 purpose/access expansion requires separate approval |
| 3 | Approved Google Maps/Places route | Business discovery, address, website and phone within approved licence/method | A1 bounded route exists; not automatically active for A2 |
| 4 | Commercial enrichment and verification providers | Email/phone discovery, deliverability verification or structured business data | None approved or connected; benchmark and budget required |
| 5 | LinkedIn, Facebook, Instagram and similar platforms | Manual discovery or official API use only | Automated access blocked without platform permission/approved API |
| 6 | Search index | Discover destination URLs and candidate sources | Discovery only; snippets are not retained evidence |

## 3. Recommended no-integration source stack

For the first A2 synthetic and bounded manual tests, use only:

1. the approved A1 handoff and evidence;
2. a targeted official-site check only when A1 left an approved field gap, conflict, verification need or freshness issue, subject to per-site access checks;
3. Equinet-authorised files supplied for the specific test;
4. a human-supplied official registry or association result when its use is permitted;
5. deterministic format and consistency checks.

Do not use during the initial no-integration test:

- paid enrichment providers;
- automated LinkedIn, Facebook or Instagram access;
- login-gated or member-only data;
- private or inferred personal contact details;
- direct Google Maps scraping;
- repeat or broaden A1 directory collection by default;
- A1-approved directory automation for a new A2 field or purpose unless the A2 register explicitly authorises it;
- any source or method that requires unapproved spend or account access.

## 4. Field-specific source recommendations

| Field family | Preferred sources | Important boundary |
|---|---|---|
| Existing identity and contacts | A1 handoff, then HubSpot when connected | Preserve protected/manual values and conflicts |
| Current role/title | Official business site, authorised CRM, direct Equinet confirmation | A role supports business context but does not automatically prove consent or final purchasing authority |
| Professional email/phone | Official business site; later approved provider | Work/business contact only unless Equinet approves another category; no guessed patterns |
| Company identity/domain/address | Official website, authorised CRM, approved business source | Company domain is not a unique HubSpot key by itself |
| Farrier status and credentials | Official professional site, association/credential registry, direct confirmation | Current activity and credential status need freshness rules |
| Farrier disciplines/services | Official services/profile pages, permitted association record | Use controlled taxonomy; preserve uncategorised source wording |
| Farrier service area | Explicit official statement, approved directory or direct confirmation | Do not infer solely from one address |
| Farrier client base | Explicit aggregate professional statement or authorised internal data | Do not collect client names or infer size from followers/reviews |
| Horses served per month | Explicit direct/authorised source | Do not infer from social activity or business size |
| Horse count | Authorised CRM/direct confirmation or explicit official statement | Do not infer; resolve HubSpot range overlap before deterministic use |
| Stable/farm type and disciplines | Official business site, authorised CRM/direct confirmation | Keep facility type separate from person role |
| Recent activity | Dated official website/news/event page or authorised CRM activity | Equinet must define qualifying event types and freshness window |
| Public social signals | Manual public observation or approved official API | Define allowed signals; no scraping or follower-based authority inference |
| Mutual connections | Authorised CRM or approved official platform integration | Keep unavailable until source, account, rights and purpose are approved |
| Consent, opt-out, customer, Deal and sequence status | HubSpot only when connected | Never infer from public data or an enrichment provider |
| Owner, team and territory | HubSpot plus approved assignment rules | Preserve existing owner; use `needs_owner_review` until rules and backup are confirmed |

## 5. Commercial provider strategy

Do not select one generic provider before defining the exact fields. Separate provider jobs:

- email discovery;
- email deliverability verification;
- business phone/direct-dial discovery;
- phone validation;
- company/domain enrichment;
- professional-profile data;
- equine-industry-specific data.

Equinet previously tested Apollo, Dropcontact, Hunter, RocketReach and ContactOut without sufficient quality or relevance. Unitalk should therefore benchmark providers against an approved fixed dataset rather than assume a broad database will cover US Farriers and Horse Owners.

A provider benchmark must compare:

- precision against known truth;
- coverage by Farrier and Horse Owner segment;
- source/provenance transparency;
- freshness and last-verification date;
- false-positive and identity-mismatch rate;
- US equine-market relevance;
- API and storage rights;
- privacy and opt-out handling;
- cost per useful verified field, not cost per returned record;
- latency, rate limits and retry behaviour;
- HubSpot/Unitalk integration fit.

No provider test may use live Mustad Data until the provider, account, DPA/data route, purpose and budget are approved.

## 6. Why the current enrichment-field list is incomplete

The A2 blueprint names useful information but does not yet provide a deployable field catalogue.

Current examples include:

- email;
- phone;
- role;
- herd size;
- disciplines;
- recent activity;
- Farrier client base and service area;
- social signals;
- mutual connections;
- basic Contact and Company properties;
- unspecified “other relevant data”.

For each field, the following decisions are still missing or incomplete:

1. canonical field key and business definition;
2. person, organisation, relationship or record-level ownership;
3. applicable segment: Farrier, Horse Owner or both;
4. required before A2 review, required before outreach or optional;
5. exact value type, unit and controlled taxonomy;
6. allowed and prohibited sources;
7. accepted evidence and verification rule;
8. confidence threshold;
9. freshness period and recheck trigger;
10. protected/manual status;
11. conflict and precedence rule;
12. behaviour when unknown, unavailable or not found;
13. permitted personal-data category;
14. whether paid lookup is allowed;
15. HubSpot mapping candidate and direction;
16. whether the field can affect A1 requalification;
17. human reviewer and approval requirement.

The existence of a HubSpot property does not answer these business questions.

## 7. Ambiguous fields requiring Equinet decisions

### Professional contact details

Equinet must confirm:

- whether one verified work email **or** one verified business phone is sufficient;
- whether personal email addresses are prohibited, allowed only when publicly published for business use, or allowed from an approved provider;
- whether mobile/direct-dial discovery is permitted;
- whether secondary emails and phone numbers are needed;
- whether a general organisation contact can satisfy the minimum package when no named contact is available.

### Role and buying influence

Confirm:

- which roles A2 should actively seek;
- whether HubSpot Buying Role may be proposed by A2 or must remain human/CRM-owned;
- which titles justify a requalification signal;
- how current a role must be.

### Horse Owner fields

Confirm:

- whether exact horse count, range or either format is acceptable;
- how to resolve the overlapping HubSpot ranges `5 - 20` and `11 - 25`;
- whether horse count is required before enrichment review or only before outreach;
- the approved discipline and stable-type taxonomies;
- whether business/farm-level horse count may be associated with an individual Contact.

For the pilot, the recommended resolution is not to create or modify a HubSpot property. A2 should use a verified exact `owner_horse_count` when available and place the record in a non-overlapping internal A2 horse-count category. The existing HubSpot `horse_count_range` remains a protected baseline. After workflow, report and historical-data impact review, Unitalk may propose correcting the options of that existing property; no new HubSpot range property is proposed by default.

### Farrier fields

Confirm:

- required professional-status values;
- accepted certification bodies and statuses;
- whether years of experience is required or optional;
- whether `horses served per month` may be stored and from which source;
- service-area format: states, counties, radius, postal codes or free text;
- whether client-base information means aggregate size/type only; client identities should remain prohibited by default.

### Recent activity

Define:

- qualifying activity types;
- the freshness window;
- whether website updates, events, competition entries, business expansion, app activity and CRM engagement are separate fields;
- which activity may affect ICP requalification versus outreach timing only.

### Social signals

Define:

- permitted platforms;
- permitted access methods;
- allowed signals, such as dated professional posts or public business profile presence;
- prohibited signals, such as private networks, inferred personal interests or follower-based purchasing authority;
- freshness and corroboration requirements.

### Mutual connections

Confirm:

- the authorised source;
- the entitled user/account;
- whether the purpose is routing, introduction or context only;
- what may be stored;
- whether the platform permits API access and internal CRM storage.

Until these items are confirmed, `mutual_connections` should remain unavailable.

### LinkedIn automation feasibility

Apify currently lists Community Actors that can technically search employees from a LinkedIn company URL or company name, search people by company/job title/location, and retrieve profile details from an individual LinkedIn profile URL. The reviewed Actors are maintained by HarvestAPI rather than Apify.

Technical capability does not create permission. LinkedIn's current User Agreement prohibits scraping or copying profiles and other service data with scripts, robots or other automated means unless LinkedIn separately permits it. Apify's Actor Terms state that Community Actors are not vetted or guaranteed for security, accuracy or legal compliance and that the customer must perform due diligence.

The candidate Actors are therefore recorded as `blocked_pending_rights_and_vendor_review`. The current recommended pilot route is official-site evidence plus an authorised human manual LinkedIn check limited to current professional role and company. See `A2-LINKEDIN-APIFY-FEASIBILITY-REVIEW.md`.

## 8. HubSpot fields already available as mapping candidates

The received property export contains relevant candidates including:

- identity/contact fields;
- `contact_type` and `company_type`;
- Farrier status, certifications, disciplines and horses served;
- Horse Owner count, range, disciplines, breeds, stable name and type;
- `contact_verified`, Company address verification and `data_quality`;
- enrichment opt-out;
- consent, legal basis, opt-out and do-not-contact fields;
- Lifecycle Stage, Lead Status, current-customer and sequence states;
- owner, assigned rep, team, territory and business unit.

These are mapping candidates only. Unitalk must propose how the canonical fields map to them, and Equinet must approve the business meaning, protected status and exceptions.

Existing HubSpot score fields are not the A1 score and must not replace the approved A1 score-revision model. A1 owns scoring; A2 may only trigger requalification with verified evidence.

## 9. Decisions owned by Unitalk

Unitalk should propose:

- the canonical field-assessment structure and field keys;
- the A2 source-register format and access profiles;
- source-specific technical preflight and runtime controls;
- deterministic normalisation and validation methods;
- evidence, confidence, freshness and conflict models;
- provider benchmark design;
- cost, retry and idempotency controls;
- A2-to-HubSpot mapping and gap fields;
- audit, review and failure behaviour;
- minimum-scoped connector design.

Unitalk must not ask Equinet to design APIs, schemas, retry logic or implementation internals from scratch.

## 10. Decisions owned by Equinet

Equinet should confirm:

- business purpose and priority of each enrichment field;
- mandatory versus optional fields by segment and stage;
- accepted professional/personal contact categories;
- prohibited data categories;
- approved sources or source families from a business perspective;
- acceptable inference level and evidence standard;
- field freshness expectations;
- protected fields and business exceptions;
- reviewer and backup reviewer;
- provider budget and spend approver;
- whether internal Equinet app or other first-party data may be used;
- cross-entity access boundary between Equinet and other Mustad records;
- business acceptance criteria and representative examples.

Equinet business approval does not override source terms, privacy rules or platform permissions.

## 11. Joint approval decisions

Unitalk and Equinet must jointly approve:

- the A2 business field catalogue;
- Farrier and Horse Owner minimum data packages;
- the A2 source register and access methods;
- field-specific source precedence;
- verification and confidence definitions;
- provider selection and budget caps;
- protected-field and conflict rules;
- the A2-to-HubSpot mapping;
- pilot volume, accuracy and coverage measures;
- escalation and fallback behaviour.

## 12. Minimum Equinet information request

The original 28-row field-decision template is an internal Unitalk working matrix. Do not send it to Equinet as the primary questionnaire.

Use the slim client template `A2-EQUINET-CLIENT-DECISION-TEMPLATE-SLIM.csv`. Five decisions are needed before finalising the business field catalogue:

1. target Farrier roles and priority;
2. target Horse Owner organisation roles and priority;
3. maximum named contacts and fallback when no target role is found;
4. minimum contactability for A2 review readiness.
5. non-overlapping horse-count ranges and whether ranges are derived from a verified exact count.

The remaining privacy, field-priority, reviewer, provider/budget and owner-assignment decisions are labelled for their later pilot, paid-test or go-live gate.

The detailed internal matrix remains available for Unitalk design traceability and contains the following decision areas:

| Area | Decision required from Equinet |
|---|---|
| Minimum contact | Is verified work email or business phone sufficient, and are public personal/mobile details permitted? |
| Stakeholders | Which roles should A2 seek, and what is the maximum number of additional stakeholders per prospect? |
| Horse Owner | Exact versus range horse count, required stage, stable type and discipline taxonomy; resolve overlapping ranges. |
| Farrier | Required status, certifications, service-area format, horses-served/client-base boundaries. |
| Activity | Qualifying activity types and freshness window. |
| Social | Permitted platforms, signals and manual/API access rules. |
| Mutual connections | Approved source/account, purpose and storage boundary, or confirmation that the field remains disabled. |
| Sources | Business-approved source families and prohibited sources for A2. |
| Privacy | Data categories A2 must never collect or store. |
| Review | Named A2 reviewer and backup; field-level approval exceptions. |
| Cost | Pilot budget, provider/spend approver and permitted paid lookup types. |
| Success | Accuracy, coverage and review-time measures for the pilot. |

## 13. Recommended decision sequence

1. Approve the field purposes and minimum packages.
2. Approve source families and prohibited data.
3. Unitalk drafts the A2 source register and field catalogue.
4. Unitalk designs a provider benchmark only for gaps not covered by A1, official websites, HubSpot or authorised internal data.
5. Equinet approves provider, budget and data route.
6. Unitalk configures and tests the connector with synthetic or approved non-production data.
7. Begin a bounded no-integration pilot with every record reviewed.

## 14. Current readiness

```text
A1 evidence reuse: available through approved handoff design
Official-site A2 research: recommended for bounded pilot after A2 source-register approval
HubSpot metadata: received
HubSpot live records: unavailable
Commercial enrichment provider: none approved or connected
LinkedIn/Social automation: prohibited without approved official access
A2 business field catalogue: incomplete
A2 source register: not yet created
Provider benchmark: pending field decisions and budget
```
