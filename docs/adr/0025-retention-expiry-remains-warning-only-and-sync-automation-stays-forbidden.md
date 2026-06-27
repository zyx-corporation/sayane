# ADR 0025: Retention expiry remains warning-only and sync automation stays forbidden

## Status

Accepted — 2026-06-28

## Context

P3 now has a supported reviewable external package format, explicit retention
classes, preview-only import, and permanent legacy compatibility paths.

Two final boundary questions remained:

1. whether retention expiry should immediately block package preview/import
2. whether any package-external automation should be treated as an allowed
   future default in the Community path

## Decision

### 1. Retention expiry remains warning-only

For the current Community contract, package retention expiry does **not** block
preview or verification. It remains an operator-facing warning:

- `retention_expiry_mode = warning_only`

This keeps reviewability visible while avoiding a false sense that age alone is
enough to prove a package unsafe or unusable.

### 2. Sync automation remains forbidden outside the package contract

The following automation patterns remain forbidden in the supported path:

- `automatic_external_sync_promotion`
- `automatic_bidirectional_sync`
- `implicit_filesystem_git_auto_commit_as_primary_sync`

These are distinct from manual compatibility commands. They are forbidden as
default or background operator flows because they blur the Local Vault boundary.

## Consequences

Positive:

- package review remains available even when timing guidance is exceeded
- Community behavior stays compatible with manual operator recovery flows
- automatic sync semantics are clearly excluded from the supported path

Negative:

- stale packages require operator judgment instead of hard-stop enforcement
- future automation requires a fresh explicit design decision

## Related

- `docs/adr/0022-vault-aware-external-packages-are-the-supported-reviewable-exchange-format.md`
- `docs/adr/0024-preview-only-import-package-contract-and-permanent-legacy-external-workflows.md`
- `docs/storage-manual.md`
