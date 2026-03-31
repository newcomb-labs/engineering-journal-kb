#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

from content_validation_common import is_generated_artifact, parse_frontmatter

ALLOWED_LIFECYCLES = {"draft", "review", "published", "archived"}
PUBLISHED_REQUIRED_FIELDS = {"title", "description", "type", "category", "tags"}


def validate_lifecycle(files: list[Path]) -> list[str]:
    errors: list[str] = []

    for path in files:
        frontmatter, parse_error = parse_frontmatter(path)
        if parse_error:
            continue

        assert frontmatter is not None

        if is_generated_artifact(path, frontmatter):
            continue

        lifecycle = frontmatter.get("lifecycle")
        if not isinstance(lifecycle, str) or not lifecycle.strip():
            errors.append(
                f"{path}: frontmatter field 'lifecycle' must be a non-empty string"
            )
            continue

        if lifecycle not in ALLOWED_LIFECYCLES:
            allowed = sorted(ALLOWED_LIFECYCLES)
            errors.append(
                f"{path}: invalid lifecycle '{lifecycle}'; allowed values: {allowed}"
            )
            continue

        if lifecycle == "published":
            for field in sorted(PUBLISHED_REQUIRED_FIELDS):
                value = frontmatter.get(field)
                if value is None or (isinstance(value, str) and not value.strip()):
                    errors.append(
                        f"{path}: published content requires non-empty frontmatter field '{field}'"
                    )

    return errors
