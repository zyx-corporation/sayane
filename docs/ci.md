# CI 方針

## 目的

Phase 0 では、以降の Phase で破壊しやすい基盤（Python パッケージ、JSON Schema、Extension スケルトン）を継続的に検証する最小 CI を整える。

L1 自動受け入れの要件対応は [acceptance-spec.md §5](acceptance-spec.md) を参照する。

## ワークフロー

`.github/workflows/ci.yml` で以下を実行する。

### Python job

| ステップ | 内容 |
|---------|------|
| install | `pip install -e ".[dev]"` |
| ruff check | `src/`, `tests/` の lint |
| ruff format --check | フォーマット逸脱検出 |
| pytest | パッケージ import と schema 検証 |

### Extension job

| ステップ | 内容 |
|---------|------|
| npm ci | `extension/` の依存関係固定インストール |
| typecheck | `tsc --noEmit` |
| build | `tsc` で `dist/` 生成 |

## ローカル実行

```bash
pip install -e ".[dev]"
ruff check src tests
ruff format --check src tests
pytest -v
```

```bash
cd extension
npm install
npm run typecheck
npm run build
```

## Phase 別の拡張予定

| Phase | CI 追加 |
|-------|---------|
| Phase 1 | Adapter / CLI の regression fixtures、coverage 任意 |
| Phase 2 | Bridge contract test、security test |
| Phase 2.5 | MCP server smoke test |
| Phase 3 | Extension site-adapter の分離テスト方針 |
| Phase 4 | RDE diff regression fixtures |

## 原則

- main への直接 push は想定しない（[開発原則](development-principles.md) の Branch first）
- Core 変更は PR でテスト必須
- secret や実 Profile を CI に含めない。fixtures は `examples/` の匿名サンプルのみ
