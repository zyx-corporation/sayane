# Sayane CLI マニュアル

`sayane` コマンドの利用者向けマニュアルである（Phase 1 CLI + Phase 2 Bridge + Phase 2.5 MCP サブコマンド）。

初めて使う場合は [はじめに](getting-started.md) を先に読むこと。Bridge 詳細は [Bridge マニュアル](bridge-manual.md)、MCP 詳細は [MCP マニュアル](mcp-manual.md)。受け入れテストは [CLI 受け入れテスト](cli-acceptance-test.md) を参照。管理ディレクトリの詳細は [Sayane 管理ディレクトリ（SAYANE_DIR）](sayane-dir-layout.md) を参照。

設計: [CLI / Local Bridge / Chrome Extension 設計](cli-chrome-extension.md) / データ: [Profile と Prompt IR](profile-ir.md)

## 1. 概要

Sayane CLI は、ローカルに保持した **Sayane Profile** から **Prompt IR**（中間表現）を生成し、**Adapter** 経由で各 LLM 向けのリクエスト形式へ変換する制御面である。

```text
sayane.profile.yaml  →  Prompt IR  →  Adapter  →  JSON / Markdown 出力
```

## 表示言語

CLI のメッセージ（`typer.echo` 出力・`sayane help` 一覧）は次で切り替える。

```bash
export SAYANE_LANG=ja          # 優先: --lang > SAYANE_LANG > LANG
export LANG=ja_JP.UTF-8         # SAYANE_LANG 未設定時のみ参照
sayane --lang ja candidate list
```

対応: `en`（既定）、`ja`。`sayane compile --help` など Typer 標準ヘルプの説明文は英語のまま。

階層的ヘルプ:

```bash
sayane help                      # 全体一覧（コマンド・グループ）
sayane help candidate evaluate   # 特定サブコマンドの詳細
sayane candidate --help          # グループ単位（Typer 標準）
```

利用可能な主なコマンドは次のとおりである。

| コマンド | 概要 |
|---------|------|
| `sayane --version` / `-V` | パッケージ版を表示して終了 |
| `sayane help [TOPIC...]` | 階層的ヘルプ（上記） |
| `sayane init` | ローカル Sayane 管理ディレクトリと Profile Store を初期化する |
| `sayane profile inspect` | Profile の要約を表示する |
| `sayane compile` | 指定 LLM 向けにプロンプトをコンパイルする（JSON 出力） |
| `sayane export` | Prompt IR とコンパイル結果を Markdown で出力する |
| `sayane serve` | Local Bridge API を起動する（Phase 2） |
| `sayane mcp serve` | MCP Server（stdio）起動（Phase 2.5） |
| `sayane mcp list-profiles` など | MCP Tools と同等の CLI 操作 |
| `sayane candidate …` | Candidate 評価・approve（Phase 4） |
| `sayane storage …` | Obsidian import/export・index・Git commit（Phase 5） |

Bridge HTTP API の詳細は [Bridge マニュアル](bridge-manual.md)。MCP Tools / Cursor 設定は [MCP マニュアル](mcp-manual.md)。Storage 詳細は [Storage マニュアル](storage-manual.md)。

未実装（ロードマップ参照）: CLI の `capture` など。文脈 capture は Bridge `POST /capture` または Extension から可能。`candidate evaluate` / `approve` は CLI から利用可（[評価マニュアル](evaluation-manual.md)）。

## 環境変数

| 変数 | 用途 |
|------|------|
| `SAYANE_DIR` | Sayane 管理ルート。未指定時は `~/.sayane`。Profile、prompt adaptation、E2E状態をこの配下に置く |
| `SAYANE_LANG` | CLI メッセージの表示言語（`en` / `ja`）。`--lang` でも指定可 |
| `LANG` | `SAYANE_LANG` 未設定時のフォールバック（例: `ja_JP.UTF-8` → `ja`） |
| `SAYANE_OBSIDIAN_VAULT` | Obsidian vault の既定パス。ディレクトリが存在する場合 `storage import` / `export` で `<vault>` 引数を省略可 |
| `SAYANE_JUDGE_BASE_URL` | Level 2/3 LLM judge の API ベース URL（任意） |
| `SAYANE_JUDGE_API_KEY` | Level 2/3 judge の API キー（任意） |
| `SAYANE_JUDGE_MODEL` | Level 2/3 judge のモデル名（任意） |

Extension の表示言語（`displayLanguage`）は CLI とは独立し、Chrome Options で設定する（[Extension マニュアル](extension-manual.md)）。

## 2. インストール

リポジトリルートで editable インストールする。

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

インストール後、次でヘルプを確認できる。

```bash
sayane --help
sayane profile --help
sayane compile --help
```

## 3. Sayane 管理ディレクトリ / Profile Store

### 3.1 既定の配置

