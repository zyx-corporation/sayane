# Rust 境界設計（Phase 6）

Python Core と Commercial Edition（Rust engine）の **境界・移行基準・互換テスト** を定義する。実装本体は [sayane-pro](https://github.com/zyx-corporation/sayane-pro) に置き、OSS は **契約と安定 API** を維持する。

Parent Epic: [#8](https://github.com/zyx-corporation/sayane/issues/8)

## 1. 目的

| 目的 | 内容 |
|------|------|
| **安定 API** | CLI / Bridge / MCP / Storage 抽象の Python 表面を Rust 化後も維持 |
| **段階移行** | ボトルネックが計測されたコンポーネントのみ Rust へ抽出 |
| **契約テスト** | OSS fixture と pro 実装の **同一入出力** を CI で検証 |
| **local-first** | Rust モジュールもオフライン・ローカル完結（ネットワーク不要） |

## 2. レイヤと移行候補

```text
┌─────────────────────────────────────────────────────────┐
│  CLI / Bridge / MCP / Extension (Python + TypeScript)   │
├─────────────────────────────────────────────────────────┤
│  Core Library (Python) — Profile, IR, RDE, Adapters     │
├─────────────────────────────────────────────────────────┤
│  Storage / License / Confidentiality (Python 抽象)       │
├─────────────────────────────────────────────────────────┤
│  Commercial plugins (sayane-pro)                         │
│    · License verification (Python, #2)                   │
│    · Confidentiality audit L1 (Python, #7)               │
│    · encrypted-sqlite backend (Rust, #3)                 │
│    · semantic diff / vault indexer (Rust, 拡張)          │
└─────────────────────────────────────────────────────────┘
```

### 2.1 Rust 化の優先順位

| 順 | コンポーネント | 理由 | 状態 |
|----|---------------|------|------|
| 1 | encrypted SQLite storage engine | 暗号化・CRUD・性能 | sayane-pro #3 |
| 2 | markdown vault indexer（大規模） | I/O + 索引がボトルネック | 拡張 |
| 3 | semantic diff engine | CPU 集約 | 拡張 |
| 4 | local daemon（Bridge 常駐） | プロセス寿命・Rust 同梱 | 拡張 |

**Rust 化しない（Python 維持）**: Profile model、Prompt IR builder、Adapter、RDE ヒューリスティック、Bridge HTTP 契約、MCP read-only tools。

## 3. インターフェース方式

### 3.1 採用: PyO3 拡張 + Storage entry point

| 方式 | 採用 | 用途 |
|------|------|------|
| **PyO3 / maturin** | ✓ 第一選択 | encrypted-sqlite backend、将来 diff/indexer |
| **JSON Schema + pytest 契約** | ✓ | Confidentiality Policy、Storage bundle 振る舞い |
| **CLI entry point** (`sayane.cli_extensions`) | ✓ | license / confidentiality CLI |
| **Hook registry** (`sayane.hooks`) | ✓ | approve 前ゲート等 |
| subprocess / FFI 直叩き | ✗ | デプロイ・エラー処理が複雑 |
| gRPC localhost | 将来検討 | daemon 常駐化時のみ |

Storage backend は既存の [`sayane.storage_backends`](storage-backend.md) entry point に Rust 実装を登録する:

```toml
[project.entry-points."sayane.storage_backends"]
encrypted-sqlite = "sayane_pro.storage:create_backend"
```

Python 側は `open_storage()` の戻り `StorageBundle`（Profile / Context / Lineage 3 リポジトリ）のみに依存する。

### 3.2 Rust crate 境界

```text
sayane-pro/crates/
  sayane-storage/     # SQLite + 暗号化、Profile/Context CRUD
  sayane-index/         # （将来）vault indexer
  sayane-diff/          # （将来）semantic diff
python/src/sayane_pro/  # PyO3 ラッパー、license、confidentiality
```

Rust → Python 境界では **Pydantic / dataclass 相当の plain dict** または **JSON 文字列** を渡し、Profile オブジェクトを Rust 内部に再定義しない（スキーマ drift を防ぐ）。

## 4. 移行基準（Python → Rust）

次の **すべて** を満たす場合に Rust 抽出を検討する。

1. **仕様固定** — JSON Schema または pytest 契約テストが OSS に存在
2. **ボトルネック計測** — プロファイルサイズ / vault ファイル数 / 操作レイテンシの baseline あり（§6）
3. **Python 参照実装** — 同一 fixture で pass する実装が Python または pro mock に存在
4. **API 不変** — `StorageBundle` / CLI / Bridge エンドポイントのシグネチャ変更なし
5. **フォールバック** — Community `filesystem` backend は継続メンテ

移行 **非推奨**: RDE 分類、LLM judge、Adapter compile（LLM 非依存だが変更頻度が高い）。

## 5. Fixture 設計

### 5.1 配置

```text
sayane/tests/fixtures/rust_contract/     # OSS 公開 fixture（匿名化）
sayane-pro/tests/fixtures/rust_contract/ # pro 専用（暗号化 DB バイナリ等）
```

### 5.2 カテゴリ

| カテゴリ | 内容 | 検証 |
|---------|------|------|
| **profile_roundtrip** | minimal + rich Profile YAML | load → save バイト一致 or 正規化一致 |
| **context_crud** | 複数 Markdown + context_index | write/list/read/delete |
| **lineage_append** | jsonl イベント列 | append 順序・フィールド |
| **migrate_import** | filesystem スナップショット → DB | 件数・checksum |
| **confidentiality_scan** | policy + 違反サンプル text | violation 件数・rule_id |

Fixture は **PII なし・合成データ** とし、リポジトリにコミット可能なサイズ（単一 DB < 1 MiB）に抑える。

### 5.3 バージョニング

```text
fixtures/rust_contract/v1/...
```

破壊的変更時は `v2` を追加し、pro は `v1` と `v2` 両方を CI で通す移行期間を設ける。

## 6. 性能 baseline 計画

初回 baseline は **filesystem backend（Python）** で計測し、Rust 化後に同一 benchmark を再実行する。

| シナリオ | 入力規模 | 計測指標 | 目標（Rust 化後） |
|---------|---------|---------|------------------|
| Profile load/save | 1 profile, 50 context files | p50/p95 ms | ≥ 2× 改善 |
| context_index 再生成 | 200 markdown files | wall time | ≥ 3× 改善 |
| vault import | 500 files / 50 MiB | wall time | ≥ 2× 改善 |
| encrypted DB open + list | 1 store.db 10 MiB | cold open ms | < 500 ms |

計測スクリプト: `scripts/bench_storage.py`（将来追加）。結果は `docs/benchmarks/` に CSV コミット（任意）。

## 7. 互換テスト仕様

### 7.1 OSS CI（sayane）

- 既存 `pytest` 97+ tests — **常に pass**
- `tests/test_storage_backend.py` — mock backend 契約
- `tests/test_confidentiality_policy_schema.py` — policy schema
- `tests/test_cli_plugins.py` — entry point 読み込み（hook 未インストール時 no-op）

### 7.2 pro CI（sayane-pro）

- editable install `sayane` + `sayane-pro`
- `tests/test_license.py` — 署名・期限・改ざん
- `tests/test_confidentiality.py` — scan / gate / audit
- `tests/test_rust_contract.py` — fixture 入出力（Rust 実装追加後）

### 7.3 クロスリポジトリ

pro PR は **sayane の main 最新** に対する matrix を推奨。Storage / schema 破壊変更時は sayane 側で minor bump。

## 8. エラーハンドリング

| 層 | 方針 |
|----|------|
| Rust | `Result<T, StorageError>` → PyO3 で Python `StorageBackendError` に変換 |
| License | 無効時 `LicenseError` → CLI exit 1、Bridge 503 |
| Python API | 公開関数は typed exception のみ。裸の `Exception` を漏らさない |

## 9. セキュリティ境界

- Rust crate は **ネットワークを開かない**（ライセンス検証含む）
- 暗号鍵は OS キーチェーン連携またはユーザー派生鍵（詳細 sayane-pro storage.md）
- 監査 excerpt は redaction 必須（[security.md](security.md)）

## 10. 非目標

- 全 Core の Rust 書き換え
- ABI 安定の C FFI 公開
- クラウドライセンスサーバー必須化

## 11. 関連

- [Storage backend 契約](storage-backend.md)
- [Confidentiality Policy スキーマ](confidentiality-policy-schema.md)
- [商用版設計（sayane-pro）](https://github.com/zyx-corporation/sayane-pro/blob/main/docs/commercial-edition.md)
- Issue [#28](https://github.com/zyx-corporation/sayane/issues/28) / [#8](https://github.com/zyx-corporation/sayane/issues/8)
