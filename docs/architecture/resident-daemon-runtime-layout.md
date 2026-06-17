# Resident Daemon Runtime Layout

This document records #194 resident daemon runtime directory layout contract.

## Status

A plan-only runtime directory layout model is implemented.

It does not create directories, write files, acquire locks, or control processes.

## Layout fields

The model records a runtime root and planned child directories:

```text
runtime_root
pid_dir
lock_dir
socket_dir
log_dir
temp_dir
state_dir
```

Default child directory names are:

```text
pid
lock
socket
log
tmp
state
```

## Runtime-root path policy

All planned child directories must stay under `runtime_root`.

Parent-relative names that would place a path outside `runtime_root` are rejected.

## Non-mutating behavior

The layout model is diagnostic only.

It explicitly reports:

```text
creates_directories: false
writes_files: false
is_filesystem_mutation: false
```

## Relationship to daemon identity

The runtime layout contract complements the daemon identity contract.

Identity records planned PID, lock, and socket files.

Runtime layout records the planned directories in which daemon runtime artifacts may later live.

Neither contract mutates the filesystem.

## Non-goals

This work does not add:

- directory creation
- PID file writes
- lock file writes
- socket creation
- log writes
- temp file creation
- state file persistence
- stale file cleanup
- OS service integration

## RDE Delta-M Review

### Preserved

No hidden daemon process is introduced.

Runtime layout remains a plan-only contract.

### Supplemented

Future daemon implementation now has a stable runtime directory layout before process control or filesystem mutation is added.

### Deviation Risk

Do not treat this layout preview as proof that runtime directories exist.

Do not add filesystem mutation without a separate review.