`sayane init` は、既定では `~/.sayane` を Sayane 管理ディレクトリとして初期化する。

`SAYANE_DIR` を指定すると、そのディレクトリを管理ルートとして使う。

```bash
export SAYANE_DIR="$HOME/.sayane"
sayane init
```

標準レイアウトは次のとおりである。

```text
$SAYANE_DIR/
  profiles/
    default/
      sayane.profile.yaml    # メイン Profile
      context/
        MyContext.md          # 文脈ファイル（プレースホルダ）
        AI_HANDOFF.md         # 引き継ぎ用（プレースホルダ）

  prompts/
    targets/                  # target別 prompt adaptation
    models/                   # model別 prompt optimization
    providers/                # provider/UI別 constraints

  e2e/
    user-data/                # Chromium persistent profile等。prompt正本ではない
    prompts/                  # E2E専用 prompt fixture
```

`--profile` を省略したコマンドは、既定で次を読み込む。

```text
$SAYANE_DIR/profiles/default/sayane.profile.yaml
```

`SAYANE_DIR` 未指定時は次と同じである。

```text
~/.sayane/profiles/default/sayane.profile.yaml
```

### 3.2 prompt / E2E 領域の分離

モデルごとに最適化されたプロンプトは `e2e/user-data/` には置かない。

`e2e/user-data/` は、cookies、localStorage、IndexedDB、ログイン状態などを含み得る不透明なブラウザ実行状態である。

prompt adaptation は、監査可能な意味資産として `prompts/` 配下に置く。

| 領域 | 用途 |
|------|------|
| `prompts/targets/` | ChatGPT / Claude / Gemini / DeepSeek など target別の prompt adaptation |
| `prompts/models/` | Qwen / DeepSeek-R1-Distill / ELYZA など model別の prompt optimization |
| `prompts/providers/` | Open WebUI / LibreChat / local custom UI など provider/UI別の制約 |
| `e2e/user-data/` | 実DOM E2E用のブラウザ profile 状態 |
| `e2e/prompts/` | E2E専用の marker 付きテストプロンプト |

詳細は [Sayane 管理ディレクトリ（SAYANE_DIR）](sayane-dir-layout.md) を参照。

### 3.3 リポジトリ内のサンプル

開発・検証用の最小 Profile は次にある。

```text
examples/profiles/minimal.yaml
```

README や本マニュアルの例では、必要に応じて `--profile examples/profiles/minimal.yaml` を付与する。

## 4. 処理フロー

### 4.1 compile / export の内部処理

1. YAML から **Sayane Profile** を読み込み、Pydantic で検証する
2. Profile フィールドから **Prompt IR** を組み立てる（Builder）
3. `--target` に応じた **Adapter** が Prompt IR を LLM 固有形式へ変換する

```text
Profile
  ├─ identity / voice / values / knowledge  →  Prompt IR.system
  ├─ context_index                          →  Prompt IR.context（パス参照）
  ├─ policy.response                        →  Prompt IR.constraints
  └─ --instruction（任意）                  →  Prompt IR.instruction
```

Phase 5 以降、`context_index` に記載されたファイルがプロファイルディレクトリ内に存在すれば **本文を読み込み** Prompt IR の `context` に含める（最大約 32KB/ファイル）。それ以前はパス参照のみだった。

### 4.2 Adapter と出力形式

| `--target` | 別名 | 出力 `format` | 主な payload 構造 |
|------------|------|---------------|-------------------|
| `chatgpt` | `openai` | `openai_chat` | `{ "messages": [ { "role", "content" }, ... ] }` |
| `claude` | `anthropic` | `anthropic_messages` | `{ "system": "...", "messages": [ ... ] }` |

**ChatGPT（OpenAI）**: `system` ロールに人格・価値観など。`user` ロールに文脈参照・制約。

**Claude（Anthropic）**: `system` に人格・価値観・制約。`user` に文脈参照・タスク指示。

同じ Profile でも target ごとにメッセージ分割が異なる（「同一人格 ≠ 同一プロンプト」）。

## 5. コマンドリファレンス

### 5.1 `sayane init`

Sayane 管理ディレクトリとローカル Profile Store を初期化する。

```bash
sayane init
sayane init --force
```

| オプション | 説明 |
|-----------|------|
| `--force` | 既存 Profile があっても既定テンプレートで上書きして再作成する |

**動作**

- `$SAYANE_DIR` 未指定時は `~/.sayane` を使う
- `$SAYANE_DIR/profiles/default/` と `context/` を作成する
- `$SAYANE_DIR/prompts/targets/`, `prompts/models/`, `prompts/providers/` を作成する
- `$SAYANE_DIR/e2e/user-data/`, `e2e/prompts/` を作成する
- テンプレート `sayane.profile.yaml` と空の Markdown を配置する
- 既に Profile があり `--force` なしの場合は、Profileを上書きせず、補助ディレクトリだけを非破壊で補完して終了コード `0` で終了する

