# Sayane (紗綾音)

Sayane は、LLM間でユーザーの人格的文脈・価値観・応答様式・作業方針を可搬化するための **local-first** ツールです（現行 **0.5.9**）。

ChatGPT、Claude など異なる LLM 実行基盤のあいだで、ユーザーの文脈を構造化し、評価を挟んで Profile へ反映します。LLM は人格の所有者ではなく、**実行基盤**として扱います。

## 中核原則

Sayane の設計は、次の 3 つの命題に支えられています。

### 1. 人格と実行を分離する

> 人格と実行を分離する。

ユーザーの価値観・文体・方針・文脈は **Sayane Profile** としてローカルに保持する。ChatGPT の Custom Instructions、Claude の Project 設定、各 SaaS の「メモリ」などは **実行基盤ごとの投影** に過ぎず、人格の正本ではない。

LLM は人格を「覚えている」主体ではなく、Profile からコンパイルされたプロンプトを **実行する** 側である。

### 2. すべては中間表現（IR）を通る

プロンプト文字列をそのままコピーして LLM 間を行き来するのではない。Profile から **Prompt IR**（LLM 非依存の中間表現）を生成し、**Adapter** が各 LLM 向け形式へ変換する。

```text
同一人格  ≠  同一プロンプト
同一 Profile  →  異なる target ごとに最適化された出力
```

ChatGPT 向けと Claude 向けで payload の形は変わるが、根底にある identity / values / policy は同じ Profile から導かれる。

### 3. 意味変化は評価され、記録される

Profile への更新は「設定の上書き」ではなく **意味変化** として扱う。capture や会話から得た内容は Candidate として一旦保留し、RDE / UIB 評価と **明示的な approve** を経て merge する。approve / reject の履歴は **Lineage** に残る。

```text
capture → Candidate → evaluate（RDE+UIB）→ approve / reject → lineage
         （即 merge しない）
```

```text
Sayane Profile  →  Prompt IR  →  Adapter  →  LLM 出力
        ↑
Candidate（capture）→ RDE 評価 → 承認 merge → Lineage
```

