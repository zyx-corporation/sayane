# Extension Playwright E2E (#91)

Chrome Extension の **Insert 実 DOM** を、本物の ChatGPT / Claude に依存せず Playwright で検証する。

| 項目 | 値 |
|------|-----|
| **対象** | INS-CG-02, INS-CL-02, INS-CG-04（任意） |
| **実行** | ローカル手動 / GitHub Actions `extension-e2e.yml` |
| **スケジュール** | 毎週月曜 06:00 UTC + `workflow_dispatch` + `extension/**` 変更時 PR |

## 前提

- Python 3.11+、`pip install -e ".[dev]"`（sayane ルート）
- Node 22+、`extension/` で `npm ci && npm run build`
- Chromium（`npm run test:e2e:install`）

## ローカル実行

```bash
# sayane ルート
pip install -e ".[dev]"

cd extension
npm ci
npm run build
npm run test:e2e:install
npm run test:e2e
```

Bridge は `e2e/global-setup.ts` が一時 `HOME` で `sayane` プロファイルと `uvicorn` を起動する。手動で `sayane serve` を走らせる必要はない。

## テスト方針

| ファイル | 内容 |
|---------|------|
| `e2e/fixtures/chatgpt.html` | `#prompt-textarea` を持つ ChatGPT DOM モック |
| `e2e/fixtures/claude.html` | `.ProseMirror` を持つ Claude DOM モック |
| `e2e/insert-chatgpt.spec.ts` | INS-CG-02（DOM + popup UI） |
| `e2e/insert-claude.spec.ts` | INS-CL-02（DOM + popup UI） |
| `e2e/site-mismatch.spec.ts` | INS-CG-04（Claude adapter × ChatGPT ページ） |

`page.route()` で `https://chatgpt.com/` / `https://claude.ai/` を fixture HTML に差し替える。Extension の `host_permissions` と site adapter の URL 判定は本番と同じ。

**popup UI テスト**は `chrome.action.openPopup()` が使える環境でのみ実行する。自動化で開けない場合は **skip**（DOM 挿入テストが INS-CG-02 / INS-CL-02 の主証拠）。

## CI

`.github/workflows/extension-e2e.yml` — Ubuntu + Chromium `--with-deps`。

## 手動 UAT との関係

[L3 手動](extension-acceptance-test.md) の実サイト Insert は引き続き任意／リリース時確認。本 E2E は DOM 回帰の **scheduled** ゲートとして L1 補完とする。
