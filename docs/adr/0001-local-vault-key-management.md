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

## Consequences

Benefits:

- Local-first storage becomes meaningfully protected.
- Key rotation is feasible because DEKs can be re-wrapped without re-encrypting all data.
- Data-class separation supports Least Context and Right to Fade.
- Deep Private / Layer 3 data receives stronger interaction friction.
- MCP, Bridge, UI, and CLI can share a common vault without sharing all permissions.

Costs:

- More implementation complexity than plaintext SQLite.
- Search and indexing over encrypted content require careful design.
- Linux/headless environments need fallback UX.
- Runtime compromise can still access unlocked data; memory discipline and timeout policy are required.

## Non-goals

This ADR does not define:

- the final persistent store schema;
- the full migration path from in-memory store;
- cloud sync protocol;
- multi-device key recovery;
- organization/team key management.

## Follow-up work

- Implement `PlatformKeychainProvider` abstraction.
- Implement `KeyManager` and `CryptoProvider` interfaces.
- Define SQLite schema for keyring and encrypted records.
- Add unlock session manager with idle and absolute timeout.
- Define Deep Private / Layer 3 classification in a separate ADR or specification.
- Add local vault security tests.
- Ensure MCP Context Exposure Policy works only after scoped vault access.

## RDE audit note

This ADR preserves the meaning of local-first without weakening it into plain local storage. Local storage is not safe merely because it is local. Sayane must protect local context with encryption, scoped unlock, capability separation, and retention policy.

The key semantic boundary is that local vault access, UI unlock, and external tool access are different acts. Unlocking the UI must not imply that MCP, Bridge, or any extension can read the same context.
