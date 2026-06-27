# ADR 0017: Transitional FileSystem Working Stores Remain Debug and Legacy Compatibility Only After P2

## Status

Accepted

## Date

2026-06-28

## Context

Issue `P2 Sensitive working-store migration` moved the active `Candidate`,
`ReviewDecision`, and `Lineage` paths for resident app, legacy bridge, and
explicit vault-aware CLI flows onto vault-backed repositories.

That migration closes the main production-completion risk that remained after
P1: app-facing high-sensitivity working state no longer needs to land in
plaintext-ish FileSystem working stores when an explicit Local Vault runtime is
active.

However, the repository still contains legacy FileSystem working-store paths.
Those paths remain useful for:

1. debug and smoke flows that intentionally avoid Local Vault setup
2. import / legacy / fixture-oriented compatibility flows
3. fail-closed local development where vault runtime selection is not explicit

The project needs one explicit post-P2 boundary so future work does not slowly
re-promote those FileSystem stores back into operator-default persistence.

## Decision

After P2, transitional FileSystem working stores remain in the Community
edition only as:

1. debug-only local working paths
2. legacy compatibility paths
3. import / fixture / smoke-test support paths

They are **not**:

1. the preferred operator path
2. the default persistence target when an explicit Local Vault runtime is active
3. a valid destination for new app-facing high-sensitivity features
4. a substitute for the Local Vault security model

More concretely:

- resident app, native macOS app, legacy bridge, and explicit vault-aware CLI
  flows must keep preferring repository-backed persistence whenever
  `BridgeConfig.repositories` is present
- new high-sensitivity app-facing work must extend the repository / vault path,
  not add new FileSystem working-store dependencies
- FileSystem working stores may remain for non-vault debug, smoke, fixture, and
  backward-compatibility flows until later retirement work is scheduled
- retirement or further narrowing of `/app/ui*` and of legacy FileSystem paths
  remains separate work, not an implicit side effect of this ADR

## Consequences

### Positive

- P2 now has a clear closure statement instead of an open-ended “temporary for
  now” boundary
- future storage, integration, and packaging work can assume Local Vault is the
  growth path for sensitive working state
- debug and smoke flows stay available without pretending to be the production
  security posture

### Negative

- the codebase still carries dual persistence paths for a while
- docs and tests must keep distinguishing debug compatibility from supported
  sensitive-state persistence

## Boundaries

This decision does not:

- make Local Vault an implicit production-default runtime selection
- remove FileSystem working stores immediately
- retire `/app/ui*` by itself
- define the external sync / Obsidian / Git redesign
- define Linux or Windows packaging completion

## Related

- `docs/adr/0001-local-vault-key-management.md`
- `docs/adr/0007-resident-app-local-vault-foundation.md`
- `docs/adr/0014-app-ui-debug-only-compatibility-surface.md`
- `docs/adr/0016-mvp-native-first-operator-boundary-closure.md`
- `docs/release/v1.0.68-p2-vault-aware-resident-working-store-release-note.md`
