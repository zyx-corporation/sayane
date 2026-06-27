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

Implemented unlock policy presets:

- `src/sayane/vault/unlock_policy.py`
  - `UnlockLevel`
  - `UnlockPolicy`
  - `default_unlock_policy()`
  - `build_unlock_session_from_policy()`

The current presets encode the ADR 0001 timeout model:

| Level | Idle timeout | Absolute timeout | Default scope family |
| --- | --- | --- | --- |
| `normal` | 15 min | 60 min | profile / project context / MCP compiled context read |
| `sensitive` | 5 min | 15 min | candidate / review decision / lineage read-write-key |
| `deep_private` | 3 min | 5 min | deep private / raw capture / cloud transfer detail |

Implemented session management:

- `src/sayane/vault/session.py`
  - `InMemoryUnlockSessionManager`

`InMemoryUnlockSessionManager` delegates key release to a `PlatformKeychainProvider`, tracks session metadata, enforces session existence, rejects expired sessions, checks scopes, and closes sessions through the keychain. It is currently used by `VaultRuntime`.

`InMemoryUnlockSessionManager.open_policy_session()` can open sessions using the ADR 0001 unlock presets. This makes timeout and scope policy executable without treating unlock as a global process state.

Implemented explicit lower-assurance development runtime:

- `src/sayane/vault/development.py`
  - `PassphraseKeychainProvider`
  - `SQLiteKeyringKeyManager`
  - `AesGcmCryptoProvider`
  - `build_sqlite_development_vault_runtime()`

This adds a concrete encrypted SQLite path for explicit development use:

- passphrase-derived wrapping secret
- persisted wrapped DEKs in the `keyring` table
- AES-256-GCM encrypted records with canonicalized AAD binding
- scoped unlock sessions over the same vault boundary

It remains intentionally lower assurance than future OS-backed production keychain integrations and
does not change the fail-closed production default.

Implemented explicit macOS keychain-backed runtime:

- `src/sayane/vault/macos_keychain.py`
  - `MacOSKeychainProvider`
  - `build_sqlite_macos_vault_runtime()`

This adds the first concrete OS-backed keychain path for Local Vault:

- wrapping secret stored in macOS Keychain generic-password item storage
- persisted wrapped DEKs in SQLite `keyring`
- AES-256-GCM encrypted records over the same record/key boundary
- explicit opt-in runtime opening rather than silent production default selection

The current macOS path is production-shaped but still intentionally explicit:

- callers must provide a vault SQLite path
- callers must request the macOS keychain backend directly
- production default remains fail-closed until broader backend selection is accepted

Implemented SQLite schema contract:

- `src/sayane/vault/sqlite_schema.py`
  - `SCHEMA_VERSION = local_vault.sqlite.v1`
  - `VaultTable`
  - `TableContract`
  - `required_table_contracts()`
  - `validate_sqlite_vault_schema()`
  - `inspect_sqlite_tables()`
  - `quote_sqlite_identifier()`
  - `create_table_statements()`

The schema contract defines three required table families:

| Table | Purpose |
| --- | --- |
| `keyring` | wrapped DEK metadata and key status |
| `encrypted_records` | encrypted vault record content with AAD binding |
| `audit_metadata` | non-secret audit metadata for vault operations |

The contract requires `wrapped_dek`, `ciphertext`, and `aad_json` style fields, and explicitly rejects production schema columns such as `plaintext`, `plain_text`, `raw_content`, `master_key`, `unwrapped_dek`, and `private_key`.

`inspect_sqlite_tables()` reads only SQLite metadata via `sqlite_master` and `PRAGMA table_info`; it must not select record rows or expose encrypted record content. This supports `sayane vault schema --database` as a schema validation tool, not a data inspection tool.

Implemented SQLite-backed encrypted persistence seam:

- `src/sayane/vault/sqlite_store.py`
  - `SQLiteVaultStore`

`SQLiteVaultStore` persists `EncryptedRecord` rows into `encrypted_records` using an injected `CryptoProvider`. It reports `is_plaintext_default() == False`, enforces session scopes for read/write/delete/list operations, and stores ciphertext plus AAD metadata rather than plaintext content. This is not yet a production Local Vault backend because production OS-backed key release and production cryptography are still missing.

Implemented explicit SQLite test runtime builder:

- `src/sayane/vault/sqlite_runtime.py`
  - `build_sqlite_test_vault_runtime()`

`build_sqlite_test_vault_runtime()` wires `TestOnlyKeychainProvider`, `TestOnlyKeyManager`, `TestOnlyCryptoProvider`, `SQLiteVaultStore`, and `VaultRepositoryBundle` together for explicit test-only diagnostics and CI coverage. It exercises the encrypted persistence seam and repository adapter path, but it is not a production backend and must not be selected by production defaults.

Implemented test-only infrastructure:

- `src/sayane/vault/test_store.py`
  - `TestOnlyKeychainProvider`
  - `InMemoryTestVaultStore`
  - `CryptoBackedInMemoryTestVaultStore`
- `src/sayane/vault/test_crypto.py`
  - `TestOnlyKeyManager`
  - `TestOnlyCryptoProvider`

These test-only components are not cryptographic protection. They exist only to exercise the contract shape, scope checks, AAD binding, DEK separation, rotation/destroy semantics, repository adapter behavior, and SQLite persistence behavior.

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
- `src/sayane/vault/sqlite_runtime.py`
  - `build_sqlite_test_vault_runtime()`

