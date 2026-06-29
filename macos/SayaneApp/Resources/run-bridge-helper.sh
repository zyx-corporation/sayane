#!/usr/bin/env bash
set -euo pipefail

HOST="${SAYANE_BRIDGE_HOST:-127.0.0.1}"
PORT="${SAYANE_BRIDGE_PORT:-38741}"
BRIDGE_URL="http://${HOST}:${PORT}"
LOG_FILE="${SAYANE_APP_LOG_FILE:-$HOME/.sayane/run-app-local.log}"
TOKEN_FILE="${SAYANE_BRIDGE_TOKEN_FILE:-$HOME/.sayane/bridge.token}"

info() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

find_sayane_cli() {
  local candidate
  for candidate in \
    "${SAYANE_CLI_BIN:-}" \
    "$HOME/.local/bin/sayane" \
    /opt/homebrew/bin/sayane \
    /usr/local/bin/sayane \
    /usr/bin/sayane \
    "$(command -v sayane 2>/dev/null || true)"
  do
    [[ -n "${candidate}" ]] || continue
    [[ -x "${candidate}" ]] || continue
    printf '%s\n' "${candidate}"
    return 0
  done
  return 1
}

bridge_healthy() {
  curl --max-time 2 -fsS "${BRIDGE_URL}/health" >/dev/null 2>&1
}

wait_for_bridge() {
  local attempt
  for attempt in {1..30}; do
    if bridge_healthy; then
      return 0
    fi
    sleep 1
  done
  return 1
}

main() {
  local sayane_bin
  sayane_bin="$(find_sayane_cli)" || die "Could not find installed sayane CLI"

  mkdir -p "$HOME/.sayane"
  if [[ ! -f "$HOME/.sayane/profiles/default/sayane.profile.yaml" ]]; then
    info "Initializing ~/.sayane"
    "${sayane_bin}" init >>"${LOG_FILE}" 2>&1 || true
  fi

  if bridge_healthy; then
    info "Using existing Bridge at ${BRIDGE_URL}"
    exit 0
  fi

  info "Starting Bridge through bundled helper"
  nohup "${sayane_bin}" serve --host "${HOST}" --port "${PORT}" >>"${LOG_FILE}" 2>&1 </dev/null &
  wait_for_bridge || die "Bridge did not become healthy. Check ${LOG_FILE}"

  [[ -f "${TOKEN_FILE}" ]] || die "Missing token file after bridge startup: ${TOKEN_FILE}"
}

main "$@"
