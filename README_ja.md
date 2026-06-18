# Sayane（紗綾音）

[English README](README.md) · [ドキュメント索引](docs/index.md) · [ロードマップ](docs/roadmap.md)

**Sayane は、LLM との作業における人格設定・文脈・プロンプト・監査履歴を、ローカルファーストに保持し、持ち運び、レビュー可能にするツールキットです。**

ChatGPT、Claude、Gemini、Cursor、ローカル LLM などを使い分けると、文脈は簡単に分断されます。どの前提で話していたのか、どの価値観や文体を使っていたのか、会話から得た学びを本当に自分のプロファイルへ反映してよいのか。Sayane は、その判断を各サービスの「メモリ」に閉じ込めず、自分の PC 上で管理できるようにします。

モデルを変えても、あなたの文脈は消えるべきではありません。

**現行バージョン**: Community Edition **v1.0.12**（PyPI: `pip install sayane`）

---

## Sayane が解決したいこと

AI 活用が本格化すると、単なるプロンプト管理だけでは足りなくなります。

- ChatGPT と Claude で、毎回同じ自己紹介・方針をコピペしている
- ある LLM 用の設定を別の LLM に移したいが、形式が違って困る
- 会話から得た学びを、いきなりプロファイルへ上書きしたくない
- AI がどの立場・文脈・制約から応答したのかを後から追いたい
- Obsidian や Markdown の知識メモを、LLM 用の文脈として使いたい
- 特定ベンダーのメモリ機能に、自分の文脈を閉じ込めたくない

Sayane は、人格・文脈・更新候補・承認履歴を、ローカルに置かれた検証可能な作業資産として扱います。

---

## Sayane でできること

| やりたいこと | Sayane の仕組み |
|-------------|----------------|
| 自分用の人格・方針・文脈を一か所にまとめる | ローカルの **Sayane Profile**（`~/.sayane/`） |
| ChatGPT 用・Claude 用などにプロンプトを生成する | **Profile → Prompt IR → Adapter** |
| ブラウザや会話から文脈を取り込む | **capture → Candidate** |
| 反映してよいか判断してから更新する | **evaluate → approve / reject** |
| 採用・拒否の履歴を残す | **lineage** |
| Markdown 文脈を Profile に載せる | `context/` / storage index / filesystem-first 運用 |
| エディタや外部ツールから使う | CLI / Local Bridge / MCP Server / Chrome Extension（legacy） |

---

## 基本用語

### Sayane Profile（プロファイル）

あなたの **identity（名前・役割）**、**voice（文体）**、**values（価値観）**、**policy（応答方針）**、**context（作業文脈）** などを YAML と Markdown で管理する「正本」です。通常は `~/.sayane/profiles/default/sayane.profile.yaml` に置かれます。

### Prompt IR（プロンプト中間表現）

LLM に依存しない中間フォーマットです。同じ Profile から、ChatGPT、Claude、Gemini、DeepSeek、local-openwebui など、target ごとに異なる形式へ変換するための土台になります。

### Adapter（アダプター）

Prompt IR を各 LLM が期待する形式へ変換する層です。たとえば OpenAI 系の `messages`、Anthropic 系の構造などへ変換します。

### Candidate（更新候補）

会話や capture で得た「プロファイルへ入れたい変更案」です。承認するまで、本番の Profile には merge されません。

### lineage（更新の来歴）

どの Candidate を採用・拒否したかの記録です。後から「いつ、何が、なぜ変わったか」を追えるようにします。

---

## 全体の流れ

```text
Sayane Profile（ローカルの正本）
        ↓
Prompt IR（LLM 非依存の中間表現）
        ↓
Adapter（ChatGPT / Claude / Gemini / local など）
        ↓
target ごとのプロンプト出力

capture した文脈 → Candidate → 評価 → approve/reject → lineage
```

LLM は人格の所有者ではありません。LLM は、ローカルの Profile からコンパイルされたプロンプトを受け取って実行する側です。

