# ADR 0001: Local Vault Key Management for Sayane App

## Status

Proposed

## Context

Sayane is moving from a CLI/Bridge-centered workflow toward a resident local application with integrated UI, MCP, Bridge, and clipboard capture.

This changes the security model. Local-first does not mean local storage is safe by default. Sayane local storage may contain Profile, Project Context, Candidate records, Review Decisions, Lineage, raw captures, cloud transfer logs, and MCP compiled context previews. These are not merely application settings; they may encode user intent, rejected thoughts, uncertainty, decision history, and high-sensitivity context.

The local store must therefore be treated as a protected vault.

Related design principles:

- Context Sovereignty: the user should control where context is stored and where it is sent.
- Least Context: only the minimum required context should be exposed to external tools or cloud AI providers.
- Candidate Boundary: LLM output must become a Candidate first, then be reviewed before reuse.
- Thought Firewall: Sayane should protect in-progress thoughts, not only completed documents.

## Decision

Sayane will use hierarchical key management with envelope encryption.

The system may have a master key, but the master key must not directly encrypt all application data.

Instead:

1. A platform-backed wrapping secret or Key Encryption Key (KEK) is protected by the OS secret store.
2. Data-class-specific Data Encryption Keys (DEKs) are wrapped by the KEK.
3. DEKs encrypt actual record content for each data class.
4. High-sensitivity data classes receive stricter unlock and timeout policy.

## Key hierarchy

```text
OS Secret Store / OS Authentication / optional passphrase
        │
        ▼
Master KEK / wrapping secret
        │
        ├── profile_dek
        ├── project_context_dek
        ├── candidate_dek
        ├── review_decision_dek
        ├── lineage_dek
        ├── raw_capture_dek
        ├── cloud_transfer_log_dek
        ├── mcp_preview_dek
        └── export_dek
```

The master KEK is used only to wrap and unwrap DEKs. It must not be used as a universal data encryption key.

## OS abstraction

Sayane must use a platform abstraction layer for OS-specific key handling.

Suggested interface:

```python
class PlatformKeychainProvider:
    def platform_name(self) -> str: ...
    def capabilities(self) -> KeychainCapabilities: ...
    def get_or_create_wrapping_secret(self, key_id: str) -> bytes: ...
    def unlock(self, purpose: str, scopes: list[str]) -> UnlockSession: ...
    def lock(self, session_id: str) -> None: ...
    def rotate_wrapping_secret(self, key_id: str) -> None: ...
```

Backends:

- macOS: Keychain / LocalAuthentication / Secure Enclave when available.
- Windows: DPAPI / Windows Hello / Credential Manager where appropriate.
- Linux desktop: Secret Service / libsecret / GNOME Keyring / KWallet when available.
- Headless Linux: explicit passphrase fallback, marked as lower assurance.
- Test: deterministic in-memory provider, never for production.

If no secure OS secret store is available, Sayane must not silently downgrade to plaintext production storage.

Allowed fallback:

- explicit passphrase-based local vault;
- lower-assurance warning;
- restricted access to sensitive and Deep Private scopes unless explicitly unlocked.

Forbidden fallback:

- plaintext master key in config;
- plaintext SQLite as production default;
- sharing UI unlock state with MCP / Bridge / Extension tokens.

## Unlock policy

A resident Sayane application must not keep keys unlocked indefinitely.

Unlock sessions must be explicit, scoped, and time-limited.

Suggested unlock levels:

| Level | Examples | Idle timeout | Absolute timeout |
| --- | --- | --- | --- |
| normal | Profile, Project Context | 15 min | 60 min |
| sensitive | Candidate Review, Lineage summary | 5 min | 15 min |
| deep_private | Deep Private / Layer 3 detail, raw captures, cloud transfer detail | 1-3 min | 5 min or per access |

Deep Private / Layer 3 context must require explicit unlock. It must not be opened merely because the general vault is unlocked.

UI unlock sessions must not be automatically inherited by MCP, Bridge, Chrome Extension, or other external tool tokens.

## Capability model

Key access must be combined with capability-based access control.

Examples:

- `capture:write`
- `candidate:read_metadata`
- `candidate:review`
- `profile:read`
- `lineage:read_summary`
- `lineage:read_detail`
- `raw_capture:read`
- `cloud_log:read`
- `mcp:compiled_context`
- `admin:export`

MCP access should normally be limited to `mcp:compiled_context` and must still pass MCP Context Exposure Policy guards.

Chrome Extension or clipboard capture flows must create Candidate records. They must not gain Profile read/write capability by default.

## Database storage model

Sayane may use SQLite for the local store, but production storage must be encryption-ready and should not be plaintext by default.

Preferred model:

1. DB-level encryption for broad at-rest protection.
2. Additional column/record-level envelope encryption for high-sensitivity content.

DB-level encryption alone is insufficient for data-class separation. Column/record-level encryption is needed for classes such as raw captures, Profile, Lineage detail, and cloud transfer logs.

Suggested keyring table:

