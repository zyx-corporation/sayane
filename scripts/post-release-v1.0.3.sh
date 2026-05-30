#!/usr/bin/env bash
# Publish GitHub Release v1.0.3 and trigger PyPI workflow. Requires: gh auth login, PYPI_API_TOKEN secret.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TAG=v1.0.3
REPO="${SAYANE_REPO:-zyx-corporation/sayane}"

if ! gh auth status >/dev/null 2>&1; then
  echo "Run: gh auth login" >&2
  exit 1
fi

gh release create "$TAG" \
  --repo "$REPO" \
  --title "Community Edition v1.0.3" \
  --notes-file "$ROOT/scripts/release-v1.0.3-notes.md"

echo "Release $TAG created. PyPI workflow runs if PYPI_API_TOKEN is set."
echo "Or: gh workflow run publish-pypi.yml --repo $REPO -f tag=$TAG"

gh issue close 82 --repo "$REPO" \
  --comment "Published sayane 1.0.3 to PyPI (Community CLI + Bridge + MCP). pip install sayane"

echo "Done."
