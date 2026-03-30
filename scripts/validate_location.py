#!/usr/bin/env python3
"""Validate content location against taxonomy rules."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from content_validation_common import (
    discover_content_files,
    extract_frontmatter,
    format_error,
    load_rules,
    parse_args,
    repo_relative,
)


def normalize_prefix(prefix: str) -> str:
    return prefix if prefix.endswith("/") else f"{prefix}/"


def validate_location(
    file_paths: list[Path],
    rules: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    taxonomy_rules = rules.get("taxonomy", {})
    type_rules = taxonomy_rules.get("types", {})

    for path in file_paths:
        frontmatter, _ = extract_frontmatter(path)
        if frontmatter is None:
            continue

        content_type = frontmatter.get("type")
        category = frontmatter.get("category")

        if content_type not in type_rules:
            continue

        config = type_rules[content_type]
        path_prefixes = config.get("path_prefixes", [])

        expected_prefixes: list[str] = []
        if isinstance(path_prefixes, list):
            expected_prefixes = [normalize_prefix(prefix) for prefix in path_prefixes]
        elif isinstance(path_prefixes, dict):
            category_prefix = path_prefixes.get(category)
            if category_prefix:
                expected_prefixes = [normalize_prefix(category_prefix)]

        actual_path = repo_relative(path)
        if not expected_prefixes:
            errors.append(
                format_error(
                    path,
                    f"no path mapping defined for type '{content_type}' and category '{category}'",
                )
            )
            continue

        if not any(actual_path.startswith(prefix) for prefix in expected_prefixes):
            errors.append(
                format_error(
                    path,
                    (
                        f"path does not match taxonomy mapping for type '{content_type}' "
                        f"and category '{category}'; expected under {expected_prefixes}"
                    ),
                )
            )

    return errors


def main() -> int:
    args = parse_args("Validate content file locations.")
    rules = load_rules(Path(args.rules))
    file_paths = discover_content_files(rules, args.paths)
    errors = validate_location(file_paths, rules)

    for error in errors:
        print(error)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
