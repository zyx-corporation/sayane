# Chrome Extension マニュアル

> 現行方針: Chrome Extension は **freeze / deprecated** である。既存利用者向けの互換導線として維持するが、新機能の主対象ではない。新規導入では CLI / MCP Server / Local Bridge を優先する。

Phase 3 の Sayane Chrome Extension は **補助 UI** ではあるが、**人間↔Sayane の実行境界**として LLM チャットと同格に重要である。判断・保存・merge の本体は Core / Bridge 側だが、入出力の意味を UI が伝えられなければパイプラインは成立しない。

**UI の基本コンセプト**（実行要素としての位置づけ、busy / unavailable、カーソル）: [ui-design-principles.md](ui-design-principles.md)

## 1. 前提

1. `sayane init` で Profile Store を作成
2. `sayane serve` で Local Bridge を起動（`127.0.0.1:38741`）
3. Extension Options に Bridge URL と Bearer token を設定（`~/.sayane/bridge.token`）

### 権限について

- **履歴は読まない**。Chrome 日本語 UI で「閲覧履歴の読み取り」と出る場合は旧 `tabs` 権限の表示であり、本 Extension は履歴 API を使わない。
- **Capture** は `activeTab` + `scripting` で、ツールバーから Extension を開いた**現在のタブ**の選択テキストのみ読み取る。
- **Insert** は ChatGPT / Claude / Gemini / DeepSeek / Open WebUI 等、`host_permissions` に列挙したサイト、または localhost Open WebUI。
- manifest 更新後は Chrome の「更新」だけでは権限表示が変わらないことがある。**削除してから Load unpacked し直す**。

## 2. インストール

### 2.1 GitHub Release zip 版（推奨）

Zenn 記事の読者や一般利用者は、GitHub Release から zip をダウンロードして読み込む方法を推奨する。

1. [GitHub Releases](https://github.com/zyx-corporation/sayane/releases) から `sayane-extension-vX.Y.Z.zip` をダウンロード
2. zip を展開（`sayane-extension-vX.Y.Z/` ディレクトリができる）
3. `chrome://extensions/` を開く
4. **デベロッパーモード** を有効化
5. 「**パッケージ化されていない拡張機能を読み込む**」→ 展開したディレクトリを選択

**チェックサム確認（任意）:**

```bash
shasum -a 256 -c sayane-extension-vX.Y.Z.zip.sha256
```

**注意:**

- この拡張は **Chrome Web Store 版ではありません**。GitHub Release から取得した zip のみを使ってください。
- 選択範囲をローカルブリッジ（`127.0.0.1:38741`）へ送ります。外部クラウドへ直接送信しません。
- Capture はプロファイルへの即時反映ではなく、更新候補の作成です。

### 2.2 開発者向けビルド

Extension を改修する開発者は、リポジトリからビルドする。

```bash
git clone https://github.com/zyx-corporation/sayane.git
cd sayane/extension
npm install
npm run build
```

Chrome の「パッケージ化されていない拡張機能を読み込む」→ `extension/` ディレクトリ。

### 2.3 Release zip のビルド（メンテナ向け）

```bash
cd extension
npm run package
```

`release/sayane-extension-vX.Y.Z.zip` と `.sha256` が生成される。

## 2.1 表示言語（i18n）

popup / Options の UI 文言は **英語（既定）** と **日本語** に対応する。

1. **Options** → **表示言語**（Display language）
   - **自動（ブラウザ）** — `navigator.language` が `ja` なら日本語、それ以外は英語
   - **English** / **日本語** — 固定
2. **Save** で `chrome.storage.sync` に保存（CLI の `SAYANE_LANG` とは独立）
3. 言語を変更したら popup を開き直す

カタログ: `extension/locale/en.json`, `extension/locale/ja.json`。実装: `extension/src/i18n.ts`。

## 3. Popup 操作

| ボタン | 動作 |
|--------|------|
| Capture selection | 選択テキスト → Bridge `/capture`（Candidate） |
| Capture this page | ページ要約 → `/capture` |
| Insert context (ChatGPT) | `/context-packet?target=chatgpt` → 入力欄へ挿入 |
| Insert context (Claude) | `target=claude` で同様 |
| Insert context (Gemini / DeepSeek) | 各 provider 向け compile + DOM insert |
| Insert context (Open WebUI) | `target=local-openwebui` — localhost Open WebUI（例: `http://localhost:3000/`） |
| Insert context (preview) | `local-custom` のみ — Bridge compile 未対応 |
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
| `INPUT_NOT_FOUND` | LLM 入力欄のセレクタ不一致（DOM 変更）— `extension/src/providers/` を更新 |
| `SITE_MISMATCH` | 適切なサイトでないのに挿入を試行 |
| `UNSUPPORTED_SITE` | 未対応ホスト |

アダプタ定義: `extension/src/providers/`（`registry.ts`）。旧 `src/sites/*` は re-export のみ。

### Open WebUI（local-openwebui）

1. Open WebUI を起動（例: Docker → `http://localhost:3000/`）
2. ログイン後、**Open WebUI タブをアクティブ**にする
3. `sayane serve` 常駐 + Extension Options で token 設定
4. popup → **Insert context (Open WebUI)**

zsh で CLI を使う場合: `pip install "sayane==1.0.12"`（`==` はクォート推奨）。

| 症状 | 対処 |
|------|------|
| `SITE_MISMATCH` | Open WebUI タブがアクティブか、URL が `/auth` でないか |
| `INPUT_NOT_FOUND` | チャット画面を開き直す · Extension 0.3.8+ |

## 5. 責任の限界

Extension は行わない:

- Profile YAML の直接編集
- LLM judge の設定（`judge.yaml` / 環境変数は Bridge ホスト側）
- API key の永続保存

## 6. トラブルシューティング

| 症状 | 対処 |
|------|------|
| Bridge unreachable | `sayane serve` 起動、Options の URL/port |
| `401` / capture 失敗 | Bearer token を `~/.sayane/bridge.token` からコピー |
| `INPUT_NOT_FOUND` | ChatGPT/Claude/Open WebUI の DOM 変更。`extension/src/providers/` を更新 |
| 選択 capture でテキストなし | ページ上でテキストを選択してから実行 |
| `Receiving end does not exist` | `https://example.com` 等の通常ページを開き、Extension 更新後はタブを再読み込み（F5） |

## 7. 受け入れテスト

リリース前・popup / サイトアダプタ変更後は [Chrome Extension 受け入れテスト手順書](extension-acceptance-test.md) に従い手動 UAT を実施する。

## 8. 関連

- [**UI 設計の基本コンセプト**](../docs/ui-design-principles.md) — busy / unavailable、カーソル
- [はじめに](getting-started.md)
- [Bridge マニュアル](bridge-manual.md)
- [CLI マニュアル](cli-manual.md) — `sayane serve`
- [評価マニュアル](evaluation-manual.md) — Level 2 judge
- [Dogfood 手順書](dogfood-walkthrough.md)
- [CLI / Bridge 設計](cli-chrome-extension.md)
- [Security Design](security.md)
