#!/usr/bin/env python3
"""Validate content taxonomy and type/category mappings."""

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
)


def validate_taxonomy(
    file_paths: list[Path],
    rules: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    taxonomy_rules = rules.get("taxonomy", {})
    type_rules = taxonomy_rules.get("types", {})
    allowed_types = set(type_rules.keys())

    for path in file_paths:
        frontmatter, _ = extract_frontmatter(path)
        if frontmatter is None:
            continue

        content_type = frontmatter.get("type")
        category = frontmatter.get("category")

        if content_type not in allowed_types:
            errors.append(
                format_error(
                    path,
                    f"invalid content type '{content_type}'; allowed values: {sorted(allowed_types)}",
                )
            )
            continue

        config = type_rules.get(content_type, {})
        allowed_categories = set(config.get("categories", []))
        if category not in allowed_categories:
            errors.append(
                format_error(
                    path,
                    (
                        f"invalid category '{category}' for type '{content_type}'; "
                        f"allowed categories: {sorted(allowed_categories)}"
                    ),
                )
            )

    return errors


def main() -> int:
    args = parse_args("Validate taxonomy rules.")
    rules = load_rules(Path(args.rules))
    file_paths = discover_content_files(rules, args.paths)
    errors = validate_taxonomy(file_paths, rules)

    for error in errors:
        print(error)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
