# Contributing to Sayane

Sayane への貢献ありがとうございます。

このプロジェクトは、LLM間でユーザーの人格的文脈・価値観・応答様式・作業方針を可搬化する local-first ツールです。人格的文脈を扱うため、通常のソフトウェア開発以上に、変更が生む意味変化を慎重に扱います。

## 1. 基本原則

Sayane の開発は、以下を基本とします。

```text
RDE原則
Issue first
Branch first
TDD / test first
デザインパターン重視
Security / Privacy by design
```

詳しくは以下を参照してください。

- `docs/development-principles.md`
- `docs/mvp-scope.md`
- `docs/security.md`
- `docs/roadmap.md`

## 2. 貢献の流れ

### 2.1 Issue first

実装、修正、設計変更、文書変更は、原則としてIssueから始めます。

Issueには以下を含めてください。

- 目的
- 背景
- 対象範囲
- 非対象範囲
- 受け入れ条件
- RDE観点
- テスト方針

既存のIssue templateを利用してください。

### 2.2 Branch first

`main` ブランチへ直接pushしないでください。

ブランチ名は以下の形式を推奨します。

```text
feature/<issue-number>-<short-name>
fix/<issue-number>-<short-name>
docs/<issue-number>-<short-name>
refactor/<issue-number>-<short-name>
test/<issue-number>-<short-name>
```

例:

```text
feature/9-python-package-setup
docs/18-mcp-server-design
fix/24-profile-diff-classification
```

### 2.3 TDD / test first

Core、CLI、Adapter、Evaluator、Storageなどの変更では、可能な限り先にテストを書いてください。

基本サイクル:

```text
Red   : 失敗するテストを書く
Green : 最小実装で通す
Refactor : 設計を整える
RDE Review : 意味変化を確認する
```

### 2.4 Pull Request

Pull Request templateに従って、以下を明記してください。

- 関連Issue
- 変更概要
- 実行したテスト
- RDEレビュー
- デザインパターン確認
- Security / Privacy確認
- 互換性影響
- ドキュメント更新有無

## 3. RDEレビュー

Sayaneでは、変更を単なる機能追加ではなく、意味変化として扱います。

PRでは、可能な範囲で以下を確認してください。

```text
Preserved: 保存された要素
Authorized Transformation: 許可された変換
Inferred Extension: 推論による補完
Unresolved Gap: 未解決の要素
Suspicious Drift: 逸脱リスク
Critical Distortion: 重大な歪曲
```

特に以下を避けてください。

- 元Issueより強い主張にすること
- 未検証内容を実証済みとして扱うこと
- 実装上の便宜を設計思想として正当化すること
- Profile / Prompt IR / Lineage の意味を意図せず変えること
- 同一人格の完全再現を示唆すること
- ユーザー承認なしの自動Profile更新を導入すること

## 4. デザインパターン

Sayaneは、LLM差異、UI差異、Storage差異、評価差異を扱うため、設計パターンを明示的に重視します。

主に以下を想定します。

- Adapter Pattern
- Strategy Pattern
- Builder Pattern
- Factory Pattern
- Decorator Pattern
- Observer Pattern
- Repository Pattern

新しい実装を追加する場合は、どの責務をどの層に置くかを明確にしてください。

## 5. Security / Privacy

Sayane Profileは機微情報を含み得ます。

以下を守ってください。

- secret、token、API key、private keyをcommitしない
- ログやfixtureに実在の機微情報を入れない
- Local BridgeやMCP Serverの認証境界を弱めない
- captureした情報を承認なしにProfileへmergeしない
- Profile、values、policy、identityを危険に上書きしない

Security設計の詳細は `docs/security.md` を参照してください。

## 6. Phase 1の優先順位

初期実装では、Phase 1 CLI MVPを最優先します。

最初の開発順は以下を推奨します。

```text
#9  Project skeleton and Python package setup
#10 SayaneProfile schema and Pydantic model
#11 PromptIR model and builder
#12 Adapter interface and ChatGPT / Claude adapters
#13 CLI commands for init / inspect / compile / export
#14 Examples and documentation for CLI MVP
```

Phase 1では、Local Bridge、MCP Server、Chrome Extension、RDE/UIB自動評価を実装しません。

## 7. ライセンス

Sayane は Apache License, Version 2.0 の下で提供されます。

貢献するコード、文書、テスト、設定は、特別な明記がない限り Apache-2.0 として提供されるものとします。

SPDX-License-Identifier: Apache-2.0
