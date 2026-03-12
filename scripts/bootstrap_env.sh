#!/usr/bin/env bash
set -e

VENV_DIR=".venv"

echo "🔧 Checking Python virtual environment..."

if [ ! -d "$VENV_DIR" ]; then
  echo "📦 Creating virtual environment"
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "⬆️ Installing development dependencies"
pip install --upgrade pip >/dev/null
pip install -r requirements-dev.txt >/dev/null

echo "✅ Python environment ready"
