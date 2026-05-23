# Chrome Extension 受け入れテスト手順書

Omomuki Chrome Extension の **手動受け入れテスト（UAT）** 手順である。  
自動テスト（`npm run build` / pytest）を補完し、Bridge・ブラウザ DOM・popup UI の結合を確認する。

| 項目 | 値 |
|------|-----|
| **Omomuki** | **0.5.6** 以降（`omomuki --version`） |
| **Extension manifest** | **0.3.1** 以降 |
| **所要時間** | 30〜45 分（Level 2 評価を含む場合は +10 分） |

関連: [Extension マニュアル](extension-manual.md) / [Dogfood 手順書](dogfood-walkthrough.md)

### 実装メモ（0.5.6 / Extension 0.3.1）

| 操作 | 方式 |
|------|------|
| Bridge API（Profile / Candidate / capture 保存） | Service Worker → `bridge-client.ts` |
| **Capture**（選択・ページ） | `chrome.scripting.executeScript`（`activeTab`） |
| **Insert**（ChatGPT / Claude） | 同上（サイト別セレクタを in-page 実行） |
| Options **Test connection** | `/health` + Bearer 付き `/profiles` |
| content script `sendMessage` | **使わない**（旧版で `Receiving end does not exist` の原因） |

**共通ルール**: 操作対象のタブを前面にした状態で **Extension アイコンをクリック** してから popup でボタンを押す（`activeTab` はそのタブにのみ有効）。

### 結果の記入方法

各テストケースの **結果** 列に次のいずれかを記入する。

| 記号 | 意味 |
|------|------|
| **P** | Pass（期待どおり） |
| **F** | Fail（期待と異なる・未実施） |
| **S** | Skip（任意項目で未実施） |
| **N/A** | 対象外（環境に LLM サイトがない等） |

**実測・メモ** 列には、popup に表示された文言・Candidate ID・エラー全文など、後から再現できる情報を書く。

---

## 0. 結果記録シート（全項目）

実施後にこの表を埋める。詳細手順は各 § を参照。

| ID | 区分 | 必須 | 結果 | 実測・メモ |
|----|------|:----:|:----:|------------|
| PRE-01 | 前提 | ✓ | | |
| PRE-02 | 前提 | ✓ | | |
| PRE-03 | 前提 | ✓ | | |
| PRE-04 | 前提 | ✓ | | |
| PRE-05 | 前提 | ✓ | | |
| OPT-01 | Options | | | |
| OPT-02 | Options | ✓ | | |
| OPT-03 | Options | ✓ | | |
| OPT-03b | Options | ✓ | | |
| OPT-04 | Options | ✓ | | |
| OPT-05 | Options i18n | | | |
| POP-01 | Popup | ✓ | | |
| POP-02 | Popup | ✓ | | |
| POP-03 | Popup | ✓ | | |
| POP-04 | Popup | | | |
| CAP-01 | Capture | ✓ | | |
| CAP-02 | Capture | ✓ | | |
| CAP-03 | Capture | | | |
| CAP-04 | Capture | | | |
| CND-01 | Candidate | ✓ | | |
| CND-02 | Candidate | ✓ | | |
| CND-03 | Candidate | ✓ | | |
| CND-04 | Candidate | ✓ | | |
| CND-05 | Candidate | | | |
| CND-06 | Candidate | | | |
| CND-L2-01 | Candidate L2 | | | |
| CND-L2-02 | Candidate L2 | | | |
| CND-L2-03 | Candidate L2 | | | |
| INS-CG-01 | Insert CG | | | |
| INS-CG-02 | Insert CG | ✓ | | |
| INS-CG-03 | Insert CG | | | |
| INS-CG-04 | Insert CG | | | |
| INS-CL-01 | Insert CL | | | |
| INS-CL-02 | Insert CL | ✓ | | |
| INS-CL-03 | Insert CL | | | |
| INS-CL-04 | Insert CL | | | |
| SEC-01 | Security | ✓ | | |
| SEC-02 | Security | ✓ | | |
| SEC-03 | Security | | | |
| SEC-04 | Security | | | |

**合計判定**（§10）: ☐ Pass（必須がすべて P） / ☐ Fail

---

## 1. テスト環境

