# Sayane（紗綾音）

Sayane は、**複数の LLM 間でユーザー文脈を持ち運ぶ local-first ツール**です。  
Profile（人格的文脈の正本）をローカルに保持し、ChatGPT / Claude などの target 向けにコンパイルして使います。

## 何をするツールか

- **文脈の正本をローカル管理**（`~/.sayane/`）
- **target ごとにプロンプト生成**（Prompt IR → Adapter）
- **capture を即 merge しない**（candidate 評価 + approve/reject）
- **履歴を lineage（更新の来歴）で追跡**（何を採用/拒否したか）

## 5分で確認できること

まずは CLI をインストールします（詳細は [docs/install.md](docs/install.md)）。

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
```

```powershell
# Windows (PowerShell)
irm https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.ps1 | iex
```

インストール後、動作確認します。

```bash
sayane --version
sayane init
sayane compile --target chatgpt --profile examples/profiles/minimal.yaml
```

この5分で、次を確認できます。

- CLI が正しくインストールされている
- ローカル Profile Store が作成される
- サンプル Profile から target 向け出力が生成される

### アンインストール

```bash
# macOS / Linux
rm -rf ~/.local/share/sayane ~/.local/bin/sayane
# Profile データを残す場合は ~/.sayane は削除しない
```

```powershell
# Windows
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Sayane"
# PATH から ...\Sayane\bin を手動削除（設定 → 環境変数）
```

詳細は [docs/install.md#アンインストール](docs/install.md#アンインストール) を参照。

## 今どこまで使えるか（Community Release 1.0 / v1.0.0）

| 接続面 | 現状 | 主な用途 |
|--------|------|----------|
| CLI | 利用可能 | init / compile / candidate / storage |
| Local Bridge | 利用可能 | `sayane serve` + HTTP API |
| MCP Server | 利用可能 | Cursor / Claude Desktop 連携 |
| Chrome Extension | 利用可能 | capture / context insert / candidate 操作 |
| RDE / Candidate 評価 | 利用可能 | evaluate / approve / reject / lineage（更新の来歴） |
| Storage (Obsidian / Git) | 利用可能 | import / index / export / commit |

## Start Here

- [インストール手順](docs/install.md)
- [はじめに（利用者ガイド）](docs/getting-started.md)
- [CLI マニュアル](docs/cli-manual.md)
- [Bridge マニュアル](docs/bridge-manual.md)
- [MCP マニュアル](docs/mcp-manual.md)
- [Extension マニュアル](docs/extension-manual.md)
- [評価マニュアル](docs/evaluation-manual.md)
- [Storage マニュアル](docs/storage-manual.md)
- [ドキュメント索引](docs/index.md)

## Core principles

### 1. 人格と実行基盤を分離する

人格の正本はベンダー memory ではなく、ローカルの Sayane Profile に置く。

### 2. 中間表現（Prompt IR）を経由する

同じ文字列をコピーするのではなく、Profile から target ごとに再コンパイルする。

### 3. 意味変化を評価してから反映する

```text
capture → candidate → evaluate (RDE/UIB) → approve/reject → lineage（更新の来歴）
```

## Development

- [CI 方針](docs/ci.md)
- [開発原則](docs/development-principles.md)
- [ロードマップ](docs/roadmap.md)

## License

Apache License 2.0  
SPDX-License-Identifier: Apache-2.0
