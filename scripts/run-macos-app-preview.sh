#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PACKAGE_PATH="$ROOT/macos/SayaneApp"
EXECUTABLE_PATH="$PACKAGE_PATH/.build/arm64-apple-macosx/debug/SayaneApp"
APP_LOG_FILE="${SAYANE_MACOS_APP_PREVIEW_LOG_FILE:-$HOME/.sayane/macos-app-preview.log}"
BRIDGE_URL="${SAYANE_BRIDGE_URL:-http://127.0.0.1:38741}"
BRIDGE_HOST="${SAYANE_BRIDGE_HOST:-127.0.0.1}"
BRIDGE_PORT="${SAYANE_BRIDGE_PORT:-38741}"
BRIDGE_LOG_FILE="${SAYANE_APP_LOG_FILE:-$HOME/.sayane/run-app-local.log}"
BRIDGE_START_MODE="${SAYANE_BRIDGE_START_MODE:-auto}"
RUN_BRIDGE=1
RUN_BUILD=1
OPEN_XCODE=0
STOP_EXISTING=1
FOREGROUND=0

info() { printf '==> %s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --no-bridge      Do not start or refresh the local Bridge
  --bridge-foreground  Start Bridge in the current terminal
  --bridge-background  Start Bridge in the background
  --bridge-terminal    Start Bridge in a new Terminal window (macOS)
  --no-build       Do not run swift build before launch
  --xcode          Open Package.swift in Xcode instead of launching the binary
  --no-stop        Do not stop an existing SayaneApp preview process
  --foreground     Run the native preview in the current terminal
  -h, --help       Show this help

Environment:
  SAYANE_MACOS_APP_PREVIEW_LOG_FILE
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-bridge)
      RUN_BRIDGE=0
      ;;
    --no-build)
      RUN_BUILD=0
      ;;
    --bridge-foreground)
      BRIDGE_START_MODE="foreground"
      ;;
    --bridge-background)
      BRIDGE_START_MODE="background"
      ;;
    --bridge-terminal)
      BRIDGE_START_MODE="terminal"
      ;;
    --xcode)
      OPEN_XCODE=1
      ;;
    --no-stop)
      STOP_EXISTING=0
      ;;
    --foreground)
      FOREGROUND=1
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

preview_pids() {
  pgrep -f "${EXECUTABLE_PATH}" 2>/dev/null || true
}

