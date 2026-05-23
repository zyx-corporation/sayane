# RDE / Candidate 評価マニュアル

Phase 4 の Candidate Update 評価・承認フロー（Level 0–1: ヒューリスティック、LLM なし）。

設計: [evaluation-lineage.md](evaluation-lineage.md)

## 1. フロー

```text
capture → Candidate Update → evaluate (RDE+UIB) → approve / reject → lineage
```

- **capture**: Bridge / Extension → `~/.omomuki/candidates/*.json`
- **merge**: `approve` のみ。`knowledge.concepts` への追加が MVP 範囲
- **critical section**（identity, values, policy, voice）への自動 merge は不可

## 2. CLI

```bash
omomuki candidate list
omomuki candidate show <id>
omomuki candidate evaluate <id>
omomuki candidate diff <id>
omomuki profile diff --candidate <id>
omomuki candidate approve <id>
omomuki candidate reject <id> --reason "..."
omomuki candidate lineage --profile-id default
```

## 3. RDE 分類（ヒューリスティック）

| 分類 | 目安 |
|------|------|
| Inferred Extension | 知識概念への非破壊的追加（既定） |
| Unresolved Gap | 短文・提案なし |
| Suspicious Drift | 断定的・命令的表現 |
| Critical Distortion | secret / critical section 言及 |

`Critical Distortion` は **approve 不可**（手動編集を推奨）。

## 4. UIB スコア

0.0–1.0 の 6 軸（UD, MI, CH, DT, VP, FG）。Phase 4 は参考値であり、自動 merge の唯一の判定には使わない。

## 5. Lineage

`~/.omomuki/lineage/<profile_id>.jsonl` に approve / reject イベントを追記。

## 6. バージョン

Omomuki **0.4.0**（Phase 4 MVP）