The runtime factory is intentionally fail-closed. Production and development Local Vault backends are not implemented yet, so `open_vault_runtime()` without `mode="test"` raises an error. Test-only components are available only through explicit `mode="test"`, `build_test_vault_runtime()`, or `build_sqlite_test_vault_runtime()` calls.

`VaultRuntime` now owns an `UnlockSessionManager`, so runtime callers can open, require, and close scoped sessions without directly sharing UI unlock state with external tools.

Implemented diagnostic entrypoint:

- `src/sayane/cli/vault_cmd.py`
  - `sayane vault status`
  - `sayane vault status --json`
  - `sayane vault status --test`
  - `sayane vault status --test --json`
  - `sayane vault status --test --sqlite <path> --json`
  - `sayane vault policy`
  - `sayane vault policy --json`
  - `sayane vault schema`
  - `sayane vault schema --json`
  - `sayane vault schema --ddl`
  - `sayane vault schema --ddl --json`
  - `sayane vault schema --database <path>`
  - `sayane vault schema --database <path> --json`

The diagnostic commands are non-destructive and do not expose plaintext records. `vault status` checks runtime readiness and remains fail-closed for production while the backend is unimplemented. `vault status --test --sqlite <path> --json` opens only the explicit SQLite-backed test runtime and must report `test_only: true`, `sqlite_backed: true`, and `production_ready: false`. `vault policy` displays unlock policy presets without opening the runtime. `vault schema` displays the SQLite schema contract without opening a database by default. `vault schema --database` opens an existing SQLite file read-only and inspects schema metadata only; validation failure returns exit code 1.

The current Vault adapters cover:

- Candidate records as `DataClass.CANDIDATE`
- ReviewDecision records as `DataClass.REVIEW_DECISION`
- Lineage records as `DataClass.LINEAGE`

Current AAD binding includes profile identity, record type, schema version, and record-specific identifiers such as candidate id, decision type, event id, operation, and node kind where applicable.

Current limitations:

- No production OS-backed keychain provider exists yet.
- No production cryptographic provider exists yet.
- SQLite-backed encrypted persistence exists only as a store seam, not as the default production Local Vault backend.
- SQLite-backed runtime construction exists only as an explicit test-only seam.
- Test-only providers must not be selected by production defaults.
- Existing FileSystem stores remain transitional local working stores until the Local Vault backend is production-ready.

## CI enforcement

This ADR must be enforced by automated checks before Local Vault or persistent Candidate / ReviewDecision / Lineage storage becomes a default path.

Required CI checks:

- run storage backend tests;
- run storage security policy tests;
- run MCP context exposure tests;
- run Local Vault contract tests;
- run unlock policy preset tests;
- run unlock session manager tests;
- run SQLite Local Vault schema contract tests;
- run SQLite-backed VaultStore tests;
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
- fail if SQLite Local Vault schema contains plaintext, master key, unwrapped DEK, raw content, or private key columns;
- fail if SQLite-backed VaultStore persists plaintext content instead of encrypted records;
- fail if SQLite-backed VaultStore reports itself as plaintext default;
- fail if explicit SQLite test runtime construction is treated as production-ready;
- fail if `sayane vault schema --database` reads record rows instead of schema metadata only;
- fail if `sayane vault schema --database` cannot detect forbidden production columns;
- fail if test-only vault providers become production defaults;
- fail if test-only vault runtime can be opened as production default;
- fail if `sayane vault status` opens test-only runtime without an explicit test flag;
- fail if `sayane vault status --test --sqlite` is treated as a production backend path.

Current targeted CI checks:

```bash
pytest tests/test_storage_backend.py
pytest tests/test_storage_security_policy.py
pytest tests/test_storage_write_policy.py
pytest tests/test_review_decision_store.py
pytest tests/test_vault_contracts.py
pytest tests/test_unlock_policy.py
pytest tests/test_unlock_session_manager.py
pytest tests/test_vault_test_store.py
pytest tests/test_vault_test_crypto.py
pytest tests/test_vault_candidate_adapter.py
pytest tests/test_vault_review_decision_adapter.py
pytest tests/test_vault_lineage_adapter.py
pytest tests/test_vault_repository_bundle.py
pytest tests/test_vault_factory.py
pytest tests/test_vault_cli.py
pytest tests/test_sqlite_vault_schema.py
pytest tests/test_sqlite_vault_store.py
pytest tests/test_mcp_context.py
```

Future CI targets, once production Local Vault modules exist:

```bash
pytest tests/test_vault_key_manager.py
pytest tests/test_platform_keychain_provider.py
pytest tests/test_local_vault_persistence.py
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
- Unlock policy presets make normal / sensitive / deep_private timeout behavior executable and testable.
- SQLite schema contract makes keyring / encrypted record boundaries executable before persistent storage is implemented.
- SQLite schema metadata validation allows future vault files to be checked without reading record rows.
- SQLite-backed VaultStore provides an encrypted persistence seam without making SQLite plaintext or production-default.
- Explicit SQLite test runtime construction makes the SQLite persistence seam diagnosable without promoting it to production.
- Vault diagnostics now expose runtime readiness without exposing plaintext or silently opening test-only storage.

Costs:

- More implementation complexity than plaintext SQLite.
- Search and indexing over encrypted content require careful design.
- Linux/headless environments need fallback UX.
- Runtime compromise can still access unlocked data; memory discipline and timeout policy are required.
- Test-only infrastructure must be kept clearly separated from production defaults.

## Non-goals

This ADR does not define:

- the final persistent store migration path;
- cloud sync protocol;
- multi-device key recovery;
- organization/team key management;
