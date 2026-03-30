#!/usr/bin/env python3
"""Validate markdown frontmatter structure and field types."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from content_validation_common import (
    discover_content_files,
    extract_frontmatter,
    format_error,
    is_nonempty_string,
    load_rules,
    matches_expected_type,
    parse_args,
    type_name,
)


def validate_frontmatter(
    file_paths: list[Path],
    rules: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    frontmatter_rules = rules.get("frontmatter", {})
    required_fields = frontmatter_rules.get("required_fields", [])
    field_rules = frontmatter_rules.get("fields", {})

    for path in file_paths:
        frontmatter, _ = extract_frontmatter(path)

        if frontmatter is None:
            errors.append(format_error(path, "missing valid YAML frontmatter block"))
            continue

        for field in required_fields:
            if field not in frontmatter:
                errors.append(
                    format_error(path, f"missing required frontmatter field '{field}'")
                )
                continue

            value = frontmatter.get(field)
            if isinstance(value, str) and not is_nonempty_string(value):
                errors.append(
                    format_error(path, f"required field '{field}' must be non-empty")
                )
            if isinstance(value, list) and len(value) == 0:
                errors.append(
                    format_error(path, f"required field '{field}' must not be empty")
                )

        for field_name, field_config in field_rules.items():
            if not isinstance(field_config, dict):
                continue

            required = field_config.get("required", True)
            expected_type = field_config.get("type")

            if field_name not in frontmatter:
                if required and field_name in required_fields:
                    errors.append(
                        format_error(
                            path, f"missing required frontmatter field '{field_name}'"
                        )
                    )
                continue

            value = frontmatter[field_name]

            if expected_type and not matches_expected_type(value, expected_type):
                errors.append(
                    format_error(
                        path,
                        f"field '{field_name}' expected type '{expected_type}', got '{type_name(value)}'",
                    )
                )

            if expected_type == "list" and isinstance(value, list):
                for index, item in enumerate(value):
                    if not isinstance(item, str):
                        errors.append(
                            format_error(
                                path,
                                f"field '{field_name}' item at index {index} must be a string",
                            )
                        )

    return errors


def main() -> int:
    args = parse_args("Validate markdown frontmatter.")
    rules = load_rules(Path(args.rules))
    file_paths = discover_content_files(rules, args.paths)
    errors = validate_frontmatter(file_paths, rules)

    for error in errors:
        print(error)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
