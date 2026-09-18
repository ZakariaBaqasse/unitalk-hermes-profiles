#!/usr/bin/env python3
"""Build Step 9C release-candidate documentation and manifest."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
STEP9 = ROOT / "evaluations/step9"
DELIVERY = STEP9 / "delivery"
RC = STEP9 / "release-candidate"
PHASE9A = STEP9 / "phase9a-validation.json"
PHASE9B = STEP9 / "regression/phase9b-regression.json"
INVENTORY = STEP9 / "release-candidate-inventory.json"
RC_FOUNDATION = RC / "A2-ACTIVE-FOUNDATION-MANIFEST-1.1.0-rc.1.json"
RC_POLICY = RC / "a2-no-integration-runtime-policy-1.0.0-rc.1.yaml"
STEP8 = ROOT / "evaluations/step8/acceptance-record.json"
LANGUAGE = ROOT / "evaluations/foundation-clarifications/language-audit.json"
CONFIG = ROOT / "config.yaml"
SOUL = ROOT / "SOUL.md"
PLAN = STEP9 / "step9-plan.json"
MANIFEST = RC / "release-candidate-manifest-1.0.0-rc.1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    DELIVERY.mkdir(parents=True, exist_ok=True)
    phase9a = load(PHASE9A)
    phase9b = load(PHASE9B)
    inventory = load(INVENTORY)
    foundation = load(RC_FOUNDATION)
    step8 = load(STEP8)
    language = load(LANGUAGE)
    policy = yaml.safe_load(RC_POLICY.read_text(encoding="utf-8"))
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if phase9a.get("status") != "pass_ready_for_step9b" or phase9b.get("status") != "pass_ready_for_step9c":
        raise RuntimeError("Step 9A or 9B prerequisite is not valid")

    configuration = DELIVERY / "A2-NO-INTEGRATION-CONFIGURATION-PACKAGE.md"
    runbook = DELIVERY / "A2-MANUAL-NO-INTEGRATION-RUNBOOK.md"
    evaluation = DELIVERY / "A2-STEP9-EVALUATION-REPORT.md"
    open_items = DELIVERY / "A2-OPEN-ITEMS-REGISTER.md"
    acceptance_review = DELIVERY / "A2-STEP9-ACCEPTANCE-REVIEW.md"

    skill_rows = "\n".join(
        f"| `{item['skill_id']}` | `{item['version']}` | `{item['status']}` |"
        for item in foundation["skills"]
    )
    write(
        configuration,
        f"""# Equinet A2 No-Integration Configuration Package

**Release candidate:** `equinet-a2-no-integration-1.0.0-rc.1`  
**Status:** `READY FOR STEP 9D PACKAGING — NOT APPROVED OR ACTIVE`  
**Profile:** `equinet-a2-enrichment`

## Mission and scope

Prepare evidence-backed, human-reviewable enrichment records from an approved A1 handoff. Preserve the A1 snapshot and score, use authorised evidence only, expose gaps and conflicts, and never infer consent or purchasing authority.

## Runtime

| Control | Release-candidate value |
|---|---|
| Primary model | `deepseek-v4-flash` |
| Gateway | Unitalk LiteLLM |
| Upstream | Microsoft Azure, Europe |
| Fallback | Disabled |
| Default Web | Disabled |
| Candidate concurrency | 1 |
| Max model iterations | 50 circuit breaker |
| API retries | 1 |
| Token warning | 300,000 per candidate |
| Token escalation | 600,000 per candidate |
| Local token hard stop | None |
| Economic hard stop | Unitalk–Mustad prepaid balance; negative balance prohibited |

Credential values remain only in the isolated profile `.env` with mode `0600`; they are excluded from manifests and delivery packages.

## Skills

| Skill | Version | Release status |
|---|---|---|
{skill_rows}

## Operating rules

- One consolidated final human review after all permitted processing.
- `selected_named_contact` is separate from `relationship.target_role_priority`.
- An A1 High score may coexist with an A2 `held` state.
- Missing required evidence creates a visible gap, never an invented value or automatic ICP downgrade.
- Official-site Web access is disabled by default and requires candidate-specific activation.
- HubSpot, Twenty, n8n, Apify, outreach and durable downstream delivery remain disabled.

## Validation baseline

- Step 9A correction propagation: **15/15 PASS**.
- Step 9B offline regression: **10/10 PASS**.
- Offline suites/workflows: **11/11 PASS**.
- Operator compilation: **14/14 PASS**.
- Exact accepted-record replay: **2/2 PASS**.
- External actions: **0**.

## Status boundary

This package is a release candidate. It is not `PILOT_READY_NO_INTEGRATION`, production acceptance or contractual acceptance until Step 9D packaging and Step 9E approval are complete.
""",
    )

    write(
        runbook,
        """# Equinet A2 Manual No-Integration Runbook

