# Chrome Extension 受け入れテスト手順書

Omomuki Chrome Extension の **手動受け入れテスト（UAT）** 手順である。  
自動テスト（`npm run build` / pytest）を補完し、Bridge・ブラウザ DOM・popup UI の結合を確認する。

**対象バージョン**: Omomuki **0.5.4** 以降（Candidate evaluate/approve popup 含む）  
**所要時間の目安**: 30〜45 分（Level 2 評価を含む場合は +10 分）

関連: [Extension マニュアル](extension-manual.md) / [Dogfood 手順書](dogfood-walkthrough.md)

---

## 1. テスト環境

| 項目 | 推奨値 |
|------|--------|
| OS | macOS / Linux / Windows（いずれか） |
| ブラウザ | Google Chrome 最新安定版 |
| Omomuki | `pip install -e ".[dev]"` 済み、`omomuki --version` が 0.5.4+ |
| Bridge | `omomuki serve` を**別ターミナルで常駐** |
| ネットワーク | ローカルのみ（`127.0.0.1:38741`） |
| 任意（L2） | Ollama 起動、`OMOMUKI_JUDGE_MODEL` 設定済み |

### 1.1 事前セットアップ（実施者）

```bash
cd /path/to/omomuki
pip install -e ".[dev]"
omomuki init

# ターミナル A
omomuki serve

# ターミナル B（ビルド）
cd extension && npm install && npm run build
```

Chrome → **拡張機能** → **デベロッパーモード** → **パッケージ化されていない拡張機能を読み込む** → リポジトリの `extension/` フォルダを指定。

### 1.2 テスト用ページ

| 用途 | URL / ページ |
|------|----------------|
| Capture（選択・ページ） | 任意の HTTPS ページ（例: `https://example.com`） |
| Insert ChatGPT | `https://chatgpt.com` または `https://chat.openai.com` の新規チャット |
| Insert Claude | `https://claude.ai` の新規チャット |

### 1.3 記録欄

| 実施日 | 実施者 | Chrome 版 | Omomuki 版 | 結果 |
|--------|--------|-----------|------------|------|
| | | | | ☐ Pass / ☐ Fail |

---

## 2. 前提条件チェック（PRE）

実施前にすべて **OK** であること。

| ID | 確認内容 | 期待結果 | 結果 |
|----|----------|----------|------|
| PRE-01 | `curl -s http://127.0.0.1:38741/health` | HTTP 200 | ☐ |
| PRE-02 | `~/.omomuki/bridge.token` が存在する | ファイルあり | ☐ |
| PRE-03 | `omomuki profile inspect` | default 等の Profile 表示 | ☐ |
| PRE-04 | `extension/dist/` がビルド済み | `npm run build` 成功後 | ☐ |
| PRE-05 | Extension が Chrome に読み込まれている | 拡張機能一覧に Omomuki 表示 | ☐ |

---

## 3. Options / ペアリング（OPT）

| ID | 手順 | 期待結果 | 結果 | 備考 |
|----|------|----------|------|------|
| OPT-01 | popup → **Options / Pairing** | Options ページが開く | ☐ | |
| OPT-02 | Bridge URL に `http://127.0.0.1:38741`、Bearer token に `bridge.token` の内容を貼り付け → **Save** | `Saved.` と表示 | ☐ | |
| OPT-03 | **Test /health** をクリック | `Bridge /health OK` | ☐ | 失敗時は PRE-01 を再確認 |
| OPT-04 | Default profile id を `default` に設定して Save | 保存成功 | ☐ | 複数 Profile がある場合は実在 ID |

**CLI 照合（任意）**:

```bash
TOKEN=$(cat ~/.omomuki/bridge.token)
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:38741/profiles | python3 -m json.tool
```

---

## 4. Popup 基本（POP）

