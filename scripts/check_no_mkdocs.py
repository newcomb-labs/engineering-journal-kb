#!/usr/bin/env python3
"""Fail if MkDocs references exist anywhere in the repository.

This repository uses Docusaurus as the only documentation system.
Any MkDocs references are treated as configuration drift.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

EXCLUDED_DIR_NAMES = {
    ".git",
    ".github/.cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "node_modules",
    "site",
    "venv",
    "__pycache__",
}

EXCLUDED_PATHS = {
    REPO_ROOT / "website" / "build",
    REPO_ROOT / "website" / ".docusaurus",
    REPO_ROOT / "scripts" / "check_no_mkdocs.py",
}

PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bmkdocs\.yml\b", re.IGNORECASE),
    re.compile(r"\bmkdocs-material\b", re.IGNORECASE),
    re.compile(r"\bmkdocs\b", re.IGNORECASE),
)


def is_excluded(path: Path) -> bool:
    if path in EXCLUDED_PATHS:
        return True

    for part in path.parts:
        if part in EXCLUDED_DIR_NAMES:
            return True

    for excluded in EXCLUDED_PATHS:
        try:
            path.relative_to(excluded)
            return True
        except ValueError:
            continue

    return False


def scan_file(path: Path) -> list[str]:
    violations: list[str] = []

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return violations
    except OSError as exc:
        violations.append(f"{path}:0: unable to read file: {exc}")
        return violations

    for line_number, line in enumerate(content.splitlines(), start=1):
        for pattern in PATTERNS:
            if pattern.search(line):
                violations.append(f"{path}:{line_number}: {line.strip()}")
                break

    return violations


def main() -> int:
    violations: list[str] = []

    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if is_excluded(path):
            continue
        violations.extend(scan_file(path))

    if violations:
        print("MkDocs references detected. This repository is Docusaurus-only.\n")
        for violation in violations:
            print(violation)
        return 1

    print("No MkDocs references detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
