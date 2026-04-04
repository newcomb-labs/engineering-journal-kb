#!/usr/bin/env bash
set -euo pipefail

echo "== Docs validation =="

echo "-> Install website dependencies"
cd website
npm ci

echo "-> Build Docusaurus site"
npm run build

echo ""
echo "✔ Docs validation completed successfully"
