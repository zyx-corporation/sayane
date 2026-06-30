#!/usr/bin/env bash
set -euo pipefail

HOST="${SAYANE_BRIDGE_HOST:-127.0.0.1}"
PORT="${SAYANE_BRIDGE_PORT:-38741}"
BRIDGE_URL="http://${HOST}:${PORT}"
LOG_FILE="${SAYANE_APP_LOG_FILE:-$HOME/.sayane/run-app-local.log}"
TOKEN_FILE="${SAYANE_BRIDGE_TOKEN_FILE:-$HOME/.sayane/bridge.token}"
LOCK_DIR="${SAYANE_BACKEND_LOCK_DIR:-$HOME/.sayane/backend-launch.lock}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_ENV_FILE="${SCRIPT_DIR}/runtime-env.sh"

info() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

if [[ -f "${RUNTIME_ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${RUNTIME_ENV_FILE}"
fi

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

python_supports_sayane_runtime() {
  local python_bin="$1"
  [[ -x "${python_bin}" ]] || return 1
  "${python_bin}" - <<'PY' >/dev/null 2>&1
import importlib
import sys
if sys.version_info < (3, 11):
    raise SystemExit(1)
for module_name in ("sayane", "typer", "fastapi", "uvicorn"):
    importlib.import_module(module_name)
PY
}

resolve_repo_runtime() {
  local repo_root="${SAYANE_REPO_ROOT:-${SAYANE_DEFAULT_REPO_ROOT:-}}"
  local candidate python_bin src_dir
  local -a candidates=()

  if [[ -n "${repo_root}" ]]; then
    candidates+=("${repo_root}")
  fi
  candidates+=(
    "$(cd "${SCRIPT_DIR}/../../.." 2>/dev/null && pwd || true)"
    "$(pwd)"
  )

  for candidate in "${candidates[@]}"; do
    [[ -n "${candidate}" ]] || continue
    [[ -d "${candidate}" ]] || continue
    python_bin="${candidate}/.venv/bin/python"
    src_dir="${candidate}/src"
    [[ -d "${src_dir}" ]] || continue
    python_supports_sayane_runtime "${python_bin}" || continue
    printf '%s\n%s\n' "${python_bin}" "${src_dir}"
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

backend_listener_pids() {
  lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true
}

backend_command_pids() {
  pgrep -f "sayane.*serve --host ${HOST} --port ${PORT}" 2>/dev/null || true
}

backend_process_present() {
  [[ -n "$(backend_listener_pids)" || -n "$(backend_command_pids)" ]]
}

acquire_launch_lock() {
  local attempt
  mkdir -p "$(dirname "${LOCK_DIR}")"
  for attempt in {1..40}; do
    if mkdir "${LOCK_DIR}" 2>/dev/null; then
      trap 'rm -rf "${LOCK_DIR}"' EXIT
      return 0
    fi
    sleep 0.25
  done
  die "Timed out waiting for backend launch lock: ${LOCK_DIR}"
}

main() {
  local sayane_bin
  local repo_runtime repo_python repo_src
  repo_runtime="$(resolve_repo_runtime || true)"
  if [[ -n "${repo_runtime}" ]]; then
    repo_python="$(printf '%s\n' "${repo_runtime}" | sed -n '1p')"
    repo_src="$(printf '%s\n' "${repo_runtime}" | sed -n '2p')"
  else
    sayane_bin="$(find_sayane_cli)" || die "Could not find installed sayane CLI or compatible repo runtime"
  fi
  acquire_launch_lock

  mkdir -p "$HOME/.sayane"
  if [[ ! -f "$HOME/.sayane/profiles/default/sayane.profile.yaml" ]]; then
    info "Initializing ~/.sayane"
    if [[ -n "${repo_python:-}" && -n "${repo_src:-}" ]]; then
      PYTHONPATH="${repo_src}${PYTHONPATH:+:${PYTHONPATH}}" "${repo_python}" -m sayane.cli.main init >>"${LOG_FILE}" 2>&1 || true
    else
      "${sayane_bin}" init >>"${LOG_FILE}" 2>&1 || true
    fi
  fi

  if bridge_healthy; then
    info "Using existing backend at ${BRIDGE_URL}"
    exit 0
  fi

  if backend_process_present; then
    info "Existing backend process detected; waiting for health at ${BRIDGE_URL}"
    wait_for_bridge || die "Existing backend process did not become healthy. Not starting a duplicate. Check ${LOG_FILE}"
    [[ -f "${TOKEN_FILE}" ]] || die "Missing token file after backend warmup: ${TOKEN_FILE}"
    exit 0
  fi

  info "Starting backend through bundled helper"
  if [[ -n "${repo_python:-}" && -n "${repo_src:-}" ]]; then
    nohup env PYTHONPATH="${repo_src}${PYTHONPATH:+:${PYTHONPATH}}" "${repo_python}" -m sayane.cli.main serve --host "${HOST}" --port "${PORT}" >>"${LOG_FILE}" 2>&1 </dev/null &
  else
    nohup "${sayane_bin}" serve --host "${HOST}" --port "${PORT}" >>"${LOG_FILE}" 2>&1 </dev/null &
  fi
  wait_for_bridge || die "Backend did not become healthy. Check ${LOG_FILE}"

  [[ -f "${TOKEN_FILE}" ]] || die "Missing token file after backend startup: ${TOKEN_FILE}"
}

main "$@"
