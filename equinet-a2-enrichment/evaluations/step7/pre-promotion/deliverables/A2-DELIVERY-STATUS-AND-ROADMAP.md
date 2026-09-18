# Equinet A2 Enrichment — Delivery Status and Ordered Roadmap

**Version:** `1.2.9`  
**Updated:** `2026-08-29T21:26:43Z`  
**Profile:** `equinet-a2-enrichment`  
**Current status:** `FOUNDATION CONFIGURED — NOT PILOT-READY`  
**Next delivery gate:** `Step 7 — synthetic acceptance review and approval`

## 1. Completed and approved foundation work

- **Profile shell — COMPLETED**
  - Isolated profile `equinet-a2-enrichment` created.
  - No cloned A1 identity, memory, broad skills or integrations.
  - Temporary English safety SOUL installed.
  - Live enrichment, CRM access, paid providers, outreach and downstream delivery prohibited.

- **Step 1B: A2 Implementation Contract — COMPLETED / APPROVED FOR FOUNDATION**
  - Current version: `0.1.4`.
  - Mission, scope, users, systems of truth, actions, approval boundaries, audit, errors and integration status defined.
  - A1 scoring ownership and A2-triggered requalification clarified.
  - HubSpot metadata, operational-model and governance confirmations incorporated.
  - No live action authorised.

- **Step 1C: A1-to-A2 Boundary and Handoff Contract — COMPLETED / APPROVED**
  - Contract and JSON Schema version: `1.0.1`.
  - Full immutable A1 candidate snapshot and deterministic integrity hash defined.
  - Approval, eligibility, hold, block, delivery and receipt states defined.
  - Manual no-integration handoff capped at `ready_for_delivery`.
  - A1 score/evidence/approval kept immutable.
  - Requalification signal/return boundary defined.
  - Two valid fixtures and nine negative fixtures created.
  - Deterministic suite: `11/11 PASS`.

- **Step 2A: Canonical Record Design and Field Ownership — COMPLETED / APPROVED**
  - Design version: `0.1.0`.
  - One A2 record lineage per accepted A1 handoff version.
  - Immutable record revisions and append-only evidence/approval/audit history approved.
  - Fourteen canonical sections and ownership boundaries defined.
  - Generic `field_assessments[]` structure approved.
  - Baseline, observations, proposed resolution, human decision and application states separated.
  - A2 evidence namespace and A1 evidence references separated.
  - Field-level and record-level review approved.
  - Nullable connector-controlled external references approved.

- **Step 2B: Field Dictionary and State Model — COMPLETED / APPROVED**
  - Structural dictionary version: `0.1.0`.
  - 216 unique structural paths across all 14 canonical sections.
  - 37 orthogonal state vocabularies and 16 workflow states.
  - Nine negative regressions passed.

- **Step 2C: Requalification and Score-Revision Data Contract — COMPLETED / APPROVED**
  - Contract version: `0.1.1`; four strict schemas remain `0.1.0`.
  - A2 signal, return, A1 score-revision reference and package defined.
  - A2 numeric score production prohibited; A1 remains the deterministic score owner.
  - Fifteen positive and negative cases passed.

- **Step 2D: Canonical A2 JSON Schema — COMPLETED / APPROVED FOR STEP 2E**
  - Approved baseline schema: `1.0.0-draft.1`.
  - All 14 canonical sections required.
  - Every locally defined structural object is strict.
  - Eight dependency hashes and 39 state-vocabulary bindings passed.
  - Seven structural smoke cases passed.
  - Business field catalogue and CRM mappings remain external.
  - Draft.2 correction for relationship-scoped assessment targets was approved through Step 2E decision E13.

## 2. Completed supporting discovery and intake work

- **HubSpot object/property intake — COMPLETED / NO CONNECTION**
  - Data-model image and 950 property definitions parsed.
  - Company, Contact, Deal, Ticket, Complaints and Sample Requests metadata inventoried.
  - Relevant Contact/Company/Deal mapping candidates identified.
  - Read-only, enum and unique-lookup metadata analysed.
  - Horse-count range overlap, duplicate labels and sensitive out-of-scope fields flagged.

