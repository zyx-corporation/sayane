#!/usr/bin/env bash
# Close GitHub issues after merge. Requires: gh auth login
set -euo pipefail

if ! gh auth status >/dev/null 2>&1; then
  echo "Run: gh auth login" >&2
  exit 1
fi

REPO="${SAYANE_REPO:-zyx-corporation/sayane}"

gh issue close 96 --repo "$REPO" \
  --comment "Merged to main @ 8f2b558 — Extension provider registry, collapsed preview UI, L3 E2E record."

gh issue close 83 --repo "$REPO" \
  --comment "Merged to main @ 8f2b558 — WinGet/Scoop draft manifests under packaging/."

echo "Closed #96 and #83 on $REPO"

PRO_REPO="${SAYANE_PRO_REPO:-zyx-corporation/sayane-pro}"
if gh issue list --repo "$PRO_REPO" --state open --search "RecursionError context_index" --json number --jq '.[0].number' 2>/dev/null | grep -q .; then
  num=$(gh issue list --repo "$PRO_REPO" --state open --search "RecursionError context_index" --json number --jq '.[0].number')
  gh issue close "$num" --repo "$PRO_REPO" \
    --comment "Fixed on main @ eae09d8 — idempotent hooks patch + regression test."
  echo "Closed sayane-pro #$num"
fi
