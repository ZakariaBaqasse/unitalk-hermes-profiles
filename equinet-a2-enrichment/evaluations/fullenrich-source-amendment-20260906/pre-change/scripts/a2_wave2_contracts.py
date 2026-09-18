#!/usr/bin/env python3
"""Shared strict JSON and active-foundation helpers for A2 Wave 2."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_MANIFEST = ROOT / "foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json"


class ContractError(ValueError):
    """Raised when a JSON contract or active dependency is invalid."""


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ContractError(f"non-finite JSON number is not allowed: {value}")


def load_json_strict(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"JSON root must be an object: {path}")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_active(relative_path: str) -> dict[str, Any]:
    manifest = load_json_strict(ACTIVE_MANIFEST)
    index = {item.get("path"): item for item in manifest.get("active_files", [])}
    entry = index.get(relative_path)
    if not entry:
        raise ContractError(f"dependency is not active: {relative_path}")
    path = ROOT / relative_path
    if not path.is_file():
        raise ContractError(f"active dependency is missing: {relative_path}")
    actual = sha256_file(path)
    if actual != entry.get("sha256"):
        raise ContractError(f"active dependency hash mismatch: {relative_path}")
    return load_json_strict(path)


def ensure_finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ContractError(f"non-finite number at {path}")
    if isinstance(value, dict):
        for key, item in value.items():
            ensure_finite(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            ensure_finite(item, f"{path}[{index}]")
