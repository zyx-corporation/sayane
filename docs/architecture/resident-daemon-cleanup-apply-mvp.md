# Resident Daemon Cleanup Apply MVP

Status: Minimal implementation slice

## Summary

`daemon-cleanup-apply` is the first conservative cleanup apply surface for the resident daemon MVP.

It is intentionally narrower than the cleanup preview and decision surfaces.

## Current scope

The MVP may remove only explicitly requested file targets:

- `pid_file`
- `lock_file`
- `socket_file`

It does not remove runtime directories.

## Safety boundary

Cleanup apply:

- is local-only
- requires explicit target selection with repeated `--remove`
- requires matching `--confirm-operation-id` and `--confirm-preview-hash`
- refuses to run while the daemon is running
- refuses type-mismatch targets as unsafe
- may return a schema-only event record when requested
