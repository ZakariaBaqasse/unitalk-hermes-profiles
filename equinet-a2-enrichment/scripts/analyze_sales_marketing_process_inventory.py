#!/usr/bin/env python3
"""Profile Equinet's HubSpot Sales and Marketing process inventory."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

SOURCE = Path("/opt/data/profiles/equinet/attachments/Sales_Marketing_Process_Inventory.csv")
OUTPUT = Path("/opt/data/profiles/equinet-a2-enrichment/evaluations/hubspot-intake/process-inventory-summary.json")


def main() -> None:
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    by_category = Counter(row["Category"] for row in rows)
    by_asset_type = Counter(row["Asset type"] for row in rows)
    by_status = Counter(row["Status or list type"] for row in rows)
    enabled_workflows = [row for row in rows if row["Asset type"] == "Workflow" and row["Status or list type"] == "Enabled"]
    disabled_workflows = [row for row in rows if row["Asset type"] == "Workflow" and row["Status or list type"] == "Disabled"]
    lists = [row for row in rows if row["Asset type"] == "List"]
    audit_findings = [row for row in rows if row["Asset type"] == "Audit finding"]

    side_effect_terms = {
        "sends_external_communication": ["sends an app download invite email", "sends a referral email", "resends the email"],
        "creates_tasks": ["creates a call task", "creates a follow-up task", "creates high-priority follow-up tasks", "creates a task"],
        "updates_status_or_subscription": ["updates sms subscription status", "sets app engagement status", "moves approved", "updates the sample request stage"],
        "creates_records": ["creates sample requests", "creates a note"],
    }
    side_effects = defaultdict(list)
    for row in enabled_workflows:
        description = row["Description"].lower()
        for effect, terms in side_effect_terms.items():
            if any(term in description for term in terms):
                side_effects[effect].append(row["Name"])

    category_detail = {}
    for category in sorted(by_category):
        items = [row for row in rows if row["Category"] == category]
        category_detail[category] = {
            "count": len(items),
            "asset_types": dict(Counter(row["Asset type"] for row in items)),
            "statuses": dict(Counter(row["Status or list type"] for row in items)),
            "names": [row["Name"] for row in items],
        }

    result = {
        "source": str(SOURCE),
        "rows": len(rows),
        "categories": dict(by_category),
        "asset_types": dict(by_asset_type),
        "statuses": dict(by_status),
        "enabled_workflow_count": len(enabled_workflows),
        "disabled_workflow_count": len(disabled_workflows),
        "list_count": len(lists),
        "audit_finding_count": len(audit_findings),
        "enabled_workflow_side_effects": dict(side_effects),
        "audit_findings": [
            {
                "category": row["Category"],
                "name": row["Name"],
                "status": row["Status or list type"],
                "description": row["Description"],
            }
            for row in audit_findings
        ],
        "category_detail": category_detail,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "rows": len(rows),
        "categories": dict(by_category),
        "asset_types": dict(by_asset_type),
        "statuses": dict(by_status),
        "enabled_workflows": len(enabled_workflows),
        "disabled_workflows": len(disabled_workflows),
        "lists": len(lists),
        "audit_findings": len(audit_findings),
        "output": str(OUTPUT),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
