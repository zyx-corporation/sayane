#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${SAYANE_MACOS_APP_NAME:-SayaneApp}"
REPO="${SAYANE_REPO:-zyx-corporation/sayane}"
APPLICATIONS_DIR="${SAYANE_MACOS_APPLICATIONS_DIR:-${HOME}/Applications}"
INSTALLED_APP_PATH=""
VERIFY_INSTALL=1
AUTO_OPEN=1
KEEP_TEMP=0
VERSION=""
TAG=""
ZIP_PATH=""
DOWNLOAD_URL=""
TMP_DIR=""

info() { printf '==> %s\n' "$*" >&2; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Install the native macOS app from a release zip asset.

Options:
  --version VERSION   Download a specific released version (for example: 1.0.14.post1)
  --tag TAG           Download from an explicit Git tag (for example: v1.0.14.post1)
  --url URL           Download from an explicit zip URL
  --zip PATH          Install from a local zip file instead of downloading
  --applications DIR  Override the installation target directory
  --no-verify         Skip post-install verification
  --no-open           Do not open the installed app after install
  --keep-temp         Keep the temporary extraction directory
  -h, --help          Show this help

Environment:
  SAYANE_MACOS_APP_NAME
  SAYANE_MACOS_APPLICATIONS_DIR
  SAYANE_REPO
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      shift
      [[ $# -gt 0 ]] || die "--version requires a value"
      VERSION="$1"
      ;;
    --tag)
      shift
      [[ $# -gt 0 ]] || die "--tag requires a value"
      TAG="$1"
      ;;
    --url)
      shift
      [[ $# -gt 0 ]] || die "--url requires a value"
      DOWNLOAD_URL="$1"
      ;;
    --zip)
      shift
      [[ $# -gt 0 ]] || die "--zip requires a path"
      ZIP_PATH="$1"
      ;;
    --applications)
      shift
      [[ $# -gt 0 ]] || die "--applications requires a path"
      APPLICATIONS_DIR="$1"
      ;;
    --no-verify)
      VERIFY_INSTALL=0
      ;;
    --no-open)
      AUTO_OPEN=0
      ;;
    --keep-temp)
      KEEP_TEMP=1
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

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

normalize_tag() {
  local value="$1"
  if [[ -z "${value}" ]]; then
    return 1
  fi
  if [[ "${value}" == v* ]]; then
    printf '%s\n' "${value}"
  else
    printf 'v%s\n' "${value}"
  fi
}

derive_download_url() {
  if [[ -n "${DOWNLOAD_URL}" ]]; then
    printf '%s\n' "${DOWNLOAD_URL}"
    return 0
  fi
  if [[ -n "${ZIP_PATH}" ]]; then
    return 0
  fi
  if [[ -n "${TAG}" && -z "${VERSION}" ]]; then
    VERSION="${TAG#v}"
  fi
  if [[ -n "${VERSION}" && -z "${TAG}" ]]; then
    TAG="$(normalize_tag "${VERSION}")"
  fi
  if [[ -n "${TAG}" && -n "${VERSION}" ]]; then
    printf 'https://github.com/%s/releases/download/%s/%s-%s-macos-release.zip\n' \
      "${REPO}" "${TAG}" "${APP_NAME}" "${VERSION}"
    return 0
  fi
  printf 'https://github.com/%s/releases/latest/download/%s-latest-macos-release.zip\n' \
    "${REPO}" "${APP_NAME}"
}

cleanup() {
  if [[ "${KEEP_TEMP}" == "1" || -z "${TMP_DIR}" ]]; then
    return 0
  fi
  rm -rf "${TMP_DIR}"
}

download_zip_if_needed() {
  if [[ -n "${ZIP_PATH}" ]]; then
    [[ -f "${ZIP_PATH}" ]] || die "Missing local zip: ${ZIP_PATH}"
    return 0
  fi
  local url
  url="$(derive_download_url)"
  ZIP_PATH="${TMP_DIR}/${APP_NAME}.zip"
  info "Downloading ${url}"
  curl -fL --retry 3 --retry-delay 1 -o "${ZIP_PATH}" "${url}"
}

extract_zip() {
  local extracted_app
  info "Extracting release zip"
  ditto -x -k "${ZIP_PATH}" "${TMP_DIR}/extracted"
  extracted_app="${TMP_DIR}/extracted/${APP_NAME}.app"
  [[ -d "${extracted_app}" ]] || die "Release zip did not contain ${APP_NAME}.app"
  printf '%s\n' "${extracted_app}"
}

install_bundle() {
  local extracted_app="$1"
  INSTALLED_APP_PATH="${APPLICATIONS_DIR}/${APP_NAME}.app"
  mkdir -p "${APPLICATIONS_DIR}"
  info "Installing ${APP_NAME}.app to ${APPLICATIONS_DIR}"
  rm -rf "${INSTALLED_APP_PATH}"
  ditto "${extracted_app}" "${INSTALLED_APP_PATH}"
}

adhoc_sign_if_needed() {
  command -v codesign >/dev/null 2>&1 || return 0
  info "Applying local ad-hoc signature for LaunchServices"
  codesign --force --deep -s - "${INSTALLED_APP_PATH}"
}

verify_bundle() {
  [[ -d "${INSTALLED_APP_PATH}" ]] || die "Missing installed app: ${INSTALLED_APP_PATH}"
  [[ -f "${INSTALLED_APP_PATH}/Contents/Info.plist" ]] || die "Missing Info.plist"
  [[ -x "${INSTALLED_APP_PATH}/Contents/MacOS/${APP_NAME}" ]] || die "Missing executable"
  [[ -x "${INSTALLED_APP_PATH}/Contents/Resources/run-bridge-helper.sh" ]] || die "Missing bundled backend helper"
  plutil -lint "${INSTALLED_APP_PATH}/Contents/Info.plist" >/dev/null
  file "${INSTALLED_APP_PATH}/Contents/MacOS/${APP_NAME}" >/dev/null
  if command -v codesign >/dev/null 2>&1; then
    codesign --verify --deep --strict --verbose=2 "${INSTALLED_APP_PATH}" >/dev/null 2>&1 || true
  fi
}

open_if_needed() {
  [[ "${AUTO_OPEN}" == "1" ]] || return 0
  command -v open >/dev/null 2>&1 || return 0
  info "Opening installed app"
  open "${INSTALLED_APP_PATH}"
}

verify_if_needed() {
  [[ "${VERIFY_INSTALL}" == "1" ]] || return 0
  info "Verifying installed app"
  verify_bundle
}

main() {
  [[ "$(uname -s)" == "Darwin" ]] || die "This installer currently supports macOS only."
  need_cmd curl
  need_cmd ditto
  TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/sayane-macos-release.XXXXXX")"
  trap cleanup EXIT

  download_zip_if_needed
  local extracted_app
  extracted_app="$(extract_zip)"
  install_bundle "${extracted_app}"
  adhoc_sign_if_needed
  verify_if_needed
  open_if_needed

  cat <<EOF

Installed native macOS app from release artifact:
  App: ${INSTALLED_APP_PATH}
  Source zip: ${ZIP_PATH}

Routine flow:
  open "${INSTALLED_APP_PATH}"
EOF
}

main "$@"
