#!/usr/bin/env python3
"""Build the Step 5A operational skill architecture and runtime manifest."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "foundations" / "contracts" / "skills"
EVAL_DIR = ROOT / "evaluations" / "step5a"
VERSION = "0.1.0-draft.1"
CREATED_AT = "2026-08-27T12:00:31Z"
ACTIVE_FOUNDATION = ROOT / "foundations" / "contracts" / "A2-ACTIVE-FOUNDATION-MANIFEST.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def skill(skill_id, wave, mission, triggers, inputs, outputs, dependencies, scripts, boundaries, evals):
    return {
        "skill_id": skill_id,
        "package_path": f"skills/{skill_id}",
        "wave": wave,
        "status": "planned_not_created",
        "mission": mission,
        "triggers": triggers,
        "inputs": inputs,
        "outputs": outputs,
        "skill_dependencies": dependencies,
        "script_dependencies": scripts,
        "boundaries": boundaries,
        "representative_evaluations": evals,
    }


skills = [
    skill(
        "a2-handoff-intake-and-initialisation", 1,
        "Validate an authorised A1 handoff and create or return the first immutable canonical A2 revision.",
        ["A1 handoff received", "manual no-integration handoff supplied"],
        ["A1-to-A2 handoff 1.0.1", "operating scope", "idempotency ledger"],
        ["validated intake result", "canonical initial revision", "receipt or rejection reason"],
        [], ["a2-intake"],
        ["no research", "no handoff mutation", "no external delivery claim without receipt"],
        ["accepted organisation-only handoff", "invalid approval/hash rejection", "idempotent retry and collision"],
    ),
    skill(
        "a2-entity-resolution-and-normalisation", 1,
        "Normalise person and organisation identity while preserving source values and surfacing ambiguity.",
        ["canonical record initialised", "identity or relationship ambiguity detected"],
        ["canonical A2 revision", "immutable A1 identity", "approved normalisation rules"],
        ["normalised identity proposal", "match status", "ambiguity or conflict record"],
        ["a2-handoff-intake-and-initialisation"], ["a2-normalise-resolve-entities"],
        ["no invented entity", "no unproven relationship", "domain is not a unique key"],
        ["exact person-plus-company match", "same-name ambiguous match", "candidate alias not assigned to an entity"],
    ),
    skill(
        "a2-duplicate-and-eligibility-review", 1,
        "Evaluate duplicate and eligibility evidence without inferring unavailable CRM checks.",
        ["identity proposal available", "duplicate or exclusion signal present"],
        ["resolved identity proposal", "A1 duplicate evidence", "authoritative checks when connected"],
        ["continue, hold or block recommendation", "duplicate checks", "eligibility reasons"],
        ["a2-entity-resolution-and-normalisation"], ["a2-duplicate-eligibility"],
        ["possible duplicate means hold", "confirmed duplicate or exclusion means block", "unavailable is not clear"],
        ["no duplicate", "possible duplicate hold", "confirmed exclusion block"],
    ),
    skill(
        "a2-gap-analysis-and-enrichment-planning", 2,
        "Compare reusable evidence with the applicable minimum package and create a bounded field-level plan.",
        ["Wave 1 record can continue", "targeted enrichment fields requested"],
        ["canonical revision", "Business Field Catalogue", "Minimum Data Packages", "source availability"],
        ["named gap/conflict/freshness list", "bounded enrichment plan", "no-research decision when complete"],
        ["a2-duplicate-and-eligibility-review"], ["a2-build-gap-plan", "a2-evaluate-minimum-package"],
        ["reuse A1 first", "optional gaps do not block", "missing required data does not reject or rescore"],
        ["complete Farrier needs no research", "required gap creates plan", "exhausted required gap becomes hold"],
    ),
    skill(
        "a2-permitted-enrichment-research", 2,
        "Execute or simulate only a source-policy-approved, field-bounded enrichment plan.",
        ["approved enrichment plan contains an authorised source action"],
        ["enrichment plan", "A2 Source Register", "provider policy", "runtime permissions"],
        ["source attempts", "raw bounded observations", "blocked/not-found/error states", "audit usage"],
        ["a2-gap-analysis-and-enrichment-planning"], ["a2-source-preflight", "a2-social-link-classifier"],
        ["no second discovery crawl", "no social-profile opening", "Apify blocked until all gates", "one targeted retry"],
        ["official-site bounded plan", "explicit LinkedIn company URL retained", "blocked Apify request"],
    ),
    skill(
        "a2-field-verification", 2,
        "Normalise and verify contact, professional and equine-business observations against approved field rules.",
        ["bounded observations are available"],
        ["observation batch", "Business Field Catalogue", "source and evidence references"],
        ["field assessments", "normalised proposals", "unresolved or conflicting values"],
        ["a2-permitted-enrichment-research"], ["a2-normalise-validate-observations"],
        ["no guessed contact", "person and organisation URLs remain separate", "horse count is never inferred"],
        ["professional contact verification", "organisation social URL classification", "ambiguous role or horse count"],
    ),
    skill(
        "a2-evidence-confidence-and-freshness", 3,
        "Create traceable evidence records and deterministic confidence, verification and freshness results.",
        ["verified observation requires canonical evidence"],
        ["field observations", "Evidence Policy", "source receipts"],
        ["evidence records", "confidence score/level", "verification and freshness states"],
        ["a2-field-verification"], ["a2-evaluate-evidence-confidence"],
        ["confidence is not ICP fit", "blocked sources score zero", "unknown remains unknown"],
        ["official-site direct fact", "stale time-sensitive fact", "material conflict cap"],
    ),
    skill(
        "a2-protected-field-conflict-resolution", 3,
        "Compare observations with baseline values and produce safe field-level proposals without overwriting protected data.",
        ["verified observation differs from a baseline", "protected or manual value encountered"],
        ["field assessment", "Protected Fields Policy", "evidence result"],
        ["no-change, add, update, preserve-and-hold or block proposal"],
        ["a2-evidence-confidence-and-freshness"], ["a2-evaluate-protected-field-action"],
        ["no silent overwrite", "no consent/owner/lifecycle change", "low confidence is not a fact"],
        ["empty unprotected field", "different manual value", "authoritative consent conflict"],
    ),
    skill(
        "a2-data-quality-and-review-readiness", 3,
        "Evaluate record completeness and create the next immutable revision with an explicit review recommendation.",
        ["field proposals are complete", "research is exhausted", "record revision requested"],
        ["field assessments", "Minimum Data Packages", "prior canonical revision"],
        ["data-quality result", "workflow recommendation", "new immutable revision"],
        ["a2-protected-field-conflict-resolution"], ["a2-evaluate-minimum-package", "a2-create-revision"],
        ["no automatic rejection for a gap", "prior revisions remain immutable", "A2 never recalculates A1 score"],
        ["review-ready Farrier", "required gap still open", "material conflict held"],
    ),
    skill(
        "a2-review-package-and-governed-handoffs", 3,
        "Render lossless review views and prepare, validate or receive strictly gated Twenty, A1, HubSpot, A3 and A14 payloads.",
        ["record is ready for review", "review receipt received", "approved downstream preparation requested"],
        ["validated canonical revision", "review decision or receipt", "destination contract"],
        ["Markdown/CSV/XLSX package", "new correction revision", "prepared handoff or proposed patch"],
        ["a2-data-quality-and-review-readiness"], ["a2-render-review-package", "a2-twenty-review", "a2-governed-handoff"],
        ["canonical JSON remains authoritative", "no delivery/write claim without receipt", "A1 alone produces score revisions"],
        ["manual review package", "Twenty receipt mismatch", "A1 requalification and HubSpot proposal remain unexecuted"],
    ),
]

commands = [
    {"command_id": "a2-intake", "entrypoint": "scripts/a2_intake.py", "status": "planned_wrapper", "wave": 1, "owner_skill": skills[0]["skill_id"], "uses": ["scripts/validate_a1_to_a2_handoff.py", "scripts/initialize_a2_record.py", "scripts/validate_a2_enrichment_record.py"]},
    {"command_id": "a2-normalise-resolve-entities", "entrypoint": "scripts/normalise_and_resolve_a2_entities.py", "status": "to_build", "wave": 1, "owner_skill": skills[1]["skill_id"], "uses": []},
    {"command_id": "a2-duplicate-eligibility", "entrypoint": "scripts/evaluate_a2_duplicate_eligibility.py", "status": "to_build", "wave": 1, "owner_skill": skills[2]["skill_id"], "uses": []},
    {"command_id": "a2-build-gap-plan", "entrypoint": "scripts/build_a2_gap_plan.py", "status": "to_build", "wave": 2, "owner_skill": skills[3]["skill_id"], "uses": ["scripts/evaluate_a2_minimum_package.py"]},
    {"command_id": "a2-evaluate-minimum-package", "entrypoint": "scripts/evaluate_a2_minimum_package.py", "status": "existing_reuse", "wave": 2, "owner_skill": skills[3]["skill_id"], "uses": []},
    {"command_id": "a2-source-preflight", "entrypoint": "scripts/preflight_a2_source_action.py", "status": "to_build", "wave": 2, "owner_skill": skills[4]["skill_id"], "uses": []},
    {"command_id": "a2-social-link-classifier", "entrypoint": "scripts/classify_official_site_social_link.py", "status": "existing_reuse", "wave": 2, "owner_skill": skills[4]["skill_id"], "uses": []},
    {"command_id": "a2-normalise-validate-observations", "entrypoint": "scripts/normalise_and_validate_a2_observations.py", "status": "to_build", "wave": 2, "owner_skill": skills[5]["skill_id"], "uses": ["scripts/classify_official_site_social_link.py"]},
    {"command_id": "a2-evaluate-evidence-confidence", "entrypoint": "scripts/evaluate_a2_evidence_confidence.py", "status": "existing_reuse", "wave": 3, "owner_skill": skills[6]["skill_id"], "uses": []},
    {"command_id": "a2-evaluate-protected-field-action", "entrypoint": "scripts/evaluate_a2_protected_field_action.py", "status": "existing_reuse", "wave": 3, "owner_skill": skills[7]["skill_id"], "uses": []},
    {"command_id": "a2-create-revision", "entrypoint": "scripts/create_a2_revision.py", "status": "to_build", "wave": 3, "owner_skill": skills[8]["skill_id"], "uses": ["scripts/validate_a2_enrichment_record.py"]},
    {"command_id": "a2-render-review-package", "entrypoint": "scripts/render_and_validate_a2_review_package.py", "status": "planned_wrapper", "wave": 3, "owner_skill": skills[9]["skill_id"], "uses": ["scripts/render_a2_review_views.py"]},
    {"command_id": "a2-twenty-review", "entrypoint": "scripts/build_and_validate_a2_twenty_review.py", "status": "planned_wrapper_integration_disabled", "wave": 3, "owner_skill": skills[9]["skill_id"], "uses": ["scripts/build_step3h_twenty_review.py", "scripts/validate_step3h_twenty_review.py"]},
    {"command_id": "a2-governed-handoff", "entrypoint": "scripts/build_and_validate_a2_handoff.py", "status": "to_build_delivery_disabled", "wave": 3, "owner_skill": skills[9]["skill_id"], "uses": []},
]

manifest = {
    "manifest_id": "equinet-a2-operational-skill-architecture",
    "version": VERSION,
    "status": "ready_for_severine_review_not_approved",
    "profile": "equinet-a2-enrichment",
    "created_at": CREATED_AT,
    "active_foundation": {"path": str(ACTIVE_FOUNDATION.relative_to(ROOT)), "sha256": sha(ACTIVE_FOUNDATION)},
    "architecture_principles": {
        "skill_packages": 10,
        "dependency_waves": 3,
        "operator_entrypoints": 14,
        "canonical_json_is_lossless_source": True,
        "business_configuration_is_referenced_not_duplicated": True,
        "deterministic_logic_uses_scripts": True,
        "external_system_access_requires_integration": True,
        "default_action_mode": "draft_for_approval",
        "a1_owns_numeric_scoring": True,
        "no_integration_mode_has_no_external_actions": True,
    },
    "waves": [
        {"wave": 1, "name": "Intake and Identity", "objective": "Create a valid canonical A2 starting point and resolve identity, duplicate and eligibility states before research.", "skill_ids": [x["skill_id"] for x in skills if x["wave"] == 1], "external_tools_required": [], "approval_gate": "wave_1_business_and_safety_acceptance"},
        {"wave": 2, "name": "Planning, Research and Verification", "objective": "Plan only named gaps, apply source preflight and verify bounded observations.", "skill_ids": [x["skill_id"] for x in skills if x["wave"] == 2], "external_tools_required": [], "conditional_future_tools": ["bounded official-site web access", "approved Apify connector"], "approval_gate": "wave_2_source_and_field_acceptance"},
        {"wave": 3, "name": "Decision, Review and Handoffs", "objective": "Create evidence-backed proposals, immutable revisions, review packages and non-executed governed handoffs.", "skill_ids": [x["skill_id"] for x in skills if x["wave"] == 3], "external_tools_required": [], "conditional_future_tools": ["Twenty", "HubSpot", "n8n", "A1/A3/A14 durable handoffs"], "approval_gate": "wave_3_review_and_handoff_acceptance"},
    ],
    "skills": skills,
    "operator_commands": commands,
    "supporting_modules_not_counted_as_operator_entrypoints": [
        "scripts/validate_a1_to_a2_handoff.py",
        "scripts/initialize_a2_record.py",
        "scripts/validate_a2_enrichment_record.py",
        "scripts/render_a2_review_views.py",
        "scripts/classify_official_site_social_link.py",
    ],
    "profile_orchestration_entrypoint": {
        "path": "scripts/run_a2_no_integration_workflow.py",
        "status": "to_build_after_wave_3",
        "counted_in_operator_entrypoints": False,
        "reason": "It orchestrates approved skill commands but is not owned by one business skill package.",
    },
    "integration_boundary": {
        "step_5": "Build skills, local deterministic scripts, schemas and fixture-backed outputs without live integrations.",
        "step_6": "Configure models, tool allowlists, permissions, quotas and runtime controls.",
        "step_8": "Run bounded official-site checks only after the approved runtime policy is active.",
        "step_10": "Connect Twenty, HubSpot, n8n and any approved provider; replace preparation-only commands with guarded execution adapters.",
        "current_external_actions_authorized": False,
        "apify_runtime_active": False,
        "hubspot_write_authorized": False,
        "outreach_authorized": False,
    },
    "wave_delivery_method": [
        "create all skill packages and scripts in the wave",
        "run package and static validation",
        "run deterministic positive and negative fixtures",
        "run two or three targeted profile-level behavioural cases",
        "present complete business review in chat",
        "obtain explicit Séverine approval",
        "promote the whole wave atomically and rerun regression checks",
    ],
    "decision_checkpoint": {
        "decision_ids": [f"5A-{n}" for n in range(1, 11)],
        "approval_required_before_wave_1_build": True,
        "next_gate_after_approval": "Step 5B — Wave 1 Intake and Identity",
    },
}

OUT_DIR.mkdir(parents=True, exist_ok=True)
EVAL_DIR.mkdir(parents=True, exist_ok=True)
manifest_path = OUT_DIR / f"a2-operational-skill-manifest-{VERSION}.json"
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

rows = []
for item in skills:
    rows.append(
        f"| {item['wave']} | `{item['skill_id']}` | {item['mission']} | "
        f"{', '.join(item['skill_dependencies']) or 'None'} | `{item['status']}` |"
    )
command_rows = []
for item in commands:
    command_rows.append(
        f"| {item['wave']} | `{item['command_id']}` | `{item['entrypoint']}` | `{item['status']}` | `{item['owner_skill']}` |"
    )
architecture = f"""# Equinet A2 Operational Skill Architecture

