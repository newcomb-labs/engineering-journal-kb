#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

BLOG_DIR = Path("website/blog")
TAGS_FILE = BLOG_DIR / "tags.yml"

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL | re.MULTILINE)


def load_tags() -> set[str]:
    if not TAGS_FILE.exists():
        print(f"ERROR: Missing tags file: {TAGS_FILE}", file=sys.stderr)
        sys.exit(1)

    data = yaml.safe_load(TAGS_FILE.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        print(
            f"ERROR: {TAGS_FILE} must contain a mapping of tag keys.", file=sys.stderr
        )
        sys.exit(1)

    return set(data.keys())


def iter_posts() -> list[Path]:
    posts = []
    for pattern in ("*.md", "*.mdx"):
        posts.extend(BLOG_DIR.glob(pattern))
        posts.extend(BLOG_DIR.glob(f"*/index{pattern[1:]}"))
    return sorted(set(posts))


def extract_front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}

    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        print(f"ERROR: Failed to parse front matter in {path}: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict):
        return {}
    return data


def normalize_tags(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return [str(value).strip()]


def main() -> int:
    defined_tags = load_tags()
    missing: dict[str, list[str]] = {}

    for post in iter_posts():
        fm = extract_front_matter(post)
        tags = normalize_tags(fm.get("tags"))
        for tag in tags:
            if tag not in defined_tags:
                missing.setdefault(str(post), []).append(tag)

    if missing:
        print("ERROR: Undefined blog tags found:\n", file=sys.stderr)
        for post, tags in missing.items():
            joined = ", ".join(sorted(tags))
            print(f"- {post}: {joined}", file=sys.stderr)
        print(
            f"\nDefine missing tags in {TAGS_FILE} before committing.",
            file=sys.stderr,
        )
        return 1

    print("Blog tag validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
