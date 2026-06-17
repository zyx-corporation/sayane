# Resident Daemon Stale Artifact Diagnostics

This document records #199 resident daemon stale artifact diagnostic preview.

## Status

Read-only diagnostic preview.

No filesystem mutation is introduced.

## Command

```bash
sayane app daemon-stale-artifacts --json
```

Optional runtime root override:

```bash
sayane app daemon-stale-artifacts --runtime-root /path/to/runtime --json
```

## Purpose

This command reports the observable state of planned resident daemon runtime artifacts without deleting, repairing, creating, or modifying anything.

It supports future daemon implementation by establishing a conservative diagnostic payload before stale artifact cleanup is ever added.

## Artifacts observed

The diagnostic preview observes planned paths for:

```text
runtime_root
pid_file
lock_file
socket_file
pid_dir
lock_dir
socket_dir
log_dir
temp_dir
state_dir
```

## Payload

Top-level payload fields include:

```text
kind
preview_only
runtime_root
stale_artifact_policy
repairs_artifacts
deletes_artifacts
creates_artifacts
mutates_filesystem
manual_review_required
diagnostics
```

Each diagnostic item includes:

```text
kind
path
expected_type
exists
is_file
is_dir
is_socket
status
manual_review_required
safe_to_delete
mutates_filesystem
```

## Conservative statuses

The diagnostic preview uses conservative statuses:

```text
missing
present_review_required
type_mismatch_review_required
```

A missing artifact does not require review.

A present artifact requires review because this preview does not prove ownership, liveness, or safety.

A type mismatch requires review because it may indicate an unexpected file at a daemon-owned path.

## Manual review policy

The default stale artifact policy remains:

```text
manual_review_required
```

The preview never reports an artifact as safe to delete.

```text
safe_to_delete: false
```

A future mutating cleanup command must establish stronger ownership and liveness checks before changing this behavior.

## Non-mutating guarantees

This command does not:

- create runtime directories
- write PID files
- acquire locks
- create socket files
- write logs
- write temp files
- write state files
- delete stale artifacts
- repair stale artifacts
- start, stop, or restart processes

It explicitly reports:

```text
repairs_artifacts: false
deletes_artifacts: false
creates_artifacts: false
mutates_filesystem: false
preview_only: true
```

## Relationship to #198

#198 defines the filesystem mutation policy.

#199 implements only the read-only diagnostic layer allowed by that policy.

This preserves the boundary between observation and mutation.

## RDE Delta-M Review

### Preserved

Preview commands remain non-mutating.

Ambiguous stale artifacts still require manual review.

### Supplemented

Operators can now inspect whether planned daemon artifact paths exist before any mutating behavior is introduced.

Future cleanup logic gains a stable diagnostic payload.

### Deviation Risks

Do not interpret `present_review_required` as proof that an artifact is stale.

Do not treat missing artifacts as an error by default.

Do not delete, repair, or overwrite artifacts based only on this preview payload.

Do not use this diagnostic as process liveness proof.
