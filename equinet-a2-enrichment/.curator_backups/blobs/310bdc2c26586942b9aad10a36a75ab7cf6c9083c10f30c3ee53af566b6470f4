#!/usr/bin/env python3
"""Verify a raw-byte SHA-256 manifest without mutating its files."""
from __future__ import annotations

import argparse
import hashlib
import json
import py_compile
import re
from pathlib import Path

SUSPICIOUS = [
    re.compile(r"\*\*\*"),
    re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\.\.\.[A-Za-z0-9_]+\b"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--entries-key", default="active_files")
    parser.add_argument("--compile-python", action="store_true")
    parser.add_argument("--scan-redaction-markers", action="store_true")
    parser.add_argument("--fail-on-redaction-markers", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    rows = manifest.get(args.entries_key)
    if not isinstance(rows, list):
        raise SystemExit(f"manifest key is not a list: {args.entries_key}")

    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    checked = 0
    compiled = 0

    declared_count = manifest.get("active_file_count")
    if args.entries_key == "active_files" and declared_count is not None and declared_count != len(rows):
        errors.append(f"active_file_count is {declared_count}; entries contain {len(rows)}")

    for item in rows:
        rel = item.get("path")
        if not isinstance(rel, str) or not rel:
            errors.append("manifest entry has no valid path")
            continue
        if rel in seen:
            errors.append(f"duplicate path: {rel}")
            continue
        seen.add(rel)
        path = args.root / rel
        if not path.is_file():
            errors.append(f"missing: {rel}")
            continue

        checked += 1
        actual_size = path.stat().st_size
        actual_hash = sha256(path)
        if item.get("bytes") is not None and actual_size != item["bytes"]:
            errors.append(f"byte-size mismatch: {rel}: expected {item['bytes']}, got {actual_size}")
        if actual_hash != item.get("sha256"):
            errors.append(f"sha256 mismatch: {rel}: expected {item.get('sha256')}, got {actual_hash}")

        if args.compile_python and path.suffix == ".py":
            try:
                py_compile.compile(str(path), doraise=True)
                compiled += 1
            except Exception as exc:
                errors.append(f"python syntax error: {rel}: {exc}")

        if args.scan_redaction_markers and path.suffix.lower() in {".py", ".json", ".yaml", ".yml", ".md", ".toml"}:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(text.splitlines(), 1):
                if any(pattern.search(line) for pattern in SUSPICIOUS):
                    warnings.append(f"possible redaction marker: {rel}:{line_number}")

    if args.fail_on_redaction_markers and warnings:
        errors.extend(warnings)

    result = {
        "status": "pass" if not errors else "fail",
        "hash_algorithm": "sha256_raw_file_bytes",
        "entries_key": args.entries_key,
        "entries": len(rows),
        "files_checked": checked,
        "python_files_compiled": compiled,
        "errors": errors,
        "warnings": warnings,
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
