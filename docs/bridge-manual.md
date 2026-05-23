# Local Bridge マニュアル

Phase 2 の **Local Bridge** は、`127.0.0.1` 上の HTTP API である。Chrome Extension や curl から Omomuki Core を呼び出す。

CLI からの起動: `omomuki serve`（[CLI マニュアル](cli-manual.md) 5.5 節と同等）。設計: [Security Design](security.md) 第 4 節。

## 1. 概要

| 項目 | 値 |
|------|-----|
| 既定 URL | `http://127.0.0.1:38741` |
| バインド | `127.0.0.1` のみ（`omomuki serve --host` で変更可） |
| 認証 | `Authorization: Bearer <token>` |
| トークン保存 | `~/.omomuki/bridge.token` |
| CORS | 既定 deny（ブラウザ拡張は host_permissions で localhost へアクセス） |

**capture は merge ではない。** `POST /capture` は `~/.omomuki/candidates/` に Candidate として保存する。

## 2. 起動

```bash
omomuki init    # 未実施の場合
omomuki serve
omomuki serve --port 38741 --host 127.0.0.1
```

初回起動時:

- `~/.omomuki/bridge.token` を生成
- コンソールに pairing code（表示用ヒント）と token ファイルパスを出力

## 3. エンドポイント

### 3.1 認証不要

#### `GET /health`

```bash
curl -s http://127.0.0.1:38741/health
# {"status":"ok"}
```

機微情報は含めない。

### 3.2 認証必須（Bearer token）

ヘッダ例:

```bash
TOKEN=$(cat ~/.omomuki/bridge.token)
AUTH="Authorization: Bearer $TOKEN"
```

#### `GET /profiles`

Profile 一覧。

```bash
curl -s -H "$AUTH" http://127.0.0.1:38741/profiles
```

レスポンス例:

```json
[
  {"id": "default", "path": "/Users/.../omomuki.profile.yaml", "name": "Example User"}
]
```

#### `POST /capture`

文脈候補を Candidate として保存。

```bash
curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"content":"Selected text","source":"selection","source_url":"https://example.com"}' \
  http://127.0.0.1:38741/capture
```

#### `POST /compile`

JSON body でコンパイル。

```bash
curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"target":"chatgpt","profile_id":"default","instruction":"Summarize priorities"}' \
  http://127.0.0.1:38741/compile
```

#### `GET /context-packet`

クエリパラメータでコンパイル（Extension が利用）。

```bash
curl -s -H "$AUTH" \
  "http://127.0.0.1:38741/context-packet?target=claude&profile=default"
```

| パラメータ | 説明 |
|-----------|------|
| `target` | 必須。`chatgpt` / `claude` |
| `profile` | Profile id（既定 `default`） |
| `instruction` | 任意。タスク指示 |

#### Candidate 評価・承認（Phase 4+ / Bridge API）

capture 後、CLI と同等の評価フローを HTTP から実行できる。いずれも Bearer 必須。

| メソッド | パス | 説明 |
|---------|------|------|
| `GET` | `/candidates` | Candidate 一覧（要約） |
| `GET` | `/candidates/{id}` | Candidate 全文 |
| `POST` | `/candidates/{id}/evaluate` | RDE/UIB 評価（body: `{"level": 1}`） |
| `GET` | `/candidates/{id}/diff` | Profile との rule-based diff |
| `POST` | `/candidates/{id}/approve` | 承認して merge（body: `{"force_critical": false}`） |
| `POST` | `/candidates/{id}/reject` | 却下（body: `{"reason": "..."}` 任意） |

```bash
# capture 後
CID=<candidate-id>
curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"level": 2}' "http://127.0.0.1:38741/candidates/$CID/evaluate"
curl -s -H "$AUTH" "http://127.0.0.1:38741/candidates/$CID/diff"
curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"force_critical": false}' "http://127.0.0.1:38741/candidates/$CID/approve"
```

詳細: [RDE / Candidate 評価マニュアル](evaluation-manual.md)

### 3.3 意図的に未提供

- Profile への任意フィールド直接 PATCH
- RDE 評価なしの bulk merge

## 4. Chrome Extension 連携

1. `omomuki serve` を常時起動
2. Extension Options に Bridge URL と Bearer token を設定
3. Popup から capture / insert

→ [Chrome Extension マニュアル](extension-manual.md)

## 5. MCP Server との違い

| | Bridge | MCP Server |
|--|--------|------------|
| プロトコル | HTTP | MCP (stdio) |
| 起動 | `omomuki serve` | `omomuki mcp serve` |
| 主なクライアント | Extension、curl | Cursor、Claude Desktop |
| 認証 | Bearer token 必須（`/health` 除く） | ローカル子プロセス |

同一 Core（Profile → Prompt IR → Adapter）を共有する。

## 6. トラブルシューティング

| 症状 | 対処 |
|------|------|
| `401 Unauthorized` | `bridge.token` を確認。`Authorization: Bearer` 形式 |
| `404 Profile not found` | `omomuki init`、または `profiles/default/omomuki.profile.yaml` の存在 |
| Extension が Bridge unreachable | `omomuki serve` 起動中か、URL/port、token |
| curl から接続できない | `127.0.0.1` のみバインド。ファイアウォールは通常不要 |

## 7. バージョン

Omomuki **0.5.8** 時点（Candidate evaluate/approve API 含む）。
