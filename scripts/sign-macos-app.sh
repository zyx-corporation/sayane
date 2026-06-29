#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_PATH="${SAYANE_MACOS_APP_PATH:-${ROOT}/dist/macos/SayaneApp.app}"
IDENTITY="${SAYANE_MACOS_CODESIGN_IDENTITY:-}"
VERIFY_ONLY=0
DRY_RUN=0

info() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --app PATH        Override the app bundle path
  --identity NAME   Override the Developer ID Application identity
  --verify-only     Only run codesign verification and display checks
  --dry-run         Print the signing plan without mutating the bundle
  -h, --help        Show this help

Environment:
  SAYANE_MACOS_APP_PATH
  SAYANE_MACOS_CODESIGN_IDENTITY
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app)
      shift
      [[ $# -gt 0 ]] || die "--app requires a path"
      APP_PATH="$1"
      ;;
    --identity)
      shift
      [[ $# -gt 0 ]] || die "--identity requires a value"
      IDENTITY="$1"
      ;;
    --verify-only)
      VERIFY_ONLY=1
      ;;
    --dry-run)
      DRY_RUN=1
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

require_tools() {
  command -v codesign >/dev/null 2>&1 || die "codesign is required"
  command -v spctl >/dev/null 2>&1 || die "spctl is required"
}

require_bundle() {
  [[ -d "${APP_PATH}" ]] || die "Missing app bundle: ${APP_PATH}"
}

signature_state() {
  local details
  details="$(codesign -dv --verbose=4 "${APP_PATH}/Contents/MacOS/$(basename "${APP_PATH}" .app)" 2>&1 || true)"
  if [[ -z "${details}" ]]; then
    printf 'unsigned\n'
    return 0
  fi
  if grep -q "Signature=adhoc" <<<"${details}"; then
    printf 'adhoc\n'
    return 0
  fi
  if grep -q "Authority=" <<<"${details}"; then
    printf 'signed\n'
    return 0
  fi
  printf 'unsigned\n'
}

print_plan() {
  cat <<EOF
Signing plan:
  App: ${APP_PATH}
  Identity: ${IDENTITY:-<unset>}
  Verify only: ${VERIFY_ONLY}
  Dry run: ${DRY_RUN}

Commands:
  codesign --force --deep --options runtime --timestamp --sign "<identity>" "${APP_PATH}"
  codesign --verify --deep --strict --verbose=2 "${APP_PATH}"
  spctl --assess --type execute --verbose=4 "${APP_PATH}"
EOF
}

sign_bundle() {
  [[ -n "${IDENTITY}" ]] || die "Missing signing identity. Pass --identity or set SAYANE_MACOS_CODESIGN_IDENTITY."
  info "Signing ${APP_PATH}"
  codesign --force --deep --options runtime --timestamp --sign "${IDENTITY}" "${APP_PATH}"
}

verify_bundle() {
  local state
  state="$(signature_state)"
  if [[ "${VERIFY_ONLY}" == "1" && "${state}" != "signed" ]]; then
    info "Current bundle is in pre-sign state (${state})"
    printf 'note: run this script again with --identity after Developer ID credentials are available.\n'
    return 0
  fi
  info "Verifying codesign"
  codesign --verify --deep --strict --verbose=2 "${APP_PATH}"
  info "Assessing with spctl"
  spctl --assess --type execute --verbose=4 "${APP_PATH}"
}

main() {
  require_tools
  require_bundle
  print_plan
  [[ "${DRY_RUN}" == "1" ]] && exit 0
  [[ "${VERIFY_ONLY}" == "1" ]] || sign_bundle
  verify_bundle
}

main "$@"
