#!/usr/bin/env python3
"""Validate Step 3E protected fields and conflict handling."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import sys
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROFILE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from evaluate_a2_protected_field_action import evaluate  # noqa: E402

POLICY = PROFILE_ROOT / "foundations" / "contracts" / "governance" / "a2-protected-fields-and-conflict-policy-0.1.0-draft.1.json"
FIXTURES = PROFILE_ROOT / "evaluations" / "step3e" / "fixtures" / "cases.json"
PROPERTY_CSV = Path("/opt/data/profiles/equinet/attachments/Property_Definitions (1).csv")
CONTRACT = PROFILE_ROOT / "foundations" / "A2-PROTECTED-FIELDS-AND-CONFLICT-POLICY.md"
ROOT = PROFILE_ROOT / "evaluations" / "step3e"
REVIEW = ROOT / "A2-PROTECTED-FIELDS-CONFLICT-REVIEW.md"
OUTPUT = ROOT / "technical-validation.json"
MANIFEST = ROOT / "step3e-draft-package-manifest.json"
LANGUAGE = PROFILE_ROOT / "evaluations" / "foundation-clarifications" / "language-audit.json"
BUILDER = SCRIPTS / "build_step3e_protected_fields.py"
EVALUATOR = SCRIPTS / "evaluate_a2_protected_field_action.py"
VALIDATOR = Path(__file__).resolve()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metadata_index() -> set[tuple[str, str]]:
    with PROPERTY_CSV.open(encoding="utf-8-sig", newline="") as handle:
        return {(row["Object"], row["Internal name"]) for row in csv.DictReader(handle)}


def validate_policy(policy: dict) -> list[str]:
    errors = []
    if policy.get("status") != "approved_by_unitalk_as_working_baseline_pending_equinet_confirmation":
        errors.append("policy status must be the approved Unitalk working baseline pending Equinet confirmation")
    approval = policy.get("unitalk_approval", {})
    if approval.get("approver") != "Séverine, Unitalk Operations" or approval.get("scope") != "decisions_3E_1_through_3E_10":
        errors.append("Unitalk approval metadata is invalid")
    for dep in policy.get("dependencies", []):
        path = Path(dep["path"]) if str(dep["path"]).startswith("/") else PROFILE_ROOT / dep["path"]
        if not path.exists() or sha256(path) != dep["sha256"]:
            errors.append(f"dependency hash mismatch: {dep['path']}")
    classes = policy.get("protection_classes", {})
    expected_classes = {"authoritative_control", "system_read_only", "owner_and_routing", "manual_business_value", "a2_enrichment_candidate", "review_only_personal_data", "prohibited_personal_or_sensitive"}
    if set(classes) != expected_classes:
        errors.append("protection class set mismatch")
    confirmed = metadata_index()
    protected = policy.get("hubspot_protected_fields", [])
    pairs = [(item["object"], item["property"]) for item in protected]
    if len(pairs) != len(set(pairs)):
        errors.append("duplicate protected HubSpot field")
    for pair in pairs:
        if pair not in confirmed:
            errors.append(f"protected field not found in supplied HubSpot metadata: {pair[0]}.{pair[1]}")
    rules = policy.get("global_rules", {})
    for key in ["existing_manual_value_preserved", "protected_field_never_overwritten_automatically", "null_or_missing_connector_reference_is_not_a_negative_check_result", "workflow_dependency_verification_required_before_write", "list_membership_impact_verification_required_before_write", "idempotency_receipt_and_readback_required_for_future_write", "a1_snapshot_never_mutated", "a2_numeric_score_change_prohibited"]:
        if rules.get(key) is not True:
            errors.append(f"required protection rule missing: {key}")
    if rules.get("current_hubspot_write_authorized") is not False:
        errors.append("HubSpot write authority must remain false")
    workflow = policy.get("workflow_dependency_gate", {})
    if workflow.get("enabled_workflows_observed") != 28 or workflow.get("lists_observed") != 32:
        errors.append("workflow/list inventory count mismatch")
    if workflow.get("exact_trigger_action_dependencies_verified") is not False or workflow.get("write_action") != "blocked":
        errors.append("workflow dependency gate was weakened")
    required_exception = {"field_key", "current_value", "proposed_value", "evidence_ids", "reason", "approval_matrix_version", "reviewer_id", "reviewer_role", "approved_at", "approved_action", "scope", "expiry_or_single_use", "workflow_dependency_status"}
    if set(policy.get("field_level_exception_requirements", [])) != required_exception:
        errors.append("field-level exception requirements mismatch")
    return errors


def negative_cases(policy: dict) -> list[dict]:
    cases = []
    def run(name, expected, fn):
        value = copy.deepcopy(policy); fn(value); errs = validate_policy(value)
        cases.append({"name": name, "expected_error": expected, "errors": errs, "passed": any(expected in error for error in errs)})
    run("dependency_hash", "dependency hash mismatch", lambda v: v["dependencies"][0].update(sha256="0" * 64))
    run("unknown_protected_field", "not found in supplied HubSpot metadata", lambda v: v["hubspot_protected_fields"].append({"object":"Contact","property":"invented_field","class":"authoritative_control","reason":"test"}))
    run("duplicate_protected_field", "duplicate protected HubSpot field", lambda v: v["hubspot_protected_fields"].append(copy.deepcopy(v["hubspot_protected_fields"][0])))
    run("manual_overwrite_enabled", "required protection rule missing", lambda v: v["global_rules"].update(existing_manual_value_preserved=False))
    run("hubspot_write_enabled", "write authority must remain false", lambda v: v["global_rules"].update(current_hubspot_write_authorized=True))
    run("workflow_gate_bypassed", "workflow dependency gate was weakened", lambda v: v["workflow_dependency_gate"].update(exact_trigger_action_dependencies_verified=True, write_action="allowed"))
    run("exception_reviewer_removed", "exception requirements mismatch", lambda v: v["field_level_exception_requirements"].remove("reviewer_id"))
    run("a1_mutation_enabled", "required protection rule missing", lambda v: v["global_rules"].update(a1_snapshot_never_mutated=False))
    run("approval_removed", "Unitalk approval metadata is invalid", lambda v: v["unitalk_approval"].update(scope="draft_only"))

    return cases


def render(policy: dict, cases: list[dict]) -> None:
    classes = "\n".join(f"| `{name}` | `{value['default_action']}` | {'Yes' if value['exception_allowed'] else 'No'} |" for name, value in policy["protection_classes"].items())
    fields = "\n".join(f"| {item['object']} | `{item['property']}` | `{item['class']}` | {item['reason']} |" for item in policy["hubspot_protected_fields"])
    outcomes = "\n".join(f"| `{item['name']}` | `{item['recommended_action']}` | {'Yes' if item['baseline_preserved'] else 'No'} | {'PASS' if item['passed'] else 'FAIL'} |" for item in cases)
    contract = f"""# Equinet A2 Protected Fields and Conflict Policy

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING`  
**Decision timestamp:** `2026-08-26T19:39:20Z`  
**Profile:** `equinet-a2-enrichment`  
**Step:** `3E — Protected Fields and Conflict Policy`

## 1. Core boundary

A2 may observe and propose. It does not silently overwrite an existing manual value, an authoritative control, a system-managed field, an owner or an A1 snapshot. HubSpot write authority remains false.

## 2. Protection classes

| Class | Default action | Exception possible |
|---|---|---:|
{classes}

## 3. Confirmed HubSpot protected-field candidates

| Object | Internal property | Class | Reason |
|---|---|---|---|
{fields}

These fields were found in the supplied HubSpot metadata. Their presence does not prove live values, permissions or write safety.

## 4. Manual value policy

- Same value: no change.
- Empty unprotected baseline plus verified proposal: propose an addition for human review.
- Different manual or protected baseline: preserve the baseline, record the conflict and hold.
- No silent overwrite or clear.

## 5. Conflict precedence

Consent, suppression, customer, lifecycle, Deal, sequence and system-read-only states remain authoritative. Authorised first-party records and existing manual CRM values take precedence over non-authoritative enrichment. Official business-site facts may support a proposal, but a material disagreement remains visible and requires review.

## 6. Future exception record

A field-level exception must record the field, current and proposed values, evidence, reason, approval-matrix version, reviewer identity and role, time, approved action, scope, expiry or single-use state, and workflow-dependency status.

## 7. Workflow-side-effect gate

The supplied inventory contains 28 enabled workflows and 32 lists. Exact trigger/action and membership effects have not been verified. Every future write remains blocked until dependencies, approval, idempotency, receipt, read-back and rollback are validated.

## 8. Decision boundary

Séverine approved decisions 3E-1 through 3E-10 as the Unitalk working baseline. Step 3F may begin in draft form. This approval does not authorise a CRM connection, write, owner reassignment, consent change, outreach, pilot or production action.
"""
    CONTRACT.write_text(contract, encoding="utf-8")
    review = f"""# Decision Review — Step 3E Protected Fields and Conflict Policy

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED AS UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING`  
**Decision timestamp:** `2026-08-26T19:39:20Z`

