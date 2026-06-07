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

The PRFAQ also needs to remain testable as part of Sayane's T-RDE discipline. T-RDE here means treating public narrative, documentation, and release positioning as surfaces where meaning drift can occur. The PRFAQ should therefore be reviewed not only for readability, but also for whether it preserves the intended boundaries of the implementation.

## Decision

Add `docs/public/sayane-prfaq.md` as the canonical PRFAQ draft for public and internal messaging.

Connect this PRFAQ from the ADR layer so that future changes to public narrative remain aligned with the Context Acceptance architecture and RDE boundaries.

Treat PRFAQ updates as T-RDE-relevant documentation changes. A PRFAQ change may be documentation-only, but it can still alter the public meaning of Sayane. Changes should therefore be checked for boundary preservation, overclaiming, scope loss, and accidental conversion of reviewable candidates into automatic memory.

The PRFAQ is a narrative and positioning document. It is not a product specification and does not introduce new runtime behavior.

## Consequences

### Positive

- Provides a stable public explanation of Sayane.
- Reduces risk of describing Sayane as automatic AI memory.
- Clarifies scoped context acceptance and Trojan context risk.
- Gives README, Zenn, release notes, and business materials a common source.
- Adds a T-RDE anchor for public narrative review.

### Negative / Trade-offs

- Requires maintenance when architecture changes.
- May become stale if not connected to release closure and roadmap documents.
- Public language must avoid overclaiming legal, trust, or truth guarantees.
- Documentation-only changes may require architectural review when they affect boundary language.

## T-RDE documentation check

PRFAQ changes should be reviewed with the following T-RDE questions:

- Does the text preserve the human review boundary?
- Does it avoid describing Sayane as automatic memory?
- Does it avoid implying automatic candidate acceptance or rejection?
- Does it keep `scoped_accept` distinct from ordinary approval?
- Does it preserve the distinction between canonical profile and derived MCP output?
- Does it avoid treating package preview or verification as import or acceptance?
- Does it treat signatures as integrity evidence, not truth claims?
- Does it keep dashboard/reporting as observation, not enforcement?
- Does it avoid promoting partial context into global context without review?
- Does it clearly mark intentionally unresolved capabilities as unresolved?

A PRFAQ update should be considered unsafe if it turns an implementation boundary into a product promise, or if it describes a review aid as an autonomous decision mechanism.

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
- T-RDE remains applicable to public narrative and documentation, not only runtime behavior.

### Transformed

- Internal architecture and release closure are transformed into public-facing explanation.
- T-RDE is extended to PRFAQ and public positioning review.

### Complemented

- PRFAQ becomes a shared source for README, Zenn, release notes, and business explanations.
- ADR-0002 provides a T-RDE checklist for narrative changes.

### Intentionally unresolved

- Cross-instance audit import.
- Encrypted export package.
- Organization key trust model.
- Remote registry.
- Legal non-repudiation.
- Automated documentation scoring.

### Deviation risks

- Public narrative may overclaim automatic judgement.
- `scoped_accept` may be mistaken for full approval.
- Verified package may be mistaken for automatic acceptance.
- Signing may be mistaken for truth proof.
- T-RDE may be mistaken for an automatic truth or quality oracle.

### Next update policy

- Update PRFAQ when public positioning changes.
- Keep ADR connection so narrative changes are reviewed as architecture-affecting changes.
- Apply T-RDE review to PRFAQ, README, release notes, and public articles when they describe Sayane's boundaries.