**次のステップ**: `sayane.profile.yaml` を編集し、`sayane profile inspect` で確認する。

---

### 5.2 `sayane profile inspect`

読み込んだ Profile の要約を標準出力に表示する。

```bash
sayane profile inspect
sayane profile inspect --profile /path/to/sayane.profile.yaml
sayane profile inspect --profile examples/profiles/minimal.yaml
```

| オプション | 既定値 | 説明 |
|-----------|--------|------|
| `--profile` | `$SAYANE_DIR/profiles/default/sayane.profile.yaml` | 読み込む Profile YAML のパス |

**表示例**（フィールドがある場合のみ行を出力）

```text
Path: examples/profiles/minimal.yaml
Kind: SayaneProfile (v0.1.0)
Identity: Example User (example)
Roles: developer
Tone: precise, logical
Values: human dignity, explicit uncertainty
Concepts: RDE, Sayane
Context entrypoint: context/MyContext.md
```

**エラー**: ファイルが存在しない場合は `Profile not found` と表示し、非ゼロ終了。先に `sayane init` するか `--profile` を確認する。

---

### 5.3 `sayane compile`

Prompt IR を経由して LLM 向け JSON を標準出力する。

```bash
sayane compile --target chatgpt
sayane compile --target claude --profile examples/profiles/minimal.yaml
sayane compile --target chatgpt --instruction "今週の優先タスクを整理して"
```

| オプション | 必須 | 既定値 | 説明 |
|-----------|------|--------|------|
| `--target` | はい | — | `chatgpt` / `claude`（`openai` / `anthropic` も可） |
| `--profile` | いいえ | 既定 Store | Profile YAML のパス |
| `--instruction` | いいえ | — | タスク指示（Prompt IR の `instruction` に入る） |

**出力**: UTF-8 JSON（`indent=2`）。パイプやファイルリダイレクトに適する。

```bash
sayane compile --target chatgpt --profile examples/profiles/minimal.yaml \
  > /tmp/sayane-chatgpt.json
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

### 5.4 `sayane export`

Prompt IR とコンパイル結果を Markdown で標準出力する。確認・ドキュメント化・レビュー用。

```bash
sayane export --format markdown
sayane export --format markdown --target claude --profile examples/profiles/minimal.yaml
sayane export --format markdown --target chatgpt \
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

### 5.5 `sayane serve`

Local Bridge（localhost API）を起動する。Phase 2。

```bash
sayane serve
sayane serve --port 38741 --host 127.0.0.1
```

| オプション | 既定値 | 説明 |
|-----------|--------|------|
| `--host` | `127.0.0.1` | バインドアドレス（localhost のみ） |
| `--port` | `38741` | 待ち受けポート |

初回起動時に `$SAYANE_DIR/bridge.token` を生成し、Bearer トークンと pairing code を表示する。

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
TOKEN=$(cat ${SAYANE_DIR:-$HOME/.sayane}/bridge.token)
curl -s http://127.0.0.1:38741/health
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:38741/profiles
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"target":"chatgpt","profile_id":"default"}' \
  http://127.0.0.1:38741/compile