**Release candidate:** `equinet-a2-no-integration-1.0.0-rc.1`

## 1. Preflight

1. Work only in `/opt/data/profiles/equinet-a2-enrichment`.
2. Require an approved A1 handoff and valid candidate snapshot hash.
3. Confirm the candidate-specific processing approval, reviewer and scope.
4. Confirm that the Unitalk gateway route is available without printing credentials.
5. Confirm fallback is disabled and the prepaid balance is below no-stop risk thresholds.
6. Keep HubSpot, Twenty, n8n, Apify, outreach and downstream delivery disabled.
7. Keep Web disabled unless a separate bounded source plan is approved for that candidate.

## 2. Intake and planning

Use absolute commands:

```bash
/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python \
  /opt/data/profiles/equinet-a2-enrichment/scripts/a2_intake.py <handoff.json> --output-dir <candidate-dir>

/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python \
  /opt/data/profiles/equinet-a2-enrichment/scripts/build_a2_gap_plan.py <request.json> --output <gap-plan.json>
```

Reuse approved A1 evidence first. Never recollect a verified current value without a named reason.

## 3. Conditional official-site research

Activate Web only for an approved candidate, allowed domain and named gap. Record the page/call/retry budget before access. Stop on terms or robots denial, login, paywall, CAPTCHA, HTTP 403/429, unexpected personal data or budget/scope limit. Search snippets are discovery-only. Do not open linked social profiles.

After collection, disable Web before classification, confidence, quality and review generation.

## 4. Verification and quality

```bash
/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python \
  /opt/data/profiles/equinet-a2-enrichment/scripts/normalise_and_validate_a2_observations.py \
  <observations.json> --output <validated-observations.json>

/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python \
  /opt/data/profiles/equinet-a2-enrichment/scripts/evaluate_a2_evidence_confidence.py \
  <evidence-request.json> --output <evidence-result.json>

/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python \
  /opt/data/profiles/equinet-a2-enrichment/scripts/evaluate_a2_minimum_package.py \
  <field-state-snapshot.json> --output <minimum-package-result.json>
```

A selected named contact may map to `secondary`. A `primary` role does not satisfy named-contactability without a verified named email or phone. A High A1 score does not override an incomplete A2 package.

## 5. Canonical revision and review

```bash
/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python \
  /opt/data/profiles/equinet-a2-enrichment/scripts/create_a2_revision.py \
  <previous.json> <proposed.json> --output <revision-result.json>

/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python \
  /opt/data/profiles/equinet-a2-enrichment/scripts/render_and_validate_a2_review_package.py \
  <record.json> --previous-record <previous.json> --output-dir <review-dir>
```

Present one consolidated final review containing field decisions, corrected values, the record decision, evidence, gaps, limitations and any exact future patch preview. Intermediate implementation checks are not runtime approval gates.

## 6. Decision outcomes

- `approved`: preserve the review receipt; no write follows without a separately approved guarded action.
- `held`: retain the record and named gaps; do not downgrade the A1 score.
- `needs_changes`: create a new immutable revision after authorised correction.
- `rejected`: record the reason without altering the A1 source snapshot.

## 7. Failures and recovery

- Never retry a full run automatically.
- Retry one failed source URL at most once when policy permits.
- Preserve the last validated artifact and resume from the first missing gate.
- Treat unavailable usage or cost as unknown, not zero.
- Use absolute paths in non-interactive sessions.
- If the gateway fails, save partial artifacts, stop and notify; fallback remains disabled.

## 8. Audit and closeout

Record actor, trigger, timestamp, source references, model/tool route, output, approval state, external actions, result, retries and usage. Verify zero unauthorised external actions and retain the authoritative canonical JSON plus validated review exports.
""",
    )

    write(
        evaluation,
        """# Equinet A2 Step 9 Evaluation Report

## Scope

Evaluation covers the accepted two-candidate Step 8 no-integration pilot, current offline regressions and exact no-Web replay. The sample is too small to establish production-level precision or commercial uplift.

## Candidate outcomes

| Candidate | A1 score/band | A2 outcome | Material result |
|---|---:|---|---|
| Jonabell Farm / Kate Galvin | 75 / High | Approved | Complete review package; selected named contact classified `secondary` |
| Rood & Riddle / Manfred Eckert | 80 / High | Held | Role and organisation-level disciplines verified; required status, service area and named contactability remain incomplete |

## Quality findings

- Canonical identity and A1 score lineage were preserved for both candidates.
- No candidate was forced to pass an A2 package because of a High A1 score.
- No purchasing authority, service area, employment status or contact detail was invented.
- The contact-form placeholder was excluded.
- One official-site contact-field allowlist mismatch was found and corrected.
- Review views remained lossless and consistent across Markdown, CSV and Excel.

