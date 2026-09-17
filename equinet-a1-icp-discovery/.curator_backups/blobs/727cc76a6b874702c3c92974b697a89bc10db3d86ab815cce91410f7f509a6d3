#!/usr/bin/env python3
"""Provision the profile-local Python runtime during profile installation.

This is an installer/deployment command, not a discovery-run command.
It creates a fresh local virtual environment from the versioned runtime
requirements and verifies the imports required by A1 state validation.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


PROFILE_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_VENV = PROFILE_ROOT / ".venv"
DEFAULT_REQUIREMENTS = (
    PROFILE_ROOT / "configurations/operations/a1-python-runtime-requirements.txt"
)
REQUIRED_IMPORTS = ("jsonschema",)


def interpreter(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=PROFILE_ROOT, check=True)


def verify(venv: Path) -> dict[str, str]:
    python = interpreter(venv)
    if not python.is_file():
        raise RuntimeError(f"profile runtime interpreter is missing: {python}")

    code = (
        "import importlib.metadata, json; "
        f"mods={REQUIRED_IMPORTS!r}; "
        "[__import__(m) for m in mods]; "
        "print(json.dumps({m: importlib.metadata.version(m) for m in mods}, sort_keys=True))"
    )
    completed = subprocess.run(
        [str(python), "-c", code],
        cwd=PROFILE_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def provision(venv: Path, requirements: Path) -> dict[str, str]:
    if not requirements.is_file():
        raise RuntimeError(f"runtime requirements are missing: {requirements}")
    uv = shutil.which("uv")
    if not uv:
        raise RuntimeError("uv is required by the profile installer but was not found on PATH")

    build_dir = Path(
        tempfile.mkdtemp(prefix=".a1-venv-build-", dir=str(PROFILE_ROOT))
    )
    backup = venv.with_name(f"{venv.name}.previous")
    try:
        shutil.rmtree(build_dir)
        run([uv, "venv", str(build_dir)])
        run(
            [
                uv,
                "pip",
                "install",
                "--python",
                str(interpreter(build_dir)),
                "-r",
                str(requirements),
            ]
        )
        versions = verify(build_dir)

        if backup.exists() or backup.is_symlink():
            if backup.is_dir() and not backup.is_symlink():
                shutil.rmtree(backup)
            else:
                backup.unlink()
        if venv.exists() or venv.is_symlink():
            venv.rename(backup)
        build_dir.rename(venv)
        if backup.exists() or backup.is_symlink():
            if backup.is_dir() and not backup.is_symlink():
                shutil.rmtree(backup)
            else:
                backup.unlink()
        return versions
    except Exception:
        if not venv.exists() and backup.exists():
            backup.rename(venv)
        if build_dir.exists():
            shutil.rmtree(build_dir)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify only; do not install")
    parser.add_argument("--venv", type=Path, default=DEFAULT_VENV)
    parser.add_argument("--requirements", type=Path, default=DEFAULT_REQUIREMENTS)
    args = parser.parse_args()

    versions = verify(args.venv) if args.check else provision(args.venv, args.requirements)
    print(
        json.dumps(
            {
                "status": "ready",
                "profile_root": str(PROFILE_ROOT),
                "python": str(interpreter(args.venv)),
                "requirements": str(args.requirements),
                "packages": versions,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
