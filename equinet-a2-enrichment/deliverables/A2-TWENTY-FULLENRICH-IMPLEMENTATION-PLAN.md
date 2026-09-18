# Equinet A2 — Twenty → FullEnrich → Twenty Implementation Plan

**Document status:** Proposed implementation plan; no integration activation or data write is authorised by this document.  
**Target workflow:** Chat-invoked, LLM-controlled enrichment using Twenty as the operational system of record and FullEnrich as the only enrichment provider for this stage.  
**Out of scope:** Direct A1-to-A2 handoff, HubSpot, official-site research, Apify, other enrichment providers, outreach and sequence enrolment.

## 1. Verified live baseline

### Twenty connectivity and capabilities

Read-only connectivity has been verified against the configured Twenty workspace. Equinet has additionally confirmed that the API key can write, create People, create Company–Person associations and filter Companies by the proposed enrichment status. No webhook or event workflow is required.

The live schema currently contains:

- 40 Companies and 35 People;
- a Company `people` one-to-many relation and Person `company` many-to-one relation;
- 35 Companies with one linked Person and five with none;
- six Companies with a domain URL, confirming that domainless search is required;
- no populated Person job titles or LinkedIn URLs;
- 35 Person records with empty `lastName`, with 34 apparent full names stored in `firstName`.

### New Company fields

- `a2EnrichmentStatus`: `NOT_ENRICHED`, `PROCESSING`, `ENRICHED`, `PARTIALLY_ENRICHED`, `COMPLETED_NO_TARGET`, `RETRYABLE_ERROR`, `BLOCKED`
- `a2EnrichmentVersion`
- `a2EnrichmentRunId`
- `a2ProcessingStartedAt`
- `a2LastAttemptedAt`
- `a2LastEnrichedAt`
- `a2NextRetryAt`
- `a2EnrichmentErrorCode`

### New Person fields

- `a2IdentityStatus`: `VERIFIED`, `AMBIGUOUS`, `CONFLICT`, `NOT_FOUND`
- `a2RoleStatus`: `CURRENT`, `STALE`, `UNKOWN`
- `a2RolePriority`: `PRIMARY`, `SECONDARY`, `REVIEW_ONLY`, `EXCLUDED`, `UNKNOWN`
- `a2CompanyMatchStatus`: `CONFIRMED`, `PROBABLE`, `AMBIGUOUS`, `MISMATCH`
- `a2EnrichmentStatus`: `PENDING`, `ENRICHED`, `PARTIAL`, `NOT_FOUND`, `ERROR`
- `a2FullenrichPersonid`
- `a2LastVerifiedAt`
- `a2LastEnrichedAt`
- `a2EnrichmentRunId`

### Required schema corrections before coding

1. Correct the Person role-status enum value `UNKOWN` to `UNKNOWN`.
2. Prefer renaming the internal field `a2FullenrichPersonid` to `a2FullEnrichPersonId`. If Twenty cannot safely rename it, preserve the live token exactly in the mapping contract and never silently normalise it in API payloads.
3. Decide whether `a2FullEnrichPersonId` should be unique. If it cannot be unique, the connector must query it before every Person creation and enforce uniqueness in the A2 run ledger.
4. All new status fields are currently null. Before the pilot, either backfill eligible Companies to `NOT_ENRICHED`, or make the pull contract treat null and `NOT_ENRICHED` as equivalent. Backfill is preferred after an approved dry run.
5. Confirm whether `Person.emails` is professional-email-only for A2 and whether `Person.phones` may hold a FullEnrich mobile. An incidental personal email must never be automatically written to the generic email field.

## 2. Target operating model

- A1 creates Companies and may create at most one initial linked Person in Twenty.
- A2 retrieves eligible Companies directly from Twenty.
- Twenty is the operational system of record for Companies, People and their relationships.
- FullEnrich is the sole enrichment provider for current professional profile and contact information during this stage.
- The chat LLM controls decisions. Scripts perform deterministic transport, polling, normalisation, validation, persistence and approved writes.
- A2 may add up to two newly selected target People when a Company has no fresh verified primary contact. Search progresses through primary, generic Owner, verified linked-secondary reuse, then paid secondary roles; a secondary selection records `SECONDARY` priority.
- Existing non-primary, stale or unresolved People remain linked and receive explicit statuses.
- No A1 qualification, score, confidence, discovery or lifecycle field is changed by A2.
- Every Twenty write is followed by read-back reconciliation.

