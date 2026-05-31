# Sayane MCP Server マニュアル

Phase 2.5 の MCP Server は、Cursor・Claude Desktop・Cline などの MCP クライアントから Sayane を利用する安定接続面である。Profile の compile・参照に加え、Candidate の評価・承認も可能（`approve_candidate` は明示呼び出し時のみ merge）。

設計: [MCP Server Integration](mcp-integration.md) / セキュリティ: [Security Design](security.md)

## 1. 概要

| 方式 | 用途 |
|------|------|
| **MCP Server（stdio）** | AI クライアントが `sayane mcp serve` を子プロセス起動 |
| **CLI `sayane mcp`** | 同じ操作をターミナルから直接実行（デバッグ・スクリプト用） |

Profile への任意編集は **行わない**。Candidate の `approve_candidate` のみ、承認済み提案を Profile へ merge する。

## 2. MCP Tools

| Tool | 説明 |
|------|------|
| `list_profiles` | ローカル Profile 一覧 |
| `inspect_profile` | Profile 要約（`profile_id` 既定: `default`） |
| `compile_prompt` | `target` 向けコンパイル（`chatgpt` / `claude` / `gemini` / `deepseek` / `local-openwebui` 等） |
| `generate_context_packet` | `compile_prompt` と同等（LLM クライアント向け） |
| `list_candidate_updates` | Candidate 一覧 |
| `show_candidate` | Candidate 全文 |
| `evaluate_candidate` | RDE/UIB 評価（`level` 1–3） |
| `diff_candidate` | Profile との diff |
| `approve_candidate` | 承認して merge（`force_critical` 任意） |
| `reject_candidate` | 却下 |

## 3. CLI コマンド（MCP と同等）

```bash
sayane mcp serve
sayane mcp list-profiles
sayane mcp inspect-profile --profile-id default
sayane mcp compile --target chatgpt --profile-id default
sayane mcp context-packet --target claude --instruction "タスク"
sayane mcp list-candidates
sayane mcp evaluate-candidate <id> --level 1
sayane mcp diff-candidate <id>
sayane mcp approve-candidate <id>
sayane mcp reject-candidate <id> --reason "..."
```

Candidate フロー詳細: [RDE / Candidate 評価マニュアル](evaluation-manual.md)

## 4. Cursor / Claude Desktop 設定例

```json
{
  "mcpServers": {
    "sayane": {
      "command": "sayane",
      "args": ["mcp", "serve"]
    }
  }
}
```

`sayane` が PATH にあること。venv 利用時はフルパスを指定する。

```json
{
  "mcpServers": {
    "sayane": {
      "command": "/path/to/sayane/.venv/bin/sayane",
      "args": ["mcp", "serve"]
    }
  }
}
```

## 5. 前提

- `sayane init` 済み、または `examples/profiles/minimal.yaml` を `--profile-id` 用 Store に配置
- Local Bridge（`sayane serve`）とは別プロセス。HTTP Bridge ではなく stdio MCP

## 6. Local Bridge との違い

| | Local Bridge | MCP Server |
|--|--------------|------------|
| プロトコル | HTTP (localhost) | MCP (stdio) |
| 主な利用者 | Chrome Extension | AI クライアント |
| 認証 | Bearer token | ローカルプロセス（stdio） |

## 7. トラブルシューティング

| 症状 | 対処 |
|------|------|
| クライアントがサーバーに接続できない | `sayane` の PATH、venv のフルパス指定 |
| `Profile not found` | `sayane init`、または `profiles/default/` の存在 |
| `Unknown target` | `chatgpt` / `claude` / `gemini` / `deepseek` / `local-openwebui` 等（`local-custom` は未対応） |
| Bridge と混同 | MCP は `mcp serve`（stdio）。HTTP は `sayane serve` |

## 8. 関連

- [はじめに](getting-started.md)
- [CLI マニュアル](cli-manual.md) — `sayane mcp` サブコマンド
- [Bridge マニュアル](bridge-manual.md)

## 9. バージョン

Sayane **0.3.0**（Phase 2.5）時点。
