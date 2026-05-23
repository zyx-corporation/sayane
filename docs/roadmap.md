# Omomuki 実装ロードマップ

## 1. 方針

Omomuki は、まずCLI + Chrome Extensionを持つ単体アプリケーションとして実装する。

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
- CI方針検討

想定ディレクトリ:

```text
omomuki/
  README.md
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
  extension/
    manifest.json
    src/
  examples/
  tests/
```

## 3. Phase 1: CLI MVP

目的は、Omomuki Profileを作成し、Prompt IRへ変換し、LLM別promptへcompileできること。

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

- sample profileからChatGPT/Claude向けpromptを生成できる
- pytestで基本modelとadapterが検証されている
- examplesに最小profileが存在する

## 4. Phase 2: Local Bridge MVP

目的は、Chrome ExtensionからCore Libraryを利用できるlocalhost APIを提供すること。

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

## 5. Phase 3: Chrome Extension MVP

目的は、ブラウザ上の文脈をOmomukiへ取り込み、LLM入力欄へ挿入できること。

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

## 6. Phase 4: RDE / UIB Evaluation MVP

目的は、Profile更新候補を即時mergeせず、意味変化評価を挟めること。

実装対象:

- Candidate Update model
- RDE classification
- UIB simple scoring
- approve / reject flow
- lineage record
- profile diff

完了条件:

- captureした情報がCandidate Updateとして保存される
- RDE分類が付与される
- ユーザー承認後にProfileへmergeされる
- lineageに更新履歴が残る

## 7. Phase 5: Storage / Obsidian / Git

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

## 8. Phase 6: Rust Extraction

目的は、安定した高負荷部分をRustへ切り出すこと。

候補:

- semantic diff engine
- markdown vault indexer
- encrypted profile store
- local daemon
- WASM module for extension-side lightweight processing

Rust化は、Python実装で仕様とボトルネックが明確になってから行う。

## 9. 優先順位

初期の最重要成果物は以下である。

```text
1. OmomukiProfile model
2. PromptIR model
3. Adapter interface
4. CLI compile
5. Local Bridge
6. Chrome Extension capture/insert
7. Candidate Update + RDE diff
```

## 10. 非目標

初期段階では以下を目標にしない。

- 完全自動人格更新
- 全LLM API対応
- 完全な意味理解
- 意識や人格保存の主張
- クラウドSaaS化
- 複雑なGUI

Omomukiはまず、local-firstなPersona / Context IR基盤として最小実装を完成させる。