## Decisions approved as the Unitalk working baseline

| ID | Proposed decision |
|---|---|
| 3E-1 | Treat consent, suppression, customer, lifecycle, Deal and sequence fields as authoritative controls or system-read-only. |
| 3E-2 | Preserve all populated manual CRM values; A2 may propose but never silently overwrite. |
| 3E-3 | Preserve owner fields and route unresolved assignments to `needs_owner_review`. |
| 3E-4 | Treat `contact_verified`, `data_quality` and `mailing_verified` as protected mapping candidates until semantics are approved. |
| 3E-5 | Apply the documented conflict-precedence order while preserving every conflict in the audit trail. |
| 3E-6 | Require a complete field-level exception record for any future protected-field change. |
| 3E-7 | Block every write while workflow or list dependencies remain unverified. |
| 3E-8 | Require future approved writes to be idempotent, receipted, read back and reconcilable. |
| 3E-9 | Keep the A1 snapshot immutable and route score-related evidence through requalification. |
| 3E-10 | Keep current HubSpot write authority false. |

## Deterministic outcomes

| Case | Action | Baseline preserved | Test |
|---|---|---:|---:|
{outcomes}

## Approval scope

This approval establishes the Unitalk working baseline and authorises Step 3F draft preparation. Equinet action-level approvers, protected-field exceptions and workflow dependencies remain pending.
"""
    REVIEW.write_text(review, encoding="utf-8")


def main() -> int:
    policy = load(POLICY)
    errors = validate_policy(policy)
    results = []
    for item in load(FIXTURES)["cases"]:
        result = evaluate(item, policy)
        passed = result["recommended_action"] == item["expected_action"] and not result["errors"] and not result["external_write_allowed"] and not result["a1_score_changed"]
        results.append({"name": item["name"], **result, "expected_action": item["expected_action"], "passed": passed})
        if not passed:
            errors.append(f"fixture failed: {item['name']}")
    negative = negative_cases(policy)
    if any(not item["passed"] for item in negative):
        errors.append("negative regression failed")
    render(policy, results)
    docs = {"contract_version": "**Version:** `0.1.0-draft.1`" in CONTRACT.read_text(), "review_pending": "APPROVED AS UNITALK WORKING BASELINE — EQUINET CONFIRMATION PENDING" in REVIEW.read_text(), "decisions": all(f"| 3E-{n} |" in REVIEW.read_text() for n in range(1,11)), "write_block": "Every future write remains blocked" in CONTRACT.read_text()}
    if not all(docs.values()): errors.append("documentation check failed")
    language = load(LANGUAGE)
    if language.get("pass") is not True: errors.append("language audit failed")
    result = {"step":"3E","version":policy["version"],"approval_state":"approved_unitalk_working_baseline_pending_equinet_confirmation","policy":{"path":str(POLICY.relative_to(PROFILE_ROOT)),"sha256":sha256(POLICY)},"protected_field_count":len(policy["hubspot_protected_fields"]),"policy_validation":{"errors":validate_policy(policy),"passed":not validate_policy(policy)},"fixtures":{"total":len(results),"passed":sum(x["passed"] for x in results),"cases":results},"negative_regressions":{"total":len(negative),"passed":sum(x["passed"] for x in negative),"cases":negative},"documentation_checks":docs,"language_audit":{"files_checked":language.get("files_checked"),"findings":len(language.get("findings",[])),"passed":language.get("pass") is True},"hubspot_write_authorized":False,"external_actions":0,"next_gate_after_approval":"Step 3F — Provider and Cost Policy","failures":errors,"pass":not errors}
    ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    paths=[POLICY,FIXTURES,BUILDER,EVALUATOR,VALIDATOR,CONTRACT,REVIEW,OUTPUT]
    manifest={"manifest_id":"equinet-a2-step3e-draft-package","version":policy["version"],"status":"approved_unitalk_working_baseline_pending_equinet_confirmation","files":[{"path":str(p.relative_to(PROFILE_ROOT)),"bytes":p.stat().st_size,"sha256":sha256(p)} for p in paths],"file_count":len(paths),"external_actions":0}
    MANIFEST.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"pass":result["pass"],"approval_state":result["approval_state"],"protected_fields":result["protected_field_count"],"fixtures":f"{result['fixtures']['passed']}/{result['fixtures']['total']}","negative":f"{result['negative_regressions']['passed']}/{result['negative_regressions']['total']}","review":str(REVIEW),"failures":errors},indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