## 3. Skill architecture

### 3.1 `a2-twenty-fullenrich-enrichment-workflow`

Master skill. It defines the ordered stages, required receipts, stop rules and LLM decision checkpoints. It does not contain provider credentials or mutable role catalogues.

Supporting script:

- `scripts/manage_a2_enrichment_run.py`: creates/resumes a run, records checkpoints, validates artifact hashes and produces compact run summaries. It must not decide role priority or Person selection.

### 3.2 `a2-twenty-connector`

Responsibilities: retrieve, claim, create, update, associate and reconcile Twenty records.

Scripts:

- `scripts/pull_twenty_companies.py`
  - validates environment and live metadata;
  - filters null/`NOT_ENRICHED`, due `RETRYABLE_ERROR`, or older enrichment versions;
  - paginates and applies a configured batch limit;
  - retrieves all linked People;
  - optionally claims records by writing `PROCESSING`, run ID and processing timestamp;
  - writes raw and normalised snapshots.

- `scripts/push_twenty_enrichment.py`
  - subcommands: `claim`, `apply`, `reconcile`;
  - accepts only a validated write plan;
  - creates/updates People and Company–Person associations;
  - writes Person and Company A2 statuses;
  - reads back affected objects and relationships;
  - emits operation-level receipts and reconciliation results.

### 3.3 `a2-fullenrich-connector`

Responsibilities: execute FullEnrich calls, protect credentials, poll asynchronous jobs and produce field-minimised responses.

Scripts:

- `scripts/fullenrich_people_lookup.py`
- `scripts/fullenrich_people_search.py`
- `scripts/fullenrich_contact_enrichment.py`

All scripts accept arrays, use bounded concurrency, store raw restricted responses separately, return one result per request and never write to Twenty.

### 3.4 `a2-contact-resolution-and-selection`

LLM decisioning instructions plus deterministic packet builders and validators.

Scripts:

- `scripts/build_lookup_decision_packet.py`
- `scripts/validate_lookup_decisions.py`
- `scripts/build_search_candidate_packet.py`
- `scripts/validate_person_selection_decisions.py`

The LLM decides identity, current-company match, role priority, freshness, Search necessity and retention. Validators enforce source IDs, approved enums, evidence references, maximum-two selection and non-invention.

### 3.5 `a2-twenty-write-governance`

Responsibilities: field ownership, conflict handling, explicit write plans and reconciliation.

Scripts:

- `scripts/build_twenty_enrichment_write_plan.py`
- `scripts/validate_twenty_enrichment_write_plan.py`
- `scripts/validate_twenty_reconciliation.py`

### 3.6 `a2-enrichment-exception-review`

Optional but recommended for ambiguous Company matches, conflicting populated values, incidental personal email, provider-policy blocks and failed reconciliation. Routine successful runs do not require an extra review object.

## 4. Versioned data contracts

Create strict JSON Schemas for these boundaries:

1. common artifact envelope;
2. Twenty metadata snapshot and field mapping;
3. Twenty pull request and Company/People batch;
4. Company claim request and receipt;
5. FullEnrich Lookup request/result;
6. Lookup decision packet and LLM decision;
7. FullEnrich Search request/result;
8. Search candidate packet and Person selection decision;
9. selected-contact batch;
10. Contact Enrichment request, async job and terminal result;
11. Person field-merge decisions;
12. Company and Person status state models;
13. Twenty write plan;
14. Twenty operation receipt;
15. post-write snapshot and reconciliation;
16. run ledger, audit and consumption record;
17. exception-review record.

Every artifact must include schema version, run ID, Company ID where applicable, UTC timestamp, policy versions, input hash, idempotency key, status, errors, warnings and output hash.

## 5. Field mapping and ownership

### A2-read-only Company fields

Treat A1 fields as protected, including `discoveryStatus`, `discoverySourceNotes`, `discoveryFingerprint`, `qualificationStatus`, `icpScoreStatus`, `icpScore`, `icpBand`, `icpOutcome`, `evidenceConfidenceScore` and `evidenceConfidenceLevel`.

### Company values used by A2

- `id`, `name`, `segment`;
- `domainName` when populated;
- structured `address`, with custom city/state/country as supporting values;
- `linkedinLink` and `sourceUrl` when available;
- Company–People relation;
- A2 control fields.

### Person mapping

