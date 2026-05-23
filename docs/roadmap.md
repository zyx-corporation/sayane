# Omomuki 実装ロードマップ

## 1. 方針

Omomuki は、まずCLIで最小価値を実証し、その後 Local Bridge、MCP Server、Chrome Extension へ段階的に展開する。

Chrome Extension は有用な入口・出口であるが、Web UIのDOM変更に弱いため、安定接続面としてはMCP ServerをPhase 2.5に置く。

ただし、最初からCore Libraryを分離し、将来的なKotonoha、Obsidian plugin、VSCode extension、MCP server、Tauri desktopへの再利用を考慮する。

実装言語は以下を基本とする。

```text
Core / CLI / Bridge : Python
Chrome Extension    : TypeScript
Schema / IR         : JSON Schema + Pydantic
将来の高速化部分     : Rust
```

## 2. Phase 0: Repository Foundation

目的は、設計文書と最低限の開発基盤を整えることである。

作業項目:

- README整備
- Apache-2.0 LICENSE確認
- docs整備
- pyproject.toml追加
- extension/package.json追加
- 基本ディレクトリ作成
- CI方針検討（[`ci.md`](ci.md)、`.github/workflows/ci.yml`）
- security方針の明文化（[`security.md`](security.md)）
- MVP範囲の明文化（[`mvp-scope.md`](mvp-scope.md)）

Phase 0 完了時点で整備済み:

- `schemas/` — Omomuki Profile / Prompt IR の JSON Schema
- `src/omomuki/` — core, cli, bridge, adapters, strategies, evaluators, storage, mcp
- `examples/profiles/minimal.yaml`
- `tests/` — パッケージ import と schema 検証
- `extension/` — Manifest V3 スケルトン

想定ディレクトリ:

```text
omomuki/
  README.md
  README.ja.md
  LICENSE
  docs/
  schemas/
  src/
    omomuki/
      core/
      cli/
      bridge/
      adapters/
      strategies/
      evaluators/
      storage/
      mcp/
  extension/
    manifest.json
    src/
  examples/
  tests/
```

## 3. Phase 1: CLI MVP

目的は、Omomuki Profileを読み込み、Prompt IRへ変換し、ChatGPT / Claude向けpromptへcompileできることを実証することである。

このPhaseでは、Local Bridge、Chrome Extension、MCP Server、RDE/UIB自動評価は実装しない。Omomukiの最小価値である `Profile → Prompt IR → Adapter` を動かすことに集中する。

実装対象:

- `omomuki init`
- `omomuki profile inspect`
- `omomuki compile --target chatgpt`
- `omomuki compile --target claude`
- `omomuki export --format markdown`

Core model:

- OmomukiProfile
- PromptIR
- Policy
- ContextIndex
- Adapter base class
- ChatGPTAdapter
- ClaudeAdapter

完了条件:

- sample Omomuki Profile を読み込める
- schema validation が通る
- Prompt IR を生成できる
- ChatGPT向けpromptを生成できる
- Claude向けpromptを生成できる
- pytestで基本modelとadapterが検証されている
- examplesに最小profileが存在する
- READMEまたはdocsにCLI実行例がある

**マニュアル**: [CLI マニュアル](cli-manual.md) / [はじめに](getting-started.md)

## 4. Phase 2: Local Bridge MVP

目的は、外部UIや将来のExtensionからCore Libraryを利用できるlocalhost APIを提供することである。

実装前に `docs/security.md` の要件を満たすことを確認する。

実装対象:

- `omomuki serve`
- `GET /health`
- `GET /profiles`
- `POST /capture`
- `POST /compile`
- `GET /context-packet`

完了条件:

- curlでcapture/compileが動作する
- pairing tokenの初期設計がある
- ExtensionなしでもBridge APIの動作確認ができる
- CORS deny by default
- localhost bind限定
- profile merge endpointを持たない、または明示承認を必須にする

**マニュアル**: [Bridge マニュアル](bridge-manual.md) / [CLI マニュアル](cli-manual.md)（`omomuki serve`）

## 5. Phase 2.5: MCP Server MVP

目的は、DOM注入に依存しない安定接続面として、MCP対応クライアントからOmomuki Coreを利用できるようにすることである。

