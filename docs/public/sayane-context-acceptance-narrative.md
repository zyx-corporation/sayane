# Sayane: From Context Portability to Context Acceptance

> **Abstract**: Sayane is not a prompt manager. It is a context acceptance and verifiable handoff system that treats imported context as reviewable candidates, not as memory.

---

## 1. なぜプロンプト管理では足りないのか

LLM に「このユーザーについての情報」をプロンプトとして渡すだけでは、以下の問題が解決しない。

- 渡した文脈が正しく保存されたか分からない
- 別の LLM に渡すと語は残っても意味配置が揺れる
- 人間の判断なしに文脈が上書きされる
- 誰がいつ何を承諾したか追跡できない
- 外部へ渡した文脈束が改ざんされていないか検証できない

## 2. 文脈は「記憶」ではなく「候補」として戻る

Sayane では、外部から取り込まれた文脈は直接保存されない。

```text
Import → Candidate → Semantic Review → Human Decision → Stored Context (with lineage)
```

すべての取り込みは候補（Candidate）として扱われ、人間の明示的な判断（approve / reject / modify / defer）を経て初めて保存される。

## 3. LLM をまたぐと、語は残っても意味配置は揺れる

A2 ラウンドトリップで観測された現象:

- `RDE` と `Sayane` は語として保存された
- しかし `technical.preferences` と `principles` の間で配置が揺れた
- Phase 6 で semantic review によりこの揺れを検出できるようにした

## 4. Sayane が行うこと

| 機能 | 説明 |
|---|---|
| Candidate 化 | 外部文脈を直接保存せず候補にする |
| Semantic Review | 意味重複・不安定配置・境界侵犯を検出 |
| Human Review | approve / reject / modify / defer |
| Audit Trail | 判断を append-only で保存 |
| Provenance | 文脈束の由来・hash・同一性を検証 |
| Policy | strict/standard/legacy/development + custom files |
| Decision Diff | 判断前後の差分を表示 |
| Audit Export | markdown/json/jsonl で監査記録を出力 |
| Cryptographic Signing | Ed25519 で artifact を署名 |
| Signed Package | 文脈・監査・方針・レポートを検証可能な package に |

## 5. Sayane が行わないこと

- 候補を自動承認しない
- 候補を自動棄却しない
- 文脈の真偽を自動判定しない
- 外部 profile を memory として扱わない
- 署名を真実性の証明として扱わない
- verified package を自動受容として扱わない

## 6. 文脈受容アーキテクチャとしての Sayane

```
外部文脈 → Candidate → Semantic Review → Human Decision → Audit Trail
                ↑                          ↑
         Provenance Verification    Policy Profiles

Audit Trail → Decision Diff → Audit Export → Signing → Signed Package
```

Sayane は、文脈を「保存する」だけでなく「引き受ける」ための基盤である。

引き受けるとは、由来を確認し、警告を見て、判断し、その判断の来歴ごと移送可能にすることである。

## 7. 関連文書

- `docs/release/phase6-17-release-closure.md`
- `docs/architecture/sayane-context-acceptance-architecture.md`
- `docs/reference/cli-command-reference.md`