- source full name → `name`;
- exact FullEnrich source title → `jobTitle`;
- verified professional email → `emails` only after professional-email semantics are confirmed;
- FullEnrich mobile/direct phone → `phones` only after mobile semantics are approved;
- professional-network URL → `linkedinLink`;
- FullEnrich Person ID and A2 statuses → new A2 fields.

### Write rules

- Fill empty fields when evidence and identity are valid.
- Same normalised value produces no change.
- Do not silently overwrite a different populated manual value.
- Existing non-primary/stale People remain linked.
- Never mutate an existing Person into a different person.
- Before creating a Person, deduplicate by FullEnrich ID, LinkedIn URL, work email, normalised name plus Company and supporting phone.
- At most two new selected target People may be created/linked per Company across the complete staged Search sequence.
- Personal email is not requested. If incidentally returned, retain it in a restricted audit/exception artifact and do not automatically write it to Twenty.

## 6. End-to-end runtime workflow

### Stage 0 — Chat invocation and preflight

The user invokes the master skill with a requested batch size or the default approved batch limit. The LLM:

1. resolves the active manifest and contract hashes;
2. verifies Twenty and FullEnrich environment variables without printing secrets;
3. verifies read/write integration gates, provider credit policy and run limits;
4. creates a run ID and run directory;
5. starts an immutable audit record.

Stop on missing credentials, policy versions, budget approval or live metadata mismatch.

### Stage 1 — Pull and claim Companies

1. Pull Companies where status is null/`NOT_ENRICHED`, or due for approved retry/version refresh.
2. Retrieve every linked Person.
3. Preserve raw Twenty responses and create a normalised snapshot.
4. Claim each Company by transitioning it to `PROCESSING`, setting run ID, `a2ProcessingStartedAt` and `a2LastAttemptedAt`.
5. Read back every claim. Only successfully claimed Companies proceed.

No provider call occurs before a verified claim.

### Stage 2 — Existing-Person Lookup

For each linked Person that is not already fresh and verified under the active policy:

1. build a Lookup request using the strongest available identifiers;
2. normalise the malformed legacy Twenty name structure without rewriting it;
3. run Lookups concurrently within approved limits;
4. preserve exact FullEnrich role and current-organisation wording;
5. build compact Lookup decision packets.

### Stage 3 — LLM Lookup decisions

For every existing Person, the LLM decides:

- identity: verified, ambiguous, conflict or not found;
- Company match: confirmed, probable, ambiguous or mismatch;
- role priority using the approved segment-specific target-role model;
- role freshness: current, stale or unknown;
- whether the Person is retained as a target contact.

At Company level, the LLM decides whether Search is required. Search is required when no fresh verified primary contact remains. All decisions are strict JSON and must pass the validator before Search or contact enrichment. Search then progresses one validated stage at a time: approved primary titles excluding generic `Owner`; exact `Owner`; verified A1-linked secondary reuse with zero provider Search calls; approved paid secondary Search only if no linked fallback is selected; `completed_no_target`. A later stage is permitted only when the prior stage completed without a retained candidate.

### Stage 4 — FullEnrich People Search

For Companies requiring Search:

1. use exact domain when available;
2. otherwise use the strongest FullEnrich-supported combination of Company name, structured location, professional-network URL or provider organisation identifier;
3. always include the role constraints for the active stage: primary, exact generic Owner, or secondary;
4. prohibit broad role-free and cross-organisation search;
5. return a bounded candidate set sufficient to select up to two People;
6. store raw provider results and build field-minimised candidate packets.

Domain absence is a warning, not a blocker. If the live FullEnrich API cannot support a meaningful domainless request, record `insufficient_company_identity` and route to `BLOCKED` rather than inventing a match.

### Stage 5 — LLM Person selection

The LLM assesses each Search candidate for:

- identity;
- current Company match;
- exact current role and approved primary classification;
- duplication against linked or existing Twenty People;
- retention.

It selects zero, one or two stage-appropriate candidates and records reasons for every rejection. The validator rejects unknown candidate IDs, more than two selected candidates, Company mismatches, unsupported classifications, PRIMARY selections outside the primary/owner stages, and SECONDARY selections outside the secondary stage.

### Stage 6 — Contact Enrichment

Aggregate selected existing and newly found People into bounded bulk requests. Request exactly:

- `contact.work_emails`;
- `contact.phones`.

The Contact Enrichment script submits, polls internally until a terminal state or approved timeout, performs at most one retry for a transient technical failure and returns individual outcomes. It never requests personal email.