## Regression and replay

- Step 9A: 15/15 controls passed.
- Step 9B: 10/10 controls passed.
- Offline suites and workflows: 11/11 passed.
- Operator compilation: 14/14 passed.
- Canonical byte equality: 2/2 passed.
- Derived export equality: passed.
- Web/provider/external actions during replay: 0/0/0.

## Consumption

The Rood & Riddle behavioural replay used 232,286 input tokens, 2,247 output tokens and 234,533 total tokens across 9 model API calls. The reported cost value was 0.0 but `cost_status` was `unknown`; cost is therefore undetermined.

The main optimisation opportunity is to avoid failed relative-path discovery and reduce repeated context loading. The release candidate requires absolute paths and records warning/escalation thresholds without imposing an arbitrary local token hard stop.

## Limitations

- Two candidates are insufficient for production quality claims.
- No live HubSpot, Twenty, n8n or Apify integration was tested.
- No CRM duplicate/customer/Deal/consent/suppression/owner state was authoritatively checked.
- No write, outreach, downstream delivery or production rollback was tested.
- Time saved and commercial impact were not measured against an Equinet baseline.
""",
    )

    write(
        open_items,
        """# Equinet A2 Open Items Register

| Item | Status | Blocks no-integration pilot | Blocks integrated/production use | Required owner/input |
|---|---|---:|---:|---|
| Real ten-person roster and A2 access assignments | To confirm with Equinet | No | Yes | Equinet |
| Named A2 primary and backup reviewers | To confirm with Equinet | No for Unitalk-controlled pilot | Yes | Equinet |
| Equinet business and provider-spend approvers | To confirm with Equinet | No | Yes | Equinet |
| Final Business Field Catalogue priorities and taxonomies | Working baseline pending Equinet confirmation | No | Yes | Equinet |
| HubSpot read OAuth and scopes | Integration pending | No | Yes | Equinet/Unitalk |
| HubSpot duplicate, customer, Deal, consent, suppression and owner checks | Integration pending | No | Yes | Equinet/Unitalk |
| Twenty workspace, schema, permissions and webhooks | Integration pending | No | Yes | Equinet/Unitalk |
| n8n orchestration, retries and durable receipts | Integration pending | No | Yes | Unitalk |
| Apify/HarvestAPI rights, vendor, account, build, retention and budget | Blocked pending review | No | Yes if activated | Unitalk/Equinet |
| DPA retention detail and administrator visibility | To confirm | No | Yes | Unitalk/Equinet |
| Gateway per-request telemetry and cost conversion | Partial; cost unknown | No | Yes for mature operations | Unitalk |
| Global prepaid-balance hard-stop evidence | To verify | No | Yes | Unitalk |
| Candidate scope beyond explicit approved runs | Approval required per run | No | Yes for scale | Equinet/Unitalk |
| Rood & Riddle professional status | Missing | Record remains held | N/A | Approved evidence or Equinet exception |
| Rood & Riddle service area | Missing | Record remains held | N/A | Approved evidence or Equinet exception |
| Rood & Riddle named professional email or phone | Missing | Record remains held | N/A | Approved evidence or contact-path exception |
| Success KPI baselines: time saved, correction rate and commercial outcome | Not measured | No | Yes for production acceptance | Equinet/Unitalk |

No open item authorises an external action or weakens source-system permissions.
""",
    )

    write(
        acceptance_review,
        """# Equinet A2 Step 9 Release-Candidate Acceptance Review

**Release candidate:** `equinet-a2-no-integration-1.0.0-rc.1`  
**Current status:** `READY FOR STEP 9D SAFE PACKAGING — NOT APPROVED OR ACTIVE`

## Proposed Step 9 decisions

| ID | Proposed decision |
|---|---|
| S9-1 | Approve release ID `equinet-a2-no-integration-1.0.0`. |
| S9-2 | Approve the ten-skill package, including the three corrected skills promoted from `0.1.1-rc.1` to `0.1.1`. |
| S9-3 | Approve No-Integration Runtime Policy `1.0.0`, with DeepSeek primary, fallback disabled and Web disabled by default. |
| S9-4 | Approve one consolidated final human review; intermediate implementation checkpoints are not runtime gates. |
| S9-5 | Approve the separation of selected named contact, target-role priority, named contactability and buying authority. |
| S9-6 | Approve the independent A1-score/A2-readiness rule, including High-score records remaining `held` when required A2 evidence is missing. |
| S9-7 | Approve monitoring warnings at 300,000 tokens/candidate and escalation at 600,000, with no arbitrary local hard stop and the global prepaid-balance hard stop preserved. |
| S9-8 | Accept all listed no-integration limitations and production blockers. |
| S9-9 | Authorise atomic promotion to `PILOT_READY_NO_INTEGRATION` only after Step 9D archive and integrity checks pass. |
| S9-10 | Confirm that Step 9 approval is not Equinet production acceptance or contractual delivery acceptance. |

