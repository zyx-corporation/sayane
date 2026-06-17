# Resident Daemon Process Identity

This document records #191 resident daemon process identity and lockfile contract.

## Status

A plan-only process identity contract is implemented.

It does not write PID files, acquire locks, create sockets, or control processes.

## Identity fields

The model records:

```text
name
runtime_dir
pid_path
lock_path
socket_path
writes_files
acquires_lock
stale_lock_policy
is_process_control
```

Default identity name:

```text
sayane-resident
```

Default planned filenames:

```text
sayane-resident.pid
sayane-resident.lock
sayane-resident.sock
```

## Runtime-local path policy

PID, lock, and socket paths must stay under `runtime_dir`.

Path escape attempts such as `../escape.pid` are rejected.

## Non-mutating behavior

The identity model is diagnostic only.

It does not create:

- runtime directories
- PID files
- lock files
- socket files

It also does not acquire locks or clean stale locks.

## Stale lock policy

The initial stale lock policy is:

```text
manual_review_required
```

Automatic stale lock cleanup is intentionally deferred.

## Non-goals

This work does not add:

- PID file writes
- file locking
- socket creation
- process killing
- process restart
- OS service integration
- production daemon process control

## RDE Delta-M Review

### Preserved

No hidden daemon process is introduced.

Lifecycle and operation commands remain plan-only.

### Supplemented

Future daemon implementation now has an explicit identity, PID path, lock path, and socket path contract.

### Deviation Risk

Do not treat the identity contract as a running daemon registry.

Do not add automatic stale lock cleanup without a separate review.
