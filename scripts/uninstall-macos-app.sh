#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${SAYANE_MACOS_APP_NAME:-SayaneApp}"
APPLICATIONS_DIR="${SAYANE_MACOS_APPLICATIONS_DIR:-${HOME}/Applications}"
APP_PATH="${APPLICATIONS_DIR}/${APP_NAME}.app"

info() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --applications DIR Override the install directory
  -h, --help         Show this help

Environment:
  SAYANE_MACOS_APPLICATIONS_DIR
  SAYANE_MACOS_APP_NAME
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --applications)
      shift
      [[ $# -gt 0 ]] || die "--applications requires a path"
      APPLICATIONS_DIR="$1"
      APP_PATH="${APPLICATIONS_DIR}/${APP_NAME}.app"
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
  if [[ ! -e "${APP_PATH}" ]]; then
    info "No installed app found at ${APP_PATH}"
    exit 0
  fi
  info "Removing ${APP_PATH}"
  rm -rf "${APP_PATH}"
  cat <<EOF

Removed:
  ${APP_PATH}

If needed, rebuild or reinstall with:
  bash scripts/install-macos-app.sh
EOF
}

main "$@"