```text
keyring
- key_id
- data_class
- wrapped_dek
- wrapping_key_id
- algorithm
- created_at
- rotated_at
- status
```

Suggested encrypted record fields:

```text
encrypted_records or encrypted columns
- record_id
- data_class
- key_id
- nonce
- ciphertext
- aad_json
- created_at
```

AAD (Additional Authenticated Data) should include non-secret metadata used for integrity binding, such as:

- profile_id
- project_id
- record_type
- schema_version
- key_id

This helps detect ciphertext substitution across records or data classes.

## Data-class boundaries

At minimum, separate DEKs should exist for:

- Profile
- Project Context
- Candidate
- Review Decision
- Lineage
- Raw Capture
- Cloud Transfer Log
- MCP Preview / Compiled Context Cache
- Export / Backup

Raw Capture, Lineage detail, and Deep Private context must be treated as especially sensitive.

Reject lineage may remain, but rejected content retention should be configurable. Raw captures should default to short retention unless explicitly promoted.

## Export and backup

Exports and backups must not bypass local vault protections.

- Plaintext export must require explicit user confirmation.
- Encrypted export should be the default.
- Export keys should be separate from local storage DEKs.
- Export events should be logged as audit metadata.

## Current implementation status

This ADR is partially implemented as an executable contract layer. The current implementation is not yet a production Local Vault, but it defines and tests the boundary that production implementations must satisfy.

Implemented contract layer:

- `src/sayane/vault/contracts.py`
  - `DataClass`
  - `SecretStoreAssurance`
  - `VaultStoreMode`
  - `PlatformKeychainProvider`
  - `UnlockSession`
  - `UnlockSessionManager`
  - `KeyManager`
  - `CryptoProvider`
  - `VaultStore`
  - `assert_vault_store_safe_for_production()`

Implemented session management:

- `src/sayane/vault/session.py`
  - `InMemoryUnlockSessionManager`

`InMemoryUnlockSessionManager` delegates key release to a `PlatformKeychainProvider`, tracks session metadata, enforces session existence, rejects expired sessions, checks scopes, and closes sessions through the keychain. It is currently used by `VaultRuntime`.

Implemented test-only infrastructure:

- `src/sayane/vault/test_store.py`
  - `TestOnlyKeychainProvider`
  - `InMemoryTestVaultStore`
  - `CryptoBackedInMemoryTestVaultStore`
- `src/sayane/vault/test_crypto.py`
  - `TestOnlyKeyManager`
  - `TestOnlyCryptoProvider`

These test-only components are not cryptographic protection. They exist only to exercise the contract shape, scope checks, AAD binding, DEK separation, rotation/destroy semantics, and repository adapter behavior.

Implemented Vault-backed repository adapters:

- `src/sayane/storage/vault_candidates.py`
  - `VaultCandidateStore`
- `src/sayane/storage/vault_review_decisions.py`
  - `VaultReviewDecisionStore`
- `src/sayane/storage/vault_lineage.py`
  - `VaultLineageStore`
- `src/sayane/storage/vault_bundle.py`
  - `VaultRepositoryBundle`
  - `build_vault_repository_bundle()`

Implemented guarded runtime construction:

- `src/sayane/vault/factory.py`
  - `VaultRuntime`
  - `build_test_vault_runtime()`
  - `open_vault_runtime()`

The runtime factory is intentionally fail-closed. Production and development Local Vault backends are not implemented yet, so `open_vault_runtime()` without `mode="test"` raises an error. Test-only components are available only through explicit `mode="test"` or `build_test_vault_runtime()` calls.

`VaultRuntime` now owns an `UnlockSessionManager`, so runtime callers can open, require, and close scoped sessions without directly sharing UI unlock state with external tools.

Implemented diagnostic entrypoint:

- `src/sayane/cli/vault_cmd.py`
  - `sayane vault status`
  - `sayane vault status --json`
  - `sayane vault status --test`
  - `sayane vault status --test --json`

The diagnostic command is non-destructive and does not expose plaintext records. By default it checks production mode and reports the production Local Vault backend as unavailable while it remains unimplemented. Test-only runtime is shown only when `--test` is explicitly provided, and its output is marked `production_ready: false` and `test_only: true`.

The current Vault adapters cover:

- Candidate records as `DataClass.CANDIDATE`
- ReviewDecision records as `DataClass.REVIEW_DECISION`
- Lineage records as `DataClass.LINEAGE`

Current AAD binding includes profile identity, record type, schema version, and record-specific identifiers such as candidate id, decision type, event id, operation, and node kind where applicable.

Current limitations:

- No production OS-backed keychain provider exists yet.
- No production cryptographic provider exists yet.
- No SQLite-backed encrypted persistent VaultStore exists yet.
- Test-only providers must not be selected by production defaults.
- Existing FileSystem stores remain transitional local working stores until the Local Vault backend is production-ready.

## CI enforcement

This ADR must be enforced by automated checks before Local Vault or persistent Candidate / ReviewDecision / Lineage storage becomes a default path.

