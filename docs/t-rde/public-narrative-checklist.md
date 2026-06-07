# T-RDE Public Narrative Checklist

Use this checklist for README, PRFAQ, release notes, Zenn articles, and public explanations about Sayane.

## Required Checks

- [ ] Does the text avoid describing Sayane as automatic memory?
- [ ] Does the text preserve the human review boundary?
- [ ] Does it avoid implying automatic candidate acceptance or rejection?
- [ ] Does it keep `scoped_accept` distinct from ordinary `approve`?
- [ ] Does it preserve the distinction between canonical profile and derived MCP output?
- [ ] Does it avoid treating package preview or verification as import or acceptance?
- [ ] Does it treat signatures as integrity evidence, not truth claims?
- [ ] Does it keep dashboards and reports as observation, not enforcement?
- [ ] Does it avoid promoting partial context into global context without review?
- [ ] Does it clearly mark unresolved capabilities as unresolved?

## Unsafe Patterns

| Unsafe | Safe |
|---|---|
| "Sayane remembers your context automatically." | "Sayane imports context as reviewable candidates." |
| "Verified packages can be imported safely without review." | "Package preview shows what is inside a package before import." |
| "scoped_accept means approved." | "scoped_accept means conditionally accepted within a declared scope." |
| "The dashboard enforces safety." | "The dashboard observes and reports transfer status." |
| "Signature proves truth." | "Signature provides integrity evidence." |
| "MCP output is the profile." | "MCP output is a target-specific derived context, not the canonical profile." |

## Boundary Statements (必ず守る)

- Sayane は候補を自動承認しない。
- Sayane は候補を自動棄却しない。
- Sayane は取り込まれた文脈の真偽を自動判定しない。
- Sayane は外部 profile を memory として扱わない。
- 署名は真実性の証明ではなく改ざん検出のための整合性証拠である。
- verified package は自動受容ではなく検証可能な handoff 単位である。
- Dashboard は観測面であり、制御面ではない。
- T-RDE は自動的な真理判定装置ではない。
