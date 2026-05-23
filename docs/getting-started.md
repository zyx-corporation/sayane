# Omomuki はじめに（利用者ガイド）

Omomuki **0.5.8** 時点で、Phase 0〜5 の成果物が利用可能である。本書は「何ができて」「どこから始めるか」をまとめる。

設計の詳細は [設計概要](architecture.md)、開発者向けは [開発原則](development-principles.md) を参照。

## 1. Omomuki とは

LLM 間で、ユーザーの人格的文脈・価値観・応答様式を **local-first** に保持し、各 LLM 向けプロンプトへ変換するツールである。

```text
人格と実行を分離する
```

```text
Omomuki Profile  →  Prompt IR  →  Adapter  →  LLM 向け出力
```

LLM は人格の所有者ではない。Profile と Prompt IR は LLM 非依存の中間表現である。

## 2. 現在利用できる構成（Phase 0〜5）

| Phase | 成果物 | 主な用途 |
|-------|--------|----------|
| 0 | スキーマ・CI・パッケージ骨格 | 開発基盤 |
| 1 | **CLI** (`init`, `compile`, `export` …) | ターミナルから Profile → プロンプト |
| 2 | **Local Bridge** (`omomuki serve`) | HTTP API・Extension 連携 |
| 2.5 | **MCP Server** (`omomuki mcp serve`) | Cursor / Claude Desktop 等 |
| 3 | **Chrome Extension** | ブラウザ capture・LLM 挿入・Candidate popup（ja/en） |
| 4 | **RDE / Candidate 評価** | ヒューリスティック評価・approve/reject・lineage |
| 5 | **Storage / Obsidian / Git** | vault 取り込み・context_index・Git commit |

**未実装（Phase 6 以降）**: Rust 抽出など。

## 3. 接続面の選び方

```text
                    ┌─────────────────┐
                    │  Core Library   │
                    │ Profile / IR    │
                    └────────┬────────┘
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
      ┌─────────┐     ┌───────────┐    ┌────────────┐
      │   CLI   │     │  Bridge   │    │ MCP Server │
      │ 直接操作 │     │ HTTP:38741│    │ stdio MCP  │
      └─────────┘     └─────┬─────┘    └──────┬─────┘
                            │                  │
                            ▼                  ▼
                     Chrome Extension    Cursor / Cline
```

| やりたいこと | 推奨 |
|-------------|------|
| 手元でプロンプト JSON を得る | [CLI マニュアル](cli-manual.md) |
| Cursor から Profile を参照・compile | [MCP マニュアル](mcp-manual.md) |
| ブラウザで文脈を capture / LLM 欄に挿入 | [Extension マニュアル](extension-manual.md) + Bridge |
| スクリプトから HTTP で呼ぶ | [Bridge マニュアル](bridge-manual.md) |

## 4. 共通セットアップ

```bash
git clone <repository>
cd omomuki
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Profile Store の初期化:

```bash
omomuki init
# ~/.omomuki/profiles/default/omomuki.profile.yaml を編集
omomuki profile inspect
```

サンプルだけ試す場合:

```bash
omomuki compile --target chatgpt --profile examples/profiles/minimal.yaml
```

## 5. シナリオ別クイックスタート

### 5.1 CLI のみ（Phase 1）

```bash
omomuki compile --target claude --profile examples/profiles/minimal.yaml
omomuki export --format markdown --target chatgpt \
  --profile examples/profiles/minimal.yaml
```

→ [CLI マニュアル](cli-manual.md)

### 5.2 MCP クライアント（Phase 2.5）

```bash
omomuki mcp serve   # stdio — クライアントが子プロセス起動
# またはデバッグ用:
omomuki mcp list-profiles
omomuki mcp compile --target chatgpt --profile-id default
```

→ [MCP マニュアル](mcp-manual.md)

### 5.3 Chrome Extension + Bridge（Phase 2 + 3）

ターミナル 1:

```bash
omomuki serve
# Bearer token: ~/.omomuki/bridge.token
```

ターミナル 2:

```bash
cd extension && npm install && npm run build
# Chrome で extension/ を読み込み、Options に token を設定
```

→ [Bridge マニュアル](bridge-manual.md) / [Extension マニュアル](extension-manual.md)

### 5.4 Obsidian / Git（Phase 5）

```bash
export OMOMUKI_OBSIDIAN_VAULT="$HOME/Documents/MyVault"   # 任意: 存在する vault
omomuki storage import          # または omomuki storage import /path/to/vault
omomuki storage index
omomuki compile --target chatgpt   # context 本文を Prompt IR に含める
omomuki storage commit -m "omomuki: sync context" --init
```

→ [Storage マニュアル](storage-manual.md)

## 6. ローカルデータの場所

```text
~/.omomuki/
  bridge.token              # Bridge 認証（Phase 2）
  profiles/
    default/
      omomuki.profile.yaml  # メイン Profile
      context/              # 文脈 Markdown（参照用）
  candidates/               # capture された Candidate（merge 前）
```

capture は **Profile へ即 merge しない**。評価・承認は CLI / Bridge / Extension / MCP から行う（[評価マニュアル](evaluation-manual.md)）。

## 7. マニュアル一覧

| ドキュメント | 内容 |
|-------------|------|
| [CLI マニュアル](cli-manual.md) | `init`, `profile`, `compile`, `export`, `serve`, `mcp` 概要 |
| [Bridge マニュアル](bridge-manual.md) | HTTP API・認証・curl |
| [MCP Server マニュアル](mcp-manual.md) | Tools・Cursor 設定 |
| [Chrome Extension マニュアル](extension-manual.md) | ビルド・popup・i18n・site adapter |
| [Chrome Extension 受け入れテスト](extension-acceptance-test.md) | 手動 UAT 手順 |
| [RDE / Candidate 評価マニュアル](evaluation-manual.md) | evaluate・approve・lineage |
| [Storage マニュアル](storage-manual.md) | Obsidian import/export・Git |
| [Omomuki Profile と Prompt IR](profile-ir.md) | データ構造 |
| [Security Design](security.md) | 脅威モデル・read-only 方針 |

## 8. 制限事項（現バージョン）

- `compile` の context 本文読み込みはプロファイルディレクトリ内のファイルに限定（最大約 32KB/ファイル）
- Adapter は **chatgpt / claude** のみ
- Obsidian: `OMOMUKI_OBSIDIAN_VAULT` 設定時は `storage import` / `export` で vault 引数を省略可
- Obsidian export は vault 内サブディレクトリ（既定 `omomuki/`）のみ
- Level 3 judge は API key とネットワークが必要（任意機能）

## 9. 次のロードマップ

[実装ロードマップ](roadmap.md) — Phase 6: Rust 抽出（diff engine、vault indexer 等）。
