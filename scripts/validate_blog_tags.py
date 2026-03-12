#!/usr/bin/env python3

import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
BLOG_DIR = ROOT / "website" / "blog"
TAGS_FILE = BLOG_DIR / "tags.yml"

TAG_PATTERN = re.compile(r"tags:\s*\[(.*?)\]")


def load_tags():
    with open(TAGS_FILE) as f:
        data = yaml.safe_load(f)

    return set(data.keys())


def extract_tags(md_file):
    content = md_file.read_text()

    match = TAG_PATTERN.search(content)

    if not match:
        return []

    tags = match.group(1)
    return [t.strip() for t in tags.split(",")]


def main():
    valid_tags = load_tags()
    errors = []

    for md in BLOG_DIR.glob("*.md"):
        tags = extract_tags(md)

        for tag in tags:
            if tag not in valid_tags:
                errors.append(f"{md.name}: undefined tag '{tag}'")

    if errors:
        print("\n❌ Undefined blog tags detected:\n")
        for err in errors:
            print(" -", err)

        sys.exit(1)

    print("✅ Blog tags validated successfully")


if __name__ == "__main__":
    main()
