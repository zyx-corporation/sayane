#!/usr/bin/env bash
# GitHub Release v1.0.2 + close completed issues. Requires: gh auth login
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

bash "$ROOT/scripts/publish-github-release-v1.0.2.sh"
bash "$ROOT/scripts/close-completed-issues.sh"

echo "Done: GitHub Release v1.0.2 + issue cleanup"
