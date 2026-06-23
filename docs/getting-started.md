# Sayane はじめに（利用者ガイド）

Sayane **1.0.13** 時点で、Phase 0〜5 の成果物に加え resident app 準備フェーズのプレビュー/方針文書が追加されている。本書は「何ができて」「どこから始めるか」をまとめる。

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
| 3 | **Chrome Extension** | ブラウザ capture・LLM 挿入・Candidate popup（ja/en、現行方針では freeze / deprecated） |
| 4 | **RDE / Candidate 評価** | ヒューリスティック評価・approve/reject・lineage |
| 5 | **Storage / Obsidian / Git** | local Markdown / context_index。Obsidian / Git は互換運用 |

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
| ローカル browser shell で queue / daemon / diagnostics を使う | [Bridge マニュアル](bridge-manual.md) の resident app 導線 |
| Cursor から Profile を参照・compile | [MCP マニュアル](mcp-manual.md) |
| ブラウザで文脈を capture / LLM 欄に挿入 | [Extension マニュアル](extension-manual.md) + Bridge |
| スクリプトから HTTP で呼ぶ | [Bridge マニュアル](bridge-manual.md) |

## 4. インストール

**PyPI**（Python 3.11+）:

```bash
pip install "sayane==1.0.13"
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

### 5.3 Chrome Extension + Bridge（Phase 2 + 3 / legacy）

Chrome Extension は既存利用者向けには利用可能だが、現行方針では **freeze / deprecated** であり、新規の主経路は CLI / MCP / Local Bridge である。

ターミナル 1:

```bash
sayane serve
# Bearer token: ~/.sayane/bridge.token
# Dedicated local UI session artifact: ~/.sayane/bridge.ui-session.json
# Resident app bootstrap: http://127.0.0.1:38741/app/ui
```

ターミナル 2:

```bash
cd extension && npm install && npm run build
# Chrome で extension/ を読み込み、Options に token を設定
```

→ [Bridge マニュアル](bridge-manual.md) / [Extension マニュアル](extension-manual.md)

### 5.4 resident app local shell（current app-first path）

現行の operator-facing growth path は、extension ではなく Bridge-hosted local shell である。

```bash
./scripts/run-app-local.sh
# 必要なら:
# ./scripts/run-app-local.sh --foreground
# ./scripts/run-app-local.sh --no-open
# 初回ブラウザ導線は /app/ui?bootstrap_token=... を 1 回だけ踏み、
# 以後は dedicated local UI session cookie で /app/ui を継続利用する
sayane app overview --json
sayane app daemon-overview --json
sayane app daemon-packaging-status --json
sayane app daemon-service-control-boundary --json
sayane app daemon-supervision-status --json
sayane app daemon-recovery-consent-status --json
```

この local shell は preview / review / operator guidance surface であり、直接 profile patch や
OS service activation を行うものではない。

現在の resident app entrypoint は:

```text
http://127.0.0.1:38741/app/ui
```

`http://127.0.0.1:8008/index.html` のような別 static-site URL は使わない。

→ [Bridge マニュアル](bridge-manual.md) / [CLI コマンドリファレンス](reference/cli-command-reference.md)

### 5.5 macOS native app preview

macOS では、Bridge-hosted web shell に加えて native app preview も開発中です。

```bash
swift build --package-path macos/SayaneApp
./scripts/run-macos-app-preview.sh
./scripts/check-macos-app-preview.sh
```

Swift package を Xcode で開き、`SayaneApp` executable target を起動する。
Bridge 切断時は native error view の `Start Bridge` / `Reconnect` を使う。
`./scripts/check-macos-app-preview.sh` は local Bridge shell の準備、Swift package build/test、
`/app/ui` bootstrap と screen-state surface の smoke check をまとめて実行する。
既存の手動起動 Bridge をそのまま使いたい場合は `--no-start`、Bridge/session 切り分けだけを
したい場合は `--no-build --no-tests`、失敗時のレスポンス本文まで見たい場合は `--verbose` を使う。

