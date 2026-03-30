#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = REPO_ROOT / ".github" / "governance" / "required-sections.yml"
DOCS_ROOT = REPO_ROOT / "website" / "docs"

H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def normalize_heading(value: str) -> str:
    return " ".join(value.strip().split()).casefold()


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text

    parts = text.splitlines(keepends=True)
    if len(parts) < 3:
        return {}, text

    end_index = None
    for index in range(1, len(parts)):
        if parts[index].strip() == "---":
            end_index = index
            break

    if end_index is None:
        return {}, text

    frontmatter_text = "".join(parts[1:end_index])
    body = "".join(parts[end_index + 1 :])
    data = yaml.safe_load(frontmatter_text) or {}
    if not isinstance(data, dict):
        raise ValueError("Frontmatter must parse to a mapping.")
    return data, body


def load_rules(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Rules file is invalid: {path}")
    return data


def is_excluded(rel_path: str, rules: dict) -> bool:
    excluded = rules.get("excluded_paths", [])
    return rel_path in excluded


def existing_h2_headings(body: str) -> set[str]:
    return {normalize_heading(match.group(1)) for match in H2_RE.finditer(body)}


def infer_type_from_path(rel_path: str) -> str:
    if "/case-studies/" in rel_path:
        return "case-study"
    if "/labs/" in rel_path:
        return "lab"
    if "/journal/" in rel_path:
        return "journal"
    return "doc"


def required_sections_for(frontmatter: dict, rel_path: str, rules: dict) -> list[str]:
    content_type = frontmatter.get("type") or infer_type_from_path(rel_path)
    sections = rules.get("required_sections", {}).get(content_type, [])
    if not isinstance(sections, list):
        raise ValueError(f"Required sections for type '{content_type}' must be a list.")
    return [str(section) for section in sections]


def iter_markdown_files(paths: list[str]) -> Iterable[Path]:
    if paths:
        for raw_path in paths:
            path = Path(raw_path).resolve()
            if path.exists() and path.suffix == ".md":
                yield path
        return

    for path in sorted(DOCS_ROOT.rglob("*.md")):
        yield path.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate required H2 sections for governed markdown files."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional markdown file paths. Defaults to all website/docs/*.md files.",
    )
    args = parser.parse_args()

    rules = load_rules(RULES_PATH)

    for path in iter_markdown_files(args.paths):
        rel_path = path.relative_to(REPO_ROOT).as_posix()

        if is_excluded(rel_path, rules):
            continue

        text = path.read_text(encoding="utf-8")
        frontmatter, body = split_frontmatter(text)
        required_sections = required_sections_for(frontmatter, rel_path, rules)

        if not required_sections:
            continue

        existing = existing_h2_headings(body)
        missing = [
            section
            for section in required_sections
            if normalize_heading(section) not in existing
        ]

        if missing:
            print(
                "required heading validation failed:\n"
                f"- file: {rel_path}\n"
                f"- type: {frontmatter.get('type') or infer_type_from_path(rel_path)}\n"
                f"- missing headings: {', '.join(f'## {section}' for section in missing)}"
            )
            return 1

    print("required heading validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