| 項目 | 推奨値 |
|------|--------|
| OS | macOS / Linux / Windows（いずれか） |
| ブラウザ | Google Chrome 最新安定版 |
| Omomuki | `pip install -e ".[dev]"` 済み、`omomuki --version` → `omomuki 0.5.6` |
| Bridge | `omomuki serve` を**別ターミナルで常駐** |
| ネットワーク | ローカルのみ（`127.0.0.1:38741`） |
| 任意（L2） | Ollama 起動、`OMOMUKI_JUDGE_MODEL` 設定済み |

### 1.0 Extension の権限（Chrome 日本語 UI・0.3.1）

| 権限 / 表示 | 用途 |
|-------------|------|
| **サイトへのアクセス** | `host_permissions`（Bridge・ChatGPT・Claude） |
| `storage` | Options の URL / token 保存 |
| `activeTab` + `scripting` | **アイコンを押したタブ**での Capture / Insert |

**含まれないもの**: `tabs` 権限、`<all_urls>` への常時 content script、履歴 API。

`example.com` 等は「自動許可サイト」一覧に**出なくてよい**。Capture は `activeTab` で動作する。

manifest 更新後、「新しい権限」ダイアログが出ないことがある。**拡張機能を削除 → `extension/` を再読み込み**で表示と挙動を揃える。

### 1.1 事前セットアップ（実施者）

```bash
cd /path/to/omomuki
git pull
pip install -e ".[dev]"
omomuki --version    # omomuki 0.5.6
omomuki init

# ターミナル A
omomuki serve

# ターミナル B
cd extension && npm install && npm run build
```

Chrome → **拡張機能** → **デベロッパーモード** → **パッケージ化されていない拡張機能を読み込む** → `extension/` フォルダ。

### 1.2 テスト用ページ

| 用途 | URL / ページ |
|------|----------------|
| Capture（選択・ページ） | `https://example.com` 等の **https://** 通常ページ |
| Insert ChatGPT | `https://chatgpt.com` または `https://chat.openai.com` の**新規チャット** |
| Insert Claude | `https://claude.ai` の**新規チャット** |

**不可**: `chrome://`、新規タブ、PDF ビューア、Chrome Web Store、Extension 管理ページ。

### 1.3 実施メタデータ

| 項目 | 記入 |
|------|------|
| 実施日 | |
| 実施者 | |
| Chrome 版 | |
| Omomuki 版 | 0.5.6 |
| Extension 版 | 0.3.1 |
| git commit / PR | |
| 総合判定 | ☐ Pass / ☐ Fail |
| 備考 | |

---

## 2. 前提条件チェック（PRE）

実施前にすべて **OK** であること。

| ID | 確認内容 | 期待結果 | 結果 | 実測・メモ |
|----|----------|----------|:----:|------------|
| PRE-01 | `curl -s http://127.0.0.1:38741/health` | HTTP 200 | | |
| PRE-02 | `~/.omomuki/bridge.token` が存在する | ファイルあり | | |
| PRE-03 | `omomuki profile inspect` | default 等の Profile 表示 | | |
| PRE-04 | `extension/dist/` がビルド済み | `npm run build` 成功後 | | |
| PRE-05 | Extension が Chrome に読み込まれている | 拡張機能一覧に Omomuki **0.3.1** | | |

---

## 3. Options / ペアリング（OPT）

| ID | 手順 | 期待結果 | 結果 | 実測・メモ |
|----|------|----------|:----:|------------|
| OPT-01 | popup → **Options / Pairing** | Options ページが開く | | |
| OPT-02 | Bridge URL + token → **Save** | `Saved.` | | |
| OPT-03 | token 空で **Test connection** | `Bearer token not configured` | | |
| OPT-03b | token ありで **Test connection** | `Bridge OK (/health + /profiles)` | | **必須** |
| OPT-04 | Default profile id = `default` → Save | 保存成功 | | |
| OPT-05 | **表示言語** を 日本語 → Save → popup 再表示 | ボタン・ステータスが日本語 | | 任意 |

**CLI 照合（任意）**:

```bash
TOKEN=$(cat ~/.omomuki/bridge.token)
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:38741/profiles | python3 -m json.tool
```

---

## 4. Popup 基本（POP）