この native app preview は resident app contract / screen-state / action surfaces を使う。
native app 自体は `~/.sayane/bridge.token` を使って bearer-backed app-facing surface を直接読む。
Browser bootstrap と resident app UI session は Bridge-hosted debug shell 側の話として切り分ける。
Home と error view には共通の connection diagnostics card があり、Bridge URL / health endpoint /
debug shell URL / token path / log path と、Reconnect / Start Bridge / Open Logs などの復旧操作を
同じ場所から使える。
さらに Home 最上部には Bridge status panel があり、未接続 / 起動中 / 利用可能 を先に判断してから
次の操作へ進める。
同じ status rail は Queue / Daemon にも compact 表示されるため、作業中の画面から戻らずに
Bridge の再接続やログ確認へ進める。
また capture / review / copy の結果は共通の feedback banner に集約され、mutation 失敗時は
sheet が閉じずに入力内容を保ったまま再試行できる。
Queue detail では、現在選択中の候補に関係する直近アクション結果だけを candidate result strip として
残すため、approve / revise 後の文脈を見失いにくい。
さらに Queue detail の review command deck に readiness / 実行ボタン / shortcut をまとめ、
判断と操作を 1 箇所で完結できるようにしている。
Home では review / quick link / daemon action の先頭項目を start-here section に集約し、
起動直後の最初の一手を選びやすくしている。
Daemon でも next action / LaunchAgent status / runbook を focus section にまとめ、
長い運用情報に入る前の優先確認ポイントを先に見せる。
daemon 画面では copyable な CLI / `launchctl` コマンド、LaunchAgent plist 確認、
runtime-init / cleanup / repair の conservative preview 要約を確認できる。
さらに current operator packaging / supervision / recovery contract を read-first で表示し、
packaging model 候補、background supervision 候補、guardrails、推奨 recovery flow を
native app 内で参照できる。加えて startup command / bootstrap UI / phase closure checklist
も native 側で可視化する。handoff 向けに workstream 状態と recommended implementation order
も同じ画面で確認できる。service lifecycle operation / policy gate / app-UI exposure limit /
governing rule も同じ daemon 画面で read-first に確認できる。macOS では LaunchAgent 向けの
preflight / verification / log path / security boundary / troubleshooting に加えて、
plist preview / program arguments / environment assumptions も native 画面で参照できる。
さらに operation id / preview hash も native 画面で確認でき、handoff 時の照合に使える。
stdout/stderr の tail コマンドと preview/apply boundary も同画面で確認できる。
loaded status / return code / stderr summary も先に確認できる。
主要セクションは折りたたみ表示になっており、要点だけ先に確認しやすい。

失敗時の基本切り分け:

```bash
curl -s http://127.0.0.1:38741/health
open "http://127.0.0.1:38741/app/ui?bootstrap_token=$(cat ~/.sayane/bridge.token)"
tail -n 40 ~/.sayane/macos-app-smoke.log
```

- `ERR_CONNECTION_REFUSED`: Bridge 未起動または listen 失敗
- `Missing bootstrap bearer or valid resident app UI session`: bootstrap URL を踏まずに `/app/ui` を開いている
- `Missing or invalid resident app UI session`: cookie が stale。bootstrap URL を開き直すか smoke script を再実行する

→ [macOS app preview](../macos/SayaneApp/README.md)

### 5.6 Obsidian / Git（Phase 5 / compatibility）

```bash
export SAYANE_OBSIDIAN_VAULT="$HOME/Documents/MyVault"   # 任意: 存在する vault
sayane storage import          # または sayane storage import /path/to/vault
sayane storage index
sayane compile --target chatgpt   # context 本文を Prompt IR に含める
# Git / Obsidian は互換導線として残るが、現行方針では primary path ではない
```

→ [Storage マニュアル](storage-manual.md)

## 6. ローカルデータの場所

```text
~/.sayane/
  bridge.token              # Bridge 認証（Phase 2）
  bridge.ui-session.json    # resident app の dedicated local UI session artifact
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
