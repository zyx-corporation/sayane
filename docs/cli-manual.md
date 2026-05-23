# Omomuki CLI マニュアル

`omomuki` コマンドの利用者向けマニュアルである（Phase 1 CLI + Phase 2 Bridge + Phase 2.5 MCP サブコマンド）。

初めて使う場合は [はじめに](getting-started.md) を先に読むこと。Bridge 詳細は [Bridge マニュアル](bridge-manual.md)、MCP 詳細は [MCP マニュアル](mcp-manual.md)。

設計: [CLI / Local Bridge / Chrome Extension 設計](cli-chrome-extension.md) / データ: [Profile と Prompt IR](profile-ir.md)

## 1. 概要

Omomuki CLI は、ローカルに保持した **Omomuki Profile** から **Prompt IR**（中間表現）を生成し、**Adapter** 経由で各 LLM 向けのリクエスト形式へ変換する制御面である。

```text
omomuki.profile.yaml  →  Prompt IR  →  Adapter  →  JSON / Markdown 出力
```

利用可能な主なコマンドは次のとおりである。

| コマンド | 概要 |
|---------|------|
| `omomuki init` | ローカル Profile Store を初期化する |
| `omomuki profile inspect` | Profile の要約を表示する |
| `omomuki compile` | 指定 LLM 向けにプロンプトをコンパイルする（JSON 出力） |
| `omomuki export` | Prompt IR とコンパイル結果を Markdown で出力する |
| `omomuki serve` | Local Bridge API を起動する（Phase 2） |
| `omomuki mcp serve` | MCP Server（stdio）起動（Phase 2.5） |
| `omomuki mcp list-profiles` など | MCP Tools と同等の CLI 操作 |

Bridge HTTP API の詳細は [Bridge マニュアル](bridge-manual.md)。MCP Tools / Cursor 設定は [MCP マニュアル](mcp-manual.md)。

未実装（ロードマップ参照）: CLI の `capture`, `diff`, `evaluate` など。文脈 capture は Bridge `POST /capture` または Extension から可能。

## 2. インストール

リポジトリルートで editable インストールする。

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

インストール後、次でヘルプを確認できる。

```bash
omomuki --help
omomuki profile --help
omomuki compile --help
```

## 3. Profile Store

### 3.1 既定の配置

`omomuki init` は次のディレクトリを作成する。

```text
~/.omomuki/
  profiles/
    default/
      omomuki.profile.yaml    # メイン Profile
      context/
        MyContext.md          # 文脈ファイル（プレースホルダ）
        AI_HANDOFF.md         # 引き継ぎ用（プレースホルダ）
```

`--profile` を省略したコマンドは、既定で `~/.omomuki/profiles/default/omomuki.profile.yaml` を読み込む。

### 3.2 リポジトリ内のサンプル

開発・検証用の最小 Profile は次にある。

```text
examples/profiles/minimal.yaml
```

README や本マニュアルの例では、必要に応じて `--profile examples/profiles/minimal.yaml` を付与する。

## 4. 処理フロー

### 4.1 compile / export の内部処理

1. YAML から **Omomuki Profile** を読み込み、Pydantic で検証する
2. Profile フィールドから **Prompt IR** を組み立てる（Builder）
3. `--target` に応じた **Adapter** が Prompt IR を LLM 固有形式へ変換する

```text
Profile
  ├─ identity / voice / values / knowledge  →  Prompt IR.system
  ├─ context_index                          →  Prompt IR.context（パス参照）
  ├─ policy.response                        →  Prompt IR.constraints
  └─ --instruction（任意）                  →  Prompt IR.instruction
```

Phase 1 では `context_index` に記載されたファイルの**中身は読み込まない**。パス文字列を文脈参照として Prompt IR に載せるのみである。

### 4.2 Adapter と出力形式

| `--target` | 別名 | 出力 `format` | 主な payload 構造 |
|------------|------|---------------|-------------------|
| `chatgpt` | `openai` | `openai_chat` | `{ "messages": [ { "role", "content" }, ... ] }` |
| `claude` | `anthropic` | `anthropic_messages` | `{ "system": "...", "messages": [ ... ] }` |

**ChatGPT（OpenAI）**: `system` ロールに人格・価値観など。`user` ロールに文脈参照・制約。

**Claude（Anthropic）**: `system` に人格・価値観・制約。`user` に文脈参照・タスク指示。

同じ Profile でも target ごとにメッセージ分割が異なる（「同一人格 ≠ 同一プロンプト」）。

## 5. コマンドリファレンス

### 5.1 `omomuki init`

ローカル Profile Store を初期化する。

```bash
omomuki init
omomuki init --force
```

| オプション | 説明 |
|-----------|------|
| `--force` | 既存 Store があっても上書きして再作成する |

