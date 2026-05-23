# RDE / Candidate 評価マニュアル

Phase 4 の Candidate Update 評価・承認フロー。Level 0–1 はヒューリスティック、Level 2–3 は任意の LLM-as-a-Judge。

設計: [evaluation-lineage.md](evaluation-lineage.md)

## 1. フロー

```text
capture → Candidate Update → evaluate (RDE+UIB) → approve / reject → lineage
```

- **capture**: Bridge / Extension → `~/.omomuki/candidates/*.json`
- **merge**: `approve` のみ
- **knowledge.concepts**: `--force-critical` なしで merge 可
- **critical section**（values, voice, policy, roles）: `--force-critical` が必要
- **identity.name / preferred_name**: 自動 merge 不可（手動編集）

## 2. CLI

```bash
omomuki candidate list
omomuki candidate show <id>
omomuki candidate evaluate <id>              # Level 1（既定）
omomuki candidate evaluate <id> --level 2    # + ローカル LLM judge
omomuki candidate evaluate <id> --level 3    # + 外部 API（要 API key）
omomuki candidate diff <id>
omomuki profile diff --candidate <id>
omomuki candidate approve <id>
omomuki candidate approve <id> --force-critical
omomuki candidate reject <id> --reason "..."
omomuki candidate lineage --profile-id default
```

## 3. 評価レベル

| Level | 内容 |
|-------|------|
| 0 | スキーマ検証（load 時） |
| 1 | ヒューリスティック RDE + UIB（既定） |
| 2 | Level 1 + ローカル LLM judge（Ollama 等） |
| 3 | Level 1 + 外部 OpenAI 互換 API |

LLM judge の設定: `~/.omomuki/judge.yaml` または環境変数 `OMOMUKI_JUDGE_BASE_URL`, `OMOMUKI_JUDGE_API_KEY`, `OMOMUKI_JUDGE_MODEL`。例は [examples/judge.yaml.example](../examples/judge.yaml.example)。

ヒューリスティックと LLM の RDE 分類が異なる場合、**より保守的（厳しい）方**を採用する。

## 4. RDE 分類（ヒューリスティック）

| 分類 | 目安 |
|------|------|
| Inferred Extension | 知識概念への非破壊的追加（既定） |
| Unresolved Gap | 短文・提案なし |
| Suspicious Drift | 断定的・命令的表現 |
| Critical Distortion | secret / critical section 言及 |

`Critical Distortion` は通常 **approve 不可**。`--force-critical` でも identity.name は merge 不可。

## 5. UIB スコア

0.0–1.0 の 6 軸（UD, MI, CH, DT, VP, FG）。Level 2+ では LLM が UIB を返した場合に上書きされる。

## 6. Merge 対象セクション

| section | approve | --force-critical |
|---------|---------|------------------|
| knowledge.concepts | 可 | 可 |
| values.core | 不可 | 可 |
| voice.tone | 不可 | 可 |
| policy.response.avoid / prefer | 不可 | 可 |
| identity.roles | 不可 | 可 |
| identity.name | 不可 | 不可 |

## 7. Lineage

`~/.omomuki/lineage/<profile_id>.jsonl` に approve / reject イベントを追記。

## 8. バージョン

Omomuki **0.5.1**（Phase 4 拡張）
