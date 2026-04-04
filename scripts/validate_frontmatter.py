#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

import yaml
from content_validation_common import is_generated_artifact, parse_frontmatter

SCHEMA_PATH = Path(".github/governance/frontmatter-schema.yml")


def load_schema() -> dict:
    return yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8")) or {}


def validate_frontmatter(files: list[Path]) -> list[str]:
    schema = load_schema()
    required_fields = schema.get("required", [])

    errors: list[str] = []

    for path in files:
        frontmatter, parse_error = parse_frontmatter(path)
        if parse_error:
            errors.append(f"{path}: {parse_error}")
            continue

        assert frontmatter is not None

        if is_generated_artifact(path, frontmatter):
            continue

        for field in required_fields:
            value = frontmatter.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"{path}: missing required frontmatter field '{field}'")

    return errors
