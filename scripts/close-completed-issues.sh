#!/usr/bin/env bash
# Close GitHub issues after merge. Requires: gh auth login
set -euo pipefail

if ! gh auth status >/dev/null 2>&1; then
  echo "Run: gh auth login" >&2
  exit 1
fi

REPO="${SAYANE_REPO:-zyx-corporation/sayane}"

gh issue close 96 --repo "$REPO" \
  --comment "Released v1.0.2 — Extension provider registry, collapsed preview UI, L3 E2E record."

gh issue close 83 --repo "$REPO" \
  --comment "Released v1.0.2 — WinGet/Scoop draft manifests under packaging/."

gh issue close 85 --repo "$REPO" \
  --comment "Released v1.0.2 — GeminiAdapter compile / context-packet / Extension insert."

gh issue close 84 --repo "$REPO" \
  --comment "Released v1.0.2 — CLI sayane capture (--text / --file / stdin)."

gh issue close 88 --repo "$REPO" \
  --comment "L2 Core manual sign-off recorded in acceptance-spec §4.0 / §8.3."

gh issue close 89 --repo "$REPO" \
  --comment "L3 Extension: Playwright E2E Pass §6.1 (2026-05-30); Extension 0.3.5."

echo "Closed #96, #83, #85, #84, #88, #89 on $REPO"

PRO_REPO="${SAYANE_PRO_REPO:-zyx-corporation/sayane-pro}"
if gh issue list --repo "$PRO_REPO" --state open --search "RecursionError context_index" --json number --jq '.[0].number' 2>/dev/null | grep -q .; then
  num=$(gh issue list --repo "$PRO_REPO" --state open --search "RecursionError context_index" --json number --jq '.[0].number')
  gh issue close "$num" --repo "$PRO_REPO" \
    --comment "Fixed on main @ eae09d8 — idempotent hooks patch + regression test."
  echo "Closed sayane-pro #$num"
fi
