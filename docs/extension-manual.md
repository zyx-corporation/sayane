# Chrome Extension マニュアル

Phase 3 の Omomuki Chrome Extension は **補助 UI** である。判断・保存・merge は Core / Bridge 側で行う。

## 1. 前提

1. `omomuki init` で Profile Store を作成
2. `omomuki serve` で Local Bridge を起動（`127.0.0.1:38741`）
3. Extension Options に Bridge URL と Bearer token を設定（`~/.omomuki/bridge.token`）

### 権限について

- **履歴は読まない**。Chrome 日本語 UI で「閲覧履歴の読み取り」と出る場合は旧 `tabs` 権限の表示であり、本 Extension は履歴 API を使わない。
- **Capture** は `activeTab` + `scripting` で、ツールバーから Extension を開いた**現在のタブ**の選択テキストのみ読み取る。
- **Insert** は ChatGPT / Claude 等、`host_permissions` に列挙したサイトのみ。
- manifest 更新後は Chrome の「更新」だけでは権限表示が変わらないことがある。**削除してから Load unpacked し直す**。

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
| Refresh / Evaluate / Show diff / Approve / Reject | Bridge `/candidates/*`（popup） |

Profile ドロップダウンは `/profiles` から取得。Candidate 一覧は `/candidates` から取得し、capture 後は該当 ID を自動選択する。

### Candidate 操作（popup）

1. **Refresh** — 直近の Candidate 一覧を再取得
2. **Evaluate** — Level 1（既定）または Level 2（Ollama 等が Bridge 側で設定されている場合）
3. **Show diff** — merge 前の差分を popup 内に表示
4. **Approve** / **Reject** — Profile への反映または却下（判断本体は Core）

`Critical Distortion` など CLI と同様に auto-approve できない場合は Bridge が `400` を返す。CLI の `--force-critical` は Extension では未対応（意図的に限定）。

## 4. Site adapter と failure mode

| code | 意味 |
|------|------|
| `INPUT_NOT_FOUND` | LLM 入力欄のセレクタ不一致（DOM 変更） |
| `SITE_MISMATCH` | 適切なサイトでないのに挿入を試行 |
| `UNSUPPORTED_SITE` | 未対応ホスト |

アダプタ定義: `extension/src/sites/`。ChatGPT / Claude の DOM 変更時はここだけ更新する。

## 5. 責任の限界

Extension は行わない:

- Profile YAML の直接編集
- LLM judge の設定（`judge.yaml` / 環境変数は Bridge ホスト側）
- API key の永続保存

## 6. トラブルシューティング

| 症状 | 対処 |
|------|------|
| Bridge unreachable | `omomuki serve` 起動、Options の URL/port |
| `401` / capture 失敗 | Bearer token を `~/.omomuki/bridge.token` からコピー |
| Insert 失敗 `INPUT_NOT_FOUND` | ChatGPT/Claude の DOM 変更。`extension/src/sites/` を更新 |
| 選択 capture でテキストなし | ページ上でテキストを選択してから実行 |
| `Receiving end does not exist` | `https://example.com` 等の通常ページを開き、Extension 更新後はタブを再読み込み（F5） |

## 7. 受け入れテスト

リリース前・popup / サイトアダプタ変更後は [Chrome Extension 受け入れテスト手順書](extension-acceptance-test.md) に従い手動 UAT を実施する。

## 8. 関連

- [はじめに](getting-started.md)
- [Bridge マニュアル](bridge-manual.md)
- [CLI マニュアル](cli-manual.md) — `omomuki serve`
- [評価マニュアル](evaluation-manual.md) — Level 2 judge
- [Dogfood 手順書](dogfood-walkthrough.md)
- [CLI / Bridge 設計](cli-chrome-extension.md)
- [Security Design](security.md)
