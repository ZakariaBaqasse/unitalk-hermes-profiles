#!/usr/bin/env python3
"""Evaluate A2 duplicate and eligibility gates without external access."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

VERSION = "0.1.0"
DUPLICATE_STATES = {"unavailable", "not_checked", "no_match", "possible_match", "confirmed_duplicate", "error"}
IDENTITY_STATES = {"unresolved", "possible_match", "resolved", "conflict", "invalid"}
SCOPES = {"synthetic_test", "manual_no_integration_pilot", "integrated_pilot", "production"}


def evaluate(request: dict) -> dict:
    scope = request.get("operating_scope")
    identity = request.get("identity_resolution_status")
    upstream = request.get("a1_eligibility_status")
    checks = request.get("checks", [])
    if scope not in SCOPES:
        raise ValueError("unknown operating_scope")
    if identity not in IDENTITY_STATES:
        raise ValueError("unknown identity_resolution_status")
    if upstream not in {"eligible", "hold", "blocked"}:
        raise ValueError("a1_eligibility_status must be eligible, hold or blocked")
    if not isinstance(checks, list):
        raise ValueError("checks must be an array")
    for check in checks:
        if check.get("status") not in DUPLICATE_STATES:
            raise ValueError(f"unknown duplicate status: {check.get('status')}")
        if not check.get("check_type") or not check.get("system"):
            raise ValueError("each duplicate check requires check_type and system")

    reasons = []
    if upstream == "blocked":
        decision = "blocked"; reasons.append("A1 eligibility is blocked")
    elif upstream == "hold":
        decision = "hold"; reasons.append("A1 eligibility is on hold")
    elif identity == "invalid":
        decision = "blocked"; reasons.append("identity resolution is invalid")
    elif any(x["status"] == "confirmed_duplicate" for x in checks):
        decision = "blocked"; reasons.append("a confirmed duplicate exists")
    elif identity in {"possible_match", "unresolved", "conflict"} or any(x["status"] in {"possible_match", "error"} for x in checks):
        decision = "hold"; reasons.append("identity or duplicate ambiguity requires review")
    else:
        authoritative = [x for x in checks if x.get("authoritative") is True]
        unavailable_authoritative = [x for x in authoritative if x["status"] in {"unavailable", "not_checked"}]
        if scope in {"integrated_pilot", "production"} and unavailable_authoritative:
            decision = "hold"; reasons.append("an authoritative duplicate check is unavailable")
        else:
            decision = "eligible"; reasons.append("no blocking or review-required duplicate signal exists for the declared scope")

    outreach = "blocked" if decision == "blocked" else "unavailable"
    if scope in {"integrated_pilot", "production"} and decision == "hold":
        outreach = "hold"
    return {
        "command": "a2-duplicate-eligibility",
        "version": VERSION,
        "a2_eligibility_status": decision,
        "outreach_eligibility_status": outreach,
        "owner_routing_status": "needs_owner_review",
        "reasons": reasons,
        "checks": checks,
        "crm_write_authorized": False,
        "outreach_authorized": False,
        "external_actions": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(json.loads(args.request.read_text(encoding="utf-8")))
        rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except Exception as exc:
        print(json.dumps({"valid": False, "command": "a2-duplicate-eligibility", "error": str(exc), "external_actions": 0}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
