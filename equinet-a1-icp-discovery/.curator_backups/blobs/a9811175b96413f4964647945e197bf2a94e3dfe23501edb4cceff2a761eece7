# Equinet A1 Prospect Candidate — Field Dictionary

**Version:** 1.1.0  
**Status:** Approved by Unitalk for A1 pilot configuration  
**Scope:** A1 ICP Discovery output and A1-to-A2 handoff

## Design rules

1. One candidate represents one prospective person, organisation, or linked person–organisation identity.
2. A candidate is not a HubSpot Contact or Company. CRM identifiers appear only after an authoritative match or approved write.
3. Every production candidate carries at least one source-evidence record.
4. Publicly available data does not establish consent or outreach eligibility.
5. ICP score measures commercial fit. Confidence measures evidence quality and identity certainty.
6. Unknown, unavailable and not checked are valid states and must not be converted into positive results.
7. A1 gathers only the minimum public information needed to identify and qualify. Deeper enrichment remains with A2 unless an approved A1 minimum-data rule requires it.
8. For an organisation, `identity.person` may contain one selected primary named contact. One optional secondary named contact may appear only in `public_contacts[]` with an explicit label; all other people remain an A2 responsibility.

## Main sections

| Section | Business meaning | Primary producer | Later consumers |
|---|---|---|---|
| Identity | Who or what the candidate appears to be | A1 | Reviewer, A2, CRM mapping |
| Location | Geographic eligibility and routing context | A1 | Reviewer, territory mapping |
| Public contacts | Professional contact details plainly published by an approved source | A1 when available | A2, later approved workflows |
| Source evidence | URLs, excerpts, dates and reliability supporting claims | A1 | Reviewer, audit, A2 |
| Qualification | ICP criteria, exclusions and minimum-data outcome | A1 | Scoring, reviewer |
| Scoring | Deterministic fit score, component contributions and explanation | Scoring script + A1 explanation | Reviewer, ranking |
| Confidence | Reliability and completeness of evidence | Confidence method | Reviewer |
| Duplicate check | Results by system, including unavailable systems | Script/connectors | Reviewer, Twenty, HubSpot |
| Data quality | Missing fields, conflicts and validation status | Validator | Reviewer, handoff gates |
| Data governance | Collection context and prohibition on A1 outreach | Policy/control layer | All downstream components |
| Recommendation | Proposed next action, not an autonomous action | A1 | Reviewer |
| Workflow | Review and integration state | Reviewer/workflow | A2, n8n, HubSpot sync |
| System references | Stable IDs created later by Twenty, A2 and HubSpot | Connectors/workflows | Reconciliation and audit |
| Provenance | Profile, trigger, model, tools and correlation ID | Runtime/audit layer | Audit and monitoring |

## Important statuses

### Evidence

- `direct_fact`: explicitly visible in the cited source.
- `reasonable_inference`: interpretation supported by evidence but not directly stated.
- `contradictory_evidence`: the source conflicts with another source or candidate claim.

### Duplicate checks

- `unavailable`: no connection or source exists; this is the correct V1 HubSpot/Twenty state.
- `not_checked`: a check could be made but has not run.
- `no_match`: the check ran and no meaningful match was found.
- `possible_match`: human review is required.
- `confirmed_duplicate`: the candidate must not be treated as new.
- `error`: the check failed technically.

### Workflow

The V1 normally stops at `needs_review`. The future integrated path may continue through `approved_for_a2`, A2 review, `approved_for_hubspot`, and `synced`.

## Canonical record and exports

The validated JSON record is the canonical data contract. Markdown, CSV and Excel are derived human-review views. Their exact column mapping and serialisation rules are defined in `export-view.md`; they must not introduce new fields or become an alternative source of truth.

## Twenty Company and Person references

- `system_references.twenty_company_id` is the verified Twenty Company UUID after read-back reconciliation.
- `system_references.twenty_person_id` is the optional verified Twenty Person UUID created or matched for `identity.person`.
- `system_references.twenty_person_relation_status` is `verified`, `not_required`, `unverified`, or null. `verified` requires both IDs and verified Person `companyId` read-back.
- When a Person is present, public professional phone/email values belong to the Person only. When no Person is present, those values may remain on the Company.
- Scoring remains Company/candidate-level; Person availability does not award points or change ranking.

## Version lifecycle

`1.1.0` separates Twenty Company and Person identifiers and records relation status. Later breaking structural changes require a new major version; compatible optional fields require a minor version.

## Confirmed by Séverine

- A1 may retain professional contact details that are publicly displayed and collected while consulting an approved source. The evidence record must preserve where each detail was found. This avoids unnecessary recollection during A2 enrichment.
- One Prospect Candidate may represent a person, an organisation, or a person associated with an organisation.
- A1 may retain one primary named contact, one optional justified secondary named contact and the organisation general contact when they are publicly published on the official site. Contact availability does not alter ICP score or ranking by itself.

## A1 versus A2 boundary

A1 may capture identity, organisation, location, one primary named contact, one optional justified secondary named contact, organisation general contact details, segment, qualification evidence and minimum information needed for review. The primary is stored in `identity.person`; secondary details remain labelled in `public_contacts[]`. A1 must not guess contact data, collect every listed employee or perform paid/deep enrichment by default. A2 owns broader buying-committee and contact enrichment after approval.

## Configurations deliberately kept outside this schema

The following rules change independently and therefore require separate versioned files:

- Farrier and Horse Owner ICP criteria;
- scoring weights and bands;
- pilot geography;
- approved-source register;
- minimum A1 fields;
- retention policy;
- HubSpot property mapping;
- Twenty field mapping;
- territory and owner assignment rules.

## Open decisions for Equinet

1. Final minimum A1 fields for review.
2. Final review stages and reviewer roles.
3. Retention policy version for rejected candidates.
4. Whether a professional Horse Owner below the horse-count threshold may qualify through stronger commercial signals.
5. Final owner and territory outputs once the HubSpot model is supplied.
