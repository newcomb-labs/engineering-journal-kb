#!/usr/bin/env python3
"""Validate generated content freshness for Phase 3 artifacts.

The validator regenerates content in an isolated temp copy of the repository and
compares the configured managed outputs with the checked-in versions.
"""

from __future__ import annotations

import filecmp
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GENERATED_DIR = REPO_ROOT / "website" / "docs" / "_generated"
CONFIG_PATH = REPO_ROOT / ".github" / "governance" / "generated-content.yml"

SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    "dist",
    "build",
}

SKIP_FILE_NAMES = {".DS_Store"}


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping at the top level")
    return data


def normalize_path_values(values: Any) -> list[Path]:
    if values is None:
        return []
    if isinstance(values, (str, Path)):
        return [Path(str(values))]
    if isinstance(values, list):
        return [Path(str(value)) for value in values if isinstance(value, (str, Path))]
    return []


def resolve_generated_paths(config: dict[str, Any]) -> list[Path]:
    candidates: list[Path] = []

    generated_outputs = config.get("generated_outputs")
    if isinstance(generated_outputs, dict):
        docs_root = generated_outputs.get("docs_root")
        if docs_root:
            candidates.extend(normalize_path_values(docs_root))
        candidates.extend(normalize_path_values(generated_outputs.get("files")))

    candidates.extend(normalize_path_values(config.get("generated_paths")))
    candidates.extend(normalize_path_values(config.get("managed_paths")))
    candidates.extend(normalize_path_values(config.get("artifacts")))

    generated = config.get("generated")
    if isinstance(generated, dict):
        candidates.extend(normalize_path_values(generated.get("paths")))
        candidates.extend(normalize_path_values(generated.get("artifacts")))

    if not candidates:
        candidates = [DEFAULT_GENERATED_DIR.relative_to(REPO_ROOT)]

    resolved: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        absolute = (REPO_ROOT / candidate).resolve()
        if absolute in seen:
            continue
        seen.add(absolute)
        resolved.append(absolute)

    return sorted(resolved)


def should_skip_dir(dirname: str) -> bool:
    return dirname in SKIP_DIR_NAMES


def should_skip_file(filename: str) -> bool:
    return filename in SKIP_FILE_NAMES


def copy_repo_to_temp(temp_root: Path) -> Path:
    temp_repo = temp_root / "repo"
    temp_repo.mkdir(parents=True, exist_ok=True)

    for root, dirs, files in os.walk(REPO_ROOT):
        root_path = Path(root)
        dirs[:] = [dirname for dirname in dirs if not should_skip_dir(dirname)]

        rel_root = root_path.relative_to(REPO_ROOT)
        dest_root = temp_repo / rel_root
        dest_root.mkdir(parents=True, exist_ok=True)

        for filename in files:
            if should_skip_file(filename):
                continue
            shutil.copy2(root_path / filename, dest_root / filename)

    return temp_repo


def run_generator(temp_repo: Path) -> None:
    generator = temp_repo / "scripts" / "generate_content_artifacts.py"
    if not generator.exists():
        raise FileNotFoundError(f"Generator script not found: {generator}")

    result = subprocess.run(
        [sys.executable, str(generator)],
        cwd=temp_repo,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        message = [
            "ERROR: generated artifact regeneration failed in validation sandbox."
        ]
        if result.stdout.strip():
            message.extend(["", "STDOUT:", result.stdout.strip()])
        if result.stderr.strip():
            message.extend(["", "STDERR:", result.stderr.strip()])
        raise RuntimeError("\n".join(message))


def compare_files(src: Path, dst: Path, mismatches: list[str]) -> None:
    if not src.exists() and not dst.exists():
        return
    if src.exists() and not dst.exists():
        mismatches.append(
            f"Missing generated file in repository: {src.relative_to(REPO_ROOT)}"
        )
        return
    if not src.exists() and dst.exists():
        mismatches.append(
            f"Unexpected generated file found in repository: {dst.relative_to(REPO_ROOT)}"
        )
        return
    if not filecmp.cmp(src, dst, shallow=False):
        mismatches.append(f"Generated file is stale: {src.relative_to(REPO_ROOT)}")


def compare_directories(src_dir: Path, dst_dir: Path, mismatches: list[str]) -> None:
    if not src_dir.exists() and not dst_dir.exists():
        return
    if src_dir.exists() and not dst_dir.exists():
        mismatches.append(
            f"Missing generated directory in repository: {src_dir.relative_to(REPO_ROOT)}"
        )
        return
    if not src_dir.exists() and dst_dir.exists():
        mismatches.append(
            f"Unexpected generated directory found in repository: {dst_dir.relative_to(REPO_ROOT)}"
        )
        return

    comparison = filecmp.dircmp(src_dir, dst_dir)
    for name in sorted(comparison.left_only):
        mismatches.append(
            f"Missing generated artifact in repository: {(src_dir / name).relative_to(REPO_ROOT)}"
        )
    for name in sorted(comparison.right_only):
        mismatches.append(
            f"Unexpected generated artifact in repository: {(dst_dir / name).relative_to(REPO_ROOT)}"
        )
    for name in sorted(comparison.diff_files):
        mismatches.append(
            f"Generated file is stale: {(src_dir / name).relative_to(REPO_ROOT)}"
        )

    for common_dir in sorted(comparison.common_dirs):
        compare_directories(src_dir / common_dir, dst_dir / common_dir, mismatches)


def validate_paths(repo_paths: list[Path], temp_repo_paths: list[Path]) -> list[str]:
    mismatches: list[str] = []
    for repo_path, temp_path in zip(repo_paths, temp_repo_paths, strict=True):
        if repo_path.is_dir() or temp_path.is_dir():
            compare_directories(repo_path, temp_path, mismatches)
        else:
            compare_files(repo_path, temp_path, mismatches)
    return mismatches


def main() -> int:
    config = load_yaml(CONFIG_PATH)
    repo_paths = resolve_generated_paths(config)

    with tempfile.TemporaryDirectory(prefix="generated-content-") as tmp:
        temp_root = Path(tmp)
        temp_repo = copy_repo_to_temp(temp_root)
        run_generator(temp_repo)

        temp_paths = [temp_repo / path.relative_to(REPO_ROOT) for path in repo_paths]
        mismatches = validate_paths(repo_paths, temp_paths)

    if mismatches:
        print("ERROR: generated content is out of date. Regenerate before committing:")
        for mismatch in mismatches:
            print(f"- {mismatch}")
        return 1

    print("Generated content is current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
