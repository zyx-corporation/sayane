# Local Bridge マニュアル

Phase 2 の **Local Bridge** は、`127.0.0.1` 上の HTTP API である。Chrome Extension や curl から Sayane Core を呼び出す。

CLI からの起動: `sayane serve`（[CLI マニュアル](cli-manual.md) 5.5 節と同等）。設計: [Security Design](security.md) 第 4 節。

## 1. 概要

| 項目 | 値 |
|------|-----|
| 既定 URL | `http://127.0.0.1:38741` |
| バインド | `127.0.0.1` のみ（`sayane serve --host` で変更可） |
| 認証 | `Authorization: Bearer <token>` |
| トークン保存 | `~/.sayane/bridge.token` |
| Resident UI session artifact | `~/.sayane/bridge.ui-session.json` |
| CORS | 既定 deny（ブラウザ拡張は host_permissions で localhost へアクセス） |

**capture は merge ではない。** `POST /capture` は `~/.sayane/candidates/` に Candidate として保存する。

## 2. 起動

```bash
sayane init    # 未実施の場合
sayane serve
sayane serve --port 38741 --host 127.0.0.1
```

初回起動時:

- `~/.sayane/bridge.token` を生成
- コンソールに pairing code（表示用ヒント）と token ファイルパスを出力
- resident app debug shell は `/app/ui` bootstrap 後に dedicated local UI session へ切り替わる

`/app/ui-state/*` と `/app/ui-action/*` は current macOS line では maintainer/debug 用の
cookie-backed compatibility seam であり、通常の operator-facing app integration は
bearer-backed `/app/*` を優先する。

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
TOKEN=$(cat ~/.sayane/bridge.token)
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
  {"id": "default", "path": "/Users/.../sayane.profile.yaml", "name": "Example User"}
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

#### `POST /capture`

| フィールド | 説明 |
|-----------|------|
| `content` | 必須。キャプチャ本文 |
| `source` | 任意。`selection` / `page` 等 |
| `source_url` | 任意 |
| `section` | 任意。`knowledge.concepts` 等（指定時はヒューリスティックより優先） |

構造化ペルソナ全文を capture した場合、レスポンス `warnings` に context 移行の案内が入る（`section` 指定時は出さない）。

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

#### `GET /app/daemon-overview`

Future resident UI 向けの app-facing aggregate preview。

```bash
curl -s -H "$AUTH" \
  "http://127.0.0.1:38741/app/daemon-overview"
```

レスポンスは以下をまとめて返す:

- daemon lifecycle status
- liveness diagnostic preview
- readiness diagnostic preview
- runtime init preview
- cleanup / repair preview
- service target status preview
- macOS LaunchAgent preview（macOS のみ）
- macOS LaunchAgent status observation（macOS のみ）
- suggested next actions

この payload は derived preview であり、process identity / daemon readiness / API readiness の
証明ではない。

#### `GET /app/overview`

Future resident UI 向けの aggregate app overview。

```bash
curl -s -H "$AUTH" \
  "http://127.0.0.1:38741/app/overview"
```

レスポンスは以下を束ねる:

- resident app runtime diagnostics
- local vault backend / keychain summary
- local vault unlock session summary
- UI-friendly summary counts
- review queue preview
- MCP preview
- daemon overview preview
- operator packaging / service target / supervision / recovery boundary previews

Current post-app operator boundary review is also available through aligned CLI summaries:

- `sayane app daemon-packaging-status`
- `sayane app daemon-service-targets-status`
- `sayane app daemon-service-control-boundary`
- `sayane app daemon-supervision-status`
- `sayane app daemon-recovery-consent-status`
- `sayane app daemon-operator-phase-status`

#### `GET /app/vault-status`

Future resident UI / native app 向けの Local Vault backend summary。

```bash
curl -s -H "$AUTH" \
  "http://127.0.0.1:38741/app/vault-status"
```

レスポンスは以下を返す:

- current repository backend が Local Vault かどうか
- runtime mode / vault mode
- keychain platform / assurance
- vault path と session support の有無