- **HubSpot operational metadata intake — COMPLETED / NO CONNECTION**
  - Lifecycle stages, Deal pipeline, custom-object pipelines and status models documented.
  - Users, teams, owners and territories documented.
  - 68 Sales/Marketing process assets analysed: 33 workflows, 32 lists and 3 audit findings.
  - 28 enabled workflows and possible communication/task/status/record side effects identified.
  - No current HubSpot enrichment-review asset found.
  - No owner-assignment or backup-owner rules found.
  - Hard block added for future writes until workflow dependencies are verified.

- **HubSpot object and governance confirmations — COMPLETED**
  - Creator absent.
  - Campaign confirmed as a standard HubSpot object.
  - Complaints and Sample Requests confirmed as custom objects.
  - Super Admins, CRM/business owners, configuration approvers and OAuth approvers recorded.
  - OAuth still ungranted and unconnected.
  - A2 business reviewer and backup remain unconfirmed.

- **Source and field decision pack — DRAFTED / NOT ACTIVATED**
  - Recommended source hierarchy documented.
  - A1-versus-A2 collection boundary clarified.
  - A2 must reuse A1 data and run field-level gap analysis before new research.
  - Detailed 28-row Unitalk working matrix retained internally.
  - Slim 12-row Equinet decision template created.
  - Horse-count range question clarified: no new HubSpot property by default; A2-only category for pilot review.

- **LinkedIn and Apify feasibility — REVIEWED / AUTOMATION BLOCKED**
  - HarvestAPI Company Employees, Profile Search and Profile Scraper Actors reviewed.
  - Technical capability confirmed.
  - LinkedIn terms and Apify Community Actor governance reviewed.
  - Automated use remains `blocked_pending_rights_and_vendor_review`.
  - Recommended pilot route: official site plus authorised human manual LinkedIn role verification.

- **Language and package controls — ACTIVE**
  - Stored A2 profile artifacts are English.
  - French is reserved for implementation conversations with Séverine.
  - Latest language audit passed with zero findings.

## 3. Equinet decisions to collect in parallel

### Required before finalising the business field catalogue

- Confirm target Farrier job roles and priority: Primary, Secondary or Exclude.
- Confirm target Horse Owner organisation job roles and priority.
- Confirm maximum named contacts per prospect and fallback when no target role is found.
- Confirm minimum contactability for A2 review readiness.
- Confirm the horse-count range approach and non-overlapping categories.

### Required before the no-integration pilot

- Confirm personal email and mobile/direct-dial policy.
- Confirm Required, Optional and Do Not Collect Farrier fields.
- Confirm Required, Optional and Do Not Collect Horse Owner fields.
- Confirm manual LinkedIn/social-profile policy.
- Name the A2 business reviewer and backup.
- Approve field-level exceptions for protected data.

### Required before a paid provider test

- Confirm permitted paid lookup types.
- Name the provider and budget approver.
- Approve provider/account/data route and hard credit cap.
- Approve privacy, retention and data-processing route.

### Required before go-live

- Approve owner and territory assignment and backup rules.
- Approve consent, suppression, customer, Deal and sequence eligibility mapping.
- Approve A2-to-HubSpot mapping and protected-field exceptions.
- Confirm Equinet-versus-Mustad business-unit access boundary.
- Approve retention, deletion and administrator-visibility rules.

## 4. Remaining delivery work in required order

### Step 2B — Field Dictionary and State Model — COMPLETED / APPROVED

- Define every canonical structural field.
- Define data types, ownership, mutability and required/nullable rules.
- Define exact state vocabularies for:
  - unknown, not checked, unavailable, not found and error;
  - proposed, verified, partial, gap, conflict and stale;
  - field review and record review;
  - application/sync;
  - requalification and score revisions;
  - duplicate and eligibility checks;
  - `needs_owner_review` and `workflow_dependency_unverified`.
- Add HubSpot status models as external references without making them canonical A2 states.
- Obtain Séverine review and approval.

### Step 2C — Requalification and Score-Revision Data Contract — COMPLETED / APPROVED

- Define exact `requalification_signal` fields.
- Define `requalification_return` payload and states.
- Define A1 score-revision references and lineage.
- Ensure A2 cannot award points or calculate the revised score.
- Add human-review and audit requirements.

### Step 2D — Canonical A2 JSON Schema — COMPLETED / APPROVED FOR STEP 2E

