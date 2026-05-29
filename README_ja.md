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
- Obsidian などのメモと、LLM 用の文脈をつなげたい

---

## Sayane でできること（かんたんに）

| やりたいこと | Sayane のやり方 |
|-------------|----------------|
| 自分用の「人格・方針」を一か所にまとめる | ローカルの **Sayane Profile**（`~/.sayane/`） |
| ChatGPT 用・Claude 用にそれぞれプロンプトを作る | **compile**（中間表現 Prompt IR 経由） |
| ブラウザで拾った文脈を保存する | **capture** → **Candidate**（すぐには反映しない） |
| 反映してよいか判断してから更新する | **evaluate** → **approve** / **reject** |
| 更新の履歴を残す | **lineage**（採用・拒否の記録） |
| Obsidian のメモを取り込む | **storage import** / **index** |

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