これは status / boundary の read surface であり、unlock 自体は行わない。

#### `GET /app/vault-session`

Future resident UI / native app 向けの process-local unlock session summary。

```bash
curl -s -H "$AUTH" \
  "http://127.0.0.1:38741/app/vault-session"
```

レスポンスは以下を返す:

- active unlock session 一覧
- `normal` / `sensitive` / `deep_private` policy preset
- runtime-local session reuse 可否

UI / app session と Local Vault unlock session は別物であり、自動継承しない。

#### `POST /app/vault-session/open`

Future resident UI / native app 向けの scoped unlock session open。

```bash
curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"level":"sensitive","purpose":"candidate-review"}' \
  "http://127.0.0.1:38741/app/vault-session/open"
```

`level` は `normal` / `sensitive` / `deep_private` を取る。

#### `POST /app/vault-session/lock`

Future resident UI / native app 向けの unlock session lock。

```bash
curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"scope":"all"}' \
  "http://127.0.0.1:38741/app/vault-session/lock"
```

現在の Local Vault integration では、vault backend が有効なとき:

- clipboard capture は active unlock session が必要
- candidate evaluate / approve / reject は active unlock session が必要
- candidate revise は active unlock session が必要

unlock session が無い場合、write surface は fail-closed で `409` を返す。

#### `GET /app/contract`

Future resident UI handoff 向けの contract metadata。

```bash
curl -s -H "$AUTH" \
  "http://127.0.0.1:38741/app/contract"
```

レスポンスは以下を返す:

- human-facing bootstrap surface
- preferred entrypoint
- read surfaces
- write surfaces
- recommended flow
- retained boundaries

#### `GET /app/ui`

Resident app の maintainer/debug local HTML compatibility shell。

Current maintenance boundary:

- current native macOS operator flowの代替 primary UI ではない
- explicit maintainer/debug / fallback / historical handoff のためだけに残す
- routine operator guidance や日常的な browser 起動導線は増やさない

Retirement boundary:

- `/app/ui-state/*` と `/app/ui-action/*` に必要な maintainer/debug transport が残っていても
  server-rendered HTML 自体は後で retire 可能
- HTML rendering 固有の debug/runbook 依存がなくなった時点で removable legacy surface に移せる

```bash
curl -s -H "$AUTH" \
  "http://127.0.0.1:38741/app/ui"
```

ブラウザで直接開く場合の debug shell entrypoint も同じで、`http://127.0.0.1:38741/app/ui` を使う。
routine operator flow ではなく、native diagnostics で不足するときだけ明示的に使う。
`http://127.0.0.1:8008/index.html` のような別静的配信前提の URL は現行 debug shell では使わない。

この endpoint は server-rendered HTML として以下を束ねて表示する:

- overview summary cards
- top review items
- top daemon next actions
- contract bootstrap guidance

これは local presentation surface であり、final GUI framework の確定ではない。
native macOS app の代替 primary UI ではなく、maintainer/debug / fallback / handoff 用の
compatibility surface として残している。

daemon panel では runtime / cleanup / repair preview に加えて、service target status と
macOS LaunchAgent preview も表示する。

また、packaging / service-control / supervision / recovery-consent の各契約も
structured panel として表示する。

resident shell 側の daemon 表示は raw nested payload を直接前提にせず、`operator_panels` /
`service_target_summary` / `launchagent_summary` を優先して描画する。

さらに current post-app line では `operator_phase_summary` と `operator_phase_details` を使い、
現在の運用経路、workstreams、read surfaces、exit criteria、not-in-scope reminders を
read-only で表示する。

bootstrap 後の resident app browser activity は dedicated local UI session cookie を使う。
follow-up browser request に raw bearer を毎回与える前提ではない。

#### `GET /app/ui/candidates`

Resident app の local HTML candidate queue screen。

```bash
curl -s -H "$AUTH" \
  "http://127.0.0.1:38741/app/ui/candidates"
```

`GET /app/ui/candidates/{id}` と `GET /app/ui/candidates/{id}/diff` を辿れる。