**動作**

- `~/.omomuki/profiles/default/` と `context/` を作成する
- テンプレート `omomuki.profile.yaml` と空の Markdown を配置する
- 既に Profile があり `--force` なしの場合はメッセージを出して終了コード `0` で終了する

**次のステップ**: `omomuki.profile.yaml` を編集し、`omomuki profile inspect` で確認する。

---

### 5.2 `omomuki profile inspect`

読み込んだ Profile の要約を標準出力に表示する。

```bash
omomuki profile inspect
omomuki profile inspect --profile /path/to/omomuki.profile.yaml
omomuki profile inspect --profile examples/profiles/minimal.yaml
```

| オプション | 既定値 | 説明 |
|-----------|--------|------|
| `--profile` | `~/.omomuki/.../omomuki.profile.yaml` | 読み込む Profile YAML のパス |

**表示例**（フィールドがある場合のみ行を出力）

```text
Path: examples/profiles/minimal.yaml
Kind: OmomukiProfile (v0.1.0)
Identity: Example User (example)
Roles: developer
Tone: precise, logical
Values: human dignity, explicit uncertainty
Concepts: RDE, Omomuki
Context entrypoint: context/MyContext.md
```

**エラー**: ファイルが存在しない場合は `Profile not found` と表示し、非ゼロ終了。先に `omomuki init` するか `--profile` を確認する。

---

### 5.3 `omomuki compile`

Prompt IR を経由して LLM 向け JSON を標準出力する。

```bash
omomuki compile --target chatgpt
omomuki compile --target claude --profile examples/profiles/minimal.yaml
omomuki compile --target chatgpt --instruction "今週の優先タスクを整理して"
```

| オプション | 必須 | 既定値 | 説明 |
|-----------|------|--------|------|
| `--target` | はい | — | `chatgpt` / `claude`（`openai` / `anthropic` も可） |
| `--profile` | いいえ | 既定 Store | Profile YAML のパス |
| `--instruction` | いいえ | — | タスク指示（Prompt IR の `instruction` に入る） |

**出力**: UTF-8 JSON（`indent=2`）。パイプやファイルリダイレクトに適する。

```bash
omomuki compile --target chatgpt --profile examples/profiles/minimal.yaml \
  > /tmp/omomuki-chatgpt.json
```

**ChatGPT 出力例**（抜粋）:

```json
{
  "messages": [
    { "role": "system", "content": "You are assisting Example User.\n..." },
    { "role": "user", "content": "Context entrypoint: context/MyContext.md\n..." }
  ]
}
```

**Claude 出力例**（抜粋）:

```json
{
  "system": "You are assisting Example User.\n...\nAvoid: ...",
  "messages": [
    { "role": "user", "content": "Context entrypoint: ...\n..." }
  ]
}
```

リポジトリ内の完全なサンプル: `examples/compiled/chatgpt.json`, `examples/compiled/claude.json`。

**エラー**

- 未対応の `--target`（例: `gemini`）→ `Unknown target`
- Profile 不在 → `Profile not found`

---

### 5.4 `omomuki export`

Prompt IR とコンパイル結果を Markdown で標準出力する。確認・ドキュメント化・レビュー用。

```bash
omomuki export --format markdown
omomuki export --format markdown --target claude --profile examples/profiles/minimal.yaml
omomuki export --format markdown --target chatgpt \
  --instruction "README の CLI 節を推敲して" \
  > compiled-review.md
```

| オプション | 必須 | 既定値 | 説明 |
|-----------|------|--------|------|
| `--format` | はい | — | Phase 1 では `markdown` のみ |
| `--target` | いいえ | `chatgpt` | コンパイル先 LLM |
| `--profile` | いいえ | 既定 Store | Profile YAML のパス |
| `--instruction` | いいえ | — | `compile` と同様 |

**出力構成**

1. 見出しと target / format のメタ情報
2. `## Prompt IR` — YAML ブロック
3. `## Compiled Payload` — JSON ブロック

`--format` に `markdown` 以外を指定すると `Unsupported format` エラー。

---

### 5.5 `omomuki serve`

Local Bridge（localhost API）を起動する。Phase 2。

```bash
omomuki serve
omomuki serve --port 38741 --host 127.0.0.1
```

| オプション | 既定値 | 説明 |
|-----------|--------|------|
| `--host` | `127.0.0.1` | バインドアドレス（localhost のみ） |
| `--port` | `38741` | 待ち受けポート |

初回起動時に `~/.omomuki/bridge.token` を生成し、Bearer トークンと pairing code を表示する。

**HTTP エンドポイント**（保護系は `Authorization: Bearer <token>` 必須）

