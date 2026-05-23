# Chrome Extension マニュアル

Phase 3 の Omomuki Chrome Extension は **補助 UI** である。判断・保存・merge は Core / Bridge 側で行う。

## 1. 前提

1. `omomuki init` で Profile Store を作成
2. `omomuki serve` で Local Bridge を起動（`127.0.0.1:38741`）
3. Extension Options に Bridge URL と Bearer token を設定（`~/.omomuki/bridge.token`）

## 2. ビルドと読み込み

```bash
cd extension && npm install && npm run build
```

Chrome の「パッケージ化されていない拡張機能を読み込む」→ `extension/` ディレクトリ。

## 3. Popup 操作

| ボタン | 動作 |
|--------|------|
| Capture selection | 選択テキスト → Bridge `/capture`（Candidate） |
| Capture this page | ページ要約 → `/capture` |
| Insert context (ChatGPT) | `/context-packet?target=chatgpt` → 入力欄へ挿入 |
| Insert context (Claude) | `target=claude` で同様 |

Profile ドロップダウンは `/profiles` から取得。

## 4. Site adapter と failure mode

| code | 意味 |
|------|------|
| `INPUT_NOT_FOUND` | LLM 入力欄のセレクタ不一致（DOM 変更） |
| `SITE_MISMATCH` | 適切なサイトでないのに挿入を試行 |
| `UNSUPPORTED_SITE` | 未対応ホスト |

アダプタ定義: `extension/src/sites/`。ChatGPT / Claude の DOM 変更時はここだけ更新する。

## 5. 責任の限界

Extension は行わない:

- Profile の直接編集・merge
- RDE 評価の本体
- API key 管理

## 6. トラブルシューティング

| 症状 | 対処 |
|------|------|
| Bridge unreachable | `omomuki serve` 起動、Options の URL/port |
| `401` / capture 失敗 | Bearer token を `~/.omomuki/bridge.token` からコピー |
| Insert 失敗 `INPUT_NOT_FOUND` | ChatGPT/Claude の DOM 変更。`extension/src/sites/` を更新 |
| 選択 capture でテキストなし | ページ上でテキストを選択してから実行 |

## 7. 関連

- [はじめに](getting-started.md)
- [Bridge マニュアル](bridge-manual.md)
- [CLI マニュアル](cli-manual.md) — `omomuki serve`
- [CLI / Bridge 設計](cli-chrome-extension.md)
- [Security Design](security.md)
