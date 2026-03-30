#!/usr/bin/env python3
"""Validate lifecycle states and state-based requirements."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from content_validation_common import (
    discover_content_files,
    extract_frontmatter,
    format_error,
    is_nonempty_list,
    is_nonempty_string,
    load_rules,
    parse_args,
)


def has_nonempty_value(value: Any) -> bool:
    if isinstance(value, str):
        return is_nonempty_string(value)
    if isinstance(value, list):
        return is_nonempty_list(value)
    return value is not None


def validate_lifecycle(
    file_paths: list[Path],
    rules: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    lifecycle_rules = rules.get("lifecycle", {})
    allowed_states = set(lifecycle_rules.get("allowed", []))
    state_requirements = lifecycle_rules.get("state_requirements", {})

    for path in file_paths:
        frontmatter, _ = extract_frontmatter(path)
        if frontmatter is None:
            continue

        lifecycle = frontmatter.get("lifecycle")
        if not isinstance(lifecycle, str) or lifecycle.strip() == "":
            errors.append(
                format_error(
                    path, "frontmatter field 'lifecycle' must be a non-empty string"
                )
            )
            continue

        if lifecycle not in allowed_states:
            errors.append(
                format_error(
                    path,
                    f"invalid lifecycle '{lifecycle}'; allowed values: {sorted(allowed_states)}",
                )
            )
            continue

        for field_name in state_requirements.get(lifecycle, []):
            value = frontmatter.get(field_name)
            if not has_nonempty_value(value):
                errors.append(
                    format_error(
                        path,
                        f"lifecycle '{lifecycle}' requires non-empty field '{field_name}'",
                    )
                )

    return errors


def main() -> int:
    args = parse_args("Validate lifecycle rules.")
    rules = load_rules(Path(args.rules))
    file_paths = discover_content_files(rules, args.paths)
    errors = validate_lifecycle(file_paths, rules)

    for error in errors:
        print(error)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
