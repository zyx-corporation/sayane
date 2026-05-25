# Chrome Extension Real DOM E2E 手順

Sayane Chrome Extension の **本物の ChatGPT / Claude DOM** に対する Playwright E2E 手順である。

このテストは mock LLM page ではなく、実際の `https://chatgpt.com` / `https://claude.ai` の新規チャット入力欄へ Sayane context packet を挿入する。

送信は行わない。検証対象は、入力欄に `SAYANE_E2E_MARKER::*` が挿入されることのみである。

---

## 1. 位置づけ

このE2Eは通常PR CIの必須ゲートではない。外部サービスのDOM、ログイン状態、A/B UI、ネットワークに依存するためである。

ただし、以下では実行対象とする。

- release前 acceptance run
- `extension/src/sites/*` 変更時
- `workflow_dispatch`
- scheduled weekly run
- ChatGPT / Claude DOM drift の監視

---

## 2. 実装範囲

| 項目 | 内容 |
|------|------|
| テストランナー | Playwright |
| ブラウザ | Chromium persistent context |
| Extension | `extension/` を unpacked extension として読み込み |
| Bridge | mock Bridge fixture |
| 実サイト | `chatgpt.com`, `claude.ai` |
| 検証 | 入力欄に marker が挿入されること |
| 送信 | 行わない |
| Artifact | screenshot, trace, sanitized DOM snapshot, selector report |

mock Bridge は `/health`, `/profiles`, `/context-packet` を返す。実DOM挿入経路の検証に集中するため、Candidate / RDE / Profile Store はこのE2Eでは直接検証しない。

---

## 3. Sayane 管理ディレクトリ

E2E のブラウザ状態は `$SAYANE_DIR` 以下にまとめる。

`SAYANE_DIR` 未指定時は `~/.sayane` を使う。

```text
$SAYANE_DIR/
  e2e/
    user-data/
      chatgpt/
      claude/
      gemini/        # 将来拡張
      deepseek/      # 将来拡張
      local-openwebui/  # 将来拡張
```

各 `{key}` は `RealSiteSpec.profileKey` に対応する。新しい実サイトや local SLM UI を追加する場合も、この key を増やすだけで同じ解決規則を使う。

---

## 4. 事前準備

```bash
cd extension
npm install
npm run build
npx playwright install chromium
```

必要に応じて `SAYANE_DIR` を指定する。

```bash
export SAYANE_DIR="$HOME/.sayane"
```

ChatGPT / Claude にログイン済みの Chromium user data dir は次の場所に置く。

```bash
mkdir -p "$SAYANE_DIR/e2e/user-data/chatgpt"
mkdir -p "$SAYANE_DIR/e2e/user-data/claude"
```

初回は対象ディレクトリを使ってブラウザを起動し、手動ログインしてから閉じる運用を想定する。

ログイン状態の作成を自動化しない。CAPTCHA、2FA、アカウント作成、内部API呼び出しは対象外である。

---

## 5. 実行コマンド

```bash
cd extension
npm run test:e2e:real
```

個別実行:

```bash
npm run test:e2e:real:chatgpt
npm run test:e2e:real:claude
```

ログイン済み profile がない場合、そのサイトのE2Eは `AUTH_REQUIRED` として skip される。

---

## 6. 受け入れ条件

| ID | 条件 | 期待結果 |
|----|------|----------|
| E2E-REAL-01 | Extension load | service worker が起動し extension id を取得できる |
| E2E-REAL-02 | mock Bridge pairing | extension storage に bridgeUrl / bridgeToken が設定される |
| E2E-REAL-03 | ChatGPT real DOM | 入力欄に `SAYANE_E2E_MARKER::*` が挿入される |
| E2E-REAL-04 | Claude real DOM | 入力欄に `SAYANE_E2E_MARKER::*` が挿入される |
| E2E-REAL-05 | Artifact | 失敗時に selector report / DOM snapshot / screenshot を保存する |
| E2E-REAL-06 | Security | 実サービスにメッセージ送信しない |

---

## 7. 失敗分類

| 分類 | 意味 | 判定 |
|------|------|------|
| `AUTH_REQUIRED` | 未ログイン / セッション切れ | 通常PRではSkip相当。ログイン済みprofileを更新 |
| `DOM_DRIFT` | 入力欄セレクタ不一致 | `extension/src/sites/*` 更新Issue |
| `PERMISSION_ERROR` | `activeTab`, `scripting`, host permission 問題 | Extension権限・読み込み状態を確認 |
| `SAYANE_REGRESSION` | Extension / Bridge / formatting の回帰 | 実装修正対象 |
| `NETWORK_OR_RATE_LIMIT` | 外部サイト到達不可 / rate limit | 再実行または環境確認 |
| `ENVIRONMENT_ERROR` | user data dir, secrets, browser setup 問題 | E2E環境を修正 |

---

## 8. Artifact

失敗時、`extension/test-results/` 配下に次を保存する。

- Playwright trace
- screenshot
- selector report JSON
- sanitized DOM snapshot
- failure reason
- console log attachment

DOM snapshot は `script`, `style`, `svg`, `canvas`, `img`, `video`, `audio` を除去し、`input` / `textarea` の値を redacted にする。

---

## 9. GitHub Actions

workflow: `.github/workflows/extension-real-dom-e2e.yml`

実行条件:

- `workflow_dispatch`
- weekly schedule

通常PRの必須CIにはしない。

CI では `SAYANE_DIR=${{ github.workspace }}/.sayane-e2e` を使う。ログイン済みprofileを扱う場合は、GitHub Secrets へ直接セッション情報を置くより、self-hosted runner または暗号化artifactの利用を優先する。

---

## 10. RDE観点

### 保存された要素

- token は page DOM / content script に露出しない。
- Context Packet は background / service worker 経由で取得する。
- Extension は送信せず、入力欄への挿入に留める。
- Sayaneの人格・文脈所有はLLM側ではなくローカル側に残る。
- Sayane関連の状態は `$SAYANE_DIR` 以下に集約する。

### 変換された要素

- 手動UATの INS-CG / INS-CL を real DOM E2E で部分自動化した。
- popup UI操作ではなく background message 経由で同じ insert経路を検証する。
- サイト別 env ではなく `$SAYANE_DIR/e2e/user-data/{key}` へ一般化した。

### 補完された要素

- mock Bridge fixture
- marker-based assertion
- failure classification
- selector report
- sanitized DOM snapshot
- profileKey による provider 拡張点

### 逸脱リスク

- 外部DOM変更を Sayane regression と誤判定すること。
- screenshot / DOM snapshot に機密情報を残すこと。
- 自動テストが実サービスへメッセージ送信してしまうこと。
- `$SAYANE_DIR` に認証状態が集まるため、ディレクトリ権限管理が甘いと被害範囲が広がること。

### 対策

- marker挿入のみ検証し送信しない。
- DOM snapshot を sanitize する。
- `AUTH_REQUIRED` / `DOM_DRIFT` / `SAYANE_REGRESSION` を分類する。
- `$SAYANE_DIR/e2e/user-data` は Git 管理対象外とし、権限を利用者ローカルに閉じる。

---

## 11. 関連

- [Chrome Extension 受け入れテスト手順書](extension-acceptance-test.md)
- [Extension マニュアル](extension-manual.md)
- GitHub Issue #91: Stable real DOM E2E
