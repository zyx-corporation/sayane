# Omomuki Profile と Prompt IR

## 1. 概要

Omomuki Profile は、ユーザーの人格的文脈・価値観・応答様式・作業方針を、LLM非依存に保持する構造化プロファイルである。

Prompt IR は、Omomuki Profile とタスク文脈から生成される中間表現である。各LLMへ直接渡すプロンプトではなく、Adapterが各LLM向けに変換する前段階の構造である。

## 2. 設計原則

```text
人格はLLMを知らない
すべてはIRを通る
同一人格 ≠ 同一プロンプト
状態はProfileとLineageに保持する
```

同じOmomuki Profileであっても、ChatGPT、Claude、Gemini、OSSモデルに対して同一プロンプトを渡す必要はない。重要なのは、同一の人格的文脈・価値観・制約が、それぞれのLLM特性に応じて適切に変換されることである。

## 3. Omomuki Profile 初期構造

```yaml
version: "0.1.0"
kind: "OmomukiProfile"
identity:
  name: "Tomoyuki Kano"
  preferred_name: "tomyuk"
  roles:
    - "AI startup founder"
    - "engineer"
    - "architect"
voice:
  default_language: "ja"
  tone:
    - "precise"
    - "logical"
    - "occasionally poetic"
values:
  core:
    - "human dignity"
    - "anti-discrimination"
    - "relational intelligence"
knowledge:
  concepts:
    - "RDE"
    - "UIB"
    - "Kotonoha"
    - "Resonanceverse"
policy:
  response:
    avoid:
      - "unsupported overclaiming"
      - "unnecessary repetition"
    prefer:
      - "structured reasoning"
      - "explicit uncertainty"
context_index:
  entrypoint: "context/MyContext.md"
  handoff: "context/AI_HANDOFF.md"
lineage:
  created_at: "2026-05-23T00:00:00+09:00"
  updated_at: "2026-05-23T00:00:00+09:00"
```

## 4. Profile セクション

### 4.1 identity

ユーザーの基本的な識別情報を保持する。

ただし、これは人格そのものではなく、LLMがユーザーを誤認しないための最小限の構造である。

### 4.2 voice

文体、口調、応答の傾向を保持する。

例:

- 既定言語
- フォーマル/カジュアル傾向
- 叙情性の許容量
- 技術的厳密性の優先度
- markdown使用傾向

### 4.3 values

価値観、判断基準、倫理的優先順位を保持する。

これはLLMの応答がユーザーの価値観から逸脱しないようにするための参照情報である。

### 4.4 knowledge

ユーザー固有の概念、プロジェクト、研究テーマ、頻出用語を保持する。

これは単なる知識ベースではなく、ユーザーがどのような意味体系を扱っているかを示す。

### 4.5 policy

応答制約、禁止事項、優先方針を保持する。

policy は人格ではなく、実行時の制御条件である。

### 4.6 context_index

AIが読むべき文脈ファイルへの目次である。

大量の文脈を一括投入せず、タスクに必要な最小文脈だけを選択するために用いる。

### 4.7 lineage

Profileの生成、更新、分岐、統合の履歴を保持する。

これはRDEによる意味変化監査の前提となる。

## 5. Prompt IR 初期構造

```python
class PromptIR:
    system: list[str]
    context: list[str]
    instruction: list[str]
    constraints: list[str]
    examples: list[dict]
```

Prompt IR は文字列ではなく構造である。

### 5.1 system

LLMに与える役割・前提・対話対象情報。

### 5.2 context

タスクに必要な文脈。Profile全体ではなく、context_indexとStrategyにより選択された最小文脈を入れる。

### 5.3 instruction

ユーザー要求と、その要求を実行するための指示。

### 5.4 constraints

応答制約、禁止事項、形式条件。

### 5.5 examples

Few-shot例や、文体・変換例を保持する。

## 6. Adapter との関係

Prompt IR はそのままLLMへ送信しない。

Claude向け、ChatGPT向け、Gemini向け、OSSモデル向けのAdapterが、LLMごとのAPI形式・プロンプト作法・推論癖に応じて変換する。

```text
Prompt IR
  → ClaudeAdapter
  → OpenAIAdapter
  → GeminiAdapter
  → OSSAdapter
```

## 7. RDEとの関係

Omomuki Profile は更新候補を即時mergeしない。

```text
Captured Context
  → Candidate Update
  → RDE Diff
  → User Approval
  → Profile Merge
```

これにより、WebやAIから取り込まれた情報が、勝手にユーザー人格へ混入することを防ぐ。

## 8. 注意点

Omomuki Profile は人格そのものではない。

それは、LLMがユーザーの人格的文脈へ接近するための構造化媒介である。

したがって、「人格コピー」「人格保存」「意識再現」のような強い主張は避ける。Omomukiはあくまで文脈・価値観・応答様式の可搬化基盤である。