### Stage 7 — LLM field and status decisions

For each Person, the LLM compares Twenty baseline values with validated FullEnrich values and returns only:

- `add`;
- `update_a2_owned`;
- `no_change`;
- `preserve_manual`;
- `hold_conflict`;
- `privacy_review`;
- `reject_invalid`.

The write-plan builder copies values from validated provider artifacts; it does not accept free-form values invented by the LLM.

### Stage 8 — Twenty apply and reconcile

1. Update statuses on existing People.
2. Match or create selected new People.
3. Add Company–Person associations.
4. Apply approved empty-field/A2-owned updates.
5. Read back every affected Person and relation.
6. Reconcile exact intended and observed values.
7. Update Company status only after Person and association reconciliation.

### Stage 9 — Final state

- `ENRICHED`: at least one current verified selected target Person is linked; applicable contact-enrichment actions reached terminal states; intended writes reconciled.
- `PARTIALLY_ENRICHED`: a selected target Person is linked but a retryable/partial contact or write outcome remains.
- `COMPLETED_NO_TARGET`: primary and generic Owner Search, linked-secondary resolution, and paid secondary Search completed successfully with no acceptable retained target.
- `RETRYABLE_ERROR`: approved transient provider or Twenty failure; set `a2NextRetryAt`.
- `BLOCKED`: identity ambiguity, policy/budget/authentication failure, protected-field conflict or unreconciled write requiring intervention.

Clear processing ownership only after a terminal status is read back. Preserve run ID and timestamps for audit.

## 7. Multi-Company execution model

The chat remains the reasoning controller. Scripts perform concurrent external I/O in batches.

1. Pull and claim a bounded Company batch.
2. Run all required Lookups concurrently.
3. Present one compact Lookup decision packet to the LLM.
4. Run Searches concurrently only for approved Companies.
5. Present one compact selection packet to the LLM.
6. Bulk-enrich selected People.
7. Present compact field-conflict packets to the LLM.
8. Apply and reconcile writes per Company with bounded concurrency.

Raw responses remain in restricted run artifacts; only necessary decision fields enter model context. Split packets by configured item/byte limits. One Company failure must not abort the rest of the batch.

## 8. Idempotency, resume and locking

Idempotency keys include active policy version, Twenty Company ID, Twenty/FullEnrich Person ID, operation type and normalised input hash.

The run ledger records these checkpoints:

- pulled;
- claimed;
- lookup complete;
- Lookup decisions validated;
- Search complete;
- selection decisions validated;
- Contact Enrichment complete;
- write plan validated;
- Twenty written;
- reconciled;
- terminal.

A later invocation may resume from the last validated checkpoint. Successful FullEnrich results are reused. Duplicate Twenty creates or associations are prohibited. A stale `PROCESSING` claim may be reclaimed only after the approved lock timeout and verification that the prior run is no longer active.

## 9. Error, retry and budget policy

- Authentication, policy, budget and invalid-input failures: no retry; Company becomes `BLOCKED`.
- Provider `not_found`: no retry in the same run.
- Approved transient technical failure: maximum one retry.
- Twenty write failure: do not repeat the complete write set blindly; read back first and resume only missing operations.
- Reconciliation mismatch: `BLOCKED` or `PARTIALLY_ENRICHED`, depending on whether a safe retry exists.
- Record credits before, used and after for every FullEnrich action.
- Enforce per-run, daily and pilot caps before live provider activation.

## 10. Security and privacy

- Credentials remain in environment/approved secret storage and are never logged.
- Raw FullEnrich responses have restricted retention and access.
- Normal outputs discard education, skills, employment history, descriptions and connection counts.
- Personal email is never requested and is never automatically written.
- Contact data does not create consent, outreach eligibility or sequence authority.
- Logs use IDs and redacted values where full values are unnecessary.

## 11. Implementation phases

### Phase 1 — Foundation amendment

- Resolve the current active-manifest version discrepancy before activation.
- Record the approved architecture change.
- Remove A1 handoff, HubSpot, official-site and Apify dependencies from the active runtime path.
- Publish the new Twenty mapping, source register, provider policy, role/contact policy, status model and runtime manifest.
- Mark the redesigned workflow integration-pending until acceptance completes.

### Phase 2 — Schema and contract package

