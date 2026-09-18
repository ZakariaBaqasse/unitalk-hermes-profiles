# Equinet A2 Operational Skill Architecture

**Version:** `0.1.0`  
**Status:** `APPROVED FOR WAVE 1 BUILD`  
**Profile:** `equinet-a2-enrichment`  
**Step:** `5A — Operational Skill Architecture and Runtime Manifest`

## 1. Decision

Build ten operational skill packages in three dependency waves. Keep mutable Equinet configurations outside the skills and resolve them through the Active Foundation Manifest. Use deterministic scripts for validation, normalisation, state decisions, revision creation, package rendering and handoff preparation.

Step 5 does not activate Web access, Apify, Twenty, HubSpot, n8n, outreach or any production write.

## 2. Wave order

| Wave | Name | Skills | Business checkpoint |
|---|---|---:|---|
| 1 | Intake and Identity | 3 | Approve intake, identity, duplicate and eligibility behaviour before research |
| 2 | Planning, Research and Verification | 3 | Approve source planning and field verification before decision logic |
| 3 | Decision, Review and Handoffs | 4 | Approve evidence, conflicts, readiness, review views and preparation-only handoffs |

## 3. Skill packages

| Wave | Skill | Mission | Skill dependency | Status |
|---:|---|---|---|---|
| 1 | `a2-handoff-intake-and-initialisation` | Validate an authorised A1 handoff and create or return the first immutable canonical A2 revision. | None | `planned_not_created` |
| 1 | `a2-entity-resolution-and-normalisation` | Normalise person and organisation identity while preserving source values and surfacing ambiguity. | a2-handoff-intake-and-initialisation | `planned_not_created` |
| 1 | `a2-duplicate-and-eligibility-review` | Evaluate duplicate and eligibility evidence without inferring unavailable CRM checks. | a2-entity-resolution-and-normalisation | `planned_not_created` |
| 2 | `a2-gap-analysis-and-enrichment-planning` | Compare reusable evidence with the applicable minimum package and create a bounded field-level plan. | a2-duplicate-and-eligibility-review | `planned_not_created` |
| 2 | `a2-permitted-enrichment-research` | Execute or simulate only a source-policy-approved, field-bounded enrichment plan. | a2-gap-analysis-and-enrichment-planning | `planned_not_created` |
| 2 | `a2-field-verification` | Normalise and verify contact, professional and equine-business observations against approved field rules. | a2-permitted-enrichment-research | `planned_not_created` |
| 3 | `a2-evidence-confidence-and-freshness` | Create traceable evidence records and deterministic confidence, verification and freshness results. | a2-field-verification | `planned_not_created` |
| 3 | `a2-protected-field-conflict-resolution` | Compare observations with baseline values and produce safe field-level proposals without overwriting protected data. | a2-evidence-confidence-and-freshness | `planned_not_created` |
| 3 | `a2-data-quality-and-review-readiness` | Evaluate record completeness and create the next immutable revision with an explicit review recommendation. | a2-protected-field-conflict-resolution | `planned_not_created` |
| 3 | `a2-review-package-and-governed-handoffs` | Render lossless review views and prepare, validate or receive strictly gated Twenty, A1, HubSpot, A3 and A14 payloads. | a2-data-quality-and-review-readiness | `planned_not_created` |

The three contact, professional and equine verification variants remain references inside one `a2-field-verification` package. Split them only if future tools or permissions materially diverge.

## 4. Operator-facing deterministic commands

