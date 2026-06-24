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
  if [[ -x "${ROOT}/.venv/bin/python" ]]; then
    printf '%s\n' "${ROOT}/.venv/bin/python"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi
  die "Could not find python for Bridge startup"
}

spawn_detached() {
  local log_file="$1"
  shift
  env DETACH_LOG_FILE="${log_file}" DETACH_ROOT="${ROOT}" DETACH_ARGV="$(printf '%s\n' "$@")" \
    python3 - <<'PY'
import os
import sys

log_path = os.environ["DETACH_LOG_FILE"]
argv_blob = os.environ["DETACH_ARGV"]
argv = [part for part in argv_blob.splitlines() if part]
root = os.environ["DETACH_ROOT"]

pid = os.fork()
if pid > 0:
    os.waitpid(pid, 0)
    raise SystemExit(0)

os.setsid()

pid = os.fork()
if pid > 0:
    os._exit(0)

os.chdir(root)
os.umask(0)

with open(log_path, "ab", buffering=0) as log:
    fd = log.fileno()
    devnull = os.open(os.devnull, os.O_RDONLY)
    os.dup2(devnull, 0)
    os.dup2(fd, 1)
    os.dup2(fd, 2)
    try:
        max_fd = os.sysconf("SC_OPEN_MAX")
    except (AttributeError, ValueError):
        max_fd = 256
    for extra_fd in range(3, int(max_fd)):
        try:
            if extra_fd != fd:
                os.close(extra_fd)
        except OSError:
            pass
    if devnull > 2:
        os.close(devnull)
    os.execvp(argv[0], argv)
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

stop_existing_bridge() {
  local pids
  pids="$(bridge_listener_pids)"
  [[ -n "${pids}" ]] || return 0
  info "Stopping existing Bridge listener on ${BRIDGE_HOST}:${BRIDGE_PORT}"
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
  local python_bin
  python_bin="$(find_python)"
  mkdir -p "$(dirname "${BRIDGE_LOG_FILE}")"
  info "Starting Bridge directly at ${BRIDGE_URL}"
  spawn_detached "${BRIDGE_LOG_FILE}" env \
    "PYTHONPATH=${ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}" \
    "${python_bin}" -m sayane.cli.main serve --host "${BRIDGE_HOST}" --port "${BRIDGE_PORT}"
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
  spawn_detached "${APP_LOG_FILE}" "${EXECUTABLE_PATH}"
  sleep 2
  local pids
  pids="$(preview_pids)"
  [[ -n "${pids}" ]] || die "SayaneApp did not stay running. Check ${APP_LOG_FILE}"
}

print_summary() {
  cat <<EOF

SayaneApp native preview:
  Executable: ${EXECUTABLE_PATH}
  Bridge UI: ${BRIDGE_URL}/app/ui
  App log: ${APP_LOG_FILE}

Useful checks:
  pgrep -fl "${EXECUTABLE_PATH}"
  tail -n 40 "${APP_LOG_FILE}"
  open -a "Google Chrome" "${BRIDGE_URL}/app/ui?bootstrap_token=\$(cat ~/.sayane/bridge.token)"
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
  print_summary
  exit 0
}

main "$@"
