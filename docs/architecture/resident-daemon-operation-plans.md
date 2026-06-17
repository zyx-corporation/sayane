# Resident Daemon Operation Plans

This document records #189 resident daemon start/stop/restart plan commands.

## Status

Plan-only lifecycle operation commands are implemented.

They do not start, stop, or restart a daemon process.

## Commands

```bash
sayane app daemon-start-plan --json
sayane app daemon-stop-plan --json
sayane app daemon-restart-plan --json
```

## Shared properties

Each command returns a `resident_daemon_operation_plan` payload.

Common fields include:

```text
operation
target_state
transition_allowed
plan_only
would_start_daemon
would_stop_daemon
would_restart_daemon
planned_sequence
current_serve_path
bridge_command
```

`plan_only` is always `true`.

All process mutation flags remain `false` in this phase.

## Start plan

`daemon-start-plan` describes the future transition from `stopped` to `starting`.

It does not start a daemon.

## Stop plan

`daemon-stop-plan` describes the future stop operation.

When current modeled state is `stopped`, `transition_allowed` is `false` for `stopping`.

It does not stop any process.

## Restart plan

`daemon-restart-plan` describes a two-step sequence:

```text
stop-if-running
start
```

It does not restart any process.

## Bind policy

All operation plan commands reuse the resident lifecycle local-bind validation:

```text
127.0.0.1
localhost
::1
```

Non-local bind addresses are rejected.

## Relationship to daemon lifecycle

These commands are built on the lifecycle contract from:

```text
docs/architecture/resident-daemon-lifecycle.md
```

They are the next step after `daemon-status` and `daemon-plan`.

## Non-goals

This work does not add:

- daemon process control
- PID files
- OS service installation
- systemd, launchd, or Windows Service support
- production credentials
- vault unlock-session binding
- network-exposed resident API

## RDE Delta-M Review

### Preserved

The daemon remains a future resident process, not a hidden side effect of CLI inspection.

Bridge delegation remains the active serving path.

### Supplemented

Operators and future UI code now have stable operation-plan payloads.

### Deviation Risk

Do not treat operation plans as control commands.

Do not implement real process mutation without revisiting credential and service lifecycle design.