---

## 5分で試す

### 1. CLI をインストール

**PyPI**（Python 3.11+）:

```bash
pip install 'sayane==1.0.12'
```

**macOS / Linux**:

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
```

特定バージョンを指定する場合:

```bash
SAYANE_REF=v1.0.12 curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
```

**Windows PowerShell**:

```powershell
irm https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.ps1 | iex
```

インストール後、新しいターミナルを開いて確認します。

```bash
sayane --version
```

`command not found` になる場合は、macOS/Linux では `~/.local/bin`、Windows では `%LOCALAPPDATA%\Sayane\bin` が PATH に入っているか確認してください。詳しくは [インストール手順](docs/install.md) を参照してください。

### 2. ローカル Profile Store を初期化

```bash
sayane init
```

これにより、通常は次の構成が作られます。

```text
~/.sayane/
  bridge.token                 # Local Bridge 用トークン（sayane serve 時）
  profiles/
    default/
      sayane.profile.yaml      # メイン Profile
      context/                 # 文脈用 Markdown
        MyContext.md
        AI_HANDOFF.md
  candidates/                  # capture された更新候補
```

重要: capture した内容は、すぐには `sayane.profile.yaml` に反映されません。評価と承認のあとに反映されます。

### 3. サンプル Profile からプロンプトを生成

リポジトリを clone 済みの場合、同梱の最小サンプルで試せます。

```bash
cd /path/to/sayane
sayane compile --target chatgpt --profile examples/profiles/minimal.yaml
```

Claude 向けも試す場合:

```bash
sayane compile --target claude --profile examples/profiles/minimal.yaml
```

この5分で、Profile → Prompt IR → Adapter という最小フローを確認できます。

---

## よくある使い方

### A. ターミナルだけで使う（CLI）

```bash
# 自分の Profile で ChatGPT 向けにコンパイル
sayane compile --target chatgpt

# Markdown で確認したいとき
sayane export --format markdown --target chatgpt
```

詳しくは [CLI マニュアル](docs/cli-manual.md) を参照してください。

### B. Cursor / Claude Desktop から使う（MCP）

```bash
sayane mcp list-profiles
sayane mcp compile --target chatgpt --profile-id default
```

クライアント側の設定は [MCP マニュアル](docs/mcp-manual.md) を参照してください。

### C. ブラウザで capture・挿入する（Extension + Bridge / legacy）

Chrome Extension は引き続き利用できるが、現行方針では **freeze / deprecated** であり、新規導入の主経路ではない。

ターミナル 1:

```bash
sayane serve
# 表示される Bearer token を Extension の設定に入力
```

ターミナル 2:

```bash
cd extension && npm install && npm run build
# Chrome で extension/ を読み込む
```

詳しくは [Bridge マニュアル](docs/bridge-manual.md) と [Extension マニュアル](docs/extension-manual.md) を参照してください。

### D. Markdown 文脈を管理する（Storage）

文脈の正本は `~/.sayane/profiles/default/context/` 配下の Markdown として扱えます。

直接編集する場合:

```bash
# context/MyContext.md などをエディタで編集
sayane storage index
sayane compile --target chatgpt
```

Obsidian vault などとの連携は互換運用として残っているが、現行方針では primary path ではない。

Obsidian vault などから取り込む場合:

```bash
export SAYANE_OBSIDIAN_VAULT="$HOME/Documents/MyVault"
sayane storage import
sayane storage index
sayane compile --target chatgpt
```

詳しくは [Storage マニュアル](docs/storage-manual.md) を参照してください。

### E. 開発者向けにリポジトリから入れる

```bash
git clone https://github.com/zyx-corporation/sayane.git
cd sayane
python -m venv .venv
source .venv/bin/activate
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
      └────┬────┘     └─────┬─────┘    └─────┬──────┘
           │                │                │
           ▼                ▼                ▼
     Terminal / shell   Chrome Extension   Cursor 等
