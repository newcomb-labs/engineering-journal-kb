#!/usr/bin/env python3
"""
validate_content.py

Unified content governance validator for the Engineering Journal.

Enforces:
- Frontmatter schema (required fields, enums, date format)
- Taxonomy (domains + tags)
- content_type ↔ path alignment
- Required sections per content type

Generated artifacts under website/docs/_generated are intentionally skipped.

Exit code:
- 0 = success
- 1 = validation failures
"""

import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except Exception:
    print(
        "ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr
    )
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parents[1]

DOCS_DIR = REPO_ROOT / "website" / "docs"
GENERATED_DIR = DOCS_DIR / "_generated"
TAXONOMY_FILE = REPO_ROOT / ".github" / "taxonomy.yml"

ALLOWED_STATUS = {"draft", "review", "active", "deprecated", "archived"}

REQUIRED_FIELDS = {
    "title",
    "description",
    "content_type",
    "status",
    "tags",
    "owners",
    "created_at",
    "last_reviewed",
}

CONTENT_PATHS = {
    "doc": "website/docs/",
    "lab": "website/docs/labs/",
    "case-study": "website/docs/case-studies/",
    "journal": "website/docs/journal/",
    "adr": "website/docs/adr/",
}

REQUIRED_SECTIONS = {
    "lab": [
        "## Overview",
        "## Environment",
        "## Steps",
        "## Validation",
        "## Lessons Learned",
    ],
    "case-study": [
        "## Summary",
        "## Problem",
        "## Impact",
        "## Root Cause",
        "## Resolution",
        "## Lessons Learned",
    ],
    "journal": ["## Summary", "## Notes", "## Insights"],
    "adr": ["## Title", "## Status", "## Context", "## Decision", "## Consequences"],
}


def fail(msg: str) -> bool:
    print(f"ERROR: {msg}")
    return False


def parse_frontmatter(text: str):
    """
    Extract YAML frontmatter between leading --- blocks.
    Returns dict or None if not present/invalid.
    """
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    fm_raw = parts[1]
    try:
        return yaml.safe_load(fm_raw) or {}
    except Exception as exc:
        print(f"ERROR: Invalid YAML frontmatter: {exc}")
        return None


def is_iso_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except Exception:
        return False


def load_taxonomy():
    if not TAXONOMY_FILE.exists():
        print(f"ERROR: Missing taxonomy file: {TAXONOMY_FILE}")
        sys.exit(1)
    data = yaml.safe_load(TAXONOMY_FILE.read_text(encoding="utf-8")) or {}
    domains = set(data.get("domains", []))
    tags = set(data.get("tags", []))
    return domains, tags


def validate_file(path: Path, domains, tags) -> bool:
    ok = True
    text = path.read_text(encoding="utf-8")

    fm = parse_frontmatter(text)
    if fm is None:
        return fail(f"{path}: missing or invalid frontmatter")

    # Required fields
    missing = REQUIRED_FIELDS - set(fm.keys())
    if missing:
        ok &= fail(f"{path}: missing required fields: {sorted(missing)}")

    # Status enum
    status = fm.get("status")
    if status not in ALLOWED_STATUS:
        ok &= fail(f"{path}: invalid status '{status}'")

    # Dates
    for field in ("created_at", "last_reviewed"):
        val = fm.get(field)
        if not isinstance(val, str) or not is_iso_date(val):
            ok &= fail(f"{path}: {field} must be YYYY-MM-DD")

    # Owners
    owners = fm.get("owners", [])
    if not isinstance(owners, list) or not all(
        isinstance(owner, str) and owner.startswith("@") for owner in owners
    ):
        ok &= fail(f"{path}: owners must be list of @usernames")

    # Tags
    file_tags = fm.get("tags", [])
    if not isinstance(file_tags, list):
        ok &= fail(f"{path}: tags must be a list")
    else:
        unknown = [tag for tag in file_tags if tag not in tags]
        if unknown:
            ok &= fail(f"{path}: unknown tags: {unknown}")

    # Domains
    primary = fm.get("primary_domain")
    secondary = fm.get("secondary_domains", [])

    if primary not in domains:
        ok &= fail(f"{path}: invalid primary_domain '{primary}'")

    if not isinstance(secondary, list) or any(
        domain not in domains for domain in secondary
    ):
        ok &= fail(f"{path}: invalid secondary_domains '{secondary}'")

    # content_type ↔ path alignment
    ctype = fm.get("content_type")
    expected_prefix = CONTENT_PATHS.get(ctype)
    if expected_prefix is None:
        ok &= fail(f"{path}: unknown content_type '{ctype}'")
    else:
        path_str = path.as_posix()
        if expected_prefix not in path_str:
            ok &= fail(
                f"{path}: content_type '{ctype}' does not match path '{expected_prefix}'"
            )

    # Required sections
    sections = REQUIRED_SECTIONS.get(ctype, [])
    for section in sections:
        if section not in text:
            ok &= fail(f"{path}: missing section '{section}'")

    return ok


def get_target_files() -> list[Path]:
    if len(sys.argv) > 1:
        resolved = []
        for arg in sys.argv[1:]:
            if not arg.endswith(".md"):
                continue
            p = Path(arg)
            if not p.is_absolute():
                p = REPO_ROOT / p
            resolved.append(p.resolve())
        return resolved
    return list(DOCS_DIR.rglob("*.md"))


def main():
    if not DOCS_DIR.exists():
        print(f"ERROR: Docs directory not found: {DOCS_DIR}")
        sys.exit(1)

    domains, tags = load_taxonomy()

    files = get_target_files()
    if not files:
        print("No markdown files found under website/docs")
        sys.exit(0)

    all_ok = True
    for file_path in files:
        # Skip generated content artifacts entirely
        if GENERATED_DIR in file_path.parents:
            print(f"SKIP (generated): {file_path}")
            continue

        all_ok &= validate_file(file_path, domains, tags)

    if not all_ok:
        print("\nValidation failed.")
        sys.exit(1)

    print("Validation passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
