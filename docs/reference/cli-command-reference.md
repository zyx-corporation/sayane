# Sayane CLI Command Reference

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
