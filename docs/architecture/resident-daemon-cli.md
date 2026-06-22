# Resident Daemon Lifecycle CLI

This document records #188 resident daemon lifecycle CLI commands.

## Status

Resident daemon lifecycle and control CLI commands are implemented for a minimal local-only MVP.

## Commands

```bash
sayane app daemon-status --json
sayane app daemon-plan --json
sayane app daemon-start --json
sayane app daemon-stop --json
sayane app daemon-restart --json
sayane app daemon-cleanup-preview --json
sayane app daemon-cleanup-apply --remove pid_file --json
sayane app daemon-repair-preview --json
sayane app daemon-repair-apply --create runtime_root --json
sayane app daemon-readiness-diagnostic --json
sayane app daemon-packaging-status --json
sayane app daemon-service-targets-status --json
sayane app daemon-service-control-boundary --json
sayane app daemon-supervision-status --json
sayane app daemon-recovery-consent-status --json
sayane app daemon-launchagent-preview --json
sayane app daemon-launchagent-apply --json
sayane app daemon-launchagent-bootstrap --json
sayane app daemon-launchagent-bootout --json
sayane app daemon-launchagent-kickstart --json
sayane app daemon-overview --json
```

## daemon-status

`daemon-status` returns the current local resident daemon status metadata:

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
runtime_root
pid_path
lock_path
log_path
health_url
pid
pid_file_status
runtime_initialized
lock_exists
healthcheck_ok
manual_review_required
failure_mode
```

The default state is `stopped` until a daemon is started.

## daemon-plan

`daemon-plan` still returns a non-running plan payload.

It records the current serving relationship:

```text
current_serve_path: delegate_to_sayane_serve
bridge_command: sayane serve --host ... --port ...
```

The command does not start a process.

## daemon-start / daemon-stop / daemon-restart

These commands implement the first actual local-only resident daemon control slice.

`daemon-start` launches the existing `sayane serve` bridge as a subprocess after runtime
initialization has been completed.

`daemon-stop` sends a graceful termination signal to the managed subprocess and removes the PID and
lock files after exit.

`daemon-restart` combines the two operations.

When `--include-event-record` is supplied, these commands also return a derived
`resident_daemon_event_record` with `process` category.

## daemon-cleanup-apply

`daemon-cleanup-apply` is a narrow cleanup surface for reviewed local artifacts.

In the current MVP it removes only explicitly requested file targets such as `pid_file`,
`lock_file`, and `socket_file`.

It also requires the current cleanup preview's `operation_id` and `preview_hash` before mutation.

## daemon-repair-preview / daemon-repair-apply

`daemon-repair-apply` is a separate conservative repair surface for reviewed local directory
creation.

In the current MVP it creates only explicitly requested directory targets such as `runtime_root`,
`pid_dir`, `lock_dir`, `socket_dir`, `log_dir`, `temp_dir`, and `state_dir`.

It requires the current repair preview's `operation_id` and `preview_hash` before mutation.

When `--include-event-record` is supplied, the command also returns a derived
`resident_daemon_event_record` with `apply` category.

## daemon-readiness-diagnostic

`daemon-readiness-diagnostic` is a preview-only readiness observation surface.

It reports conservative `readiness_status` and `api_readiness_status` values for an
operator-visible operation class, but it does not prove process identity, daemon readiness, or
API readiness.

When the local health endpoint responds, the evidence ceiling remains
`unauthenticated_health_endpoint_only`.

## daemon-packaging-status

`daemon-packaging-status` exposes the current operator-facing packaging and supervision contract.

It makes the current local-only commitment explicit:

- primary entrypoint remains `sayane serve`
- local daemon control remains CLI-first and bridge-delegated
- cross-platform service targets are defined but only macOS LaunchAgent has concrete operator commands today
- tray, menu-bar, and background supervision UX are not yet supported

The current baseline is now more precise:

- cross-platform service targets are recorded for macOS, Linux, and Windows
- concrete preview/apply plus explicit local `launchctl` control currently exists for macOS LaunchAgent only
- Linux and Windows remain contract-only targets for now

## daemon-service-targets-status

`daemon-service-targets-status` exposes the shared service-target matrix across macOS, Linux, and
Windows.

It keeps these points explicit:

- macOS uses `launchd` / LaunchAgent as the first concrete packaging target
- Linux is tracked as a future `systemd --user` target
- Windows is tracked as a future Windows Service target

## daemon-launchagent-preview / daemon-launchagent-apply / daemon-launchagent-bootstrap / daemon-launchagent-bootout / daemon-launchagent-kickstart

These commands implement the first concrete macOS service-packaging slice.

`daemon-launchagent-preview` builds a LaunchAgent plist preview, including:

- plist path
- label
- program arguments
- stdout/stderr log paths
- suggested `launchctl` follow-up commands

`daemon-launchagent-apply` writes the reviewed plist after matching operation id and preview hash.

It does not silently call `launchctl bootstrap`; loading the service remains an explicit next step.

The three `launchctl` commands keep control explicit and local-only:

- `daemon-launchagent-bootstrap` runs `launchctl bootstrap gui/$(id -u) ...`
- `daemon-launchagent-bootout` runs `launchctl bootout gui/$(id -u) ...`
- `daemon-launchagent-kickstart` runs `launchctl kickstart -k gui/$(id -u)/com.sayane.resident.bridge`

They are separate from plist writing so the consent/review boundary remains clear.

## daemon-service-control-boundary

`daemon-service-control-boundary` exposes the current control-plane and service-plane split.

It makes all of the following explicit:

- local control commands are supported only through CLI-first localhost operations
- app UI may expose `daemon-start` only as a bounded next action, not as an unrestricted control surface
- service-manager commands remain deferred until platform-specific rollback and policy work lands
- background supervision toggles remain out of scope for the current app shell

## daemon-supervision-status

`daemon-supervision-status` exposes the current supervision UX decision line.

It keeps these points explicit:

- passive daemon visibility is supported through app and CLI read surfaces
- active supervision remains limited to explicit CLI control commands
- tray, menu-bar, and background agent surfaces remain deferred
- recovery stays CLI-first and evidence-oriented

## daemon-recovery-consent-status

`daemon-recovery-consent-status` exposes the current recovery path and consent boundary.

It keeps all of the following explicit:

- diagnostics and proof-oriented reads remain non-mutating
- cleanup and repair recovery steps still require explicit operator confirmation
- local app surfaces may explain recovery but must not bypass CLI consent checks
- post-recovery validation remains status-first and readiness-aware

## daemon-overview

`daemon-overview` is an app-facing aggregate preview for future UI code.

It combines current lifecycle status, liveness, readiness, runtime-init preview, cleanup preview,
repair preview, service-target status, macOS LaunchAgent preview, and suggested next commands into one non-mutating payload.

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

This work still does not add:

- Linux `systemd --user` or Windows Service implementation
- durable credentials
- vault unlock-session binding
- a second HTTP server path

## RDE Delta-M Review

### Preserved

The resident daemon remains a contract, not a hidden background process.

Bridge delegation remains the active serving path.

### Supplemented

Future UI and operators can inspect daemon lifecycle assumptions through stable JSON.

### Deviation Risk

Do not interpret repair apply as metadata, PID, lock, or socket rewrite authority.

Do not expose resident service beyond localhost.
