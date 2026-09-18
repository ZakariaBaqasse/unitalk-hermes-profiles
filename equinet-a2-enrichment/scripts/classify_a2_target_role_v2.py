#!/usr/bin/env python3
"""Classify an Equinet A2 current role using the confirmed 0.3.1 role model."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOGUE = ROOT / "foundations/contracts/business/a2-business-field-catalogue-0.3.1.json"

ALIASES = {
    "farrier": {
        "primary": {
            "independent_self_employed_farrier": ["independent farrier", "self employed farrier", "self-employed farrier"],
            "farrier_business_owner": ["farrier business owner", "owner"],
            "farrier_business_founder_cofounder": ["founder", "co founder", "co-founder"],
            "lead_head_farrier": ["lead farrier", "head farrier"],
            "professional_farrier": ["professional farrier", "farrier"],
        },
        "secondary": {
            "associate_staff_farrier": ["associate farrier", "staff farrier"],
            "multi_farrier_practice_farrier": ["farrier at a multi farrier practice", "farrier at a multi-farrier practice"],
            "business_office_practice_manager_with_commercial_responsibility": ["business manager", "office manager", "practice manager"],
        },
        "review_only": {"apprentice_student_farrier": ["apprentice farrier", "student farrier"]},
        "excluded": {
            "farrier_instructor_educator_without_current_commercial_activity": ["farrier school instructor", "farrier educator", "instructor", "educator"],
            "retired_inactive_farrier_without_current_professional_activity": ["retired farrier", "inactive farrier", "retired", "inactive"],
        },
    },
    "horse_owner": {
        "primary": {
            "owner_horse_owner": ["owner", "horse owner"],
            "farm_owner_manager": ["farm owner", "farm manager"],
            "stable_owner_manager": ["stable owner", "stable manager"],
            "equestrian_centre_owner_manager": ["equestrian centre owner", "equestrian center owner", "equestrian centre manager", "equestrian center manager"],
            "breeding_farm_owner_manager": ["breeding farm owner", "breeding manager"],
            "equine_business_managing_director_general_manager": ["managing director", "general manager"],
            "operations_manager_with_horse_care_or_purchasing_responsibility": ["operations manager"],
        },
        "secondary": {
            "head_trainer_head_coach": ["head trainer", "head coach"],
            "trainer_professional_rider": ["trainer", "professional rider"],
            "barn_yard_manager": ["barn manager", "yard manager"],
            "equine_program_manager": ["equine program manager", "equine programme manager"],
            "purchasing_procurement_manager": ["purchasing manager", "procurement manager"],
            "assistant_manager_operations_coordinator_with_purchasing_responsibility": ["assistant manager", "operations coordinator"],
        },
        "review_only": {},
        "excluded": {},
    },
}

CONDITIONS = {
    "business_office_practice_manager_with_commercial_responsibility": "commercial_or_purchasing_responsibility_required",
    "operations_manager_with_horse_care_or_purchasing_responsibility": "horse_care_or_purchasing_responsibility_required",
    "assistant_manager_operations_coordinator_with_purchasing_responsibility": "purchasing_responsibility_required",
    "farrier_instructor_educator_without_current_commercial_activity": "exclude_only_when_no_current_commercial_or_professional_farrier_activity",
    "retired_inactive_farrier_without_current_professional_activity": "exclude_only_when_no_current_professional_activity",
}


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def classify(request: dict[str, Any]) -> dict[str, Any]:
    segment = request.get("segment")
    title = request.get("source_role_title")
    evidence_flags = set(request.get("evidence_flags") or [])
    if segment not in ALIASES or not isinstance(title, str) or not title.strip():
        return {"status": "invalid", "priority": None, "canonical_role": None, "source_role_title": title, "reason": "segment and source_role_title are required", "human_review_required": True}
    normalized = norm(title)
    matches = []
    for priority, groups in ALIASES[segment].items():
        for role_id, aliases in groups.items():
            if normalized in {norm(alias) for alias in aliases}:
                matches.append((priority, role_id))
    if not matches:
        return {"status": "needs_review", "priority": None, "canonical_role": None, "source_role_title": title, "reason": "role is not an exact confirmed-title match", "human_review_required": True}
    priority, role_id = matches[0]
    condition = CONDITIONS.get(role_id)
    if condition and condition not in evidence_flags:
        return {"status": "needs_review", "priority": None, "canonical_role": role_id, "source_role_title": title, "reason": f"conditional evidence is missing: {condition}", "human_review_required": True}
    return {"status": "classified", "priority": priority, "canonical_role": role_id, "source_role_title": title, "reason": "exact confirmed title and required conditions passed", "human_review_required": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    catalogue = json.loads(args.catalogue.read_text(encoding="utf-8"))
    if catalogue.get("version") != "0.3.1":
        print(json.dumps({"status": "invalid", "error": "active catalogue 0.3.1 is required"}, indent=2))
        return 1
    result = classify(request)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result["status"] == "invalid" else 0


if __name__ == "__main__":
    raise SystemExit(main())
