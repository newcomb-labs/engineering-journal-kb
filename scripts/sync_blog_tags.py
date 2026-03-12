#!/usr/bin/env python3

import re
from pathlib import Path

import yaml

BLOG_DIR = Path("website/blog")
TAGS_FILE = BLOG_DIR / "tags.yml"

tag_pattern = re.compile(r"tags:\s*\[(.*?)\]")

tags_found = set()

for post in BLOG_DIR.glob("*.md*"):
    text = post.read_text()
    match = tag_pattern.search(text)
    if match:
        tags = [t.strip() for t in match.group(1).split(",")]
        tags_found.update(tags)

existing = {}
if TAGS_FILE.exists():
    existing = yaml.safe_load(TAGS_FILE.read_text()) or {}

for tag in tags_found:
    if tag not in existing:
        existing[tag] = {
            "label": tag.capitalize(),
            "permalink": f"/{tag}",
            "description": f"Posts tagged with {tag}",
        }

with open(TAGS_FILE, "w") as f:
    yaml.dump(existing, f, sort_keys=True)

print("✔ Blog tags synced")
