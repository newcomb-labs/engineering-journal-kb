#!/usr/bin/env python3

from __future__ import annotations


from content_validation_common import get_target_files, parse_args
from validate_frontmatter import validate_frontmatter
from validate_lifecycle import validate_lifecycle
from validate_location import validate_location
from validate_taxonomy import validate_taxonomy


def print_section(name: str, errors: list[str]) -> None:
    print(f"\n== {name} ==")
    if errors:
        print(f"FAIL ({len(errors)})")
        for error in errors:
            print(f"- {error}")
    else:
        print("PASS")


def main() -> int:
    args = parse_args()
    files = get_target_files(args.files)

    if not files:
        print("No governed content files matched validation scope.")
        return 0

    print(f"Validated {len(files)} content file(s)")

    frontmatter_errors = validate_frontmatter(files)
    lifecycle_errors = validate_lifecycle(files)
    taxonomy_errors = validate_taxonomy(files)
    location_errors = validate_location(files)

    print_section("Frontmatter", frontmatter_errors)
    print_section("Lifecycle", lifecycle_errors)
    print_section("Taxonomy", taxonomy_errors)
    print_section("Location", location_errors)

    total_errors = (
        len(frontmatter_errors)
        + len(lifecycle_errors)
        + len(taxonomy_errors)
        + len(location_errors)
    )

    print("\n== Summary ==")
    if total_errors:
        print(f"FAIL ({total_errors} total error(s))")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
