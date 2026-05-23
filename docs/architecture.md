# Omomuki 設計概要

## 1. 目的

Omomuki は、ユーザーの人格的文脈・価値観・応答様式・作業方針を、特定のLLMプラットフォームに閉じ込めず、複数のLLM実行基盤へ移植可能にするための local-first ツールである。

主な目的は以下である。

- LLM間でユーザー文脈を再利用可能にする
- AIプラットフォーム固有の記憶ロックインを避ける
- プロンプトを文字列ではなく中間表現として扱う
- プロファイル更新時の意味変化を監査する
- CLI、Chrome Extension、将来のKotonoha連携などから再利用できるCore Libraryを提供する

## 2. 基本アーキテクチャ

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

この流れにより、人格・文脈・方針はLLM固有のプロンプトへ直結しない。まず抽象的なOmomuki Profileとして保持し、Prompt IRへ変換し、Adapterが各LLM固有形式へコンパイルする。

## 3. コンポーネント

### 3.1 Core Library

Core Library はOmomukiの中核であり、以下を扱う。

- Omomuki Profile
- Prompt IR
- Policy
- Context Index
- Lineage
- Diff / Merge / Fork
- RDE / UIB Evaluator
- Storage abstraction

この層はCLI、Local Bridge、Chrome Extension、将来のObsidian pluginやMCP serverから再利用される。

### 3.2 CLI

CLIは信頼できる制御面である。

役割は以下である。

- profile の初期化
- context の取り込み
- Prompt IR の生成
- LLM別promptのcompile
- profile diff
- RDE / UIB評価
- export
- Local Bridge の起動

### 3.3 Local Bridge

Local Bridge はChrome ExtensionとCore Libraryを接続するlocalhost APIである。

Chrome Extensionが直接ローカルファイルやprofile storeを管理しないようにするため、Bridgeがcapture、compile、evaluateなどの要求を受け取り、Core Libraryへ委譲する。

### 3.4 Chrome Extension

Chrome Extension は入口と出口である。

入口としては、Webページ、選択テキスト、YouTube、note、GitHub、ChatGPT/Claude/Gemini画面などから文脈候補を取得する。

出口としては、Omomukiが生成したcontext packetやpromptを、各LLMの入力欄へ挿入する。

### 3.5 Evaluator

Evaluator は、プロファイル更新やLLM出力を評価する層である。

初期段階では以下を想定する。

- RDE: 意味変化の分類と逸脱検出
- UIB: 不確実性、最小文脈、複数仮説、価値配慮、失敗モードの評価

## 4. 責任分離

Omomukiでは、各層の責任を明確に分離する。

```text
Core      : 永続的価値、意味処理、評価、履歴
CLI       : 信頼できる制御面
Bridge    : ローカル連携面
Extension : 便利なUI、capture、insert
Adapter   : LLM固有形式への変換
```

Chrome Extensionに人格管理の本体を持たせない。Extensionは壊れてもよいが、Profile、IR、Lineageは壊れてはならない。

## 5. Local-first 原則

Omomukiはlocal-firstを基本とする。

ユーザーの人格的文脈は、外部SaaSではなくローカルのProfile Storeに保持する。

Phase 5 以降、Obsidian vault との import/export（`omomuki storage`）、**Git による履歴化（Profile 変更時の自動コミット、SQLite 実装まで既定）**、環境変数 `OMOMUKI_OBSIDIAN_VAULT` による既定 vault 指定が利用できる。暗号化ストア・SQLite は Phase 6 以降を検討する。

## 6. 将来拡張

- Obsidian plugin（CLI 連携は Phase 5 で提供済み）
- VSCode extension
- Tauri desktop app
- Kotonoha連携
- Rust製diff/index engine（Phase 6）
- encrypted profile store
- semantic lineage system連携

**実装済み（Phase 0〜5）**: CLI、Local Bridge、MCP Server、Chrome Extension、RDE/Candidate 評価、Storage/Obsidian/Git。
