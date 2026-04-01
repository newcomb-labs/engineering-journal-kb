#!/usr/bin/env python3
"""Generate deterministic Phase 3 content artifacts for the docs site.

Outputs:
- website/docs/_generated/content-manifest.json
- website/docs/_generated/glossary.md
- website/docs/_generated/indexes/{labs,journal,case-studies,governance}.md
- website/docs/_generated/_category_.json
- website/docs/_generated/indexes/_category_.json
- managed in-place _category_.json files for top-level docs folders

Design notes:
- Source docs remain the source of truth.
- Generated landing pages live in website/docs/_generated/ and use slug frontmatter
  so URLs remain stable and user-friendly.
- Category metadata files are generated in-place because Docusaurus requires
  `_category_.json` to live in the directory it controls.
- Archived content is excluded from generated navigation/indexes but still appears
  in the manifest with `visible: false`.
- Journal index is generated from blog post metadata.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "website" / "docs"
BLOG_DIR = REPO_ROOT / "blog"
GENERATED_DIR = DOCS_DIR / "_generated"
INDEXES_DIR = GENERATED_DIR / "indexes"
GLOSSARY_PATH = GENERATED_DIR / "glossary.md"
MANIFEST_PATH = GENERATED_DIR / "content-manifest.json"
CONFIG_PATH = REPO_ROOT / ".github" / "governance" / "generated-content.yml"

GENERATED_DIR_NAME = "_generated"

DEFAULT_AREA_ORDER = {
    "labs": 10,
    "case-studies": 20,
    "governance": 30,
    "engineering": 40,
    "operations": 50,
}

DEFAULT_AREA_LABELS = {
    "labs": "Labs",
    "case-studies": "Case Studies",
    "governance": "Governance",
    "engineering": "Engineering",
    "operations": "Operations",
}

DEFAULT_AREA_DESCRIPTIONS = {
    "labs": "Hands-on labs and reproducible exercises.",
    "case-studies": "Troubleshooting and engineering analysis write-ups.",
    "governance": "Repository standards, policies, and operating agreements.",
    "engineering": "Evergreen engineering references and implementation notes.",
    "operations": "Operational runbooks, response docs, and execution guidance.",
}

INDEX_DEFINITIONS = {
    "labs": {
        "title": "Labs Index",
        "description": "Metadata-driven index of hands-on labs.",
        "slug": "/indexes/labs",
        "source": "docs",
        "area": "labs",
    },
    "journal": {
        "title": "Journal Index",
        "description": "Metadata-driven index of dated engineering journal entries.",
        "slug": "/indexes/journal",
        "source": "blog",
        "area": "journal",
    },
    "case-studies": {
        "title": "Case Studies Index",
        "description": "Metadata-driven index of case studies and analysis write-ups.",
        "slug": "/indexes/case-studies",
        "source": "docs",
        "area": "case-studies",
    },
    "governance": {
        "title": "Governance Index",
        "description": "Metadata-driven index of governance and repository policy docs.",
        "slug": "/indexes/governance",
        "source": "docs",
        "area": "governance",
    },
}


@dataclass(frozen=True)
class DocRecord:
    kind: str
    source_path: str
    title: str
    description: str
    area: str
    type: str
    content_type: str
    lifecycle: str
    tags: list[str]
    owners: list[str]
    created_at: str | None
    last_reviewed: str | None
    sidebar_position: int
    sidebar_label: str | None
    visible: bool
    permalink: str
    relative_doc_path: str | None
    glossary_terms: list[str]
    related_content: list[str]


@dataclass(frozen=True)
class BlogRecord:
    source_path: str
    title: str
    description: str
    slug: str
    tags: list[str]
    authors: list[str]
    date: str
    visible: bool
    glossary_terms: list[str]


def load_yaml_frontmatter(path: Path) -> tuple[dict[str, Any], str] | tuple[None, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text

    try:
        frontmatter = yaml.safe_load(parts[1]) or {}
    except Exception as exc:
        raise ValueError(f"Failed to parse frontmatter in {path}: {exc}") from exc

    if not isinstance(frontmatter, dict):
        raise ValueError(f"Frontmatter in {path} must be a mapping")

    body = parts[2].lstrip("\n")
    return frontmatter, body


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True))


def doc_permalink(relative_doc_path: Path) -> str:
    rel = relative_doc_path.as_posix().removesuffix(".md").removesuffix(".mdx")
    if rel.endswith("/index"):
        rel = rel[: -len("/index")]
    return f"/docs/{rel}"


def blog_permalink(slug: str) -> str:
    cleaned = slug.strip()
    if cleaned.startswith("/"):
        return f"/blog{cleaned}"
    return f"/blog/{cleaned}"


def normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def coerce_sidebar_position(value: Any, fallback: int = 9999) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def normalize_term(term: str) -> str:
    return " ".join(term.strip().split())


def anchor_for_term(term: str) -> str:
    return normalize_term(term).lower().replace(" ", "-")


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{CONFIG_PATH} must contain a top-level mapping")
    return data


def collect_docs() -> list[DocRecord]:
    records: list[DocRecord] = []

    for path in sorted(DOCS_DIR.rglob("*.md")) + sorted(DOCS_DIR.rglob("*.mdx")):
        if GENERATED_DIR_NAME in path.parts:
            continue

        frontmatter, _body = load_yaml_frontmatter(path)
        if not frontmatter:
            continue

        relative = path.relative_to(DOCS_DIR)
        if relative.name in {"index.md", "index.mdx"}:
            continue

        area = str(frontmatter.get("category") or relative.parts[0])
        lifecycle = str(
            frontmatter.get("lifecycle") or frontmatter.get("status") or "draft"
        )
        visible = lifecycle != "archived"
        tags = sorted(
            {
                normalize_term(tag)
                for tag in normalize_string_list(frontmatter.get("tags"))
                if normalize_term(tag)
            }
        )
        glossary_terms = sorted(
            {
                normalize_term(term)
                for term in normalize_string_list(frontmatter.get("glossary_terms"))
                + tags
                if normalize_term(term)
            }
        )
        related_content = sorted(
            {
                item
                for item in normalize_string_list(frontmatter.get("related_content"))
                if item
            }
        )

        records.append(
            DocRecord(
                kind="doc",
                source_path=relative.as_posix(),
                title=str(frontmatter.get("title") or path.stem),
                description=str(frontmatter.get("description") or "").strip(),
                area=area,
                type=str(
                    frontmatter.get("type") or frontmatter.get("content_type") or "doc"
                ),
                content_type=str(
                    frontmatter.get("content_type") or frontmatter.get("type") or "doc"
                ),
                lifecycle=lifecycle,
                tags=tags,
                owners=normalize_string_list(frontmatter.get("owners")),
                created_at=frontmatter.get("created_at"),
                last_reviewed=frontmatter.get("last_reviewed"),
                sidebar_position=coerce_sidebar_position(
                    frontmatter.get("sidebar_position")
                ),
                sidebar_label=(
                    str(frontmatter.get("sidebar_label"))
                    if frontmatter.get("sidebar_label")
                    else None
                ),
                visible=visible,
                permalink=doc_permalink(relative),
                relative_doc_path=relative.as_posix(),
                glossary_terms=glossary_terms,
                related_content=related_content,
            )
        )

    return sorted(
        records,
        key=lambda item: (
            item.area,
            item.sidebar_position,
            item.title.lower(),
            item.source_path,
        ),
    )


def collect_blog_posts() -> list[BlogRecord]:
    records: list[BlogRecord] = []
    if not BLOG_DIR.exists():
        return records

    for path in sorted(BLOG_DIR.rglob("*.md")) + sorted(BLOG_DIR.rglob("*.mdx")):
        frontmatter, _body = load_yaml_frontmatter(path)
        if not frontmatter:
            continue

        slug = str(frontmatter.get("slug") or path.stem)
        tags = sorted(
            {
                normalize_term(tag)
                for tag in normalize_string_list(frontmatter.get("tags"))
                if normalize_term(tag)
            }
        )
        glossary_terms = sorted(
            {
                normalize_term(term)
                for term in normalize_string_list(frontmatter.get("glossary_terms"))
                + tags
                if normalize_term(term)
            }
        )
        date_prefix = path.stem.split("-", 3)
        derived_date = "-".join(date_prefix[:3]) if len(date_prefix) >= 3 else ""

        records.append(
            BlogRecord(
                source_path=path.relative_to(REPO_ROOT).as_posix(),
                title=str(frontmatter.get("title") or path.stem),
                description=str(frontmatter.get("description") or "").strip(),
                slug=slug,
                tags=tags,
                authors=normalize_string_list(frontmatter.get("authors")),
                date=str(frontmatter.get("date") or derived_date or ""),
                visible=str(frontmatter.get("draft") or "false").lower() != "true",
                glossary_terms=glossary_terms,
            )
        )

    return sorted(
        records,
        key=lambda item: (item.date, item.title.lower(), item.source_path),
        reverse=True,
    )


def generate_generated_categories(config: dict[str, Any]) -> None:
    generated_meta = (
        config.get("generated", {}) if isinstance(config.get("generated"), dict) else {}
    )

    root_category = {
        "label": str(generated_meta.get("label") or "Browse"),
        "position": int(generated_meta.get("position") or 5),
        "collapsed": False,
        "collapsible": True,
        "link": {
            "type": "generated-index",
            "title": str(generated_meta.get("title") or "Browse"),
            "description": str(
                generated_meta.get("description")
                or "Generated navigation aids, discovery indexes, and the glossary."
            ),
        },
    }
    write_json(GENERATED_DIR / "_category_.json", root_category)

    indexes_category = {
        "label": "Indexes",
        "position": 10,
        "collapsed": False,
        "collapsible": True,
        "link": {
            "type": "generated-index",
            "title": "Indexes",
            "description": "Generated area landing pages for governed content.",
        },
    }
    write_json(INDEXES_DIR / "_category_.json", indexes_category)


def generate_in_place_area_categories(docs: list[DocRecord]) -> None:
    areas = sorted({doc.area for doc in docs if doc.area and doc.area != "journal"})
    for area in areas:
        directory = DOCS_DIR / area
        if not directory.exists() or not directory.is_dir():
            continue

        category_payload = {
            "label": DEFAULT_AREA_LABELS.get(area, area.replace("-", " ").title()),
            "position": DEFAULT_AREA_ORDER.get(area, 999),
            "collapsed": False,
            "collapsible": True,
            "link": {
                "type": "generated-index",
                "description": DEFAULT_AREA_DESCRIPTIONS.get(
                    area,
                    f"Generated landing page for the {area} section.",
                ),
            },
        }
        write_json(directory / "_category_.json", category_payload)


def manifest_payload(
    docs: list[DocRecord], posts: list[BlogRecord]
) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []

    for doc in docs:
        payload.append(
            {
                "area": doc.area,
                "content_type": doc.content_type,
                "created_at": doc.created_at,
                "description": doc.description,
                "glossary_terms": doc.glossary_terms,
                "kind": doc.kind,
                "last_reviewed": doc.last_reviewed,
                "lifecycle": doc.lifecycle,
                "owners": doc.owners,
                "path": doc.permalink,
                "related_content": doc.related_content,
                "sidebar_label": doc.sidebar_label,
                "sidebar_position": doc.sidebar_position,
                "source_path": doc.source_path,
                "tags": doc.tags,
                "title": doc.title,
                "type": doc.type,
                "visible": doc.visible,
                "visibility": {
                    "in_nav": doc.visible,
                    "in_generated_indexes": doc.visible,
                    "direct_access": True,
                    "searchable": True,
                },
            }
        )

    for post in posts:
        payload.append(
            {
                "area": "journal",
                "content_type": "journal",
                "created_at": post.date,
                "description": post.description,
                "glossary_terms": post.glossary_terms,
                "kind": "blog",
                "last_reviewed": None,
                "lifecycle": "active" if post.visible else "draft",
                "owners": post.authors,
                "path": blog_permalink(post.slug),
                "related_content": [],
                "sidebar_label": None,
                "sidebar_position": 9999,
                "source_path": post.source_path,
                "tags": post.tags,
                "title": post.title,
                "type": "journal",
                "visible": post.visible,
                "visibility": {
                    "in_nav": post.visible,
                    "in_generated_indexes": post.visible,
                    "direct_access": True,
                    "searchable": True,
                },
            }
        )

    return sorted(
        payload,
        key=lambda item: (item["area"], item["title"].lower(), item["source_path"]),
    )


def glossary_entries(
    docs: list[DocRecord], posts: list[BlogRecord]
) -> list[tuple[str, list[str]]]:
    occurrences: dict[str, set[str]] = {}

    for doc in docs:
        for term in doc.glossary_terms:
            occurrences.setdefault(term, set()).add(doc.permalink)

    for post in posts:
        for term in post.glossary_terms:
            occurrences.setdefault(term, set()).add(blog_permalink(post.slug))

    return sorted((term, sorted(paths)) for term, paths in occurrences.items())


def generate_glossary(docs: list[DocRecord], posts: list[BlogRecord]) -> None:
    entries = glossary_entries(docs, posts)

    lines = [
        "---",
        "title: Glossary",
        "description: Central glossary of recurring terms detected in governed content.",
        "slug: /glossary",
        "sidebar_label: Glossary",
        "sidebar_position: 20",
        "generated_by: scripts/generate_content_artifacts.py",
        "generated_content: true",
        "---",
        "",
        "# Glossary",
        "",
        "This glossary is generated from governed metadata and is safe to link manually from docs.",
        "Automatic term-link injection can consume the same glossary metadata later without changing the URL contract.",
        "",
    ]

    if not entries:
        lines.extend(["No glossary terms were discovered yet.", ""])
    else:
        for term, paths in entries:
            lines.append(f"## {term}")
            lines.append("")
            lines.append(f"Canonical anchor: `#{anchor_for_term(term)}`")
            lines.append("")
            lines.append("Referenced by:")
            lines.append("")
            for path in paths:
                lines.append(f"- [{path}]({path})")
            lines.append("")

    write_text(GLOSSARY_PATH, "\n".join(lines))


def render_doc_listing(items: list[DocRecord]) -> list[str]:
    lines: list[str] = []
    if not items:
        return ["No visible content is available in this section yet.", ""]

    for item in items:
        lines.append(f"## [{item.title}]({item.permalink})")
        lines.append("")
        if item.description:
            lines.append(item.description)
            lines.append("")
        meta: list[str] = []
        if item.type:
            meta.append(f"Type: `{item.type}`")
        if item.lifecycle:
            meta.append(f"Lifecycle: `{item.lifecycle}`")
        if item.created_at:
            meta.append(f"Created: `{item.created_at}`")
        if item.last_reviewed:
            meta.append(f"Last reviewed: `{item.last_reviewed}`")
        if meta:
            lines.append("- " + " | ".join(meta))
        if item.tags:
            lines.append("- Tags: " + ", ".join(f"`{tag}`" for tag in item.tags))
        if item.related_content:
            lines.append(
                "- Related content: "
                + ", ".join(f"`{path}`" for path in item.related_content)
            )
        lines.append("")

    return lines


def render_blog_listing(items: list[BlogRecord]) -> list[str]:
    lines: list[str] = []
    if not items:
        return ["No visible journal entries are available yet.", ""]

    for item in items:
        permalink = blog_permalink(item.slug)
        lines.append(f"## [{item.title}]({permalink})")
        lines.append("")
        if item.description:
            lines.append(item.description)
            lines.append("")
        meta: list[str] = []
        if item.date:
            meta.append(f"Date: `{item.date}`")
        if item.authors:
            meta.append(
                "Authors: " + ", ".join(f"`{author}`" for author in item.authors)
            )
        if meta:
            lines.append("- " + " | ".join(meta))
        if item.tags:
            lines.append("- Tags: " + ", ".join(f"`{tag}`" for tag in item.tags))
        lines.append("")

    return lines


def generate_indexes(docs: list[DocRecord], posts: list[BlogRecord]) -> None:
    for index_name, definition in INDEX_DEFINITIONS.items():
        lines = [
            "---",
            f"title: {definition['title']}",
            f"description: {definition['description']}",
            f"slug: {definition['slug']}",
            f"sidebar_label: {definition['title'].replace(' Index', '')}",
            f"sidebar_position: {10 + list(INDEX_DEFINITIONS.keys()).index(index_name) * 10}",
            "generated_by: scripts/generate_content_artifacts.py",
            "generated_content: true",
            "---",
            "",
            f"# {definition['title']}",
            "",
            definition["description"],
            "",
        ]

        if definition["source"] == "docs":
            items = [
                doc for doc in docs if doc.area == definition["area"] and doc.visible
            ]
            items = sorted(
                items,
                key=lambda item: (
                    item.sidebar_position,
                    item.title.lower(),
                    item.source_path,
                ),
            )
            lines.extend(render_doc_listing(items))
        else:
            items = [post for post in posts if post.visible]
            lines.extend(render_blog_listing(items))

        write_text(INDEXES_DIR / f"{index_name}.md", "\n".join(lines))


def generate_manifest(docs: list[DocRecord], posts: list[BlogRecord]) -> None:
    write_json(MANIFEST_PATH, manifest_payload(docs, posts))


def main() -> None:
    config = load_config()
    docs = collect_docs()
    posts = collect_blog_posts()

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    INDEXES_DIR.mkdir(parents=True, exist_ok=True)

    generate_generated_categories(config)
    generate_in_place_area_categories(docs)
    generate_indexes(docs, posts)
    generate_glossary(docs, posts)
    generate_manifest(docs, posts)

    print("Generated content artifacts:")
    for path in sorted(GENERATED_DIR.rglob("*")):
        if path.is_file():
            print(f"- {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
