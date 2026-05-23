# Omomuki

Omomuki は、LLM間でユーザーの人格的文脈・価値観・応答様式・作業方針を可搬化するための local-first ツールです。

ChatGPT、Claude、Gemini、OSSモデルなど、異なるLLM実行基盤のあいだで、ユーザーの文脈・作業スタイル・価値観・応答 preferences を抽出し、構造化し、移植し、評価することを目指します。

Omomuki は、LLMを人格や文脈の所有者ではなく、実行基盤として扱います。

## コンセプト

Omomuki の中核原則は単純です。

> 人格と実行を分離する。

ユーザーの人格的文脈、方針、作業記憶は、特定のAIプラットフォーム内部に閉じ込められるべきではありません。Omomuki は、人格・文脈・方針をLLM非依存の中間表現として保持し、Adapterを通じて各LLM向けの形式へ変換します。

```text
Omomuki Profile
        ↓
Prompt IR
        ↓
Strategy
        ↓
Adapter
        ↓
LLM Runtime
        ↓
Output
        ↓
Evaluation / Lineage
```

## 初期プロダクト構成

Omomuki は、まず以下の要素からなる単体アプリケーションとして実装します。

- Python製 Core Library
- Python製 CLI
- Local Bridge API
- TypeScript製 Chrome Extension

Chrome Extension は、Web上の文脈を取り込み、LLM入力欄へ文脈パケットを挿入する入口・出口を担います。一方、CLI と Core Library は、Profile保存、Prompt IR生成、変換、履歴、評価を管理します。

## 主要目的

- ユーザーの人格的文脈をLLM間で可搬化する
- AIプラットフォーム固有のメモリロックインを避ける
- プロンプトを単なる文字列ではなく、構造化された中間表現として扱う
- Omomuki Profileを各LLM向け形式へcompileする
- local-firstなProfile保存とLineage管理を行う
- Profile更新候補を、長期的な人格的文脈へmergeする前に評価する
- 将来的にKotonoha、Obsidian plugin、VSCode extension、MCP server、desktop appから再利用可能なモジュールとして設計する

## Omomuki が扱うもの

Omomuki は、以下のような情報を構造化します。

- identity: ユーザーの基本情報
- voice: 文体、口調、応答傾向
- values: 価値観、判断基準、倫理的優先順位
- knowledge: ユーザー固有の概念、プロジェクト、研究テーマ
- policy: 応答制約、禁止事項、優先方針
- context_index: AIが読むべき文脈への目次
- lineage: Profile更新、分岐、統合、評価の履歴

Omomuki Profile は人格そのものではありません。それは、LLMがユーザーの人格的文脈へ接近するための構造化媒介です。

## CLI構想

初期CLIでは、以下のようなコマンドを想定します。

```bash
omomuki init
omomuki profile build
omomuki profile inspect
omomuki capture ./note.md
omomuki compile --target chatgpt
omomuki compile --target claude
omomuki compile --target gemini
omomuki diff old.yaml new.yaml
omomuki evaluate --mode rde
omomuki export --format markdown
omomuki serve --port 38741
```

## Chrome Extension構想

Chrome Extension は、ブラウザ上の文脈をOmomukiへ取り込み、Omomukiが生成した文脈パケットを各LLMの入力欄へ挿入します。

想定機能:

- 選択テキストのcapture
- 現在ページのcapture
- YouTube transcriptのcapture
- note、GitHub、ChatGPT、Claude、Gemini画面からの文脈取得
- ChatGPT / Claude / Gemini入力欄へのcontext packet挿入
- profile選択
- candidate update確認

## RDE / UIB評価

Omomuki は、captureした情報をすぐに長期Profileへmergeしません。

```text
Captured Context
  → Candidate Update
  → RDE Diff
  → User Approval
  → Profile Merge
  → Lineage Record
```

RDEは、Profile更新候補が既存の人格的文脈・価値観・応答方針からどのように変化したかを評価します。

UIBは、不確実性、最小文脈、複数仮説、価値配慮、失敗モードを補助評価します。

## 実装方針

```text
Core / CLI / Bridge : Python
Chrome Extension    : TypeScript
Schema / IR         : JSON Schema + Pydantic
将来の高速化部分     : Rust
```

初期段階ではPythonで仕様を柔軟に固め、性能・配布・暗号化・indexingなどの必要が明確になった段階でRustによる切り出しを検討します。

## ドキュメント

詳細な設計文書は [`docs/`](docs/) にあります。

- [ドキュメント索引](docs/index.md)
- [設計概要](docs/architecture.md)
- [Omomuki Profile と Prompt IR](docs/profile-ir.md)
- [CLI / Local Bridge / Chrome Extension 設計](docs/cli-chrome-extension.md)
- [RDE / UIB 評価と Lineage](docs/evaluation-lineage.md)
- [実装ロードマップ](docs/roadmap.md)

## ライセンス

Omomuki は Apache License, Version 2.0 の下で提供されます。

SPDX-License-Identifier: Apache-2.0
