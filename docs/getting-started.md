# Sayane はじめに（利用者ガイド）

Sayane **1.0.0** 時点で、Phase 0〜5 の成果物が利用可能である。本書は「何ができて」「どこから始めるか」をまとめる。

設計の詳細は [設計概要](architecture.md)、開発者向けは [開発原則](development-principles.md) を参照。

## 1. Sayane とは

LLM 間で、ユーザーの人格的文脈・価値観・応答様式を **local-first** に保持し、各 LLM 向けプロンプトへ変換するツールである。

```text
人格と実行を分離する
```

```text
Sayane Profile  →  Prompt IR  →  Adapter  →  LLM 向け出力
```

LLM は人格の所有者ではない。Profile と Prompt IR は LLM 非依存の中間表現である。

## 2. 現在利用できる構成（Phase 0〜5）

| Phase | 成果物 | 主な用途 |
|-------|--------|----------|
| 0 | スキーマ・CI・パッケージ骨格 | 開発基盤 |
| 1 | **CLI** (`init`, `compile`, `export` …) | ターミナルから Profile → プロンプト |
| 2 | **Local Bridge** (`sayane serve`) | HTTP API・Extension 連携 |
| 2.5 | **MCP Server** (`sayane mcp serve`) | Cursor / Claude Desktop 等 |
| 3 | **Chrome Extension** | ブラウザ capture・LLM 挿入・Candidate popup（ja/en） |
| 4 | **RDE / Candidate 評価** | ヒューリスティック評価・approve/reject・lineage |
| 5 | **Storage / Obsidian / Git** | vault 取り込み・context_index・Git commit |

**未実装（Phase 6 / Commercial Edition）**: 概要は [roadmap.md §9](roadmap.md)。商用版 CLI・MSI 等のマニュアルは sayane-pro 側。

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

## 4. インストール

**PyPI**（Python 3.11+）:

```bash
pip install sayane==1.0.5
```

**macOS / Linux**（curl + bash）:

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
```

**Windows**（PowerShell）:

```powershell
irm https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.ps1 | iex
```

詳細: [インストール](install.md)

### 開発者向け（clone 済み）

```bash
git clone https://github.com/zyx-corporation/sayane.git
cd sayane
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

または `SAYANE_SOURCE_DIR=$PWD bash scripts/install.sh`

Profile Store の初期化:

```bash
sayane init
# ~/.sayane/profiles/default/sayane.profile.yaml を編集
sayane profile inspect
```

サンプルだけ試す場合:

```bash
sayane compile --target chatgpt --profile examples/profiles/minimal.yaml
```

## 5. シナリオ別クイックスタート

### 5.1 CLI のみ（Phase 1）

```bash
sayane compile --target claude --profile examples/profiles/minimal.yaml
sayane export --format markdown --target chatgpt \
  --profile examples/profiles/minimal.yaml
```

→ [CLI マニュアル](cli-manual.md)

### 5.2 MCP クライアント（Phase 2.5）

```bash
sayane mcp serve   # stdio — クライアントが子プロセス起動
# またはデバッグ用:
sayane mcp list-profiles
sayane mcp compile --target chatgpt --profile-id default
```

→ [MCP マニュアル](mcp-manual.md)

### 5.3 Chrome Extension + Bridge（Phase 2 + 3）

ターミナル 1:

```bash
sayane serve
# Bearer token: ~/.sayane/bridge.token
```

ターミナル 2:

```bash
cd extension && npm install && npm run build
# Chrome で extension/ を読み込み、Options に token を設定
```

→ [Bridge マニュアル](bridge-manual.md) / [Extension マニュアル](extension-manual.md)

### 5.4 Obsidian / Git（Phase 5）

```bash
export SAYANE_OBSIDIAN_VAULT="$HOME/Documents/MyVault"   # 任意: 存在する vault
sayane storage import          # または sayane storage import /path/to/vault
sayane storage index
sayane compile --target chatgpt   # context 本文を Prompt IR に含める
# Git は init / import / index / approve 時に自動コミット（0.5.9+）
```

→ [Storage マニュアル](storage-manual.md)

## 6. ローカルデータの場所

```text
~/.sayane/
  bridge.token              # Bridge 認証（Phase 2）
  profiles/
    default/
      sayane.profile.yaml  # メイン Profile
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
| [Storage マニュアル](storage-manual.md) | Obsidian import/export・Git・直接編集 |
| [Sayane Profile と Prompt IR](profile-ir.md) | データ構造 |
| [Security Design](security.md) | 脅威モデル・read-only 方針 |

## 8. 制限事項（現バージョン）

- `compile` の context 本文読み込みはプロファイルディレクトリ内のファイルに限定（最大約 32KB/ファイル）
- Adapter は **chatgpt / claude** のみ
- Obsidian: `SAYANE_OBSIDIAN_VAULT` 設定時は `storage import` / `export` で vault 引数を省略可
- Obsidian export は vault 内サブディレクトリ（既定 `sayane/`）のみ
- Level 3 judge は API key とネットワークが必要（任意機能）

## 9. 次のロードマップ

[実装ロードマップ](roadmap.md) — Phase 6: Rust 抽出（diff engine、vault indexer 等）。