- Correct live Twenty field issues listed in Section 1.
- Snapshot and hash live Twenty metadata.
- Implement all JSON Schemas from Section 4.
- Implement cross-field validators and golden fixtures.
- Validate actual FullEnrich domainless Search and polling parameters against the live provider account/docs.

### Phase 3 — Twenty connector

- Implement metadata preflight, pull, filtering, pagination, claiming and normalisation.
- Implement apply/reconcile subcommands.
- Add dry-run and fixture modes.
- Validate create, update, association, status filtering and read-back in a dedicated synthetic record.

### Phase 4 — FullEnrich connector

- Implement key verification and credit preflight.
- Implement Lookup and Search batch wrappers.
- Implement Contact Enrichment submit/poll/timeout logic.
- Implement minimisation, retries, cost receipts and restricted raw storage.

### Phase 5 — Decisioning and governance

- Repurpose the existing role classifier for the active primary-role model.
- Implement decision packet builders and strict decision validators.
- Implement Company matching, legacy name normalisation and deduplication.
- Implement field ownership, write-plan and reconciliation validators.

### Phase 6 — Master skill and run management

- Create the master skill and run-state helper.
- Implement bounded packet sizes, checkpointing, resume and per-Company isolation.
- Add concise chat summaries and exception outputs.

### Phase 7 — Synthetic acceptance

Run deterministic fixtures without live writes or provider spend. All tests must preserve zero external actions.

### Phase 8 — Integration acceptance

Use dedicated synthetic Twenty records and an approved FullEnrich test allocation. Verify external receipts and read-back after every action.

### Phase 9 — Controlled live pilot

- Backfill or filter null Company statuses as approved.
- Select a small business-approved batch.
- Run in dry-run mode and review proposed actions.
- Enable writes for the same batch only after dry-run acceptance.
- Review duplicates, costs, errors, field conflicts and reconciliation.
- Increase batch size only after explicit pilot acceptance.

## 12. Required acceptance scenarios

1. Company without Person; primary Search finds an approved target.
2. Company without Person; Search finds one.
3. Company without Person; Search finds none.
4. Existing Person is current primary; Lookup and Contact Enrichment update permitted gaps.
5. Existing Person is non-primary; preserve it, then run primary → Owner → linked-secondary reuse → paid secondary fallback and retain only a stage-valid target.
6. Existing Person is stale or at a different Company; preserve/status it and Search.
7. Domainless Company resolves using name/location.
8. Domainless Search is ambiguous and creates no association.
9. Search candidate duplicates an existing Twenty Person.
10. A rerun creates no duplicate Person or association.
11. Contact Enrichment returns email only, phone only, neither and both.
12. Incidental personal email is isolated and not written.
13. Existing manual email/phone/LinkedIn conflict is preserved.
14. One of two selected People fails enrichment without aborting the other.
15. FullEnrich asynchronous job times out.
16. Provider rate limit and one approved retry.
17. Twenty write partially succeeds; read-back prevents duplicate replay.
18. Twenty API success with read-back mismatch.
19. Stale processing lock is safely resumed.
20. Company status/version filter selects exactly eligible records.
21. A1 score and qualification fields remain unchanged.
22. Multiple Companies are processed with bounded concurrency and isolated outcomes.

## 13. Definition of done

The workflow is implementation-complete only when:

- every active contract is versioned, hashed and referenced by the new manifest;
- the Twenty live metadata snapshot matches the mapping contract;
- the corrected status enums and provider-ID field are verified;
- FullEnrich domainless Search and Contact polling are demonstrated with real receipts;
- all synthetic and integration scenarios pass;
- dry-run and write-enabled paths produce identical semantic write plans;
- every Twenty write has successful read-back reconciliation;
- reruns are idempotent;
- no A1-owned field, HubSpot record or outreach system is modified;
- provider costs and retries are auditable;
- a controlled live batch is accepted by the named Equinet/Unitalk business reviewer;
- the profile status is updated only after the new architecture receives explicit pilot acceptance.

## 14. Immediate next actions

1. Correct `UNKOWN` and decide the final FullEnrich Person-ID internal field name/uniqueness.
2. Approve the professional-email and mobile-phone mapping semantics.
3. Confirm the active manifest baseline and authorise the foundation amendment.
4. Capture live FullEnrich request/response samples, domainless Search support and polling endpoint semantics.
5. Build and approve the schema/fixture package before connector code.
6. Implement the Twenty connector first, then FullEnrich, decision validation and orchestration.