| ID | 手順 | 期待結果 | 結果 | 備考 |
|----|------|----------|------|------|
| POP-01 | 任意タブで Extension アイコン → popup 表示 | タイトル「Omomuki」、ステータス行あり | ☐ | |
| POP-02 | Bridge 起動済みの状態で popup を開く | ステータス **Bridge connected**（赤文字でない） | ☐ | |
| POP-03 | Profile ドロップダウン | `omomuki init` の Profile が 1 件以上表示 | ☐ | 0 件の場合は `default (not found)` でも可 |
| POP-04 | Bridge を停止した状態で popup を再表示 | **Bridge unreachable. Run: omomuki serve**（赤） | ☐ | 負荷テスト後は `serve` を再開 |

---

## 5. Capture（CAP）

**テストデータ**: ページ上で次の英文を**ドラッグ選択**してから実施する。

```text
Omomuki acceptance test capture — explicit uncertainty and local-first portability.
```

| ID | 手順 | 期待結果 | 結果 | 備考 |
|----|------|----------|------|------|
| CAP-01 | 上記テキストを選択 → **Capture selection** | ステータス `Captured: <uuid>` | ☐ | |
| CAP-02 | Candidate ドロップダウン | 直後に当該 ID（先頭 8 文字…）が選択されている | ☐ | |
| CAP-03 | 選択なしで **Capture selection** | エラー表示（例: No text selected） | ☐ | 負例 |
| CAP-04 | `https://example.com` で **Capture this page** | `Captured: <uuid>`、Candidate に追加 | ☐ | ページ要約が content になる |

**CLI 照合**:

```bash
omomuki candidate list
# 直近の id が CAP-01 / CAP-04 と一致すること
```

---

## 6. Candidate 評価・merge（CND）

CAP-01 で作成した Candidate を対象とする（ドロップダウンで選択済みであること）。

| ID | 手順 | 期待結果 | 結果 | 備考 |
|----|------|----------|------|------|
| CND-01 | **Refresh** | ステータス `Candidates refreshed`、一覧に複数件表示可 | ☐ | |
| CND-02 | Eval level **Level 1** → **Evaluate** | ステータス `Evaluated: <RDE class> (L1)` 等 | ☐ | 例: Compatible Enrichment |
| CND-03 | **Show diff** | popup 内に JSON diff（`add` / `already_present` 等） | ☐ | `add` が空でも失敗ではない |
| CND-04 | **Approve** | ステータス `Approved: <id>…`、Candidate の status が変化 | ☐ | Critical で 400 の場合は CND-06 へ |
| CND-05 | 新規 capture → **Reject** | `Rejected: …`、CLI で rejected 状態 | ☐ | CAP-01 とは別 ID で可 |
| CND-06 | （任意）Critical Distortion の Candidate で Approve | エラー表示（Bridge 400） | ☐ | Extension は `--force-critical` 非対応 |

**CLI 照合**:

```bash
omomuki candidate show <id>
omomuki candidate lineage --profile-id default
```

### 6.1 Level 2 評価（任意・CND-L2）

Bridge ホストで Ollama 等を設定している場合のみ。

| ID | 手順 | 期待結果 | 結果 | 備考 |
|----|------|----------|------|------|
| CND-L2-01 | 新規 capture（未評価） | — | ☐ | |
| CND-L2-02 | Eval level **Level 2** → **Evaluate** | 成功または judge 接続エラーが明確 | ☐ | 404 時は `OMOMUKI_JUDGE_MODEL` を確認 |
| CND-L2-03 | `omomuki candidate show <id>` | `evaluation.llm_review` が非 null（成功時） | ☐ | [評価マニュアル](evaluation-manual.md) |

---

## 7. Context 挿入（INS）

Profile ドロップダウンで **default**（または有効な Profile）を選択。

### 7.1 ChatGPT

| ID | 手順 | 期待結果 | 結果 | 備考 |
|----|------|----------|------|------|
| INS-CG-01 | ChatGPT の**新規チャット**を開き、入力欄が表示されている | — | ☐ | |
| INS-CG-02 | popup → **Insert context (ChatGPT)** | ステータス `Inserted (chatgpt)` | ☐ | |
| INS-CG-03 | 入力欄の内容 | Omomuki の system/user 形式テキストが入っている | ☐ | 上書きではなく追記の場合あり |
| INS-CG-04 | 非 ChatGPT ページで Insert (ChatGPT) | エラー（`SITE_MISMATCH` 等） | ☐ | 負例 |

