# CI 方針

## 目的

Phase 0 では、以降の Phase で破壊しやすい基盤（Python パッケージ、JSON Schema、Extension スケルトン）を継続的に検証する最小 CI を整える。

L1 自動受け入れの要件対応は [acceptance-spec.md §5](acceptance-spec.md) を参照する。T-RDE 横断意味監査の方針は [trde-acceptance-audit.md](trde-acceptance-audit.md) を参照する。

CI は「動作するか」だけでなく、意味監査の最低限の構造も検証する。特に T-RDE では、未承認の意味変形・意味逸脱・高リスク暗黙補完が検出された場合、UI や JSON 出力が成功していても品質ゲートを通過させない。

## ワークフロー

`.github/workflows/ci.yml` で以下を実行する。

### Python job

| ステップ | 内容 |
|---------|------|
| install | `pip install -e ".[dev]"` |
| ruff check | `src/`, `tests/` の lint |
| ruff format --check | フォーマット逸脱検出 |
| pytest | パッケージ import、schema、CLI、Bridge、RDE、T-RDE を検証 |

### Extension job

| ステップ | 内容 |
|---------|------|
| npm ci | `extension/` の依存関係固定インストール |
| typecheck | `tsc --noEmit` |
| build | `tsc` で `dist/` 生成 |

### Real DOM E2E job

Real DOM E2E は通常 PR の必須ゲートではない。`workflow_dispatch` / scheduled / release前 acceptance run で実施する。

| ステップ | 内容 |
|---------|------|
| build extension | Extension を unpacked extension として読み込める状態にする |
| mock bridge | E2E用 mock Bridge を起動する |
| real DOM insert | ChatGPT / Claude 等の実DOMに marker を挿入する |
| diagnostics | selector report / screenshot / sanitized DOM snapshot を保存する |

Real DOM E2E が成功しても、T-RDE が意味逸脱を検出した場合は総合 Pass にしてはならない。

## ローカル実行

```bash
pip install -e ".[dev]"
ruff check src tests
ruff format --check src tests
pytest -v
```

T-RDE の最小確認:

```bash
pytest -q tests/test_trde_runner.py
```

```bash
cd extension
npm install
npm run typecheck
npm run build
```

Real DOM E2E（任意・ログイン済みprofileが必要）:

```bash
export SAYANE_DIR="$HOME/.sayane"
cd extension
npm run test:e2e:real:chatgpt
npm run test:e2e:real:claude
```

## テスト計画

| 層 | 対象 | 自動化 | 主な証拠 |
|----|------|--------|----------|
| L1 | Core / CLI / Bridge / MCP / Storage | 必須 | `pytest -q` |
| L1-RDE | Candidate RDE / critical gate | 必須 | `test_rde.py`, `test_critical_merge.py`, `test_rde_merge.py` |
| L1-T-RDE | SemanticMap / DeltaM / quality gate | 必須 | `test_trde_runner.py` |
| L2 | CLI / Bridge / MCP / Storage 手動UAT | リリース前 | `cli-acceptance-test.md`, `acceptance-spec.md` |
| L3 | Extension popup / DOM / Bridge 結合 | Extension変更時 | `extension-acceptance-test.md` |
| Real DOM E2E | ChatGPT / Claude 実DOM | 任意・scheduled | `extension-real-dom-e2e.yml` artifacts |
| T-RDE | Raw / Edited / Normalize / Interpret / Export / Live 横断意味監査 | リリース前・Prompt/Adapter/Extension変更時必須 | `trde-acceptance-audit.md` 記録 |

## T-RDE 自動テスト計画

### 実装済み

| テスト | 目的 |
|--------|------|
| `test_trde_detects_unintended_deviation_and_high_risk_implicit` | 未承認の意味逸脱と高リスク暗黙補完で品質ゲートが落ちること |
| `test_trde_passes_when_sayane_design_principles_are_preserved` | Sayaneの中核設計意図が保存されている場合にPassすること |
| `test_trde_quality_gate_thresholds_are_configurable` | 閾値を緩めても実際の意味逸脱は隠せないこと |

### 追加予定

| テスト | 目的 |
|--------|------|
| `test_trde_raw_edited.py` | Raw→Edited の主張強化・制約削除を検出 |
| `test_trde_normalize_interpret.py` | Normalize / Interpret での暗黙補完・推論混入を検出 |
| `test_trde_export_live.py` | Adapter / Extension 挿入で意味制約が欠落しないこと |
| `test_trde_provider_model_split.py` | provider / target / model の混同を検出 |
| `test_trde_lineage_evidence.py` | ΔM と lineage / evidence の接続を検証 |

## Phase 別の拡張予定

| Phase | CI 追加 |
|-------|---------|
| Phase 1 | Adapter / CLI の regression fixtures、coverage 任意 |
| Phase 2 | Bridge contract test、security test |
| Phase 2.5 | MCP server smoke test |
| Phase 3 | Extension site-adapter の分離テスト方針 |
| Phase 4 | RDE diff regression fixtures |
| Phase 4.5 | T-RDE semantic map / quality gate / golden fixtures |
| Phase 5 | Prompt adaptation fixtures（targets / models / providers） |
| Phase 6 | Real DOM E2E scheduled monitoring |

## 原則

- main への直接 push は想定しない（[開発原則](development-principles.md) の Branch first）
- Core 変更は PR でテスト必須
- secret や実 Profile を CI に含めない。fixtures は `examples/` または `tests/fixtures/` の匿名サンプルのみ
- `e2e/user-data/` は browser/session state であり、canonical prompt source にしない
- UI 成功・HTTP 200・JSON 出力だけを T-RDE Pass の根拠にしない
