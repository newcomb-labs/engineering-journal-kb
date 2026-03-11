#!/usr/bin/env python3
"""
Sync GitHub labels from .github/labels.yml to a repository.

Features:
- Creates missing labels
- Updates changed labels
- Optionally deletes unmanaged labels with --prune
- Works locally and in CI
- Uses GitHub CLI auth/session via `gh api`

Requirements:
- Python 3.11+
- GitHub CLI (`gh`) installed and authenticated
- PyYAML installed

Examples:
    python scripts/sync_labels.py
    python scripts/sync_labels.py --repo owner/repo
    python scripts/sync_labels.py --prune
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install it with: pip install pyyaml") from exc


DEFAULT_LABEL_FILE = Path(".github/labels.yml")


@dataclass(frozen=True)
class Label:
    name: str
    color: str
    description: str

    @classmethod
    def from_dict(cls, data: dict) -> "Label":
        name = str(data.get("name", "")).strip()
        color = str(data.get("color", "")).strip().lower().lstrip("#")
        description = str(data.get("description", "") or "").strip()

        if not name:
            raise ValueError("Label entry is missing 'name'.")

        if len(color) != 6 or any(ch not in "0123456789abcdef" for ch in color):
            raise ValueError(
                f"Label '{name}' has invalid color '{color}'. Use 6-digit hex."
            )

        return cls(name=name, color=color, description=description)


def run_command(
    cmd: list[str], capture_output: bool = True
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        capture_output=capture_output,
    )


def ensure_dependency(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"Missing required dependency: {name}")


def ensure_gh_auth() -> None:
    try:
        run_command(["gh", "auth", "status"])
    except subprocess.CalledProcessError as exc:
        message = (
            exc.stderr.strip() if exc.stderr else "GitHub CLI is not authenticated."
        )
        raise SystemExit(f"{message}\nRun: gh auth login") from exc


def resolve_repo(explicit_repo: str | None) -> str:
    if explicit_repo:
        return explicit_repo

    try:
        result = run_command(
            ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]
        )
    except subprocess.CalledProcessError as exc:
        message = (
            exc.stderr.strip() if exc.stderr else "Unable to determine repository."
        )
        raise SystemExit(
            f"{message}\nPass --repo owner/name or run inside a GitHub repository."
        ) from exc

    repo = result.stdout.strip()
    if not repo:
        raise SystemExit("Could not determine repository. Pass --repo owner/name.")
    return repo


def load_desired_labels(label_file: Path) -> dict[str, Label]:
    if not label_file.exists():
        raise SystemExit(f"Label file not found: {label_file}")

    with label_file.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, list):
        raise SystemExit("Label file must contain a YAML list of label objects.")

    labels: dict[str, Label] = {}
    for idx, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise SystemExit(f"Label entry #{idx} must be a mapping/object.")

        try:
            label = Label.from_dict(item)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc

        if label.name in labels:
            raise SystemExit(f"Duplicate label name in {label_file}: {label.name}")

        labels[label.name] = label

    return labels


def gh_api_json(
    method: str, endpoint: str, fields: dict[str, str] | None = None
) -> dict | list:
    cmd = ["gh", "api", "--method", method, endpoint]

    if fields:
        for key, value in fields.items():
            cmd.extend(["-f", f"{key}={value}"])

    result = run_command(cmd)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse GitHub API response for {endpoint}") from exc


def fetch_existing_labels(repo: str) -> dict[str, Label]:
    owner, name = repo.split("/", 1)
    endpoint = f"/repos/{owner}/{name}/labels?per_page=100"

    data = gh_api_json("GET", endpoint)
    if not isinstance(data, list):
        raise SystemExit("Unexpected response while listing repository labels.")

    labels: dict[str, Label] = {}
    for item in data:
        label = Label(
            name=str(item.get("name", "")).strip(),
            color=str(item.get("color", "")).strip().lower().lstrip("#"),
            description=str(item.get("description", "") or "").strip(),
        )
        labels[label.name] = label

    return labels


def create_label(repo: str, label: Label) -> None:
    owner, name = repo.split("/", 1)
    endpoint = f"/repos/{owner}/{name}/labels"
    gh_api_json(
        "POST",
        endpoint,
        fields={
            "name": label.name,
            "color": label.color,
            "description": label.description,
        },
    )
    print(f"+ created: {label.name}")


def update_label(repo: str, label: Label) -> None:
    owner, name = repo.split("/", 1)
    endpoint = f"/repos/{owner}/{name}/labels/{label.name}"
    gh_api_json(
        "PATCH",
        endpoint,
        fields={
            "new_name": label.name,
            "color": label.color,
            "description": label.description,
        },
    )
    print(f"~ updated: {label.name}")


def delete_label(repo: str, label_name: str) -> None:
    owner, name = repo.split("/", 1)
    endpoint = f"/repos/{owner}/{name}/labels/{label_name}"
    gh_api_json("DELETE", endpoint)
    print(f"- deleted: {label_name}")


def sync_labels(
    repo: str, desired: dict[str, Label], existing: dict[str, Label], prune: bool
) -> int:
    changes = 0

    for name, desired_label in desired.items():
        current = existing.get(name)

        if current is None:
            create_label(repo, desired_label)
            changes += 1
            continue

        if (
            current.color != desired_label.color
            or current.description != desired_label.description
        ):
            update_label(repo, desired_label)
            changes += 1
        else:
            print(f"= no change: {name}")

    unmanaged = sorted(set(existing) - set(desired))

    if prune:
        for name in unmanaged:
            delete_label(repo, name)
            changes += 1
    elif unmanaged:
        print("\nUnmanaged labels preserved:")
        for name in unmanaged:
            print(f"  - {name}")

    return changes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync GitHub labels from .github/labels.yml"
    )
    parser.add_argument(
        "--repo",
        help="Repository in owner/name format. Defaults to the current gh repo.",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_LABEL_FILE,
        help="Path to labels YAML file (default: .github/labels.yml)",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Delete repository labels not present in the labels file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    ensure_dependency("gh")
    ensure_gh_auth()

    repo = resolve_repo(args.repo)
    desired = load_desired_labels(args.file)
    existing = fetch_existing_labels(repo)

    print(f"Repository: {repo}")
    print(f"Label file: {args.file}")
    print(f"Prune mode: {'enabled' if args.prune else 'disabled'}\n")

    changes = sync_labels(repo, desired, existing, args.prune)

    print(f"\nDone. {changes} change(s) applied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
