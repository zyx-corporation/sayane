# ADR 0026: Explicit review-queue import command for vault-aware packages

## Status

Accepted — 2026-06-28

## Context

ADR 0024 fixed that `sayane storage import-package` must remain preview-only and
that any future mutating intake must be a separate explicit workflow.

P3 still needed that separate workflow, otherwise operators could preview a
package but had no first-class path to turn it into pending review work without
reconstructing the package as ad hoc captures.

## Decision

Sayane adds:

- `sayane storage queue-package <dir>`

This command:

1. verifies the package
2. parses the provenance-aware `bundle.yml`
3. creates pending `CandidateUpdate` records
4. persists those candidates into the review queue
5. does **not** mutate the profile

The command is explicit and separate from `import-package`, so the preview-only
meaning of `import-package` remains stable.

## Consequences

Positive:

- package review can proceed with first-class pending candidates
- preview-only and queue-import semantics are clearly separated
- future UI flows can target the same explicit queueing boundary

Negative:

- operators now choose between two adjacent commands
- this still stops before merge; approval remains a separate step

## Related

- `docs/adr/0024-preview-only-import-package-contract-and-permanent-legacy-external-workflows.md`
- `docs/storage-manual.md`
