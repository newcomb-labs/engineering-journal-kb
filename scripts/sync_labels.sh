#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-$(gh repo view --json nameWithOwner --jq '.nameWithOwner')}"
LABEL_FILE=".github/labels.yml"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required" >&2
  exit 1
fi

if [[ ! -f "$LABEL_FILE" ]]; then
  echo "Missing $LABEL_FILE" >&2
  exit 1
fi

python3 - "$LABEL_FILE" <<'PY' | while IFS=$'\t' read -r name color description; do
import sys

try:
    import yaml
except ImportError:
    print("PyYAML is required. Install it with: python3 -m pip install pyyaml", file=sys.stderr)
    sys.exit(1)

with open(sys.argv[1], encoding="utf-8") as fh:
    labels = yaml.safe_load(fh)

for label in labels:
    print(f"{label['name']}\t{label['color']}\t{label['description']}")
PY
  gh label create "$name" \
    --repo "$REPO" \
    --color "$color" \
    --description "$description" \
    --force
  echo "synced: $name"
done
