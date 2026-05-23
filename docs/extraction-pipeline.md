# Conversation Extract / Reverse Compile Pipeline

## 1. 概要

Omomukiは、ProfileからLLM向けpromptを生成するだけでは不十分である。

LLMとの会話やWeb上の作業から新しい文脈が生まれた場合、それをどのようにOmomuki Profileへ戻すかが重要になる。

この逆方向の流れを、Conversation Extract / Reverse Compile Pipeline と呼ぶ。

```text
LLM Conversation / Web Context
  → Extractor
  → Candidate Update
  → RDE Diff
  → User Approval
  → Profile Merge
  → Lineage Record
```

## 2. なぜ必要か

LLMとの対話では、以下のような情報が生まれる。

- 新しいユーザー嗜好
- 新しいプロジェクト情報
- 新しい概念定義
- 既存Profileの訂正
- 一時的文脈
- 長期的に保持すべき文脈

これらをすべて自動的にProfileへmergeすると、Profile汚染が起きる。

一方で、すべて手作業で整理すると、文脈再説明コストが残る。

したがって、Omomukiでは、抽出は支援し、mergeは評価と承認を通す。

## 3. Extractorの役割

Extractorは、会話ログやWebコンテンツからProfile更新候補を抽出する。

ExtractorはProfileを直接変更しない。

出力はCandidate Updateである。

## 4. 抽出対象

### 4.1 User Preference

例:

- 文体の好み
- 出力形式の好み
- 技術スタックの好み
- 禁止したい表現

### 4.2 Project Context

例:

- 新規プロジェクト
- 既存プロジェクトの状態変化
- リポジトリ名
- 実装方針

### 4.3 Concept Definition

例:

- RDE
- UIB
- Kotonoha
- Omomuki
- 独自理論や用語

### 4.4 Correction

既存Profileの誤りを訂正する情報。

### 4.5 Ephemeral Context

短期的には有用だが、長期Profileには入れない情報。

## 5. Candidate Update形式

```yaml
id: "candidate-20260523-001"
source:
  type: "conversation"
  platform: "chatgpt"
  captured_at: "2026-05-23T00:00:00+09:00"
extractor:
  version: "0.1.0"
  mode: "heuristic"
target:
  profile: "default"
  section: "policy.response.prefer"
proposal:
  add:
    - "RDE観点を必要に応じて明示する"
evidence:
  quote: "RDE差異検証モードを重視する"
  confidence: 0.8
evaluation:
  rde_class: "Inferred Extension"
status: "pending"
```

## 6. Reverse Compileの意味

通常のcompileは以下である。

```text
Profile → Prompt IR → Target Prompt
```

Reverse Compileはその逆である。

```text
Conversation / Output → Candidate Update → Profile Patch
```

ただし、完全な逆変換ではない。会話ログからProfileへ戻す過程では、情報の選別、推測、要約、抽象化が発生する。

したがって、Reverse Compileは常に不確実性を伴う。

## 7. RDE観点

Reverse CompileはProfile汚染の最大リスク領域である。

確認すべき点:

- LLMの推測をユーザー事実として扱っていないか
- 一時的な会話文脈を長期人格へ昇格していないか
- ユーザーの皮肉、仮説、反語を嗜好として誤抽出していないか
- 外部ページの価値観をユーザー価値観として取り込んでいないか
- 実験的発言を固定的方針として扱っていないか

## 8. 評価階層

初期実装では以下の順に進める。

```text
Level 0: regex / rule-based extraction
Level 1: heuristic classification
Level 2: local LLM assisted extraction
Level 3: external LLM assisted extraction
```

Phase 1では実装しない。

Phase 4以降でCandidate UpdateとRDE評価が整ってから、本格的に扱う。

## 9. 非目標

初期段階では以下を目標にしない。

- 会話履歴の完全自動同期
- Profileの完全自動更新
- すべてのチャット履歴の永続保存
- LLM出力の無条件取り込み
- ユーザー人格の自動推定

## 10. 完了条件

このパイプラインの最小実装は、以下を満たしたら完了とする。

```text
会話ログからCandidate Updateを生成できる
Candidate Updateにsource/evidence/confidenceが含まれる
RDE分類が付与される
ユーザー承認なしにProfileへmergeされない
Lineageに更新履歴が残る
```
