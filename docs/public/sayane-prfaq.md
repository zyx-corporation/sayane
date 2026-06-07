# Sayane PRFAQ: Context Acceptance and Verifiable Handoff

Created: 2026-06-07T11:43:20+09:00
Status: draft
Target release line: v1.1 after Sayane 1.0.5

## Press Release

### Sayane: local-first context acceptance for the LLM era

ZYX Corp announces Sayane, a local-first context acceptance foundation for users who work across multiple LLMs and AI tools.

Sayane is designed for people who use ChatGPT, Claude, Cursor, Open WebUI, and other AI environments while needing to preserve their own context without turning every useful AI response into long-term memory.

Prompt management can store reusable text. Sayane handles something different: the process by which context is brought back as a candidate, reviewed by a human, accepted or rejected with reasons, audited, verified, signed, and handed off.

Sayane does not automatically memorize LLM output. It imports external context as reviewable candidates. A candidate may be approved, rejected, modified, deferred, or accepted only within a specific scope.

The v1.1 line strengthens this architecture with scoped context acceptance. Some context is useful only within a project, article, session, or note. If that condition is lost, local context can become a Trojan context: harmless in one place, dangerous when promoted into global profile context.

Sayane therefore records scope, conditions, negative constraints, promotion policy, and reuse policy for scoped context. It preserves those boundaries through review, audit, MCP output, package preview, and regression dashboards.

Sayane is not an automatic memory system. It is a candidate, review, lineage, provenance, policy, and handoff system that keeps human review at the center.

## FAQ

### Q1. What is Sayane?

Sayane is a local-first context acceptance system for LLM workflows.

It helps users handle context generated through LLM interactions as reviewable candidates rather than automatic memory. A candidate can be reviewed, approved, rejected, modified, deferred, or accepted only within a specific scope.

### Q2. How is Sayane different from prompt management?

Prompt management stores reusable prompt text.

Sayane manages the lifecycle of context: where it came from, how it changed, where it is proposed to go, whether it conflicts with existing context, how a human reviewed it, and how that decision can later be audited.

### Q3. Is Sayane an AI memory system?

No.

Sayane is intentionally not an automatic AI memory system. It is designed to prevent AI-generated text or inferred profile fragments from silently becoming long-term memory.

External context is imported as a candidate, not as memory.

### Q4. Why does Sayane use candidates?

Because useful LLM output is not automatically safe context.

A response may be locally useful but too broad for a global profile. It may be based on a temporary conversation. It may overstate a preference, turn a hypothesis into a fact, or move project-specific context into a general rule.

Candidates create a review boundary before context is accepted.

### Q5. What is `scoped_accept`?

`scoped_accept` is scoped acceptance.

It is used when context is useful only under specific conditions. Instead of approving it as a general profile update, Sayane records the accepted scope, conditions, negative constraints, promotion policy, and reuse policy.

Example:

```yaml
decision: scoped_accept
accepted_scope:
  level: project
  target: zenn-sayane-series
  sub_scope: article-02-introduction
conditions:
  - Use only to raise reader awareness in this article introduction.
negative_constraints:
  - Do not treat as global writing preference.
  - Do not treat as identity.
promotion_policy:
  can_promote: false
reuse_policy:
  review_on_reuse: true
```

### Q6. What is Trojan context risk?

Trojan context risk occurs when locally valid context loses its scope or conditions and enters broader context as if it were globally valid.

For example:

```text
Local context:
  In the introduction of Zenn article 2, a stronger problem statement is acceptable.

Unsafe promotion:
  The user generally prefers strong aggressive writing.
```

The first statement may be valid in one article. The second is an unsafe global inference.

### Q7. How does Sayane prevent scoped context from leaking through MCP output?

Sayane treats MCP output as derived context, not as the canonical profile.

When scoped context is included in compiled MCP output, Sayane preserves scope, conditions, negative constraints, and reuse policy. It must not emit project-scoped context as a global instruction unless a new review decision explicitly promotes it.

### Q8. What is Package Import Preview?

Package Import Preview lets a user inspect an external Sayane export package before any future import.