- Strict `a2-enrichment-record.schema.json` created and compiled.
- `additionalProperties: false` applied to all locally defined structural objects.
- Nullable future HubSpot/Twenty/n8n/provider references included.
- Mutable field catalogue, source policy and CRM mapping kept outside the schema.
- Baseline `1.0.0-draft.1` was approved for Step 2E. Corrective `1.0.0-draft.2` is included in the Step 2E review; final promotion remains Step 2I.

### Step 2E — Deterministic Cross-Field Validator — COMPLETED / APPROVED FOR STEP 2F

- Validator version `0.1.0` implemented with schema-first fail-closed behaviour.
- Handoff, evidence, entity, relationship, revision, review, application and audit references validated.
- A1 scoring checks reused; A2-calculated score revisions rejected.
- Synthetic/production separation and no-integration ceilings enforced.
- Prior revision required after revision 1; lifecycle transitions and append-only history validated.
- Optional external Field Catalogue key/type checks implemented without embedding the catalogue.
- Corrective schema `1.0.0-draft.2` and Step 2C lifecycle clarification `0.1.1` approved through E13.
- Deterministic suite approved after `59/59 PASS`.

### Step 2F — Fixtures and Regression Tests — COMPLETED / APPROVED FOR STEP 2G

- Sixteen valid Farrier and Horse Owner business scenarios created.
- Gap, conflict, possible duplicate, confirmed duplicate, protected-field and complete requalification paths included.
- Thirteen negative safety and integrity scenarios created with exact expected error counts.
- Scenario-specific business assertions and fixture hashes enforced.
- All fixture records are synthetic and contain zero recorded external-action claims.
- Step 2F suite approved after `29/29 PASS`.

### Step 2G — Handoff-to-Record Initialisation — COMPLETED / APPROVED FOR STEP 2H

- Initialiser CLI version `0.1.0` implemented.
- Complete A1 handoff validation and lossless snapshot preservation enforced.
- Stable A2 lineage/revision/run IDs derived from the complete handoff hash.
- Empty A2 evidence, assessment and requalification containers initialised.
- Integrations unavailable, review pending and every external action disabled.
- Three valid, eight invalid and fifteen deterministic/idempotency controls pass.
- Positive manual no-integration case remains pending an approved real production handoff.
- Step 2G suite approved after `11/11` fixtures and `15/15` controls PASS.

### Step 2H — Review-View Specification — COMPLETED / APPROVED FOR STEP 2I

- Read-only review-view specification `0.1.0` created.
- Markdown, six CSV files and seven-sheet Excel package defined and rendered.
- Current/proposed values, observations, evidence, confidence, freshness, gaps, conflicts, protection and requalification are visible.
- Six representative packages and eleven negative checks pass.
- Canonical JSON remains the sole lossless source; projections contain no reviewer input, formula or external action.
- Step 2H approved after `6/6` sample packages and `11/11` negative checks PASS, including the post-approval carriage-return regression.

### Step 2I — Canonical Data Contract Review and Promotion — COMPLETED / APPROVED

- Six representative synthetic canonical records reviewed and validated.
- Séverine approved decisions I1–I10 on `2026-08-26T15:15:50Z`.
- Schema and active dependent artifacts promoted atomically to `1.0.0`.
- Pre-promotion evidence preserved by hash.
- Step 2D–2H regressions and language audit rerun after promotion.

### Step 3A — Business Field Catalogue — UNITALK BASELINE APPROVED / EQUINET CONFIRMATION PENDING

- Active Unitalk proposal `0.1.1-draft.1` contains 33 business fields after the approved SOC-1 through SOC-8 clarification.
- `person.public_profile_urls` and `organisation.public_profile_urls` are separate optional fields.
- Proposed Farrier and Horse Owner target-role models included.
- Proposed field priorities use Required, Conditional Required, Optional and Do Not Collect.
- Proposed contact limit, general-contact fallback and review contactability included.
- Proposed verified exact horse count and non-overlapping A2-only review bands included.
- Séverine approved decisions 3A-1 through 3A-8 as the Unitalk working baseline.
- A missing Required field creates a visible gap and an incomplete record; it does not automatically reject the prospect or change the A1 score.
- Equinet business confirmation remains pending before final promotion to `0.1.0`.

