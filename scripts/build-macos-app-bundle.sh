#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PACKAGE_PATH="${ROOT}/macos/SayaneApp"
RESOURCE_DIR="${PACKAGE_PATH}/Resources"
APP_NAME="${SAYANE_MACOS_APP_NAME:-SayaneApp}"
APP_BUNDLE_ID="${SAYANE_MACOS_APP_BUNDLE_ID:-io.sayane.app}"
APP_VERSION="${SAYANE_MACOS_APP_VERSION:-$(python3 - <<'PY'
from pathlib import Path
import re

content = Path("pyproject.toml").read_text(encoding="utf-8")
match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
print(match.group(1) if match else "0.0.0")
PY
)}"
APP_SHORT_VERSION="${SAYANE_MACOS_APP_SHORT_VERSION:-${APP_VERSION}}"
APP_BUNDLE_VERSION="${SAYANE_MACOS_APP_BUNDLE_VERSION:-$(python3 - <<'PY'
from pathlib import Path
import re

content = Path("pyproject.toml").read_text(encoding="utf-8")
match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
version = match.group(1) if match else "0.0.0"
numeric = re.match(r'^(\d+)\.(\d+)\.(\d+)', version)
if numeric:
    print(".".join(numeric.groups()))
else:
    digits = re.findall(r'\d+', version)
    print(".".join(digits[:3]) if digits else "0.0.0")
PY
)}"
OUTPUT_DIR="${SAYANE_MACOS_APP_OUTPUT_DIR:-${ROOT}/dist/macos}"
CONFIGURATION="release"
RUN_BUILD=1
CREATE_ZIP=0
CREATE_CHECKSUMS=1

