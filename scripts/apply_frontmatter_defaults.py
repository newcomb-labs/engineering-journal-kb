#!/usr/bin/env python3

from __future__ import annotations

import re
from pathlib import Path

import yaml

DOCS_ROOT = Path("website/docs")


def infer_type(path: Path) -> str:
    p = str(path)

    if "/case-studies/" in p:
        return "case-study"
    if "/labs/" in p:
        return "lab"
    if "/journal/" in p:
        return "journal"

    return "doc"


def infer_category(path: Path) -> str:
    p = str(path)

    if "/case-studies/" in p:
        return "case-studies"
    if "/labs/" in p:
        return "labs"
    if "/engineering/" in p:
        return "engineering"
    if "/governance/" in p:
        return "governance"
    if "/operations/" in p:
        return "operations"

    return "engineering"


def extract_title(content: str, path: Path) -> str:
    match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
    if match:
        return match.group(1).strip()

    return path.stem.replace("-", " ").title()


def split_frontmatter(content: str):
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end != -1:
            fm = content[3:end]
            body = content[end + 4 :]
            return fm, body

    return None, content


def apply_defaults(path: Path):
    original = path.read_text(encoding="utf-8")

    fm_raw, body = split_frontmatter(original)

    if fm_raw:
        frontmatter = yaml.safe_load(fm_raw) or {}
    else:
        frontmatter = {}

    changed = False

    # title
    if "title" not in frontmatter or not str(frontmatter["title"]).strip():
        frontmatter["title"] = extract_title(original, path)
        changed = True

    # type
    if "type" not in frontmatter or not frontmatter["type"]:
        frontmatter["type"] = infer_type(path)
        changed = True

    # lifecycle
    if "lifecycle" not in frontmatter or not str(frontmatter["lifecycle"]).strip():
        frontmatter["lifecycle"] = "draft"
        changed = True

    # category
    if "category" not in frontmatter or not frontmatter["category"]:
        frontmatter["category"] = infer_category(path)
        changed = True

    if not changed:
        return False

    new_content = (
        "---\n"
        + yaml.safe_dump(frontmatter, sort_keys=False).strip()
        + "\n---\n\n"
        + body.lstrip()
    )

    path.write_text(new_content, encoding="utf-8")
    return True


def main():
    files = list(DOCS_ROOT.rglob("*.md"))

    updated = 0

    for f in files:
        if apply_defaults(f):
            print(f"updated: {f}")
            updated += 1

    print(f"\nDone. Updated {updated} file(s).")


if __name__ == "__main__":
    main()