Chrome Extensionは便利なUIであるが、長期的な安定接続面ではない。MCP Serverは、Cline、Cursor、Claude Desktop、その他MCP対応クライアントからOmomukiのProfile / Context / Prompt IR生成機能を呼び出すための接続面となる。

実装対象:

- Omomuki MCP server skeleton
- profile list tool
- compile prompt tool
- context packet tool
- candidate update list tool
- read-only mode

完了条件:

- MCPクライアントからprofile一覧を取得できる
- MCPクライアントからChatGPT/Claude向けcontext packetを生成できる
- read-only modeでProfile本体を変更しない
- Local Bridgeと同等以上のsecurity境界を持つ
- Extensionなしで安定した接続面として動作する

**マニュアル**: [MCP マニュアル](mcp-manual.md) / [CLI マニュアル](cli-manual.md)（`omomuki mcp`）

## 6. Phase 3: Chrome Extension MVP

目的は、ブラウザ上の文脈をOmomukiへ取り込み、LLM入力欄へ挿入できること。

Chrome Extension は補助UIであり、Omomukiの本体ではない。DOM依存箇所は分離し、壊れてもCore / CLI / MCPが影響を受けない構成にする。

実装対象:

- Manifest V3
- popup UI
- options UI
- content script
- selected text capture
- current page capture
- context packet insertion
- Bridge pairing

完了条件:

- 選択テキストをBridgeへ送信できる
- ChatGPT/Claudeの入力欄へcontext packetを挿入できる
- profile selectionが可能
- DOM selectorをsite adapterとして分離している
- DOM変更時のfailure modeが明示されている

**マニュアル**: [Chrome Extension マニュアル](extension-manual.md) / [Bridge マニュアル](bridge-manual.md)

## 7. Phase 4: RDE / UIB Evaluation MVP

目的は、Profile更新候補を即時mergeせず、意味変化評価を挟めること。

初期段階ではLLM-as-a-Judgeへ依存しすぎない。まずは schema validation、rule-based diff、heuristic RDE classification を中心にする。

評価階層:

```text
Level 0: schema validation + rule-based diff
Level 1: heuristic RDE classification
Level 2: local LLM assisted review
Level 3: external LLM assisted review
```

実装対象:

- Candidate Update model
- schema validation
- rule-based diff
- heuristic RDE classification
- UIB simple checklist
- approve / reject flow
- lineage record
- profile diff

完了条件:

- captureした情報がCandidate Updateとして保存される
- RDE分類が付与される
- ユーザー承認後にProfileへmergeされる
- lineageに更新履歴が残る
- LLM評価なしでも最小評価が動作する

**マニュアル**: [RDE / Candidate 評価マニュアル](evaluation-manual.md)

Phase 4 拡張（0.5.1）: Level 2/3 LLM-as-a-Judge、`--force-critical` による values/voice/policy/roles の merge。

## 8. Phase 5: Storage / Obsidian / Git

目的は、ProfileとContextを長期運用可能な形で保存すること。

実装対象:

- FileSystem storage
- Obsidian vault import/export
- Git commit integration
- context_index generation
- markdown normalization

完了条件:

- Obsidian vaultからcontextを取り込める
- Profile更新をGit履歴に残せる
- context_indexを自動生成できる

**マニュアル**: [Storage / Obsidian / Git マニュアル](storage-manual.md)

## 9. Phase 6: Rust Extraction

目的は、安定した高負荷部分をRustへ切り出すこと。

候補:

- semantic diff engine
- markdown vault indexer
- encrypted profile store
- local daemon
- WASM module for extension-side lightweight processing

Rust化は、Python実装で仕様とボトルネックが明確になってから行う。

## 10. 優先順位

初期の最重要成果物は以下である。

```text
1. OmomukiProfile model
2. PromptIR model
3. Adapter interface
4. CLI compile
5. Local Bridge security design
6. MCP Server MVP
7. Chrome Extension capture/insert
8. Candidate Update + RDE diff
```

## 11. 非目標

初期段階では以下を目標にしない。

- 完全自動人格更新
- 全LLM API対応
- 完全な意味理解
- 意識や人格保存の主張
- クラウドSaaS化
- 複雑なGUI
- Chrome Extension中心の安定接続設計
- RDE/UIB評価の完全自動化
- 同一人格の完全再現という主張

Omomukiはまず、local-firstなPersona / Context IR基盤として最小実装を完成させる。
