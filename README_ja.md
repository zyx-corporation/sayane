# Sayane（紗綾音）

**LLMをまたいで、人格的文脈・応答様式・価値観を持ち運ぶための local-first ツール。**

Sayane は、ユーザーの人格的文脈、作業スタイル、価値観、応答の好み、長期的なコンテキストを、特定の LLM プラットフォームに閉じ込めず、ユーザー自身の手元で管理するためのツールです。

ChatGPT、Claude、Gemini、Cursor、ローカルLLMなどを「人格の所有者」として扱うのではなく、Sayane は手元の **Sayane Profile** を正本として保持し、それを LLM 非依存の **Prompt IR** に変換し、各ランタイム向けに最適化されたプロンプトとして出力します。

```text
人格は、LLMランタイムに所有されるものではない。
ユーザーの手元に保存され、明示的に構造化され、必要に応じて各LLMへ投影される。
```

---

## Sayane がすること

Sayane は、複数の LLM を使い分けながら、自分の文脈を持ち運びたい人のためのツールです。

主に次のことを行います。

- 人格・文脈・価値観・応答様式を local-first に保存する
- 同一の Profile から ChatGPT / Claude 向けプロンプトを生成する
- ベンダー固有の memory / project / custom instructions へのロックインを避ける
- 新しい文脈を Candidate として capture する
- 長期 Profile に merge する前に意味変化を評価する
- approve / reject の履歴を lineage として残す
- CLI、Local Bridge、MCP Server、Chrome Extension、Obsidian、Git と連携する

Sayane にとって、LLM は人格の所有者ではありません。

LLM は、Sayane Profile から生成されたプロンプトを実行する **実行基盤** です。

---

## なぜ必要か

現在の LLM 利用では、ユーザーの文脈は次のような場所に散らばりがちです。

- Custom Instructions
- Project settings
- vendor memory
- chat history
- local notes
- prompt snippets
- IDE agents
- browser sessions

その結果、ユーザーは自分自身の文脈を、毎回手作業でコピーしながら移動することになります。

```text
ユーザーは、自分自身の断片をコピーすることでしか、LLM間を移動できない。
```

Sayane は、この状態を変えるために、次の分離を行います。

- persona と runtime を分離する
- profile と prompt を分離する
- capture と merge を分離する
- generation と evaluation を分離する
- memory と vendor lock-in を分離する

目的は、同じプロンプト文字列を各LLMへ貼り付けることではありません。

目的は、ユーザーの文脈の正本を構造化して保持し、それを必要なランタイムへ適切に変換することです。

---

## 現在の状態

Sayane は現在 **pre-alpha** 段階です。

Community Edition では、次の構成が利用できます。

| 領域 | 状態 | 用途 |
|------|------|------|
| Core Profile / Prompt IR | 利用可能 | 人格・文脈の構造化モデル |
| CLI | 利用可能 | `init`, `compile`, `export`, profile inspect など |
| Local Bridge | 利用可能 | Extension / 自動化用のローカル HTTP API |
| MCP Server | 利用可能 | Cursor / Cline / Claude Desktop 風クライアントとの連携 |
| Chrome Extension | 利用可能 | ブラウザ上での capture / insert |
| RDE / Candidate 評価 | 利用可能 | capture された意味変化を merge 前に評価 |
| Storage / Obsidian / Git | 利用可能 | Markdown vault の import / index / Git 履歴管理 |

Commercial Edition の機能は別途計画中です。詳細は [`docs/roadmap.md`](docs/roadmap.md) を参照してください。

---

## Quick Start

### ソースからインストール

```bash
git clone https://github.com/zyx-corporation/sayane.git
cd sayane

python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

### ローカル Profile Store を初期化

```bash
sayane init
sayane profile inspect
```

既定では、Sayane のローカルデータは次の場所に保存されます。

```text
~/.sayane/
```

### サンプル Profile を compile する

```bash
sayane compile --target chatgpt --profile examples/profiles/minimal.yaml
```

### Markdown として export する

```bash
sayane export --format markdown --target claude \
  --profile examples/profiles/minimal.yaml
```

---

## インストーラ

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
```

### Windows PowerShell

```powershell
irm https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.ps1 | iex
```

詳細、オプション、アンインストール方法は [`docs/install.md`](docs/install.md) を参照してください。

---

## 中核概念

### 1. Sayane Profile

**Sayane Profile** は、ユーザーの人格的文脈と長期コンテキストの正本です。

Profile には、たとえば次の情報を含めます。

- identity
- tone / response preferences
- values
- policy preferences
- project context
- working style
- long-term notes
- context references

Profile は、単なるプロンプト文字列ではありません。

LLM 向けプロンプトへ変換可能な、構造化されたデータです。

---

