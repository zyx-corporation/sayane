# Sayane Security Design

## 1. 目的

Sayane は、ユーザーの人格的文脈・価値観・応答様式・作業方針を扱う。そのため、通常のローカルツール以上に privacy と security を重視する必要がある。

特に Local Bridge と MCP Server は、ローカルで動作するとはいえ、外部ページ、ブラウザ拡張、MCPクライアントから到達可能な接続面になる。localhost API は安全であると仮定してはならない。

## 2. 基本原則

```text
Profileは機微情報である。
localhostは信頼境界ではない。
captureはmergeではない。
read-onlyを既定にする。
危険操作は明示承認を必須にする。
```

## 3. 脅威モデル

### 3.1 悪意あるWebページ

ブラウザからlocalhost APIへアクセスを試みる可能性がある。

対策:

- CORS deny by default
- Origin allowlist
- pairing token
- CSRF token
- JSON content-type enforcement
- unsafe endpoint separation

### 3.2 Chrome Extensionの侵害

Extensionが侵害された場合、ProfileやContextへのアクセス経路になり得る。

対策:

- Extension ID verification
- least privilege permissions
- token rotation
- read-only mode
- merge操作の分離
- audit log

### 3.3 SSRF / Localhost probing

外部ページがユーザーのブラウザを通じてlocalhost上のサービスを探索する可能性がある。

対策:

- random high port
- explicit bind to 127.0.0.1 only
- token required for all non-health endpoints
- `/health` に機微情報を含めない
- rate limit
- invalid request logging

### 3.4 Profile汚染

WebページやLLM出力が、ユーザーの長期Profileへ不正確な情報を混入させる危険がある。

対策:

- captureをCandidate Updateとして保存
- automatic merge禁止
- RDE diff
- user approval
- lineage record

### 3.5 Prompt Injection

Webページや会話ログに、AIまたはSayane処理を誘導する命令が含まれる可能性がある。

対策:

- captured contentを命令ではなくデータとして扱う
- source metadataを保持
- prompt injection indicator検出
- evaluatorでSuspicious Driftへ分類
- Profile / Policyへの直接反映禁止

## 4. Local Bridge Security

Local Bridge は、Phase 2で実装するlocalhost APIである。

最低要件:

```text
bind: 127.0.0.1 only
CORS: deny by default
Auth: bearer token required
Pairing: one-time pairing code
Origin: allowlist required
Extension ID: verification if available
Merge: explicit approval only
Audit: all state-changing requests logged
```

## 5. API分類

### 5.1 Safe read endpoint

例:

- `GET /health`
- `GET /profiles`

注意:

`/health` は機微情報を返さない。

### 5.2 Compile endpoint

例:

- `POST /compile`
- `GET /context-packet`

注意:

Profile情報を含む出力を返すため、認証必須。

### 5.3 Capture endpoint

例:

- `POST /capture`

注意:

captureはProfile mergeではない。Candidate Updateとして保存する。

### 5.4 Dangerous endpoint

例:

- `POST /candidate-updates/{id}/approve`
- `POST /profile/merge`

注意:

初期段階ではprofile merge endpointを公開しない方針とする。実装する場合は、明示的なユーザー承認、RDE結果、lineage記録を必須とする。

## 6. MCP Server Security

MCP Server はPhase 2.5で実装する安定接続面である。

初期MVPではread-only modeを既定にする。

許可する操作:

- profile list
- profile inspect summary
- compile prompt
- context packet generation
- candidate update list

禁止する操作:

- direct profile merge
- policy rewrite
- identity rewrite
- values rewrite
- secret export

MCP経由でProfileを変更する場合は、Phase 4以降に明示承認フローとRDE評価を実装してから扱う。

## 7. Secret Handling

Sayane ProfileやContextにAPI key、password、token、private keyなどが混入する可能性がある。

初期段階で以下を検討する。

- secret pattern detection
- capture時の警告
- export時のredaction option
- lineageへのsecret保存禁止
- Git commit前のsecret scan

Commercial Edition では **機密データ基準・許容範囲の登録** と **逸脱監査** を提供する（[Confidentiality Policy 契約](confidentiality-policy-schema.md)）。RDE（意味変化）と相互補完する。

## 8. Audit Log

状態変更操作はaudit logへ記録する。

記録対象:

- capture
- candidate generation
- evaluation
- approval
- rejection
- merge
- export
- adapter compile

ただし、audit log自体にも機微情報が含まれる可能性があるため、保存形式とredactionを検討する。

## 9. RDE観点

Security設計は単なる防御ではない。

Sayaneにおいては、セキュリティ侵害は同時に意味変化の侵害でもある。

```text
Profileが汚染されることは、ユーザーの人格的文脈が外部要因によって改変されることである。
```

したがって、security review と RDE review は分離せず、相互補完的に扱う。

Commercial Edition では、機密区分・セクション許容範囲の登録と逸脱監査を [Confidentiality Policy 契約](confidentiality-policy-schema.md) に基づいて行う。
