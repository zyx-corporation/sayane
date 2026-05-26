# Sayane 開発原則

## 1. 基本方針

Sayane の開発は、RDE原則、Issue first、Branch first、TDD/test first、デザインパターン重視を基本とする。

Sayane は、人格的文脈・価値観・応答様式・方針を扱うため、通常のアプリケーション以上に「意味変化」を慎重に扱う必要がある。実装上の都合によって、設計思想やユーザーの人格的文脈が意図せず変形されてはならない。

そのため、すべての変更は以下の観点で扱う。

```text
変更は機能追加ではなく、意味変化である。
意味変化は記録され、評価され、必要に応じて差し戻せなければならない。
```

## 2. RDE原則

RDEは、生成物・実装・仕様変更における意味変化を評価する原則である。

Sayane 開発では、各Issue、Pull Request、設計変更において、可能な範囲で以下を確認する。

```text
Preserved: 保存された要素
Authorized Transformation: 許可された変換
Inferred Extension: 推論による補完
Unresolved Gap: 未解決の要素
Suspicious Drift: 逸脱リスク
Critical Distortion: 重大な歪曲
```

## 3. RDEレビュー観点

Pull Requestでは、少なくとも以下を確認する。

- 元Issueの意図が保存されているか
- 実装が元の設計思想より強い主張になっていないか
- 未検証内容を実証済みとして扱っていないか
- 実装上の便宜が理論的主張へすり替わっていないか
- Profile / Prompt IR / Lineage の意味が意図せず変化していないか
- セキュリティやprivacy上の前提が弱まっていないか
- ユーザー承認なしに人格的文脈をmergeする経路が生じていないか

## 4. Issue first

すべての実装作業は、原則としてIssueから開始する。

Issueには以下を含める。

```text
目的
背景
対象範囲
非対象範囲
受け入れ条件
RDE観点
テスト方針
```

### 4.1 Issueテンプレート案

```markdown
## 目的

## 背景

## 対象範囲

## 非対象範囲

## 受け入れ条件

## RDE観点

### 保存された要素

### 許可された変換

### 補完される要素

### 未解決の要素

### 逸脱リスク

## テスト方針
```

## 5. Branch first

mainブランチへ直接pushしない。

すべての変更はIssueに対応したbranchで行う。

ブランチ命名規則:

```text
feature/<issue-number>-<short-name>
fix/<issue-number>-<short-name>
docs/<issue-number>-<short-name>
refactor/<issue-number>-<short-name>
test/<issue-number>-<short-name>
```

例:

```text
feature/12-prompt-ir-builder
docs/18-development-principles
fix/24-profile-schema-validation
```

## 6. TDD / test first

Sayaneでは、可能な限りTDDを採用する。

新しい仕様、モデル、Adapter、Evaluator、Storage実装を追加する場合、先にテストを書く。

基本サイクル:

```text
Red   : 失敗するテストを書く
Green : 最小実装で通す
Refactor : 設計を整える
RDE Review : 意味変化を確認する
```

## 7. テスト方針

### 7.1 Unit Test

対象:

- SayaneProfile model
- PromptIR model
- Adapter
- Strategy
- Evaluator
- Storage
- Diff / Merge

### 7.5 Acceptance Test

Community Edition の受け入れ条件・手動シナリオ・CI 証拠の対応は [acceptance-spec.md](acceptance-spec.md) を正とする。手動／自動の境界は [acceptance-manual-only.md](acceptance-manual-only.md)。CLI 詳細は [cli-acceptance-test.md](cli-acceptance-test.md)、Chrome Extension 専用 UAT は [extension-acceptance-test.md](extension-acceptance-test.md)、Extension Playwright E2E は [extension-e2e.md](extension-e2e.md) を参照する。

### 7.2 Contract Test

AdapterやBridge APIは契約を明確にする。

対象:

- ClaudeAdapter
- ChatGPTAdapter
- GeminiAdapter
- Local Bridge API
- Chrome Extensionとの通信形式

### 7.3 Regression Test

Profile変換、Prompt IR生成、RDE分類は、過去の出力を壊しやすい。

代表的profileやcontext packetをfixturesとして保持し、意図しない差分を検出する。

### 7.4 Security / Privacy Test

対象:

- Local Bridge token
- Origin検証
- Profile merge承認フロー
- secret混入検出
- 外部ページからのprompt injection耐性

## 8. デザインパターン重視

Sayaneは、LLM差異、UI差異、Storage差異、評価差異を扱うため、設計パターンを明示的に用いる。

### 8.1 Adapter Pattern

LLM固有形式への変換を分離する。

```text
PromptIR → ClaudeAdapter → Claude prompt/messages
PromptIR → ChatGPTAdapter → OpenAI messages
PromptIR → GeminiAdapter → Gemini request
```

### 8.2 Strategy Pattern

推論様式や文脈選択方針を切り替える。

例:

- MinimalContextStrategy
- DeepReasoningStrategy
- StructuredOutputStrategy
- RDEReviewStrategy

### 8.3 Builder Pattern

Profile、Context、TaskからPrompt IRを組み立てる。

### 8.4 Factory Pattern

target名からAdapterやStrategyを生成する。

### 8.5 Decorator Pattern

Logging、Tracing、RDE評価、Token count、Security checkなどの横断機能を追加する。

### 8.6 Observer Pattern

Outputや評価結果をLineage、Candidate Update、Profile Evolutionへ通知する。

### 8.7 Repository Pattern

Profile Store、Context Store、Lineage Storeを抽象化する。

FileSystem、Obsidian、Git、**Commercial Edition（Rust 暗号化 SQLite）** を差し替え可能にする。商用版の設計・ライセンス保護対象は Commercial Edition 側で管理し、本 OSS リポジトリでは [storage-backend 契約](storage-backend.md) と [Confidentiality Policy 契約](confidentiality-policy-schema.md) のみ公開する。

## 9. アンチパターン

以下を避ける。

- mainへの直接push
- Issueなしの大規模変更
- テストなしのCore変更
- Prompt文字列の直生成
- LLM固有処理をProfile modelへ混入すること
- Chrome Extensionに人格管理の本体を持たせること
- 自動capture情報を承認なしに長期Profileへmergeすること
- RDE分類なしに意味変更をmergeすること
- if分岐でAdapter差異を処理し続けること
- 実装上の都合を設計思想として正当化すること

## 10. PRレビュー基準

Pull Requestは以下を満たすことを原則とする。

```text
Issueに紐づいている
branch命名が明確である
テストが追加または更新されている
RDE観点が記載されている
README/docs/schemaの更新が必要なら反映されている
Core/API/Schema変更では互換性影響が説明されている
```

## 11. 開発フェーズ別の適用

### Phase 0

ドキュメント中心。ただし設計変更にもRDE観点を適用する。

### Phase 1

Core modelとCLIはtest firstを必須に近い扱いとする。

### Phase 2

Local Bridgeではcontract testとsecurity testを重視する。

### Phase 3

Chrome ExtensionではDOM変更に弱い箇所を分離し、Coreへ判断を持ち込まない。

### Phase 4以降

RDE / UIB / LineageはSayaneの中核であり、回帰テストとfixturesを重視する。

## 12. 総括

Sayaneの開発は、単に機能を積み上げる作業ではない。

人格的文脈を扱うシステムでは、実装の一行が意味の一部を変える可能性がある。

そのためSayaneでは、Issue first、Branch first、TDD/test first、デザインパターン重視を、RDE原則のもとで統合する。

```text
安全な実装とは、意味変化を見失わない実装である。
```
