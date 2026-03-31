#!/usr/bin/env python3
"""
generate_content_artifacts.py

Generates deterministic content artifacts for the Engineering Journal:

- Index pages per category
- Governance summary
- Content manifest (JSON)

Guarantees:
- Stable ordering (sorted paths)
- No inclusion of generated files
- Docusaurus-safe links
- Deterministic output across environments
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import yaml

REPO_ROOT = Path(".").resolve()
DOCS_DIR = REPO_ROOT / "website" / "docs"
INDEX_DIR = DOCS_DIR / "indexes"

GENERATED_DIR_NAME = "indexes"


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def load_frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")

    if not text.startswith("---"):
        return None

    parts = text.split("---", 2)
    if len(parts) < 3:
        return None

    try:
        return yaml.safe_load(parts[1]) or {}
    except Exception:
        return None


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def doc_link_from_path(path: Path) -> str:
    rel = path.relative_to(DOCS_DIR).as_posix().replace(".md", "")
    if rel.endswith("/index"):
        rel = rel[:-6]
    return f"/docs/{rel}"


# ------------------------------------------------------------
# Collect documents (DETERMINISTIC)
# ------------------------------------------------------------
def collect_documents() -> list[dict]:
    docs: list[dict] = []

    for path in sorted(DOCS_DIR.rglob("*.md")):
        # Skip generated content
        if GENERATED_DIR_NAME in path.parts:
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


# ------------------------------------------------------------
# Manifest (DETERMINISTIC)
# ------------------------------------------------------------
def generate_manifest(docs: list[dict]) -> None:
    manifest = []

    for doc in sorted(docs, key=lambda item: item["path"].as_posix()):
        manifest.append(
            {
                "title": doc["title"],
                "path": doc_link_from_path(doc["path"]),
                "type": doc["type"],
                "category": doc["category"],
                "lifecycle": doc["lifecycle"],
            }
        )

    write(
        INDEX_DIR / "content-manifest.json",
        json.dumps(manifest, indent=2, sort_keys=True),
    )


# ------------------------------------------------------------
# Governance summary
# ------------------------------------------------------------
def generate_governance_summary(docs: list[dict]) -> None:
    type_counts = Counter(doc["type"] for doc in docs)
    category_counts = Counter(doc["category"] for doc in docs)
    lifecycle_counts = Counter(doc["lifecycle"] for doc in docs)

    def table(title: str, data: dict[str, int]) -> str:
        lines = [f"## {title}", "", "| Value | Count |", "| --- | ---: |"]
        for key in sorted(data.keys()):
            lines.append(f"| {key} | {data[key]} |")
        return "\n".join(lines)

    content = [
        "# Governance Summary",
        "",
        f"Total governed documents: **{len(docs)}**",
        "",
        table("Counts by Type", type_counts),
        "",
        table("Counts by Category", category_counts),
        "",
        table("Counts by Lifecycle", lifecycle_counts),
    ]

    write(INDEX_DIR / "governance-summary.md", "\n".join(content))


# ------------------------------------------------------------
# Category indexes
# ------------------------------------------------------------
def generate_category_indexes(docs: list[dict]) -> None:
    grouped: defaultdict[str, list[dict]] = defaultdict(list)

    for doc in docs:
        grouped[doc["category"]].append(doc)

    for category in sorted(grouped.keys()):
        items = sorted(grouped[category], key=lambda item: item["path"].as_posix())

        lines = [f"# {category.title()} Index", ""]

        for doc in items:
            link = doc_link_from_path(doc["path"])
            lines.append(f"- [{doc['title']}]({link})")

        write(INDEX_DIR / f"{category}.md", "\n".join(lines))


# ------------------------------------------------------------
# Root index
# ------------------------------------------------------------
def generate_root_index(docs: list[dict]) -> None:
    categories = sorted(set(doc["category"] for doc in docs))

    lines = ["# Content Index", ""]

    for category in categories:
        lines.append(f"- [{category.title()}](/docs/indexes/{category})")

    write(INDEX_DIR / "index.md", "\n".join(lines))


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main() -> None:
    docs = collect_documents()

    generate_manifest(docs)
    generate_governance_summary(docs)
    generate_category_indexes(docs)
    generate_root_index(docs)

    print("Generated content artifacts:")
    for path in sorted(INDEX_DIR.glob("*")):
        print(f"- {path}")


if __name__ == "__main__":
    main()