Required CI checks:

- run storage backend tests;
- run storage security policy tests;
- run MCP context exposure tests;
- run Local Vault contract tests;
- run unlock session manager tests;
- run test-only keychain / crypto / vault store tests;
- run Vault-backed Candidate / ReviewDecision / Lineage adapter tests;
- run Vault runtime factory tests;
- run Vault diagnostic CLI tests;
- fail if filesystem storage enables implicit Git auto-commit by default;
- fail if Candidate / ReviewDecision / Lineage write paths bypass the storage security policy;
- fail if normal MCP context output exposes pending, rejected, or deferred Candidate content;
- fail if UI unlock state is treated as equivalent to MCP / Bridge / capture access;
- fail if production code stores a plaintext master key in config;
- fail if plaintext SQLite is introduced as a production default;
- fail if test-only vault providers become production defaults;
- fail if test-only vault runtime can be opened as production default;
- fail if `sayane vault status` opens test-only runtime without an explicit test flag.

Current targeted CI checks:

```bash
pytest tests/test_storage_backend.py
pytest tests/test_storage_security_policy.py
pytest tests/test_storage_write_policy.py
pytest tests/test_review_decision_store.py
pytest tests/test_vault_contracts.py
pytest tests/test_unlock_session_manager.py
pytest tests/test_vault_test_store.py
pytest tests/test_vault_test_crypto.py
pytest tests/test_vault_candidate_adapter.py
pytest tests/test_vault_review_decision_adapter.py
pytest tests/test_vault_lineage_adapter.py
pytest tests/test_vault_repository_bundle.py
pytest tests/test_vault_factory.py
pytest tests/test_vault_cli.py
pytest tests/test_mcp_context.py
```

Future CI targets, once production Local Vault modules exist:

```bash
pytest tests/test_vault_key_manager.py
pytest tests/test_platform_keychain_provider.py
pytest tests/test_local_vault_persistence.py
pytest tests/test_sqlite_vault_store.py
```

CI may use deterministic in-memory or test keychain providers, but those providers must be clearly marked as test-only and must not be selected by production defaults.

## Consequences

Benefits:

- Local-first storage becomes meaningfully protected.
- Key rotation is feasible because DEKs can be re-wrapped without re-encrypting all data.
- Data-class separation supports Least Context and Right to Fade.
- Deep Private / Layer 3 data receives stronger interaction friction.
- MCP, Bridge, UI, and CLI can share a common vault without sharing all permissions.
- Candidate / ReviewDecision / Lineage now have a clear migration seam from FileSystem local working stores to Local Vault repositories.
- Vault runtime construction now has a fail-closed seam that prevents test-only components from becoming production defaults.
- Unlock session management now has a runtime seam that separates keychain unlock, scoped session validation, and repository access.
- Vault diagnostics now expose runtime readiness without exposing plaintext or silently opening test-only storage.

Costs:

- More implementation complexity than plaintext SQLite.
- Search and indexing over encrypted content require careful design.
- Linux/headless environments need fallback UX.
- Runtime compromise can still access unlocked data; memory discipline and timeout policy are required.
- Test-only infrastructure must be kept clearly separated from production defaults.

## Non-goals

This ADR does not define:

- the final persistent store schema;
- the full migration path from in-memory store;
- cloud sync protocol;
- multi-device key recovery;
- organization/team key management;
- production cryptographic implementation details.

## Follow-up work

- Implement production `PlatformKeychainProvider` backends.
- Implement production `KeyManager` and `CryptoProvider` backends.
- Define SQLite schema for keyring and encrypted records.
- Add idle and absolute timeout policy presets for runtime unlock sessions.
- Define Deep Private / Layer 3 classification in a separate ADR or specification.
- Add production local vault security tests.
- Ensure MCP Context Exposure Policy works only after scoped vault access.
- Add CI jobs that enforce this ADR's storage, key, unlock, and MCP exposure invariants.
- Migrate Candidate / ReviewDecision / Lineage runtime paths from transitional FileSystem stores to Local Vault once production backends are ready.
- Replace fail-closed production `open_vault_runtime()` behavior with a production backend only after OS-backed key release and encrypted persistence are implemented.

## RDE audit note

This ADR preserves the meaning of local-first without weakening it into plain local storage. Local storage is not safe merely because it is local. Sayane must protect local context with encryption, scoped unlock, capability separation, and retention policy.

The key semantic boundary is that local vault access, UI unlock, and external tool access are different acts. Unlocking the UI must not imply that MCP, Bridge, or any extension can read the same context.

The current implementation status should be read as bounded evidence, not proof of production security. The test-only vault components make the intended boundaries executable for CI, but they do not provide production cryptographic assurance. The guarded runtime factory adds an additional fail-closed boundary by making test-only vault runtime explicit rather than implicit. The session manager adds another boundary by requiring scoped sessions at runtime instead of treating unlock as a global process state. The vault diagnostic command adds observability while preserving the same fail-closed boundary.
