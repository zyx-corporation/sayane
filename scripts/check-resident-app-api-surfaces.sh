#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${SAYANE_BRIDGE_HOST:-127.0.0.1}"
PORT="${SAYANE_BRIDGE_PORT:-38741}"
BASE_URL="http://${HOST}:${PORT}"
TOKEN_FILE="${SAYANE_BRIDGE_TOKEN_FILE:-$HOME/.sayane/bridge.token}"
CHECK_TIMEOUT_SECONDS="${SAYANE_API_SURFACE_CHECK_TIMEOUT_SECONDS:-15}"
START_BRIDGE=0
LOG_FILE="${SAYANE_API_SURFACE_LOG_FILE:-$HOME/.sayane/resident-app-api-surfaces.log}"
LAST_RESPONSE_BODY=""

info() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --start      Start a local Bridge when one is not healthy
  -h, --help   Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --start)
      START_BRIDGE=1
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

require_token() {
  [[ -f "${TOKEN_FILE}" ]] || die "Missing token file: ${TOKEN_FILE}"
  TOKEN="$(<"${TOKEN_FILE}")"
  [[ -n "${TOKEN}" ]] || die "Token file is empty: ${TOKEN_FILE}"
}

capture_response_body() {
  local output_file
  output_file="$(mktemp)"
  if curl --max-time "${CHECK_TIMEOUT_SECONDS}" "$@" -o "${output_file}"; then
    LAST_RESPONSE_BODY="$(cat "${output_file}")"
    rm -f "${output_file}"
    return 0
  fi
  LAST_RESPONSE_BODY="$(cat "${output_file}")"
  rm -f "${output_file}"
  return 1
}

bridge_healthy() {
  curl --max-time 2 -fsS "${BASE_URL}/health" >/dev/null 2>&1
}

find_python() {
  if [[ -x "${ROOT}/.venv/bin/python" ]]; then
    printf '%s\n' "${ROOT}/.venv/bin/python"
    return 0
  fi
  command -v python3 >/dev/null 2>&1 || die "Could not find python3"
  command -v python3
}

find_sayane() {
  if [[ -x "${ROOT}/.venv/bin/sayane" ]]; then
    printf '%s\n' "${ROOT}/.venv/bin/sayane"
    return 0
  fi
  if command -v sayane >/dev/null 2>&1; then
    command -v sayane
    return 0
  fi
  die "Could not find \`sayane\`."
}

run_init_if_needed() {
  if [[ -f "${HOME}/.sayane/profiles/default/sayane.profile.yaml" ]]; then
    return 0
  fi
  local sayane_bin
  sayane_bin="$(find_sayane)"
  info "Initializing ~/.sayane"
  "${sayane_bin}" init
}

bridge_listener_pids() {
  lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true
}

bridge_command_pids() {
  pgrep -f "serve --host ${HOST} --port ${PORT}" 2>/dev/null || true
}

stop_existing_bridge() {
  local pids
  pids="$(printf '%s\n%s\n' "$(bridge_listener_pids)" "$(bridge_command_pids)" | awk 'NF' | sort -u)"
  [[ -n "${pids}" ]] || return 0
  info "Stopping existing Bridge processes on ${HOST}:${PORT}"
  while IFS= read -r pid; do
    [[ -n "${pid}" ]] || continue
    kill "${pid}" 2>/dev/null || true
  done <<< "${pids}"
  sleep 1
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

ensure_bridge() {
  if bridge_healthy; then
    return 0
  fi
  [[ "${START_BRIDGE}" == "1" ]] || die "Bridge is not healthy at ${BASE_URL}"
  run_init_if_needed
  stop_existing_bridge
  local sayane_bin
  sayane_bin="$(find_sayane)"
  mkdir -p "$(dirname "${LOG_FILE}")"
  info "Starting Bridge at ${BASE_URL}"
  nohup "${sayane_bin}" serve --host "${HOST}" --port "${PORT}" >"${LOG_FILE}" 2>&1 &
  wait_for_bridge || die "Bridge did not become healthy. Check ${LOG_FILE}"
}

check_json_surface() {
  local path="$1"
  info "Checking ${path}"
  capture_response_body \
    -fsS \
    -H "Authorization: Bearer ${TOKEN}" \
    "${BASE_URL}${path}" >/dev/null
}

main() {
  cd "${ROOT}"
  require_token
  ensure_bridge
  check_json_surface "/health"
  check_json_surface "/app/contract"
  check_json_surface "/app/overview"
  check_json_surface "/app/screen-state/home"
  check_json_surface "/app/daemon-overview"
  check_json_surface "/app/operator-phase-status"
  check_json_surface "/app/daemon-packaging-status"
  check_json_surface "/app/daemon-service-targets-status"
  check_json_surface "/app/daemon-service-control-boundary"
  check_json_surface "/app/daemon-supervision-status"
  check_json_surface "/app/daemon-recovery-consent-status"
  check_json_surface "/app/daemon-preflight"
  check_json_surface "/app/screen-state/daemon"
  check_json_surface "/app/candidates"
  check_json_surface "/app/screen-state/candidates"
  cat <<EOF

Resident app API surface smoke passed:
  Bridge: ${BASE_URL}
  Token file: ${TOKEN_FILE}
EOF
}

main "$@"
