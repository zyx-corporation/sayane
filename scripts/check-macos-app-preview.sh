#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${SAYANE_BRIDGE_HOST:-127.0.0.1}"
PORT="${SAYANE_BRIDGE_PORT:-38741}"
BASE_URL="http://${HOST}:${PORT}"
PACKAGE_PATH="$ROOT/macos/SayaneApp"
TOKEN_FILE="${SAYANE_BRIDGE_TOKEN_FILE:-$HOME/.sayane/bridge.token}"
COOKIE_JAR="${SAYANE_MACOS_SMOKE_COOKIE_JAR:-$HOME/.sayane/macos-app-smoke.cookies.txt}"
LOG_FILE="${SAYANE_MACOS_SMOKE_LOG_FILE:-$HOME/.sayane/macos-app-smoke.log}"
START_LOCAL_SHELL=1
RUN_BUILD=1
RUN_TESTS=1
WITH_DEBUG_SHELL=0
VERBOSE=0
TEST_TIMEOUT_SECONDS="${SAYANE_MACOS_SMOKE_TEST_TIMEOUT_SECONDS:-120}"
CHECK_TIMEOUT_SECONDS="${SAYANE_MACOS_SMOKE_CHECK_TIMEOUT_SECONDS:-15}"
CURRENT_STEP="initializing"
STARTED_BRIDGE=0
LAST_RESPONSE_BODY=""

info() { printf '==> %s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --no-start   Use the existing Bridge instead of starting a fresh one
  --no-build   Skip swift build
  --no-tests   Skip swift test validation
  --with-debug-shell  Also validate /app/ui compatibility shell flows
  --verbose    Print response-body and curl diagnostics on failure
  -h, --help   Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-start)
      START_LOCAL_SHELL=0
      ;;
    --no-build)
      RUN_BUILD=0
      ;;
    --no-tests)
      RUN_TESTS=0
      ;;
    --with-debug-shell)
      WITH_DEBUG_SHELL=1
      ;;
    --verbose)
      VERBOSE=1
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

find_sayane() {
  if [[ -x "${ROOT}/.venv/bin/sayane" ]]; then
    printf '%s\n' "${ROOT}/.venv/bin/sayane"
    return 0
  fi
  if command -v sayane >/dev/null 2>&1; then
    local sayane_bin
    sayane_bin="$(command -v sayane)"
    if sayane_supports_runtime "${sayane_bin}"; then
      printf '%s\n' "${sayane_bin}"
      return 0
    fi
  fi
  die "Could not find a compatible \`sayane\` CLI. Run \`uv run --extra dev pytest -q\` once or create \`.venv\` with \`pip install -e \".[dev]\"\`."
}

find_python() {
  local candidate
  for candidate in "${ROOT}/.venv/bin/python" python3 python; do
    if [[ "${candidate}" == *"/"* ]]; then
      [[ -x "${candidate}" ]] || continue
    elif ! command -v "${candidate}" >/dev/null 2>&1; then
      continue
    else
      candidate="$(command -v "${candidate}")"
    fi
    if python_supports_sayane_runtime "${candidate}"; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  die "Could not find a compatible Python runtime (>=3.11 with Sayane deps). Run \`uv run --extra dev pytest -q\` once or create \`.venv\` with \`pip install -e \".[dev]\"\`."
}

python_supports_sayane_runtime() {
  local python_bin="$1"
  "${python_bin}" - <<'PY' >/dev/null 2>&1
import importlib
import sys

if sys.version_info < (3, 11):
    raise SystemExit(1)

required = [
    "fastapi",
    "pydantic",
    "yaml",
    "cryptography",
    "typer",
    "uvicorn",
    "mcp",
]
for module_name in required:
    importlib.import_module(module_name)
PY
}

