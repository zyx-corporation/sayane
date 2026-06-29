#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

INSTALL_DIR="${TMP_DIR}/install-root"
BIN_DIR="${TMP_DIR}/bin"
HOME_DIR="${TMP_DIR}/home"
LOG_FILE="${TMP_DIR}/install.log"

info() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0")

Runs a local smoke check for the primary curl+bash installer path using:

- temporary install/bin/home directories
- local source install instead of network install
- non-interactive quickstart output
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

mkdir -p "${INSTALL_DIR}" "${BIN_DIR}" "${HOME_DIR}"

info "Running installer smoke with local source"
(
  export HOME="${HOME_DIR}"
  export SAYANE_INSTALL_DIR="${INSTALL_DIR}"
  export SAYANE_BIN_DIR="${BIN_DIR}"
  export SAYANE_SOURCE_DIR="${ROOT}"
  export SAYANE_DEV=1
  export SAYANE_YES=1
  export SAYANE_PRINT_QUICKSTART=1
  bash "${ROOT}/scripts/install.sh"
) | tee "${LOG_FILE}"

WRAPPER="${BIN_DIR}/sayane"
[[ -x "${WRAPPER}" ]] || die "Missing wrapper: ${WRAPPER}"

info "Checking installed CLI"
"${WRAPPER}" --version >/dev/null

PROFILE_PATH="${HOME_DIR}/.sayane/profiles/default/sayane.profile.yaml"
[[ -f "${PROFILE_PATH}" ]] || die "Missing initialized profile: ${PROFILE_PATH}"

grep -q "Quickstart commands:" "${LOG_FILE}" || die "Installer did not print quickstart commands"
grep -q "Primary install path complete: curl+bash -> CLI / Bridge runtime" "${LOG_FILE}" || die "Missing primary path hint"

cat <<EOF

Installer smoke passed:
  wrapper: ${WRAPPER}
  profile: ${PROFILE_PATH}
  log: ${LOG_FILE}
EOF
