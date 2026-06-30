#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
START_BRIDGE=0
SKIP_NATIVE=0

info() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Routine macOS smoke for the primary operator path:
  - bearer-backed resident app API surface
  - native macOS preview

This command intentionally excludes the Bridge-hosted HTML/UI-session
compatibility shell. Use \`check-resident-app-release-smoke.sh\` or
\`check-resident-app-ui-session.sh\` only for maintainer/debug checks.

Options:
  --start       Start a local Bridge when one is not healthy
  --no-native   Skip native macOS preview smoke and run API-only routine checks
  -h, --help    Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --start)
      START_BRIDGE=1
      ;;
    --no-native)
      SKIP_NATIVE=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown option: $1"
      ;;
  esac
  shift
done

main() {
  cd "${ROOT}"

  local args=()
  if [[ "${START_BRIDGE}" == "1" ]]; then
    args+=(--start)
  fi
  if [[ "${SKIP_NATIVE}" == "0" ]]; then
    args+=(--routine)
  else
    args+=(--api-only)
  fi

  info "Running routine macOS operator smoke"
  bash "${ROOT}/scripts/check-resident-app-release-smoke.sh" "${args[@]}"

  cat <<EOF

Routine macOS smoke passed:
  API surfaces: yes
  Native macOS preview: $( [[ "${SKIP_NATIVE}" == "0" ]] && printf 'yes' || printf 'skipped' )
  HTML/UI-session compatibility shell: intentionally skipped
EOF
}

main "$@"