### Step 3B — Minimum Data Packages — UNITALK BASELINE APPROVED / EQUINET CONFIRMATION PENDING

- Farrier review-ready package defined with five verified core fields and two alternative contact paths.
- Horse Owner review-ready package defined with three verified core fields and the same contact-path structure.
- Named-target and organisation-general fallback paths are kept distinct.
- Missing Required fields produce a visible gap and incomplete record without automatic rejection or A1 score change.
- Material conflicts produce `needs_review` with a `held` workflow recommendation.
- Outreach readiness remains separate and unavailable pending authoritative HubSpot checks.
- Human review remains mandatory during the pilot.
- Séverine approved decisions 3B-1 through 3B-7 as the Unitalk working baseline.
- Equinet confirmation remains pending before final promotion.

### Step 3C — A2 Source Register — UNITALK BASELINE APPROVED / RUNTIME ACTIVATION PENDING

- Eleven source or access categories recorded.
- Official-site check recorded as Equinet business-approved for every candidate when a site exists.
- Website access bounded to five relevant pages, one targeted retry and explicit stop conditions.
- `harvestapi/linkedin-profile-search` recorded as Equinet business-approved for A2.
- Actor profile output restricted to minimum role/company/location/profile fields; email results are governed as a separate provider action.
- Actor runs only after an official-site role/contact gap.
- Independent professional-email search is approved as a separately governed Actor action; personal-email retention remains disabled by default.
- Actor output field allowlist will be reviewed after a bounded sample.
- Search-engine discovery is approved only to locate an official website; snippets are not evidence.
- No additional A2 registry or association is selected beyond A1 evidence reuse.
- Actor runtime remains blocked pending LinkedIn rights, HarvestAPI vendor review, account, build, budget, retention and connector controls.
- Apollo, Clay and other paid enrichment providers remain unselected and unconnected.
- A1 directory evidence is reuse-only; no default A2 recrawl.
- Séverine approved the Step 3C register as the Unitalk working baseline.

### Step 3D — Evidence, Verification, Confidence and Freshness Policies — UNITALK BASELINE APPROVED / EQUINET CONFIRMATION PENDING

- Six deterministic confidence dimensions defined with a 100-point total.
- High, Medium and Low confidence bands proposed.
- Verification, partial-verification, conflict and blocked-source rules defined.
- Official-site, A1 evidence, HubSpot, Apify profile, Apify email and search-discovery treatments separated.
- Field-specific freshness windows proposed.
- Material-conflict, unresolved-identity, inference-only, stale and source-gate caps implemented.
- Ten positive/edge fixtures and ten negative regressions implemented.
- Séverine approved decisions 3D-1 through 3D-10 as the Unitalk working baseline.
- Protected SOUL synchronisation completed after Séverine's explicit authorisation.
- Equinet confirmation of freshness windows, relevant activity types and personal-email policy remains pending.

### Step 3E — Protected Fields and Conflict Policy — UNITALK BASELINE APPROVED / EQUINET CONFIRMATION PENDING

- Thirty-two confirmed HubSpot protected-field candidates recorded by object and internal property name.
- Authoritative controls, system-read-only fields, owner/routing fields, manual values and A2 proposal fields separated.
- Preserve, propose, hold, block, reject and requalification outcomes defined.
- Field-level exception requirements defined.
- All writes remain blocked while the 28 enabled workflows and 32 lists lack exact dependency verification.
- Ten deterministic outcomes and eight negative regressions implemented.
- Séverine approved decisions 3E-1 through 3E-10 as the Unitalk working baseline.
- Equinet action-level approvers, exceptions and workflow dependencies remain pending.
- Protected SOUL synchronisation completed after Séverine's explicit authorisation.


### Step 3F — Provider and Cost Policy — UNITALK BASELINE APPROVED / RUNTIME ACTIVATION PENDING

- Current provider scope limited to Apify profile search and its separately governed email-search action.
- Apollo, Clay and other providers remain unselected pending Equinet tests.
- Ten-candidate benchmark design recorded.
- Per-candidate Actor limits inherited from Step 3C.
- Cost caps, spend approver, consumption owner and retention remain pending; runtime is therefore blocked.
- Idempotency, retry, no-fallback, audit and prepaid-balance controls defined.
- Personal emails are held for human privacy review and cannot be used operationally before approval.
- Five authorization scenarios and eleven negative regressions implemented.
- Séverine approved decisions 3F-1 through 3F-10 as the Unitalk working baseline.
- Budget, spend approver, consumption owner, account, rights, vendor and retention inputs remain pending.
- Protected SOUL synchronisation completed after Séverine's explicit authorisation.

