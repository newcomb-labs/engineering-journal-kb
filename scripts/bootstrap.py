#!/usr/bin/env python3
# ---
# file: scripts/bootstrap.py
# managed_by: ansible-repo
# ---

"""
Repo bootstrap helper.

Goals:
- Deterministic tooling aligned with CI (Python 3.11)
- Idempotent: safe to run repeatedly
- No root required
- Clear failure messages

Behavior:
- Select Python interpreter from PYTHON_BIN env var (default: python3.11)
- Enforce Python 3.11.x (fail-closed)
- Create .venv if missing; verify existing venv is also 3.11.x
- Upgrade pip, setuptools, wheel
- Install dev requirements if requirements-dev.txt exists
- Install pre-commit hooks (pre-commit + pre-push)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = REPO_ROOT / ".venv"
REQ_DEV = REPO_ROOT / "requirements-dev.txt"

REQUIRED_PYTHON = (3, 11)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
    )


def die(msg: str, code: int = 2) -> None:
    """Print error and exit immediately — never returns."""
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def which(prog: str) -> str | None:
    return shutil.which(prog)


def python_version(py: str) -> tuple[int, int, int]:
    res = run([py, "-c", "import sys; print(*sys.version_info[:3])"])
    if res.returncode != 0:
        raise RuntimeError((res.stderr + res.stdout).strip() or f"failed to run {py}")
    parts = res.stdout.strip().split()
    if len(parts) != 3:
        raise RuntimeError(f"unexpected version output from {py}: {res.stdout!r}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def assert_python_311(py: str, label: str = "") -> None:
    """Raise RuntimeError if *py* is not Python 3.11.x."""
    maj, minu, mic = python_version(py)
    if (maj, minu) != REQUIRED_PYTHON:
        src = f" ({label})" if label else ""
        raise RuntimeError(
            f"repo requires Python 3.11.x; got {maj}.{minu}.{mic} from '{py}'{src}"
        )


# ---------------------------------------------------------------------------
# Bootstrap steps
# ---------------------------------------------------------------------------


def ensure_venv(py: str) -> None:
    """Create venv if absent; verify it is 3.11.x if it already exists."""
    venv_py = VENV_DIR / "bin" / "python"

    if VENV_DIR.exists() and venv_py.exists():
        # Existing venv — verify it matches the required version before reusing.
        assert_python_311(str(venv_py), label="existing venv")
        return

    print(f"Creating venv at {VENV_DIR} using {py}...")
    res = run([py, "-m", "venv", str(VENV_DIR)], cwd=REPO_ROOT)
    if res.returncode != 0:
        raise RuntimeError((res.stderr + res.stdout).strip() or "venv creation failed")


def venv_python() -> str:
    py = VENV_DIR / "bin" / "python"
    if not py.exists():
        raise RuntimeError("venv python not found; venv creation may have failed")
    return str(py)


def venv_bin(name: str) -> str:
    """Return path to a binary inside the venv."""
    return str(VENV_DIR / "bin" / name)


def pip_install(venv_py: str, pkgs: list[str]) -> None:
    res = run([venv_py, "-m", "pip", "install", *pkgs], cwd=REPO_ROOT)
    if res.returncode != 0:
        raise RuntimeError((res.stderr + res.stdout).strip() or "pip install failed")


def pip_install_requirements(venv_py: str, req_file: Path) -> None:
    res = run([venv_py, "-m", "pip", "install", "-r", str(req_file)], cwd=REPO_ROOT)
    if res.returncode != 0:
        raise RuntimeError((res.stderr + res.stdout).strip() or "pip install -r failed")


def precommit_install() -> None:
    """Install pre-commit and pre-push hooks using the venv binary directly."""
    pc_bin = venv_bin("pre-commit")
    if not Path(pc_bin).exists():
        raise RuntimeError(
            f"pre-commit binary not found at {pc_bin}; was it installed?"
        )

    for extra_args in ([], ["--hook-type", "pre-push"]):
        res = run([pc_bin, "install", *extra_args], cwd=REPO_ROOT)
        if res.returncode != 0:
            raise RuntimeError(
                (res.stderr + res.stdout).strip() or "pre-commit install failed"
            )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    py = os.environ.get("PYTHON_BIN", "python3.11")

    if which(py) is None:
        die(
            f"'{py}' not found in PATH. "
            "Install Python 3.11 or set PYTHON_BIN to an available python3.11 binary."
        )

    try:
        # Verify the host interpreter before touching anything.
        assert_python_311(py, label="host interpreter")

        ensure_venv(py)

        vpy = venv_python()

        print("Upgrading pip / setuptools / wheel...")
        pip_install(vpy, ["--upgrade", "pip", "setuptools", "wheel"])

        if REQ_DEV.exists():
            print(f"Installing dev requirements from {REQ_DEV}...")
            pip_install_requirements(vpy, REQ_DEV)
        else:
            print("requirements-dev.txt not found; installing minimal tooling set.")
            pip_install(vpy, ["pre-commit", "ansible-core", "ansible-lint", "yamllint"])

        print("Installing pre-commit hooks (pre-commit + pre-push)...")
        precommit_install()

        maj, minu, mic = python_version(vpy)
        activate = VENV_DIR / "bin" / "activate"
        print(f"OK: bootstrap complete using venv python {maj}.{minu}.{mic}")
        print()
        print("  Venv ready. To activate in your current shell run:")
        print(f"    source {activate}")
        print()

    except Exception as e:
        die(str(e))


if __name__ == "__main__":
    main()
