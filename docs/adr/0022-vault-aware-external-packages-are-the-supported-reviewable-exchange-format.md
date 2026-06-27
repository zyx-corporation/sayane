# ADR 0022: Vault-aware external packages are the supported reviewable exchange format

## Status

Accepted — 2026-06-28

## Context

P3 re-designs external integrations after P2 moved high-sensitivity working
state onto vault-aware repositories.

At this point:

- Obsidian import / export and Git commit remain explicit legacy compatibility
  paths behind `--legacy-compatible`
- `storage export` writes non-canonical compatibility artifacts with retention
  and redaction metadata
- `storage import` can be bounded to safe subdirectories

What remained undefined was the supported reviewable exchange format for data
that may cross the local boundary without reopening the old “external vault is
the working store” model.

## Decision

Sayane defines a **vault-aware external package** as the supported reviewable
exchange format.

The package:

1. is a directory package with `manifest.json`
2. carries a provenance-aware `bundle.yml` as the reviewable context artifact
3. may carry a redacted `audit-export.json`
4. is marked as **non-canonical**
5. requires **review before merge**
6. is **not** a legacy compatibility path
7. carries explicit retention classes per artifact

The initial CLI surface is:

- `sayane storage export-package`
- `sayane storage import-package`

`import-package` is preview-only in this slice. It verifies the package and
renders candidate-style review output, but it does not mutate the profile and
does not persist candidates.

The preview-only contract and reserved future mutating path are fixed in:

- `docs/adr/0024-preview-only-import-package-contract-and-permanent-legacy-external-workflows.md`

The current retention classes are:

- `reviewable_context_bundle` — default `30d`
- `redacted_audit_export` — default `14d`

## Consequences

Supported direction:

- reviewable external exchange is package-based
- bundle provenance and package verification are preserved together
- import remains candidate/review first rather than direct merge
- retention guidance is explicit per artifact instead of implied by docs only

Not supported by this ADR:

- making Obsidian vaults canonical working stores again
- direct package import into profile state without review
- automatic external sync promotion

The explicit supported / forbidden workflow list is specified in:

- `docs/adr/0023-supported-and-forbidden-external-workflows-for-vault-aware-packages.md`

## Follow-up

- define a separate explicit review-queue import workflow, if needed
