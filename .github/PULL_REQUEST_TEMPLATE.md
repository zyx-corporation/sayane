# Pull Request

## 関連Issue

Closes #

## 概要

このPRで変更した内容を簡潔に書く。

## 変更種別

- [ ] feature
- [ ] bug fix
- [ ] docs / design
- [ ] refactor
- [ ] test
- [ ] security / privacy
- [ ] chore

## 対象範囲

- [ ] Core
- [ ] CLI
- [ ] Local Bridge
- [ ] MCP Server
- [ ] Chrome Extension
- [ ] Adapter
- [ ] Strategy
- [ ] Evaluator
- [ ] Storage
- [ ] Documentation
- [ ] CI / tooling

## Branch first 確認

- [ ] mainへ直接pushしていない
- [ ] Issueに対応したbranchで作業している
- [ ] branch名が目的を表している

Branch:

```text
feature/<issue-number>-<short-name>
fix/<issue-number>-<short-name>
docs/<issue-number>-<short-name>
refactor/<issue-number>-<short-name>
test/<issue-number>-<short-name>
```

## TDD / test first 確認

- [ ] 先に失敗するテストを書いた、または既存テストで再現した
- [ ] 最小実装でテストを通した
- [ ] refactor後もテストが通る
- [ ] テスト追加が不要な場合、その理由を下に記載した

テスト不要の理由:

```text

```

## 実行したテスト

```bash
# 実行したコマンドを書く
```

## RDEレビュー

### 保存された要素

元Issue、既存設計、既存挙動のうち、保存されたものを書く。

### 許可された変換

このPRで許可された仕様・実装・文書上の変換を書く。

### 推論による補完

既存文書やIssueから推論して補完した内容があれば書く。

### 未解決の要素

このPRでは解決しない問題を書く。

### 逸脱リスク

以下を確認する。

- [ ] 元Issueより強い主張になっていない
- [ ] 未検証内容を実証済みとして扱っていない
- [ ] 実装上の便宜を設計思想として正当化していない
- [ ] Profile / Prompt IR / Lineage の意味を意図せず変えていない
- [ ] 同一人格の完全再現を示唆していない
- [ ] 自動mergeや自動Profile更新を導入していない、または明示承認を維持している

補足:

```text

```

## デザインパターン確認

このPRで利用・追加・維持したパターンを選ぶ。

- [ ] Adapter
- [ ] Strategy
- [ ] Builder
- [ ] Factory
- [ ] Decorator
- [ ] Observer
- [ ] Repository
- [ ] なし
- [ ] Other: 

設計上の補足:

```text

```

## Security / Privacy確認

- [ ] secret、token、API key、private keyを含めていない
- [ ] ログやテストfixtureに機微情報を含めていない
- [ ] Local Bridge / MCP Server の認証境界を弱めていない
- [ ] CORS / Origin / pairing token / read-only mode に悪影響がない
- [ ] Candidate Updateが承認なしにProfileへmergeされない
- [ ] Profile、values、policy、identityを危険に上書きしない
- [ ] 該当なし

## 互換性影響

- [ ] 破壊的変更なし
- [ ] 破壊的変更あり
- [ ] schema変更あり
- [ ] CLI変更あり
- [ ] API変更あり
- [ ] docs更新済み

破壊的変更・schema変更の説明:

```text

```

## ドキュメント更新

- [ ] README.md
- [ ] README_ja.md
- [ ] docs/index.md
- [ ] docs/architecture.md
- [ ] docs/profile-ir.md
- [ ] docs/mvp-scope.md
- [ ] docs/security.md
- [ ] docs/mcp-integration.md
- [ ] docs/extraction-pipeline.md
- [ ] docs/evaluation-lineage.md
- [ ] docs/development-principles.md
- [ ] docs/roadmap.md
- [ ] 更新不要

## レビュアーへの注記

重点的に見てほしい点を書く。

```text

```