No decision is recorded yet. Step 9D must complete before this package is presented for final approval.
""",
    )

    documents = [configuration, runbook, evaluation, open_items, acceptance_review]
    manifest = {
        "manifest_id": "equinet-a2-no-integration-release-candidate",
        "release_id": "equinet-a2-no-integration-1.0.0-rc.1",
        "version": "1.0.0-rc.1",
        "status": "ready_for_step9d_safe_packaging_not_approved",
        "profile": "equinet-a2-enrichment",
        "model": policy["model_routing"],
        "runtime_policy": {"path": str(RC_POLICY.relative_to(ROOT)), "sha256": sha(RC_POLICY)},
        "foundation_manifest": {"path": str(RC_FOUNDATION.relative_to(ROOT)), "sha256": sha(RC_FOUNDATION)},
        "component_inventory": {
            "path": str(INVENTORY.relative_to(ROOT)),
            "sha256": sha(INVENTORY),
            "count": inventory["counts"]["total"],
            "missing": inventory["counts"]["missing"],
            "unversioned": inventory["counts"]["unversioned"],
            "items": inventory["items"],
        },
        "validated_steps": {
            "step8_acceptance": {"path": str(STEP8.relative_to(ROOT)), "sha256": sha(STEP8)},
            "step9a": {"path": str(PHASE9A.relative_to(ROOT)), "sha256": sha(PHASE9A), "checks": "15/15"},
            "step9b": {"path": str(PHASE9B.relative_to(ROOT)), "sha256": sha(PHASE9B), "checks": "10/10"},
            "language_audit": {"path": str(LANGUAGE.relative_to(ROOT)), "sha256": sha(LANGUAGE), "files_checked": language.get("files_checked"), "findings": len(language.get("findings", []))},
        },
        "documents": [{"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha(path)} for path in documents],
        "permissions": foundation["permissions"],
        "unavailable_integrations": ["HubSpot read/write", "Twenty", "n8n", "Apify/HarvestAPI", "outreach", "durable A1/A3/A14 delivery"],
        "prohibited_actions": ["CRM write", "external communication", "outreach", "A1 score mutation", "consent inference", "unapproved source access", "negative prepaid balance"],
        "open_items_register": str(open_items.relative_to(ROOT)),
        "promotion_performed": False,
        "approval_recorded": False,
        "next_gate": "Step 9D — Safe Archive and Independent Verification",
        "external_actions": 0,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    checks = {
        "phase9a": phase9a["status"] == "pass_ready_for_step9b" and phase9a["checks_passed"] == phase9a["checks_total"] == 15,
        "phase9b": phase9b["status"] == "pass_ready_for_step9c" and phase9b["checks_passed"] == phase9b["checks_total"] == 10,
        "language_audit": language.get("pass") is True,
        "inventory_complete": inventory["counts"]["missing"] == inventory["counts"]["unversioned"] == 0,
        "foundation_hashes": all((ROOT / item["path"]).exists() and sha(ROOT / item["path"]) == item["sha256"] for item in foundation["active_files"]),
        "documents": all(path.exists() and path.stat().st_size > 0 for path in documents),
        "web_disabled": "web" not in config and "web" not in config.get("platform_toolsets", {}).get("cli", []),
        "fallback_disabled": config.get("fallback_providers") == [],
        "not_promoted": manifest["promotion_performed"] is False and manifest["approval_recorded"] is False,
        "external_actions_zero": manifest["external_actions"] == 0,
    }
    validation = {
        "record_type": "step9c_delivery_package_validation",
        "profile": "equinet-a2-enrichment",
        "status": "pass_ready_for_step9d" if all(checks.values()) else "failed",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "manifest_sha256": sha(MANIFEST),
        "documents": len(documents),
        "external_actions": 0,
        "errors": [key for key, value in checks.items() if not value],
    }
    validation_path = STEP9 / "phase9c-validation.json"
    validation_path.write_text(json.dumps(validation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    plan = load(PLAN)
    for phase in plan["phases"]:
        if phase["id"] == "9C":
            phase["status"] = "completed" if all(checks.values()) else "blocked"
        elif phase["id"] == "9D" and all(checks.values()):
            phase["status"] = "ready"
    plan["status"] = "step9c_completed_ready_for_step9d" if all(checks.values()) else "step9c_blocked"
    PLAN.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": validation["status"], "checks": f"{validation['checks_passed']}/{validation['checks_total']}", "documents": len(documents), "inventory": inventory["counts"], "manifest": str(MANIFEST.relative_to(ROOT)), "promotion_performed": False, "external_actions": 0}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