| Wave | Command | Entrypoint | Status | Owning skill |
|---:|---|---|---|---|
| 1 | `a2-intake` | `scripts/a2_intake.py` | `planned_wrapper` | `a2-handoff-intake-and-initialisation` |
| 1 | `a2-normalise-resolve-entities` | `scripts/normalise_and_resolve_a2_entities.py` | `to_build` | `a2-entity-resolution-and-normalisation` |
| 1 | `a2-duplicate-eligibility` | `scripts/evaluate_a2_duplicate_eligibility.py` | `to_build` | `a2-duplicate-and-eligibility-review` |
| 2 | `a2-build-gap-plan` | `scripts/build_a2_gap_plan.py` | `to_build` | `a2-gap-analysis-and-enrichment-planning` |
| 2 | `a2-evaluate-minimum-package` | `scripts/evaluate_a2_minimum_package.py` | `existing_reuse` | `a2-gap-analysis-and-enrichment-planning` |
| 2 | `a2-source-preflight` | `scripts/preflight_a2_source_action.py` | `to_build` | `a2-permitted-enrichment-research` |
| 2 | `a2-social-link-classifier` | `scripts/classify_official_site_social_link.py` | `existing_reuse` | `a2-permitted-enrichment-research` |
| 2 | `a2-normalise-validate-observations` | `scripts/normalise_and_validate_a2_observations.py` | `to_build` | `a2-field-verification` |
| 3 | `a2-evaluate-evidence-confidence` | `scripts/evaluate_a2_evidence_confidence.py` | `existing_reuse` | `a2-evidence-confidence-and-freshness` |
| 3 | `a2-evaluate-protected-field-action` | `scripts/evaluate_a2_protected_field_action.py` | `existing_reuse` | `a2-protected-field-conflict-resolution` |
| 3 | `a2-create-revision` | `scripts/create_a2_revision.py` | `to_build` | `a2-data-quality-and-review-readiness` |
| 3 | `a2-render-review-package` | `scripts/render_and_validate_a2_review_package.py` | `planned_wrapper` | `a2-review-package-and-governed-handoffs` |
| 3 | `a2-twenty-review` | `scripts/build_and_validate_a2_twenty_review.py` | `planned_wrapper_integration_disabled` | `a2-review-package-and-governed-handoffs` |
| 3 | `a2-governed-handoff` | `scripts/build_and_validate_a2_handoff.py` | `to_build_delivery_disabled` | `a2-review-package-and-governed-handoffs` |

The profile-level `run_a2_no_integration_workflow.py` orchestration command is built after Wave 3 and is not counted among the fourteen skill-owned entrypoints.

## 5. Existing components to reuse

- `validate_a1_to_a2_handoff.py`;
- `initialize_a2_record.py`;
- `validate_a2_enrichment_record.py`;
- `evaluate_a2_minimum_package.py`;
- `classify_official_site_social_link.py`;
- `evaluate_a2_evidence_confidence.py`;
- `evaluate_a2_protected_field_action.py`;
- `render_a2_review_views.py`;
- Step 3H Twenty payload/receipt builders as inputs to a new operational wrapper.

Existing Step 3 builders and validators pinned to `0.1.0-draft.1` remain historical reproduction tools. They must not regenerate the active `0.1.1-draft.1` baseline.

## 6. Packaging standard

Each skill package must contain:

- `SKILL.md` with a concise trigger;
- exact input and output contracts;
- authoritative dependency references;
- deterministic workflow and stop conditions;
- explicit prohibited actions;
- bundled scripts or references where needed;
- two or three representative evaluation cases;
- the handoff to the next skill;
- version and approval status.

## 7. Validation ladder per wave

1. Package and static validation.
2. Deterministic fixtures and negative regressions.
3. Two or three targeted profile-level behavioural cases.
4. Complete business review in chat.
5. Explicit Séverine approval.
6. Atomic promotion and post-promotion regression.

No large baseline benchmark is required unless a real quality or model-selection decision needs it.

## 8. Integration boundary

During Step 5, every integration-dependent command remains preparation-only. Step 6 configures runtime tools and permissions. Step 8 may activate bounded official-site access. Step 10 handles Twenty, HubSpot, n8n, Apify and durable cross-profile delivery.

## 9. Next gate

Decisions `5A-1` through `5A-10` were approved by Séverine. Proceed to `Step 5B — Wave 1 Intake and Identity`.
