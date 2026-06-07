# ADR-0002: Connect Sayane PRFAQ to Context Acceptance Architecture

Date: 2026-06-07T11:43:20+09:00
Status: Proposed

## Context

Sayane v1.0.5 established the Context Acceptance architecture. The v1.1 workstream added scoped context acceptance and related safeguards across MCP output, sidepanel review, package preview, and regression dashboards.

The project now needs a public-facing PRFAQ that explains Sayane without reducing it to an automatic AI memory tool or generic prompt manager.

The PRFAQ must preserve key architectural boundaries:

- Sayane does not automatically accept candidates.
- Sayane does not automatically reject candidates.
- External context is not memory.
- `scoped_accept` is not ordinary approval.
- MCP output is derived context, not the canonical profile.
- Package preview is not package import.
- Verified package is not automatic acceptance.
- Signatures are integrity evidence, not truth claims.
- Dashboard is observation, not enforcement.

## Decision

Add `docs/public/sayane-prfaq.md` as the canonical PRFAQ draft for public and internal messaging.

Connect this PRFAQ from the ADR layer so that future changes to public narrative remain aligned with the Context Acceptance architecture and RDE boundaries.

The PRFAQ is a narrative and positioning document. It is not a product specification and does not introduce new runtime behavior.

## Consequences

### Positive

- Provides a stable public explanation of Sayane.
- Reduces risk of describing Sayane as automatic AI memory.
- Clarifies scoped context acceptance and Trojan context risk.
- Gives README, Zenn, release notes, and business materials a common source.

### Negative / Trade-offs

- Requires maintenance when architecture changes.
- May become stale if not connected to release closure and roadmap documents.
- Public language must avoid overclaiming legal, trust, or truth guarantees.

## Links

- `docs/public/sayane-prfaq.md`
- `docs/release/phase6-17-release-closure.md`
- `docs/public/sayane-context-acceptance-narrative.md`
- `docs/architecture/sayane-context-acceptance-architecture.md`
- `docs/design/scoped-context-acceptance.md`
- `docs/mcp/scoped-context-output.md`
- `docs/package/import-preview.md`
- `docs/reports/transfer-regression-html-dashboard.md`

## RDE consistency check

### Preserved

- Sayane remains a candidate, review, lineage, audit, and handoff system.
- Human review remains the final acceptance boundary.
- External context is not treated as memory.
- Scoped context remains scoped.
- Signatures remain integrity evidence, not truth claims.

### Transformed

- Internal architecture and release closure are transformed into public-facing explanation.

### Complemented

- PRFAQ becomes a shared source for README, Zenn, release notes, and business explanations.

### Intentionally unresolved

- Cross-instance audit import.
- Encrypted export package.
- Organization key trust model.
- Remote registry.
- Legal non-repudiation.

### Deviation risks

- Public narrative may overclaim automatic judgement.
- `scoped_accept` may be mistaken for full approval.
- Verified package may be mistaken for automatic acceptance.
- Signing may be mistaken for truth proof.

### Next update policy

- Update PRFAQ when public positioning changes.
- Keep ADR connection so narrative changes are reviewed as architecture-affecting changes.