| ID | 手順 | 期待結果 | 結果 | 実測・メモ |
|----|------|----------|:----:|------------|
| POP-01 | Extension アイコン → popup | 「Omomuki」、ステータス行 | | |
| POP-02 | Bridge 起動済み | **Bridge connected** | | |
| POP-03 | Profile ドロップダウン | 1 件以上 | | 例: `default — Your Name` |
| POP-04 | Bridge 停止後 | **Bridge unreachable…** | | 任意 |

---

## 5. Capture（CAP）

1. **`https://example.com` を開く**（前面）
2. **Extension アイコン**で popup を開く
3. 下記テキストを**選択**して **Capture selection**

```text
Omomuki acceptance test capture — explicit uncertainty and local-first portability.
```

| ID | 手順 | 期待結果 | 結果 | 実測・メモ |
|----|------|----------|:----:|------------|
| CAP-01 | 選択 → **Capture selection** | `Captured: <uuid>` | | Candidate ID: |
| CAP-02 | Candidate ドロップダウン | 当該 ID が自動選択 | | |
| CAP-03 | 選択なしで Capture | `No text selected` 等 | | 任意 |
| CAP-04 | **Capture this page** | `Captured: <uuid>` | | 任意 |

**CLI 照合**:

```bash
omomuki candidate list
```

---

## 6. Candidate 評価・merge（CND）

CAP-01 の Candidate を対象（ドロップダウンで選択）。

| ID | 手順 | 期待結果 | 結果 | 実測・メモ |
|----|------|----------|:----:|------------|
| CND-01 | **Refresh** | `Candidates refreshed` | | |
| CND-02 | Level 1 → **Evaluate** | `Evaluated: … (L1)` | | RDE class: |
| CND-03 | **Show diff** | popup 内に JSON | | `add` 空でも可 |
| CND-04 | **Approve** | `Approved: …` | | |
| CND-05 | 別 ID で **Reject** | `Rejected: …` | | 任意 |
| CND-06 | Critical で Approve | Bridge 400 | | 任意 |

### 6.1 Level 2（任意・CND-L2）

Ollama 等が Bridge 側で設定されている場合のみ。[評価マニュアル](evaluation-manual.md) 参照。

| ID | 手順 | 期待結果 | 結果 | 実測・メモ |
|----|------|----------|:----:|------------|
| CND-L2-01 | 新規 capture | — | | |
| CND-L2-02 | Level 2 → **Evaluate** | 成功 or 明確な judge エラー | | |
| CND-L2-03 | `omomuki candidate show <id>` | `llm_review` 非 null（成功時） | | |

---

## 7. Context 挿入（INS）

Profile = **default**（または有効な Profile）。

**共通**: **LLM サイトのタブ**を前面 → Extension アイコン → popup から Insert。

### 7.1 ChatGPT

| ID | 手順 | 期待結果 | 結果 | 実測・メモ |
|----|------|----------|:----:|------------|
| INS-CG-01 | 新規チャット、入力欄表示 | — | | |
| INS-CG-02 | **Insert context (ChatGPT)** | `Inserted (chatgpt)` | | **必須** |
| INS-CG-03 | 入力欄の内容 | 文脈テキストあり | | 先頭数十文字: |
| INS-CG-04 | 非 ChatGPT で Insert | `SITE_MISMATCH` 等 | | 任意 |

### 7.2 Claude

| ID | 手順 | 期待結果 | 結果 | 実測・メモ |
|----|------|----------|:----:|------------|
| INS-CL-01 | 新規チャットを開く | — | | |
| INS-CL-02 | **Insert context (Claude)** | `Inserted (claude)` | | **必須** |
| INS-CL-03 | 入力欄の内容 | 文脈テキストあり | | |
| INS-CL-04 | `INPUT_NOT_FOUND` 時 | code / hint | | 任意 |

---

## 8. セキュリティ・責務境界（SEC）

| ID | 確認内容 | 期待結果 | 結果 | 実測・メモ |
|----|----------|----------|:----:|------------|
| SEC-01 | Profile YAML 直接編集 UI なし | 不可 | | |
| SEC-02 | token は Options のみ | popup に token 欄なし | | |
| SEC-03 | 誤 token で capture | 401 相当 | | 任意 |
| SEC-04 | capture は即 merge しない | Approve 前に概念不増 | | 任意 |

---

## 9. リグレッション（Extension 変更後）

