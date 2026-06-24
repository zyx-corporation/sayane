#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${SAYANE_BRIDGE_HOST:-127.0.0.1}"
PORT="${SAYANE_BRIDGE_PORT:-38741}"
BRIDGE_URL="http://${HOST}:${PORT}"
APP_URL="${BRIDGE_URL}/app/ui"
TOKEN_FILE="${SAYANE_BRIDGE_TOKEN_FILE:-$HOME/.sayane/bridge.token}"
LOG_FILE="${SAYANE_APP_LOG_FILE:-$HOME/.sayane/run-app-local.log}"
BOOTSTRAP_CHECK=1
AUTO_OPEN=1
AUTO_INIT=1
START_MODE="auto"

info() { printf '==> %s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --foreground        Start \`sayane serve\` in the current terminal
  --no-open           Do not open the browser URL
  --no-init           Do not run \`sayane init\` automatically
  --no-bootstrap-check  Skip bearer-based \`/app/ui\` check
  -h, --help          Show this help

Environment:
  SAYANE_BRIDGE_HOST
  SAYANE_BRIDGE_PORT
  SAYANE_BRIDGE_TOKEN_FILE
  SAYANE_APP_LOG_FILE
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --foreground)
      START_MODE="foreground"
      ;;
    --no-open)
      AUTO_OPEN=0
      ;;
    --no-init)
      AUTO_INIT=0
      ;;
    --no-bootstrap-check)
      BOOTSTRAP_CHECK=0
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

find_sayane_python() {
  if [[ -x "${ROOT}/.venv/bin/python" ]]; then
    printf '%s\n' "${ROOT}/.venv/bin/python"
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi
  die "Could not find \`python3\` for background Bridge startup."
}

SAYANE_PYTHON_BIN="$(find_sayane_python)"
SAYANE_PYTHONPATH="${ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

run_sayane_cli() {
  PYTHONPATH="${SAYANE_PYTHONPATH}" "${SAYANE_PYTHON_BIN}" -m sayane.cli.main "$@"
}

run_init_if_needed() {
  if [[ "${AUTO_INIT}" != "1" ]]; then
    return 0
  fi
  if [[ -f "${HOME}/.sayane/profiles/default/sayane.profile.yaml" ]]; then
    return 0
  fi
  info "Initializing ~/.sayane"
  run_sayane_cli init
}

bridge_healthy() {
  curl -fsS "${BRIDGE_URL}/health" >/dev/null 2>&1
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

bridge_listener_pids() {
  lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true
}

bridge_command_pids() {
  pgrep -f "serve --host ${HOST} --port ${PORT}" 2>/dev/null || true
}

stop_existing_bridge() {
  local pids listener_pids command_pids
  listener_pids="$(bridge_listener_pids)"
  command_pids="$(bridge_command_pids)"
  pids="$(printf '%s\n%s\n' "${listener_pids}" "${command_pids}" | awk 'NF' | sort -u)"
  if [[ -z "${pids}" ]]; then
    return 0
  fi
  info "Stopping existing Bridge processes for ${HOST}:${PORT}"
  while IFS= read -r pid; do
    [[ -n "${pid}" ]] || continue
    kill "${pid}" 2>/dev/null || true
  done <<< "${pids}"

  local attempt
  for attempt in {1..10}; do
    if [[ -z "$(bridge_listener_pids)" && -z "$(bridge_command_pids)" ]]; then
      return 0
    fi
    sleep 1
  done

  pids="$(printf '%s\n%s\n' "$(bridge_listener_pids)" "$(bridge_command_pids)" | awk 'NF' | sort -u)"
  if [[ -n "${pids}" ]]; then
    warn "Bridge process still present; forcing stop on ${HOST}:${PORT}"
    while IFS= read -r pid; do
      [[ -n "${pid}" ]] || continue
      kill -9 "${pid}" 2>/dev/null || true
    done <<< "${pids}"
  fi
}

start_bridge_background() {
  mkdir -p "$(dirname "${LOG_FILE}")"
  info "Starting Bridge in background"
  nohup env PYTHONPATH="${SAYANE_PYTHONPATH}" "${SAYANE_PYTHON_BIN}" -m sayane.cli.main serve --host "${HOST}" --port "${PORT}" >"${LOG_FILE}" 2>&1 </dev/null &
}

start_bridge_foreground() {
  info "Starting Bridge in foreground at ${BRIDGE_URL}"
  exec env PYTHONPATH="${SAYANE_PYTHONPATH}" "${SAYANE_PYTHON_BIN}" -m sayane.cli.main serve --host "${HOST}" --port "${PORT}"
}

ensure_token() {
  [[ -f "${TOKEN_FILE}" ]] || die "Missing token file: ${TOKEN_FILE}"
  TOKEN="$(<"${TOKEN_FILE}")"
  [[ -n "${TOKEN}" ]] || die "Token file is empty: ${TOKEN_FILE}"
}

bootstrap_check() {
  if [[ "${BOOTSTRAP_CHECK}" != "1" ]]; then
    return 0
  fi
  info "Checking resident app bootstrap"
  curl -fsS -H "Authorization: Bearer ${TOKEN}" "${APP_URL}" >/dev/null
}

open_browser() {
  if [[ "${AUTO_OPEN}" != "1" ]]; then
    return 0
  fi
  local bootstrap_url="${APP_URL}?bootstrap_token=${TOKEN}"
  if command -v open >/dev/null 2>&1 && [[ -d "/Applications/Google Chrome.app" ]]; then
    info "Opening browser bootstrap in Google Chrome"
    (nohup open -a "Google Chrome" "${bootstrap_url}" >/dev/null 2>&1 &) || warn "Could not open Google Chrome automatically"
    return 0
  fi
  if command -v open >/dev/null 2>&1; then
    info "Opening browser bootstrap"
    (nohup open "${bootstrap_url}" >/dev/null 2>&1 &) || warn "Could not open browser automatically"
    return 0
  fi
  if command -v xdg-open >/dev/null 2>&1; then
    info "Opening browser bootstrap"
    (nohup xdg-open "${bootstrap_url}" >/dev/null 2>&1 &) || warn "Could not open browser automatically"
    return 0
  fi
  warn "No supported browser opener found. Open manually: ${bootstrap_url}"
}

print_summary() {
  cat <<EOF

Resident app local shell:
  URL: ${APP_URL}
  Health: ${BRIDGE_URL}/health
  Token: ${TOKEN_FILE}

Useful checks:
  curl -s ${BRIDGE_URL}/health
  curl -s -H "Authorization: Bearer \$(cat ${TOKEN_FILE})" ${BRIDGE_URL}/app/contract
  curl -s -H "Authorization: Bearer \$(cat ${TOKEN_FILE})" ${BRIDGE_URL}/app/overview
  curl -s -H "Authorization: Bearer \$(cat ${TOKEN_FILE})" ${BRIDGE_URL}/app/operator-phase-status
  curl -s -H "Authorization: Bearer \$(cat ${TOKEN_FILE})" ${BRIDGE_URL}/app/daemon-packaging-status
  curl -s -H "Authorization: Bearer \$(cat ${TOKEN_FILE})" ${BRIDGE_URL}/app/daemon-service-targets-status
  sayane app daemon-operator-phase-status --json
  sayane app daemon-service-targets-status --json
  sayane app daemon-preflight --json
  sayane app daemon-proof-diagnostics --operation-class bridge_health --json

Notes:
  - Current resident app entrypoint is ${APP_URL}
  - Bridge startup prefers repo-local source via PYTHONPATH=${ROOT}/src
  - Do not use http://127.0.0.1:8008/index.html
  - Browser bootstrap is performed through one local URL hop using /app/ui?bootstrap_token=...
  - If browser or follow-up shell requests return 401, reopen ${APP_URL} after restarting the Bridge
EOF
  if [[ "${START_MODE}" == "auto" ]]; then
    printf '  - Background log: %s\n' "${LOG_FILE}"
  fi
}

main() {
  run_init_if_needed
  stop_existing_bridge

  if [[ "${START_MODE}" == "foreground" ]]; then
    start_bridge_foreground
  fi

  start_bridge_background
  info "Waiting for Bridge"
  if ! wait_for_bridge; then
    warn "Initial Bridge launch did not become healthy; retrying once"
    stop_existing_bridge
    start_bridge_background
    info "Waiting for Bridge"
    wait_for_bridge || die "Bridge did not become healthy. Check ${LOG_FILE}"
  fi

  ensure_token
  bootstrap_check
  open_browser
  print_summary
}

main "$@"
