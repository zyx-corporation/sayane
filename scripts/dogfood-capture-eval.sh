#!/usr/bin/env bash
# Dogfood: capture → evaluate (level 1) → diff → optional approve
set -euo pipefail

BRIDGE_URL="${OMOMUKI_BRIDGE_URL:-http://127.0.0.1:38741}"
TOKEN_FILE="${OMOMUKI_BRIDGE_TOKEN_FILE:-$HOME/.omomuki/bridge.token}"
LEVEL="${1:-1}"
APPROVE="${2:-}"
CONTENT="${OMOMUKI_DOGFOOD_CONTENT:-Explicit uncertainty and local-first context portability.}"

if [[ ! -f "$TOKEN_FILE" ]]; then
  echo "Missing token: $TOKEN_FILE (run: omomuki serve)" >&2
  exit 1
fi

TOKEN=$(cat "$TOKEN_FILE")
AUTH="Authorization: Bearer $TOKEN"
BODY=$(CONTENT="$CONTENT" python3 -c 'import json,os; print(json.dumps({"content":os.environ["CONTENT"],"source":"dogfood-script"}))')

CAP=$(curl -sf -X POST -H "$AUTH" -H "Content-Type: application/json" -d "$BODY" "$BRIDGE_URL/capture")
CID=$(echo "$CAP" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Captured: $CID"

EVAL=$(curl -sf -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"level\":$LEVEL}" "$BRIDGE_URL/candidates/$CID/evaluate")
echo "RDE: $(echo "$EVAL" | python3 -c "import sys,json; print(json.load(sys.stdin)['evaluation']['rde_class'])")"

echo "--- diff ---"
curl -sf -H "$AUTH" "$BRIDGE_URL/candidates/$CID/diff" | python3 -m json.tool

if [[ "$APPROVE" == "approve" ]]; then
  curl -sf -X POST -H "$AUTH" -H "Content-Type: application/json" \
    -d '{"force_critical":false}' "$BRIDGE_URL/candidates/$CID/approve" | python3 -m json.tool
  echo "Approved."
fi
