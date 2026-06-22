# Sayane CLI Command Reference

Target: Sayane `1.0.5` (PyPI) / v1.0 Context Acceptance architecture.

Phase 6–17 commands for context acceptance and verifiable handoff.

---

## Review

```bash
# Show candidate detail with flags, warnings, transfer path, lineage
sayane review show <candidate-id>

# List decisions with optional filter
sayane review list --filter semantic_overlap
sayane review list --filter boundary_sensitive

# Show overlap group detail
sayane review overlap <overlap-id>

# Show decision diff (original vs applied)
sayane review diff <candidate-id>
```

## Audit

```bash
# List all audit records
sayane audit list

# Query by candidate
sayane audit by-candidate <candidate-id>

# Query by term
sayane audit by-term RDE

# Export audit trail
sayane audit export --format markdown -o report.md
sayane audit export --format json -o report.json
sayane audit export --format jsonl --term RDE
sayane audit export --format markdown --redact -o report.md
```

## Bundle / Provenance

```bash
# Verify a bundle's content hash and signature
sayane bundle-verify <bundle>
```

## Policy

```bash
# List built-in policies
sayane policy list

# Show a built-in policy
sayane policy show strict

# Validate a custom policy file
sayane policy validate --file examples/policies/ci-strict.yaml

# Show effective policy from a custom file
sayane policy show --file examples/policies/ci-strict.yaml
```

## Signing

```bash
# Generate an Ed25519 keypair
sayane key generate

# List keys
sayane key list

# Sign a bundle
sayane sign bundle.yml
sayane sign bundle.yml --key <key-id>
```

## Package

```bash
# Create a signed export package
sayane package create \
  --bundle bundle.yml \
  --audit-export audit.json \
  --transfer-report report.json \
  --policy-file policy.yaml \
  -o pkg/

# Inspect a package
sayane package inspect pkg/

# Verify a package (hashes, signatures, manifest)
sayane package verify pkg/
```

## Transfer Report

```bash
# Generate a cross-LLM transfer regression report
sayane transfer-report --format markdown -o report.md
sayane transfer-report --format json -o report.json
```

## Import

```bash
# Import a context bundle as reviewable candidates
sayane import-bundle bundle.yml --profile examples/profiles/minimal.yaml
```

## Resident Daemon

```bash
# Preview runtime initialization
sayane app daemon-runtime-init --json

# Initialize runtime directories
sayane app daemon-runtime-init --apply --json

# Start the local-only resident daemon MVP
sayane app daemon-start --json
sayane app daemon-start --include-event-record --json

# Inspect current daemon status
sayane app daemon-status --json

# Stop or restart the daemon
sayane app daemon-stop --json
sayane app daemon-restart --json

# Remove an explicitly reviewed stale runtime file
sayane app daemon-cleanup-preview --json
sayane app daemon-cleanup-apply \
  --remove pid_file \
  --confirm-operation-id cleanup-preview-... \
  --confirm-preview-hash ... \
  --json

# Create an explicitly reviewed runtime directory target
sayane app daemon-repair-preview --json
sayane app daemon-repair-apply \
  --create runtime_root \
  --confirm-operation-id repair-preview-... \
  --confirm-preview-hash ... \
  --json

# Preview conservative daemon/API readiness observations
sayane app daemon-readiness-diagnostic \
  --operation-class bridge_health \
  --json

# Preview current operator-facing packaging and supervision boundary
sayane app daemon-packaging-status --json

# Preview cross-platform service target status for macOS, Linux, and Windows
sayane app daemon-service-targets-status --json

# Preview current service/control boundary for allowed CLI control and deferred service commands
sayane app daemon-service-control-boundary --json

# Preview current supervision UX boundary for passive visibility and CLI recovery
sayane app daemon-supervision-status --json

# Preview current recovery flow and consent boundary
sayane app daemon-recovery-consent-status --json

# Preview and write a macOS LaunchAgent plist for the resident daemon line
sayane app daemon-launchagent-preview --json
sayane app daemon-launchagent-apply \
  --operation-id launchagent-... \
  --confirm-operation-id launchagent-... \
  --confirm-preview-hash ... \
  --json
sayane app daemon-launchagent-status --json

# Explicitly bootstrap, bootout, or kickstart the reviewed macOS LaunchAgent
sayane app daemon-launchagent-bootstrap --json
sayane app daemon-launchagent-bootout --json
sayane app daemon-launchagent-kickstart --json

# Preview conservative daemon identity-proof observations
sayane app daemon-identity-proof --json

# Preview conservative daemon readiness-proof observations
sayane app daemon-readiness-proof \
  --operation-class bridge_health \
  --json

# Preview conservative daemon API-readiness-proof observations
sayane app daemon-api-readiness-proof \
  --operation-class bridge_health \
  --json

# Preview an aggregated daemon proof diagnostics snapshot
sayane app daemon-proof-diagnostics \
  --operation-class bridge_health \
  --json

# Preview a future-UI-oriented daemon overview payload
sayane app daemon-overview --json

# Preview an aggregate app overview payload
sayane app overview --json

# Show app-facing UI handoff contract metadata
sayane app contract --json
```

## Bridge App Surfaces

```bash
# Read aggregate app-facing preview state
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:38741/app/overview

# Read app-facing UI handoff contract metadata
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:38741/app/contract

# Open the local HTML bootstrap UI
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:38741/app/ui

# After bootstrap, browser-driven follow-up UI activity uses the dedicated local UI session
# rather than resupplying the raw bearer on every request

# Capture clipboard text into the resident candidate flow
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"content":"important_terms:\n  - \"Sayane\""}' \
  http://127.0.0.1:38741/app/capture-clipboard

# Read and act on app-facing review candidates
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:38741/app/candidates
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:38741/app/candidates/<id>
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:38741/app/candidates/<id>/diff
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"level":1}' http://127.0.0.1:38741/app/candidates/<id>/evaluate
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"edited_text":"Revised text","target_section":"knowledge.concepts"}' \
  http://127.0.0.1:38741/app/candidates/<id>/revise
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"force_critical":false}' http://127.0.0.1:38741/app/candidates/<id>/approve
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"reason":"not needed"}' http://127.0.0.1:38741/app/candidates/<id>/reject
```