### 7.2 Claude

| ID | 手順 | 期待結果 | 結果 | 備考 |
|----|------|----------|------|------|
| INS-CL-01 | Claude の**新規チャット**を開く | — | ☐ | |
| INS-CL-02 | **Insert context (Claude)** | `Inserted (claude)` | ☐ | |
| INS-CL-03 | 入力欄の内容 | コンテキスト本文が挿入されている | ☐ | |
| INS-CL-04 | DOM 変更で `INPUT_NOT_FOUND` になった場合 | エラーメッセージに code / hint | ☐ | `extension/src/sites/claude.ts` 要更新 |

---

## 8. セキュリティ・責務境界（SEC）

| ID | 確認内容 | 期待結果 | 結果 |
|----|----------|----------|------|
| SEC-01 | Extension から Profile YAML を直接編集する UI がない | 該当操作不可 | ☐ |
| SEC-02 | Bearer token は Options のみ（popup に平文表示されない） | popup に token 欄なし | ☐ |
| SEC-03 | 誤った token で capture | `401` 相当のエラー表示 | ☐ |
| SEC-04 | capture は Candidate 作成のみ（即 merge しない） | Approve 前に `omomuki profile inspect` で概念が増えない | ☐ |

---

## 9. リグレッション（ビルド後）

ソース変更後、受け入れテストの**サブセット**を再実施する。

| 変更箇所 | 最低限再実施する ID |
|----------|---------------------|
| `extension/src/bridge-client.ts` | PRE, OPT-03, POP-02, CAP-01, CND-02 |
| `extension/src/popup.ts` / `popup.html` | POP-01〜03, CAP-01〜02, CND-01〜04 |
| `extension/src/sites/*` | INS-CG-02〜03, INS-CL-02〜03 |
| `extension/src/background.ts` | CAP-01, CND-02, INS-CG-02 |
| `extension/src/content.ts` | CAP-01, CAP-04, INS-CG-02 |

```bash
cd extension && npm run build
# Chrome 拡張機能ページで「更新」ボタン
```

---

## 10. 合否判定

| 区分 | 必須 ID | 備考 |
|------|---------|------|
| **必須 Pass** | PRE-01〜05, OPT-01〜03, POP-01〜03, CAP-01〜02, CND-01〜04, INS-CG-02, INS-CL-02, SEC-01〜02 | |
| **任意** | CAP-03〜04, CND-05〜06, CND-L2-*, INS-*-04, SEC-03〜04 | 環境・DOM 依存 |
| **Fail** | 必須のいずれか 1 件でも NG | Issue 起票・再テスト |

### 10.1 既知の許容事項

| 現象 | 判定 |
|------|------|
| `diff.add` が空 / `already_present: true` | **Pass**（Profile に同内容が既にある） |
| Level 2 が未設定で judge エラー | CND-L2 は **Skip**（必須ではない） |
| ChatGPT/Claude の DOM 変更で Insert 失敗 | **Fail**（サイトアダプタ更新が必要） |

---

## 11. トラブル時の切り分け

| 症状 | 確認コマンド / 対処 |
|------|---------------------|
| Bridge unreachable | `omomuki serve`、Options URL |
| capture 401 | token 再コピー、`curl` で `/capture` 試行 |
| Candidate 一覧が空 | `omomuki candidate list`、**Refresh** |
| Approve 400 | `omomuki candidate show <id>` の RDE class、CLI で diff 確認 |
| Insert 失敗 | 対象サイトか、DevTools Console の content script エラー |

---

## 12. 関連ドキュメント

- [Extension マニュアル](extension-manual.md)
- [Bridge マニュアル](bridge-manual.md)
- [評価マニュアル](evaluation-manual.md)
- [Dogfood 手順書](dogfood-walkthrough.md) — CLI 中心の E2E
