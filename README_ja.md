# Sayane（紗綾音）

[English README](README.md)

Sayane は、**ChatGPT・Claude など複数の LLM のあいだで、あなたの文脈（価値観・文体・作業方針）を持ち運ぶ**ための **local-first** ツールです。

各サービスの「メモリ」や Custom Instructions に頼るのではなく、**自分の PC 上の Profile（プロファイル）を正本**として保持し、LLM ごとに最適なプロンプトへ変換して使います。

**現行バージョン**: Community Edition **v1.0.0**（Phase 0〜5 の機能が利用可能）

---

## こんな方におすすめ

- ChatGPT と Claude で、毎回同じ自己紹介・方針をコピペしている
- 「この LLM 用の設定」を別の LLM に移したいが、形式が違って困る
- 会話から得た学びを、いきなりプロファイルに上書きしたくない
- ローカルの Markdown メモ（Obsidian・エディタ・他ツール）を LLM 用の文脈につなげたい

---

## Sayane でできること（かんたんに）

| やりたいこと | Sayane のやり方 |
|-------------|----------------|
| 自分用の「人格・方針」を一か所にまとめる | ローカルの **Sayane Profile**（`~/.sayane/`） |
| ChatGPT 用・Claude 用にそれぞれプロンプトを作る | **compile**（中間表現 Prompt IR 経由） |
| ブラウザで拾った文脈を保存する | **capture** → **Candidate**（すぐには反映しない） |
| 反映してよいか判断してから更新する | **evaluate** → **approve** / **reject** |
| 更新の履歴を残す | **lineage**（採用・拒否の記録） |
| Markdown 文脈を Profile に載せる | **`context/`** に置く / **storage index**（Obsidian vault からの **import** は任意） |

---

## まず覚える用語（初心者向け）

### Sayane Profile（プロファイル）

あなたの **identity（名前・役割）**、**voice（文体）**、**values（価値観）**、**policy（応答の好み）** などを YAML で書いた「正本」です。  
通常は `~/.sayane/profiles/default/sayane.profile.yaml` に置かれます。

### Prompt IR（プロンプト中間表現）

LLM に依存しない **中間フォーマット** です。  
同じ Profile から、ChatGPT 向け・Claude 向けなど **target ごとに別の形**へ変換するための共通の土台になります。

### Adapter（アダプター）

Prompt IR を、各 LLM が期待する JSON 形式（例: OpenAI の `messages`、Anthropic 形式）に変換する層です。  
Community Edition では主に **chatgpt** と **claude** に対応しています。

### Candidate（更新候補）

会話や capture で得た「プロファイルへ入れたい変更案」です。  
**承認（approve）するまで、本番の Profile には merge されません。**

### lineage（更新の来歴）

どの Candidate を採用・拒否したかの記録です。後から「いつ何が変わったか」を追えます。

---

## 全体の流れ

```text
Sayane Profile（ローカル正本）
        ↓
   Prompt IR（中間表現）
        ↓
   Adapter（LLM ごとの形式）
        ↓
   ChatGPT / Claude などへ渡すプロンプト

capture した内容 → Candidate → 評価 → approve のときだけ Profile に反映 → lineage に記録
```

LLM は人格の「所有者」ではなく、**Profile からコンパイルされたプロンプトを実行する側**と考えます。

---

## 事前準備

インストール前に、次があるとスムーズです。

| 項目 | 内容 |
|------|------|
| OS | macOS / Linux / Windows |
| Python | **3.11 以上**（インストーラが venv を作成します） |
| ネットワーク | 初回インストール時（GitHub から取得） |
| ターミナル | macOS/Linux: Terminal / Windows: PowerShell |

---

## 5分で試す（初回セットアップ）

### ステップ 1: CLI をインストール

