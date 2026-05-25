# OSS 版（Community Edition）受け入れテスト仕様

Sayane **Community Edition（OSS）** の受け入れ条件・テストシナリオ・証拠（自動テスト / 手動 UAT）の対応を定義する。

| 項目 | 値 |
|------|-----|
| **対象リリース** | sayane **0.6.0+**（`sayane --version`） |
| **対象エディション** | Community Edition（Apache 2.0）のみ |
| **非対象** | sayane-pro 商用機能（暗号化 SQLite、ライセンス、Web UI 等）— pro 側ドキュメント参照 |
| **関連 Issue** | [#78](https://github.com/zyx-corporation/sayane/issues/78) OSS 契約維持 · [#88](https://github.com/zyx-corporation/sayane/issues/88) L2 Core 手動 · [#89](https://github.com/zyx-corporation/sayane/issues/89) L3 Extension UAT · [#92](https://github.com/zyx-corporation/sayane/issues/92) L1 自動化バックログ · [#93](https://github.com/zyx-corporation/sayane/issues/93) 手動のみ整理 |

下位手順書:

- [CLI 受け入れテスト（考察・手順）](cli-acceptance-test.md) — L2-CLI 詳細（本書 §4 の拡張）
- [Chrome Extension 受け入れテスト](extension-acceptance-test.md) — Extension 専用 UAT（本書 §8 から参照）
- [Dogfood 手順書](dogfood-walkthrough.md) — エンドツーエンド手動確認

---

## 1. 受け入れの三層

| 層 | 目的 | 実施タイミング | 証拠 |
|----|------|--------------|------|
| **L1 自動（CI）** | 回帰・契約の機械検証 | 毎 PR / main push | `pytest`（本リポジトリ `tests/`） |
| **L2 手動（Core）** | CLI / Bridge / MCP / Storage の結合 | リリース前・Core 変更時 | 本書 §4 · Issue [#88](https://github.com/zyx-corporation/sayane/issues/88) |
| **L3 手動（Extension）** | ブラウザ DOM・popup 結合 | Extension / Bridge 変更時 | [extension-acceptance-test.md](extension-acceptance-test.md) · Issue [#89](https://github.com/zyx-corporation/sayane/issues/89) |

**リリース判定**: L1 が green、L2 の **必須シナリオがすべて Pass**、Extension に変更がある場合は L3 必須 Pass。

### 1.1 自動化できる部分 / できない部分

| 区分 | 内容 | 追跡 Issue |
|------|------|-----------|
| **L1 済み** | Core schema、Adapter、Bridge TestClient 主要経路、Storage 契約、MCP operations、CLI Candidate フルフロー・エラー経路・Critical 拒否、Storage export/commit、PLG 境界 | 本書 §5.2 · `tests/test_acceptance_cli.py` |
| **L1 拡張（任意）** | 受け入れ ID ↔ pytest の網羅レジストリ拡張 | `tests/test_acceptance_coverage.py` · [#92](https://github.com/zyx-corporation/sayane/issues/92) |
| **手動のみ** | Extension DOM・Options UI、実サイト Insert、サインオフ記録、任意 LLM judge、UX 目視 | [#93](https://github.com/zyx-corporation/sayane/issues/93) |
| **手動＋scheduled E2E** | ChatGPT / Claude 実 DOM Insert | [#91](https://github.com/zyx-corporation/sayane/issues/91) |

[#92](https://github.com/zyx-corporation/sayane/issues/92) 完了後は、該当シナリオを L2 必須から外し L1 のみで足りる旨を本書と [#88](https://github.com/zyx-corporation/sayane/issues/88) に反映する。

---

## 2. OSS スコープ（機能仕様）

Community Edition が **保証する** 機能境界。詳細操作は各マニュアルを正とする。

### 2.1 Core / Compile

| 要件 ID | 仕様 | 根拠 |
|---------|------|------|
| CORE-01 | `SayaneProfile` / `PromptIR` が JSON Schema と整合する | `schemas/`, `tests/test_schemas.py` |
| CORE-02 | 最小 Profile から Prompt IR を構築できる | `tests/test_builder.py` |
| CORE-03 | `chatgpt` / `claude` / `gemini` adapter が Prompt IR を各 LLM 形式に変換する | `tests/test_adapters.py` |
| CORE-04 | 未知 `target` は明示エラー | `tests/test_adapters.py::test_factory_rejects_unknown_target` |

### 2.2 CLI

| 要件 ID | 仕様 | 根拠 |
|---------|------|------|
| CLI-01 | `sayane init` で `~/.sayane/profiles/default/` を作成 | `tests/test_cli.py` |
| CLI-02 | `sayane compile --target <adapter>` で stdout に JSON 出力 | `tests/test_cli.py` |
| CLI-03 | `sayane profile inspect` / `export` が動作 | `tests/test_cli.py` |
| CLI-04 | `sayane candidate list|evaluate|diff|approve|reject|lineage` | `tests/test_candidate_cli.py`, `tests/test_acceptance_cli.py`, `tests/test_critical_merge.py` |
| CLI-05 | `sayane storage import|index|commit|backend status|list|set` | `tests/test_storage_cli.py`, `tests/test_storage_backend.py`, `tests/test_acceptance_cli.py` |
| CLI-06 | `sayane mcp serve` および MCP サブコマンド（`context-packet` 含む） | `tests/test_mcp_cli.py`, `tests/test_acceptance_cli.py` |
| CLI-07 | `sayane serve` で Bridge を起動 | Bridge テスト・Dogfood |
| CLI-08 | i18n（`SAYANE_LANG` / `--lang`） | `tests/test_cli_i18n.py`, `tests/test_cli_locale_resolve.py` |
| CLI-09 | `sayane-pro` 未インストール時、商用 CLI 拡張が `--help` に出ない | `tests/test_acceptance_cli.py::test_help_excludes_commercial_commands_without_extensions` |

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
| BRG-07 | `GET|POST /candidates/*` — list / evaluate / diff / approve / reject、Critical approve 拒否 | `tests/test_bridge_api.py` |
| BRG-08 | バインドは `127.0.0.1` のみ（外部公開非対象） | [security.md](security.md), [bridge-manual.md](bridge-manual.md) |

### 2.6 MCP Server

| 要件 ID | 仕様 | 根拠 |
|---------|------|------|
| MCP-01 | `list_profiles` / `inspect_profile` | `tests/test_mcp_operations.py` |
| MCP-02 | `compile` と `context-packet` の出力整合 | `tests/test_mcp_operations.py::test_generate_context_packet_matches_compile` |
| MCP-03 | candidate list / evaluate / diff / show | `tests/test_mcp_operations.py` |
| MCP-04 | 未対応 target はエラー | `tests/test_mcp_operations.py::test_unsupported_target` |

### 2.7 OSS 公開契約（スキーマ）

| 要件 ID | 仕様 | 根拠 |
|---------|------|------|
| OSS-01 | Confidentiality Policy JSON Schema が有効 | `tests/test_confidentiality_policy_schema.py` |
| OSS-02 | サンプル policy YAML が schema を pass | `tests/test_confidentiality_policy_schema.py` |
| OSS-03 | Storage backend プラグイン IF が文書化・テスト済み | [storage-backend.md](storage-backend.md), `#65` |
| OSS-04 | Commercial 側 `test_oss_contract` が本契約を参照可能 | sayane-pro `python/tests/test_oss_contract.py` |

### 2.8 非スコープ（Community が保証しない）

- 暗号化 SQLite / `storage migrate` / 商用 daemon / Web UI / 機密監査 CLI 実行体
- Rust semantic diff / vault indexer（sayane-pro ライセンス feature）
- Windows MSI インストーラ
- LLM judge（Level 2）— **任意機能**（未設定時は Skip 可）

---

## 3. 契約とテストの対応表

[development-principles.md §7](development-principles.md) の Contract / Regression / Security と pytest の対応。

| 原則カテゴリ | 契約対象 | 自動テスト | 手動 UAT |
|-------------|---------|-----------|---------|
| Unit | Profile / PromptIR / Adapter | `test_models.py`, `test_adapters.py`, `test_builder.py` | — |
| Contract | Storage backend IF | `test_storage_backend.py` | STOR-M01 |
| Contract | Bridge HTTP | `test_bridge_api.py` | BRG-M01〜M03 |
| Contract | MCP operations | `test_mcp_operations.py` | MCP-M01 |
| Contract | Confidentiality schema | `test_confidentiality_policy_schema.py` | — |
| Contract | Extension ↔ Bridge | — | [extension-acceptance-test.md](extension-acceptance-test.md) |
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
| PRE-M03 | 前提 | ✓ | | |
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
| PRE-M03 | `sayane init`（未実施環境） | `~/.sayane/profiles/default/sayane.profile.yaml` 存在 |

### 4.2 CLI（CLI-M）

詳細シナリオ・考察・記録シートは **[cli-acceptance-test.md](cli-acceptance-test.md)** を正とする。本節は L2 Core の最小確認。

| ID | 手順 | 期待結果 | 詳細 ID |
|----|------|----------|---------|
| CLI-M01 | `sayane profile inspect` | Profile メタデータ表示 | PROF-01 |
| CLI-M02 | `sayane compile --target chatgpt` | JSON（`messages` 含む） | COMP-01 |
| CLI-M03 | `sayane compile --target claude` | JSON（Anthropic 形式） | COMP-02 |

**L2-CLI 必須（リリース時）**: `cli-acceptance-test.md` §2 の ✓ 項目すべて Pass。

### 4.3 Storage（STOR-M）

| ID | 手順 | 期待結果 |
|----|------|----------|
| STOR-M01 | `sayane storage backend status` | `filesystem` |
| STOR-M02 | `context/` に `.md` 追加 → `sayane storage index` | entries 件数増加、`storage index` メッセージ |

### 4.4 Candidate（CAND-M）

[Dogfood §3–5](dogfood-walkthrough.md) と同等。

| ID | 手順 | 期待結果 |
|----|------|----------|
| CAND-M01 | Bridge または CLI で capture → L1 evaluate → diff → approve | status `approved`、Profile に提案反映 |
| CAND-M02 | `Critical Distortion` candidate で approve（force なし） | 拒否（400 / CLI エラー） |
| CAND-M03 | `sayane candidate lineage --profile-id default` | approve イベントが記録 | 任意 |

### 4.5 Bridge HTTP（BRG-M）

Bridge 常駐: `sayane serve`

| ID | 手順 | 期待結果 |
|----|------|----------|
| BRG-M01 | `curl /health` | 200, `{"status":"ok"}` |
| BRG-M02 | token なし `GET /profiles` | 401 |
| BRG-M03 | Dogfood §3 の capture → evaluate → diff → approve | 一連成功 |

### 4.6 MCP（MCP-M）

| ID | 手順 | 期待結果 |
|----|------|----------|
| MCP-M01 | `sayane mcp list-profiles` / `inspect-profile default` | Profile 情報返却 |

### 4.7 Security（SEC-M）

| ID | 手順 | 期待結果 |
|----|------|----------|
| SEC-M01 | 誤 Bearer token で `/profiles` | 401 |
| SEC-M02 | capture 直後に Profile YAML を直接確認 | approve 前は提案セクションが merge されていない |

---

## 5. 自動受け入れ（L1 CI）シナリオ

CI（[ci.md](ci.md)）で毎回実行する pytest 集合。リリースタグ時は **main green** を必須とする。

### 5.1 実行コマンド

```bash
cd sayane
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ruff check src tests
pytest -q
```

### 5.2 必須テストモジュール（カテゴリ別）

| カテゴリ | モジュール | 受け入れ要件 |
|---------|-----------|-------------|
| Package | `test_package.py` | CORE 起動 |
| Schema | `test_schemas.py`, `test_confidentiality_policy_schema.py` | CORE-01, OSS-01/02 |
| Models / Builder | `test_models.py`, `test_builder.py` | CORE-02 |
| Adapters | `test_adapters.py` | CORE-03/04 |
| CLI | `test_cli.py`, `test_cli_help.py`, `test_candidate_cli.py`, `test_acceptance_cli.py`, `test_storage_cli.py`, `test_mcp_cli.py` | CLI-01〜09 |
| Storage | `test_storage_backend.py`, `test_context_index.py`, `test_storage_git.py`, `test_obsidian.py` | STOR-01〜07 |
| Candidate / RDE | `test_candidate_flow.py`, `test_critical_merge.py`, `test_rde.py`, `test_rde_merge.py` | CAND-01〜07 |
| Bridge | `test_bridge_api.py` | BRG-01〜07 |
| MCP | `test_mcp_operations.py`, `test_acceptance_cli.py` | MCP-01〜04 |
| Acceptance registry | `test_acceptance_coverage.py` | #92 シナリオ ID 紐づけ |
| i18n | `test_cli_i18n.py`, `test_cli_locale_resolve.py`, `test_acceptance_cli.py` | CLI-08 |

### 5.3 Skip 許容

- LLM judge 未設定環境での Level 2 関連（該当 test が skip する場合）
- 外部 vault パス未設定の Obsidian 統合 test

---

## 6. Extension 受け入れ（L3）

Chrome Extension のシナリオ・合否判定は **[extension-acceptance-test.md](extension-acceptance-test.md)** を正とする。

| 変更種別 | 最低限再実施 |
|---------|-------------|
| Bridge API 破壊的変更 | L2 BRG-M03 + L3 必須項目 |
| Extension のみ | L3 記載のリグレッション表 |
| Core Candidate / diff 変更 | L2 CAND-M01 + L3 CND-* |

---

## 7. クロスリポジトリ契約（sayane-pro）

OSS 契約は sayane 側で定義し、Commercial Edition は **同一 IF** で検証する。

| 契約 | OSS 定義 | pro 側検証 |
|------|---------|-----------|
| Storage backend entry point | [storage-backend.md](storage-backend.md) | `test_oss_contract.py::test_encrypted_sqlite_entry_point_registered` |
| Factory シグネチャ | 同上 | `test_oss_contract.py::test_storage_factory_signature_matches_oss_contract` |
| StorageBundle 型 | `src/sayane/storage/base.py` | `test_oss_contract.py::test_factory_return_type_is_storage_bundle` |
| Confidentiality schema | [confidentiality-policy-schema.md](confidentiality-policy-schema.md) | `test_oss_contract.py::test_*_policy_schema` |

**sayane リリース時**: storage / schema の破壊的変更がある場合、sayane-pro CI の `test_oss_contract` が green であることを確認する（minor bump 連携）。

---

## 8. 合否判定とリリースサインオフ

### 8.1 必須 Pass（Community リリース）

| 層 | 条件 |
|----|------|
| L1 | `pytest` 全 pass（意図的 skip のみ） |
| L2 | §4.0 の **✓ 項目すべて P**（CLI 詳細は [cli-acceptance-test.md](cli-acceptance-test.md) §2 も Pass） |
| L3 | Extension 変更がある PR / タグでは [extension-acceptance-test.md §10](extension-acceptance-test.md) Pass |

### 8.2 Fail 時

1. Issue 起票（再現手順・ログ・`sayane --version`）
2. 修正 PR（テスト追加を含む — [development-principles.md §6](development-principles.md)）
3. 該当シナリオ再実施

### 8.3 サインオフ記録

| 項目 | 記入 |
|------|------|
| リリース tag | |
| sayane version | |
| pytest 結果 | passed / skipped |
| L2 実施日 | |
| L3 実施日（該当時） | |
| 判定 | ☐ Pass / ☐ Fail |

---

## 9. 既知の許容事項

| 現象 | 判定 |
|------|------|
| diff の `add` が空（`already_present` のみ） | **Pass** — Profile に既存概念あり |
| Level 2 judge 未設定 | CAND-M / CND-L2 は **Skip** |
| ChatGPT / Claude DOM 変更 | Extension L3 **Fail**（adapter / sites 更新） |
| sayane-pro 未インストール | Commercial 機能不可は **Pass**（Community 仕様） |

---

## 10. 関連ドキュメント

- [開発原則 §7 テスト方針](development-principles.md)
- [Storage backend 契約](storage-backend.md)
- [Confidentiality Policy 契約](confidentiality-policy-schema.md)
- [Security Design](security.md)
- [CLI マニュアル](cli-manual.md)
- [Bridge マニュアル](bridge-manual.md)
- [MCP マニュアル](mcp-manual.md)
- [評価マニュアル](evaluation-manual.md)
- [CI 方針](ci.md)

---

## 11. 変更履歴

| 日付 | 版 | 内容 |
|------|-----|------|
| 2026-05-24 | 0.6.0 | 初版 — OSS Community 受け入れ仕様・L1/L2/L3 三層・契約対応表・cli-acceptance-test リンク |
