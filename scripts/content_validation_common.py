#!/usr/bin/env python3
"""Shared helpers for content governance validation."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES_PATH = REPO_ROOT / ".github" / "governance" / "content-rules.yml"


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def load_rules(rules_path: Path = DEFAULT_RULES_PATH) -> dict[str, Any]:
    with rules_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Rules file must load as a mapping: {rules_path}")
    return data


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional list of files or directories to validate. Defaults to all content roots.",
    )
    parser.add_argument(
        "--rules",
        default=str(DEFAULT_RULES_PATH),
        help="Path to the governance rules YAML file.",
    )
    return parser.parse_args()


def should_ignore(path: Path, ignore_paths: list[str]) -> bool:
    rel = repo_relative(path)
    for ignored in ignore_paths:
        ignored = ignored.rstrip("/")
        if rel == ignored or rel.startswith(f"{ignored}/"):
            return True
    return False


def discover_content_files(
    rules: dict[str, Any],
    explicit_paths: list[str] | None = None,
) -> list[Path]:
    allowed_extensions = set(rules.get("allowed_extensions", [".md", ".mdx"]))
    ignore_paths = rules.get("ignore_paths", [])
    discovered: list[Path] = []

    if explicit_paths:
        candidates = [REPO_ROOT / item for item in explicit_paths]
    else:
        candidates = [REPO_ROOT / root for root in rules.get("content_roots", [])]

    for candidate in candidates:
        if not candidate.exists():
            continue

        if candidate.is_file():
            if candidate.suffix.lower() in allowed_extensions and not should_ignore(
                candidate, ignore_paths
            ):
                discovered.append(candidate)
            continue

        for file_path in sorted(candidate.rglob("*")):
            if (
                file_path.is_file()
                and file_path.suffix.lower() in allowed_extensions
                and not should_ignore(file_path, ignore_paths)
            ):
                discovered.append(file_path)

    deduped = sorted({path.resolve() for path in discovered})
    return deduped


def extract_frontmatter(path: Path) -> tuple[dict[str, Any] | None, str]:
    text = path.read_text(encoding="utf-8")

    if not text.startswith("---\n"):
        return None, text

    lines = text.splitlines(keepends=True)
    closing_index: int | None = None

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        return None, text

    raw_frontmatter = "".join(lines[1:closing_index])
    body = "".join(lines[closing_index + 1 :])

    loaded = yaml.safe_load(raw_frontmatter) or {}
    if not isinstance(loaded, dict):
        return None, body

    return loaded, body


def is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def is_nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


def type_name(value: Any) -> str:
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, str):
        return "string"
    if value is None:
        return "null"
    return type(value).__name__


def matches_expected_type(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "list":
        return isinstance(value, list)
    if expected == "dict":
        return isinstance(value, dict)
    return True


def format_error(path: Path, message: str) -> str:
    return f"{repo_relative(path)}: {message}"
