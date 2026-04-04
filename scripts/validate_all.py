#!/usr/bin/env python3
"""
validate_all.py

Thin wrapper — delegates to validate_content.py, which is the canonical
unified content governance validator.

This file exists only for backward compatibility with CI steps that reference
validate_all.py by name. Do not add logic here.

See validate_content.py for the full implementation.
"""

import subprocess
import sys
from pathlib import Path

VALIDATE_CONTENT = Path(__file__).resolve().parent / "validate_content.py"

if __name__ == "__main__":
    result = subprocess.run(
        [sys.executable, str(VALIDATE_CONTENT)] + sys.argv[1:],
        check=False,
    )
    sys.exit(result.returncode)
