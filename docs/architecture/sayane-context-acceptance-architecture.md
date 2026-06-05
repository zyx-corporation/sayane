# Sayene Context Acceptance Architecture

## Boundary Statements

- Sayane does not automatically accept candidates.
- Sayane does not automatically reject candidates.
- Sayane does not judge whether imported context is true.
- Sayane does not treat external profiles as memory.
- Sayane does not treat signatures as truth claims.
- Sayane does not treat verified packages as automatic acceptance.
- Sayane preserves human review boundaries.
- Sayane records rejected and deferred candidates as meaningful lineage.

### 境界宣言（日本語）

- Sayane は候補を自動承認しない。
- Sayane は候補を自動棄却しない。
- Sayane は取り込まれた文脈の真偽を自動判定しない。
- Sayane は外部 profile を memory として扱わない。
- Sayane は署名を真実性の証明として扱わない。
- Sayane は verified package を自動受容として扱わない。
- Sayane は人間の review 境界を保持する。
- Sayane は reject / defer された候補も意味ある来歴として残す。

## Layers

| Layer | Components |
|---|---|
| Context Transfer | export, import, round-trip bundles |
| Semantic Review | overlap, placement, boundary detection |
| Human Review | approve/reject/modify/defer with reason |
| Audit | append-only store, decision records, diff |
| Provenance | metadata, content hash, verification |
| Policy | built-in profiles, custom files, hard constraints |
| Review Surface | CLI show/list/overlap/diff |
| Export & Handoff | audit export, signing, signed packages |

## Diagrams

- [Overall Architecture](diagrams/context-acceptance-overview.md)
- [Review Decision Flow](diagrams/review-decision-flow.md)

## Related

- `docs/release/phase6-17-release-closure.md`
- `docs/public/sayane-context-acceptance-narrative.md`
- `docs/reference/cli-command-reference.md`
