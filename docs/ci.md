# CI 方針

## 目的

Phase 0 では、以降の Phase で破壊しやすい基盤（Python パッケージ、JSON Schema、Extension スケルトン）を継続的に検証する最小 CI を整える。

現在は Phase 4 / Phase 6 前倒し方針により、Local Vault / storage security / MCP exposure boundary を CI で明示的に検証する。

CI の上位方針は [ADR 0002: CI Governance and T-RDE Execution Surface](adr/0002-ci-governance-and-t-rde.md) に従う。CI は project-wide な T-RDE 実行面であり、Core CI は primary phase gate である。ただし CI pass は correctness certification ではなく、bounded evidence として扱う。

L1 自動受け入れの要件対応は [acceptance-spec.md §5](acceptance-spec.md) を参照する。

## ワークフロー

`.github/workflows/ci.yml` で以下を実行する。

### Python job

| ステップ | 内容 |
|---------|------|
| install | `pip install -e ".[dev]"` |
| ruff check | `src/`, `tests/` の lint |
| ruff format --check | フォーマット逸脱検出 |
| ADR 0001 targeted checks | storage / security / vault / MCP exposure の重点検証 |
| pytest | 全テスト |

ADR 0001 targeted checks は以下を実行する。

```bash
pytest -v tests/test_storage_backend.py
pytest -v tests/test_storage_security_policy.py
pytest -v tests/test_storage_write_policy.py
pytest -v tests/test_review_decision_store.py
pytest -v tests/test_vault_contracts.py
pytest -v tests/test_unlock_policy.py
pytest -v tests/test_unlock_session_manager.py
pytest -v tests/test_vault_test_store.py
pytest -v tests/test_vault_test_crypto.py
pytest -v tests/test_vault_candidate_adapter.py
pytest -v tests/test_vault_review_decision_adapter.py
pytest -v tests/test_vault_lineage_adapter.py
pytest -v tests/test_vault_repository_bundle.py
pytest -v tests/test_vault_factory.py
pytest -v tests/test_vault_cli.py
pytest -v tests/test_sqlite_vault_schema.py
pytest -v tests/test_mcp_context.py
```

この targeted checks は、以下の退行を早期に検出するために置く。

- filesystem storage が implicit Git auto-commit を既定有効に戻すこと
- Candidate / ReviewDecision / Lineage の保存先境界が外部同期・Git・Obsidianへ拡散すること
- Candidate / ReviewDecision / Lineage が Vault adapter 境界を失うこと
- unlock policy preset が ADR 0001 の normal / sensitive / deep_private の意味から逸脱すること
- SQLite Local Vault schema から `keyring` / `encrypted_records` / `audit_metadata` 契約が失われること
- SQLite Local Vault schema に `plaintext` / `master_key` / `unwrapped_dek` などの禁止カラムが入ること
- `sayane vault schema --database` が既存 SQLite DB の schema metadata validation で禁止カラムを検出できないこと
- test-only vault provider / runtime が production default として開くこと
- `sayane vault status` が明示 `--test` なしに test-only runtime を開くこと
- `sayane vault policy` が unlock policy preset と異なる値を表示すること
- `sayane vault schema` が SQLite schema contract と異なる値を表示すること
- MCP context output が pending / rejected / deferred Candidate content を通常 context として露出すること
- Local Vault / unlock / key management 実装時に、ADR 0001 の方針と矛盾する変更が入ること

### Local Vault diagnostics

`vault status` は production Local Vault の readiness を確認するための非破壊診断入口である。

```bash
sayane vault status
sayane vault status --json
```

production backend が未実装の間は unavailable を返す。これは失敗ではなく fail-closed な期待動作である。

明示的な test-only runtime 診断は以下で行う。

```bash
sayane vault status --test
sayane vault status --test --json
```

`--test` の出力は `production_ready: false` と `test_only: true` を含む必要がある。

`vault policy` は unlock policy preset を確認するための非破壊診断入口である。Vault runtime を開かず、plaintext record にも触れない。

```bash
sayane vault policy
sayane vault policy --json
sayane vault policy --level normal --json
sayane vault policy --level sensitive --json
sayane vault policy --level deep_private --json
```

`normal` / `sensitive` / `deep_private` の timeout と scope は ADR 0001 と一致していなければならない。

`vault schema` は SQLite Local Vault schema contract を確認するための非破壊診断入口である。既定では Vault runtime も database も開かない。

```bash
sayane vault schema
sayane vault schema --json
sayane vault schema --ddl
sayane vault schema --ddl --json
```

既存 SQLite ファイルの schema metadata validation は以下で行う。これは SQLite metadata のみを読み、record rows を読み出さない。

```bash
sayane vault schema --database path/to/vault.sqlite
sayane vault schema --database path/to/vault.sqlite --json
```

