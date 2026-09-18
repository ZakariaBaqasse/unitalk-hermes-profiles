# A2 Step 5C Wave 2 Implementation Plan

> **For Unitalk:** Execute this plan task-by-task and keep promotion behind Séverine's explicit approval.

**Goal:** Deliver fixture-backed, deterministic Wave 2 skills for bounded gap planning, source-action preflight and field observation verification without enabling any external integration.

**Architecture:** Three skill packages reference the active Business Field Catalogue, Minimum Data Packages, Source Register and Provider Policy through the Active Foundation Manifest. Three deterministic commands exchange compact JSON contracts. Web, Apify, HubSpot, Twenty, n8n, outreach and CRM writes remain disabled; source actions are simulated only from controlled fixtures.

**Tech stack:** Python 3.13 standard library, JSON fixtures, Markdown skill packages, existing Equinet A2 foundation contracts.

---

## Task 1 — Wave 2 contracts and fixtures

- Create `evaluations/step5c/fixtures/wave2-cases.json`.
- Cover complete records, required gaps, optional gaps, exhausted research, prohibited fields, source-policy blocks, official-site fixtures, Apify blocks, social-link attribution, professional contacts, ambiguous roles and explicit versus inferred horse counts.
- Keep every fixture synthetic and reserve external actions at zero.

## Task 2 — Gap analysis and planning

- Create `scripts/build_a2_gap_plan.py`.
- Reuse the active Business Field Catalogue and Minimum Data Packages.
- Require a Wave 1 `eligible` decision.
- Create field-level needs only for gaps, conflicts, stale values or verification needs.
- Exclude optional fields unless explicitly requested.
- Reject `do_not_collect` requests and never reject or rescore a prospect because a required field is missing.
- Create `skills/a2-gap-analysis-and-enrichment-planning/` with three eval cases.

## Task 3 — Source-action preflight

- Create `scripts/preflight_a2_source_action.py`.
- Resolve the requested source from the active Source Register.
- Check named need, field policy, source status, rights, runtime, limits, provider budget and stop conditions.
- Permit only controlled local fixture simulation during Step 5C.
- Keep official-site live access pending Step 6 runtime controls and keep HarvestAPI blocked pending all approved gates.
- Create `skills/a2-permitted-enrichment-research/` with three eval cases.

## Task 4 — Field observation normalisation and verification

- Create `scripts/normalise_and_validate_a2_observations.py`.
- Validate field keys, source/action receipts and evidence references.
- Normalise approved emails, phones, URLs, text, lists, integers and role classifications.
- Reject guessed contact data, inferred horse counts and cross-scope social URLs.
- Hold personal email for privacy review and ambiguous links/roles for human review.
- Keep final evidence confidence and protected-field decisions for Wave 3.
- Create `skills/a2-field-verification/` plus contact, professional and equine-business reference files and three eval cases.

## Task 5 — Static and deterministic validation

- Create `scripts/validate_step5c_wave2.py`.
- Verify Step 5B approval, package structure, active dependencies and command presence.
- Execute positive and negative fixture cases.
- Write `evaluations/step5c/technical-validation.json` and a hashed draft package manifest.
- Run Python compilation and the deployment-language audit.

## Task 6 — Simplified behavioural validation

- Exercise the exact Wave 2 commands against synthetic scenarios.
- Verify complete/no-research, blocked-provider and mixed-observation pathways.
- Save `evaluations/step5c/behavioural-validation.json` with zero external actions.

## Task 7 — Human business review

- Generate `evaluations/step5c/A2-WAVE-2-REVIEW.md`.
- Present the complete W2 decision table in French in the implementation conversation.
- Do not promote the skills or update the active SOUL/runtime manifest until Séverine explicitly approves the Wave 2 decisions.
