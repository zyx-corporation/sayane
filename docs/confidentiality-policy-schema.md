# Confidentiality Policy スキーマ契約

Commercial Edition（[sayane-pro](https://github.com/zyx-corporation/sayane-pro)）の **機密データ基準・逸脱監査** 向け JSON Schema 契約。検出 engine と監査 store の実装は pro 側、スキーマとサンプルは OSS に公開する。

## スキーマ

- `schemas/sayane-confidentiality-policy.schema.json`
- サンプル: `examples/confidentiality/default.policy.yaml`

`kind: SayaneConfidentialityPolicy` を必須とする。

## 主要フィールド

| フィールド | 説明 |
|-----------|------|
| `classification_levels` | 機密区分（`id` 昇順 = 制限が強い） |
| `profile_ceiling` | Profile 全体の上限区分 |
| `section_limits` | identity / context 等セクション別の許容上限 |
| `rules` | 正規表現パターンと `reject` / `warn` / `audit_only` |
| `context_classifications` | context ファイル単位の declared 区分（任意） |
| `enforcement` | `enforce` / `warn_only` / `audit_only` |

## 配置（実行時）

```text
~/.sayane/confidentiality/default.policy.yaml
```

Profile 本文とは **別ファイル** で保持する（[confidentiality-audit.md（pro）](https://github.com/zyx-corporation/sayane-pro/blob/main/docs/confidentiality-audit.md)）。

## 検証

```bash
pytest tests/test_confidentiality_policy_schema.py -v
```

## 関連

- [Security Design](security.md)
- [Storage backend プラグイン契約](storage-backend.md)
- Issue: [#66](https://github.com/zyx-corporation/sayane/issues/66)
