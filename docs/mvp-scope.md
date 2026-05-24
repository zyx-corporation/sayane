# Sayane MVP範囲

## 1. 目的

この文書は、Sayaneの初期MVPを過剰に広げないための範囲定義である。

Sayaneは、CLI、Local Bridge、MCP Server、Chrome Extension、RDE/UIB評価、Obsidian連携など複数の方向へ拡張できる。しかし初期段階で全てを同時に実装すると、最小価値の検証が遅れる。

したがって、Phase 1では以下の最小価値に集中する。

```text
Sayane Profile から Prompt IR を生成し、ChatGPT / Claude 向けpromptへcompileできること。
```

## 2. Phase 1 MVPで実装するもの

### 2.1 Core model

- SayaneProfile
- PromptIR
- Policy
- ContextIndex
- Adapter base class
- ChatGPTAdapter
- ClaudeAdapter

### 2.2 CLI command

```bash
sayane init
sayane profile inspect
sayane compile --target chatgpt
sayane compile --target claude
sayane export --format markdown
```

### 2.3 Schema / Validation

- Sayane Profile schema
- Prompt IR schema
- Pydantic model validation

### 2.4 Tests

- profile load test
- schema validation test
- Prompt IR generation test
- ChatGPTAdapter test
- ClaudeAdapter test
- CLI smoke test

### 2.5 Examples

- minimal profile
- sample context
- generated ChatGPT prompt
- generated Claude prompt

## 3. Phase 1で実装しないもの

Phase 1では以下を実装しない。

- Local Bridge
- MCP Server
- Chrome Extension
- RDE/UIB自動評価
- Candidate Update merge flow
- Obsidian import/export
- Git integration
- encrypted storage
- Rust implementation
- full LLM API execution
- browser DOM injection

## 4. 完了条件

Phase 1は以下を満たしたら完了とする。

```text
sample Sayane Profile を読み込める
schema validation が通る
Prompt IR を生成できる
ChatGPT向けpromptを生成できる
Claude向けpromptを生成できる
pytestで基本modelとadapterが検証されている
examplesに最小profileが存在する
READMEまたはdocsにCLI実行例がある
```

## 5. RDE観点

### 保存された要素

- 人格と実行の分離
- Profile → Prompt IR → Adapter の中核構造
- LLM非依存のProfile保持
- 同一人格を同一プロンプトに固定しない設計

### 許可された変換

- 初期実装ではChatGPT / Claudeのみ対応
- RDE/UIBはPhase 4へ延期
- Chrome ExtensionはPhase 3へ延期
- MCP ServerはPhase 2.5へ配置

### 補完される要素

- CLIによる最小価値検証
- schema validationによる安全なProfile読み込み
- Adapter単位でのTDD

### 未解決の要素

- Gemini Adapter
- OSS Adapter
- context selection strategy
- RDE classification automation
- Local Bridge security implementation

### 逸脱リスク

- Phase 1で機能を広げすぎる
- AdapterがPromptIRを迂回して直接文字列生成する
- Profile modelにLLM固有ロジックを混入する
- 同一人格の完全再現を主張する

## 6. 判断基準

新しい機能提案がPhase 1へ入るかどうかは、次の問いで判断する。

```text
それは Profile → Prompt IR → Adapter の最小価値実証に必須か。
```

必須でなければ、Phase 2以降へ送る。