### Step 3G — Preliminary A2-to-HubSpot Mapping — UNITALK BASELINE APPROVED / LIVE VERIFICATION PENDING

- All 32 canonical business fields inventoried.
- Twenty-two fields have at least one exact HubSpot metadata candidate.
- Every destination property was verified against the supplied property export.
- All mapped fields remain read-and-propose only with write authority false.
- Personal-email candidates remain canonical review-only with no HubSpot mapping.
- Horse-count range and stable-type mappings remain blocked by taxonomy mismatches.
- Workflow dependencies remain unverified for every mapped field.
- Ten negative regressions implemented.
- Séverine approved decisions 3G-1 through 3G-10 as the Unitalk working baseline.
- Live HubSpot values, associations, permissions and workflow effects remain pending.
- Protected SOUL synchronisation completed after Séverine approved the retry.

### Step 3H — Twenty Review Layer Contract and Mapping — UNITALK BASELINE APPROVED / INTEGRATION PENDING

- A1 prospect retained as the main Twenty record.
- Linked versioned A2 Enrichment Review logical object proposed.
- Linked field-decision object or equivalent structured field proposed.
- Pending, in-review, changes-requested, held, approved and rejected states defined.
- Field-level corrections and record-level decisions supported.
- Approved Twenty review authorises only proposed HubSpot patch preparation, never HubSpot write.
- Strict review-receipt schema created.
- Four valid and eight invalid receipt paths pass deterministically.
- Twenty workspace metadata, exact objects/fields, API key, permissions and webhooks remain pending.
- Séverine approved decisions 3H-1 through 3H-10 as the Unitalk working baseline.
- Protected SOUL synchronisation completed after Séverine's explicit authorisation.

### Step 4 — Final Specialist SOUL — COMPLETED / APPROVED AND ACTIVE

- Proposed final specialist identity created separately from the active temporary scaffold.
- Complete A1 → Twenty → A2 → Twenty review → proposed HubSpot patch workflow defined.
- Versioned foundation contracts referenced without embedding mutable catalogues.
- Source, evidence, scoring, personal-email, protected-field, cost and action boundaries included.
- Integration states remain explicit and unavailable actions remain disabled.
- Static checks, dependency hashes and negative regressions pass.
- Active `SOUL.md` replacement was approved by Séverine and completed on `2026-08-27T11:02:47Z`.


### Foundation clarification — Official-Site Social Profile URL Capture — COMPLETED / APPROVED

- Séverine approved SOC-1 through SOC-8.
- Explicit professional social-profile URLs published on approved official-site pages may be retained without opening or extracting the linked social profile.
- Person and organisation URLs are separated; ambiguous attribution is held for review.
- LinkedIn, Facebook, Instagram, YouTube and other clearly professional profile links are optional enrichment fields.
- An exact LinkedIn company URL is the preferred future input for `harvestapi/linkedin-profile-search`; verified company name plus target role is the fallback.
- An individual LinkedIn profile URL is reserved for human review or a separately approved profile-scraper route.
- Broad social signals, automated social extraction, consent inference, outreach eligibility and buying-influence inference remain prohibited.
- Active versions are resolved through `foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json`; Step 3 builders pinned to `0.1.0-draft.1` are historical reproduction tools only.
- Apify runtime remains blocked and no external action was authorised.

### Step 5A — Operational Skill Architecture and Runtime Manifest — COMPLETED / APPROVED

- Ten skill packages defined across three dependency waves: `3 + 3 + 4`.
- Fourteen skill-owned operator commands defined: four existing reusable entrypoints and ten commands to build or wrap.
- One profile-level no-integration orchestrator is planned after Wave 3 and is not counted as a skill-owned command.
- Active Equinet configuration remains external to skills and is resolved through the Active Foundation Manifest.
- Step 5 keeps Web, Apify, Twenty, HubSpot, n8n, outreach and external writes disabled.
- Static validation and ten negative architecture regressions pass.
- Séverine approved decisions 5A-1 through 5A-10 on `2026-08-27T12:10:52Z`; Wave 1 construction is authorised.

