#!/usr/bin/env python3
"""Bump project version in pyproject.toml and package __init__.py."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
INIT_FILE = ROOT / "src/comando_cli/__init__.py"

VERSION_RE = re.compile(r'(?m)^version\s*=\s*"([^"]+)"\s*$')
INIT_VERSION_RE = re.compile(r'(?m)^__version__\s*=\s*"([^"]+)"\s*$')


def parse_version(version: str) -> tuple[int, int, int]:
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(f"Expected semantic version X.Y.Z, got: {version}")
    major, minor, patch = (int(p) for p in parts)
    return major, minor, patch


def bump(version: str, level: str) -> str:
    major, minor, patch = parse_version(version)
    if level == "major":
        major += 1
        minor = 0
        patch = 0
    elif level == "minor":
        minor += 1
        patch = 0
    elif level == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump level: {level}")
    return f"{major}.{minor}.{patch}"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: bump_version.py <major|minor|patch>")

    level = sys.argv[1]

    pyproject_text = PYPROJECT.read_text(encoding="utf-8")
    pyproject_match = VERSION_RE.search(pyproject_text)
    if not pyproject_match:
        raise SystemExit("Could not find version in pyproject.toml")

    current = pyproject_match.group(1)
    new_version = bump(current, level)

    updated_pyproject = VERSION_RE.sub(f'version = "{new_version}"', pyproject_text, count=1)
    PYPROJECT.write_text(updated_pyproject, encoding="utf-8")

    init_text = INIT_FILE.read_text(encoding="utf-8")
    init_match = INIT_VERSION_RE.search(init_text)
    if not init_match:
        raise SystemExit("Could not find __version__ in src/comando_cli/__init__.py")

    updated_init = INIT_VERSION_RE.sub(
        f'__version__ = "{new_version}"', init_text, count=1
    )
    INIT_FILE.write_text(updated_init, encoding="utf-8")

    print(f"Bumped version: {current} -> {new_version}")
    print(new_version)


if __name__ == "__main__":
    main()