### 2. Prompt IR

**Prompt IR** は、LLM 非依存の中間表現です。

Sayane は、同じプロンプト文字列をすべてのプラットフォームにコピーするわけではありません。

```text
同じ人格 ≠ 同じプロンプト
1つの Profile → Prompt IR → ターゲット別出力
```

LLM ランタイムごとに、期待される形式、制約、文体、コンテキストの渡し方は異なります。

Sayane は、意味の正本を安定させながら、出力形式をターゲットごとに最適化します。

---

### 3. Adapter

**Adapter** は、Prompt IR をターゲット別の出力へ compile する層です。

現在の対応ターゲットは次の通りです。

| Target | 状態 |
|--------|------|
| ChatGPT | 利用可能 |
| Claude | 利用可能 |

将来的には、Profile の正本を変えずに、Adapter を追加できます。

---

### 4. Candidate

capture された文脈は、すぐに長期 Profile へ merge されるわけではありません。

まず **Candidate** として保存されます。

```text
capture → Candidate → evaluate → approve / reject → lineage
```

これにより、LLM の出力や要約によって、ユーザーの文脈が無自覚に変化することを避けます。

---

### 5. RDE / UIB 評価

Sayane は、Profile 更新を単なるテキスト変更ではなく、**意味変化** として扱います。

Candidate は merge 前に、RDE / UIB に着想を得た評価を通過できます。

実用上は、次のような問いを扱います。

- 何が意味として変化したか
- 既存 Profile と整合しているか
- ユーザーの意図を保存しているか
- 正当な補完か、不審な drift か
- approve すべきか、reject すべきか

Sayane は、LLM の memory を魔法のように賢くするツールではありません。

記憶の変化を、見えるものとして扱うためのツールです。

---

### 6. Lineage

approve / reject された変更は、lineage として記録されます。

これにより、Sayane は次の問いに答えられるようになります。

```text
現在の Profile は何か。
```

だけでなく、

```text
この Profile はどのように形成されたのか。
どの変更が承認されたのか。
どの変更が拒否されたのか。
```

を追跡できます。

---

## アーキテクチャ

```text
Sayane Profile
      ↓
Prompt IR
      ↓
Strategy
      ↓
Adapter
      ↓
Target LLM Runtime
```

Candidate 評価と lineage は、別の更新経路として扱います。

```text
Capture
   ↓
Candidate
   ↓
RDE / UIB Evaluation
   ↓
Approve / Reject
   ↓
Lineage
   ↓
Profile Update
```

local-first storage は、これらの下にあります。

```text
~/.sayane/
  bridge.token
  profiles/
    default/
      sayane.profile.yaml
      context/
  candidates/
```

---

## インターフェイス

Sayane は、複数の接続面を提供します。

### CLI

CLI は、もっとも直接的なローカル操作用インターフェイスです。

```bash
sayane init
sayane profile inspect
sayane compile --target chatgpt
sayane export --format markdown --target claude
```

詳細は [`docs/cli-manual.md`](docs/cli-manual.md) を参照してください。

---

### Local Bridge

ローカル HTTP Bridge を起動します。

```bash
sayane serve
```

Bridge は、ブラウザ拡張やローカル自動化から利用されます。

詳細は [`docs/bridge-manual.md`](docs/bridge-manual.md) を参照してください。

---

### MCP Server

Sayane を MCP Server として起動できます。

```bash
sayane mcp serve
```

Cursor、Cline、Claude Desktop 風の MCP 対応クライアントとの連携に使えます。

詳細は [`docs/mcp-manual.md`](docs/mcp-manual.md) を参照してください。

---

### Chrome Extension

Chrome Extension は、ブラウザ上での capture / insert ワークフローを支援します。

開発時の典型的な手順は次の通りです。

```bash
cd extension
npm install
npm run build
```

その後、Chrome で extension ディレクトリを読み込み、Local Bridge の token を設定します。

詳細は [`docs/extension-manual.md`](docs/extension-manual.md) を参照してください。

---

### Obsidian / Git storage

Sayane は、ローカル Markdown context を import / index できます。

```bash
export SAYANE_OBSIDIAN_VAULT="$HOME/Documents/MyVault"

sayane storage import
sayane storage index
sayane compile --target chatgpt
```

詳細は [`docs/storage-manual.md`](docs/storage-manual.md) を参照してください。

---

## 単なる Profile export ではない

Sayane は、単なる profile exchange / export ツールではありません。

| 観点 | 一般的な profile export | Sayane |
|------|--------------------------|--------|
| データ形式 | プラットフォーム固有のテキスト | 構造化 Profile + Prompt IR |
| LLM 間移動 | コピー＆ペースト | ターゲット別 compile |
| 更新 | 上書き | Candidate → evaluate → approve |
| 履歴 | ほぼ存在しない | ユーザー管理の lineage |
| 保存場所 | vendor memory / app settings | local-first profile store |
| 文脈 | ツールごとに分散 | local context index |
| 安全性 | 即時適用 | merge 前レビュー |