sayane_supports_runtime() {
  local sayane_bin="$1"
  "${sayane_bin}" --version >/dev/null 2>&1
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

print_last_response_body() {
  [[ -n "${LAST_RESPONSE_BODY}" ]] || return 0
  printf '\nLast response body:\n%s\n' "${LAST_RESPONSE_BODY}" >&2
}

report_failure() {
  local exit_code="${1:-1}"
  local line_no="${2:-unknown}"
  printf '\nerror: smoke check failed during "%s" (line %s)\n' "${CURRENT_STEP}" "${line_no}" >&2
  printf '  Bridge: %s\n' "${BASE_URL}" >&2
  printf '  Token file: %s\n' "${TOKEN_FILE}" >&2
  printf '  Cookie jar: %s\n' "${COOKIE_JAR}" >&2
  printf '  Log: %s\n' "${LOG_FILE}" >&2
  printf '  Hint: curl -s %s/health\n' "${BASE_URL}" >&2
  if [[ "${WITH_DEBUG_SHELL}" == "1" ]]; then
    printf '  Hint: open %s/app/ui?bootstrap_token=$(cat %s)\n' "${BASE_URL}" "${TOKEN_FILE}" >&2
  fi
  if [[ -f "${LOG_FILE}" ]]; then
    printf '\nRecent Bridge log tail:\n' >&2
    tail -n 40 "${LOG_FILE}" >&2 || true
  fi
  if [[ "${VERBOSE}" == "1" ]]; then
    print_last_response_body
  fi
  exit "${exit_code}"
}

trap 'report_failure $? $LINENO' ERR

bridge_listener_pids() {
  lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true
}

bridge_command_pids() {
  pgrep -f "serve --host ${HOST} --port ${PORT}" 2>/dev/null || true
}

stop_existing_bridge() {
  local pids
  pids="$(printf '%s\n%s\n' "$(bridge_listener_pids)" "$(bridge_command_pids)" | awk 'NF' | sort -u)"
  [[ -z "${pids}" ]] && return 0
  info "Stopping existing Bridge processes on ${HOST}:${PORT}"
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
  [[ -z "${pids}" ]] && return 0
  info "Force stopping stale Bridge processes on ${HOST}:${PORT}"
  while IFS= read -r pid; do
    [[ -n "${pid}" ]] || continue
    kill -9 "${pid}" 2>/dev/null || true
  done <<< "${pids}"
}

bridge_healthy() {
  curl -fsS "${BASE_URL}/health" >/dev/null 2>&1
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

run_with_timeout() {
  local seconds="$1"
  shift
  python3 - "$seconds" "$@" <<'PY'
import subprocess
import sys

timeout = int(sys.argv[1])
cmd = sys.argv[2:]
try:
    completed = subprocess.run(cmd, check=False, timeout=timeout)
    raise SystemExit(completed.returncode)
except subprocess.TimeoutExpired:
    print(f"error: timed out after {timeout}s: {' '.join(cmd)}", file=sys.stderr)
    raise SystemExit(124)
PY
}

cleanup_stale_swiftpm_processes() {
  local pids=""
  pids="$(pgrep -f "/macos/SayaneApp/.build|swift test --package-path ${PACKAGE_PATH}|SayaneAppPackageTests" 2>/dev/null || true)"
  [[ -n "${pids}" ]] || return 0
  info "Stopping stale SwiftPM test processes"
  while IFS= read -r pid; do
    [[ -n "${pid}" ]] || continue
    kill "${pid}" 2>/dev/null || true
  done <<< "${pids}"
  sleep 1
}

prepare_local_bridge() {
  local sayane_bin
  sayane_bin="$(find_sayane)"
  if [[ ! -f "${HOME}/.sayane/profiles/default/sayane.profile.yaml" ]]; then
    info "Initializing ~/.sayane"
    "${sayane_bin}" init
  fi
  stop_existing_bridge
  mkdir -p "$(dirname "${LOG_FILE}")"
  info "Starting Bridge for smoke check"
  CURRENT_STEP="starting bridge"
  if ! bash "${ROOT}/scripts/run-app-local.sh" --no-open --no-bootstrap-check; then
    warn "Initial Bridge launch did not become healthy; retrying once"
    stop_existing_bridge
    bash "${ROOT}/scripts/run-app-local.sh" --no-open --no-bootstrap-check
  fi
  STARTED_BRIDGE=1
  CURRENT_STEP="waiting for bridge health"
  wait_for_bridge || die "Bridge did not become healthy. Check ${LOG_FILE}"
}

check_json_endpoint() {
  local path="$1"
  info "Checking ${path}"
  CURRENT_STEP="checking ${path}"
  capture_response_body \
    -fsS \
    -H "Authorization: Bearer ${TOKEN}" \
    "${BASE_URL}${path}" >/dev/null
}

bootstrap_ui_session() {
  mkdir -p "$(dirname "${COOKIE_JAR}")"
  rm -f "${COOKIE_JAR}"
  info "Bootstrapping resident app debug shell session"
  CURRENT_STEP="bootstrapping debug shell session"
  capture_response_body \
    -fsS \
    -c "${COOKIE_JAR}" \
    "${BASE_URL}/app/ui?bootstrap_token=${TOKEN}" >/dev/null
}

check_cookie_endpoint() {
  local path="$1"
  info "Checking ${path} with debug-shell session"
  CURRENT_STEP="checking ${path} with debug-shell session"
  capture_response_body \
    -fsS \
    -b "${COOKIE_JAR}" \
    "${BASE_URL}${path}" >/dev/null
}

main() {
  cd "${ROOT}"

  if [[ "${START_LOCAL_SHELL}" == "1" ]]; then
    prepare_local_bridge
  fi

  require_token

  if [[ "${RUN_BUILD}" == "1" ]]; then
    info "Building macOS app preview"
    swift build --package-path "${PACKAGE_PATH}"
  fi

  if [[ "${RUN_TESTS}" == "1" ]]; then
    cleanup_stale_swiftpm_processes
    info "Running full Swift package test suite"
    CURRENT_STEP="running swift test suite"
    run_with_timeout "${TEST_TIMEOUT_SECONDS}" \
      swift test --package-path "${PACKAGE_PATH}" --disable-xctest
  fi

  check_json_endpoint "/health"
  check_json_endpoint "/app/contract"
  check_json_endpoint "/app/screen-state/home"
  check_json_endpoint "/app/screen-state/candidates"
  check_json_endpoint "/app/screen-state/daemon"

  if [[ "${WITH_DEBUG_SHELL}" == "1" ]]; then
    bootstrap_ui_session
    check_cookie_endpoint "/app/ui"
  fi

  cat <<EOF

macOS app preview smoke check passed:
  Build: $( [[ "${RUN_BUILD}" == "1" ]] && printf 'yes' || printf 'skipped' )
  Tests: $( [[ "${RUN_TESTS}" == "1" ]] && printf 'yes' || printf 'skipped' )
  Debug shell: $( [[ "${WITH_DEBUG_SHELL}" == "1" ]] && printf 'checked' || printf 'skipped' )
  Bridge: ${BASE_URL}
  Cookie jar: ${COOKIE_JAR}
  Log: ${LOG_FILE}
EOF
}

main "$@"