### Step 5B — Wave 1 Intake and Identity — COMPLETED / APPROVED

- Three draft skill packages created: handoff intake, entity resolution and duplicate/eligibility review.
- Three deterministic operator commands created and executed.
- Fourteen deterministic cases pass, including valid and invalid intake, idempotency, entity ambiguity/conflict and scope-specific duplicate handling.
- Three targeted behavioural scenarios pass after one isolated correction to expose the canonical record hash in the compact intake result.
- No Web, Apify, Twenty, HubSpot or n8n access occurred; external actions remain zero.
- Séverine approved W1-1 through W1-10 on `2026-08-27T12:34:34Z`; Wave 2 construction is authorised.

### Step 5C — Wave 2 Planning, Research and Verification — COMPLETED / APPROVED

- Three draft skill packages created: gap analysis and planning, permitted enrichment research, and field verification.
- Three deterministic operator commands created and executed, with three focused field-verification references.
- Twenty-four deterministic positive and negative cases pass.
- Three targeted behavioural command scenarios pass.
- Field verification requires a matching hashed source-preflight receipt; a free-text approval state is insufficient.
- Official-site social links are retained only from explicit links and remain separate by person or organisation scope; linked social profiles are not opened.
- HarvestAPI profile and email actions remain separate and blocked pending the complete runtime activation gate.
- Wave 1 post-promotion replay remains **13/13 PASS**.
- No Web, Apify, Twenty, HubSpot or n8n access occurred; external calls and actions remain zero.
- Séverine approved W2-1 through W2-10 on `2026-08-27T13:32:09Z`; Wave 3 construction is authorised.

### Step 5D — Wave 3 Decision, Review and Handoffs — COMPLETED / APPROVED

- Four draft skill packages created for evidence/confidence, protected fields, immutable revision readiness and governed review/handoffs.
- Six deterministic operator commands and one strict contract helper created or hardened.
- Twenty-one deterministic cases pass and four targeted behavioural scenarios pass.
- Lossless Markdown, CSV and Excel review projections are independently validated.
- A1 requalification is prepared without numeric score production; Twenty, HubSpot, A3 and A14 actions remain gated and undelivered.
- Waves 1 and 2 post-promotion regressions remain green.
- No Web, Apify, Twenty, HubSpot or n8n access occurred; external calls and actions remain zero.
- Séverine approved W3-1 through W3-10 on `2026-08-28T10:15:10Z`; full Step 5 regression is authorised.

### Step 5E — Full Operational Skills Regression and No-Integration Workflow — COMPLETED / APPROVED

- Ten approved skills consolidated across Waves 1–3.
- Fourteen skill-owned operator commands inventoried, hash-checked and exercised.
- Full deterministic replay: **58/58 PASS**; behavioural replay: **10/10 PASS**.
- Two synthetic no-integration workflows pass: Farrier review and Horse Owner requalification.
- Each workflow covers all fourteen operators and produces independently validated review projections.
- A1 requalification remains prepared-not-delivered; HubSpot, A3 and A14 remain contract-blocked.
- External calls and actions remain zero; profile status remains not pilot-ready.
- Séverine approved 5E-1 through 5E-10 on `2026-08-29T17:26:25Z`; Step 5 is closed and Step 6 is authorised.

### Step 5 — Operational Skills and Scripts

- Design complete skill family, then build in dependency waves.
- Wave 1: handoff intake, entity resolution, duplicate/eligibility review.
- Wave 2: gap plan, permitted enrichment research, contact/professional/equine verification.
- Wave 3: evidence/confidence, protected-field conflict handling, data quality, review package and handoffs.
- Add deterministic normalisation, validation, reconciliation and export scripts.
- Use one business checkpoint per wave.

### Step 6 — Model, Tools, Permissions and Quotas — APPROVED FOR SYNTHETIC LOCAL TESTING / REAL-DATA GATES PENDING

