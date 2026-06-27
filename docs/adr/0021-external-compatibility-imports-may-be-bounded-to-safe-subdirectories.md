# ADR 0021: External Compatibility Imports May Be Bounded to Safe Subdirectories

## Status

Accepted

## Date

2026-06-28

## Context

P3 already made mutating external integrations explicit legacy compatibility
workflows, added export artifact metadata, and bounded export targets to safe
subdirectories.

Import still benefited from a similar narrowing step: operators should be able
to import from one explicit compatibility subtree instead of scanning an entire
external vault.

## Decision

Compatibility import may be bounded with:

`--source-subdir`

That subdirectory uses the same safety rules as compatibility export targets:

1. relative path only
2. no empty, `.`, or `..` segments
3. no hidden or reserved directories such as `.obsidian`, `.git`,
   `node_modules`, or dot-prefixed names

## Consequences

### Positive

- import can target only the intended compatibility subtree
- supported and forbidden external path rules now align between export and
  import

### Negative

- more CLI surface area to document

## Related

- `docs/adr/0020-external-compatibility-export-targets-must-stay-in-bounded-subdirectories.md`
- `docs/storage-manual.md`
