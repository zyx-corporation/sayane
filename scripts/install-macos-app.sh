#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="${SAYANE_MACOS_APP_NAME:-SayaneApp}"
APPLICATIONS_DIR="${SAYANE_MACOS_APPLICATIONS_DIR:-${HOME}/Applications}"
OUTPUT_DIR="${SAYANE_MACOS_APP_OUTPUT_DIR:-${ROOT}/dist/macos}"
CONFIGURATION="release"
RUN_BUILD=1
AUTO_OPEN=1
ADHOC_SIGN=1

info() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --debug            Install the debug bundle instead of release
  --no-build         Reuse the existing bundle without rebuilding
  --applications DIR Override the installation target directory
  --no-open          Do not open the installed app after copying
  --no-adhoc-sign    Skip local ad-hoc signing after install
  -h, --help         Show this help

Environment:
  SAYANE_MACOS_APPLICATIONS_DIR
  SAYANE_MACOS_APP_OUTPUT_DIR
  SAYANE_MACOS_APP_NAME
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --debug)
      CONFIGURATION="debug"
      ;;
    --no-build)
      RUN_BUILD=0
      ;;
    --applications)
      shift
      [[ $# -gt 0 ]] || die "--applications requires a path"
      APPLICATIONS_DIR="$1"
      ;;
    --no-open)
      AUTO_OPEN=0
      ;;
    --no-adhoc-sign)
      ADHOC_SIGN=0
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

APP_BUNDLE_PATH="${OUTPUT_DIR}/${APP_NAME}.app"
INSTALLED_APP_PATH="${APPLICATIONS_DIR}/${APP_NAME}.app"

build_bundle_if_needed() {
  local build_args=()
  [[ "${CONFIGURATION}" == "release" ]] || build_args+=(--debug)
  [[ "${RUN_BUILD}" == "1" ]] || build_args+=(--no-build)
  build_args+=(--output-dir "${OUTPUT_DIR}")
  bash "${ROOT}/scripts/build-macos-app-bundle.sh" "${build_args[@]}"
}

install_bundle() {
  [[ -d "${APP_BUNDLE_PATH}" ]] || die "Missing app bundle: ${APP_BUNDLE_PATH}"
  mkdir -p "${APPLICATIONS_DIR}"
  info "Installing ${APP_NAME}.app to ${APPLICATIONS_DIR}"
  rm -rf "${INSTALLED_APP_PATH}"
  ditto "${APP_BUNDLE_PATH}" "${INSTALLED_APP_PATH}"
}

adhoc_sign_if_needed() {
  [[ "${ADHOC_SIGN}" == "1" ]] || return 0
  command -v codesign >/dev/null 2>&1 || return 0
  info "Applying local ad-hoc signature for LaunchServices"
  codesign --force --deep -s - "${INSTALLED_APP_PATH}"
}

open_if_needed() {
  [[ "${AUTO_OPEN}" == "1" ]] || return 0
  command -v open >/dev/null 2>&1 || return 0
  info "Opening installed app"
  open "${INSTALLED_APP_PATH}"
}

print_summary() {
  cat <<EOF

Installed:
  App: ${INSTALLED_APP_PATH}
  Source bundle: ${APP_BUNDLE_PATH}

Useful commands:
  open "${INSTALLED_APP_PATH}"
  ls -la "${APPLICATIONS_DIR}"
  rm -rf "${INSTALLED_APP_PATH}"
EOF
}

main() {
  build_bundle_if_needed
  install_bundle
  adhoc_sign_if_needed
  open_if_needed
  print_summary
}

main "$@"
