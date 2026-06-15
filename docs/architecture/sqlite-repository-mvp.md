# SQLite Repository MVP

This document records the ADR 0007 Phase 3 SQLite MVP boundary.

## Status

Initial MVP path is implemented and covered by tests.

The MVP uses the existing SQLite-backed Local Vault runtime rather than introducing a direct SQLite repository dependency from CLI, Bridge, MCP, or domain code.

## Files

```text
src/sayane/vault/sqlite_store.py
src/sayane/vault/sqlite_schema.py
src/sayane/vault/sqlite_runtime.py
src/sayane/storage/vault_bundle.py
src/sayane/storage/vault_candidates.py
src/sayane/storage/vault_review_decisions.py
src/sayane/storage/vault_lineage.py
```

Test coverage:

```text
tests/test_sqlite_vault_store.py
tests/test_review_decision_repository_seam.py
tests/test_repository_contracts.py
```

## Boundary

The SQLite MVP follows this shape:

```text
MCP / CLI / Bridge / future App
  -> review decision seam / usecases
    -> ReviewDecisionRepository contract
      -> VaultReviewDecisionStore
        -> SQLiteVaultStore
          -> encrypted_records table
```

Entrypoints do not import `sqlite3` or call `SQLiteVaultStore` directly.

MCP receives review decisions through `load_review_decisions()` and still applies the exposure guard in `mcp_context.py`.

## Implemented Guarantees

The current tests prove:

- SQLite vault records round-trip through the VaultStore contract.
- Stored SQLite records do not persist plaintext in the `ciphertext` column.
- SQLite schema validation passes for the current encrypted-record schema.
- SQLite-backed repository bundles can store Candidate, ReviewDecision, and Lineage records.
- Rebuilding a SQLite runtime over the same file reloads Candidate, ReviewDecision, and Lineage records.
- `load_review_decisions()` can read from a repository-backed ReviewDecisionRepository.
- MCP compiled context can consume SQLite-backed review decisions through the repository seam.
- `save_decision()` can write through a configured SQLite-backed ReviewDecisionRepository.

## Non-goals

This MVP does not yet provide:

- production OS keychain integration
- commercial encrypted SQLite backend selection
- migration CLI
- resident app default runtime selection
- automatic CLI/Bridge/MCP repository binding
- Obsidian sync or conflict resolution
- cloud sync

## Design Notes

SQLite is not the meaning source.

The Local Vault remains the human-readable and portable context substrate.

SQLite coordinates durable application state such as Candidate, ReviewDecision, and Lineage records.

The test runtime uses test-only crypto and keychain providers. It must not become the production default.

## Next Step

The next phase should prepare resident service wiring:

```text
sayane app serve / sayane serve
  -> explicit runtime builder
  -> repository bundle
  -> local capability boundary
  -> clipboard capture as Candidate
```

Until that wiring exists, SQLite-backed persistence is available as an explicit runtime/test seam rather than a default application runtime.