```

| やりたいこと | おすすめ |
|-------------|---------|
| とにかく手元でプロンプト JSON を得たい | **CLI** |
| Cursor から Profile を参照・compile したい | **MCP Server** |
| ブラウザで文脈を拾って LLM 欄に入れたい | **Chrome Extension + Bridge** |
| スクリプトから HTTP で呼びたい | **Local Bridge** |

---

## 今どこまで使えるか

Community Edition **v1.0.12** では、以下が利用可能です。

| 接続面 | 現状 | 主な用途 |
|--------|------|----------|
| CLI | 利用可能 | `init` / `compile` / `candidate` / `storage` |
| Local Bridge | 利用可能 | `sayane serve` + HTTP API |
| MCP Server | 利用可能 | Cursor / Claude Desktop 連携 |
| Chrome Extension | 凍結 / 非推奨 | 既存利用者向けの capture / 文脈挿入 / candidate 操作 |
| RDE / Candidate 評価 | 利用可能 | `evaluate` / `approve` / `reject` / lineage |
| Storage | 利用可能 | local Markdown / filesystem-first。Obsidian / Git は互換運用 |

**Phase 6（Commercial Edition）** の暗号化 SQLite・MSI などは別製品です。概要は [ロードマップ](docs/roadmap.md) を参照してください。

---

## 単なるプロンプト管理との違い

Sayane は、プロンプト断片を保存するだけのツールではありません。

| 観点 | 典型的なコピペ運用 | Sayane |
|------|------------------|--------|
| データの形 | サービス固有のテキスト | **Sayane Profile + Prompt IR** |
| LLM 間の移行 | 同じ文字列を貼る | **target ごとに再コンパイル** |
| 更新 | 上書きするだけ | **Candidate → 評価 → approve/reject** |
| 履歴 | ほぼ残らない | **lineage** で記録 |
| 正本の所在 | 各 SaaS 内 | **ローカル**（`~/.sayane/`） |

設計の詳細は [設計概要](docs/architecture.md) と [Profile と Prompt IR](docs/profile-ir.md) を参照してください。

---

## 中核原則

### 1. 人格と実行基盤を分離する

人格・価値観・文体・作業方針の正本は、ChatGPT のメモリや Claude のプロジェクト設定ではなく、ローカルの Sayane Profile に置きます。

### 2. 中間表現（Prompt IR）を経由する

同じプロンプト文字列を LLM 間でコピーするのではなく、Profile から target ごとに再コンパイルします。

```text
同一人格  ≠  同一プロンプト文字列
同一 Profile  →  target ごとに最適化された出力
```

### 3. 意味変化を評価してから反映する

更新は、単なる設定変更ではなく「意味の変化」として扱います。

```text
capture → candidate → evaluate (RDE/UIB-inspired review) → approve/reject → lineage
         （即 merge しない）
```

### 4. local-first を優先する

本気で AI を使うほど、文脈は資産になります。Sayane は、その資産を特定サービスの記憶機能だけに依存させず、手元に残し、移動でき、検証できる形で扱います。

---

## 制限事項（v1.0.12 時点）

- `compile` で読み込む context 本文は、プロファイルディレクトリ内のファイルに限定されます（目安: 約 32KB/ファイル）
- Adapter target: `chatgpt` / `claude` / `gemini` / `deepseek` / `local-openwebui`
- PyPI で入るのは CLI + Bridge + MCP です。Chrome Extension は別途ビルドが必要で、位置づけも freeze / deprecated です
- 外部 vault（Obsidian 等）とのリアルタイム双方向同期は未対応です。`import` / `export` は CLI 経由のスナップショットです

---

## ドキュメント

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

CLI だけ削除し、Profile データは残す場合の例です。

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

詳細は [install.md#アンインストール](docs/install.md#アンインストール) を参照してください。

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
