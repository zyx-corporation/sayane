# Resident Daemon Lifecycle CLI

This document records #188 resident daemon lifecycle CLI commands.

## Status

Read-only lifecycle CLI commands are implemented.

They do not start a resident daemon.

## Commands

```bash
sayane app daemon-status --json
sayane app daemon-plan --json
```

## daemon-status

`daemon-status` returns the current lifecycle contract metadata:

```text
state
mode
host
port
runtime_backend
unlock_session_binding
capability_policy
is_local_bind
is_running_daemon
```

The default state is `stopped`.

The default mode is `bridge_delegation`.

`is_running_daemon` is always `false` in this phase.

## daemon-plan

`daemon-plan` returns a non-running plan payload.

It records the current serving relationship:

```text
current_serve_path: delegate_to_sayane_serve
bridge_command: sayane serve --host ... --port ...
```

The command does not start a process.

## Local bind policy

Both commands enforce localhost-only bind assumptions:

```text
127.0.0.1
localhost
::1
```

Non-local addresses such as `0.0.0.0` are rejected.

## Relationship to app serve

`sayane app serve` remains the operational delegation plan to the existing Bridge command.

`daemon-status` and `daemon-plan` only expose lifecycle diagnostics for the future resident daemon.

## Non-goals

This work does not add:

- daemon start or stop commands
- OS service integration
- systemd, launchd, or Windows Service support
- durable credentials
- vault unlock-session binding
- production authentication
- a second HTTP server path

## RDE Delta-M Review

### Preserved

The resident daemon remains a contract, not a hidden background process.

Bridge delegation remains the active serving path.

### Supplemented

Future UI and operators can inspect daemon lifecycle assumptions through stable JSON.

### Deviation Risk

Do not interpret these commands as daemon control commands.

Do not expose resident service beyond localhost.
