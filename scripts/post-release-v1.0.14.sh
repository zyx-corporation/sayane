#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TAG="v1.0.14"
REPO="${SAYANE_REPO:-zyx-corporation/sayane}"

bash "$ROOT/scripts/publish-github-release-v1.0.14.sh"

echo "Release $TAG created."
echo "Trigger PyPI publish with:"
echo "  gh workflow run publish-pypi.yml --repo $REPO -f tag=$TAG"
