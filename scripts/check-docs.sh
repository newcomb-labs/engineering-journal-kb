#!/usr/bin/env bash
set -euo pipefail

echo "== Engineering Journal Docs Check =="

echo "Step 1: Sync blog tags"
./scripts/sync_blog_tags.py

echo "Step 2: Install dependencies"
cd website
npm ci

echo "Step 3: Build site"
npm run build

echo ""
echo "✔ Docs build completed successfully"
