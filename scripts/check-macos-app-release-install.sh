#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/sayane-macos-release-smoke.XXXXXX")"
OUTPUT_DIR="${TMP_DIR}/out"
APPLICATIONS_DIR="${TMP_DIR}/apps"

info() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

cleanup() {
  rm -rf "${TMP_DIR}"
}

trap cleanup EXIT

main() {
  cd "${ROOT}"
  info "Building local macOS release zip"
  bash scripts/build-macos-app-bundle.sh --zip --no-build --output-dir "${OUTPUT_DIR}" >/dev/null

  local zip_path
  zip_path="$(find "${OUTPUT_DIR}" -maxdepth 1 -name 'SayaneApp-*-macos-release.zip' | head -n 1)"
  [[ -n "${zip_path}" ]] || die "Could not find generated release zip in ${OUTPUT_DIR}"

  info "Installing native app from release zip into isolated Applications dir"
  bash scripts/install-macos-app-release.sh \
    --zip "${zip_path}" \
    --applications "${APPLICATIONS_DIR}" \
    --no-open >/dev/null

  local installed_app="${APPLICATIONS_DIR}/SayaneApp.app"
  [[ -d "${installed_app}" ]] || die "Missing installed app: ${installed_app}"
  [[ -x "${installed_app}/Contents/Resources/run-bridge-helper.sh" ]] || die "Missing bundled backend helper"

  cat <<EOF

macOS release installer smoke passed:
  zip: ${zip_path}
  app: ${installed_app}
EOF
}

main "$@"
