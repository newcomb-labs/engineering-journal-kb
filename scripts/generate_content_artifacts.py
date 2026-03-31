#!/usr/bin/env python3

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import yaml

DOCS_DIR = Path("website/docs")
INDEX_DIR = DOCS_DIR / "indexes"


def load_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")

    if not text.startswith("---"):
        return {}

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}

    try:
        return yaml.safe_load(parts[1]) or {}
    except Exception:
        return {}


def collect_documents() -> list[dict]:
    docs = []

    for path in DOCS_DIR.rglob("*.md"):
        if "indexes" in path.parts:
            continue

        fm = load_frontmatter(path)

        if not fm:
            continue

        docs.append(
            {
                "path": path,
                "title": fm.get("title", path.stem),
                "type": fm.get("type", "unknown"),
                "category": fm.get("category", "unknown"),
                "lifecycle": fm.get("lifecycle", "unknown"),
            }
        )

    return docs


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


# ----------------------------
# Prettier-stable table writer
# ----------------------------
def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    align = ["---"] * len(headers)
    align[-1] = "---:"  # right-align last column

    lines = [
        f"| {' | '.join(headers)} |",
        f"| {' | '.join(align)} |",
    ]

    for row in rows:
        lines.append(f"| {' | '.join(str(cell) for cell in row)} |")

    return "\n".join(lines)


# ----------------------------
# Governance summary
# ----------------------------
def generate_governance_summary(docs: list[dict]) -> None:
    total = len(docs)

    type_counts = Counter(d["type"] for d in docs)
    category_counts = Counter(d["category"] for d in docs)
    lifecycle_counts = Counter(d["lifecycle"] for d in docs)

    content = f"""# Governance Summary

Total governed documents: **{total}**

## Counts by Type

{markdown_table(["Type", "Count"], sorted(type_counts.items()))}

## Counts by Category

{markdown_table(["Category", "Count"], sorted(category_counts.items()))}

## Counts by Lifecycle

{markdown_table(["Lifecycle", "Count"], sorted(lifecycle_counts.items()))}

<!-- generated:content:end -->
"""

    write(INDEX_DIR / "governance-summary.md", content)


# ----------------------------
# Simple index generator
# ----------------------------
def generate_index(name: str, docs: list[dict], key: str) -> None:
    filtered = [d for d in docs if d[key] == name]

    lines = [f"# {name.replace('-', ' ').title()}"]

    for d in sorted(filtered, key=lambda x: x["title"].lower()):
        rel = d["path"].relative_to("website/docs")
        lines.append(f"- [{d['title']}](/docs/{rel.as_posix().replace('.md', '')})")

    write(INDEX_DIR / f"{name}.md", "\n".join(lines))


# ----------------------------
# Master index
# ----------------------------
def generate_root_index(docs: list[dict]) -> None:
    lines = ["# Index"]

    for d in sorted(docs, key=lambda x: x["title"].lower()):
        rel = d["path"].relative_to("website/docs")
        lines.append(f"- [{d['title']}](/docs/{rel.as_posix().replace('.md', '')})")

    write(INDEX_DIR / "index.md", "\n".join(lines))


# ----------------------------
# Manifest
# ----------------------------
def generate_manifest(docs: list[dict]) -> None:
    manifest = []

    for d in docs:
        rel = d["path"].relative_to("website/docs")

        manifest.append(
            {
                "title": d["title"],
                "path": f"/docs/{rel.as_posix().replace('.md', '')}",
                "type": d["type"],
                "category": d["category"],
                "lifecycle": d["lifecycle"],
            }
        )

    write(
        INDEX_DIR / "content-manifest.json",
        json.dumps(manifest, indent=2),
    )


# ----------------------------
# Main
# ----------------------------
def main() -> None:
    docs = collect_documents()

    generate_governance_summary(docs)
    generate_root_index(docs)
    generate_manifest(docs)

    # Generate per-category indexes
    for category in sorted(set(d["category"] for d in docs)):
        generate_index(category, docs, "category")

    # Generate per-category indexes
    for category in sorted(set(d["category"] for d in docs)):
        generate_index(category, docs, "category")

    print("Generated content artifacts:")
    for p in sorted(INDEX_DIR.glob("*")):
        print(f"- {p}")


if __name__ == "__main__":
    main()
