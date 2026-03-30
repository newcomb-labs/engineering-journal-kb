#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import yaml

GOVERNED_ROOT = Path("website/docs")
ALLOWED_EXTENSIONS = {".md", ".mdx"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate governed content files.")
    parser.add_argument(
        "files",
        nargs="*",
        help="Optional explicit list of files to validate. If omitted, scan all governed content.",
    )
    return parser.parse_args()


def normalize_files(files: Iterable[str]) -> list[Path]:
    normalized: list[Path] = []

    for raw in files:
        path = Path(raw)
        if not path.exists():
            continue
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        if GOVERNED_ROOT not in path.parents and path != GOVERNED_ROOT:
            continue
        normalized.append(path)

    seen: set[Path] = set()
    unique: list[Path] = []
    for path in normalized:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)

    return sorted(unique)


def discover_all_files() -> list[Path]:
    files = [
        path
        for path in GOVERNED_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS
    ]
    return sorted(files)


def get_target_files(cli_files: list[str]) -> list[Path]:
    if cli_files:
        return normalize_files(cli_files)
    return discover_all_files()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(path: Path) -> tuple[dict | None, str | None]:
    content = read_text(path)

    if not content.startswith("---\n") and content != "---":
        return None, "missing valid YAML frontmatter block"

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, "missing valid YAML frontmatter block"

    raw_frontmatter = parts[1]

    try:
        parsed = yaml.safe_load(raw_frontmatter)
    except yaml.YAMLError:
        return None, "missing valid YAML frontmatter block"

    if parsed is None:
        parsed = {}

    if not isinstance(parsed, dict):
        return None, "frontmatter must parse to a YAML mapping"

    return parsed, None