```

CORS は既定で許可しない。詳細は [Bridge マニュアル](bridge-manual.md) および [Security Design](security.md)。

---

### 5.6 `sayane mcp`（Phase 2.5）

MCP Server と同一ロジックを CLI から実行する。read-only。

```bash
sayane mcp serve
sayane mcp list-profiles
sayane mcp inspect-profile --profile-id default
sayane mcp compile --target chatgpt --profile-id default
sayane mcp context-packet --target claude --instruction "タスク"
sayane mcp list-candidates
```

Cursor 等から使う場合は `mcp serve` のみ起動し、クライアント側で子プロセスとして登録する（[MCP マニュアル](mcp-manual.md) 参照）。

---

### 5.7 `sayane candidate`（Phase 4）

Candidate の一覧・評価・差分・承認。詳細は [RDE / Candidate 評価マニュアル](evaluation-manual.md)。

```bash
sayane candidate list
sayane candidate evaluate <id> --level 1
sayane candidate evaluate <id> --level 2   # SAYANE_JUDGE_* 要
sayane candidate diff <id>
sayane candidate approve <id>
sayane candidate reject <id>
```

---

### 5.8 `sayane storage`（Phase 5）

Obsidian vault 連携と Git commit。詳細は [Storage マニュアル](storage-manual.md)。

```bash
export SAYANE_OBSIDIAN_VAULT="$HOME/Documents/MyVault"   # 任意
sayane storage import          # または sayane storage import /path/to/vault
sayane storage export
sayane storage index
sayane storage commit -m "sayane: sync context" --init
```

| サブコマンド | 概要 |
|-------------|------|
| `import [vault]` | vault の `.md` を `context/` へ取り込む |
| `export [vault]` | `context/` を vault 内 `sayane/` へ書き出す |
| `index` | `context_index.entries` を再生成 |
| `commit -m "..."` | Profile + context を Git コミット |

`SAYANE_OBSIDIAN_VAULT` が存在するディレクトリを指す場合、`import` / `export` の vault 引数を省略できる。

`import` / `index` 実行後、Profile Store に変更があれば **Git へ自動コミット**される（`filesystem` backend かつ SQLite 実装までの既定。`init` 時も同様）。

---

### 5.9 Commercial Edition 拡張（sayane-pro 側マニュアル）

`license` / `storage backend` / `storage migrate` / `confidentiality` 等の商用版サブコマンドは **sayane-pro** リポジトリの CLI マニュアルで管理する。

Community Edition（本書 §5.8 まで）では `filesystem` backend のみを対象とする。Phase 6 の位置づけは [roadmap.md §9](roadmap.md)。

## 6. 典型的なワークフロー

### 6.1 初回セットアップ

```bash
pip install -e .
sayane init
# ${SAYANE_DIR:-$HOME/.sayane}/profiles/default/sayane.profile.yaml を編集
sayane profile inspect
sayane compile --target chatgpt
```

### 6.2 サンプル Profile で試す（Store を作らない）

```bash
sayane profile inspect --profile examples/profiles/minimal.yaml
sayane compile --target claude --profile examples/profiles/minimal.yaml
sayane export --format markdown --target chatgpt \
  --profile examples/profiles/minimal.yaml
```

### 6.3 タスク付きでコンパイル

```bash
sayane compile --target claude \
  --profile ${SAYANE_DIR:-$HOME/.sayane}/profiles/default/sayane.profile.yaml \
  --instruction "次のミーティング用に論点を3つに整理して"
```

### 6.4 Extension + Bridge（Phase 2 + 3）

```bash
# ターミナル 1
sayane serve

# ターミナル 2 — Extension ビルド後、Options に ${SAYANE_DIR:-$HOME/.sayane}/bridge.token を設定
cd extension && npm run build
```

→ [Chrome Extension マニュアル](extension-manual.md)

## 7. Profile YAML の編集

`sayane.profile.yaml` は [Sayane Profile と Prompt IR](profile-ir.md) の構造に従う。主要フィールドと CLI への影響は次のとおり。

| セクション | CLI への影響 |
|-----------|-------------|
| `identity` | `system` に名前・ロール |
| `voice` | `system` に言語・トーン |
| `values.core` | `system` に価値観 |
| `knowledge.concepts` | `system` に概念一覧 |
| `policy.response` | `constraints`（avoid / prefer） |
| `context_index` | `context`（ファイルパス参照） |

バージョン・`kind: SayaneProfile` は必須。JSON Schema は `schemas/sayane-profile.schema.json` を参照。

## 8. トラブルシューティング

| 症状 | 原因の例 | 対処 |
|------|---------|------|
| `Profile not found` | `init` 未実行、パス誤り | `sayane init` または `--profile` を確認 |
| 既定パスが想定と違う | `SAYANE_DIR` が設定されている | `echo $SAYANE_DIR` を確認 |
| `Unknown target` | 未実装 Adapter | `chatgpt` / `claude` のみ Phase 1 対応 |
| `Unsupported format` | `export` の format 誤り | `--format markdown` のみ |
| ValidationError（pytest 等） | YAML がスキーマ不整合 | `schemas/sayane-profile.schema.json` と照合 |
| 文脈ファイルの中身がプロンプトに出ない | パス外・サイズ超過 | ファイルがプロファイルディレクトリ内か、`context_index` に載っているか確認（最大約 32KB/ファイル） |
| Bridge `401` | token 未設定・不一致 | `${SAYANE_DIR:-$HOME/.sayane}/bridge.token` と Authorization ヘッダ |
| `sayane mcp` で Profile なし | init 未実施 | `sayane init` |

## 9. 関連ドキュメント

- [はじめに](getting-started.md) — 全体像・シナリオ別手順
- [Sayane 管理ディレクトリ（SAYANE_DIR）](sayane-dir-layout.md)
- [Bridge マニュアル](bridge-manual.md) — HTTP API リファレンス
- [MCP マニュアル](mcp-manual.md)
- [Chrome Extension マニュアル](extension-manual.md)
- [MVP範囲](mvp-scope.md) / [実装ロードマップ](roadmap.md)
- [開発原則](development-principles.md) / [CI方針](ci.md)

## 10. バージョン

Candidate 評価: [evaluation-manual.md](evaluation-manual.md)。

本マニュアルは Sayane **0.5.9** 時点。Extension は [Extension マニュアル](extension-manual.md) を参照。
