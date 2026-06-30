#!/usr/bin/env bash
# Sayane installer for macOS and Linux.
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
#   SAYANE_REF=v0.5.9 bash scripts/install.sh
#
# Environment:
#   SAYANE_REPO          GitHub repo (default: zyx-corporation/sayane)
#   SAYANE_REF           Git ref to install (default: main)
#   SAYANE_INSTALL_SOURCE  auto|pypi|git (default: auto)
#   SAYANE_PYPI_SPEC     PyPI spec to install in pypi/auto mode (default: sayane)
#   SAYANE_INSTALL_DIR   Install root (default: ~/.local/share/sayane)
#   SAYANE_BIN_DIR       Wrapper scripts (default: ~/.local/bin)
#   SAYANE_SOURCE_DIR    Local checkout; pip install -e instead of git URL (CI/dev)
#   SAYANE_DEV           Set to 1 to install [dev] extras
#   SAYANE_SKIP_INIT     Set to 1 to skip `sayane init`
#   SAYANE_YES           Set to 1 to skip confirmation prompts
#   SAYANE_PRINT_QUICKSTART  Set to 1 to print the shortest next-step commands at the end

set -euo pipefail

SAYANE_REPO="${SAYANE_REPO:-zyx-corporation/sayane}"
SAYANE_REF_DEFAULT="main"
if [[ -n "${SAYANE_REF+x}" ]]; then
  SAYANE_REF_IS_EXPLICIT=1
  SAYANE_REF="${SAYANE_REF}"
else
  SAYANE_REF_IS_EXPLICIT=0
  SAYANE_REF="${SAYANE_REF_DEFAULT}"
fi
SAYANE_INSTALL_SOURCE="${SAYANE_INSTALL_SOURCE:-auto}"
SAYANE_PYPI_SPEC="${SAYANE_PYPI_SPEC:-sayane}"
SAYANE_INSTALL_DIR="${SAYANE_INSTALL_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/sayane}"
SAYANE_BIN_DIR="${SAYANE_BIN_DIR:-${XDG_BIN_HOME:-$HOME/.local/bin}}"
SAYANE_GIT_URL="https://github.com/${SAYANE_REPO}.git"
SAYANE_DOCS_BASE_URL="https://github.com/${SAYANE_REPO}/blob/${SAYANE_REF}/docs"
VENV_DIR="${SAYANE_INSTALL_DIR}/venv"
WRAPPER="${SAYANE_BIN_DIR}/sayane"

