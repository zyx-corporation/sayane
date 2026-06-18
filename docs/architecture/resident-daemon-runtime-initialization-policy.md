# Resident Daemon Runtime Initialization Policy

Status: Future mutation policy

Related issues: #198, #211, #216

## Summary

This document defines the policy for future resident daemon runtime initialization.

Runtime initialization is the boundary between planning a runtime layout and actually creating filesystem state.

Current Sayane commands can preview the runtime layout but do not create directories, write metadata, write PID files, acquire locks, create sockets, or launch a daemon.

## Core rule

Runtime layout preview must remain non-mutating.

The existing command:

```bash
sayane app daemon-runtime-layout --json
```

must not initialize runtime directories or files.

A future runtime initialization command must be separate, explicit, auditable, and operator-authorized.

## Future command naming

A future initialization command should use an explicit mutating name, for example:

```bash
sayane app daemon-runtime-init
```

or:

```bash
sayane app daemon-runtime-init-apply
```

Preview commands must not become mutating by adding a casual flag.

## Initialization scope

Future runtime initialization may include only explicitly authorized operations such as:

- create runtime root
- create planned runtime subdirectories
- create empty log directory
- create empty state directory
- create initial metadata placeholders

It must not implicitly:

- write PID files
- acquire locks
- create sockets
- start a daemon
- install OS services
- delete or repair existing artifacts

Those are separate policies and commands.

## Runtime root validation

Future initialization must validate that every target path is under the runtime root.

It must reject:

- path traversal
- symlink escape where applicable
- absolute child paths where not expected
- runtime roots owned by an unexpected user
- conflicting file where a directory is expected
- conflicting directory where a file is expected

## Existing artifacts

Initialization must fail closed when an existing artifact is ambiguous.

Examples:

```text
missing directory -> may create with explicit consent
existing correct directory -> no_action
existing file where directory expected -> manual_review_required
existing symlink -> manual_review_required unless policy explicitly permits it
existing non-empty directory -> review_required for destructive changes
```

Initialization must not perform cleanup or repair as a side effect.

## Metadata creation

Initial metadata creation must not imply daemon liveness, readiness, or ownership.

Metadata should be labeled as initialization metadata, not runtime proof.

Any future metadata should include:

- schema version
- runtime root
- creation time
- creator surface
- preview/apply operation id
- non-liveness disclaimer if appropriate

## Operator consent

Future initialization requires explicit operator intent.

Acceptable future consent patterns may include:

```text
--apply
--confirm <preview-hash>
--operation-id <id>
interactive typed confirmation
```

Default invocation should be dry-run or fail without explicit apply intent.

## Audit record

Future initialization must emit a local audit record containing:

- command name
- operation id
- runtime root
- target paths
- prior state
- proposed state
- operator confirmation signal
- mutations performed
- result
- failure mode if any
- recovery note when applicable

## Relationship to daemon launch

Runtime initialization is not daemon launch.

A successfully initialized runtime root does not prove:

- daemon exists
- daemon is running
- daemon is ready
- API is reachable
- process identity is verified

Daemon launch and process control require separate policy.

## RDE Delta-M Review

### Preserved

Runtime layout preview remains non-mutating.

Filesystem mutation remains explicitly separated from diagnostics.

### Supplemented

The roadmap now defines the boundary between layout planning and runtime initialization.

### Deviation Risks

Do not let `daemon-runtime-layout` create directories.

Do not let initialization write PID, lock, or socket artifacts.

Do not treat initialized directories as daemon readiness evidence.