- Primary model configured as `deepseek-v4-flash` through Unitalk AI Gateway / LiteLLM / Microsoft Azure.
- Fallback configured as `Gemini 3.7 Flash` through Unitalk AI Gateway / LiteLLM / Google.
- Fallback is limited to one activation for technical failure after one retry.
- Local allowlist contains clarify, code execution, file, skills, terminal and todo only.
- Web, Apify, Twenty, HubSpot, n8n, outreach and durable handoffs remain disabled.
- Synthetic runs are capped at ten candidates with concurrency one and zero external API spend.
- Budget remains the global Unitalk–Mustad USD 5,000 pool with 50/80/100 percent thresholds.
- Static configuration validation passes **14/14**.
- A primary session response was observed with the configured logical model and zero external actions, but the smoke receipt is only a partial pass: LiteLLM request telemetry is absent, usage/cost is untracked and the reasoning task did not use the approved A2 catalogue or minimum package.
- The fallback live gateway route test remains pending.
- Provider region/retention evidence, named reviewers, approvers and cumulative token thresholds remain pending.

### Step 7 — Synthetic End-to-End Acceptance — READY FOR SÉVERINE REVIEW / NOT APPROVED

- Six representative synthetic scenarios pass: Farrier review, Horse Owner requalification, possible duplicate, confirmed duplicate, authoritative conflict and prohibited social-profile opening.
- Both complete workflows cover all fourteen approved operator commands.
- Export validation passes for two Markdown packages, twelve CSV files and two Excel workbooks.
- Human decisions remain pending or explicitly synthetic; external calls and actions remain zero.
- Step 6 and complete Step 5 regressions remain green.
- The bounded profile-level invocation passes with the expected 6/6 scenarios, 14/14 operators, export counts, Unitalk identity wording and unavailable—not zero—model usage/cost.

### Step 8 — Bounded Real No-Integration Pilot

- Use a small approved set of A1 candidates.
- Reuse A1 evidence first.
- Run targeted source checks only for approved gaps/conflicts/freshness.
- Use no HubSpot writes, outreach, paid provider or automated LinkedIn.
- Require human review for every record.

### Step 9 — Evaluation, Improvement and No-Integration Freeze

- Review quality, coverage, false matches, gaps, time and cost.
- Apply approved corrections.
- Replay accepted records deterministically.
- Package release manifest, runbook, open-items register and safe delivery archive.
- Promote only after approval to `PILOT_READY_NO_INTEGRATION`.

### Step 10 — Integrations

- Configure least-privilege HubSpot read OAuth after approval.
- Verify live metadata, associations, records, fill rates and permissions.
- Finalise A2-to-HubSpot mapping.
- Select/configure Twenty or another review layer.
- Build n8n triggers, waits, approvals, retries, idempotency, notifications and dead-letter handling.
- Configure any approved provider.
- Build A1 requalification, A3 and A14 structured handoffs.
- Build guarded HubSpot write action only after workflow-dependency audit.

### Step 11 — Integrated Pilot

- Run read-only and proposed-patch tests first.
- Test duplicate, customer, Deal, consent, suppression, owner and list states.
- Test approval, write, reconciliation, rollback and duplicate-execution protection in an approved environment.
- Keep all enriched records human-reviewed.

### Step 12 — Production Readiness and Acceptance

- Confirm roles, permissions, approval matrix and operating coverage.
- Confirm monitoring, audit, retention, deletion, incident and cost controls.
- Pass representative quality, safety, integration and rollback tests.
- Obtain recorded Equinet production approval.
- Keep contractual acceptance as a separate milestone.

## 5. Current blockers and non-blockers

- **Not a blocker for Step 2D:** no live HubSpot connection.
- **Not a blocker for Step 2D:** pending Equinet role/field answers; the stable schema uses generic field assessments.
- **Blocks final Business Field Catalogue:** target roles, contact limit, minimum contactability and horse-count taxonomy decisions.
- **Blocks real no-integration pilot:** A2 reviewer/backup, field priorities, source register and privacy decisions.
- **Blocks paid provider testing:** provider/data route/budget approval.
- **Blocks HubSpot integrated pilot:** OAuth, scopes, live verification, associations, mapping and workflow-dependency audit.
- **Blocks production:** complete approval matrix, permissions, monitoring, retention/deletion, audit, failure/rollback and Equinet sign-off.

## 6. Immediate next action

Review and approve or amend decisions **S7-1 through S7-10**. Step 8 remains blocked until its separate real-data, reviewer and provider-governance gates are satisfied.
