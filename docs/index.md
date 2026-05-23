# Omomuki ドキュメント索引

Omomuki は、LLM間でユーザーの人格的文脈・価値観・応答様式を可搬化するための local-first ツールである。

本リポジトリでは、README と LICENSE は英語で管理し、設計・実装方針・評価方針などの詳細ドキュメントは日本語で記述する。

## ドキュメント構成

- [設計概要](architecture.md)
- [Omomuki Profile と Prompt IR](profile-ir.md)
- [MVP範囲](mvp-scope.md)
- [CLI / Local Bridge / Chrome Extension 設計](cli-chrome-extension.md)
- [MCP Server Integration](mcp-integration.md)
- [Conversation Extract / Reverse Compile Pipeline](extraction-pipeline.md)
- [Security Design](security.md)
- [RDE / UIB 評価と Lineage](evaluation-lineage.md)
- [開発原則](development-principles.md)
- [実装ロードマップ](roadmap.md)

## 基本方針

Omomuki は、まずCLIで最小価値を実証し、その後 Local Bridge、MCP Server、Chrome Extension へ段階的に展開する。

中核処理は最初から再利用可能な Core Library として分離する。

初期構成は以下を想定する。

```text
Omomuki
  Core Library
  CLI
  Local Bridge
  MCP Server
  Chrome Extension
```

Chrome Extension は入口と出口を担う補助UIである。安定接続面としてはMCP ServerをPhase 2.5に配置する。CLI と Core Library は、人格プロファイル、文脈、方針、履歴、評価を管理する。

## 設計上の中核命題

```text
人格と実行を分離する
```

LLM は人格や文脈の所有者ではなく、実行基盤である。Omomuki Profile は、ユーザーの人格的文脈・価値観・応答様式・作業方針を、特定LLMに依存しない形で保持する。

## 開発上の中核命題

```text
変更は機能追加ではなく、意味変化である。
意味変化は記録され、評価され、必要に応じて差し戻せなければならない。
```

Omomuki の開発は、RDE原則、Issue first、Branch first、TDD/test first、デザインパターン重視を基本とする。

## 用語

- Omomuki Profile: ユーザーの人格的文脈・価値観・応答様式を保持する構造化プロファイル
- Prompt IR: LLMへ渡す前の中間表現
- Adapter: Prompt IR を各LLM向け形式へ変換する層
- Strategy: 応答様式・推論様式を切り替える層
- MCP Server: MCP対応クライアントからOmomuki Coreを利用するための安定接続面
- Candidate Update: Profileへmergeされる前の更新候補
- Reverse Compile: 会話や出力からProfile更新候補を抽出する逆方向パイプライン
- RDE: 生成物やプロファイル更新における意味変化を監査する評価層
- UIB: 不確実性・最小文脈・複数仮説・価値配慮・失敗モードを評価する補助軸
- Lineage: プロファイルや文脈更新の履歴・分岐・統合の記録
