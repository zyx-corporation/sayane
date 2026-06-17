# Changelog

All notable changes to the Sayane Community Edition (OSS) are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.0.10] - 2026-06-17 Resident Daemon Cleanup Decision Preview

### Summary

Sayane v1.0.10 packages the resident daemon cleanup decision preview track. It adds read-only stale artifact diagnostics and a non-mutating cleanup decision model for planned resident daemon runtime artifacts.

### Added

- Read-only stale artifact diagnostic model for planned resident daemon artifacts.
- Stale artifact diagnostic CLI command:
  - `sayane app daemon-stale-artifacts --json`
- Optional stale artifact diagnostic runtime root override:
  - `sayane app daemon-stale-artifacts --runtime-root /path/to/runtime --json`
- Non-mutating cleanup decision model.
- Cleanup decision CLI command:
  - `sayane app daemon-cleanup-decisions --json`
- Optional cleanup decision runtime root override:
  - `sayane app daemon-cleanup-decisions --runtime-root /path/to/runtime --json`
- Architecture docs for stale artifact diagnostics and cleanup decision model.

### Cleanup decision rules

- `missing -> no_action`
- `present_review_required -> manual_review_required`
- `type_mismatch_review_required -> unsafe_to_delete`

### Security

- Stale artifact diagnostics do not delete or repair artifacts.
- Cleanup decisions do not delete or repair artifacts.
- No command creates runtime directories.
- No command writes PID, lock, socket, log, temp, or state files.
- No command acquires locks.
- No command controls processes.
- No current cleanup decision marks an artifact as safe to delete without stronger future checks.

### CI

- GitHub Actions run #138 completed successfully on `main` after the cleanup decision preview work.

### Non-goals retained

- No production resident daemon process control.
- No OS service integration.
- No PID file writes.
- No lock acquisition.
- No socket creation.
- No stale artifact deletion or repair.

## [1.0.9] - 2026-06-17 Resident Daemon Runtime Layout Preview

### Summary

Sayane v1.0.9 packages the resident daemon runtime layout preview track. It adds a plan-only runtime directory layout contract, exposes the layout through a read-only CLI preview, and fixes CLI version reporting so it follows installed package metadata.

### Added

- Resident daemon runtime directory layout contract.
- Planned runtime directories:
  - `pid`
  - `lock`
  - `socket`
  - `log`
  - `tmp`
  - `state`
- Runtime-root path validation for layout child paths.
- Read-only daemon runtime layout CLI command:
  - `sayane app daemon-runtime-layout --json`
- Optional runtime root override:
  - `sayane app daemon-runtime-layout --runtime-root /path/to/runtime --json`
- Architecture docs for runtime layout contract and runtime layout CLI preview.

### Changed

- `sayane --version` now reads installed package metadata instead of stale source constants.
- Package tests now assert version metadata consistency.

### Security

- Runtime layout preview does not create directories.
- Runtime layout preview does not write PID, lock, socket, log, temp, or state files.
- Runtime layout preview does not acquire locks.
- Runtime layout preview does not control processes.
- Path escape attempts are rejected by the app-layer runtime layout model.

### CI

- GitHub Actions run #116 completed successfully on `main` after the runtime layout CLI preview work.

### Non-goals retained

- No production resident daemon process control.
- No OS service integration.
- No PID file writes.
- No lock acquisition.
- No socket creation.
- No stale runtime file cleanup.

## [1.0.8] - 2026-06-17 Resident Daemon Identity Preview

### Summary

Sayane v1.0.8 packages the resident daemon identity preview track. It adds a plan-only process identity contract and a read-only identity CLI preview for planned PID, lock, and socket paths without writing files, acquiring locks, creating sockets, or controlling a daemon process.

### Added

- Resident daemon process identity contract.
- Planned PID, lock, and socket paths.
- Runtime-local path validation for daemon identity paths.
- Read-only daemon identity CLI command:
  - `sayane app daemon-identity --json`
- Optional runtime directory override:
  - `sayane app daemon-identity --runtime-dir /path/to/runtime --json`
- Architecture docs for daemon identity contract and identity CLI preview.

### Security

- Identity preview does not write PID files.
- Identity preview does not acquire locks.
- Identity preview does not create sockets.
- Identity preview does not control processes.
- Path escape attempts are rejected by the app-layer identity model.

### Non-goals retained

- No production resident daemon process registry.
- No PID file writes.
- No lock acquisition.
- No stale lock cleanup.
- No OS service integration.

## [1.0.7] - 2026-06-17 Resident Daemon Lifecycle Preview

### Summary

Sayane v1.0.7 packages the resident daemon lifecycle preview track. It adds a lifecycle contract model, read-only daemon lifecycle CLI diagnostics, and plan-only daemon operation commands without starting a resident daemon or introducing production credentials.

### Added

- Resident daemon lifecycle contract model with explicit states:
  - `stopped`
  - `starting`
  - `running`
  - `stopping`
  - `failed`
- Resident daemon ownership modes:
  - `bridge_delegation`
  - `resident_server_reserved`
- Localhost-only bind validation for future resident daemon surfaces.
- Read-only lifecycle CLI commands:
  - `sayane app daemon-status --json`
  - `sayane app daemon-plan --json`
- Plan-only daemon operation CLI commands:
  - `sayane app daemon-start-plan --json`
  - `sayane app daemon-stop-plan --json`
  - `sayane app daemon-restart-plan --json`
- Architecture docs for lifecycle contract, lifecycle CLI, and operation plan commands.

### Security

- Daemon preview commands do not start, stop, restart, or expose a process.
