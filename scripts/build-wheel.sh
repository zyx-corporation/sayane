#!/usr/bin/env bash
# Build and verify sayane sdist/wheel locally.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CHECK_VENV="${ROOT}/.tmp-package-check-venv"

cleanup() {
  rm -rf "$CHECK_VENV"
}

trap cleanup EXIT

python3 -m pip install -q build
rm -rf dist build
python3 -m build
python3 -m venv "$CHECK_VENV"
"$CHECK_VENV/bin/python" -m pip install -q --upgrade pip setuptools wheel
"$CHECK_VENV/bin/python" -m pip install -q \
  "markdown-it-py>=3" \
  "pkginfo>=1.10" \
  "mdurl>=0.1"
"$CHECK_VENV/bin/python" - <<'PY'
from pathlib import Path

from markdown_it import MarkdownIt
import pkginfo

root = Path.cwd()
readme = (root / "README.md").read_text(encoding="utf-8")
rendered = MarkdownIt("commonmark", {"html": True, "linkify": True}).render(readme)
if not rendered:
    raise SystemExit("README.md did not render successfully as package metadata")

artifacts = sorted((root / "dist").glob("*"))
if not artifacts:
    raise SystemExit("No dist artifacts found")

for artifact in artifacts:
    if artifact.suffix == ".whl":
        meta = pkginfo.Wheel(str(artifact))
    elif artifact.suffix == ".gz":
        meta = pkginfo.SDist(str(artifact))
    else:
        continue
    if not meta.name or not meta.version or not meta.summary:
        raise SystemExit(f"Missing package metadata fields in {artifact.name}")
    print(f"checked {artifact.name}: {meta.name} {meta.version}")
PY
echo "Built:"
ls -la dist/
