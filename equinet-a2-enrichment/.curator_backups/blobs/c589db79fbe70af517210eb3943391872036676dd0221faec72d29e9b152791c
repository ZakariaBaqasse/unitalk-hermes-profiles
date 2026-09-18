#!/usr/bin/env python3
"""Validate a raw-byte manifest and compile listed Python files."""
from __future__ import annotations

import argparse
import hashlib
import json
import py_compile
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    root = args.root.resolve() if args.root else manifest_path.parent.parent.parent.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest.get("active_files", manifest.get("files", []))
    errors: list[str] = []
    seen: set[str] = set()
    compiled = 0

    declared_count = manifest.get("active_file_count", manifest.get("file_count"))
    if declared_count is not None and declared_count != len(rows):
        errors.append(f"declared count {declared_count} != rows {len(rows)}")

    for item in rows:
        rel = item.get("path")
        if not isinstance(rel, str) or not rel:
            errors.append("manifest row has no path")
            continue
        if rel in seen:
            errors.append(f"duplicate path: {rel}")
            continue
        seen.add(rel)
        path = root / rel
        if not path.is_file():
            errors.append(f"missing: {rel}")
            continue
        if item.get("bytes") is not None and path.stat().st_size != item["bytes"]:
            errors.append(f"byte-size mismatch: {rel}")
        if sha256(path) != item.get("sha256"):
            errors.append(f"hash mismatch: {rel}")
        if path.suffix == ".py":
            try:
                py_compile.compile(str(path), doraise=True)
                compiled += 1
            except Exception as exc:
                errors.append(f"python syntax error: {rel}: {exc}")

    result = {
        "status": "pass" if not errors else "fail",
        "manifest": str(manifest_path),
        "root": str(root),
        "entries": len(rows),
        "python_files_compiled": compiled,
        "hash_algorithm": "sha256_raw_file_bytes",
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
