#!/usr/bin/env python3
"""Render human-readable Step 2B field dictionary and state-model documents."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = PROFILE_ROOT / "foundations" / "contracts"
FIELD_CSV = CONTRACTS / "a2-field-dictionary-0.1.0.csv"
STATE_JSON = CONTRACTS / "a2-state-model-0.1.0.json"
FIELD_MD = PROFILE_ROOT / "foundations" / "A2-FIELD-DICTIONARY.md"
STATE_MD = PROFILE_ROOT / "foundations" / "A2-STATE-MODEL.md"

SECTION_PURPOSE = {
    "record_metadata": "Stable record/revision identity, run and audit correlation.",
    "source_handoff": "Immutable accepted A1-to-A2 envelope and source snapshot.",
    "subject": "A2-resolved people, organisations and relationships.",
    "enrichment_scope": "Requested field package, policy versions, scope and run limits.",
    "field_assessments": "Generic baseline, observations, proposal, field review and application state.",
    "evidence_registry": "A2-native evidence and references to reused A1 evidence.",
    "data_quality": "Deterministic completeness, gap, conflict, stale and invalid-field summary.",
    "duplicate_and_eligibility": "Separate duplicate, CRM eligibility, outreach and owner-routing visibility.",
    "requalification": "A2 signals/returns and authoritative A1 score-revision references.",
    "review": "Record-level human decision and requested changes.",
    "workflow": "Controlled A2 lifecycle state and transition evidence.",
    "system_references": "Connector-controlled A1, HubSpot, Twenty, n8n, provider and downstream IDs.",
    "governance": "Purpose, personal-data, source, consent, retention, approval and action guards.",
    "audit_and_consumption": "Append-only run, tool, model, usage, cost, error and external-action events.",
}


def escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def main() -> None:
    with FIELD_CSV.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    model = json.loads(STATE_JSON.read_text(encoding="utf-8"))
    counts = Counter(row["section"] for row in rows)

    field_lines = [
        "# Equinet A2 Canonical Field Dictionary",
        "",
        "**Version:** `0.1.0`  ",
        "**Status:** `APPROVED BY UNITALK OPERATIONS FOR STEP 2C`  ",
        "**Decision:** `APPROVED AS DRAFTED`  ",
        "**Approver:** Séverine, Unitalk Operations  ",
        "**Decision timestamp:** `2026-08-25T22:20:22Z`  ",
        "**Detailed machine-readable dictionary:** `contracts/a2-field-dictionary-0.1.0.csv`",
        "",
        "## 1. Purpose",
        "",
        "This dictionary defines the stable structural fields of the canonical A2 Enrichment Record before JSON Schema is authored. It does not define the business field catalogue such as email, service area, certifications or horse count; those fields are referenced generically through `field_assessments[].field_key`.",
        "",
        "## 2. Dictionary columns",
        "",
        "- `section` — approved canonical section.",
        "- `field_path` — unique future JSON path.",
        "- `data_type` — intended canonical type before final JSON Schema syntax.",
        "- `required` — yes, no or conditional.",
        "- `nullable` — whether explicit null is valid.",
        "- `cardinality` — one, zero-or-one, zero-or-more or one-or-more.",
        "- `producer` — actor, script, reviewer or connector that creates the value.",
        "- `authority` — source that controls the business meaning or final result.",
        "- `mutability` — immutable, append-only, derived, human-controlled, external-authoritative or connector-controlled.",
        "- `state_vocabulary` — exact vocabulary defined in the State Model where applicable.",
        "",
        "## 3. Section inventory",
        "",
        "| Section | Field paths | Purpose |",
        "|---|---:|---|",
    ]
    for section in SECTION_PURPOSE:
        field_lines.append(f"| `{section}` | {counts[section]} | {SECTION_PURPOSE[section]} |")

    field_lines += [
        "",
        f"**Total field paths:** {len(rows)}",
        "",
        "## 4. Core ownership rules",
        "",
        "- `source_handoff.*` is immutable and remains owned by the accepted A1 handoff.",
        "- `field_assessments[].baseline` mirrors the authoritative value known before the current proposal.",
        "- `observations[]` is append-only and preserves every permitted material observation, including contradictions.",
        "- A2 may create at most one `proposed_resolution` per field assessment and revision.",
        "- The authorised human controls `field_review` and `review.record_decision`.",
        "- Approval is separate from `application`; only an authorised connector can record an applied external action.",
        "- Every future external-system ID is nullable except the A1 candidate and handoff IDs; null never means checked or absent.",
        "- A2 creates requalification signals, but only A1 may produce a numeric score revision.",
        "- Source, minimum-package, confidence, freshness, retention and HubSpot mapping rules remain separate versioned configurations.",
        "",
        "## 5. Baseline, observation, proposal, decision and application",
        "",
        "```text",
        "baseline = value known before the current A2 proposal",
        "observations = permitted values collected or reused during enrichment",
        "proposed_resolution = one evidence-led recommendation",
        "field_review = human decision",
        "application = separate verified external action state",
        "```",
        "",
        "A baseline is never silently overwritten. A reviewer correction or approved external result creates a new immutable record revision.",
        "",
        "## 6. Required A1 and external references",
        "",
        "- `system_references.a1_candidate_id` and `system_references.a1_handoff_id` are required and non-nullable.",
        "- HubSpot, Twenty, n8n, provider, A3, A14 and sync references remain nullable until a connector verifies them.",
        "- The exact HubSpot property mapping is not part of this dictionary.",
        "",
        "## 7. Open items",
        "",
        "- Business field keys and Required/Optional/Do Not Collect decisions.",
        "- Farrier and Horse Owner minimum packages.",
        "- Evidence, verification, confidence and freshness calculations.",
        "- Protected-field catalogue and field-specific conflict rules.",
        "- A2 source register and provider approvals.",
        "- HubSpot/Twenty mappings and workflow dependency register.",
        "- Named A2 reviewer and backup.",
        "",
        "## 8. Step 2B approval boundary",
        "",
        "Approval of this dictionary authorises Step 2C and later JSON Schema authoring. It does not approve business fields, sources, integrations, live enrichment, CRM writes, outreach, pilot or production use.",
    ]
    FIELD_MD.write_text("\n".join(field_lines) + "\n", encoding="utf-8")

    state_lines = [
        "# Equinet A2 Canonical State Model",
        "",
        "**Version:** `0.1.0`  ",
        "**Status:** `APPROVED BY UNITALK OPERATIONS FOR STEP 2C`  ",
        "**Decision:** `APPROVED AS DRAFTED`  ",
        "**Approver:** Séverine, Unitalk Operations  ",
        "**Decision timestamp:** `2026-08-25T22:20:22Z`  ",
        "**Machine-readable vocabulary:** `contracts/a2-state-model-0.1.0.json`",
        "",
        "## 1. Purpose",
        "",
        "This model defines exact, non-interchangeable states for A2 data, review, workflow, eligibility, application and requalification. HubSpot Lifecycle, Lead, Deal and other portal states remain external mapping references and never become A2 workflow states.",
        "",
        "## 2. Critical semantic distinctions",
        "",
        "| State | Meaning |",
        "|---|---|",
        "| `unknown` | No reliable value is known after the applicable evaluation; do not infer one. |",
        "| `not_checked` | No attempt has been made. |",
        "| `unavailable` | The source, field, account or integration cannot be used in the current run. |",
        "| `not_found` | A check completed successfully but found no value. |",
        "| `error` | The check was attempted but failed technically. |",
        "| `gap` | A required/requested field remains unsatisfied after applying the relevant rules. |",
        "| `conflict` | Material permitted values disagree and require resolution. |",
        "| `stale` | A value exceeds its field-specific age or recheck rule. |",
        "",
        "These states must not be collapsed into a single blank or false value.",
        "",
        "## 3. Canonical vocabularies",
    ]

    for vocab_name, vocabulary in model["canonical_vocabularies"].items():
        state_lines += [
            "",
            f"### `{vocab_name}`",
            "",
            f"**Owner:** {vocabulary['owner']}",
            "",
            "| Value | Meaning |",
            "|---|---|",
        ]
        for item in vocabulary["values"]:
            state_lines.append(f"| `{escape(item['value'])}` | {escape(item['meaning'])} |")

    state_lines += [
        "",
        "## 4. A2 workflow transitions",
        "",
        "| From | Allowed next states |",
        "|---|---|",
    ]
    for source, targets in model["transition_models"]["workflow_state"].items():
        rendered = ", ".join(f"`{target}`" for target in targets) if targets else "Terminal"
        state_lines.append(f"| `{source}` | {rendered} |")

    state_lines += [
        "",
        "### No-integration ceiling",
        "",
        "A `manual_no_integration_pilot` record may be human-approved and closed for review purposes, but it cannot enter `ready_for_sync`, `sync_pending`, `synced` or `reconciled`.",
        "",
        "## 5. External HubSpot state references",
        "",
        "The following are external source-system states, not canonical A2 workflow states:",
        "",
        "- HubSpot Lifecycle Stage;",
        "- HubSpot Lead Status;",
        "- Deal Pipeline and Deal Stage;",
        "- Company Account Status;",
        "- Sample Request Pipeline and Approval Status;",
        "- Ticket Pipeline.",
        "",
        "Known limitations:",
        "",
        "- `Rename 1` is an unresolved Ticket-stage placeholder.",
        "- Company Account Status values `Block` and `Ship` lack approved A2 business meaning.",
        "- owner-assignment and backup-owner rules are unavailable.",
        "- no HubSpot enrichment-review asset exists.",
        "- workflow field/list dependencies remain unverified.",
        "",
        "## 6. Cross-state rules",
        "",
    ]
    for rule in model["cross_state_rules"]:
        state_lines.append(f"- {rule}")

    state_lines += [
        "",
        "## 7. Step 2B approval boundary",
        "",
        "Approval of these vocabularies authorises their use in Step 2C and Step 2D. It does not approve field-specific business rules, confidence thresholds, source activation, HubSpot mapping, external actions, pilot or production use.",
    ]
    STATE_MD.write_text("\n".join(state_lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "field_document": str(FIELD_MD),
        "state_document": str(STATE_MD),
        "field_rows": len(rows),
        "vocabularies": len(model["canonical_vocabularies"]),
    }, indent=2))


if __name__ == "__main__":
    main()
