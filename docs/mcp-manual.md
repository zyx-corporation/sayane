# Omomuki MCP Server マニュアル

Phase 2.5 の MCP Server は、Cursor・Claude Desktop・Cline などの MCP クライアントから、Omomuki Profile を **read-only** で利用するための安定接続面である。

設計: [MCP Server Integration](mcp-integration.md) / セキュリティ: [Security Design](security.md)

## 1. 概要

| 方式 | 用途 |
|------|------|
| **MCP Server（stdio）** | AI クライアントが `omomuki mcp serve` を子プロセス起動 |
| **CLI `omomuki mcp`** | 同じ操作をターミナルから直接実行（デバッグ・スクリプト用） |

Profile の merge・policy 変更・identity 上書きは **行わない**。

## 2. MCP Tools

| Tool | 説明 |
|------|------|
| `list_profiles` | ローカル Profile 一覧 |
| `inspect_profile` | Profile 要約（`profile_id` 既定: `default`） |
| `compile_prompt` | `target`（chatgpt / claude）向けコンパイル |
| `generate_context_packet` | `compile_prompt` と同等（LLM クライアント向け） |
| `list_candidate_updates` | 未 merge の Candidate 一覧 |

## 3. CLI コマンド（MCP と同等）

```bash
omomuki mcp serve
omomuki mcp list-profiles
omomuki mcp inspect-profile --profile-id default
omomuki mcp compile --target chatgpt --profile-id default
omomuki mcp context-packet --target claude --instruction "タスク"
omomuki mcp list-candidates
```

## 4. Cursor / Claude Desktop 設定例

```json
{
  "mcpServers": {
    "omomuki": {
      "command": "omomuki",
      "args": ["mcp", "serve"]
    }
  }
}
```

`omomuki` が PATH にあること。venv 利用時はフルパスを指定する。

```json
{
  "mcpServers": {
    "omomuki": {
      "command": "/path/to/omomuki/.venv/bin/omomuki",
      "args": ["mcp", "serve"]
    }
  }
}
```

## 5. 前提

- `omomuki init` 済み、または `examples/profiles/minimal.yaml` を `--profile-id` 用 Store に配置
- Local Bridge（`omomuki serve`）とは別プロセス。HTTP Bridge ではなく stdio MCP

## 6. Local Bridge との違い

| | Local Bridge | MCP Server |
|--|--------------|------------|
| プロトコル | HTTP (localhost) | MCP (stdio) |
| 主な利用者 | Chrome Extension | AI クライアント |
| 認証 | Bearer token | ローカルプロセス（stdio） |

## 7. トラブルシューティング

| 症状 | 対処 |
|------|------|
| クライアントがサーバーに接続できない | `omomuki` の PATH、venv のフルパス指定 |
| `Profile not found` | `omomuki init`、または `profiles/default/` の存在 |
| `Unknown target` | `chatgpt` / `claude` のみ（`gemini` は未対応） |
| Bridge と混同 | MCP は `mcp serve`（stdio）。HTTP は `omomuki serve` |

## 8. 関連

- [はじめに](getting-started.md)
- [CLI マニュアル](cli-manual.md) — `omomuki mcp` サブコマンド
- [Bridge マニュアル](bridge-manual.md)

## 9. バージョン

Omomuki **0.3.0**（Phase 2.5）時点。
