#!/usr/bin/env python3
"""
Repository governance guard: MkDocs must not appear anywhere in this repo.

Allowed location:
- scripts/check_no_mkdocs.py

If MkDocs-related references are found elsewhere, CI fails.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

ALLOWED_FILE = REPO_ROOT / "scripts" / "check_no_mkdocs.py"

# Patterns that indicate MkDocs usage
MKDOCS_PATTERNS = [
    r"\bmkdocs\b",
    r"mkdocs-material",
    r"mkdocs\.yml",
    r"mkdocs build",
    r"mkdocs serve",
]

IGNORE_DIRS = {
    ".git",
    ".github/actions",
    "node_modules",
    "build",
    ".venv",
    ".cache",
}


def should_skip(path: Path) -> bool:
    for part in path.parts:
        if part in IGNORE_DIRS:
            return True
    return False


def scan():
    violations = []

    for file in REPO_ROOT.rglob("*"):
        if not file.is_file():
            continue

        if file == ALLOWED_FILE:
            continue

        if should_skip(file):
            continue

        try:
            text = file.read_text(errors="ignore")
        except Exception:
            continue

        for pattern in MKDOCS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append((file.relative_to(REPO_ROOT), pattern))

    return violations


def main():
    violations = scan()

    if not violations:
        print("✓ MkDocs governance check passed.")
        return

    print("ERROR: MkDocs references detected in repository.\n")
    for path, pattern in violations:
        print(f" - {path} (matched pattern: {pattern})")

    print("\nMkDocs is prohibited in this repository.")
    print("Remove the references or update the guard if this is intentional.")
    sys.exit(1)


if __name__ == "__main__":
    main()
