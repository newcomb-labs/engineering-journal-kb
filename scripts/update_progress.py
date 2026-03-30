#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

API_BASE = "https://api.github.com"
CHECKLIST_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s*#(\d+)\b", re.MULTILINE)
MARKER_RE = re.compile(
    r".*?",
    re.DOTALL,
)


def env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def request_json(
    method: str,
    url: str,
    token: str,
    payload: dict[str, Any] | None = None,
) -> Any:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        method=method,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "engineering-journal-kb-progress-bot",
        },
    )

    with urllib.request.urlopen(request) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        raw = response.read().decode(charset)
        return json.loads(raw) if raw else None


def github_get(url: str, token: str) -> Any:
    return request_json("GET", url, token)


def github_patch(url: str, token: str, payload: dict[str, Any]) -> Any:
    return request_json("PATCH", url, token, payload)


def search_parent_epics(
    owner: str, repo: str, child_number: int, token: str
) -> list[dict[str, Any]]:
    query = f'repo:{owner}/{repo} is:issue label:"type:epic" "#{child_number}" in:body'
    encoded = urllib.parse.quote(query, safe="")
    url = f"{API_BASE}/search/issues?q={encoded}&per_page=100"
    data = github_get(url, token)
    return data.get("items", [])


def get_issue(owner: str, repo: str, number: int, token: str) -> dict[str, Any]:
    url = f"{API_BASE}/repos/{owner}/{repo}/issues/{number}"
    return github_get(url, token)


def get_children_status(
    owner: str, repo: str, child_numbers: list[int], token: str
) -> int:
    """Optimized check to see how many child issues are closed in one API call."""
    if not child_numbers:
        return 0
    numbers_query = " ".join([f"number:{n}" for n in child_numbers])
    query = f"repo:{owner}/{repo} is:issue is:closed {numbers_query}"
    encoded = urllib.parse.quote(query)
    url = f"{API_BASE}/search/issues?q={encoded}"
    data = github_get(url, token)
    return data.get("total_count", 0)


def extract_child_numbers(body: str) -> list[int]:
    return [int(match.group(1)) for match in CHECKLIST_RE.finditer(body)]


def render_progress_bar(closed_count: int, total_count: int) -> str:
    if total_count <= 0:
        return "░" * 10
    percentage = round((closed_count / total_count) * 100)
    filled = round(percentage / 10)
    filled = max(0, min(10, filled))
    return "█" * filled + "░" * (10 - filled)


def build_progress_block(closed_count: int, total_count: int) -> str:
    percentage = 0 if total_count == 0 else round((closed_count / total_count) * 100)
    bar = render_progress_bar(closed_count, total_count)
    line = f"Progress: {bar} {percentage}% ({closed_count}/{total_count})"
    return f"\n{line}\n"


def upsert_progress_block(body: str, block: str) -> str:
    if MARKER_RE.search(body):
        return MARKER_RE.sub(block, body)

    stripped = body.rstrip()
    if not stripped:
        return block + "\n"

    return f"{stripped}\n\n{block}\n"


def refresh_parent_epic(owner: str, repo: str, parent_number: int, token: str) -> None:
    parent = get_issue(owner, repo, parent_number, token)
    body = parent.get("body") or ""
    child_numbers = extract_child_numbers(body)

    if not child_numbers:
        print(f"parent #{parent_number}: no checklist issue references found; skipping")
        return

    # Using the optimized search instead of a loop for better performance
    closed_count = get_children_status(owner, repo, child_numbers, token)

    new_block = build_progress_block(closed_count, len(child_numbers))
    new_body = upsert_progress_block(body, new_block)

    if new_body == body:
        print(f"parent #{parent_number}: progress already up to date")
        return

    url = f"{API_BASE}/repos/{owner}/{repo}/issues/{parent_number}"
    github_patch(url, token, {"body": new_body})
    print(f"parent #{parent_number}: progress updated")


def main() -> None:
    token = env("GITHUB_TOKEN")
    repository = env("GITHUB_REPOSITORY")
    child_issue_number = int(env("ISSUE_NUMBER"))

    owner, repo = repository.split("/", 1)
    parents = search_parent_epics(owner, repo, child_issue_number, token)

    if not parents:
        print(f"no parent epics reference child issue #{child_issue_number}")
        return

    for parent in parents:
        refresh_parent_epic(owner, repo, int(parent["number"]), token)


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        print(message, file=sys.stderr)
        raise
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
