#!/usr/bin/env python3
"""Apply default frontmatter values to governed markdown files.

Covers all 12 required fields from .github/governance/frontmatter-schema.yml:
  title, description, content_type, type, status, lifecycle,
  created_at, last_reviewed, owners, tags, primary_domain, category

Only sets fields that are missing or empty. Never overwrites existing values.
Skips generated artifacts under website/docs/_generated/.

Usage:
  python3 scripts/apply_frontmatter_defaults.py              # all docs
  python3 scripts/apply_frontmatter_defaults.py <file> ...   # specific files
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "website" / "docs"
GENERATED_DIR = DOCS_ROOT / "_generated"

TODAY = date.today().isoformat()

# ---------------------------------------------------------------------------
# Inference helpers
# ---------------------------------------------------------------------------


def infer_content_type(path: Path) -> str:
    p = path.as_posix()
    if "/case-studies/" in p:
        return "case-study"
    if "/labs/" in p:
        return "lab"
    if "/journal/" in p:
        return "journal"
    return "doc"


def infer_category(path: Path) -> str:
    p = path.as_posix()
    if "/case-studies/" in p:
        return "case-studies"
    if "/labs/" in p:
        return "labs"
    if "/journal/" in p:
        return "journal"
    if "/engineering/" in p:
        return "engineering"
    if "/governance/" in p:
        return "governance"
    if "/operations/" in p:
        return "operations"
    return "engineering"


def infer_primary_domain(path: Path) -> str:
    p = path.as_posix()
    if "/governance/" in p:
        return "governance"
    if "/labs/" in p or "/case-studies/" in p:
        return "networking"
    if "/journal/" in p:
        return "devops"
    return "devops"


def infer_tags(content_type: str) -> list[str]:
    mapping = {
        "case-study": ["debugging"],
        "lab": ["lab"],
        "journal": ["notes"],
        "doc": ["notes"],
    }
    return mapping.get(content_type, ["notes"])


def extract_title(content: str, path: Path) -> str:
    match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return path.stem.replace("-", " ").title()


def extract_description(content: str, frontmatter_end: int) -> str:
    """Extract first non-empty paragraph from body as description fallback."""
    body = content[frontmatter_end:].lstrip()
    for line in body.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("---"):
            # Strip markdown bold/emphasis
            line = re.sub(r"\*+([^*]+)\*+", r"\1", line)
            if len(line) > 10:
                return line[:200]
    return ""


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------


def split_frontmatter(content: str) -> tuple[str | None, str, int]:
    """Return (raw_fm, body, body_start_index) or (None, content, 0)."""
    if not content.startswith("---"):
        return None, content, 0
    end = content.find("\n---", 3)
    if end == -1:
        return None, content, 0
    raw_fm = content[3:end]
    body_start = end + 4
    body = content[body_start:]
    return raw_fm, body, body_start


def is_generated(path: Path) -> bool:
    try:
        return GENERATED_DIR in path.resolve().parents
    except Exception:
        return GENERATED_DIR in path.parents


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

FIELD_ORDER = [
    "title",
    "description",
    "content_type",
    "type",
    "status",
    "lifecycle",
    "created_at",
    "last_reviewed",
    "owners",
    "tags",
    "primary_domain",
    "category",
]


def apply_defaults(path: Path) -> bool:
    if is_generated(path):
        return False

    content = path.read_text(encoding="utf-8")
    raw_fm, body, body_start = split_frontmatter(content)

    frontmatter: dict = yaml.safe_load(raw_fm) or {} if raw_fm else {}
    changed = False

    def missing(field: str) -> bool:
        v = frontmatter.get(field)
        if v is None:
            return True
        if isinstance(v, str) and not v.strip():
            return True
        if isinstance(v, list) and not v:
            return True
        return False

    # title
    if missing("title"):
        frontmatter["title"] = extract_title(content, path)
        changed = True

    # description
    if missing("description"):
        desc = extract_description(content, body_start)
        frontmatter["description"] = desc if desc else frontmatter.get("title", "")
        changed = True

    # content_type
    if missing("content_type"):
        frontmatter["content_type"] = infer_content_type(path)
        changed = True

    # type — must match content_type
    if missing("type"):
        frontmatter["type"] = frontmatter.get("content_type") or infer_content_type(
            path
        )
        changed = True

    # status
    if missing("status"):
        frontmatter["status"] = "draft"
        changed = True

    # lifecycle
    if missing("lifecycle"):
        frontmatter["lifecycle"] = "draft"
        changed = True

    # created_at
    if missing("created_at"):
        frontmatter["created_at"] = TODAY
        changed = True

    # last_reviewed
    if missing("last_reviewed"):
        frontmatter["last_reviewed"] = TODAY
        changed = True

    # owners
    if missing("owners"):
        frontmatter["owners"] = ["@newcomb-labs"]
        changed = True

    # tags
    if missing("tags"):
        ctype = frontmatter.get("content_type") or infer_content_type(path)
        frontmatter["tags"] = infer_tags(ctype)
        changed = True

    # primary_domain
    if missing("primary_domain"):
        frontmatter["primary_domain"] = infer_primary_domain(path)
        changed = True

    # category
    if missing("category"):
        frontmatter["category"] = infer_category(path)
        changed = True

    if not changed:
        return False

    # Reorder fields: required fields first in canonical order, then remainder
    ordered: dict = {}
    for field in FIELD_ORDER:
        if field in frontmatter:
            ordered[field] = frontmatter[field]
    for field, value in frontmatter.items():
        if field not in ordered:
            ordered[field] = value

    new_content = (
        "---\n"
        + yaml.safe_dump(ordered, sort_keys=False, allow_unicode=True).strip()
        + "\n---\n\n"
        + body.lstrip()
    )

    path.write_text(new_content, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def get_target_files() -> list[Path]:
    if len(sys.argv) > 1:
        files = []
        for arg in sys.argv[1:]:
            p = Path(arg)
            if not p.is_absolute():
                p = REPO_ROOT / p
            if p.exists() and p.suffix == ".md":
                files.append(p)
        return files
    return [p for p in DOCS_ROOT.rglob("*.md") if not is_generated(p)]


def main() -> None:
    files = get_target_files()
    updated = 0

    for f in files:
        if apply_defaults(f):
            print(f"updated: {f.relative_to(REPO_ROOT)}")
            updated += 1

    print(f"\nDone. Updated {updated} file(s).")


if __name__ == "__main__":
    main()
