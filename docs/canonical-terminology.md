# 正規語彙（Canonical Terminology）

## 1. 概要

正規語彙は、ユーザーまたはプロジェクトが定義する略語・旧称・展開形の対応表である。Sayane Core は特定の理論用語（例: 個人プロジェクト固有の略語）をハードコードしない。すべての正規化ルールは `SayaneProfile` または `sayane.project.yaml`（`SayaneProjectProfile`）の `canonical_terms` にのみ存在する。

Adapter 層は、Prompt IR に解決済みの `canonical_terms` を受け取り、各 LLM 向けの出力形式へ整形する。置換・警告・エクスポートブロックの判定は Core（`canonical_terms.py`）で行い、Adapter は結果を反映する。

## 2. データモデル

### 2.1 `CanonicalTerm`（Profile / Project）

| フィールド | 説明 |
|-----------|------|
| `term` | 正規の短い表記（例: `ABC`） |
| `expansion` | 展開形（例: `Approved Base Concept`） |
| `description` | 任意の説明 |
| `deprecated` | 置換・警告・ブロック対象の旧表記リスト |
| `correction_policy` | 下記いずれか |

### 2.2 `correction_policy`

| 値 | 動作 |
|----|------|
| `replace_deprecated_with_canonical` | `deprecated` 文字列を `expansion` に置換 |
| `warn_and_preserve_context` | 本文は変更せず `export_notes` に警告 |
| `block_export` | エクスポートをブロックし、Adapter 出力に `requires_user_confirmation: true` |

### 2.3 マージ優先度

同一 `term`（大文字小文字無視）について、**プロジェクト Profile がユーザ Profile を上書き**する（`merge_canonical_terms`）。

### 2.4 Prompt IR への付与

`build_prompt_ir` は Profile から用語をマージし、`CanonicalTermRef` として `PromptIR.canonical_terms` に載せる。本文への適用と `export_notes` / `export_blocked` は `attach_canonical_terms_to_ir`（または Builder 内の同等処理）で行う。

## 3. Adapter との責務分離

```text
SayaneProfile / SayaneProjectProfile
  → merge_canonical_terms
  → build_prompt_ir (+ attach)
  → PromptIR (canonical_terms, export_notes, export_blocked)
  → Adapter.compile
  → LLM 向け payload
```

- **ChatGPT / Claude**: システムプロンプト末尾に「正規語彙」セクションを付与（`ir.canonical_terms` がある場合）。
- **Gemini**: `format: gemini_working_memo` — 単一 `payload.text`（Claude 風の system/user 分割を避ける）。
- **DeepSeek**: `format: deepseek_working_memo` — 同上。正規語彙セクションでは `deprecated` の値を列挙しない（旧称の再掲載を避ける）。

`export_blocked` が真のとき、禁止句は payload 本文から除去し、`requires_user_confirmation: true` を付与する。

## 4. テスト方針（中立フィクスチャ）

Core・Adapter の自動テストでは、**特定ユーザー・理論に依存しない中立フィクスチャ**を用いる。テスト内で固定の理論略語を Core に埋め込まない。

### 4.1 標準フィクスチャ

| 記号 | 展開形（ユーザ Profile） | 用途 |
|------|-------------------------|------|
| `ABC` | `Approved Base Concept` | 置換ポリシー・Adapter 出力 |
| `XYZ` | `Cross Yield Zone` | 警告のみポリシー |
| （プロジェクト上書き） | `Architecture Boundary Contract` | マージ優先度 |
| `Alternative Broken Concept` | （deprecated） | 置換対象の旧表記 |
| `legacy-xyz` | （deprecated） | 警告のみの旧表記 |
| `forbidden phrase` | （deprecated, `block_export`） | エクスポートブロック |

### 4.2 受け入れ観点（`tests/test_canonical_terms.py`）

1. プロジェクト Profile の `ABC.expansion` がユーザ Profile より優先される。
2. `replace_deprecated_with_canonical` で旧表記が展開形に置換される。
3. `canonical_terms` 未設定の Profile では略語が勝手に展開されない。
4. DeepSeek 出力に正規語彙セクションと `export_notes` が含まれる。
5. Gemini と DeepSeek で `format` がそれぞれ `gemini_working_memo` / `deepseek_working_memo` である。
6. 置換時に `export_notes` に記録が残る。
7. `warn_and_preserve_context` では本文を保持し警告のみ。
8. `block_export` では `requires_user_confirmation` が真となり、禁止句が payload に漏れない。

関連: `tests/test_adapters.py`（各 target の基本 compile）、`tests/test_builder.py`（IR 構築）。

### 4.3 ドキュメント・サンプルとの関係

- マーケティング記事や Dogfood 手順では、実ユーザーの用語例（RDE 等）を**例示**として載せてよい。
- **仕様・受け入れ・単体テストの正**は本書および上記中立フィクスチャとする。
- `examples/profiles/*.yaml` の `knowledge.concepts` は説明用であり、Core の正規語彙ロジックとは無関係である。

## 5. 設定例

ユーザ Profile（抜粋）:

```yaml
canonical_terms:
  - term: "ABC"
    expansion: "Approved Base Concept"
    deprecated:
      - "Alternative Broken Concept"
    correction_policy: replace_deprecated_with_canonical
```

プロジェクト `sayane.project.yaml`（抜粋）:

```yaml
version: "0.1.0"
kind: "SayaneProjectProfile"
canonical_terms:
  - term: "ABC"
    expansion: "Architecture Boundary Contract"
    deprecated:
      - "Alternative Broken Concept"
```

## 6. 関連ドキュメント

- [Sayane Profile と Prompt IR](profile-ir.md)
- [開発原則 — テスト方針](development-principles.md#7-テスト方針)
- [OSS 版受け入れテスト仕様](acceptance-spec.md) — CORE-05
