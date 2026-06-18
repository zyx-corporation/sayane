# Resident Daemon Cleanup Apply Command Policy

Status: Future mutation policy

Related issues: #200, #211, #212

## Summary

This document defines the policy for any future resident daemon cleanup apply command.

Current cleanup decision commands are preview-only and non-mutating. They do not delete artifacts, repair artifacts, acquire locks, control processes, or create runtime paths.

## Core rule

Cleanup preview and cleanup apply must be separate surfaces.

The existing command:

```bash
sayane app daemon-cleanup-decisions --json
```

must remain non-mutating.

A future mutating cleanup command must use a distinct command name and must require explicit operator intent.

## Current cleanup decision boundary

Current cleanup decisions are conservative:

```text
missing -> no_action
present_review_required -> manual_review_required
type_mismatch_review_required -> unsafe_to_delete
```

No current decision reports an artifact as safe for automated deletion.

## Future command naming

A future cleanup apply command should use an explicit mutating name, for example:

```bash
sayane app daemon-artifact-cleanup-apply
```

or:

```bash
sayane app daemon-cleanup-apply
```

A preview command must not gain mutation behavior silently through a casual `--fix` flag.

## Required future flow

A future cleanup apply flow should be staged:

```text
1. diagnostic preview
2. cleanup decision preview
3. operator reviews preview output
4. apply command receives explicit operation target
5. apply command verifies preview hash or operation id
6. apply command revalidates evidence
7. apply command performs only authorized mutation
8. apply command writes audit record
```

## Preview hash or operation id

A future cleanup apply command should avoid acting on stale preview state.

Acceptable future mechanisms may include:

```text
preview_hash
operation_id
signed local approval
interactive typed confirmation
```

The apply command should re-read current artifact state before mutation and must abort if the evidence no longer matches the approved preview.

## Evidence thresholds

Future deletion or repair requires stronger evidence than artifact presence.

Examples:

```text
missing artifact -> no deletion
present artifact + no liveness evidence -> manual review, not automatic deletion
type mismatch -> unsafe to delete without stronger evidence
parsed PID only -> not enough to delete PID or signal process
process exists but identity unverified -> not enough to delete lock or socket
identity verified and daemon active -> do not delete owned artifacts
identity unverified and stale evidence ambiguous -> manual_review_required
```

## Artifact-specific policy

### PID file

A future cleanup apply command must not delete a PID file merely because the PID is parsed or unparsed.

Deletion requires evidence that the PID file is stale, not owned by an active Sayane daemon, and safe to remove.

### Lock file

Lock deletion or lock stealing requires special policy.

A lock artifact may be the only concurrency guard preventing two resident daemon instances from racing.

### Socket file

Socket deletion requires evidence that no active daemon owns the socket and that deleting it will not break an active IPC endpoint.

Socket presence is not identity proof, but socket deletion is still a mutation that may disrupt a process.

### Runtime directories

Runtime directory deletion is higher risk than single-artifact cleanup and should require a separate policy.

## Dry-run requirement

A future cleanup apply command should support a dry-run mode:

```bash
sayane app daemon-cleanup-apply --dry-run
```

Dry-run must perform no mutation and should show the exact proposed operations.

## Operator confirmation

A future mutating cleanup command should require explicit confirmation, such as:

```bash
sayane app daemon-cleanup-apply --operation-id <id> --confirm <preview-hash>
```

or an equivalent explicit mechanism.

The command should not perform mutation merely because it is invoked without a clear apply signal.

## Audit record

A future cleanup apply command must emit a local audit record containing:

- command name
- operation id
- preview hash or approval token
- runtime root
- artifact path
- artifact kind
- prior diagnostic status
- cleanup decision
- evidence inputs
- operator confirmation signal
- mutation attempted
- mutation result
- failure mode if any
- rollback or recovery note when possible

## Failure behavior

Future cleanup apply must fail closed.

It must abort when:

- evidence changes between preview and apply
- runtime root validation fails
- artifact path escapes runtime root
- process ownership is ambiguous
- lock ownership is ambiguous
- permissions are insufficient
- artifact type is unexpected
- platform behavior is unsupported

## Relationship to future repair

Cleanup and repair are distinct.

Deletion removes an artifact.

Repair changes or recreates an artifact.

A future repair command must have its own policy and must not be treated as a side effect of cleanup.

## RDE Delta-M Review

### Preserved

Cleanup decision previews remain non-mutating.

Ambiguous artifacts remain manual-review cases.

### Supplemented

The roadmap now defines a separate future execution surface for cleanup apply.

### Deviation Risks

Do not mutate from `daemon-cleanup-decisions`.

Do not treat current cleanup recommendations as deletion permission.

Do not skip preview-hash or revalidation steps before mutation.

Do not combine cleanup, repair, lock stealing, and process control into one convenience command.
