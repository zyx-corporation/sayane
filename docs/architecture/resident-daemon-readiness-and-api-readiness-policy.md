# Resident Daemon Readiness and API Readiness Policy

Status: Future verification policy

Related issues: #209, #210

## Summary

This document defines the policy boundary for future resident daemon readiness and local API readiness verification.

Even if a process exists and its identity is verified as Sayane, that does not prove that the daemon is ready or that a local API surface is usable.

## Evidence position

Readiness and API readiness are later evidence layers:

```text
PID parse validity -> process existence -> process identity -> daemon readiness -> API readiness
```

Each layer is stronger than the previous layer and must not be inferred from weaker evidence.

## Daemon readiness

Daemon readiness means the resident daemon has completed the relevant initialization and can safely accept the intended local operation class.

A verified Sayane process may still be:

- starting
- degraded
- wedged
- shutting down
- blocked on storage
- missing required capabilities
- using incompatible runtime state
- unable to serve a specific operation class

Therefore liveness is not readiness.

## API readiness

API readiness means that a future local resident API surface is:

- reachable
- authenticated
- authorized
- runtime-root scoped
- protocol-compatible
- semantically ready for the requested operation class

Daemon readiness is not automatically API readiness.

A daemon may be internally ready while a specific API surface is unavailable, unauthorized, incompatible, or disabled.

## Socket presence is not API readiness

Socket presence alone does not prove:

- endpoint ownership
- authentication
- authorization
- protocol compatibility
- API version compatibility
- operation readiness
- freshness

An open socket must not be treated as API readiness by itself.

## Future readiness evidence candidates

Future daemon readiness proof may require evidence such as:

- daemon-reported lifecycle state
- authenticated local IPC handshake
- runtime-root scoped nonce challenge
- capability scope validation
- storage readiness report
- schema/API version compatibility
- operation-class readiness declaration
- freshness timestamp or session epoch

No current Sayane command implements these checks.

## Conservative future statuses

Future readiness diagnostics should use conservative statuses such as:

```text
readiness_unverified
readiness_probe_unsupported
readiness_permission_denied
readiness_degraded
readiness_not_ready
readiness_verified
api_readiness_unverified
api_unreachable
api_unauthenticated
api_unauthorized
api_protocol_mismatch
api_operation_not_ready
api_readiness_verified
manual_review_required
```

A plain `ready` status should not be used unless the proof target is explicit.

## Operation-class readiness

Readiness is not necessarily global.

A future resident daemon may be ready for one operation class and not ready for another.

Examples:

- diagnostics ready
- review queue ready
- MCP context preview ready
- capture ready
- admin operation not ready
- mutation operation disabled

A future readiness payload should specify the operation class being verified.

## Non-goals for current preview work

Current Sayane commands do not:

- perform readiness checks
- create IPC endpoints
- expose a network-resident API
- introduce daemon authentication
- start a daemon
- stop a daemon
- restart a daemon
- supervise a daemon
- mutate filesystem artifacts

## Required future safety properties

Future readiness and API readiness verification must be:

- local by default
- runtime-root scoped
- capability scoped
- explicit about operation class
- conservative under ambiguity
- separated from process control
- separated from cleanup or repair

## Relationship to actual resident daemon implementation

Readiness and API readiness policies are prerequisites for an actual resident daemon implementation.

They do not themselves justify introducing a resident process.

A future actual daemon should be introduced only after:

```text
process existence policy
process identity policy
readiness policy
API readiness policy
mutation policy
operator consent model
```

are aligned.

## RDE Delta-M Review

### Preserved

Resident daemon evidence remains staged and explicitly bounded.

The preview layer remains non-mutating.

### Supplemented

The roadmap now separates liveness, daemon readiness, and API readiness.

### Deviation Risks

Do not treat a live process as ready.

Do not treat an identified process as API-ready.

Do not treat an open socket as authorized API readiness.

Do not introduce network exposure through a readiness diagnostic.
