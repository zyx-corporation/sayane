#!/usr/bin/env bash
# Build and verify sayane sdist/wheel locally.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m pip install -q build twine
rm -rf dist build
python3 -m build
python3 -m twine check dist/*
echo "Built:"
ls -la dist/
