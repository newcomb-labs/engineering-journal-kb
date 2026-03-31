#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

from content_validation_common import is_generated_artifact, parse_frontmatter

ALLOWED_TYPES = {"case-study", "doc", "journal", "lab"}
ALLOWED_CATEGORIES = {
    "case-studies",
    "engineering",
    "governance",
    "labs",
    "operations",
}
TYPE_TO_ALLOWED_CATEGORIES = {
    "case-study": {"case-studies"},
    "doc": {"engineering", "governance", "operations"},
    "journal": {"engineering", "operations"},
    "lab": {"labs"},
}


def validate_taxonomy(files: list[Path]) -> list[str]:
    errors: list[str] = []

    for path in files:
        frontmatter, parse_error = parse_frontmatter(path)
        if parse_error:
            continue

        assert frontmatter is not None

        if is_generated_artifact(path, frontmatter):
            continue

        content_type = frontmatter.get("type")
        category = frontmatter.get("category")

        if content_type not in ALLOWED_TYPES:
            allowed = sorted(ALLOWED_TYPES)
            errors.append(
                f"{path}: invalid content type '{content_type}'; allowed values: {allowed}"
            )
            continue

        if category not in ALLOWED_CATEGORIES:
            allowed = sorted(ALLOWED_CATEGORIES)
            errors.append(
                f"{path}: invalid category '{category}'; allowed values: {allowed}"
            )
            continue

        allowed_categories = TYPE_TO_ALLOWED_CATEGORIES[content_type]
        if category not in allowed_categories:
            expected = sorted(allowed_categories)
            errors.append(
                f"{path}: invalid category '{category}' for type '{content_type}'; allowed values: {expected}"
            )

    return errors