**local-first**: 正本はユーザーのマシン上（`~/.sayane/`）。Community Edition では Git 履歴を既定とする。**Commercial Edition**（Phase 6）— [sayane-pro](https://github.com/zyx-corporation/sayane-pro/blob/main/docs/commercial-edition.md)。

---

## 単なるユーザープロファイル交換との違い

「Custom Instructions をエクスポートして別 LLM に貼る」「アカウント設定 JSON を丸ごと移す」ような **プロファイル交換** とは、Sayane が目指すものは異なります。

| 観点 | 典型的なプロファイル交換 | Sayane |
|------|------------------------|---------|
| **データの形** | プラットフォーム固有のテキストや設定 blob | LLM 非依存の **Sayane Profile** + **Prompt IR** |
| **LLM 間の移行** | 同じ文字列をコピー＆ペースト | Adapter 経由で **target ごとに再コンパイル** |
| **更新の扱い** | 上書き・同期の成否のみ | **Candidate → 評価 → approve** で意味変化を監査 |
| **履歴** | なし、または SaaS 側の限定的ログ | **Lineage** で更新・拒否の記録をユーザーが保持 |
| **文脈の所在** | 各 LLM のメモリ / プロジェクトに分散 | **context_index** + Markdown でローカルに索引 |
| **所有** | ベンダー SaaS 内に閉じがち | **local-first**（ユーザーが正本を保持） |
| **即時反映** | 貼り付け即生效 | capture は **即 merge しない**（Critical Distortion 等は拒否可能） |

Sayane Profile は「自己紹介文の置き場」ではなく、LLM がユーザーの文脈へ **構造的に接近するための媒介** です。単一フィールドの交換ではなく、identity / voice / values / policy / context を分離して保持し、compile 時に Prompt IR へ合成します。

設計の詳細: [architecture.md](docs/architecture.md) / [Profile と Prompt IR](docs/profile-ir.md)

## 現在利用できる機能（Phase 0〜5）

| 接続面 | 用途 |
|--------|------|
| **CLI** | Profile 初期化、compile、Candidate 評価、Storage、help |
| **Local Bridge** | Extension / curl から HTTP API |
| **MCP Server** | Cursor、Claude Desktop 等（stdio） |
| **Chrome Extension** | ブラウザ capture・文脈挿入・Candidate 操作（popup、ja/en UI） |

| Phase | 内容 |
|-------|------|
| 1 | `init`, `compile`, `export`, Profile → Prompt IR |
| 2 | `sayane serve`（Bridge） |
| 2.5 | `sayane mcp serve` |
| 3 | Chrome Extension（capture / insert） |
| 4 | Candidate + RDE/UIB + approve + lineage |
| 4 拡張 | Level 2/3 LLM judge、`--force-critical` merge |
| 5 | Obsidian import/export、context index、Git commit |

## クイックインストール

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.ps1 | iex
```

→ [インストール](docs/install.md)

## クイックスタート（開発者）

```bash
git clone <repository>
cd sayane
pip install -e ".[dev]"

export SAYANE_LANG=ja              # 任意: CLI 日本語（未設定時は LANG を参照）
export SAYANE_OBSIDIAN_VAULT=~/…   # 任意: storage import/export の既定 vault
sayane init
sayane help
sayane compile --target chatgpt --profile examples/profiles/minimal.yaml
```

**初めての方**: [はじめに（利用者ガイド）](docs/getting-started.md)  
**一通り試す**: [Dogfood 手順書](docs/dogfood-walkthrough.md)

## 主要 CLI（抜粋）

```bash
# Profile / プロンプト
sayane --version
sayane profile inspect
sayane compile --target chatgpt
sayane export --format markdown --target claude

# Bridge
sayane serve

# Candidate（評価・merge）
sayane candidate list
sayane candidate evaluate <id> --level 2
sayane candidate diff <id>
sayane candidate approve <id>

# Storage（Obsidian / Git）
export SAYANE_OBSIDIAN_VAULT="$HOME/Documents/MyVault"  # 存在する vault
sayane storage import          # vault 引数省略可（import/index は Git 自動コミット）
sayane storage export
sayane storage index
# storage commit は任意（自動コミットで足りない場合）

# ヘルプ
sayane help
sayane help candidate evaluate
```

## Sayane Profile が持つもの

- **identity** — 基本情報
- **voice** — 文体・口調
- **values** — 価値観・判断基準
- **knowledge** — 概念・テーマ
- **policy** — 応答制約
- **context_index** — 文脈 Markdown への目次
- **lineage** — 更新履歴

Profile は人格そのものではなく、LLM がユーザーの文脈へ接近するための **構造化媒介** です。

## Candidate 評価（RDE）

capture した内容は即 merge しません。

```text
capture → Candidate → evaluate（RDE+UIB）→ approve / reject → lineage
```

- Level 1: ヒューリスティック（既定）
- Level 2/3: 任意の LLM-as-a-Judge（[評価マニュアル](docs/evaluation-manual.md)）
- `Critical Distortion` は原則 auto-approve 不可

## マニュアル

| 用途 | ドキュメント |
|------|----------------|
| 全体ガイド | [getting-started.md](docs/getting-started.md) |
| インストール | [install.md](docs/install.md) |
| CLI | [cli-manual.md](docs/cli-manual.md) |
| Bridge | [bridge-manual.md](docs/bridge-manual.md) |
| MCP | [mcp-manual.md](docs/mcp-manual.md) |
| Extension | [extension-manual.md](docs/extension-manual.md) / [受け入れテスト](docs/extension-acceptance-test.md) |
| 評価 / Candidate | [evaluation-manual.md](docs/evaluation-manual.md) |
| Storage | [storage-manual.md](docs/storage-manual.md) |
| Dogfood | [dogfood-walkthrough.md](docs/dogfood-walkthrough.md) |
| 設計 | [architecture.md](docs/architecture.md) / [roadmap.md](docs/roadmap.md) / [商用版（sayane-pro）](https://github.com/zyx-corporation/sayane-pro/blob/main/docs/commercial-edition.md) |
| 開発 | [development-principles.md](docs/development-principles.md) |

索引: [docs/index.md](docs/index.md)

## 実装スタック

```text
Core / CLI / Bridge : Python
Chrome Extension  : TypeScript
Schema / IR       : JSON Schema + Pydantic
将来の高速化・商用ストレージ : [Commercial Edition（sayane-pro）](https://github.com/zyx-corporation/sayane-pro/blob/main/docs/commercial-edition.md)
```

## ライセンス

Apache License 2.0 — SPDX-License-Identifier: Apache-2.0