validation が fail の場合は exit code 1 を返す。

`vault schema` は `keyring` / `encrypted_records` / `audit_metadata`、`wrapped_dek` / `ciphertext` / `aad_json`、および `plaintext` / `master_key` / `unwrapped_dek` などの禁止カラムを ADR 0001 と一致して表示しなければならない。

### Extension job

| ステップ | 内容 |
|---------|------|
| npm ci | `extension/` の依存関係固定インストール |
| typecheck | `tsc --noEmit` |
| build | `tsc` で `dist/` 生成 |

Chrome Extension は freeze / deprecated 方針であり、新機能追加対象ではない。この job は移行期間中の破損検知として残す。App clipboard capture が primary path になり、Extension が release artifact / primary docs から外れた後、この job は削除または archive 用 workflow へ移す。

## ローカル実行

```bash
pip install -e ".[dev]"
ruff check src tests
ruff format --check src tests
pytest -v tests/test_storage_backend.py
pytest -v tests/test_storage_security_policy.py
pytest -v tests/test_storage_write_policy.py
pytest -v tests/test_review_decision_store.py
pytest -v tests/test_vault_contracts.py
pytest -v tests/test_unlock_policy.py
pytest -v tests/test_unlock_session_manager.py
pytest -v tests/test_vault_test_store.py
pytest -v tests/test_vault_test_crypto.py
pytest -v tests/test_vault_candidate_adapter.py
pytest -v tests/test_vault_review_decision_adapter.py
pytest -v tests/test_vault_lineage_adapter.py
pytest -v tests/test_vault_repository_bundle.py
pytest -v tests/test_vault_factory.py
pytest -v tests/test_vault_cli.py
pytest -v tests/test_sqlite_vault_schema.py
pytest -v tests/test_mcp_context.py
pytest -v
```

```bash
sayane vault status --json
sayane vault status --test --json
sayane vault policy --json
sayane vault policy --level sensitive --json
sayane vault schema --json
sayane vault schema --ddl --json
sayane vault schema --database path/to/vault.sqlite --json
```

```bash
cd extension
npm install
npm run typecheck
npm run build
```

### Extension E2E（Playwright, #91）

```bash
pip install -e ".[dev]"   # sayane ルート
cd extension
npm ci && npm run build
npm run test:e2e:install
npm run test:e2e
```

詳細: [extension-e2e.md](extension-e2e.md)。CI ワークフロー: `.github/workflows/extension-e2e.yml`（週次 + PR path filter）。

Extension freeze 後、E2E は release artifact から Extension を外す段階で archive / remove を再評価する。

## Phase 別の拡張予定

| Phase | CI 追加 |
|-------|---------|
| Phase 1 | Adapter / CLI の regression fixtures、coverage 任意 |
| Phase 2 | Bridge contract test、security test |
| Phase 2.5 | MCP server smoke test、MCP Context Exposure Policy |
| Phase 3 | Extension freeze regression、App clipboard capture smoke test |
| Phase 4 | FileSystem storage security policy、external storage hold |
| Phase 5 | RDE diff regression fixtures、Candidate / ReviewDecision / Lineage local working store checks |
| Phase 6 | Local Vault key manager、platform keychain provider、unlock policy、unlock session、SQLite schema、persistent store、vault diagnostics |

## Issue close 時の記録

Issue close 前には、ADR 0002 に従い、少なくとも以下を記録する。

- 関連 commit
- Core CI / targeted checks の結果
- Observation E2E の該当有無と結果
- warning 分類（blocking / tracked separately / informational）
- 残課題または follow-up issue

## 原則

- main への直接 push は想定しない（[開発原則](development-principles.md) の Branch first）
- Core 変更は PR でテスト必須
- secret や実 Profile を CI に含めない。fixtures は `examples/` の匿名サンプルのみ
- CI の test provider は production default にしてはならない
- plaintext local storage、implicit external sync、implicit Git auto-commit を production default に戻す変更は CI で検出可能にする
- SQLite Local Vault schema は `wrapped_dek` / `ciphertext` / `aad_json` を持つ契約であり、`plaintext` / `master_key` / `unwrapped_dek` を含んではならない
- `sayane vault schema --database` は schema metadata のみを検査し、record rows を読んではならない
- `sayane vault status` は production 未実装時に fail-closed を示す診断であり、`--test` なしに test-only runtime を開いてはならない
- `sayane vault policy` は runtime を開かずに policy preset を表示する診断であり、normal / sensitive / deep_private の scope と timeout は ADR 0001 と一致しなければならない
- `sayane vault schema` は runtime / database を開かずに schema contract を表示する診断であり、SQLite schema の必須テーブル・必須カラム・禁止カラムは ADR 0001 と一致しなければならない
- CI workflow 変更は architecture governance として扱う
- CI pass は correctness certification ではなく bounded evidence として扱う