```bash
cd extension && npm run build
# Chrome → Omomuki → 更新（manifest 変更時は削除→再読み込み）
```

| 変更箇所 | 最低限再実施 |
|----------|--------------|
| `extension/src/options.ts` | OPT-02, OPT-03, OPT-03b |
| `extension/src/bridge-client.ts` | OPT-03b, POP-02, CND-02 |
| `extension/src/content-script-client.ts` | CAP-01, CAP-04, INS-CG-02, INS-CL-02 |
| `extension/src/popup.ts` / `popup.html` | POP-01〜03, CAP-01〜02, CND-01〜04 |
| `extension/src/sites/*` | INS-CG-02〜03, INS-CL-02〜03 |
| `extension/manifest.json` | PRE-05, OPT-03b, CAP-01, INS-CG-02, INS-CL-02 |

---

## 10. 合否判定

| 区分 | ID |
|------|-----|
| **必須 Pass** | PRE-01〜05, OPT-02, OPT-03, OPT-03b, OPT-04, POP-01〜03, CAP-01〜02, CND-01〜04, INS-CG-02, **INS-CL-02**, SEC-01〜02 |
| **任意** | CAP-03〜04, CND-05〜06, CND-L2-*, INS-CG-03〜04, INS-CL-01, INS-CL-03〜04, SEC-03〜04, POP-04 |
| **Fail** | 必須のいずれか NG → Issue 起票・再テスト |

### 10.1 既知の許容事項

| 現象 | 判定 |
|------|------|
| `diff.add` が空 / `already_present: true` | **Pass** |
| Level 2 judge 未設定 | CND-L2 は **Skip** |
| ChatGPT/Claude DOM 変更で `INPUT_NOT_FOUND` | **Fail**（`extension/src/sites/` 更新） |

### 10.2 サインオフ

| 役割 | 氏名 | 日付 | 署名 |
|------|------|------|------|
| 実施者 | | | |
| レビュー | | | |

### 10.3 記入例（参考）

| ID | 結果 | 実測・メモ（例） |
|----|:----:|------------------|
| CAP-01 | P | `Captured: 6874f8f2-…` |
| CND-02 | P | `Evaluated: Compatible Enrichment (L1)` |
| INS-CG-02 | P | `Inserted (chatgpt)` |
| INS-CG-04 | P | `SITE_MISMATCH — Page does not match adapter chatgpt` |
| INS-CL-02 | | （未実施なら空欄のまま） |

---

## 11. トラブル時の切り分け

| 症状 | 対処 |
|------|------|
| Options の Save / Test が無反応 | `npm run build` + 拡張機能**更新**。0.5.5 以前は Options ボタン型バグ |
| Test OK だが token 空 | 0.5.6 未満の旧 Extension。`git pull` して再ビルド |
| `Bridge token not configured`（popup） | Options で token 保存 → popup 開き直し |
| `Bridge unreachable` | `omomuki serve` |
| Capture / Insert 全般が動かない | **対象タブで**アイコンから popup を開く（`activeTab`） |
| `Receiving end does not exist`（0.5.5 以前） | 0.5.6+ に更新。CAP/Insert は `executeScript` 方式に変更済み |
| `SITE_MISMATCH` | 対応サイトのタブで Insert（ChatGPT 用ボタンは ChatGPT で） |
| `INPUT_NOT_FOUND` | `extension/src/sites/chatgpt.ts` / `claude.ts` のセレクタ更新 |
| capture 401 | token 再コピー |
| Approve 400 | RDE class 確認、`omomuki candidate diff` |

---

## 12. 変更履歴（手順書）

| 日付 | 版 | 内容 |
|------|-----|------|
| 2026-05-23 | 0.5.6 / Ext 0.3.1 | 結果記録シート（§0）・実測メモ列・記入例を追加 |
| 2026-05-23 | 0.5.6 / Ext 0.3.1 | UAT 反映: Test connection、executeScript Capture/Insert、権限整理 |
| 2026-05-23 | 0.5.4 | 初版（Candidate popup、受け入れテスト新設） |

---

## 13. 関連ドキュメント

- [Extension マニュアル](extension-manual.md)
- [Bridge マニュアル](bridge-manual.md)
- [評価マニュアル](evaluation-manual.md)
- [Dogfood 手順書](dogfood-walkthrough.md)