中心的な違いは、次の点にあります。

```text
Profile export はテキストを移動する。
Sayane は、人格的文脈の状態を保存し、その変化を評価する。
```

---

## 設計原則

### persona と runtime を分離する

LLM はプロンプトを実行します。

人格を所有するわけではありません。

ユーザーの価値観、作業様式、長期文脈は、特定ベンダーの memory system に閉じ込められるべきではありません。

---

### 中間表現を使う

Sayane は、どこでも通用する単一プロンプトを仮定しません。

```text
Profile → Prompt IR → Adapter → Target Output
```

これにより、各 LLM ランタイムは正本ではなく、投影先になります。

---

### 意味変化を評価する

Profile 更新は、意味的な出来事です。

Sayane は、更新候補を Candidate として capture し、評価し、approve 後に merge します。

これは、LLM がユーザーの好みや価値観を要約・圧縮・推測する場面で特に重要です。

---

### local-first である

正本は、ユーザーの手元にあります。

将来的にクラウド連携が追加されるとしても、設計の出発点は local ownership と inspectability です。

---

## ドキュメント

プロジェクト文書は [`docs/`](docs/) 以下にあります。

| Topic | Manual |
|-------|--------|
| Getting started | [`docs/getting-started.md`](docs/getting-started.md) |
| Install | [`docs/install.md`](docs/install.md) |
| CLI | [`docs/cli-manual.md`](docs/cli-manual.md) |
| Local Bridge | [`docs/bridge-manual.md`](docs/bridge-manual.md) |
| MCP Server | [`docs/mcp-manual.md`](docs/mcp-manual.md) |
| Chrome Extension | [`docs/extension-manual.md`](docs/extension-manual.md) |
| RDE / Candidate evaluation | [`docs/evaluation-manual.md`](docs/evaluation-manual.md) |
| Storage / Obsidian / Git | [`docs/storage-manual.md`](docs/storage-manual.md) |
| Profile and Prompt IR | [`docs/profile-ir.md`](docs/profile-ir.md) |
| Security Design | [`docs/security.md`](docs/security.md) |
| Roadmap | [`docs/roadmap.md`](docs/roadmap.md) |

---

## 開発

開発依存関係をインストールします。

```bash
pip install -e ".[dev]"
```

テストを実行します。

```bash
pytest
```

lint を実行します。

```bash
ruff check .
```

format を実行します。

```bash
ruff format .
```

CI と開発ワークフローの詳細は [`docs/ci.md`](docs/ci.md) を参照してください。

---

## 成熟度

Sayane は pre-alpha ソフトウェアです。

現時点では、次の変更がありえます。

- API 変更
- schema 変更
- Adapter の追加・変更
- 評価ロジックの変更
- CLI 挙動の変更
- ドキュメント不足

次の関心がある場合は、現段階でも試す価値があります。

- local-first な LLM workflow design
- persona / context portability
- prompt compilation
- MCP integration
- semantic lineage
- RDE 的な意味変化評価

安定した production SDK が必要な場合は、まだ早い段階です。

---

## Roadmap

近い方向性は次の通りです。

- Profile / Prompt IR schema の改善
- Adapter coverage の拡張
- Candidate 評価の強化
- Chrome Extension workflow の改善
- Obsidian / Git integration の改善
- example / acceptance test の追加
- Community Edition / Commercial Edition の境界整理

詳細は [`docs/roadmap.md`](docs/roadmap.md) を参照してください。

---

## Contributing

貢献を歓迎します。

特に歓迎するものは次の通りです。

- documentation improvements
- examples
- tests
- adapter experiments
- bug reports
- CLI usability feedback
- MCP client integration notes
- Chrome Extension testing
- storage / Obsidian workflow feedback

大きな設計変更の前には、Issue または Discussion で相談してください。

初回貢献としては、次のようなものが向いています。

- Quick Start example の改善
- sample profile の追加
- adapter test case の追加
- error message の明確化
- setup problem の記録
- screenshot / GIF の追加

---

## Security and privacy

Sayane は local-first ですが、local-first であることは自動的な安全を意味しません。

次の取り扱いには注意してください。

- personal context
- API keys
- bridge tokens
- exported prompts
- browser extension permissions
- copied LLM outputs
- Obsidian vault imports

詳細は [`docs/security.md`](docs/security.md) を参照してください。

---

## License

Sayane is licensed under the Apache License, Version 2.0.

SPDX-License-Identifier: Apache-2.0
