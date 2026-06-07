# MCP Scoped Context Output (F-2)

## Purpose

MCP output must preserve scope, conditions, and negative constraints when context was accepted through `scoped_accept`.

## Boundary

MCP output is not the canonical profile. It is a target-specific compiled context.

## Rules

- Do not emit `scoped_accept` context as global instruction.
- Do not drop negative constraints.
- Do not drop `review_on_reuse`.
- Do not treat project-limited context as global preference.

## Modes

| Mode | Behavior |
|---|---|
| `full` | All scope/conditions/constraints/promotion/reuse included |
| `compact` | Minimal scope note, conditions/constraints summarized |
| `strict` | Scoped context omitted entirely (out-of-scope) |

## CLI

```bash
sayane context-compile --target cursor --mode full
sayane context-compile --target cursor --mode compact
sayane context-compile --target cursor --mode strict
sayane context-compile --target cursor --show-scope
```

## Principle

```text
MCPで渡す文脈はProfile正本ではない。
対象ツール向けにcompileされた派生文脈である。
scoped_acceptされた文脈を出力する場合、scope、conditions、negative_constraintsを保持しなければならない。
```