**macOS / Linux**（ターミナル）:

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
```

特定バージョン（例: v1.0.0）を入れる場合:

```bash
SAYANE_REF=v1.0.0 curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
```

**Windows**（PowerShell）:

```powershell
irm https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.ps1 | iex
```

インストール後、**新しいターミナル**を開き、次でバージョンを確認します。

```bash
sayane --version
# 例: sayane 1.0.0
```

`command not found` になる場合:

- macOS/Linux: `~/.local/bin` が PATH に入っているか確認（[インストール手順](docs/install.md) 参照）
- Windows: `%LOCALAPPDATA%\Sayane\bin` が PATH に追加されているか確認

### ステップ 2: ローカル Profile Store を初期化

```bash
sayane init
```

**何が起きるか**:

- `~/.sayane/profiles/default/` が作成される
- `sayane.profile.yaml`（プロファイル本体）と `context/` フォルダ（文脈用 Markdown）が用意される
- 初回は Git で自動コミットされる場合があります（履歴用）

### ステップ 3: サンプル Profile からプロンプトを生成

リポジトリを clone 済みの場合、同梱の最小サンプルで試せます。

```bash
cd /path/to/sayane   # clone 先
sayane compile --target chatgpt --profile examples/profiles/minimal.yaml
```

**何が起きるか**:

- 標準出力に **JSON** が表示される（ChatGPT 向けの `messages` など）
- これが「Profile → Prompt IR → Adapter」の結果です

Claude 向けも試す場合:

```bash
sayane compile --target claude --profile examples/profiles/minimal.yaml
```

### ステップ 4: 自分の Profile を確認（任意）

```bash
sayane profile inspect
```

`init` で作ったデフォルト Profile の概要（名前・トーン・価値観など）が表示されます。

### この5分で確認できること

- [ ] CLI がインストールされ、`sayane --version` が動く
- [ ] `sayane init` で `~/.sayane/` が作られる
- [ ] `sayane compile` で JSON 形式のプロンプトが得られる

---

## ローカルに作られるファイル

```text
~/.sayane/
  bridge.token                 # Local Bridge 用トークン（sayane serve 時）
  profiles/
    default/
      sayane.profile.yaml      # メイン Profile（編集する正本）
      context/
        MyContext.md           # 文脈メモ（例）
        AI_HANDOFF.md          # 別 AI への引き継ぎ用（例）
  candidates/                  # capture された更新候補（approve 前）
```

**重要**: capture した内容は **すぐには** `sayane.profile.yaml` に反映されません。評価と承認のあとに反映されます（[評価マニュアル](docs/evaluation-manual.md)）。

---

## よくある次の一歩

### A. ターミナルだけで使う（CLI）

```bash
# 自分の Profile で ChatGPT 向けにコンパイル
sayane compile --target chatgpt

# Markdown で確認したいとき
sayane export --format markdown --target chatgpt
```

→ 詳しくは [CLI マニュアル](docs/cli-manual.md)

### B. Cursor / Claude Desktop から使う（MCP）

```bash
sayane mcp list-profiles
sayane mcp compile --target chatgpt --profile-id default
```

クライアント側の MCP 設定は [MCP マニュアル](docs/mcp-manual.md) を参照してください。

### C. ブラウザで capture・挿入する（Extension + Bridge）

ターミナル 1:

```bash
sayane serve
# 表示される Bearer token を Extension の設定に入力
```

ターミナル 2（Extension ビルド）:

```bash
cd extension && npm install && npm run build
# Chrome で extension/ を読み込む
```

→ [Bridge マニュアル](docs/bridge-manual.md) / [Extension マニュアル](docs/extension-manual.md)

### D. Markdown 文脈を管理する（Storage）

文脈の正本は `~/.sayane/profiles/default/context/` 配下の **Markdown** です。次のどちらでも構いません。

**A. 直接編集する（Obsidian 不要）**

```bash
# context/MyContext.md などをエディタで編集
sayane storage index    # 新規 .md を追加したときだけ
sayane compile --target chatgpt
```

**B. Obsidian vault などからまとめて取り込む（任意）**

```bash
export SAYANE_OBSIDIAN_VAULT="$HOME/Documents/MyVault"   # vault のパス
sayane storage import
sayane storage index
sayane compile --target chatgpt   # context 本文を Prompt IR に含められる
```

→ [Storage マニュアル](docs/storage-manual.md)

### E. 開発者向け（リポジトリから入れる）

```bash
git clone https://github.com/zyx-corporation/sayane.git
cd sayane
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
sayane init
pytest -q
```

---

## 接続面の選び方

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
                     Chrome Extension    Cursor 等
```

| やりたいこと | おすすめ |
|-------------|---------|
| とにかく手元でプロンプト JSON を得たい | **CLI** |
| Cursor から Profile を参照・compile したい | **MCP Server** |
| ブラウザで文脈を拾って LLM 欄に入れたい | **Chrome Extension** + **Bridge** |
| スクリプトから HTTP で呼びたい | **Local Bridge** |

---

## 今どこまで使えるか（Community Release 1.0）

