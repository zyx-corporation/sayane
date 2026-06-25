#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TAG="v1.0.14-post1"
NOTES="$ROOT/scripts/release-v1.0.14-post1-notes.md"
REPO="${SAYANE_REPO:-zyx-corporation/sayane}"

if ! gh auth status >/dev/null 2>&1; then
  echo "Run: gh auth login" >&2
  exit 1
fi

if ! git -C "$ROOT" rev-parse "$TAG" >/dev/null 2>&1; then
  echo "Tag $TAG not found locally. Create and push the tag first." >&2
  exit 1
fi

gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1 && {
  echo "Release $TAG already exists. Edit with: gh release edit $TAG"
  exit 0
}

gh release create "$TAG" \
  --repo "$REPO" \
  --title "Sayane Community v1.0.14.post1" \
  --notes-file "$NOTES"

echo "Published: https://github.com/$REPO/releases/tag/$TAG"
