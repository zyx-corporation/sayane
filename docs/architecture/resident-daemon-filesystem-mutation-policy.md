# Resident Daemon Filesystem Mutation Policy

This document records #198 resident daemon filesystem mutation policy.

## Status

Policy only.

No daemon process control, directory creation, file writes, lock acquisition, socket creation, or stale artifact cleanup is implemented by this document.

## Context

Sayane v1.0.9 introduced preview contracts for resident daemon runtime layout.

The preview chain now includes:

```text
identity preview -> lifecycle preview -> operation plan preview -> runtime layout preview
```

These previews intentionally do not mutate the filesystem.

Before a future resident daemon can write PID files, acquire locks, create sockets, or persist state, the mutation policy must be explicit.

## Boundary principle

Filesystem mutation is not allowed from preview commands.

Preview commands must remain diagnostic and must report their non-mutating nature explicitly.

Current preview commands include:

```bash
sayane app daemon-identity --json
sayane app daemon-plan --json
sayane app daemon-start-plan --json
sayane app daemon-stop-plan --json
sayane app daemon-restart-plan --json
sayane app daemon-runtime-layout --json
```

These commands may compute planned paths and planned transitions.

They must not:

- create runtime directories
- write PID files
- acquire locks
- create socket files
- write logs
- write temp files
- persist daemon state
- delete stale artifacts
- start, stop, or restart processes

## Future mutating command boundary

Future filesystem mutation must be introduced through explicitly named mutating commands or daemon internals.

A future mutating command must not reuse preview names in a way that silently changes their behavior.

For example, a future mutating start command may be named separately from `daemon-start-plan`.

Preview command names ending in `-plan` or using `preview` semantics must remain non-mutating.

## Runtime root policy

The default runtime root is:

```text
.sayane/run
```

All daemon-owned runtime artifacts must stay under the configured runtime root.

The daemon must reject path escape attempts.

Runtime root creation, if added in the future, must satisfy all of the following:

- local user ownership
- non-world-writable permissions
- no symlink traversal outside the runtime root
- no root privilege requirement
- explicit error on unsafe ownership or permissions

## PID file policy

A future PID file may record a resident daemon process identity.

PID file creation must be atomic.

The PID file must not be treated as sufficient proof that a daemon is alive.

A PID file can only be considered valid after checking:

- the PID exists
- the process identity matches expected Sayane daemon identity
- the process appears to belong to the current user
- the configured runtime root matches the expected daemon instance

A stale PID file must not be deleted automatically unless all validation checks prove it is safe.

Ambiguous stale PID files require manual review.

## Lock file policy

A future lock file or lock acquisition mechanism must prevent concurrent resident daemon instances for the same runtime root.

Lock acquisition must be explicit and atomic.

The lock must be scoped to the runtime root.

Lock metadata should include enough information for diagnostics, such as:

- process id
- user id or username when safe
- host name when safe
- runtime root
- created timestamp
- daemon version

Lock acquisition failure must not silently fall back to a second daemon instance.

Ambiguous stale locks require manual review.

## Socket policy

A future resident daemon socket must be local-only.

Socket creation must stay under the runtime root unless an explicitly documented platform-specific local IPC path is chosen later.

A socket file must not be exposed as a public network API.

A stale socket file must not be removed unless it is safe to prove no active daemon is using it.

## Log policy

A future log directory may be used for resident daemon diagnostics.

Logs must not store secrets, durable capability tokens, profile contents, or raw private context by default.

Log writes must be bounded or rotate safely.

A preview command must not create the log directory.

## Temp file policy

A future temp directory may be used for short-lived daemon artifacts.

Temp files must be scoped under runtime root and should be cleaned only when ownership and safety are clear.

Ambiguous temp artifacts must not be silently deleted.

## State file policy

A future state directory may persist daemon state.

State files must be versioned or schema-tagged.

State files must not store durable credentials unless a separate credential storage policy is accepted.

State persistence must distinguish:

- daemon runtime state
- local vault data
- profile/context data
- credentials or capability tokens

These categories must not be collapsed into a single untyped file.

## Failure rollback policy

A future mutating daemon operation must define rollback behavior.

If startup fails after partial filesystem mutation, the daemon must leave clear diagnostics and avoid destructive cleanup unless ownership and safety are proven.

Rollback should prefer:

1. leave safe diagnostics
2. release acquired locks when definitely owned
3. remove newly created files only when definitely owned
4. require manual review for ambiguous artifacts

## Manual review requirement

Manual review is required when Sayane cannot prove that an artifact is safe to delete or replace.

Manual review is required for ambiguous:

- PID files
- lock files
- socket files
- temp files
- state files

The default stale artifact policy remains:

```text
manual_review_required
```

## Non-root assumption

Resident daemon filesystem mutation must assume normal user privileges.

The daemon must not require root privileges for local resident operation.

If an OS service integration is introduced later, it must be documented separately and must not change the default local-user policy.

## Security non-goals retained

This policy does not add:

- process control
- directory creation
- PID file writes
- lock acquisition
- socket creation
- log writes
- temp file writes
- persisted daemon state
- stale artifact cleanup
- OS service integration
- durable credentials
- network authentication

## RDE Delta-M Review

### Preserved

Preview commands remain non-mutating.

Resident daemon implementation remains staged and auditable.

The runtime layout is still a contract, not a running daemon.

### Supplemented

Future daemon mutation now has explicit safety gates.

Stale artifact handling is conservative by default.

Manual review remains the fallback for ambiguity.

### Deviation Risks

Do not let preview commands mutate the filesystem.

Do not silently delete stale PID, lock, socket, temp, or state artifacts.

Do not treat PID files as proof of process liveness.

Do not introduce OS service assumptions into the local-user default path.

Do not store durable credentials or raw private context in daemon runtime state by default.
