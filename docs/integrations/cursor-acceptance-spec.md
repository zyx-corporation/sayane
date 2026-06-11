# Cursor Acceptance Specification

## Status

Acceptance specification.

This document defines the acceptance conditions for Sayane's Cursor MCP integration. It is a companion to the [Cursor Integration Concept](cursor.md).

## Purpose

The Cursor acceptance spec defines concrete, verifiable conditions that must be met before Cursor integration is considered complete. It translates the architectural boundaries defined in the concept document into testable gates.

## Acceptance Gates

### Gate 1: Derived Context Boundary

**Condition:** Sayane must send derived context to Cursor through MCP, never the canonical profile itself.

Verification:

- [ ] MCP output contains only compiled, scoped, filtered context
- [ ] Canonical Sayane Profile is never exposed as raw output through MCP
- [ ] Every MCP response includes scope metadata (target, valid-until, constraints)

### Gate 2: Scoped Context Integrity

**Condition:** When Sayane sends project-scoped or task-scoped context to Cursor, the scope boundary must be preserved.

Verification:

- [ ] Project-scoped context is not promoted to global context by Cursor-side processing
- [ ] Scope metadata is attached to every derived context fragment
- [ ] Expired or out-of-scope context is not re-presented after the scope closes

### Gate 3: Candidate Gate

**Condition:** Every Cursor-originated change that could affect Sayane Profile or context must pass through Candidate Update before merge.

Verification:

- [ ] Cursor agent output is never auto-merged into the canonical profile
- [ ] Every captured change is wrapped as a Candidate Update with provenance metadata
- [ ] Candidates carry a source label indicating Cursor origin
- [ ] Candidates are queued for review, not applied immediately

### Gate 4: Cursor Rules Boundary

**Condition:** Cursor Rules must not be treated as, or promoted to, canonical Sayane Profile.

Permitted Cursor Rules content:

- [ ] Workspace-local conventions (formatting, lint rules, project structure)
- [ ] Task-specific tool preferences within the workspace
- [ ] Temporary session-level instructions scoped to a task

Prohibited Cursor Rules content:

- [ ] Personal values, communication style, or identity preferences
- [ ] Global context policies that should live in Sayane Profile
- [ ] Derived persona information extracted from Sayane Profile without review

### Gate 5: Agent Output Review

**Condition:** Cursor agent output must be reviewed before it can become accepted knowledge.

Verification:

- [ ] Agent output is captured as derived output, not as profile material
- [ ] Human review is required before any agent output is promoted to Candidate
- [ ] Unreviewed agent output is marked as provisional and expires after the session
- [ ] Rejected output is logged with rejection reason and not silently discarded

### Gate 6: RDE / UIB Evaluation

**Condition:** Every Candidate originating from Cursor must pass RDE / UIB evaluation.

Evaluation criteria:

- [ ] **Intent preservation:** What original intent does the change preserve?
- [ ] **Intent transformation:** What original intent does the change transform, and why?
- [ ] **Context addition:** What new context does the change introduce?
- [ ] **Unresolved elements:** What remains ambiguous or unresolved?
- [ ] **Deviation risk:** What risk does the change introduce to Sayane's meaning model?
- [ ] **Scope validity:** Is the change local, project-scoped, or globally valid?
- [ ] **Uncertainty assessment (UIB):** Is the change based on minimum necessary context? Are multiple hypotheses considered? What failure modes exist?

### Gate 7: Repository Boundary

**Condition:** Cursor-specific implementation must not pollute Sayane Core.

Verification:

- [ ] Cursor-specific code exists only in documented integration modules
- [ ] Sayane Core has no import or dependency on Cursor-specific logic
- [ ] Cursor integration can be disabled or removed without breaking Core functionality

## Split Condition

A separate `sayane-cursor` repository should be created when **any** of the following thresholds are met:

| Threshold | Description |
|-----------|-------------|
| Extension size | Cursor-specific extension code exceeds 500 lines |
| Core pollution | Cursor assumptions begin to leak into Sayane Core interfaces |
| Rules generator | A dedicated Cursor Rules generator module is required |
| Agent log adapter | Cursor agent log capture requires Cursor-specific adapter logic |
| Workspace diff adapter | Workspace diff capture requires Cursor-specific parsing |
| UI integration | Cursor-specific UI surfaces are required beyond MCP |

Until none of these thresholds is met, Cursor integration remains within the main `sayane` repository.

## Validation Sequence

When Cursor MCP integration is implemented, the following sequence must be executed:

1. **Derived context compile test:** Verify MCP output is derived, not canonical
2. **Scope boundary test:** Verify scoped context does not leak beyond its boundary
3. **Candidate gate test:** Capture Cursor agent output and verify it enters Candidate queue
4. **Rules boundary test:** Attempt to promote Cursor Rules to Profile and verify rejection
5. **Agent output review test:** Verify unreviewed output expires and reviewed output becomes Candidate
6. **RDE / UIB test:** Run RDE / UIB evaluation on a Cursor-originated Candidate
7. **Core isolation test:** Disable Cursor integration and verify Core operates normally

## Non-Goals

The following are explicitly not acceptance requirements at this stage:

- Building a Cursor-specific extension or plugin
- Implementing a Cursor Rules generator
- Capturing Cursor agent logs in real time
- Displaying Sayane context inside Cursor UI
- Bidirectional sync between Cursor and Sayane

These are deferred to the `sayane-cursor` repository if and when it is created.

## Core Statement

```text
Cursor output is provisional until review.
Sayane context is canonical until explicitly changed.
Nothing crosses the boundary without a candidate, a review, and a record.
```
