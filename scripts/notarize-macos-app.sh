#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_PATH="${SAYANE_MACOS_APP_PATH:-${ROOT}/dist/macos/SayaneApp.app}"
ZIP_PATH="${SAYANE_MACOS_ZIP_PATH:-${ROOT}/dist/macos/SayaneApp.zip}"
KEYCHAIN_PROFILE="${SAYANE_MACOS_NOTARY_PROFILE:-}"
TEAM_ID="${SAYANE_MACOS_TEAM_ID:-}"
APPLE_ID="${SAYANE_MACOS_APPLE_ID:-}"
DRY_RUN=0
STAPLE=1

info() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --app PATH          Override the app bundle path
  --zip PATH          Override the upload zip path
  --profile NAME      notarytool keychain profile name
  --team-id ID        Apple team id (display only unless profile is omitted)
  --apple-id MAIL     Apple ID hint (display only unless profile is omitted)
  --no-staple         Skip stapling after notarization
  --dry-run           Print the notarization plan without submitting
  -h, --help          Show this help

Environment:
  SAYANE_MACOS_APP_PATH
  SAYANE_MACOS_ZIP_PATH
  SAYANE_MACOS_NOTARY_PROFILE
  SAYANE_MACOS_TEAM_ID
  SAYANE_MACOS_APPLE_ID
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app)
      shift
      [[ $# -gt 0 ]] || die "--app requires a path"
      APP_PATH="$1"
      ;;
    --zip)
      shift
      [[ $# -gt 0 ]] || die "--zip requires a path"
      ZIP_PATH="$1"
      ;;
    --profile)
      shift
      [[ $# -gt 0 ]] || die "--profile requires a value"
      KEYCHAIN_PROFILE="$1"
      ;;
    --team-id)
      shift
      [[ $# -gt 0 ]] || die "--team-id requires a value"
      TEAM_ID="$1"
      ;;
    --apple-id)
      shift
      [[ $# -gt 0 ]] || die "--apple-id requires a value"
      APPLE_ID="$1"
      ;;
    --no-staple)
      STAPLE=0
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
  command -v xcrun >/dev/null 2>&1 || die "xcrun is required"
  command -v ditto >/dev/null 2>&1 || die "ditto is required"
}

require_bundle() {
  [[ -d "${APP_PATH}" ]] || die "Missing app bundle: ${APP_PATH}"
}

ensure_zip() {
  if [[ -f "${ZIP_PATH}" ]]; then
    return 0
  fi
  info "Creating notarization zip at ${ZIP_PATH}"
  mkdir -p "$(dirname "${ZIP_PATH}")"
  ditto -c -k --sequesterRsrc --keepParent "${APP_PATH}" "${ZIP_PATH}"
}

print_plan() {
  cat <<EOF
Notarization plan:
  App: ${APP_PATH}
  Zip: ${ZIP_PATH}
  Keychain profile: ${KEYCHAIN_PROFILE:-<unset>}
  Team ID: ${TEAM_ID:-<unset>}
  Apple ID: ${APPLE_ID:-<unset>}
  Staple: ${STAPLE}
  Dry run: ${DRY_RUN}

Commands:
  xcrun notarytool submit "${ZIP_PATH}" --keychain-profile "<profile>" --wait
  xcrun stapler staple "${APP_PATH}"
  spctl --assess --type execute --verbose=4 "${APP_PATH}"
EOF
}

submit_notarization() {
  [[ -n "${KEYCHAIN_PROFILE}" ]] || die "Missing notarytool keychain profile. Pass --profile or set SAYANE_MACOS_NOTARY_PROFILE."
  info "Submitting notarization request"
  xcrun notarytool submit "${ZIP_PATH}" --keychain-profile "${KEYCHAIN_PROFILE}" --wait
}

staple_bundle() {
  [[ "${STAPLE}" == "1" ]] || return 0
  info "Stapling notarization ticket"
  xcrun stapler staple "${APP_PATH}"
}

verify_bundle() {
  info "Assessing notarized app"
  spctl --assess --type execute --verbose=4 "${APP_PATH}"
}

main() {
  require_tools
  require_bundle
  ensure_zip
  print_plan
  [[ "${DRY_RUN}" == "1" ]] && exit 0
  submit_notarization
  staple_bundle
  verify_bundle
}

main "$@"
