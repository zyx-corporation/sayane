# ADR 0008: Resident Daemon Runtime Init Consent Boundary

## Status

Accepted

## Date

2026-06-18

## Context

By `v1.0.12`, Sayane had completed the resident daemon policy and preview gate, but it still explicitly did not implement a production daemon runtime.

After `v1.0.13`, the project began the first minimal implementation slices that cross from preview-only behavior into carefully bounded local mutation:

- `daemon-runtime-init` as an explicit runtime initialization surface
- initialization metadata placeholder support
- event-record derivation for preview/apply audit shape
- explicit operation confirmation for metadata writes

These changes introduce an architectural decision that is more important than an individual command.

The core risk is silent boundary drift.

If runtime layout preview, runtime initialization, metadata writing, event records, and future daemon control are allowed to blur together, Sayane may accidentally make stronger claims than the implementation can support.

Examples of dangerous drift include:

- preview commands becoming mutating
- initialization metadata being mistaken for daemon liveness or readiness proof
- metadata writes occurring without explicit operator re-confirmation
- event records implying persistence or stronger authority than actually exists
- runtime initialization becoming an implicit launch path

The project therefore needs an ADR that captures the first accepted mutation boundary before later daemon work builds on top of it.

## Decision

Sayane accepts a minimal resident-daemon runtime initialization boundary with the following rules.

### 1. Runtime initialization is a separate command surface

Runtime layout preview remains non-mutating:

```bash
sayane app daemon-runtime-layout --json
```

Runtime initialization is a distinct command:

```bash
sayane app daemon-runtime-init
```

Preview commands must not become mutating by casually adding a flag.

### 2. The first accepted mutation slice is limited to local runtime-root preparation

The accepted initialization scope is:

- create runtime root
- create `pid/`
- create `lock/`
- create `socket/`
- create `log/`
- create `tmp/`
- create `state/`

This first slice does not authorize:

- PID writes
- lock acquisition
- socket binding
- daemon launch
- daemon stop or restart
- cleanup apply
- repair apply
- OS service integration

### 3. Initialization metadata is allowed only as a placeholder

The accepted metadata write is a single initialization placeholder at:

```text
state/runtime-init.json
```

Its purpose is to record initialization context, not runtime proof.

It must include a non-liveness disclaimer and must not be interpreted as:

- daemon existence proof
- daemon readiness proof
- API reachability proof
- PID ownership proof
- lock ownership proof

### 4. Metadata writing is stricter than directory creation

Directory creation is the first accepted filesystem mutation slice.

Metadata writing is a stronger Class 2 write and therefore requires extra consent.

Current accepted rule:

```text
--apply
+ optional directory creation

--apply + --write-metadata
+ requires matching --confirm-operation-id <operation-id>
+ requires matching --confirm-plan-fingerprint <fingerprint>
```

If either confirmation value does not match the previewed plan, the command must fail closed.

### 5. Audit shape must be visible before persistence grows

Runtime initialization preview/apply payloads must expose an audit-ready structure before any future persistent audit store exists.

The accepted shape includes:

- `operation_id`
- `plan_fingerprint`
- `creator_surface`
- `target_paths`
- `prior_state`
- `proposed_state`
- `operator_confirmation_signal`
- `mutations_performed`
- `result`
- `receipt`
- `failure_mode`
- `recovery_note`
- `confirm_operation_id`
- `confirm_plan_fingerprint`
- `confirmation_matched` when applicable
- `fingerprint_matched` when applicable

This is an audit-shaped payload, not yet an audit storage system.

### 6. Event records may be derived but are still schema-only

`daemon-runtime-init` may derive `resident_daemon_event_record` payloads for:

- preview
- apply

`daemon-runtime-init --apply` may also derive a schema-only runtime-init receipt payload.

These records and receipts remain schema-only and non-persistent unless a later ADR explicitly introduces persistent audit storage.

## Rationale

This decision preserves a narrow, inspectable transition from preview work into mutation work.

The boundary is intentionally asymmetric:

- directory creation is allowed with explicit apply
- metadata writing requires stricter confirmation
- process control remains entirely out of scope

That asymmetry is deliberate because metadata can create false authority even when no daemon exists.

Requiring matching `confirm_operation_id` and `confirm_plan_fingerprint` makes the operator repeat both the exact operation identity and the reviewed plan basis before the command writes a placeholder file that may later be read by other tools or humans.

Separating:

```text
runtime layout preview
-> runtime init directory creation
-> runtime init metadata placeholder
-> future process / IPC / readiness behavior
```

keeps each claim visible and testable.

## Consequences

### Positive

- The first resident-daemon mutation slice remains local, explicit, and bounded.
- Metadata writes are harder to trigger accidentally than directory creation.
- Preview/apply payloads are already shaped for future auditability.
- Event-record integration stays consistent with the existing schema-only resident-daemon event model.
- Future daemon work has a clear architectural starting point.

### Negative

- The command surface becomes more verbose because metadata writing needs a second confirmation input.
- Some users may find the confirmation step redundant for local-only initialization.
- The project now has another intentionally incomplete boundary to maintain:
  - directory creation is implemented
  - metadata placeholder is implemented
  - actual daemon behavior remains unimplemented

## Rejected alternatives

### Allow metadata writes on plain `--apply`

Rejected because metadata is a stronger semantic claim than empty directory creation.

### Put metadata writing into `daemon-runtime-layout`

Rejected because preview commands must remain non-mutating.

### Write PID or readiness metadata in the first slice

Rejected because those would too easily be misread as runtime proof.

### Persist event records immediately

Rejected because persistent audit storage requires a separate decision covering retention, privacy, write-failure behavior, and authority boundaries.

## Scope

This ADR applies to the current OSS Sayane resident-daemon initialization surfaces:

- `sayane app daemon-runtime-init`
- runtime init metadata placeholder
- runtime-init event-record derivation

It does not authorize:

- process control
- IPC transport
- readiness signaling
- lock ownership execution
- PID lifecycle claims
- persistent audit storage
- OS service integration

## Validation

This decision is currently exercised through:

```bash
./.venv/bin/ruff check src tests
./.venv/bin/ruff format --check src tests
./.venv/bin/pytest -q \
  tests/test_resident_daemon_event_records.py \
  tests/test_resident_daemon_runtime_metadata.py \
  tests/test_resident_daemon_runtime_init.py \
  tests/test_resident_daemon_runtime_init_cli.py
```

## Related documents

- `/Users/tomyuk/Projects/Sayane/sayane/docs/architecture/resident-daemon-runtime-initialization-policy.md`
- `/Users/tomyuk/Projects/Sayane/sayane/docs/architecture/resident-daemon-runtime-init-command.md`
- `/Users/tomyuk/Projects/Sayane/sayane/docs/architecture/resident-daemon-runtime-init-metadata-schema.md`
- `/Users/tomyuk/Projects/Sayane/sayane/docs/architecture/resident-daemon-event-record-schema.md`

## RDE Note

The intended meaning delta is:

```text
first accepted resident-daemon mutation boundary
```

The key preservation rule is:

```text
initialization is not liveness
initialization is not readiness
metadata placeholder is not authority
event schema is not persistence
```