これは HTML review surface であり、approval flow 自体は既存 candidate API boundary に留まる。

#### `POST /app/ui/capture-clipboard`

`GET /app/ui` が設定する local UI session cookie を使う HTML form action。

- clipboard text から pending Candidate を作成する
- 成功時は `/app/ui/candidates/{id}` へ redirect する

#### `POST /app/ui/candidates/{id}/evaluate|approve|reject|revise`

`GET /app/ui/candidates/{id}` の local HTML action forms。

- evaluate は detail へ戻る
- revise は新しい Candidate detail へ遷移する
- approve / reject は queue へ戻る

#### `POST /app/ui-action/session/logout`

resident app の dedicated local UI session を明示的に無効化する local JSON action。

- Bridge bearer token は rotate しない
- browser follow-up UI request は再 bootstrap が必要になる
- focused regression では logout 後に `/app/ui-state/*` と `/app/ui-action/*` が再び UI session を要求することも確認する

これらは HTML surface だが、実際の mutation / review 処理は既存 app-facing candidate endpoints と同じ boundary に留まる。

現在の local HTML surface は redirect 後に:

- success notice
- validation / transition error feedback

を画面上に表示する。

#### `GET /app/ui/daemon`

`GET /app/ui` が設定する local UI session cookie を使う daemon panel。

```bash
curl -s -H "$AUTH" \
  "http://127.0.0.1:38741/app/ui/daemon"
```

この screen は以下をまとめる:

- daemon state summary
- readiness summary
- next actions
- runtime init preview
- cleanup preview
- repair preview

これは local HTML observation surface であり、daemon proof や process identity proof ではない。

proof-oriented CLI surfaces are now available for the same local runtime line:

- `sayane app daemon-identity-proof --json`
- `sayane app daemon-readiness-proof --operation-class bridge_health --json`
- `sayane app daemon-api-readiness-proof --operation-class bridge_health --json`
- `sayane app daemon-proof-diagnostics --operation-class bridge_health --json`
- `sayane app daemon-packaging-status --json`
- `sayane app daemon-service-targets-status --json`
- `sayane app daemon-service-control-boundary --json`
- `sayane app daemon-supervision-status --json`
- `sayane app daemon-recovery-consent-status --json`
- `sayane app daemon-launchagent-preview --json`

ただし、これらも conservative proof preview であり、verified proof を主張するものではない。
また、packaging / service-control / supervision / recovery-consent contract は operator guidance
surface であり、OS service integration や background control を有効化するものではない。

#### `GET /app/ui-state/*`（maintainer debug compatibility）

`GET /app/ui` が設定する local UI session cookie を使う、Bridge-hosted local shell 向けの
JSON read surfaces です。native macOS app の routine path ではなく、maintainer/debug / fallback /
handoff 向けの maintainer/debug compatibility surface として維持しています。

```bash
curl -s -b cookie.txt -c cookie.txt -H "$AUTH" \
  "http://127.0.0.1:38741/app/ui" >/dev/null
curl -s -b cookie.txt \
  "http://127.0.0.1:38741/app/ui-state/home"
```

現在の local shell read surfaces:

| メソッド | パス | 説明 |
|---------|------|------|
| `GET` | `/app/ui-state/contract` | local shell 向け contract |
| `GET` | `/app/ui-state/home` | local shell 向け home screen state |
| `GET` | `/app/ui-state/candidates` | local shell 向け candidate queue state |
| `GET` | `/app/ui-state/candidates/{id}` | local shell 向け candidate detail state |
| `GET` | `/app/ui-state/candidates/{id}/diff` | local shell 向け candidate diff payload |
| `GET` | `/app/ui-state/candidates/{id}/lineage` | local shell 向け candidate lineage payload |
| `GET` | `/app/ui-state/daemon` | local shell 向け daemon panel state |

これは local browser shell の same-origin fetch 用 transport seam であり、Bearer ベース
`/app/...` surface と同じ resident app semantics を再利用する。