bridge_healthy() {
  curl --max-time 2 -fsS "${BRIDGE_URL}/health" >/dev/null 2>&1
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

run_init_if_needed() {
  if [[ -f "${HOME}/.sayane/profiles/default/sayane.profile.yaml" ]]; then
    return 0
  fi
  info "Initializing ~/.sayane"
  local python_bin
  python_bin="$(find_python)"
  PYTHONPATH="${ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}" "${python_bin}" -m sayane.cli.main init
}

bridge_listener_pids() {
  lsof -tiTCP:"${BRIDGE_PORT}" -sTCP:LISTEN 2>/dev/null || true
}

bridge_command_pids() {
  pgrep -f "serve --host ${BRIDGE_HOST} --port ${BRIDGE_PORT}" 2>/dev/null || true
}

stop_existing_bridge() {
  local pids
  pids="$(printf '%s\n%s\n' "$(bridge_listener_pids)" "$(bridge_command_pids)" | awk 'NF' | sort -u)"
  [[ -n "${pids}" ]] || return 0
  info "Stopping existing Bridge processes on ${BRIDGE_HOST}:${BRIDGE_PORT}"
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
  [[ -n "${pids}" ]] || return 0
  info "Force stopping stale Bridge processes on ${BRIDGE_HOST}:${BRIDGE_PORT}"
  while IFS= read -r pid; do
    [[ -n "${pid}" ]] || continue
    kill -9 "${pid}" 2>/dev/null || true
  done <<< "${pids}"
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

stop_existing_preview() {
  local pids
  pids="$(preview_pids)"
  [[ -n "${pids}" ]] || return 0
  info "Stopping existing SayaneApp preview"
  while IFS= read -r pid; do
    [[ -n "${pid}" ]] || continue
    kill "${pid}" 2>/dev/null || true
  done <<< "${pids}"
  sleep 1
}

ensure_bridge() {
  [[ "${RUN_BRIDGE}" == "1" ]] || return 0
  if bridge_healthy; then
    info "Using existing Bridge at ${BRIDGE_URL}"
    return 0
  fi
  run_init_if_needed
  stop_existing_bridge
  mkdir -p "$(dirname "${BRIDGE_LOG_FILE}")"
  info "Starting Bridge through local launcher at ${BRIDGE_URL} (mode: ${BRIDGE_START_MODE})"
  if [[ "${BRIDGE_START_MODE}" == "auto" ]]; then
    bash "${ROOT}/scripts/run-app-local.sh" --no-open --no-bootstrap-check
  else
    bash "${ROOT}/scripts/run-app-local.sh" "--${BRIDGE_START_MODE}" --no-open --no-bootstrap-check
  fi
  wait_for_bridge || die "Bridge did not become healthy at ${BRIDGE_URL}. Check ${BRIDGE_LOG_FILE}"
}

ensure_build() {
  [[ "${RUN_BUILD}" == "1" ]] || return 0
  info "Building macOS app preview"
  swift build --package-path "${PACKAGE_PATH}"
}

ensure_executable() {
  [[ -x "${EXECUTABLE_PATH}" ]] || die "Missing executable: ${EXECUTABLE_PATH}"
}

launch_foreground() {
  info "Launching SayaneApp in foreground"
  exec "${EXECUTABLE_PATH}"
}

launch_background() {
  mkdir -p "$(dirname "${APP_LOG_FILE}")"
  info "Launching SayaneApp in background"
  nohup "${EXECUTABLE_PATH}" >>"${APP_LOG_FILE}" 2>&1 </dev/null &
  sleep 2
  local pids
  pids="$(preview_pids)"
  [[ -n "${pids}" ]] || die "SayaneApp did not stay running. Check ${APP_LOG_FILE}"
}

activate_preview_window() {
  command -v osascript >/dev/null 2>&1 || return 0
  osascript <<'APPLESCRIPT' >/dev/null 2>&1 || true
tell application "System Events"
  if exists process "SayaneApp" then
    tell process "SayaneApp"
      set frontmost to true
    end tell
  end if
end tell
APPLESCRIPT
}

print_summary() {
  local bootstrap_url
  bootstrap_url="${BRIDGE_URL}/app/ui"
  if [[ -f "${HOME}/.sayane/bridge.token" ]]; then
    bootstrap_url="${BRIDGE_URL}/app/ui?bootstrap_token=\$(cat ~/.sayane/bridge.token)"
  fi
  cat <<EOF

SayaneApp native preview:
  Executable: ${EXECUTABLE_PATH}
  Bridge health: ${BRIDGE_URL}/health
  Bridge start mode: ${BRIDGE_START_MODE}
  Bridge log: ${BRIDGE_LOG_FILE}
  App log: ${APP_LOG_FILE}

Useful checks:
  pgrep -fl "${EXECUTABLE_PATH}"
  curl -s "${BRIDGE_URL}/health"
  tail -n 40 "${APP_LOG_FILE}"
  tail -n 40 "${BRIDGE_LOG_FILE}"

Notes:
  - On macOS, Bridge auto mode prefers a dedicated Terminal window.
  - If the app shows disconnected state, keep the Bridge terminal open and use Reconnect in the app.
  - Browser compatibility shell remains debug-only and is not part of the normal macOS operator flow.

Maintainer/debug checks:
  Compatibility shell: ${BRIDGE_URL}/app/ui
  Open manually if needed: ${bootstrap_url}
EOF
}

main() {
  cd "${ROOT}"

  if [[ "${OPEN_XCODE}" == "1" ]]; then
    ensure_bridge
    info "Opening Swift package in Xcode"
    open "${PACKAGE_PATH}/Package.swift"
    printf 'Opened Swift package in Xcode: %s/Package.swift\n' "${PACKAGE_PATH}"
    exit 0
  fi

  [[ "${STOP_EXISTING}" == "1" ]] && stop_existing_preview
  ensure_bridge
  ensure_build
  ensure_executable

  if [[ "${FOREGROUND}" == "1" ]]; then
    launch_foreground
  fi

  launch_background
  activate_preview_window
  print_summary
  exit 0
}

main "$@"
