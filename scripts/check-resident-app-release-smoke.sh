#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_API=1
RUN_UI=1
RUN_NATIVE=0
START_BRIDGE=0

info() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --start       Start a local Bridge when one is not healthy
  --with-native Include native macOS preview smoke
  --api-only    Run only bearer-backed API surface smoke
  --ui-only     Run only UI session smoke
  -h, --help    Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --start)
      START_BRIDGE=1
      ;;
    --with-native)
      RUN_NATIVE=1
      ;;
    --api-only)
      RUN_API=1
      RUN_UI=0
      RUN_NATIVE=0
      ;;
    --ui-only)
      RUN_API=0
      RUN_UI=1
      RUN_NATIVE=0
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

bridge_arg=()
if [[ "${START_BRIDGE}" == "1" ]]; then
  bridge_arg=(--start)
fi

run_smoke() {
  local script_path="$1"
  if (( ${#bridge_arg[@]} > 0 )); then
    bash "${script_path}" "${bridge_arg[@]}"
    return
  fi
  bash "${script_path}"
}

main() {
  cd "${ROOT}"
  if [[ "${START_BRIDGE}" == "1" ]]; then
    info "Ensuring local Bridge through run-app-local helper"
    bash "${ROOT}/scripts/run-app-local.sh" --no-open --no-bootstrap-check
    bridge_arg=()
  fi

  if [[ "${RUN_API}" == "1" ]]; then
    info "Running resident app API surface smoke"
    run_smoke "${ROOT}/scripts/check-resident-app-api-surfaces.sh"
  fi

  if [[ "${RUN_UI}" == "1" ]]; then
    info "Running resident app UI session smoke"
    run_smoke "${ROOT}/scripts/check-resident-app-ui-session.sh"
  fi

  if [[ "${RUN_NATIVE}" == "1" ]]; then
    info "Running native macOS preview smoke"
    run_smoke "${ROOT}/scripts/check-macos-app-preview.sh"
  fi

  cat <<EOF

Resident app release smoke passed:
  API surfaces: $( [[ "${RUN_API}" == "1" ]] && printf 'yes' || printf 'skipped' )
  UI session: $( [[ "${RUN_UI}" == "1" ]] && printf 'yes' || printf 'skipped' )
  Native macOS: $( [[ "${RUN_NATIVE}" == "1" ]] && printf 'yes' || printf 'skipped' )
EOF
}

main "$@"