| 接続面 | 現状 | 主な用途 |
|--------|------|----------|
| CLI | 利用可能 | `init` / `compile` / `candidate` / `storage` |
| Local Bridge | 利用可能 | `sayane serve` + HTTP API |
| MCP Server | 利用可能 | Cursor / Claude Desktop 連携 |
| Chrome Extension | 利用可能 | capture / 文脈挿入 / candidate 操作 |
| RDE / Candidate 評価 | 利用可能 | `evaluate` / `approve` / `reject` / lineage |
| Storage（Markdown 文脈 / Git） | 利用可能 | `context/` 運用 / `index` / `import`・`export`（vault 任意） / `commit` |

**Phase 6（Commercial Edition）** の暗号化 SQLite・MSI などは別製品です。概要は [ロードマップ §9](docs/roadmap.md) を参照してください。

---

## 単なる「プロファイル交換」との違い

「Custom Instructions をコピペする」「設定 JSON を丸ごと移す」だけでは、次の点が足りないことがあります。

| 観点 | 典型的なコピペ | Sayane |
|------|----------------|--------|
| データの形 | サービス固有のテキスト | **Sayane Profile** + **Prompt IR** |
| LLM 間の移行 | 同じ文字列を貼る | **target ごとに再コンパイル** |
| 更新 | 上書きするだけ | **Candidate → 評価 → approve** |
| 履歴 | ほぼ残らない | **lineage** で記録 |
| 正本の所在 | 各 SaaS 内 | **ローカル**（`~/.sayane/`） |

設計の詳細: [設計概要](docs/architecture.md) / [Profile と Prompt IR](docs/profile-ir.md)

---

## 中核原則

### 1. 人格と実行基盤を分離する

人格・価値観・方針の正本は、ChatGPT のメモリや Claude のプロジェクト設定ではなく、**ローカルの Sayane Profile** に置きます。

### 2. 中間表現（Prompt IR）を経由する

同じプロンプト文字列を LLM 間でコピーするのではなく、Profile から **毎回コンパイル** します。

```text
同一人格  ≠  同一プロンプト文字列
同一 Profile  →  target ごとに最適化された出力
```

### 3. 意味変化を評価してから反映する

更新は「設定の上書き」ではなく **意味の変化** として扱います。

```text
capture → candidate → evaluate (RDE/UIB) → approve/reject → lineage
         （即 merge しない）
```

---

## 制限事項（v1.0.0 時点）

- `compile` で読み込む context 本文は、プロファイルディレクトリ内のファイルに限定（目安: 約 32KB/ファイル）
- Adapter の **target** は主に **chatgpt** / **claude**（`gemini` 等は未対応の場合あり）
- PyPI パッケージ `sayane` は未公開。インストールは [install.md](docs/install.md) のスクリプトまたは Git タグを利用
- 外部 vault（Obsidian 等）との **リアルタイム双方向同期** は未対応（`import` / `export` は CLI 経由のスナップショット）

---

## ドキュメント（ここから読む）

| 用途 | リンク |
|------|--------|
| 初めての全体像 | [はじめに（利用者ガイド）](docs/getting-started.md) |
| インストール詳細 | [インストール手順](docs/install.md) |
| CLI コマンド一覧 | [CLI マニュアル](docs/cli-manual.md) |
| Bridge API | [Bridge マニュアル](docs/bridge-manual.md) |
| MCP 設定 | [MCP マニュアル](docs/mcp-manual.md) |
| ブラウザ拡張 | [Extension マニュアル](docs/extension-manual.md) |
| 評価・承認フロー | [評価マニュアル](docs/evaluation-manual.md) |
| Markdown 文脈 / Git | [Storage マニュアル](docs/storage-manual.md) |
| 一通り試す手順 | [Dogfood 手順書](docs/dogfood-walkthrough.md) |
| 索引 | [ドキュメント索引](docs/index.md) |

---

## アンインストール

CLI だけ削除し、**Profile データは残す**場合の例です。

```bash
# macOS / Linux
rm -rf ~/.local/share/sayane ~/.local/bin/sayane
# ~/.sayane は削除しない（プロファイルを残す）
```

```powershell
# Windows
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Sayane"
# PATH から ...\Sayane\bin を手動削除（設定 → 環境変数）
```

詳細: [install.md#アンインストール](docs/install.md#アンインストール)

---

## 開発・貢献

- [CI 方針](docs/ci.md)
- [開発原則](docs/development-principles.md)
- [ロードマップ](docs/roadmap.md)
- 貢献ガイド（日本語）: [CONTRIBUTING_ja.md](CONTRIBUTING_ja.md)
- 貢献ガイド（英語）: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## License

Apache License 2.0  
SPDX-License-Identifier: Apache-2.0