# MCP Server Integration

## 1. 位置づけ

Sayaneでは、MCP ServerをPhase 2.5に配置する。

Chrome Extensionは便利な入口・出口であるが、Web UIのDOM変更に弱い。ChatGPT、Claude、GeminiなどのWeb UIは頻繁に変更されるため、DOM注入をSayaneの安定接続面にしてはならない。

MCP Serverは、DOMに依存しない安定接続面として設計する。

```text
CLI / Core Library
        ↓
Local Bridge       MCP Server
        ↓              ↓
Chrome Extension   MCP Client
```

## 2. 目的

MCP Serverの目的は、MCP対応クライアントからSayane Coreを利用できるようにすることである。

対象クライアント例:

- Claude Desktop
- Cursor
- Cline
- その他MCP対応クライアント

## 3. 初期方針

Phase 2.5では read-only mode を既定とする。

Profile本体の変更、policy変更、identity変更、values変更は行わない。

MCP経由の操作は、まず文脈生成・Prompt IR生成・context packet生成に限定する。

## 4. 初期Tool案

### 4.1 list_profiles

利用可能なProfile一覧を返す。

### 4.2 inspect_profile

Profileの要約を返す。

機微情報を全量返さず、summary modeを既定にする。

### 4.3 compile_prompt

Sayane Profileとtask instructionから、指定target向けpromptを生成する。

target例:

```text
chatgpt
claude
gemini
markdown
```

### 4.4 generate_context_packet

LLM入力欄や外部クライアントへ渡すためのcontext packetを生成する。

### 4.5 list_candidate_updates

保留中のCandidate Updateを一覧する。

Phase 2.5では承認・mergeは行わない。

## 5. 禁止する操作

Phase 2.5では以下を禁止する。

- direct profile merge
- policy rewrite
- identity rewrite
- values rewrite
- voice rewrite
- secret export
- automatic candidate approval
- destructive storage operation

## 6. Security

MCP ServerはLocal Bridgeと同等以上のsecurity境界を持つ必要がある。

最低要件:

```text
read-only default
explicit profile scope
no automatic merge
audit log
secret redaction option
least privilege tool exposure
```

## 7. Local Bridgeとの違い

Local Bridgeは主にChrome ExtensionやローカルUIとの接続を想定する。

MCP Serverは、MCP対応AIクライアントからの構造化呼び出しを想定する。

```text
Local Bridge: UI連携面
MCP Server  : AI client連携面
CLI         : 制御面
Core        : 意味処理面
```

## 8. RDE観点

MCP Server経由で生成されるcontext packetは、Sayane Profileの一部を外部LLMへ提示する変換結果である。

したがって、MCP Serverは単なるAPIではなく、意味変換の出口である。

確認すべき点:

- Profileの意味がtarget向けpromptで過剰に変形されていないか
- 必要以上の文脈を外部LLMへ渡していないか
- LLMクライアント側の要求がProfile policyを上書きしていないか
- context packetが同一人格の完全再現を主張していないか

## 9. 完了条件

Phase 2.5は以下を満たしたら完了とする。

```text
MCPクライアントからprofile一覧を取得できる
MCPクライアントからProfile summaryを取得できる
MCPクライアントからChatGPT/Claude向けcontext packetを生成できる
read-only modeでProfile本体を変更しない
security.mdの最低要件を満たす
Extensionなしで安定した接続面として動作する
```
