# CI 方針

## 目的

Phase 0 では、以降の Phase で破壊しやすい基盤（Python パッケージ、JSON Schema、Extension スケルトン）を継続的に検証する最小 CI を整える。

現在は Phase 4 / Phase 6 前倒し方針により、Local Vault / storage security / MCP exposure boundary を CI で明示的に検証する。

L1 自動受け入れの要件対応は [acceptance-spec.md §5](acceptance-spec.md) を参照する。

## ワークフロー

`.github/workflows/ci.yml` で以下を実行する。

### Python job

| ステップ | 内容 |
|---------|------|
| install | `pip install -e ".[dev]"` |
| ruff check | `src/`, `tests/` の lint |
| ruff format --check | フォーマット逸脱検出 |
| ADR 0001 targeted checks | storage / security / MCP exposure の重点検証 |
| pytest | 全テスト |

ADR 0001 targeted checks は以下を実行する。

```bash
pytest -v tests/test_storage_backend.py
pytest -v tests/test_storage_security_policy.py
pytest -v tests/test_mcp_context.py
```

この targeted checks は、以下の退行を早期に検出するために置く。

- filesystem storage が implicit Git auto-commit を既定有効に戻すこと
- Candidate / ReviewDecision / Lineage の保存先境界が外部同期・Git・Obsidianへ拡散すること
- MCP context output が pending / rejected / deferred Candidate content を通常 context として露出すること
- Local Vault / unlock / key management 実装時に、ADR 0001 の方針と矛盾する変更が入ること

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
pytest -v tests/test_mcp_context.py
pytest -v
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
| Phase 6 | Local Vault key manager、platform keychain provider、unlock session、persistent store |

## 原則

- main への直接 push は想定しない（[開発原則](development-principles.md) の Branch first）
- Core 変更は PR でテスト必須
- secret や実 Profile を CI に含めない。fixtures は `examples/` の匿名サンプルのみ
- CI の test provider は production default にしてはならない
- plaintext local storage、implicit external sync、implicit Git auto-commit を production default に戻す変更は CI で検出可能にする