#### `POST /app/ui-action/*`（maintainer debug compatibility）

`GET /app/ui` が設定する local UI session cookie を使う、Bridge-hosted local shell 向けの
JSON write surfaces です。native macOS app の routine path ではなく、maintainer/debug / fallback /
handoff 向けの maintainer/debug compatibility surface として維持しています。

```bash
curl -s -b cookie.txt -X POST -H "Content-Type: application/json" \
  -d '{"content":"important_terms:\n  - \"Sayane\"","locale":"ja"}' \
  "http://127.0.0.1:38741/app/ui-action/capture-clipboard"
```

現在の local shell write surfaces:

| メソッド | パス | 説明 |
|---------|------|------|
| `POST` | `/app/ui-action/capture-clipboard` | local shell 向け pending candidate 作成 |
| `POST` | `/app/ui-action/candidates/{id}/evaluate` | local shell 向け candidate 評価 |
| `POST` | `/app/ui-action/candidates/{id}/revise` | local shell 向け revised pending candidate 作成 |
| `POST` | `/app/ui-action/candidates/{id}/approve` | local shell 向け candidate 承認 |
| `POST` | `/app/ui-action/candidates/{id}/reject` | local shell 向け candidate 却下 |
| `POST` | `/app/ui-action/vault-session/open` | local shell 向け Local Vault unlock session open |
| `POST` | `/app/ui-action/vault-session/lock` | local shell 向け Local Vault unlock session lock |

これらは local shell transport の違いであり、review policy 自体を増やすものではない。

#### `POST /app/capture-clipboard`

Future resident UI 向けの clipboard capture entrypoint。

```bash
curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"content":"important_terms:\n  - \"Sayane\"","locale":"ja"}' \
  "http://127.0.0.1:38741/app/capture-clipboard"
```

この endpoint は clipboard 内容を pending Candidate として保存し、Candidate payload を返す。

直接 profile を更新せず、review flow の前段に留まる。

#### `GET /app/candidates`

Future resident UI 向けの reviewable candidate queue。

```bash
curl -s -H "$AUTH" \
  "http://127.0.0.1:38741/app/candidates"
```

pending / evaluated の reviewable candidate summaries を返す。

#### `GET /app/candidates/{id}`

Candidate detail を resident app review surface 用に返す。

#### `GET /app/candidates/{id}/diff`

Candidate diff を resident app review surface 用に返す。

#### `POST /app/candidates/{id}/evaluate`

Candidate を app-facing review flow から評価する。

#### `POST /app/candidates/{id}/revise`

Candidate を app-facing review flow から改稿し、新しい pending Candidate を作る。

#### `POST /app/candidates/{id}/approve`

Candidate を app-facing review flow から承認する。

#### `POST /app/candidates/{id}/reject`

Candidate を app-facing review flow から却下する。

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

1. `sayane serve` を常時起動
2. Extension Options に Bridge URL と Bearer token を設定
3. Popup から capture / insert

→ [Chrome Extension マニュアル](extension-manual.md)

## 5. MCP Server との違い

| | Bridge | MCP Server |
|--|--------|------------|
| プロトコル | HTTP | MCP (stdio) |
| 起動 | `sayane serve` | `sayane mcp serve` |
| 主なクライアント | Extension、curl | Cursor、Claude Desktop |
| 認証 | Bearer token 必須（`/health` 除く） | ローカル子プロセス |

同一 Core（Profile → Prompt IR → Adapter）を共有する。

## 6. トラブルシューティング

| 症状 | 対処 |
|------|------|
| `401 Unauthorized` | `bridge.token` を確認。`Authorization: Bearer` 形式 |
| `404 Profile not found` | `sayane init`、または `profiles/default/sayane.profile.yaml` の存在 |
| Extension が Bridge unreachable | `sayane serve` 起動中か、URL/port、token |
| curl から接続できない | `127.0.0.1` のみバインド。ファイアウォールは通常不要 |

## 7. バージョン

Sayane **0.5.8** 時点（Candidate evaluate/approve API 含む）。
