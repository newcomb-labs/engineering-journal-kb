#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

PSEUDO_HEADINGS = {
    "Command",
    "Expected Output",
    "Actual Output",
    "Observed Failure",
    "Expected Result",
    "What this shows",
    "Why it matters",
    "Why this matters",
    "Production approach",
}

TITLE_CASE_HEADINGS = {
    "Cloned Identity Collision",
}

TAG_WORD_RE = re.compile(r"#([A-Za-z0-9_-]+)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
BOLD_ONLY_RE = re.compile(r"^\*\*(.+?)\*\*\s*$")
TITLE_RE = re.compile(r"^title:\s+.+$", re.IGNORECASE)


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text

    end = text.find("\n---\n", 4)
    if end == -1:
        return "", text

    frontmatter = text[: end + 5]
    body = text[end + 5 :]
    return frontmatter, body


def normalize_path(path: Path) -> str:
    return path.as_posix()


def is_intro_doc(path: Path) -> bool:
    return normalize_path(path) == "website/docs/intro.md"


def has_title_in_frontmatter(frontmatter: str) -> bool:
    if not frontmatter:
        return False
    return any(TITLE_RE.match(line.strip()) for line in frontmatter.splitlines())


def fix_pseudo_headings(body: str) -> str:
    lines = body.splitlines()
    fixed: list[str] = []

    for line in lines:
        match = BOLD_ONLY_RE.match(line)
        if not match:
            fixed.append(line)
            continue

        text = match.group(1).strip()
        if text in PSEUDO_HEADINGS:
            fixed.append(f"#### {text}")
        else:
            fixed.append(line)

    return "\n".join(fixed)


def fix_loose_title_case_lines(body: str) -> str:
    lines = body.splitlines()
    fixed: list[str] = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped in TITLE_CASE_HEADINGS:
            prev_line = lines[i - 1].strip() if i > 0 else ""
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""

            is_heading = stripped.startswith("#")
            is_code_fence = stripped.startswith("```")

            if not is_heading and not is_code_fence:
                if prev_line.startswith("### ") or prev_line.startswith("## "):
                    fixed.append(f"#### {stripped}")
                    continue
                if (
                    next_line.startswith("- ")
                    or next_line.startswith("```")
                    or next_line == ""
                ):
                    fixed.append(f"#### {stripped}")
                    continue

        fixed.append(line)

    return "\n".join(fixed)


def fix_tag_lines(body: str) -> str:
    lines = body.splitlines()
    fixed: list[str] = []

    for line in lines:
        stripped = line.strip()

        if stripped.lower().startswith("tags:"):
            tags = TAG_WORD_RE.findall(stripped)
            if tags:
                fixed.append("Tags: " + ", ".join(tags))
            else:
                fixed.append(line)
            continue

        tags = TAG_WORD_RE.findall(stripped)
        if tags and stripped.replace(" ", "").startswith("#"):
            fixed.append("Tags: " + ", ".join(tags))
            continue

        fixed.append(line)

    return "\n".join(fixed)


def normalize_headings(path: Path, frontmatter: str, body: str) -> str:
    lines = body.splitlines()
    fixed: list[str] = []
    first_heading_seen = False

    intro_doc = is_intro_doc(path)
    titled_frontmatter = has_title_in_frontmatter(frontmatter)

    for line in lines:
        match = HEADING_RE.match(line)
        if not match:
            fixed.append(line)
            continue

        level = len(match.group(1))
        text = match.group(2)

        if not first_heading_seen:
            first_heading_seen = True

            if intro_doc:
                fixed.append(f"# {text}")
            elif titled_frontmatter:
                fixed.append(f"## {text}")
            else:
                fixed.append(f"# {text}")
            continue

        if level == 1:
            fixed.append(f"## {text}")
        else:
            fixed.append(line)

    return "\n".join(fixed)


def ensure_trailing_newline(text: str) -> str:
    return text.rstrip("\n") + "\n"


def process_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(original)

    updated = body
    updated = fix_pseudo_headings(updated)
    updated = fix_loose_title_case_lines(updated)
    updated = fix_tag_lines(updated)
    updated = normalize_headings(path, frontmatter, updated)

    new_text = ensure_trailing_newline(frontmatter + updated)

    if new_text != original:
        path.write_text(new_text, encoding="utf-8")
        print(f"fixed {path}")
        return True

    return False


def main(argv: list[str]) -> int:
    changed = False

    for name in argv[1:]:
        path = Path(name)
        if not path.exists() or path.suffix.lower() != ".md":
            continue
        if process_file(path):
            changed = True

    return 1 if changed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
