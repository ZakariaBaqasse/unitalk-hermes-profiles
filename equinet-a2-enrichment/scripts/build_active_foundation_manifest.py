#!/usr/bin/env python3
"""Build the active Equinet A2 foundation manifest after SOC clarification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "foundations" / "contracts" / "A2-ACTIVE-FOUNDATION-MANIFEST.json"

ACTIVE = [
    "SOUL.md",
    "foundations/A2-IMPLEMENTATION-CONTRACT.md",
    "foundations/contracts/a1-to-a2-handoff.schema.json",
    "foundations/contracts/canonical/a2-enrichment-record.schema.json",
    "foundations/contracts/a2-field-dictionary-0.1.0.csv",
    "foundations/contracts/a2-state-model-0.1.0.json",
    "foundations/contracts/requalification/a2-requalification-signal.schema.json",
    "foundations/contracts/requalification/a2-requalification-return.schema.json",
    "foundations/contracts/requalification/a1-score-revision-reference.schema.json",
    "foundations/contracts/business/a2-business-field-catalogue-0.1.1-draft.1.json",
    "foundations/contracts/business/a2-business-field-catalogue-0.1.1-draft.1.csv",
    "foundations/contracts/business/a2-minimum-data-packages-0.1.1-draft.1.json",
    "foundations/contracts/sources/a2-source-register-0.1.1-draft.1.json",
    "foundations/contracts/sources/a2-source-register-0.1.1-draft.1.csv",
    "foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.1.1-draft.1.json",
    "foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.1.1-draft.1.json",
    "foundations/contracts/governance/a2-provider-and-cost-policy-0.1.1-draft.1.json",
    "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.1.1-draft.1.json",
    "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.1.1-draft.1.csv",
    "foundations/contracts/twenty/a2-twenty-review-layer-contract-0.1.0-draft.1.json",
    "foundations/contracts/twenty/a2-twenty-review-receipt.schema.json",
    "foundations/A2-HANDOFF-TO-RECORD-INITIALISATION-CONTRACT.md",
    "foundations/A2-CROSS-FIELD-VALIDATOR-CONTRACT.md",
    "foundations/A2-REVIEW-VIEW-SPECIFICATION.md",
    "scripts/validate_a1_to_a2_handoff.py",
    "scripts/initialize_a2_record.py",
    "scripts/validate_a2_enrichment_record.py",
    "scripts/render_a2_review_views.py",
    "scripts/classify_official_site_social_link.py",
    "scripts/validate_official_site_social_profile_url_capture.py",
    "foundations/contracts/skills/a2-operational-skill-manifest-0.1.0.json",
    "foundations/contracts/skills/a2-wave1-runtime-manifest-0.1.0.json",
    "skills/a2-handoff-intake-and-initialisation/SKILL.md",
    "skills/a2-entity-resolution-and-normalisation/SKILL.md",
    "skills/a2-duplicate-and-eligibility-review/SKILL.md",
    "scripts/a2_intake.py",
    "scripts/normalise_and_resolve_a2_entities.py",
    "scripts/evaluate_a2_duplicate_eligibility.py",
    "foundations/contracts/skills/a2-wave2-runtime-manifest-0.1.0.json",
    "skills/a2-gap-analysis-and-enrichment-planning/SKILL.md",
    "skills/a2-permitted-enrichment-research/SKILL.md",
    "skills/a2-field-verification/SKILL.md",
    "skills/a2-field-verification/references/contact-verification.md",
    "skills/a2-field-verification/references/professional-verification.md",
    "skills/a2-field-verification/references/equine-business-verification.md",
    "scripts/a2_wave2_contracts.py",
    "scripts/build_a2_gap_plan.py",
    "scripts/preflight_a2_source_action.py",
    "scripts/normalise_and_validate_a2_observations.py",
    "foundations/contracts/canonical/a2-review-view-spec-0.1.0.json",
    "foundations/contracts/requalification/a2-requalification-package.schema.json",
    "foundations/contracts/skills/a2-wave3-runtime-manifest-0.1.0.json",
    "skills/a2-evidence-confidence-and-freshness/SKILL.md",
    "skills/a2-protected-field-conflict-resolution/SKILL.md",
    "skills/a2-data-quality-and-review-readiness/SKILL.md",
    "skills/a2-review-package-and-governed-handoffs/SKILL.md",
    "scripts/a2_wave3_contracts.py",
    "scripts/evaluate_a2_evidence_confidence.py",
    "scripts/evaluate_a2_protected_field_action.py",
    "scripts/create_a2_revision.py",
    "scripts/render_and_validate_a2_review_package.py",
    "scripts/build_and_validate_a2_twenty_review.py",
    "scripts/build_and_validate_a2_handoff.py",
    "scripts/evaluate_a2_minimum_package.py",
    "scripts/run_a2_no_integration_workflow.py",
    "foundations/contracts/skills/a2-step5-runtime-manifest-0.1.0.json",
    "config.yaml",
    "foundations/contracts/runtime/a2-runtime-policy-0.1.0.yaml",
    "foundations/contracts/runtime/a2-step7-synthetic-acceptance-manifest-0.1.0.json",
    "foundations/contracts/runtime/a2-step8-pilot-runtime-policy-0.1.0.yaml",
]

LEGACY_BUILDERS = [
    "scripts/build_step3a_business_field_catalogue.py",
    "scripts/validate_step3a_business_field_catalogue.py",
    "scripts/build_step3b_minimum_packages.py",
    "scripts/run_step3b_tests.py",
    "scripts/build_step3c_source_register.py",
    "scripts/validate_step3c_source_register.py",
    "scripts/build_step3d_evidence_policy.py",
    "scripts/run_step3d_tests.py",
    "scripts/build_step3e_protected_fields.py",
    "scripts/run_step3e_tests.py",
    "scripts/build_step3f_provider_cost_policy.py",
    "scripts/run_step3f_tests.py",
    "scripts/build_step3g_hubspot_mapping.py",
    "scripts/validate_step3g_hubspot_mapping.py",
    "scripts/validate_step4_final_soul.py",
    "scripts/refresh_step3_acceptance_hashes.py",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    missing = [rel for rel in ACTIVE + LEGACY_BUILDERS if not (ROOT / rel).exists()]
    if missing:
        print(json.dumps({"pass": False, "missing": missing}, indent=2))
        return 1
    manifest = {
        "manifest_id": "equinet-a2-active-foundation",
        "version": "1.0.0",
        "status": "foundation_configured_not_pilot_ready",
        "active_since": "2026-08-27T11:40:17Z",
        "canonical_schema_version": "1.0.0",
        "active_business_configuration_version": "0.1.1-draft.1",
        "current_clarification": "SOC-1 through SOC-8 — Official-Site Social Profile URL Capture",
        "active_files": [
            {"path": rel, "bytes": (ROOT / rel).stat().st_size, "sha256": sha(ROOT / rel)}
            for rel in ACTIVE
        ],
        "historical_step_builders": [
            {
                "path": rel,
                "status": "historical_reproduction_only_do_not_use_to_generate_active_baseline",
                "pinned_configuration_version": "0.1.0-draft.1",
            }
            for rel in LEGACY_BUILDERS
        ],
        "runtime_activation": {
            "official_site": False,
            "apify_harvestapi": False,
            "social_profile_automated_access": False,
            "hubspot_read": False,
            "hubspot_write": False,
            "twenty": False,
            "n8n": False,
        },
        "next_gate": "Step 8 — Bounded Real No-Integration Pilot Execution",
    }
    OUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pass": True, "active_files": len(ACTIVE), "historical_builders": len(LEGACY_BUILDERS), "output": str(OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
