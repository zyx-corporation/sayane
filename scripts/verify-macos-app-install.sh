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
  --app PATH          Override the app bundle path
  --applications DIR  Override the install directory
  --open              Open the app after verification
  -h, --help          Show this help

Environment:
  SAYANE_MACOS_APP_NAME
  SAYANE_MACOS_APPLICATIONS_DIR
EOF
}

AUTO_OPEN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app)
      shift
      [[ $# -gt 0 ]] || die "--app requires a path"
      APP_PATH="$1"
      ;;
    --applications)
      shift
      [[ $# -gt 0 ]] || die "--applications requires a path"
      APPLICATIONS_DIR="$1"
      APP_PATH="${APPLICATIONS_DIR}/${APP_NAME}.app"
      ;;
    --open)
      AUTO_OPEN=1
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
  [[ -d "${APP_PATH}" ]] || die "Missing installed app: ${APP_PATH}"
  info "Verifying bundle structure"
  [[ -f "${APP_PATH}/Contents/Info.plist" ]] || die "Missing Info.plist"
  [[ -x "${APP_PATH}/Contents/MacOS/${APP_NAME}" ]] || die "Missing executable"
  [[ -x "${APP_PATH}/Contents/Resources/run-bridge-helper.sh" ]] || die "Missing bundled bridge helper"
  plutil -lint "${APP_PATH}/Contents/Info.plist"
  file "${APP_PATH}/Contents/MacOS/${APP_NAME}"

  info "Checking signature state"
  if bash "$(cd "$(dirname "$0")" && pwd)/sign-macos-app.sh" --verify-only --app "${APP_PATH}"; then
    :
  else
    die "Signature verification helper failed"
  fi

  if codesign -dv "${APP_PATH}" 2>&1 | rg -q 'Signature=adhoc'; then
    info "Detected local ad-hoc signature"
  fi

  if [[ "${AUTO_OPEN}" == "1" ]]; then
    command -v open >/dev/null 2>&1 && open "${APP_PATH}"
  fi

  cat <<EOF

Verified:
  ${APP_PATH}
EOF
}

main "$@"
