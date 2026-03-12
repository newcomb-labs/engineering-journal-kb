#!/usr/bin/env bash
set -euo pipefail

scripts/bootstrap_env.sh
source .venv/bin/activate

python3 scripts/validate_blog_tags.py

echo "Building docs"
cd website
npm run build
