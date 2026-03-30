#!/usr/bin/env python3

from pathlib import Path
from datetime import date
import yaml

DOCS_ROOT = Path("website/docs")
TAXONOMY_PATH = Path(".github/taxonomy.yml")

DEFAULT_OWNER = "@newcomb-labs"
DEFAULT_STATUS = "draft"


def load_taxonomy():
    data = yaml.safe_load(TAXONOMY_PATH.read_text()) or {}
    return set(data.get("domains", [])), set(data.get("tags", []))


def classify(path: Path):
    p = path.as_posix()
    if "case-studies" in p:
        return "case-study"
    if "labs" in p:
        return "lab"
    if "journal" in p:
        return "journal"
    if "adr" in p:
        return "adr"
    return "docs"


def required_sections(content_type):
    return {
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
    }.get(content_type, [])


def ensure_sections(body: str, content_type: str) -> str:
    sections = required_sections(content_type)
    for sec in sections:
        if sec not in body:
            body += f"\n\n{sec}\n\nTODO\n"
    return body


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    return yaml.safe_load(parts[1]) or {}, parts[2]


def render_frontmatter(fm: dict):
    return "---\n" + yaml.safe_dump(fm, sort_keys=False) + "---\n"


def infer_title(path: Path):
    return path.stem.replace("-", " ").title()


def main():
    domains, tags = load_taxonomy()
    today = date.today().isoformat()

    for path in DOCS_ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)

        ctype = classify(path)

        fm["title"] = fm.get("title") or infer_title(path)
        fm["description"] = fm.get("description") or "TODO"
        fm["content_type"] = ctype
        fm["status"] = (
            fm.get("status")
            if fm.get("status")
            in {"draft", "review", "active", "deprecated", "archived"}
            else DEFAULT_STATUS
        )
        fm["created_at"] = fm.get("created_at") or today
        fm["last_reviewed"] = fm.get("last_reviewed") or today
        fm["owners"] = [DEFAULT_OWNER]

        # domain
        fm["primary_domain"] = next(iter(domains)) if domains else None

        # tags (safe minimal set)
        fm["tags"] = [t for t in fm.get("tags", []) if t in tags][:3] or list(tags)[:1]

        body = ensure_sections(body, ctype)

        new_text = render_frontmatter(fm) + body.strip() + "\n"
        path.write_text(new_text, encoding="utf-8")
        print(f"UPDATED: {path}")

    print("DONE")


if __name__ == "__main__":
    main()
