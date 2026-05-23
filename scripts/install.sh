#!/usr/bin/env bash
# Omomuki installer for macOS and Linux.
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/zyx-corporation/omomuki/main/scripts/install.sh | bash
#   OMOMUKI_REF=v0.5.9 bash scripts/install.sh
#
# Environment:
#   OMOMUKI_REPO          GitHub repo (default: zyx-corporation/omomuki)
#   OMOMUKI_REF           Git ref to install (default: main)
#   OMOMUKI_INSTALL_DIR   Install root (default: ~/.local/share/omomuki)
#   OMOMUKI_BIN_DIR       Wrapper scripts (default: ~/.local/bin)
#   OMOMUKI_SOURCE_DIR    Local checkout; pip install -e instead of git URL (CI/dev)
#   OMOMUKI_DEV           Set to 1 to install [dev] extras
#   OMOMUKI_SKIP_INIT     Set to 1 to skip `omomuki init`
#   OMOMUKI_YES           Set to 1 to skip confirmation prompts

set -euo pipefail

OMOMUKI_REPO="${OMOMUKI_REPO:-zyx-corporation/omomuki}"
OMOMUKI_REF="${OMOMUKI_REF:-main}"
OMOMUKI_INSTALL_DIR="${OMOMUKI_INSTALL_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/omomuki}"
OMOMUKI_BIN_DIR="${OMOMUKI_BIN_DIR:-${XDG_BIN_HOME:-$HOME/.local/bin}}"
OMOMUKI_GIT_URL="https://github.com/${OMOMUKI_REPO}.git"
VENV_DIR="${OMOMUKI_INSTALL_DIR}/venv"
WRAPPER="${OMOMUKI_BIN_DIR}/omomuki"

info() { printf '==> %s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

detect_platform() {
  case "$(uname -s)" in
    Darwin) PLATFORM=macos ;;
    Linux) PLATFORM=linux ;;
    MINGW* | MSYS* | CYGWIN*)
      die "Windows detected. Use PowerShell: irm .../scripts/install.ps1 | iex"
      ;;
    *)
      die "Unsupported OS: $(uname -s). See docs/install.md"
      ;;
  esac
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

find_python() {
  local candidates=(python3.13 python3.12 python3.11 python3)
  local py
  for py in "${candidates[@]}"; do
    if command -v "$py" >/dev/null 2>&1; then
      if "$py" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
        echo "$py"
        return 0
      fi
    fi
  done
  die "Python 3.11+ is required. Install from https://www.python.org/downloads/ or your package manager."
}

ensure_venv() {
  local py="$1"
  if ! "$py" -m venv --help >/dev/null 2>&1; then
    if [[ "$PLATFORM" == "linux" ]] && command -v apt-get >/dev/null 2>&1; then
      die "python3-venv is missing. Run: sudo apt install python3-venv"
    fi
    die "Python venv module unavailable for $py"
  fi
  if [[ ! -d "$VENV_DIR" ]]; then
    info "Creating virtualenv at ${VENV_DIR}"
    "$py" -m venv "$VENV_DIR"
  else
    info "Using existing virtualenv at ${VENV_DIR}"
  fi
}

install_package() {
  local pip="${VENV_DIR}/bin/pip"
  info "Upgrading pip"
  "$pip" install --upgrade pip wheel >/dev/null

  if [[ -n "${OMOMUKI_SOURCE_DIR:-}" ]]; then
    info "Installing from local source: ${OMOMUKI_SOURCE_DIR}"
    if [[ "${OMOMUKI_DEV:-0}" == "1" ]]; then
      "$pip" install -e "${OMOMUKI_SOURCE_DIR}[dev]"
    else
      "$pip" install -e "${OMOMUKI_SOURCE_DIR}"
    fi
  else
    need_cmd git
    local spec
    if [[ "${OMOMUKI_DEV:-0}" == "1" ]]; then
      spec="omomuki[dev] @ git+${OMOMUKI_GIT_URL}@${OMOMUKI_REF}"
    else
      spec="omomuki @ git+${OMOMUKI_GIT_URL}@${OMOMUKI_REF}"
    fi
    info "Installing ${OMOMUKI_REPO}@${OMOMUKI_REF}"
    "$pip" install "$spec"
  fi
}

install_wrapper() {
  mkdir -p "$OMOMUKI_BIN_DIR"
  cat >"$WRAPPER" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "${VENV_DIR}/bin/omomuki" "\$@"
EOF
  chmod +x "$WRAPPER"
  info "Installed wrapper: ${WRAPPER}"
}

path_hint() {
  case ":$PATH:" in
    *":${OMOMUKI_BIN_DIR}:"*) ;;
    *)
      warn "${OMOMUKI_BIN_DIR} is not on PATH."
      printf 'Add to your shell profile:\n  export PATH="%s:$PATH"\n' "$OMOMUKI_BIN_DIR"
      ;;
  esac
}

maybe_init() {
  if [[ "${OMOMUKI_SKIP_INIT:-0}" == "1" ]]; then
    return 0
  fi
  if [[ -f "${HOME}/.omomuki/profiles/default/omomuki.profile.yaml" ]]; then
    info "Profile store already exists; skipping omomuki init"
    return 0
  fi
  info "Initializing profile store (~/.omomuki)"
  "$WRAPPER" init
}

confirm() {
  if [[ "${OMOMUKI_YES:-0}" == "1" ]]; then
    return 0
  fi
  if [[ ! -t 0 ]]; then
    OMOMUKI_YES=1
    return 0
  fi
  printf 'Install Omomuki to %s? [y/N] ' "$OMOMUKI_INSTALL_DIR"
  read -r reply
  case "$reply" in
    y | Y | yes | YES) ;;
    *) die "Aborted." ;;
  esac
}

main() {
  detect_platform
  info "Platform: ${PLATFORM}"
  confirm
  local py
  py="$(find_python)"
  info "Using Python: $("$py" --version)"
  mkdir -p "$OMOMUKI_INSTALL_DIR"
  ensure_venv "$py"
  install_package
  install_wrapper
  path_hint
  maybe_init
  info "Done. Run: omomuki --version"
  if [[ "$PLATFORM" == "macos" ]]; then
    info "Bridge daemon (optional): see docs/install.md#bridge-daemon"
  fi
}

main "$@"
