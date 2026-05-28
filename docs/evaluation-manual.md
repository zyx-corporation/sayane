# RDE / Candidate 評価マニュアル

Phase 4 の Candidate Update 評価・承認フロー。Level 0–1 はヒューリスティック、Level 2–3 は任意の LLM-as-a-Judge。

設計: [evaluation-lineage.md](evaluation-lineage.md)

**T-RDE 実行プロンプト（v1.1a）**: [t-rde-execution-prompt.md](t-rde-execution-prompt.md) — PR・設計・コードの意味監査に使用。`sayane candidate evaluate --level 2/3` は同プロンプトのサブセットを `llm_judge` が適用する。

## 1. フロー

```text
capture → Candidate Update → evaluate (RDE+UIB) → approve / reject → lineage
```

- **capture**: Bridge / Extension → `~/.sayane/candidates/*.json`
- **merge**: `approve` のみ
- **knowledge.concepts**: `--force-critical` なしで merge 可
- **critical section**（values, voice, policy, roles）: `--force-critical` が必要
- **identity.name / preferred_name**: 自動 merge 不可（手動編集）

## 2. 接続面

| 接続面 | 用途 |
|--------|------|
| **CLI** | `sayane candidate …`（下記） |
| **Local Bridge** | `GET/POST /candidates/...`（[Bridge マニュアル](bridge-manual.md)） |
| **MCP** | `evaluate_candidate` 等（[MCP マニュアル](mcp-manual.md)） |

## 3. CLI

```bash
sayane candidate list
sayane candidate show <id>
sayane candidate evaluate <id>              # Level 1（既定）
sayane candidate evaluate <id> --level 2    # + ローカル LLM judge
sayane candidate evaluate <id> --level 3    # + 外部 API（要 API key）
sayane candidate diff <id>
sayane profile diff --candidate <id>
sayane candidate approve <id>
sayane candidate approve <id> --force-critical
sayane candidate reject <id> --reason "..."
sayane candidate lineage --profile-id default
```

## 4. 評価レベル

| Level | 内容 |
|-------|------|
| 0 | スキーマ検証（load 時） |
| 1 | ヒューリスティック RDE + UIB（既定） |
| 2 | Level 1 + ローカル LLM judge（Ollama 等） |
| 3 | Level 1 + 外部 OpenAI 互換 API |

ヒューリスティックと LLM の RDE 分類が異なる場合、**より保守的（厳しい）方**を採用する。

### 4.1 設定の優先順位

LLM judge は **任意機能**である。未設定・接続失敗時は Level 1 の結果のみが使われ、評価自体は継続する。

| 項目 | 説明 |
|------|------|
| 設定ファイル | `~/.sayane/judge.yaml` |
| 環境変数 | 同名キーは **環境変数が優先**（ファイルより上書き） |
| 例ファイル | [examples/judge.yaml.example](../examples/judge.yaml.example) |

| キー / 環境変数 | 説明 |
|----------------|------|
| `base_url` / `SAYANE_JUDGE_BASE_URL` | OpenAI 互換 API のベース URL（末尾 `/v1`） |
| `api_key` / `SAYANE_JUDGE_API_KEY` | Bearer トークン（Level 3 では必須） |
| `model` / `SAYANE_JUDGE_MODEL` | モデル名（未指定時 `llama3.2`） |
| `timeout_sec` | リクエストタイムアウト秒（ファイルのみ、既定 60） |

**Level 2**（ローカル）: `base_url` 未設定時は `http://127.0.0.1:11434/v1`（Ollama 既定）を使う。`api_key` は不要。

**Level 3**（外部）: `base_url` と `api_key` の **両方が必須**。どちらか欠けると LLM judge はスキップされ、CLI 出力の `notes` に理由が残る。

### 4.2 設定ファイル（`~/.sayane/judge.yaml`）

#### ローカル（Level 2）向け

```yaml
base_url: "http://127.0.0.1:11434/v1"
model: "llama3.2"
timeout_sec: 60
```

#### 外部 API（Level 3）向け

```yaml
base_url: "https://api.openai.com/v1"
model: "gpt-4o-mini"
# api_key はファイルより環境変数を推奨（下記 3.3 参照）
```

`api_key` を YAML に書くこともできるが、**リポジトリや共有ディレクトリへ置かない**こと。可能なら `SAYANE_JUDGE_API_KEY` のみ環境変数で渡す。

### 4.3 外部 API key（環境変数）

シェルセッションまたは `~/.zshrc` 等で設定する例:

```bash
export SAYANE_JUDGE_BASE_URL="https://api.openai.com/v1"
export SAYANE_JUDGE_API_KEY="sk-..."          # 実際のキーに置き換え
export SAYANE_JUDGE_MODEL="gpt-4o-mini"
```

OpenAI 以外の OpenAI 互換エンドポイント（Azure OpenAI、LiteLLM プロキシ等）も、`base_url` をその `/v1` 相当に合わせれば利用できる。

**セキュリティ上の注意**

