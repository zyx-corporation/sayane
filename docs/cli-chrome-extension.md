# CLI / Local Bridge / Chrome Extension 設計

## 1. 概要

Sayane は初期形として、CLI、Local Bridge、Chrome Extensionを組み合わせた単体アプリケーションを目指す。

ただし、各UIや連携面は交換可能とし、Core Libraryを中心に据える。

```text
Chrome Extension
   ↓ capture / insert
Local Bridge
   ↓ localhost API
CLI / Core Library
   ↓
Profile Store / Context Store / Lineage
```

## 2. CLI

CLIはSayaneの信頼できる制御面である。

**Phase 1 実装済みコマンドの操作手順**は [CLI マニュアル](cli-manual.md) を参照する。

初期コマンド案（ロードマップ含む）は以下である。

```bash
sayane init
sayane profile build
sayane profile inspect
sayane capture ./note.md
sayane compile --target chatgpt
sayane compile --target claude
sayane compile --target gemini
sayane diff old.yaml new.yaml
sayane evaluate --mode rde
sayane export --format markdown
sayane serve --port 38741
```

### 2.1 init

Profile Storeを初期化する。

```text
~/.sayane/
  profiles/
    default/
      sayane.profile.yaml
      context/
      knowledge/
      policy/
      lineage/
      exports/
```

### 2.2 capture

Markdown、テキスト、ブラウザから送られた文脈候補を取り込む。

取り込まれた情報は、即座にProfileへmergeしない。まずCandidate Updateとして保存する。

### 2.3 compile

Sayane Profileとタスク文脈からPrompt IRを生成し、指定target向けのプロンプトへ変換する。

### 2.4 diff

ProfileやContextの差分を抽出する。

単なるテキスト差分ではなく、将来的には意味変化分類を行う。

### 2.5 evaluate

RDEまたはUIB評価を実行する。

### 2.6 serve

Local Bridgeを起動する。

Chrome ExtensionはこのBridgeを通してCore Libraryへアクセスする。

## 3. Local Bridge

Local Bridgeは、Chrome ExtensionとCore Libraryの間に置かれるlocalhost APIである。

Extensionが直接Profile Storeを変更しないようにする。

初期API案:

```text
GET  /health
GET  /profiles
POST /capture
POST /compile
POST /evaluate
GET  /context-packet
POST /candidate-updates/{id}/approve
POST /candidate-updates/{id}/reject
```

### 3.1 セキュリティ

localhost APIには認証トークンを必須とする。

初回接続では、CLIがpairing codeを表示し、Extension側で入力する。

```text
sayane serve
Pairing code: 123-456
```

Bridgeは以下を確認する。

- Authorization token
- Origin
- Extension ID
- request scope

### 3.2 権限モデル

Bridge APIは、読み取り、capture、compile、evaluate、mergeの権限を分ける。

特にProfileへのmergeは危険操作であり、明示承認なしに実行しない。

## 4. Chrome Extension

Chrome Extensionは入口と出口である。

### 4.1 入口

- 選択テキストをcapture
- 現在ページをMarkdown化してcapture
- YouTube transcriptをcapture
- note記事をcapture
- GitHub issue / PRをcapture
- ChatGPT / Claude / Geminiの会話をcapture

### 4.2 出口

- ChatGPT入力欄へcontext packetを挿入
- Claude入力欄へcontext packetを挿入
- Gemini入力欄へcontext packetを挿入
- Markdown形式でclipboardへコピー

### 4.3 UI案

Popup UI:

```text
Profile: default

[Capture selected text]
[Capture this page]
[Generate ChatGPT prompt]
[Generate Claude prompt]
[Insert context packet]
[Review candidate updates]
```

Options UI:

```text
Bridge URL
Pairing token
Default profile
Capture mode
Allowed domains
```

## 5. Extensionの責任制限

Extensionは便利なUIであり、Sayaneの本体ではない。

Extensionは以下を行わない。

- Profile本体の直接編集
- RDE評価の本体処理
- Lineageの確定更新
- secretの長期保存
- LLM API keyの管理

判断、保存、評価、mergeはCore Library側で行う。

## 6. 実装技術

### 6.1 CLI / Bridge

- Python
- Typer
- FastAPI
- Uvicorn
- Pydantic
- Rich

### 6.2 Chrome Extension

- TypeScript
- React
- Vite
- Manifest V3
- content script
- background service worker

## 7. MVP範囲

### 7.1 MVP 0.1 CLI

- init
- profile load/save
- compile target=chatgpt/claude
- export markdown

### 7.2 MVP 0.2 Bridge

- serve
- /health
- /profiles
- /capture
- /compile

### 7.3 MVP 0.3 Extension

- selected text capture
- page capture
- context packet insertion
- profile selection

### 7.4 MVP 0.4 Evaluation

- candidate update
- RDE diff
- approval / reject
- UIB簡易評価