| メソッド | パス | 認証 | 説明 |
|---------|------|------|------|
| GET | `/health` | 不要 | 死活確認（機微情報なし） |
| GET | `/profiles` | 必須 | 登録 Profile 一覧 |
| POST | `/capture` | 必須 | 文脈候補を Candidate として保存（merge しない） |
| POST | `/compile` | 必須 | JSON body でコンパイル |
| GET | `/context-packet` | 必須 | クエリ `target`, `profile`, `instruction` |

**curl 例**

```bash
TOKEN=$(cat ~/.omomuki/bridge.token)
curl -s http://127.0.0.1:38741/health
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:38741/profiles
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"target":"chatgpt","profile_id":"default"}' \
  http://127.0.0.1:38741/compile
```

CORS は既定で許可しない。詳細は [Bridge マニュアル](bridge-manual.md) および [Security Design](security.md)。

---

### 5.6 `omomuki mcp`（Phase 2.5）

MCP Server と同一ロジックを CLI から実行する。read-only。

```bash
omomuki mcp serve
omomuki mcp list-profiles
omomuki mcp inspect-profile --profile-id default
omomuki mcp compile --target chatgpt --profile-id default
omomuki mcp context-packet --target claude --instruction "タスク"
omomuki mcp list-candidates
```

Cursor 等から使う場合は `mcp serve` のみ起動し、クライアント側で子プロセスとして登録する（[MCP マニュアル](mcp-manual.md) 参照）。

## 6. 典型的なワークフロー

### 6.1 初回セットアップ

```bash
pip install -e .
omomuki init
# ~/.omomuki/profiles/default/omomuki.profile.yaml を編集
omomuki profile inspect
omomuki compile --target chatgpt
```

### 6.2 サンプル Profile で試す（Store を作らない）

```bash
omomuki profile inspect --profile examples/profiles/minimal.yaml
omomuki compile --target claude --profile examples/profiles/minimal.yaml
omomuki export --format markdown --target chatgpt \
  --profile examples/profiles/minimal.yaml
```

### 6.3 タスク付きでコンパイル

```bash
omomuki compile --target claude \
  --profile ~/.omomuki/profiles/default/omomuki.profile.yaml \
  --instruction "次のミーティング用に論点を3つに整理して"
```

### 6.4 Extension + Bridge（Phase 2 + 3）

```bash
# ターミナル 1
omomuki serve

# ターミナル 2 — Extension ビルド後、Options に ~/.omomuki/bridge.token を設定
cd extension && npm run build
```

→ [Chrome Extension マニュアル](extension-manual.md)

## 7. Profile YAML の編集

`omomuki.profile.yaml` は [Omomuki Profile と Prompt IR](profile-ir.md) の構造に従う。主要フィールドと CLI への影響は次のとおり。

| セクション | CLI への影響 |
|-----------|-------------|
| `identity` | `system` に名前・ロール |
| `voice` | `system` に言語・トーン |
| `values.core` | `system` に価値観 |
| `knowledge.concepts` | `system` に概念一覧 |
| `policy.response` | `constraints`（avoid / prefer） |
| `context_index` | `context`（ファイルパス参照） |

バージョン・`kind: OmomukiProfile` は必須。JSON Schema は `schemas/omomuki-profile.schema.json` を参照。

## 8. トラブルシューティング

| 症状 | 原因の例 | 対処 |
|------|---------|------|
| `Profile not found` | `init` 未実行、パス誤り | `omomuki init` または `--profile` を確認 |
| `Unknown target` | 未実装 Adapter | `chatgpt` / `claude` のみ Phase 1 対応 |
| `Unsupported format` | `export` の format 誤り | `--format markdown` のみ |
| ValidationError（pytest 等） | YAML がスキーマ不整合 | `schemas/omomuki-profile.schema.json` と照合 |
| 文脈ファイルの中身がプロンプトに出ない | Phase 1 仕様 | `context_index` はパス参照のみ。本文取り込みは将来 Phase |
| Bridge `401` | token 未設定・不一致 | `~/.omomuki/bridge.token` と Authorization ヘッダ |
| `omomuki mcp` で Profile なし | init 未実施 | `omomuki init` |

## 9. 関連ドキュメント

- [はじめに](getting-started.md) — 全体像・シナリオ別手順
- [Bridge マニュアル](bridge-manual.md) — HTTP API リファレンス
- [MCP マニュアル](mcp-manual.md)
- [Chrome Extension マニュアル](extension-manual.md)
- [MVP範囲](mvp-scope.md) / [実装ロードマップ](roadmap.md)
- [開発原則](development-principles.md) / [CI方針](ci.md)

## 10. バージョン

本マニュアルは Omomuki **0.3.0**（Phase 1〜2.5 CLI）時点。Extension は [Extension マニュアル](extension-manual.md) を参照。
