#!/usr/bin/env python3
"""Evaluate Hermes usage metadata against Equinet A1 provisional token and call quotas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

PROFILE_DIR = Path(__file__).resolve().parents[1]
POLICY_PATH = PROFILE_DIR / "configurations" / "operations" / "a1-runtime-policy-v1.yaml"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("Usage file must contain an object.")
    return value


def load_policy() -> dict[str, Any]:
    with POLICY_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def evaluate(usage: dict[str, Any], scope: str, candidate_count: int) -> dict[str, Any]:
    full_policy = load_policy()
    policy = full_policy["pilot_quotas"]
    total_tokens = int(usage.get("total_tokens") or 0)
    api_calls = int(usage.get("api_calls") or 0)
    completed = usage.get("completed") is True and usage.get("failed") is not True
    if scope == "candidate":
        token_limits = policy["tokens"]["per_candidate"]
        call_hard = policy["model_calls"]["circuit_breaker_per_turn"]
        call_warning = policy["model_calls"]["warning_per_turn"]
    elif scope == "run":
        token_limits = policy["tokens"]["per_run"]
        call_hard = policy["model_calls"]["circuit_breaker_per_turn"]
        call_warning = policy["model_calls"]["warning_per_turn"]
        if candidate_count > policy["max_live_candidates_per_run"]:
            return {"status": "exceeded", "reason": "candidate_count", "candidate_count": candidate_count}
    elif scope == "daily":
        test_mode = full_policy.get("unitalk_test_mode", {})
        token_limits = test_mode["daily_tokens"] if test_mode.get("active") is True else policy["tokens"]["per_day"]
        call_hard = None
        call_warning = None
    else:
        raise ValueError("scope must be candidate, run or daily")

    reasons: list[str] = []
    status = "pass"
    token_hard = token_limits.get("hard")
    token_escalation = token_limits.get("escalation")
    if token_hard is not None and total_tokens >= token_hard:
        status = "exceeded"
        reasons.append("token_hard_limit")
    elif token_escalation is not None and total_tokens >= token_escalation:
        status = "escalation"
        reasons.append("token_escalation_threshold")
    elif total_tokens >= token_limits["warning"]:
        status = "warning"
        reasons.append("token_warning_limit")
    if call_hard is not None and api_calls > call_hard:
        status = "exceeded"
        reasons.append("api_call_hard_limit")
    elif call_warning is not None and api_calls >= call_warning and status == "pass":
        status = "warning"
        reasons.append("api_call_warning_limit")
    if not completed:
        status = "failed"
        reasons.append("run_not_completed")
    return {
        "status": status,
        "scope": scope,
        "candidate_count": candidate_count,
        "total_tokens": total_tokens,
        "token_warning": token_limits["warning"],
        "token_escalation": token_escalation,
        "token_hard": token_hard,
        "api_calls": api_calls,
        "api_call_warning": call_warning,
        "api_call_hard": call_hard,
        "reasons": reasons,
        "model": usage.get("model"),
        "provider": usage.get("provider"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("usage", type=Path)
    parser.add_argument("--scope", choices=["candidate", "run", "daily"], default="candidate")
    parser.add_argument("--candidate-count", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(load_json(args.usage), args.scope, args.candidate_count)
    except Exception as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["status"] in {"pass", "warning", "escalation"} else 2


if __name__ == "__main__":
    sys.exit(main())
