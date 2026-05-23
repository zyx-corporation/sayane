# RDE / UIB 評価と Lineage

## 1. 概要

Omomuki は、文脈を集めるだけのツールではない。

重要なのは、収集された文脈をどのようにProfileへ昇格させるかである。Webページ、LLM出力、会話履歴、メモから得られた情報を無条件にProfileへmergeすると、ユーザーの人格的文脈が外部情報やLLMの推測によって汚染される危険がある。

そのためOmomukiでは、captureされた情報をまずCandidate Updateとして扱い、RDE / UIB評価を通してからProfileへmergeする。

```text
Captured Context
  → Candidate Update
  → RDE Diff
  → User Approval
  → Profile Merge
  → Lineage Record
```

## 2. RDEの役割

RDEは、生成物や更新候補が元の意図・価値・文脈からどのように変化したかを評価する層である。

OmomukiにおけるRDEは、主に以下を評価する。

- Profile更新候補が既存Profileと整合しているか
- 新しい文脈がユーザーの価値観を過剰に上書きしていないか
- LLMの推測が事実のように混入していないか
- 既存の応答様式を狭めていないか
- 実装上の便宜が人格的方針へすり替わっていないか

## 3. RDE分類

初期分類は以下とする。

```text
Preserved
Authorized Transformation
Inferred Extension
Unresolved Gap
Suspicious Drift
Critical Distortion
```

### 3.1 Preserved

元の意味・意図・価値が保存されている。

### 3.2 Authorized Transformation

表現形式や構造は変化しているが、目的に沿った正当な変換である。

### 3.3 Inferred Extension

既存情報から推論された補完である。

この分類では、推論であることを明示し、実証済み情報として扱わない。

### 3.4 Unresolved Gap

情報が不足しており、判断を保留すべき箇所である。

### 3.5 Suspicious Drift

元の人格的文脈、価値観、方針から逸脱する可能性がある。

### 3.6 Critical Distortion

重大な意味変形、価値の反転、誤情報の混入、またはユーザー方針の破壊がある。

## 4. UIB評価の役割

UIBは、RDEの補助評価軸として用いる。

初期軸は以下である。

```text
UD: Uncertainty Decomposition
MI: Minimal Information
CH: Competing Hypotheses
DT: Discriminative Tests
VP: Values / Power
FG: Failure Modes / Guardrails
```

### 4.1 UD

不確実性が分解されているか。

例: 事実、推測、仮説、未確認情報が区別されているか。

### 4.2 MI

必要最小限の文脈に絞られているか。

Profile全体を肥大化させず、必要な文脈だけを取り込めているか。

### 4.3 CH

複数の解釈や仮説が保持されているか。

単一の人格像へ過剰固定していないか。

### 4.4 DT

差異を検証できる問いやテストがあるか。

例: この更新は既存profileのどのセクションを変えるのか。

### 4.5 VP

価値観、権力関係、分配上の偏りを見ているか。

AIプラットフォームや外部ソースの価値観がユーザーProfileへ混入していないか。

### 4.6 FG

失敗モードとガードレールが明示されているか。

例: 誤抽出、過剰要約、人格固定化、文脈汚染、LLM由来の作話。

## 5. Candidate Update

Candidate Updateは、Profileへmergeされる前の更新候補である。

構造案:

```yaml
id: "candidate-20260523-001"
source:
  type: "web"
  uri: "https://example.com"
  captured_at: "2026-05-23T00:00:00+09:00"
target:
  profile: "default"
  section: "knowledge.concepts"
proposal:
  add:
    - "context portability"
reason:
  summary: "LLM間の文脈移植に関する重要概念として抽出"
evaluation:
  rde_class: "Inferred Extension"
  uib:
    UD: 0.7
    MI: 0.8
    CH: 0.5
    DT: 0.6
    VP: 0.4
    FG: 0.7
status: "pending"
```

## 6. Lineage

Lineageは、Profileの変化履歴である。

目的は以下である。

- 更新の出典を追跡する
- いつ何が変わったかを記録する
- RDE分類を保存する
- rollbackを可能にする
- fork / mergeを可能にする
- LLMごとの移植差分を監査する

## 7. Merge Policy

初期段階では、Profile本体へのmergeはユーザー承認を必須とする。

自動処理はCandidate Update生成までに限定する。

```text
capture: 自動可
candidate generation: 自動可
RDE evaluation: 自動可
profile merge: 原則手動承認
critical section update: 常に手動承認
```

critical sectionとは以下である。

- identity
- values
- policy
- voice
- long-term preference

## 8. RDE的注意点

Omomukiは、ユーザーを過去のProfileへ固定する装置になってはならない。

Profileは変化してよい。ただし、その変化は記録され、評価され、必要に応じて撤回可能であるべきである。

重要なのは、変化を止めることではなく、変化がどこから来たのかを失わないことである。
