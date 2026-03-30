#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

from content_validation_common import parse_frontmatter

TYPE_TO_REQUIRED_DIRECTORY = {
    "case-study": Path("website/docs/case-studies"),
    "doc": None,
    "journal": None,
    "lab": Path("website/docs/labs"),
}


def validate_location(files: list[Path]) -> list[str]:
    errors: list[str] = []

    for path in files:
        frontmatter, parse_error = parse_frontmatter(path)
        if parse_error:
            continue

        assert frontmatter is not None

        content_type = frontmatter.get("type")
        required_dir = TYPE_TO_REQUIRED_DIRECTORY.get(content_type)

        if required_dir is None:
            continue

        if required_dir not in path.parents:
            errors.append(
                f"{path}: content type '{content_type}' must live under '{required_dir}'"
            )

    return errors
