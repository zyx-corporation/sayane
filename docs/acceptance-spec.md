# OSS 版（Community Edition）受け入れテスト仕様

Sayane **Community Edition（OSS）** の受け入れ条件・テストシナリオ・証拠（自動テスト / 手動 UAT / Real Provider E2E）の対応を定義する。

受け入れテストは、単に機能が動くことだけを確認するものではない。Sayane においては、人格・文脈・prompt adaptation・provider・model・browser 実行状態の責務境界が保存され、意味変化が監査可能な状態で統合されていることを検収する。

| 項目 | 値 |
|------|-----|
| **対象リリース** | sayane **0.6.0+**（`sayane --version`） |
| **対象エディション** | Community Edition（Apache 2.0）のみ |
| **非対象** | sayane-pro 商用機能（暗号化 SQLite、ライセンス、Web UI 等）— pro 側ドキュメント参照 |
| **関連 Issue** | [#78](https://github.com/zyx-corporation/sayane/issues/78) OSS 契約維持 · [#88](https://github.com/zyx-corporation/sayane/issues/88) L2 Core 手動 · [#89](https://github.com/zyx-corporation/sayane/issues/89) L3 Extension UAT · [#91](https://github.com/zyx-corporation/sayane/issues/91) Real DOM E2E · [#96](https://github.com/zyx-corporation/sayane/issues/96) Provider adapters |

下位手順書:

- [CLI 受け入れテスト（考察・手順）](cli-acceptance-test.md) — L2-CLI 詳細
- [Chrome Extension 受け入れテスト](extension-acceptance-test.md) — Extension 手動 UAT
- [Chrome Extension Real DOM E2E 手順](extension-real-dom-e2e.md) — L4 Real Provider E2E
- [Sayane 管理ディレクトリ（SAYANE_DIR）](sayane-dir-layout.md) — L0 Layout 契約
- [Dogfood 手順書](dogfood-walkthrough.md) — エンドツーエンド手動確認

---

## 1. 受け入れの五層

| 層 | 目的 | 実施タイミング | 証拠 |
|----|------|--------------|------|
| **L0 Layout / Contract** | `$SAYANE_DIR`、`profiles/`、`prompts/`、`e2e/` の責務境界を検証 | 毎 PR / main push | `pytest`、[sayane-dir-layout.md](sayane-dir-layout.md) |
| **L1 Unit / API Contract** | Core、Adapter、RDE、Storage、Bridge、MCP の機械検証 | 毎 PR / main push | `pytest`（本リポジトリ `tests/`） |
| **L2 Core Integration** | CLI / Bridge / MCP / Storage の結合 | リリース前・Core 変更時 | 本書 §4、[cli-acceptance-test.md](cli-acceptance-test.md) |
| **L3 Extension Integration** | Extension / popup / browser / mock Bridge の結合 | Extension / Bridge 変更時 | [extension-acceptance-test.md](extension-acceptance-test.md)、Playwright mock/local E2E |
| **L4 Real Provider** | ChatGPT / Claude / 将来の Gemini / DeepSeek / local UI の実DOM・運用監視 | workflow_dispatch / scheduled / release前 / provider adapter変更時 | [extension-real-dom-e2e.md](extension-real-dom-e2e.md)、artifact、失敗分類 |

**Core リリース判定**: L0 green、L1 green、L2 の必須シナリオがすべて Pass。

**Extension リリース判定**: L0 green、L1 green、Bridge 関連 L2 が Pass、L3 必須 Pass。

**Provider adapter リリース判定**: L0 green、L1 provider contract green、L3 mock/local E2E Pass、L4 real provider が Pass または非回帰分類（`AUTH_REQUIRED` / `DOM_DRIFT` 等）で説明可能。

---

## 2. OSS スコープ（機能仕様）

Community Edition が **保証する** 機能境界。詳細操作は各マニュアルを正とする。

### 2.0 Layout / SAYANE_DIR

| 要件 ID | 仕様 | 根拠 |
|---------|------|------|
| LAY-01 | `SAYANE_DIR` 未指定時は `~/.sayane` を管理ルートとする | `tests/test_cli.py`, [sayane-dir-layout.md](sayane-dir-layout.md) |
| LAY-02 | `SAYANE_DIR` 指定時は Profile / prompt / E2E の既定パスがその配下に移る | `tests/test_cli.py` |
| LAY-03 | `sayane init` は `$SAYANE_DIR/profiles/default/sayane.profile.yaml` を作成する | `tests/test_cli.py` |
| LAY-04 | `sayane init` は `$SAYANE_DIR/prompts/targets`, `prompts/models`, `prompts/providers` を作成する | `tests/test_cli.py` |
| LAY-05 | `sayane init` は `$SAYANE_DIR/e2e/user-data`, `e2e/prompts` を作成する | `tests/test_cli.py` |
| LAY-06 | 既存 Profile は `--force` なしで上書きしない | `tests/test_cli.py` |
| LAY-07 | `e2e/user-data/` は browser/session state 専用であり、prompt 正本として扱わない | [sayane-dir-layout.md](sayane-dir-layout.md) |

### 2.1 Core / Compile

| 要件 ID | 仕様 | 根拠 |
|---------|------|------|
| CORE-01 | `SayaneProfile` / `PromptIR` が JSON Schema と整合する | `schemas/`, `tests/test_schemas.py` |
| CORE-02 | 最小 Profile から Prompt IR を構築できる | `tests/test_builder.py` |
| CORE-03 | `chatgpt` / `claude` adapter が Prompt IR を各 LLM 形式に変換する | `tests/test_adapters.py`, `src/sayane/adapters/factory.py` |
| CORE-04 | 未知 `target` は明示エラーとなり、Supported target を表示する | `tests/test_adapters.py::test_factory_rejects_unknown_target`, `tests/test_cli.py` |
| CORE-05 | `gemini` / `deepseek` / `openai_compatible` / `plain_text` は将来拡張であり、未実装時は保証対象外 | [#96](https://github.com/zyx-corporation/sayane/issues/96) |

### 2.2 CLI

| 要件 ID | 仕様 | 根拠 |
|---------|------|------|
| CLI-01 | `sayane init` で `$SAYANE_DIR` 配下の標準レイアウトを作成 | `tests/test_cli.py`, [sayane-dir-layout.md](sayane-dir-layout.md) |
| CLI-02 | `sayane compile --target <adapter>` で stdout に機械可読 JSON を出力 | `tests/test_cli.py` |
| CLI-03 | エラー診断は stderr に出し、成果物 stdout と混ぜない | `tests/test_cli.py` |
| CLI-04 | `sayane profile inspect` / `export` が動作 | `tests/test_cli.py` |
| CLI-05 | `sayane candidate list|evaluate|diff|approve|reject|lineage` | `tests/test_candidate_cli.py`, `tests/test_critical_merge.py` |
| CLI-06 | `sayane storage import|index|commit|backend status|list|set` | `tests/test_storage_cli.py`, `tests/test_storage_backend.py` |
| CLI-07 | `sayane mcp serve` および MCP サブコマンド | `tests/test_mcp_cli.py` |
| CLI-08 | `sayane serve` で Bridge を localhost に起動 | Bridge テスト・Dogfood |
| CLI-09 | i18n（`SAYANE_LANG` / `--lang`） | `tests/test_cli_i18n.py`, `tests/test_cli_locale_resolve.py` |
| CLI-10 | `sayane-pro` 未インストール時、plugin hook は no-op | `tests/test_cli_plugins.py` |

### 2.3 Storage（filesystem backend）

| 要件 ID | 仕様 | 根拠 |
|---------|------|------|
| STOR-01 | 既定 backend は `filesystem` | `tests/test_storage_backend.py` |
| STOR-02 | `StorageBundle`（Profile / Context / Lineage）抽象が安定 | [storage-backend.md](storage-backend.md) |
| STOR-03 | `sayane.storage_backends` entry point で backend 登録可能 | `tests/test_storage_backend.py::test_mock_backend_registration_contract` |
| STOR-04 | factory シグネチャ `(storage_config, *, home, profile_dir) -> StorageBundle` | `tests/test_storage_backend.py` |
| STOR-05 | `storage index` で `context_index.entries` を再生成 | `tests/test_context_index.py` |
| STOR-06 | Obsidian vault import（`.obsidian` 除外、`SAYANE_OBSIDIAN_VAULT`） | `tests/test_obsidian.py`, `tests/test_storage_cli.py` |
| STOR-07 | Git 自動コミット（filesystem backend、`storage index` / `commit`） | `tests/test_storage_git.py` |
| STOR-08 | Storage 操作は `$SAYANE_DIR` 基準の Profile Store と整合する | `tests/test_cli.py`, `tests/test_storage_cli.py` |

### 2.4 Candidate / RDE / Lineage

| 要件 ID | 仕様 | 根拠 |
|---------|------|------|
| CAND-01 | capture → pending Candidate として保存 | `tests/test_bridge_api.py`, `tests/test_candidate_flow.py` |
| CAND-02 | Level 1 評価で RDE class が付与される | `tests/test_candidate_flow.py`, `tests/test_rde.py` |
| CAND-03 | rule-based diff（`add` / `already_present`） | `tests/test_bridge_api.py`, `tests/test_critical_merge.py` |
| CAND-04 | approve 前に Profile へ merge されない | [security.md](security.md), Extension SEC-04 |
| CAND-05 | `Critical Distortion` は `force_critical` なしで approve 拒否 | `tests/test_critical_merge.py` |
| CAND-06 | approve 後 lineage に記録 | `tests/test_candidate_flow.py`, Dogfood §5 |
| CAND-07 | legacy capture JSON は読み込み時にアップグレード | `tests/test_candidate_flow.py::test_legacy_capture_upgraded_on_load` |

### 2.5 Local Bridge API

| 要件 ID | 仕様 | 根拠 |
|---------|------|------|
| BRG-01 | `GET /health` は認証不要・200 | `tests/test_bridge_api.py` |
| BRG-02 | 保護エンドポイントは Bearer token 必須（401） | `tests/test_bridge_api.py` |
| BRG-03 | `GET /profiles` — Profile 一覧 | `tests/test_bridge_api.py` |
| BRG-04 | `POST /compile` — adapter 出力 | `tests/test_bridge_api.py` |
| BRG-05 | `GET /context-packet` — 文脈パケット | `tests/test_bridge_api.py` |
| BRG-06 | `POST /capture` — Candidate 保存 | `tests/test_bridge_api.py` |
| BRG-07 | `GET|POST /candidates/*` — list / evaluate / diff / approve フロー | `tests/test_bridge_api.py` |
| BRG-08 | バインドは `127.0.0.1` のみ（外部公開非対象） | [security.md](security.md), [bridge-manual.md](bridge-manual.md) |
| BRG-09 | token は `$SAYANE_DIR` 配下に生成され、page DOM へ露出しない | [security.md](security.md), [extension-real-dom-e2e.md](extension-real-dom-e2e.md) |

### 2.6 MCP Server

| 要件 ID | 仕様 | 根拠 |
|---------|------|------|
| MCP-01 | `list_profiles` / `inspect_profile` | `tests/test_mcp_operations.py` |
| MCP-02 | `compile` と `context-packet` の出力整合 | `tests/test_mcp_operations.py::test_generate_context_packet_matches_compile` |
| MCP-03 | candidate list / evaluate / diff / show | `tests/test_mcp_operations.py` |
| MCP-04 | 未対応 target はエラー | `tests/test_mcp_operations.py::test_unsupported_target` |

### 2.7 Extension / Provider / Real DOM

| 要件 ID | 仕様 | 根拠 |
|---------|------|------|
| EXT-01 | Extension は Bridge API を background / service worker 経由で呼ぶ | [extension-manual.md](extension-manual.md), [extension-acceptance-test.md](extension-acceptance-test.md) |
| EXT-02 | Capture / Insert は `activeTab` + `chrome.scripting.executeScript` で行う | [extension-acceptance-test.md](extension-acceptance-test.md) |
| EXT-03 | token は content script / page DOM に露出しない | [security.md](security.md), [extension-real-dom-e2e.md](extension-real-dom-e2e.md) |
| EXT-04 | ChatGPT / Claude の実DOM挿入は marker 挿入のみを検証し、送信しない | [extension-real-dom-e2e.md](extension-real-dom-e2e.md), [#91](https://github.com/zyx-corporation/sayane/issues/91) |
| EXT-05 | L4 failure は `AUTH_REQUIRED` / `DOM_DRIFT` / `PERMISSION_ERROR` / `SAYANE_REGRESSION` 等に分類する | [extension-real-dom-e2e.md](extension-real-dom-e2e.md) |
| PROV-01 | provider id / target / profileKey / model を分離する | [#96](https://github.com/zyx-corporation/sayane/issues/96), [sayane-dir-layout.md](sayane-dir-layout.md) |
| PROV-02 | local SLM は単一 provider ではなく UI 単位で扱う | [#96](https://github.com/zyx-corporation/sayane/issues/96) |
| PROV-03 | model 最適化 prompt は `prompts/models/`、provider制約は `prompts/providers/` に置く | [sayane-dir-layout.md](sayane-dir-layout.md) |

### 2.8 OSS 公開契約（スキーマ）

| 要件 ID | 仕様 | 根拠 |
|---------|------|------|
| OSS-01 | Confidentiality Policy JSON Schema が有効 | `tests/test_confidentiality_policy_schema.py` |
| OSS-02 | サンプル policy YAML が schema を pass | `tests/test_confidentiality_policy_schema.py` |
| OSS-03 | Storage backend プラグイン IF が文書化・テスト済み | [storage-backend.md](storage-backend.md), `#65` |
| OSS-04 | Commercial 側 `test_oss_contract` が本契約を参照可能 | sayane-pro `python/tests/test_oss_contract.py` |

### 2.9 非スコープ（Community が保証しない）

- 暗号化 SQLite / `storage migrate` / 商用 daemon / Web UI / 機密監査 CLI 実行体
- Rust semantic diff / vault indexer（sayane-pro ライセンス feature）
- Windows MSI インストーラ
- LLM judge（Level 2）— **任意機能**（未設定時は Skip 可）
- Gemini / DeepSeek / local SLM provider の production adapter — Issue #96 の将来拡張
- 実サービスへの自動送信・応答内容検証

---

## 3. 契約とテストの対応表

[development-principles.md §7](development-principles.md) の Contract / Regression / Security と pytest / UAT / E2E の対応。

| 原則カテゴリ | 契約対象 | 自動テスト | 手動 / E2E |
|-------------|---------|-----------|------------|
| Layout | `$SAYANE_DIR`, `prompts/`, `e2e/` | `tests/test_cli.py` | [sayane-dir-layout.md](sayane-dir-layout.md) |
| Unit | Profile / PromptIR / Adapter | `test_models.py`, `test_adapters.py`, `test_builder.py` | — |
| Contract | Storage backend IF | `test_storage_backend.py` | STOR-M01 |
| Contract | Bridge HTTP | `test_bridge_api.py` | BRG-M01〜M03 |
| Contract | MCP operations | `test_mcp_operations.py` | MCP-M01 |
| Contract | Confidentiality schema | `test_confidentiality_policy_schema.py` | — |
| Contract | Extension ↔ Bridge | future Playwright mock/local | [extension-acceptance-test.md](extension-acceptance-test.md) |
| Real Provider | ChatGPT / Claude real DOM | Playwright real DOM（manual/scheduled） | [extension-real-dom-e2e.md](extension-real-dom-e2e.md) |
| Regression | RDE merge / critical gate | `test_rde.py`, `test_critical_merge.py`, `test_rde_merge.py` | CAND-M02 |
| Security | Bridge token | `test_bridge_api.py::test_invalid_token_rejected` | SEC-M01 |
| Security | Approve gate | `test_critical_merge.py` | SEC-M02 |
| Plugin | CLI/hooks noop | `test_cli_plugins.py` | — |

---

## 4. 手動受け入れシナリオ（L2 Core）

**所要時間**: 45〜60 分（Level 2 評価を含む場合 +10 分）

### 4.0 結果記録シート

| ID | 区分 | 必須 | 結果 | 実測・メモ |
|----|------|:----:|:----:|------------|
| PRE-M01 | 前提 | ✓ | | |
| PRE-M02 | 前提 | ✓ | | |
| PRE-M03 | 前提/Layout | ✓ | | |
| CLI-M01 | CLI | ✓ | | |
| CLI-M02 | CLI | ✓ | | |
| CLI-M03 | CLI | ✓ | | |
| STOR-M01 | Storage | ✓ | | |
| STOR-M02 | Storage | ✓ | | |
| CAND-M01 | Candidate | ✓ | | |
| CAND-M02 | Candidate | ✓ | | |
| CAND-M03 | Candidate | | | |
| BRG-M01 | Bridge | ✓ | | |
| BRG-M02 | Bridge | ✓ | | |
| BRG-M03 | Bridge | ✓ | | |
| MCP-M01 | MCP | ✓ | | |
| SEC-M01 | Security | ✓ | | |
| SEC-M02 | Security | ✓ | | |

**記号**: **P** Pass / **F** Fail / **S** Skip / **N/A** 対象外

### 4.1 前提（PRE-M）

| ID | 手順 | 期待結果 |
|----|------|----------|
| PRE-M01 | `pip install -e ".[dev]"` 後 `pytest -q` | 全 test pass（skip のみ許容） |
| PRE-M02 | `sayane --version` | `0.6.0` 以上 |
| PRE-M03 | `SAYANE_DIR=/tmp/sayane-uat sayane init` | `$SAYANE_DIR/profiles/default/sayane.profile.yaml`、`prompts/targets`、`prompts/models`、`prompts/providers`、`e2e/user-data`、`e2e/prompts` が存在 |

### 4.2 CLI（CLI-M）

詳細シナリオ・考察・記録シートは **[cli-acceptance-test.md](cli-acceptance-test.md)** を正とする。本書では最小セットのみ定義する。

| ID | 手順 | 期待結果 |
|----|------|----------|
| CLI-M01 | `sayane profile inspect` | Profile summary が表示される |
| CLI-M02 | `sayane compile --target chatgpt` | stdout が JSON。stderr に診断が混入しない |
| CLI-M03 | `sayane compile --target not-a-llm` | 非ゼロ終了。stdout は空。stderr に `Unknown target` と Supported target が表示 |

### 4.3 Storage（STOR-M）

| ID | 手順 | 期待結果 |
|----|------|----------|
| STOR-M01 | `sayane storage backend status` | backend が `filesystem` |
| STOR-M02 | `sayane storage index` | `context_index.entries` が再生成され、必要に応じて Git commit |

### 4.4 Candidate / RDE（CAND-M）

| ID | 手順 | 期待結果 |
|----|------|----------|
| CAND-M01 | Capture 相当の Candidate を作成し `candidate list` | pending Candidate が表示される |
| CAND-M02 | `candidate evaluate` → `candidate diff` → `candidate approve` | RDE class、diff、merge、lineage が確認できる |
| CAND-M03 | Critical candidate を `--force-critical` なしで approve | 拒否される（任意だが推奨） |

### 4.5 Bridge（BRG-M）

| ID | 手順 | 期待結果 |
|----|------|----------|
| BRG-M01 | `sayane serve` → `GET /health` | HTTP 200 |
| BRG-M02 | token なしで `GET /profiles` | 401 |
| BRG-M03 | Bearer token 付きで `/profiles` / `/context-packet` | 正常応答 |

### 4.6 MCP（MCP-M）

| ID | 手順 | 期待結果 |
|----|------|----------|
| MCP-M01 | `sayane mcp list-profiles` / `sayane mcp compile --target chatgpt` | JSON応答。CLI compile と整合 |

### 4.7 Security（SEC-M）

| ID | 手順 | 期待結果 |
|----|------|----------|
| SEC-M01 | Bridge token を誤らせる | 401 / 明示エラー |
| SEC-M02 | Critical approve を通常 approve する | 拒否される |

---

## 5. L3 Extension / L4 Real Provider

### 5.1 L3 Extension Integration

Extension の手動 UAT は [extension-acceptance-test.md](extension-acceptance-test.md) を正とする。

最低限の必須観点:

- Options pairing
- Bridge connected
- Profile / Candidate 表示
- Capture selection / page
- Candidate evaluate / diff / approve
- ChatGPT / Claude insert
- token が popup / page DOM に露出しないこと

### 5.2 L4 Real Provider E2E

Real DOM E2E は [extension-real-dom-e2e.md](extension-real-dom-e2e.md) を正とする。

L4 は通常 PR の必須ゲートではない。以下で実行する。

- workflow_dispatch
- scheduled
- release前
- provider adapter 変更時
- DOM drift 調査時

L4 の合否は単純な Pass / Fail ではなく、失敗分類を含む。

| 分類 | リリース判定 |
|------|--------------|
| `SAYANE_REGRESSION` | blocker |
| `PERMISSION_ERROR` | blocker になり得る |
| `DOM_DRIFT` | adapter update issue を作成。Sayane core の regression ではない |
| `AUTH_REQUIRED` | 環境問題。通常PRでは blocker ではない |
| `NETWORK_OR_RATE_LIMIT` | 再実行または環境確認 |
| `ENVIRONMENT_ERROR` | E2E環境修正 |

---

## 6. Provider / Target / Model 分離

Gemini、DeepSeek、local SLM UI への拡張では、次の分離を保つ。

```text
provider id = 実DOM / UI / 配送対象
target      = Prompt IR の変換先
model       = 実際の LLM / SLM 能力特性
profileKey  = $SAYANE_DIR/e2e/user-data/{key}
```

例:

| 用途 | provider id | target | model |
|------|-------------|--------|-------|
| Gemini Web | `gemini` | `gemini` | Gemini 系 |
| DeepSeek Web | `deepseek` | `deepseek` | DeepSeek 系 |
| Open WebUI + Qwen | `local-openwebui` | `plain_text` or `openai_compatible` | Qwen2.5 |
| LibreChat + DeepSeek | `local-librechat` | `openai_compatible` | DeepSeek-R1-Distill |
| custom local UI | `local-custom` | `plain_text` | 任意 SLM |

model-specific prompt optimization は `prompts/models/` に置く。provider/UI-specific constraints は `prompts/providers/` に置く。target-level prompt adaptation は `prompts/targets/` に置く。

`e2e/user-data/` には置かない。

---

## 7. RDE観点での合否基準

### 保存すべき要素

- Sayane Profile は人格・文脈の正本であり、LLMや browser user-data に従属しない。
- Prompt adaptation は監査可能な意味資産として `prompts/` に置く。
- Browser user-data は不透明な実行状態として `e2e/user-data/` に隔離する。
- Candidate は approve 前に Profile へ merge されない。
- Critical Distortion は明示的 force なしに merge されない。

### 許可された変換

- 手動 UAT の一部を Playwright E2E へ移す。
- ChatGPT / Claude 固定から provider registry 方式へ移行する。
- `~/.sayane` 固定から `$SAYANE_DIR` による管理境界へ移行する。

### 補完された要素

- L0 Layout / Contract
- L4 Real Provider
- failure classification
- provider / target / model / profileKey 分離
- prompts/targets, prompts/models, prompts/providers

### Critical drift

以下は release blocker とする。

- 未実装 target を保証済み仕様として記述する。
- `e2e/user-data/` を prompt 正本として扱う。
- token を page DOM / content script に露出する。
- Candidate approve 前に Profile を変更する。
- Critical Distortion を通常 approve できる。

---

## 8. 変更履歴

| 日付 | 版 | 内容 |
|------|-----|------|
| 2026-05-25 | 0.6.0 draft | L0〜L4へ再構成。`SAYANE_DIR`、prompt/e2e分離、Real Provider E2E、provider/target/model分離を追加。Gemini adapter を保証済みから将来拡張へ修正。 |
| 2026-05-24 | 0.6.0 draft | OSS Community Edition 受け入れ仕様初版 |