info() { printf '==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --debug            Build a debug bundle instead of release
  --no-build         Reuse the existing Swift build output
  --zip              Also create a zip archive next to the .app bundle
  --no-checksums     Skip checksum and manifest generation
  --output-dir PATH  Override the output directory
  -h, --help         Show this help

Environment:
  SAYANE_MACOS_APP_NAME
  SAYANE_MACOS_APP_BUNDLE_ID
  SAYANE_MACOS_APP_VERSION
  SAYANE_MACOS_APP_SHORT_VERSION
  SAYANE_MACOS_APP_OUTPUT_DIR
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --debug)
      CONFIGURATION="debug"
      ;;
    --no-build)
      RUN_BUILD=0
      ;;
    --zip)
      CREATE_ZIP=1
      ;;
    --no-checksums)
      CREATE_CHECKSUMS=0
      ;;
    --output-dir)
      shift
      [[ $# -gt 0 ]] || die "--output-dir requires a path"
      OUTPUT_DIR="$1"
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

build_if_needed() {
  [[ "${RUN_BUILD}" == "1" ]] || return 0
  info "Building ${APP_NAME} (${CONFIGURATION})"
  swift build --package-path "${PACKAGE_PATH}" -c "${CONFIGURATION}"
}

resolve_binary_path() {
  local bin_dir
  bin_dir="$(swift build --package-path "${PACKAGE_PATH}" -c "${CONFIGURATION}" --show-bin-path)"
  EXECUTABLE_PATH="${bin_dir}/${APP_NAME}"
  [[ -x "${EXECUTABLE_PATH}" ]] || die "Missing executable: ${EXECUTABLE_PATH}"
}

create_bundle() {
  local bundle_dir macos_dir resources_dir plist_path
  bundle_dir="${OUTPUT_DIR}/${APP_NAME}.app"
  macos_dir="${bundle_dir}/Contents/MacOS"
  resources_dir="${bundle_dir}/Contents/Resources"
  plist_path="${bundle_dir}/Contents/Info.plist"

  info "Creating bundle at ${bundle_dir}"
  rm -rf "${bundle_dir}"
  mkdir -p "${macos_dir}" "${resources_dir}"
  cp "${EXECUTABLE_PATH}" "${macos_dir}/${APP_NAME}"
  chmod +x "${macos_dir}/${APP_NAME}"
  if [[ -d "${RESOURCE_DIR}" ]]; then
    ditto "${RESOURCE_DIR}" "${resources_dir}"
    find "${resources_dir}" -type f -name '*.sh' -exec chmod +x {} +
  fi
  cat > "${resources_dir}/runtime-env.sh" <<EOF
#!/usr/bin/env bash
export SAYANE_DEFAULT_REPO_ROOT='${ROOT}'
EOF
  chmod +x "${resources_dir}/runtime-env.sh"
  codesign --remove-signature "${macos_dir}/${APP_NAME}" >/dev/null 2>&1 || true
  cat > "${plist_path}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleExecutable</key>
  <string>${APP_NAME}</string>
  <key>CFBundleIdentifier</key>
  <string>${APP_BUNDLE_ID}</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>${APP_NAME}</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleSupportedPlatforms</key>
  <array>
    <string>MacOSX</string>
  </array>
  <key>CFBundleShortVersionString</key>
  <string>${APP_SHORT_VERSION}</string>
  <key>CFBundleVersion</key>
  <string>${APP_BUNDLE_VERSION}</string>
  <key>LSMinimumSystemVersion</key>
  <string>14.0</string>
  <key>LSRequiresNativeExecution</key>
  <true/>
  <key>NSPrincipalClass</key>
  <string>NSApplication</string>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
EOF
  printf 'APPL????' > "${bundle_dir}/Contents/PkgInfo"
}

create_zip_if_needed() {
  [[ "${CREATE_ZIP}" == "1" ]] || return 0
  local zip_path
  zip_path="${OUTPUT_DIR}/${APP_NAME}-${APP_VERSION}-macos-${CONFIGURATION}.zip"
  info "Creating zip archive at ${zip_path}"
  rm -f "${zip_path}"
  ditto -c -k --sequesterRsrc --keepParent "${OUTPUT_DIR}/${APP_NAME}.app" "${zip_path}"
}

create_release_metadata() {
  [[ "${CREATE_CHECKSUMS}" == "1" ]] || return 0
  local zip_path latest_zip_path checksum_path manifest_path executable_rel
  zip_path="${OUTPUT_DIR}/${APP_NAME}-${APP_VERSION}-macos-${CONFIGURATION}.zip"
  latest_zip_path="${OUTPUT_DIR}/${APP_NAME}-latest-macos-${CONFIGURATION}.zip"
  checksum_path="${OUTPUT_DIR}/${APP_NAME}-${APP_VERSION}-macos-${CONFIGURATION}.sha256"
  manifest_path="${OUTPUT_DIR}/${APP_NAME}-${APP_VERSION}-macos-${CONFIGURATION}.manifest.txt"
  executable_rel="${APP_NAME}.app/Contents/MacOS/${APP_NAME}"

  if [[ -f "${zip_path}" ]]; then
    cp -f "${zip_path}" "${latest_zip_path}"
  fi

  info "Writing release metadata"
  {
    (cd "${OUTPUT_DIR}" && shasum -a 256 "${executable_rel}")
    if [[ -f "${zip_path}" ]]; then
      shasum -a 256 "${zip_path}"
      shasum -a 256 "${latest_zip_path}"
    fi
  } > "${checksum_path}"

  cat > "${manifest_path}" <<EOF
app_name=${APP_NAME}
version=${APP_VERSION}
bundle_version=${APP_BUNDLE_VERSION}
configuration=${CONFIGURATION}
bundle_path=${OUTPUT_DIR}/${APP_NAME}.app
bundle_executable=${OUTPUT_DIR}/${executable_rel}
bundle_resources=${OUTPUT_DIR}/${APP_NAME}.app/Contents/Resources
zip_path=${zip_path}
latest_zip_path=${latest_zip_path}
checksum_file=${checksum_path}
EOF
}

print_summary() {
  cat <<EOF

Bundle created:
  App: ${OUTPUT_DIR}/${APP_NAME}.app
  Executable: ${EXECUTABLE_PATH}
  Version: ${APP_VERSION}
  Bundle Version: ${APP_BUNDLE_VERSION}
  Configuration: ${CONFIGURATION}

Next steps:
  open "${OUTPUT_DIR}/${APP_NAME}.app"
  bash "${ROOT}/scripts/install-macos-app.sh" --no-build
EOF
  if [[ "${CREATE_ZIP}" == "1" ]]; then
    printf '  ditto archive: %s/%s-%s-macos-%s.zip\n' "${OUTPUT_DIR}" "${APP_NAME}" "${APP_VERSION}" "${CONFIGURATION}"
  fi
}

main() {
  mkdir -p "${OUTPUT_DIR}"
  build_if_needed
  resolve_binary_path
  create_bundle
  create_zip_if_needed
  create_release_metadata
  print_summary
}

main "$@"
