#!/usr/bin/env python3
"""Validate the Step 5A A2 operational skill architecture."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "evaluations" / "step5a"
MANIFEST = ROOT / "foundations/contracts/skills/a2-operational-skill-manifest-0.1.0-draft.1.json"
DOC = ROOT / "foundations/A2-OPERATIONAL-SKILL-ARCHITECTURE.md"
REVIEW = ROOT / "evaluations/step5a/A2-OPERATIONAL-SKILL-ARCHITECTURE-REVIEW.md"
OUTPUT = ROOT / "evaluations/step5a/technical-validation.json"
PACKAGE = ROOT / "evaluations/step5a/step5a-draft-package-manifest.json"
LANGUAGE = ROOT / "evaluations/foundation-clarifications/language-audit.json"
ACTIVE_FOUNDATION = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"
BUILDER = ROOT / "scripts/build_step5a_skill_architecture.py"
VALIDATOR = Path(__file__).resolve()

EXPECTED_SKILLS = {
    "a2-handoff-intake-and-initialisation": 1,
    "a2-entity-resolution-and-normalisation": 1,
    "a2-duplicate-and-eligibility-review": 1,
    "a2-gap-analysis-and-enrichment-planning": 2,
    "a2-permitted-enrichment-research": 2,
    "a2-field-verification": 2,
    "a2-evidence-confidence-and-freshness": 3,
    "a2-protected-field-conflict-resolution": 3,
    "a2-data-quality-and-review-readiness": 3,
    "a2-review-package-and-governed-handoffs": 3,
}
EXPECTED_WAVE_COUNTS = {1: 3, 2: 3, 3: 4}
EXPECTED_COMMANDS = {
    "a2-intake", "a2-normalise-resolve-entities", "a2-duplicate-eligibility", "a2-build-gap-plan",
    "a2-evaluate-minimum-package", "a2-source-preflight", "a2-social-link-classifier",
    "a2-normalise-validate-observations", "a2-evaluate-evidence-confidence",
    "a2-evaluate-protected-field-action", "a2-create-revision", "a2-render-review-package",
    "a2-twenty-review", "a2-governed-handoff",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(manifest: dict) -> list[str]:
    errors = []
    if manifest.get("version") != "0.1.0-draft.1" or manifest.get("status") != "ready_for_severine_review_not_approved":
        errors.append("Step 5A version or review status mismatch")
    foundation = manifest.get("active_foundation", {})
    foundation_path = ROOT / foundation.get("path", "missing")
    if not foundation_path.exists() or sha(foundation_path) != foundation.get("sha256"):
        errors.append("active foundation dependency hash mismatch")

    skills = manifest.get("skills", [])
    ids = [item.get("skill_id") for item in skills]
    if len(ids) != 10 or len(ids) != len(set(ids)) or set(ids) != set(EXPECTED_SKILLS):
        errors.append("skill inventory must contain the exact ten unique packages")
    by_id = {item.get("skill_id"): item for item in skills}
    for skill_id, wave in EXPECTED_SKILLS.items():
        item = by_id.get(skill_id, {})
        if item.get("wave") != wave:
            errors.append(f"skill wave mismatch: {skill_id}")
        for key in ["mission", "triggers", "inputs", "outputs", "skill_dependencies", "script_dependencies", "boundaries", "representative_evaluations"]:
            if key not in item or item[key] in (None, "", []):
                if key == "skill_dependencies" and wave == 1 and skill_id == "a2-handoff-intake-and-initialisation":
                    continue
                errors.append(f"skill contract incomplete: {skill_id}.{key}")
        if len(item.get("representative_evaluations", [])) < 3:
            errors.append(f"insufficient representative evaluations: {skill_id}")
        if item.get("status") != "planned_not_created":
            errors.append(f"skill status overstated: {skill_id}")
        for dep in item.get("skill_dependencies", []):
            if dep not in by_id:
                errors.append(f"unknown skill dependency: {skill_id}->{dep}")
            elif EXPECTED_SKILLS[dep] > wave:
                errors.append(f"forward skill dependency: {skill_id}->{dep}")

    counts = {wave: sum(item.get("wave") == wave for item in skills) for wave in EXPECTED_WAVE_COUNTS}
    if counts != EXPECTED_WAVE_COUNTS:
        errors.append("wave skill counts must be 3, 3 and 4")
    waves = manifest.get("waves", [])
    if [item.get("wave") for item in waves] != [1, 2, 3]:
        errors.append("wave order mismatch")
    for wave in waves:
        expected = [item["skill_id"] for item in skills if item["wave"] == wave["wave"]]
        if wave.get("skill_ids") != expected or not wave.get("approval_gate"):
            errors.append(f"wave membership or gate mismatch: {wave.get('wave')}")

    commands = manifest.get("operator_commands", [])
    command_ids = [item.get("command_id") for item in commands]
    if len(command_ids) != 14 or len(command_ids) != len(set(command_ids)) or set(command_ids) != EXPECTED_COMMANDS:
        errors.append("operator command registry must contain the exact fourteen unique commands")
    allowed_statuses = {"existing_reuse", "to_build", "planned_wrapper", "planned_wrapper_integration_disabled", "to_build_delivery_disabled"}
    for command in commands:
        owner = by_id.get(command.get("owner_skill"))
        if owner is None:
            errors.append(f"unknown command owner: {command.get('command_id')}")
            continue
        if owner["wave"] != command.get("wave"):
            errors.append(f"command/skill wave mismatch: {command.get('command_id')}")
        if command.get("status") not in allowed_statuses:
            errors.append(f"invalid command status: {command.get('command_id')}")
        if command.get("status") == "existing_reuse" and not (ROOT / command["entrypoint"]).exists():
            errors.append(f"existing command missing: {command.get('entrypoint')}")
        for dependency in command.get("uses", []):
            if not (ROOT / dependency).exists():
                errors.append(f"command dependency missing: {dependency}")

    for path in manifest.get("supporting_modules_not_counted_as_operator_entrypoints", []):
        if not (ROOT / path).exists():
            errors.append(f"supporting module missing: {path}")

    principles = manifest.get("architecture_principles", {})
    expected_principles = {
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
    }
    if principles != expected_principles:
        errors.append("architecture principles mismatch")
    boundary = manifest.get("integration_boundary", {})
    for key in ["current_external_actions_authorized", "apify_runtime_active", "hubspot_write_authorized", "outreach_authorized"]:
        if boundary.get(key) is not False:
            errors.append(f"integration boundary weakened: {key}")
    checkpoint = manifest.get("decision_checkpoint", {})
    if checkpoint.get("decision_ids") != [f"5A-{n}" for n in range(1, 11)] or checkpoint.get("approval_required_before_wave_1_build") is not True:
        errors.append("Step 5A decision checkpoint mismatch")
    return errors


def negative_regressions(manifest: dict) -> list[dict]:
    cases = []
    def run(name, expected, mutate):
        value = copy.deepcopy(manifest)
        mutate(value)
        found = validate(value)
        cases.append({"name": name, "expected_error": expected, "errors": found, "passed": any(expected in item for item in found)})
    run("duplicate_skill", "exact ten unique", lambda x: x["skills"].append(copy.deepcopy(x["skills"][0])))
    run("missing_skill", "exact ten unique", lambda x: x["skills"].pop())
    run("wave_count", "wave skill counts", lambda x: x["skills"][0].update(wave=2))
    run("forward_dependency", "forward skill dependency", lambda x: x["skills"][0]["skill_dependencies"].append("a2-review-package-and-governed-handoffs"))
    run("skill_claimed_created", "skill status overstated", lambda x: x["skills"][0].update(status="active"))
    run("duplicate_command", "exact fourteen unique", lambda x: x["operator_commands"].append(copy.deepcopy(x["operator_commands"][0])))
    run("command_wrong_wave", "command/skill wave mismatch", lambda x: x["operator_commands"][0].update(wave=3))
    run("external_actions_enabled", "integration boundary weakened", lambda x: x["integration_boundary"].update(current_external_actions_authorized=True))
    run("a1_score_ownership_removed", "architecture principles mismatch", lambda x: x["architecture_principles"].update(a1_owns_numeric_scoring=False))
    run("approval_gate_removed", "decision checkpoint mismatch", lambda x: x["decision_checkpoint"].update(approval_required_before_wave_1_build=False))
    return cases


def main() -> int:
    manifest = load(MANIFEST)
    errors = validate(manifest)
    negatives = negative_regressions(manifest)
    if any(not item["passed"] for item in negatives):
        errors.append("one or more negative regressions failed")
    doc = DOC.read_text(encoding="utf-8")
    review = REVIEW.read_text(encoding="utf-8")
    documentation = {
        "architecture_status": "READY FOR SÉVERINE REVIEW — NOT APPROVED" in doc,
        "three_waves": all(label in doc for label in ["Intake and Identity", "Planning, Research and Verification", "Decision, Review and Handoffs"]),
        "ten_decisions": all(f"| 5A-{n} |" in review for n in range(1, 11)),
        "integration_boundary": "does not activate Web access, Apify, Twenty, HubSpot, n8n, outreach or any production write" in doc,
        "next_gate": "Step 5B — Wave 1 Intake and Identity" in doc and "Step 5B — Wave 1 Intake and Identity" in review,
    }
    for name, passed in documentation.items():
        if not passed:
            errors.append(f"documentation check failed: {name}")
    language = load(LANGUAGE)
    if language.get("pass") is not True:
        errors.append("deployment-language audit failed")

    result = {
        "step": "5A",
        "status": "ready_for_severine_review_not_approved",
        "version": manifest["version"],
        "skill_count": len(manifest["skills"]),
        "wave_counts": {str(wave): sum(item["wave"] == wave for item in manifest["skills"]) for wave in [1, 2, 3]},
        "operator_command_count": len(manifest["operator_commands"]),
        "existing_reuse_commands": sum(item["status"] == "existing_reuse" for item in manifest["operator_commands"]),
        "commands_to_build_or_wrap": sum(item["status"] != "existing_reuse" for item in manifest["operator_commands"]),
        "validation": {"errors": validate(manifest), "passed": not validate(manifest)},
        "negative_regressions": {"total": len(negatives), "passed": sum(item["passed"] for item in negatives), "cases": negatives},
        "documentation_checks": documentation,
        "language_audit": {"files_checked": language.get("files_checked"), "findings": len(language.get("findings", [])), "passed": language.get("pass") is True},
        "skills_created": 0,
        "external_actions": 0,
        "approval_required": True,
        "next_gate_after_approval": "Step 5B — Wave 1 Intake and Identity",
        "failures": errors,
        "pass": not errors,
    }
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    files = [MANIFEST, DOC, REVIEW, BUILDER, VALIDATOR, ACTIVE_FOUNDATION, OUTPUT]
    package = {
        "manifest_id": "equinet-a2-step5a-draft-package",
        "version": manifest["version"],
        "status": "ready_for_severine_review_not_approved" if not errors else "validation_failed",
        "files": [{"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha(path)} for path in files],
        "file_count": len(files),
        "skills_created": 0,
        "external_actions": 0,
    }
    PACKAGE.write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "pass": result["pass"],
        "skills": result["skill_count"],
        "waves": result["wave_counts"],
        "operator_commands": result["operator_command_count"],
        "existing_reuse": result["existing_reuse_commands"],
        "to_build_or_wrap": result["commands_to_build_or_wrap"],
        "negative_regressions": f"{result['negative_regressions']['passed']}/{result['negative_regressions']['total']}",
        "status": result["status"],
        "failures": errors,
    }, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
