#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="${SAYANE_MACOS_APP_NAME:-SayaneApp}"
APPLICATIONS_DIR="${SAYANE_MACOS_APPLICATIONS_DIR:-${HOME}/Applications}"
OUTPUT_DIR="${SAYANE_MACOS_APP_OUTPUT_DIR:-${ROOT}/dist/macos}"
APP_PATH="${APPLICATIONS_DIR}/${APP_NAME}.app"
CONFIGURATION="release"
RUN_BUILD=1
VERIFY_INSTALL=1
AUTO_OPEN=1
STOP_RUNNING=1

info() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --debug            Refresh the debug bundle instead of release
  --no-build         Reuse the existing built bundle
  --no-verify        Skip install verification
  --no-open          Do not open the refreshed app
  --no-stop          Do not stop a running app before reinstall
  --applications DIR Override the install directory
  --output-dir DIR   Override the build output directory
  -h, --help         Show this help

Environment:
  SAYANE_MACOS_APP_NAME
  SAYANE_MACOS_APPLICATIONS_DIR
  SAYANE_MACOS_APP_OUTPUT_DIR
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
    --no-verify)
      VERIFY_INSTALL=0
      ;;
    --no-open)
      AUTO_OPEN=0
      ;;
    --no-stop)
      STOP_RUNNING=0
      ;;
    --applications)
      shift
      [[ $# -gt 0 ]] || die "--applications requires a path"
      APPLICATIONS_DIR="$1"
      APP_PATH="${APPLICATIONS_DIR}/${APP_NAME}.app"
      ;;
    --output-dir)
      shift
      [[ $# -gt 0 ]] || die "--output-dir requires a path"
      OUTPUT_DIR="$1"
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

stop_running_app() {
  [[ "${STOP_RUNNING}" == "1" ]] || return 0
  info "Stopping running ${APP_NAME} instances"
  pkill -f "${APPLICATIONS_DIR}/${APP_NAME}.app/Contents/MacOS/${APP_NAME}" 2>/dev/null || true
  pkill -x "${APP_NAME}" 2>/dev/null || true
  sleep 1
}

build_args() {
  local args=()
  [[ "${CONFIGURATION}" == "release" ]] || args+=(--debug)
  [[ "${RUN_BUILD}" == "1" ]] || args+=(--no-build)
  args+=(--output-dir "${OUTPUT_DIR}")
  printf '%s\n' "${args[@]}"
}

main() {
  stop_running_app

  info "Installing refreshed ${APP_NAME}.app"
  local install_args=()
  [[ "${CONFIGURATION}" == "release" ]] || install_args+=(--debug)
  [[ "${RUN_BUILD}" == "1" ]] || install_args+=(--no-build)
  install_args+=(--applications "${APPLICATIONS_DIR}")
  [[ "${AUTO_OPEN}" == "1" ]] || install_args+=(--no-open)

  SAYANE_MACOS_APP_OUTPUT_DIR="${OUTPUT_DIR}" \
    bash "${ROOT}/scripts/install-macos-app.sh" "${install_args[@]}"

  if [[ "${VERIFY_INSTALL}" == "1" ]]; then
    info "Verifying refreshed app"
    SAYANE_MACOS_APPLICATIONS_DIR="${APPLICATIONS_DIR}" \
      bash "${ROOT}/scripts/verify-macos-app-install.sh"
  fi

  cat <<EOF

Refreshed:
  App: ${APP_PATH}
  Output dir: ${OUTPUT_DIR}
  Configuration: ${CONFIGURATION}

Useful commands:
  open "${APP_PATH}"
  bash "${ROOT}/scripts/verify-macos-app-install.sh"
  bash "${ROOT}/scripts/uninstall-macos-app.sh"
EOF
}

main "$@"
