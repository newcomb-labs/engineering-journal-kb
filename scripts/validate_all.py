#!/usr/bin/env python3
"""Run all content governance validators with structured output."""

from __future__ import annotations

import sys
from pathlib import Path

from content_validation_common import discover_content_files, load_rules, parse_args
from validate_frontmatter import validate_frontmatter
from validate_lifecycle import validate_lifecycle
from validate_location import validate_location
from validate_taxonomy import validate_taxonomy


def print_section(title: str, errors: list[str]) -> None:
    print(f"== {title} ==")
    if errors:
        print(f"FAIL ({len(errors)})")
        for error in errors:
            print(f"- {error}")
    else:
        print("PASS")
    print("")


def main() -> int:
    args = parse_args("Run all content governance validators.")
    rules = load_rules(Path(args.rules))
    file_paths = discover_content_files(rules, args.paths)

    results = {
        "Frontmatter": validate_frontmatter(file_paths, rules),
        "Lifecycle": validate_lifecycle(file_paths, rules),
        "Taxonomy": validate_taxonomy(file_paths, rules),
        "Location": validate_location(file_paths, rules),
    }

    print(f"Validated {len(file_paths)} content file(s)")
    print("")

    total_errors = 0
    for title, errors in results.items():
        print_section(title, errors)
        total_errors += len(errors)

    print("== Summary ==")
    if total_errors:
        print(f"FAIL ({total_errors} total error(s))")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
