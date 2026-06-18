# Sayane Community v1.0.13

Resident Daemon Preflight Schema Preview

## Summary

Sayane v1.0.13 packages schema-only resident daemon implementation support on top of the v1.0.12 policy gate.

This release adds:

- schema-only resident daemon event record support
- resident daemon implementation gate preflight checklist
- optional preflight-derived event record preview output
- schema-only resident daemon state machine support

## Commands

```bash
sayane app daemon-preflight --json
sayane app daemon-preflight --json --include-event-record
```

## Safety boundary retained

- No production resident daemon runtime
- No daemon process start, stop, restart, signal sending, or supervision
- No process probing
- No PID file writes
- No lock acquisition, release, or stealing
- No socket creation
- No IPC endpoint exposure
- No runtime directory creation
- No stale artifact deletion
- No artifact repair
- No OS service integration
- No persistent IPC credentials
- No network-exposed resident API
