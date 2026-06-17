# Resident Daemon Liveness Diagnostic Preview

Status: Preview-only diagnostic design

Related issues: #204, #207

## Summary

Sayane exposes a read-only resident daemon liveness diagnostic preview:

```bash
sayane app daemon-liveness-diagnostic --json
```

The command reports the current evidence ceiling between PID file parsing and future process liveness proof.

It does not prove daemon liveness. It does not probe operating-system processes. It does not control processes. It does not mutate the filesystem.

## Motivation

The PID file diagnostic preview can classify planned PID file content as:

```text
missing
unreadable
empty
invalid
parsed
```

However, even a parsed PID proves only that the PID file contained a positive integer string. It does not prove that:

- the process exists
- the process is alive
- the process is Sayane
- the daemon is ready
- a local resident API is reachable

The liveness diagnostic preview makes this boundary explicit in a separate payload.

## Command

Default runtime root:

```bash
sayane app daemon-liveness-diagnostic --json
```

Runtime root override:

```bash
sayane app daemon-liveness-diagnostic --runtime-root /path/to/runtime --json
```

The command does not create the runtime root.

## Status model

The command maps PID parse diagnostics to conservative liveness statuses:

```text
missing -> pid_missing_liveness_unverified
unreadable -> pid_unreadable_liveness_unverified
empty -> pid_empty_liveness_unverified
invalid -> pid_invalid_liveness_unverified
parsed -> pid_parsed_process_unverified
```

No current status claims `liveness_verified`.

## Evidence ceiling

The payload includes `evidence_ceiling`:

```text
pid_file_diagnostic_only
pid_file_parsed_only
```

`pid_file_diagnostic_only` means the command observed only the PID file diagnostic state.

`pid_file_parsed_only` means the command observed a parsed PID string but still did not verify process existence, process identity, daemon readiness, or API readiness.

## Payload safety indicators

The payload keeps the following booleans false:

```text
proves_liveness: false
probes_process: false
controls_process: false
mutates_filesystem: false
```

These flags are part of the safety contract. A future command that changes any of these meanings must not silently reuse this preview surface.

## Non-mutating boundary

The liveness diagnostic preview does not:

- start a daemon
- stop a daemon
- restart a daemon
- supervise a daemon
- probe a process
- send signals
- inspect OS process tables
- read arbitrary `/proc` state
- write PID files
- acquire locks
- create sockets
- create runtime directories
- delete or repair stale artifacts
- expose a network-resident API

## Relationship to future liveness proof

This preview intentionally stops before the policy boundary documented in:

```text
docs/architecture/resident-daemon-process-liveness-proof-policy.md
```

A future liveness proof may require process existence evidence, process identity evidence, runtime-root scoping, freshness evidence, and authenticated local readiness checks.

Those checks are future work and are not implemented by this preview.

## RDE Delta-M Review

### Preserved

Resident daemon work remains staged and auditable.

Preview commands remain non-mutating.

PID parsing remains separated from process liveness proof.

### Supplemented

The preview sequence now has an explicit evidence-ceiling layer:

```text
PID parse diagnostic -> liveness diagnostic preview -> future liveness proof
```

### Deviation Risks

Do not interpret `pid_parsed_process_unverified` as `running`.

Do not treat a parsed PID as Sayane process identity.

Do not add hidden process probing behind the preview command.

Do not add repair, cleanup, restart, or lock behavior to this diagnostic surface.
