# Scoped Context Acceptance (F-1.5)

## Purpose

Scoped Context Acceptance prevents partial context from being promoted into global profile context without explicit review.

## Principle

```text
部分文脈を許容するだけでは足りない。
その文脈がどの範囲で有効で、どこへ昇格してはいけないかを保持しなければならない。
```

## Boundary

Scoped acceptance (`scoped_accept`) is not normal approval. It is conditional acceptance with:

- **accepted_scope**: the scope where this context is valid
- **conditions**: conditions under which the acceptance holds
- **negative_constraints**: what this context must NOT be treated as
- **promotion_policy**: whether and how this context can be promoted to wider scope
- **reuse_policy**: whether reuse requires re-review

## Trojan Context Risk

A locally valid context can become dangerous if its scope or condition is lost during reuse:

```
session scope → accepted with conditions
→ conditions dropped
→ reused as global instruction
→ next LLM treats it as global truth
```

Scoped acceptance guards against this by:
1. Making scope/conditions/constraints explicit
2. Requiring re-review for promotion
3. Preserving metadata in audit/export paths

## CLI

```bash
sayane review scoped-accept c-001 \
  --scope project:zenn-sayane-series:article-02-intro \
  --conditions "読者の問題意識を喚起する目的に限定,人格として扱わない" \
  --negative "global writing preference に昇格しない,scope注記を落とさない" \
  --reason "局所的には有用だが、全体方針としては過剰一般化の危険がある"
```

## Non-goals

- No automatic promotion.
- No automatic global profile update.
- No hidden reuse outside scope.
- No MCP output without scope note.