It shows package artifacts, hash and signature status, audit decisions, scoped context, conditions, negative constraints, policy results, and risk summaries.

Preview is not import. Verified package is not automatic acceptance.

### Q9. What does the Transfer Regression HTML Dashboard do?

It provides a static observation surface for transfer regression status, scoped context risks, MCP boundary checks, package preview risks, bundle verification, signature status, and audit decisions.

The dashboard is observation, not enforcement. It does not auto-fix, auto-approve, or auto-import anything.

### Q10. What does Sayane not do?

Sayane does not:

- automatically accept candidates
- automatically reject candidates
- judge truth automatically
- treat external profiles as memory
- treat signatures as truth claims
- treat verified packages as automatic acceptance
- promote scoped context to global context without review
- replace human review with LLM judgement

### Q11. Who is Sayane for?

Sayane is for developers, researchers, writers, and teams who work across multiple LLMs and AI tools and need a local-first way to preserve, review, audit, and reuse context safely.

It is especially useful for users moving between ChatGPT, Claude, Cursor, Open WebUI, MCP clients, and local workflows.

### Q12. What is the business value?

As AI workflows become more complex, the question is not only what the AI generated. The question becomes:

- What context was used?
- Where did it come from?
- Who accepted it?
- Under what conditions?
- What was rejected?
- What was scoped?
- Can the handoff be verified?

Sayane provides an auditable foundation for these questions.

## Internal FAQ

### Q13. Why write a PRFAQ now?

Because Sayane is easy to misunderstand.

Calling it an AI memory tool is too simple and misleading. Calling it a full context governance system may sound too abstract. PRFAQ fixes the public narrative and preserves architectural boundaries.

### Q14. What is the simplest public message?

Sayane helps people bring context back from AI conversations as reviewable candidates, not automatic memory.

### Q15. What is the strongest technical differentiation?

Scoped context acceptance.

Sayane does not merely store context. It records where the context is valid, what conditions apply, what interpretations are forbidden, and whether reuse requires review.

### Q16. What is the biggest RDE risk?

Sayane itself could become a carrier of Trojan context if scope, conditions, or negative constraints are dropped during reuse.

F-1.5 to F-5 address that risk across review decisions, MCP output, sidepanel review, package preview, and regression dashboard visibility.

### Q17. What should be published first?

After documentation alignment:

1. Zenn article 2: Chrome Extension as candidate capture entrypoint
2. Zenn article 3: MCP Server as scoped context output
3. Special article: Sayane context acceptance architecture
4. PRFAQ-derived public overview

### Q18. What remains intentionally unresolved?

- actual package import
- cross-instance audit import
- encrypted export package
- organization key trust model
- remote registry
- legal non-repudiation model
- full production GUI

## Boundary statements

- Sayane is not automatic memory.
- Candidates are not accepted context.
- `scoped_accept` is not ordinary approval.
- MCP output is not the canonical profile.
- Package preview is not package import.
- Verified package is not automatic acceptance.
- Signatures are integrity evidence, not truth claims.
- Dashboard is observation, not enforcement.

## RDE consistency check

### Preserved

- Human review remains the final acceptance boundary.
- Candidate gate remains central.
- External context is not treated as memory.
- Signatures are treated as integrity evidence, not truth claims.
- Verified packages are handoff / preview units, not acceptance units.

### Transformed

- Public explanation shifts from context portability to context acceptance.
- Partial context handling is reframed as scoped acceptance.

### Complemented

- PRFAQ narrative.
- Scoped context risk framing.
- Product and business positioning.

### Intentionally unresolved

- Cross-instance audit import.
- Encrypted export package.
- Organization key trust model.
- Remote registry.
- Legal non-repudiation.

### Deviation risks

- Sayane may be misunderstood as AI memory.
- `scoped_accept` may be misunderstood as full approval.
- Package verification may be mistaken for import.
- Signing may be mistaken for truth proof.

### Next update policy

- Keep boundary statements visible in public documents.
- Keep scoped context and human review central.
- Do not describe Sayane as automatic memory.
