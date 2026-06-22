# Resident Daemon Repair Apply MVP

This document records the first conservative `daemon-repair-preview` and
`daemon-repair-apply` slice.

## Status

Resident daemon repair apply is implemented for Class R1 runtime directory creation only.

## Scope

The current MVP only creates explicitly requested directories inside the validated local runtime
root:

- `runtime_root`
- `pid_dir`
- `lock_dir`
- `socket_dir`
- `log_dir`
- `temp_dir`
- `state_dir`

It does not rewrite PID files, lock files, socket files, or metadata files.

## Preview and confirmation

`daemon-repair-preview` returns:

- `operation_id`
- `preview_hash`
- per-target repair decisions
- current daemon status

`daemon-repair-apply` requires both:

- `--confirm-operation-id`
- `--confirm-preview-hash`

This keeps repair apply aligned with the explicit preview-to-apply consent boundary.

## Failure policy

Repair apply fails closed when:

- the resident daemon is running
- the preview confirmation does not match
- a target path already exists as a non-directory
- a target path is a symlink

Conflicting targets return `requires_review` rather than rewriting artifacts.

## Audit surface

When `--include-event-record` is supplied, repair apply returns a derived
`resident_daemon_event_record` with:

- `category: apply`
- `surface: daemon-repair-apply`
- requested targets
- created paths
- failure mode when present

## Non-goals

This MVP does not add:

- metadata creation or rewrite
- PID repair
- lock metadata repair
- socket recreation
- background automation
- OS service integration
