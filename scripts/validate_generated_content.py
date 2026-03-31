#!/usr/bin/env python3

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
DEFAULT_GENERATED_DIR = REPO_ROOT / "website" / "docs" / "indexes"
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

SKIP_FILE_NAMES = {
    ".DS_Store",
}


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
        out: list[Path] = []
        for value in values:
            if isinstance(value, (str, Path)):
                out.append(Path(str(value)))
        return out

    return []


def resolve_generated_paths(config: dict[str, Any]) -> list[Path]:
    candidates: list[Path] = []

    # Support a few boring, explicit schema shapes.
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

        dirs[:] = [d for d in dirs if not should_skip_dir(d)]

        rel_root = root_path.relative_to(REPO_ROOT)
        dest_root = temp_repo / rel_root
        dest_root.mkdir(parents=True, exist_ok=True)

        for filename in files:
            if should_skip_file(filename):
                continue
            src = root_path / filename
            dst = dest_root / filename
            shutil.copy2(src, dst)

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
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        message = [
            "ERROR: generated artifact regeneration failed in validation sandbox."
        ]
        if stdout:
            message.append("")
            message.append("STDOUT:")
            message.append(stdout)
        if stderr:
            message.append("")
            message.append("STDERR:")
            message.append(stderr)
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
            f"Unexpected generated file in repository: {src.relative_to(REPO_ROOT)}"
        )
        return

    if not filecmp.cmp(src, dst, shallow=False):
        mismatches.append(f"Stale generated file: {src.relative_to(REPO_ROOT)}")


def compare_directories(real_dir: Path, temp_dir: Path, mismatches: list[str]) -> None:
    real_files = (
        {path.relative_to(real_dir) for path in real_dir.rglob("*") if path.is_file()}
        if real_dir.exists()
        else set()
    )

    temp_files = (
        {path.relative_to(temp_dir) for path in temp_dir.rglob("*") if path.is_file()}
        if temp_dir.exists()
        else set()
    )

    all_files = sorted(real_files | temp_files)

    for rel_path in all_files:
        compare_files(real_dir / rel_path, temp_dir / rel_path, mismatches)


def validate_generated_paths(temp_repo: Path, generated_paths: list[Path]) -> list[str]:
    mismatches: list[str] = []

    for real_path in generated_paths:
        rel_path = real_path.relative_to(REPO_ROOT)
        temp_path = temp_repo / rel_path

        if real_path.is_dir() or (
            not real_path.exists() and str(real_path).endswith("/")
        ):
            compare_directories(real_path, temp_path, mismatches)
            continue

        if real_path.exists() and real_path.is_file():
            compare_files(real_path, temp_path, mismatches)
            continue

        # If path does not exist yet in repo, infer intent from temp output.
        if temp_path.exists() and temp_path.is_dir():
            compare_directories(real_path, temp_path, mismatches)
        else:
            compare_files(real_path, temp_path, mismatches)

    return mismatches


def main() -> int:
    try:
        config = load_yaml(CONFIG_PATH)
        generated_paths = resolve_generated_paths(config)

        with tempfile.TemporaryDirectory(
            prefix="generated-content-check-"
        ) as temp_dir_raw:
            temp_root = Path(temp_dir_raw)
            temp_repo = copy_repo_to_temp(temp_root)
            run_generator(temp_repo)
            mismatches = validate_generated_paths(temp_repo, generated_paths)

        if mismatches:
            print("Generated artifacts are stale or inconsistent.")
            print("")
            for mismatch in mismatches:
                print(f"- {mismatch}")
            print("")
            print("Regenerate them with:")
            print(f"  {sys.executable} scripts/generate_content_artifacts.py")
            return 1

        print("Generated artifacts are already up to date.")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
