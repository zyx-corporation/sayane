# Omomuki

Omomuki は、LLM間でユーザーの人格的文脈・価値観・応答様式・作業方針を可搬化するための **local-first** ツールです（現行 **0.5.4**）。

ChatGPT、Claude など異なる LLM 実行基盤のあいだで、ユーザーの文脈を構造化し、評価を挟んで Profile へ反映します。LLM は人格の所有者ではなく、**実行基盤**として扱います。

## 中核原則

> 人格と実行を分離する。

```text
Omomuki Profile  →  Prompt IR  →  Adapter  →  LLM 出力
        ↑
Candidate（capture）→ RDE 評価 → 承認 merge → Lineage
```

## 現在利用できる機能（Phase 0〜5）

| 接続面 | 用途 |
|--------|------|
| **CLI** | Profile 初期化、compile、Candidate 評価、Storage、help |
| **Local Bridge** | Extension / curl から HTTP API |
| **MCP Server** | Cursor、Claude Desktop 等（stdio） |
| **Chrome Extension** | ブラウザ capture・文脈挿入・Candidate 操作（popup） |

| Phase | 内容 |
|-------|------|
| 1 | `init`, `compile`, `export`, Profile → Prompt IR |
| 2 | `omomuki serve`（Bridge） |
| 2.5 | `omomuki mcp serve` |
| 3 | Chrome Extension（capture / insert） |
| 4 | Candidate + RDE/UIB + approve + lineage |
| 4 拡張 | Level 2/3 LLM judge、`--force-critical` merge |
| 5 | Obsidian import/export、context index、Git commit |

## クイックスタート

```bash
git clone <repository>
cd omomuki
pip install -e ".[dev]"

export OMOMUKI_LANG=ja          # 任意: CLI 日本語表示
omomuki init
omomuki help
omomuki compile --target chatgpt --profile examples/profiles/minimal.yaml
```

**初めての方**: [はじめに（利用者ガイド）](docs/getting-started.md)  
**一通り試す**: [Dogfood 手順書](docs/dogfood-walkthrough.md)

## 主要 CLI（抜粋）

```bash
# Profile / プロンプト
omomuki profile inspect
omomuki compile --target chatgpt
omomuki export --format markdown --target claude

# Bridge
omomuki serve

# Candidate（評価・merge）
omomuki candidate list
omomuki candidate evaluate <id> --level 2
omomuki candidate diff <id>
omomuki candidate approve <id>

# Storage（Obsidian / Git）
omomuki storage import /path/to/vault
omomuki storage index
omomuki storage commit -m "omomuki: update context" --init

# ヘルプ
omomuki help
omomuki help candidate evaluate
```

## Omomuki Profile が持つもの

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
| CLI | [cli-manual.md](docs/cli-manual.md) |
| Bridge | [bridge-manual.md](docs/bridge-manual.md) |
| MCP | [mcp-manual.md](docs/mcp-manual.md) |
| Extension | [extension-manual.md](docs/extension-manual.md) |
| 評価 / Candidate | [evaluation-manual.md](docs/evaluation-manual.md) |
| Storage | [storage-manual.md](docs/storage-manual.md) |
| Dogfood | [dogfood-walkthrough.md](docs/dogfood-walkthrough.md) |
| 設計 | [architecture.md](docs/architecture.md) / [roadmap.md](docs/roadmap.md) |
| 開発 | [development-principles.md](docs/development-principles.md) |

索引: [docs/index.md](docs/index.md)

## 実装スタック

```text
Core / CLI / Bridge : Python
Chrome Extension  : TypeScript
Schema / IR       : JSON Schema + Pydantic
将来の高速化      : Rust（Phase 6 以降）
```

## ライセンス

Apache License 2.0 — SPDX-License-Identifier: Apache-2.0