info() { printf '==> %s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

post_install_hints() {
  info "Primary install path complete: curl+bash -> CLI / Bridge runtime"
  info "Verify: ${WRAPPER} --version"
  info "Start Bridge when needed: ${WRAPPER} serve"
  info "Quickstart: ${SAYANE_DOCS_BASE_URL}/release/v1.0.76-curl-bash-operator-quickstart.md"
  if [[ "${SAYANE_PRINT_QUICKSTART:-0}" == "1" ]]; then
    printf '\nQuickstart commands:\n'
    printf '  %s --version\n' "${WRAPPER}"
    printf '  %s serve\n' "${WRAPPER}"
    if [[ "${PLATFORM}" == "macos" ]]; then
      printf '  # optional native shell from a repo checkout:\n'
      printf '  ./scripts/run-macos-app-preview.sh\n'
    fi
  fi
  if [[ "${PLATFORM}" == "macos" ]]; then
    info "Optional native macOS app is a secondary path. Use the release-zip helper or build/install it from a repo checkout when needed."
    info "Install guide: ${SAYANE_DOCS_BASE_URL}/install.md"
  fi
}

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

normalized_install_source() {
  case "${SAYANE_INSTALL_SOURCE}" in
    auto|pypi|git)
      printf '%s\n' "${SAYANE_INSTALL_SOURCE}"
      ;;
    *)
      die "Unsupported SAYANE_INSTALL_SOURCE: ${SAYANE_INSTALL_SOURCE} (expected: auto, pypi, git)"
      ;;
  esac
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
  local install_source spec
  info "Upgrading pip"
  "$pip" install --upgrade pip wheel >/dev/null

  if [[ -n "${SAYANE_SOURCE_DIR:-}" ]]; then
    info "Installing from local source: ${SAYANE_SOURCE_DIR}"
    if [[ "${SAYANE_DEV:-0}" == "1" ]]; then
      "$pip" install -e "${SAYANE_SOURCE_DIR}[dev]"
    else
      "$pip" install -e "${SAYANE_SOURCE_DIR}"
    fi
    return 0
  fi

  install_source="$(normalized_install_source)"
  if [[ "${install_source}" == "auto" && "${SAYANE_REF_IS_EXPLICIT}" == "1" ]]; then
    install_source="git"
  fi

  if [[ "${install_source}" == "pypi" || "${install_source}" == "auto" ]]; then
    if [[ "${SAYANE_DEV:-0}" == "1" ]]; then
      spec="${SAYANE_PYPI_SPEC}[dev]"
    else
      spec="${SAYANE_PYPI_SPEC}"
    fi
    info "Installing ${spec} from PyPI"
    if "$pip" install "${spec}"; then
      return 0
    fi
    if [[ "${install_source}" == "pypi" ]]; then
      die "PyPI install failed for ${spec}"
    fi
    warn "PyPI install failed; falling back to git source for ${SAYANE_REPO}@${SAYANE_REF}"
  fi

  if [[ "${install_source}" == "git" || "${install_source}" == "auto" ]]; then
    need_cmd git
    if [[ "${SAYANE_DEV:-0}" == "1" ]]; then
      spec="sayane[dev] @ git+${SAYANE_GIT_URL}@${SAYANE_REF}"
    else
      spec="sayane @ git+${SAYANE_GIT_URL}@${SAYANE_REF}"
    fi
    info "Installing ${SAYANE_REPO}@${SAYANE_REF} from git"
    "$pip" install "$spec"
  else
    die "Unsupported install source resolution: ${install_source}"
  fi
}

install_wrapper() {
  mkdir -p "$SAYANE_BIN_DIR"
  cat >"$WRAPPER" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "${VENV_DIR}/bin/sayane" "\$@"
EOF
  chmod +x "$WRAPPER"
  info "Installed wrapper: ${WRAPPER}"
}

path_hint() {
  case ":$PATH:" in
    *":${SAYANE_BIN_DIR}:"*) ;;
    *)
      warn "${SAYANE_BIN_DIR} is not on PATH."
      printf 'Add to your shell profile:\n  export PATH="%s:$PATH"\n' "$SAYANE_BIN_DIR"
      ;;
  esac
}

maybe_init() {
  if [[ "${SAYANE_SKIP_INIT:-0}" == "1" ]]; then
    return 0
  fi
  if [[ -f "${HOME}/.sayane/profiles/default/sayane.profile.yaml" ]]; then
    info "Profile store already exists; skipping sayane init"
    return 0
  fi
  info "Initializing profile store (~/.sayane)"
  "$WRAPPER" init
}

confirm() {
  if [[ "${SAYANE_YES:-0}" == "1" ]]; then
    return 0
  fi
  if [[ ! -t 0 ]]; then
    SAYANE_YES=1
    return 0
  fi
  printf 'Install Sayane to %s? [y/N] ' "$SAYANE_INSTALL_DIR"
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
  mkdir -p "$SAYANE_INSTALL_DIR"
  ensure_venv "$py"
  install_package
  install_wrapper
  path_hint
  maybe_init
  info "Done. Run: sayane --version"
  if [[ "$PLATFORM" == "macos" ]]; then
    info "Bridge daemon (optional): see docs/install.md#bridge-daemon"
  fi
  post_install_hints
}

main "$@"
