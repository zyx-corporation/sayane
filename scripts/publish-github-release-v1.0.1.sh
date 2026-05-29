#!/usr/bin/env bash
# Publish GitHub Release for an existing tag (v1.0.1).
# Prerequisites: gh auth login, tag v1.0.1 pushed to origin.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! gh auth status >/dev/null 2>&1; then
  echo "Run: gh auth login" >&2
  exit 1
fi

if gh release view v1.0.1 >/dev/null 2>&1; then
  echo "Release v1.0.1 already exists:"
  gh release view v1.0.1 --web
  exit 0
fi

gh release create v1.0.1 \
  --title "Sayane Community Edition v1.0.1" \
  --notes-file "$ROOT/scripts/release-v1.0.1-notes.md"

echo "Published: https://github.com/zyx-corporation/sayane/releases/tag/v1.0.1"
