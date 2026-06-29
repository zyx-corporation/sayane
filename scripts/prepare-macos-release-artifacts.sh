#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_DIR="${SAYANE_MACOS_APP_OUTPUT_DIR:-${ROOT}/dist/macos}"
APPLICATIONS_DIR="${SAYANE_MACOS_APPLICATIONS_DIR:-${HOME}/Applications}"
INSTALL_AFTER_BUILD=0
VERIFY_INSTALL=0

info() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --install         Also install the built app into ~/Applications
  --verify-install  Verify the installed app after install
  --output-dir DIR  Override the artifact output directory
  -h, --help        Show this help

Environment:
  SAYANE_MACOS_APP_OUTPUT_DIR
  SAYANE_MACOS_APPLICATIONS_DIR
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install)
      INSTALL_AFTER_BUILD=1
      ;;
    --verify-install)
      VERIFY_INSTALL=1
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

main() {
  info "Building release bundle and zip"
  bash "${ROOT}/scripts/build-macos-app-bundle.sh" --zip --output-dir "${OUTPUT_DIR}"
  bash "${ROOT}/scripts/sign-macos-app.sh" --verify-only --app "${OUTPUT_DIR}/SayaneApp.app"

  if [[ "${INSTALL_AFTER_BUILD}" == "1" ]]; then
    info "Installing built app"
    SAYANE_MACOS_APP_OUTPUT_DIR="${OUTPUT_DIR}" \
      SAYANE_MACOS_APPLICATIONS_DIR="${APPLICATIONS_DIR}" \
      bash "${ROOT}/scripts/install-macos-app.sh" --no-open --no-build
  fi

  if [[ "${VERIFY_INSTALL}" == "1" ]]; then
    info "Verifying installed app"
    SAYANE_MACOS_APPLICATIONS_DIR="${APPLICATIONS_DIR}" \
      bash "${ROOT}/scripts/verify-macos-app-install.sh"
  fi

  cat <<EOF

Release-prep artifacts:
  Bundle: ${OUTPUT_DIR}/SayaneApp.app
  Zip: ${OUTPUT_DIR}/SayaneApp-latest-macos-release.zip
  Checksums: ${OUTPUT_DIR}/SayaneApp-*.sha256
  Manifest: ${OUTPUT_DIR}/SayaneApp-*.manifest.txt

Next steps:
  bash scripts/sign-macos-app.sh --dry-run --identity "Developer ID Application: Example"
  bash scripts/notarize-macos-app.sh --dry-run --profile sayane-notary
EOF
}

main "$@"
