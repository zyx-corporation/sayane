# Sayane 管理ディレクトリ（SAYANE_DIR）

Sayane は、ユーザーの人格的文脈・価値観・応答様式・プロンプト適応・E2E実行状態を local-first に管理する。

既定の管理ルートは `~/.sayane` である。環境変数 `SAYANE_DIR` を指定すると、すべての既定パスはその配下に移る。

```bash
export SAYANE_DIR="$HOME/.sayane"
```

`SAYANE_DIR` は、Profile Store だけでなく、prompt adaptation、provider constraints、E2E browser state を含む Sayane の管理境界である。

---

## 1. 標準レイアウト

```text
$SAYANE_DIR/
  README.md

  profiles/
    default/
      sayane.profile.yaml
      context/
        MyContext.md
        AI_HANDOFF.md

  prompts/
    targets/
      README.md
      chatgpt.yaml              # 将来追加
      claude.yaml               # 将来追加
      gemini.yaml               # 将来追加
      deepseek.yaml             # 将来追加
      openai_compatible.yaml    # 将来追加
      plain_text.yaml           # 将来追加

    models/
      README.md
      qwen2.5-7b-instruct.yaml                 # 将来追加
      deepseek-r1-distill-qwen-7b.yaml         # 将来追加
      elyza-japanese-llama-2-7b-instruct.yaml  # 将来追加

    providers/
      README.md
      local-openwebui.yaml      # 将来追加
      local-librechat.yaml      # 将来追加
      local-custom.yaml         # 将来追加

  e2e/
    user-data/
      README.md
      chatgpt/
      claude/
      gemini/
      deepseek/
      local-openwebui/
      local-librechat/
      local-custom/

    prompts/
      README.md
      chatgpt.md
      claude.md
      gemini.md
      deepseek.md
      local-openwebui.md
```

`sayane init` はこの骨格を非破壊で作成する。既存ファイルは上書きしない。

---

## 2. profiles/

`profiles/` は Sayane Profile と文脈ファイルの正本である。

```text
profiles/default/sayane.profile.yaml
profiles/default/context/
```

Profile は、人格的文脈・価値観・応答様式・方針・文脈索引を保持する。

`--profile` を省略した CLI コマンドは、既定で次を読む。

```text
$SAYANE_DIR/profiles/default/sayane.profile.yaml
```

---

## 3. prompts/

`prompts/` は、モデル・target・provider ごとの prompt adaptation を置く監査可能な領域である。

ここに置く内容は Git 管理・差分確認・RDE 評価の対象にできる。ブラウザの user-data とは異なり、意味資産として扱う。

### 3.1 prompts/targets/

target-level prompt adaptation を置く。

例:

```text
prompts/targets/chatgpt.yaml
prompts/targets/claude.yaml
prompts/targets/gemini.yaml
prompts/targets/deepseek.yaml
prompts/targets/openai_compatible.yaml
prompts/targets/plain_text.yaml
```

target は、Context Packet / Prompt IR をどの出力形式へ変換するかを表す。

例:

- `chatgpt`: ChatGPT 向け整形
- `claude`: Claude 向け整形
- `gemini`: Gemini 向け整形
- `deepseek`: DeepSeek 向け整形
- `openai_compatible`: OpenAI互換API向け整形
- `plain_text`: 任意UIに貼り付けるテキスト整形

### 3.2 prompts/models/

model-specific prompt optimization を置く。

例:

```text
prompts/models/qwen2.5-7b-instruct.yaml
prompts/models/deepseek-r1-distill-qwen-7b.yaml
prompts/models/elyza-japanese-llama-2-7b-instruct.yaml
```

モデル最適化は、LLMの能力・癖・文脈長・日本語性能・指示追従特性に合わせた調整である。

これは provider/UI とは分ける。

### 3.3 prompts/providers/

provider/UI-specific constraints を置く。

例:

```text
prompts/providers/local-openwebui.yaml
prompts/providers/local-librechat.yaml
prompts/providers/local-custom.yaml
```

provider は実DOM挿入対象・UI・配送面の制約を表す。

例:

