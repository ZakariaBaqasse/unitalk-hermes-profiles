#!/usr/bin/env python3
"""Audit authored Equinet A2 artifacts for accidental French configuration text."""

from __future__ import annotations

import json
from pathlib import Path

PROFILE_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = PROFILE_ROOT / "evaluations" / "foundation-clarifications" / "language-audit.json"
SEARCH_ROOTS = [
    PROFILE_ROOT / "SOUL.md",
    PROFILE_ROOT / "profile.yaml",
    PROFILE_ROOT / "foundations",
    PROFILE_ROOT / "deliverables",
    PROFILE_ROOT / "evaluations",
    PROFILE_ROOT / "scripts",
]
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".txt", ".csv"}
FRENCH_MARKERS = [
    "Revue de décision",
    "Décision humaine",
    "Étape",
    "Résultat technique",
    "Résultat de validation",
    "Approbatrice",
    "Contrôle",
    "Frontière approuvée",
    "Décisions approuvées",
    "États approuvés",
    "Cette décision",
    "Les tests",
    "doit être",
    "peut être",
    "sans intégration",
]


def iter_files():
    for root in SEARCH_ROOTS:
        if root.is_file():
            yield root
        elif root.is_dir():
            for path in sorted(root.rglob("*")):
                if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                    if path == OUTPUT:
                        continue
                    yield path


def main() -> int:
    findings = []
    files_checked = 0
    seen = set()
    for path in iter_files():
        if path in seen or path.resolve() == Path(__file__).resolve():
            continue
        seen.add(path)
        files_checked += 1
        text = path.read_text(encoding="utf-8")
        for marker in FRENCH_MARKERS:
            if marker.casefold() in text.casefold():
                findings.append({
                    "path": str(path.relative_to(PROFILE_ROOT)),
                    "marker": marker,
                })

    result = {
        "scope": "Authored A2 profile artifacts; .venv and external package files excluded",
        "policy": "Stored profile artifacts are English; French is reserved for conversations with Séverine.",
        "files_checked": files_checked,
        "french_markers_checked": len(FRENCH_MARKERS),
        "findings": findings,
        "pass": not findings,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
