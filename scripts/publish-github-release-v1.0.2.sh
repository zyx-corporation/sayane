#!/usr/bin/env bash
# Create GitHub Release for v1.0.2. Requires: gh auth login
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TAG="v1.0.2"
NOTES="$ROOT/scripts/release-v1.0.2-notes.md"

if ! gh auth status >/dev/null 2>&1; then
  echo "Run: gh auth login" >&2
  exit 1
fi

if ! git -C "$ROOT" rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Tag $TAG not found locally. git fetch --tags" >&2
  exit 1
fi

gh release view "$TAG" --repo zyx-corporation/sayane >/dev/null 2>&1 && {
  echo "Release $TAG already exists. Edit with: gh release edit $TAG"
  exit 0
}

gh release create "$TAG" \
  --repo zyx-corporation/sayane \
  --title "Sayane Community v1.0.2" \
  --notes-file "$NOTES"

echo "Published: https://github.com/zyx-corporation/sayane/releases/tag/$TAG"
