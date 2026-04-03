#!/usr/bin/env bash
set -euo pipefail

scripts/bootstrap_env.sh
source .venv/bin/activate

echo "Building docs"
cd website
npm run build