- Open WebUI の入力欄仕様
- LibreChat の会話UI仕様
- local custom UI の制約
- provider側のsystem prompt扱いの制限

---

## 4. e2e/

`e2e/` はテスト実行状態を置く。

### 4.1 e2e/user-data/

`e2e/user-data/` は Chromium persistent profile の置き場である。

ここには cookie、localStorage、IndexedDB、ログイン状態、拡張機能状態などが入る可能性がある。

**ここを canonical prompt source として扱ってはいけない。**

例:

```text
e2e/user-data/chatgpt/
e2e/user-data/claude/
e2e/user-data/gemini/
e2e/user-data/deepseek/
e2e/user-data/local-openwebui/
```

各 key は real DOM E2E の `profileKey` に対応する。

### 4.2 e2e/prompts/

`e2e/prompts/` は E2E 専用のプロンプト fixture を置く場所である。

ここには `SAYANE_E2E_MARKER::*` のようなテスト marker を含めてよい。

production prompt の正本ではない。

---

## 5. 分離原則

| 領域 | 正体 | 監査対象 | Git管理 | 備考 |
|------|------|:------:|:------:|------|
| `profiles/` | 人格・文脈の正本 | ✓ | 任意 | 機微情報に注意 |
| `prompts/targets/` | target別prompt適応 | ✓ | 推奨 | ChatGPT/Claude/Gemini等 |
| `prompts/models/` | model別prompt最適化 | ✓ | 推奨 | Qwen/DeepSeek/ELYZA等 |
| `prompts/providers/` | provider/UI制約 | ✓ | 推奨 | Open WebUI/LibreChat等 |
| `e2e/user-data/` | browser session state | ✗ | 非推奨 | cookies等を含む |
| `e2e/prompts/` | E2E fixture | △ | 任意 | test marker 含む |

---

## 6. Gemini / DeepSeek / local SLM への拡張

Gemini、DeepSeek、local SLM は、次の3層を分けて扱う。

```text
provider id   = 実DOM / UI / 配送対象
 target       = Prompt IR の変換先
 model        = 実際のLLM / SLM能力特性
```

例:

| 用途 | provider id | target | model |
|------|-------------|--------|-------|
| Gemini Web | `gemini` | `gemini` | Gemini 系 |
| DeepSeek Web | `deepseek` | `deepseek` | DeepSeek 系 |
| Open WebUI + Qwen | `local-openwebui` | `plain_text` or `openai_compatible` | Qwen2.5 |
| LibreChat + DeepSeek | `local-librechat` | `openai_compatible` | DeepSeek-R1-Distill |
| custom local UI | `local-custom` | `plain_text` | 任意SLM |

local SLM は単一の provider ではない。Open WebUI、LibreChat、AnythingLLM、custom UI など、UI単位で provider として扱う。

---

## 7. RDE観点

### 保存された要素

- Sayane Profile は人格・文脈の正本であり、LLMやブラウザprofileに従属しない。
- prompt adaptation は監査可能な意味資産として保持する。
- browser user-data は不透明な実行状態として分離する。

### 変換された要素

- 旧来の `~/.sayane` 固定から、`SAYANE_DIR` による明示的管理境界へ移行する。
- ChatGPT / Claude 固定ではなく、provider / target / model 分離へ移行する。

### 補完された要素

- `prompts/targets/`
- `prompts/models/`
- `prompts/providers/`
- `e2e/user-data/{key}`
- `e2e/prompts/`

### 逸脱リスク

- `e2e/user-data/` に意味資産を置いてしまうこと。
- provider と model を混同すること。
- local SLM を単一UIとして扱い、複数UIの差異を消すこと。

### 対策

- prompt正本は `prompts/` に置く。
- provider / target / model を分離する。
- `e2e/user-data/` は Git 管理対象外とし、実行状態として扱う。

---

## 8. 関連

- [CLI マニュアル](cli-manual.md)
- [Chrome Extension Real DOM E2E 手順](extension-real-dom-e2e.md)
- [Chrome Extension 受け入れテスト手順書](extension-acceptance-test.md)
- GitHub Issue #96: Provider adapters for Gemini, DeepSeek, local SLM UIs
