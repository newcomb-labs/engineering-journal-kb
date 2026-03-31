#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

API_BASE = "https://api.github.com"
CHECKLIST_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s*#(\d+)\b", re.MULTILINE)
MANAGED_BLOCK_RE = re.compile(
    r"<!-- managed:epic-progress:start -->.*?<!-- managed:epic-progress:end -->",
    re.DOTALL,
)


@dataclass(frozen=True)
class ChildIssueStatus:
    number: int
    state: str | None
    exists: bool
    accessible: bool


@dataclass(frozen=True)
class EpicProgress:
    total: int
    completed: int
    open_count: int
    invalid_references: list[int]


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
            "User-Agent": "engineering-journal-kb-epic-progress",
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


def get_issue(owner: str, repo: str, number: int, token: str) -> dict[str, Any]:
    url = f"{API_BASE}/repos/{owner}/{repo}/issues/{number}"
    return github_get(url, token)


def search_parent_epics(
    owner: str, repo: str, child_number: int, token: str
) -> list[dict[str, Any]]:
    query = f'repo:{owner}/{repo} is:issue label:"type:epic" "#{child_number}" in:body'
    encoded = urllib.parse.quote(query, safe="")
    url = f"{API_BASE}/search/issues?q={encoded}&per_page=100"
    data = github_get(url, token)
    return data.get("items", [])


def extract_child_numbers(body: str) -> list[int]:
    seen: set[int] = set()
    numbers: list[int] = []
    for match in CHECKLIST_RE.finditer(body):
        number = int(match.group(1))
        if number in seen:
            continue
        seen.add(number)
        numbers.append(number)
    return numbers


def get_child_status(
    owner: str, repo: str, number: int, token: str
) -> ChildIssueStatus:
    try:
        issue = get_issue(owner, repo, number, token)
    except urllib.error.HTTPError as exc:
        if exc.code in {403, 404}:
            return ChildIssueStatus(
                number=number, state=None, exists=False, accessible=False
            )
        raise

    return ChildIssueStatus(
        number=number,
        state=issue.get("state"),
        exists=True,
        accessible=True,
    )


def compute_progress(
    owner: str, repo: str, child_numbers: list[int], token: str
) -> EpicProgress:
    statuses = [
        get_child_status(owner, repo, number, token) for number in child_numbers
    ]
    valid_statuses = [
        status for status in statuses if status.exists and status.accessible
    ]
    invalid_references = [
        status.number
        for status in statuses
        if not (status.exists and status.accessible)
    ]
    completed = sum(1 for status in valid_statuses if status.state == "closed")
    total = len(valid_statuses)
    return EpicProgress(
        total=total,
        completed=completed,
        open_count=max(total - completed, 0),
        invalid_references=invalid_references,
    )


def render_progress_bar(completed: int, total: int) -> str:
    if total <= 0:
        return "░" * 10
    percentage = round((completed / total) * 100)
    filled = round(percentage / 10)
    filled = max(0, min(10, filled))
    return "█" * filled + "░" * (10 - filled)


def build_managed_block(progress: EpicProgress) -> str:
    percentage = (
        0 if progress.total == 0 else round((progress.completed / progress.total) * 100)
    )
    invalid_text = (
        ", ".join(f"#{number}" for number in progress.invalid_references)
        if progress.invalid_references
        else "none"
    )
    return "\n".join(
        [
            "<!-- managed:epic-progress:start -->",
            f"Progress: {render_progress_bar(progress.completed, progress.total)} {percentage}% ({progress.completed}/{progress.total})",
            f"- Total child issues: {progress.total}",
            f"- Completed child issues: {progress.completed}",
            f"- Open child issues: {progress.open_count}",
            f"- Invalid references: {invalid_text}",
            "<!-- managed:epic-progress:end -->",
        ]
    )


def upsert_managed_block(body: str, block: str) -> str:
    stripped = body.rstrip()
    if MANAGED_BLOCK_RE.search(stripped):
        return MANAGED_BLOCK_RE.sub(block, stripped) + "\n"
    if not stripped:
        return block + "\n"
    return stripped + "\n\n" + block + "\n"


def refresh_parent_epic(owner: str, repo: str, parent_number: int, token: str) -> None:
    parent = get_issue(owner, repo, parent_number, token)
    body = parent.get("body") or ""
    child_numbers = extract_child_numbers(body)

    progress = compute_progress(owner, repo, child_numbers, token)
    block = build_managed_block(progress)
    new_body = upsert_managed_block(body, block)

    if new_body == body:
        print(f"parent #{parent_number}: progress already up to date")
        return

    github_patch(
        f"{API_BASE}/repos/{owner}/{repo}/issues/{parent_number}",
        token,
        {"body": new_body},
    )
    print(f"parent #{parent_number}: progress updated")


def handle_single_epic(owner: str, repo: str, epic_number: int, token: str) -> None:
    refresh_parent_epic(owner, repo, epic_number, token)


def handle_child_issue_event(
    owner: str, repo: str, child_number: int, token: str
) -> None:
    parents = search_parent_epics(owner, repo, child_number, token)
    if not parents:
        print(f"No parent epics reference child issue #{child_number}")
        return

    for parent in parents:
        refresh_parent_epic(owner, repo, int(parent["number"]), token)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--epic-number", type=int, help="Refresh a specific epic issue number."
    )
    parser.add_argument(
        "--issue-number",
        type=int,
        help="Refresh epics that reference a changed child issue.",
    )
    args = parser.parse_args()

    token = env("GITHUB_TOKEN")
    repository = env("GITHUB_REPOSITORY")
    owner, repo = repository.split("/", 1)

    if args.epic_number:
        handle_single_epic(owner, repo, args.epic_number, token)
        return

    issue_number = args.issue_number or int(env("ISSUE_NUMBER"))
    handle_child_issue_event(owner, repo, issue_number, token)


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