**Version:** `{VERSION}`  
**Status:** `READY FOR SÉVERINE REVIEW — NOT APPROVED`  
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
{chr(10).join(rows)}

The three contact, professional and equine verification variants remain references inside one `a2-field-verification` package. Split them only if future tools or permissions materially diverge.

## 4. Operator-facing deterministic commands

| Wave | Command | Entrypoint | Status | Owning skill |
|---:|---|---|---|---|
{chr(10).join(command_rows)}

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

After approval of decisions `5A-1` through `5A-10`, proceed to `Step 5B — Wave 1 Intake and Identity`.
"""
(ROOT / "foundations" / "A2-OPERATIONAL-SKILL-ARCHITECTURE.md").write_text(architecture, encoding="utf-8")

review = """# Decision Review — Step 5A Operational Skill Architecture

**Status:** `READY FOR SÉVERINE REVIEW — NOT APPROVED`  
**Profile:** `equinet-a2-enrichment`  
**Proposed manifest:** `0.1.0-draft.1`

## Decisions proposed

| ID | Decision |
|---|---|
| 5A-1 | Build ten operational skill packages in three dependency waves: 3, 3 and 4. |
| 5A-2 | Complete and approve each wave before starting the next wave. |
| 5A-3 | Keep contact, professional and equine verification as three references inside one field-verification skill unless their tools or permissions diverge. |
| 5A-4 | Expose fourteen skill-owned deterministic operator commands and one later profile-level no-integration orchestrator. |
| 5A-5 | Reuse approved contracts by reference and never duplicate mutable thresholds or catalogues inside a skill. |
| 5A-6 | Keep A1 as the only numeric ICP scoring authority. |
| 5A-7 | Keep Web, Apify, Twenty, HubSpot, n8n, outreach and external writes disabled during Step 5. |
| 5A-8 | Require package/static, deterministic and small targeted behavioural validation for each wave. |
| 5A-9 | Treat old Step 3 builders pinned to `0.1.0-draft.1` as historical reproduction tools, not active generators. |
| 5A-10 | Start Wave 1 with handoff intake, entity resolution and duplicate/eligibility review after approval. |

## Approval effect

Approval authorises creation and controlled testing of Wave 1 skill packages and local deterministic scripts. It does not activate any external integration, source access, provider spend, CRM action, outreach, pilot or production status.

## Next gate after approval

`Step 5B — Wave 1 Intake and Identity`
"""
(EVAL_DIR / "A2-OPERATIONAL-SKILL-ARCHITECTURE-REVIEW.md").write_text(review, encoding="utf-8")

print(json.dumps({"manifest": str(manifest_path), "skills": len(skills), "waves": 3, "commands": len(commands), "status": manifest["status"]}, indent=2))
