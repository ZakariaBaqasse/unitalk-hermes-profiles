#!/usr/bin/env python3
"""Aggregate A1 usage files into a daily token/call ledger and enforce the provisional daily cap."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

PROFILE_DIR = Path(__file__).resolve().parents[1]
POLICY_PATH = PROFILE_DIR / "configurations" / "operations" / "a1-runtime-policy-v1.yaml"


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object.")
    return value


def aggregate(paths: list[Path], date: str | None) -> dict[str, Any]:
    full_policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    test_mode = full_policy.get("unitalk_test_mode", {})
    if test_mode.get("active") is True:
        policy = test_mode["daily_tokens"]
        quota_mode = "unitalk_test"
    else:
        policy = full_policy["pilot_quotas"]["tokens"]["per_day"]
        quota_mode = "pilot"
    runs = []
    total_tokens = 0
    api_calls = 0
    for path in paths:
        usage = load(path)
        session_id = str(usage.get("session_id") or "")
        session_date = f"{session_id[0:4]}-{session_id[4:6]}-{session_id[6:8]}" if len(session_id) >= 8 else None
        if date and session_date != date:
            continue
        tokens = int(usage.get("total_tokens") or 0)
        calls = int(usage.get("api_calls") or 0)
        total_tokens += tokens
        api_calls += calls
        runs.append({
            "file": str(path),
            "session_id": usage.get("session_id"),
            "date": session_date,
            "model": usage.get("model"),
            "provider": usage.get("provider"),
            "tokens": tokens,
            "api_calls": calls,
            "completed": usage.get("completed"),
            "failed": usage.get("failed"),
        })
    status = "pass"
    hard = policy.get("hard")
    escalation = policy.get("escalation")
    if hard is not None and total_tokens >= hard:
        status = "exceeded"
    elif escalation is not None and total_tokens >= escalation:
        status = "escalation"
    elif total_tokens >= policy["warning"]:
        status = "warning"
    return {
        "status": status,
        "date": date,
        "quota_mode": quota_mode,
        "run_count": len(runs),
        "total_tokens": total_tokens,
        "api_calls": api_calls,
        "warning": policy["warning"],
        "escalation": escalation,
        "hard": hard,
        "runs": runs,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("usage", nargs="+", type=Path)
    parser.add_argument("--date")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = aggregate(args.usage, args.date)
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
