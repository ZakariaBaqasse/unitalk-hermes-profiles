#!/usr/bin/env python3
"""Refresh dependency hashes for the active A2 FullEnrich foundation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dep(path: str) -> dict[str, str]:
    return {"path": path, "sha256": sha(ROOT / path)}


def main() -> int:
    decision_rel = "foundations/decisions/A2-FULLENRICH-SOURCE-ROUTING-20260906.json"
    cat_rel = "foundations/contracts/business/a2-business-field-catalogue-0.3.0.json"
    min_rel = "foundations/contracts/business/a2-minimum-data-packages-0.3.0.json"
    source_rel = "foundations/contracts/sources/a2-source-register-0.3.0.json"
    evidence_rel = "foundations/contracts/evidence/a2-evidence-verification-confidence-freshness-policy-0.3.0.json"
    provider_rel = "foundations/contracts/governance/a2-provider-and-cost-policy-0.3.0.json"
    protected_rel = "foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.3.0.json"
    mapping_rel = "foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.3.0.json"
    integration_rel = "foundations/contracts/integrations/a2-fullenrich-n8n-integration-0.1.0.json"

    source = load(ROOT / source_rel)
    source["decision_record"] = dep(decision_rel)
    dump(ROOT / source_rel, source)

    catalogue = load(ROOT / cat_rel)
    catalogue["decision_record"] = dep(decision_rel)
    dump(ROOT / cat_rel, catalogue)

    minimum = load(ROOT / min_rel)
    minimum["business_field_catalogue"] = {**dep(cat_rel), "version": "0.3.0", "status": catalogue["status"]}
    dump(ROOT / min_rel, minimum)

    evidence = load(ROOT / evidence_rel)
    evidence["dependencies"] = [
        dep(source_rel), dep(cat_rel), dep("foundations/contracts/a2-state-model-0.1.0.json"), dep(decision_rel)
    ]
    dump(ROOT / evidence_rel, evidence)

    protected = load(ROOT / protected_rel)
    for item in protected["dependencies"]:
        if "business-field-catalogue" in item["path"]:
            item.update(dep(cat_rel))
        elif "evidence-verification-confidence" in item["path"]:
            item.update(dep(evidence_rel))
    dump(ROOT / protected_rel, protected)

    provider = load(ROOT / provider_rel)
    provider["dependencies"] = [dep(source_rel), dep(decision_rel)]
    dump(ROOT / provider_rel, provider)

    mapping = load(ROOT / mapping_rel)
    for item in mapping["dependencies"]:
        if "business-field-catalogue" in item["path"]:
            item.update(dep(cat_rel))
    dump(ROOT / mapping_rel, mapping)

    integration = load(ROOT / integration_rel)
    integration["dependencies"] = [dep(source_rel), dep(provider_rel), dep(cat_rel), dep(decision_rel)]
    dump(ROOT / integration_rel, integration)

    print(json.dumps({"status": "pass", "refreshed": [source_rel, cat_rel, min_rel, evidence_rel, protected_rel, provider_rel, mapping_rel, integration_rel]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