- API key を git にコミットしない（`.env` も原則コミットしない）
- `judge.yaml` に key を書いた場合、ファイル権限を `600` に制限する
- judge は Candidate 本文と Profile 要約を外部 API に送る。機微情報を含む capture では Level 3 を使わない

### 4.4 手順サンプル：ローカル LLM judge（Ollama + Level 2）

前提: Sayane インストール済み、[Ollama](https://ollama.com/) インストール済み。

**1. Ollama でモデルを用意**

```bash
ollama pull llama3.2
# Ollama が未起動なら別ターミナルで: ollama serve
```

**2. judge 設定（任意）**

Level 2 は `judge.yaml` がなくても Ollama 既定 URL を使う。モデル名を固定したい場合:

```bash
mkdir -p ~/.sayane
cp examples/judge.yaml.example ~/.sayane/judge.yaml
# model を ollama list で確認した名前に合わせる
```

**3. Profile Store と Candidate を用意**

```bash
sayane init   # 未実施の場合
```

ターミナル A — Bridge 起動:

```bash
sayane serve
```

ターミナル B — capture（Candidate 作成）:

```bash
TOKEN=$(cat ~/.sayane/bridge.token)
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Portable context is a key concept for cross-LLM collaboration.","source":"manual","source_url":"https://example.com"}' \
  http://127.0.0.1:38741/capture
# レスポンスの "id" を控える（例: candidate-20260523-abc123）
```

**4. Level 2 評価**

```bash
sayane candidate list
sayane candidate evaluate <candidate-id> --level 2
```

成功時、`evaluation.llm_review` にモデル名・LLM 側 RDE 分類・notes が入る。

```bash
sayane candidate show <candidate-id>
```

**5. 承認（任意）**

RDE が `Critical Distortion` でなければ:

```bash
sayane candidate diff <candidate-id>
sayane candidate approve <candidate-id>
sayane candidate lineage --profile-id default
```

**接続確認（Ollama）**

```bash
curl -s http://127.0.0.1:11434/v1/models
```

モデル一覧が返れば Level 2 の前提は満たしている。

### 4.5 手順サンプル：外部 API judge（Level 3）

**1. API key を環境変数で設定**

```bash
export SAYANE_JUDGE_BASE_URL="https://api.openai.com/v1"
export SAYANE_JUDGE_API_KEY="sk-..."
export SAYANE_JUDGE_MODEL="gpt-4o-mini"
```

**2. Candidate を用意**（4.4 の Bridge `POST /capture` と同様）

**3. Level 3 評価**

```bash
sayane candidate evaluate <candidate-id> --level 3
```

**4. 結果確認**

```bash
sayane candidate show <candidate-id>
```

`evaluation.level` が `3` で、`evaluation.llm_review.level` も `3` であることを確認する。

### 4.6 トラブルシュート

| 症状 | 確認事項 |
|------|----------|
| `LLM judge skipped` と出る | Level 3 では `base_url` + `api_key` が両方設定されているか |
| `LLM judge failed: ...` | Ollama / API が起動しているか、モデル名が存在するか |
| `llm_review: null`（UIB validation） | LLM が UIB 6 軸の一部だけ返した場合。最新版は欠損軸（DT/VP/FG 等）を 0.5 で補完 |
| `401` / `403` | `SAYANE_JUDGE_API_KEY` が正しいか、URL が `/v1` 付きか |
| 評価は通るが `llm_review` が null | Level 1 のみ実行されている（`--level 2` 以上を指定したか） |
| タイムアウト | `judge.yaml` の `timeout_sec` を増やす、またはモデルを軽量化 |

LLM judge が失敗しても **Level 1 のヒューリスティック評価は保存される**。外部 API 不要の確認だけなら `--level 1`（既定）で足りる。

## 5. RDE 分類（ヒューリスティック）

Level 1 のマーカー照合は **単語・フレーズ・ドットパス・YAML キー境界**付き（`heuristic_match`）で、部分文字列誤検知（例: `Melotone:` → `tone:`、`secretary` → `secret`）を避ける。セクション推定も同様。

| 分類 | 目安 |
|------|------|
| Inferred Extension | 知識概念への非破壊的追加（既定） |
| Unresolved Gap | 短文・提案なし |
| Suspicious Drift | 断定的・命令的表現 |
| Critical Distortion | secret / critical section 言及 |

`Critical Distortion` は通常 **approve 不可**。`--force-critical` でも identity.name は merge 不可。

## 6. UIB スコア

0.0–1.0 の 6 軸（UD, MI, CH, DT, VP, FG）。Level 2+ では LLM が UIB を返した場合に上書きされる。

## 7. Merge 対象セクション

| section | approve | --force-critical |
|---------|---------|------------------|
| knowledge.concepts | 可 | 可 |
| values.core | 不可 | 可 |
| voice.tone | 不可 | 可 |
| policy.response.avoid / prefer | 不可 | 可 |
| identity.roles | 不可 | 可 |
| identity.name | 不可 | 不可 |

## 8. Lineage

`~/.sayane/lineage/<profile_id>.jsonl` に approve / reject イベントを追記。

## 9. バージョン

Sayane **0.5.8**（Bridge/MCP candidate API 含む）
