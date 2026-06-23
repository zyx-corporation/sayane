#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PACKAGE_PATH="$ROOT/macos/SayaneApp"

cd "$ROOT"
./scripts/run-app-local.sh --no-open
open "$PACKAGE_PATH/Package.swift"

echo "Opened Swift package in Xcode: $PACKAGE_PATH/Package.swift"
echo "Run the SayaneApp executable target from Xcode."
