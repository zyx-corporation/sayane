# 受け入れテスト — 手動のみシナリオ（#93）

pytest / Playwright では代替できない、または代替すべきでないシナリオの境界を固定する。

| 項目 | 値 |
|------|-----|
| **関連 Issue** | [#93](https://github.com/zyx-corporation/sayane/issues/93) 本書 · [#88](https://github.com/zyx-corporation/sayane/issues/88) L2 Core · [#89](https://github.com/zyx-corporation/sayane/issues/89) L3 Extension |
| **自動化済み** | [#92](https://github.com/zyx-corporation/sayane/issues/92) L1 pytest · [#91](https://github.com/zyx-corporation/sayane/issues/91) Extension Playwright E2E |

正本の三層定義: [acceptance-spec.md](acceptance-spec.md)

---

## 1. 手動に残す理由（分類）

| 分類 | 理由 | 例 |
|------|------|-----|
| **外部 DOM** | 第三者サイト UI が変わる。PR 必須 CI は flake | 実 ChatGPT / Claude Insert |
| **人間可読 UX** | 文言・レイアウトは assert だけでは不十分 | 日本語ヘルプの自然さ、popup 表示 |
| **環境依存** | 実 vault / OS / ファイアウォール | 本番 Obsidian vault、Windows PATH |
| **運用記録** | サインオフ・証跡 | L2/L3 記録シートの P/F |
| **任意機能** | 未設定時 Skip が正しい | Level 2 LLM judge（Ollama） |
| **初回体験** | 開発者マシンでのセットアップ体感 | `sayane serve` 常駐 + Options ペアリング |

---

## 2. L1 / Playwright で代替済み（L2 必須から除外）

[#92](https://github.com/zyx-corporation/sayane/issues/92) / [#91](https://github.com/zyx-corporation/sayane/issues/91) 完了後、次は **L2 必須ではない**（CI の L1 / scheduled E2E で足りる）。

| 旧 L2 ID | 内容 | L1 / E2E 根拠 |
|----------|------|----------------|
| CLI-M01〜03 | profile inspect / compile | `tests/test_cli.py` |
| STOR-M01 | `storage backend status` | `tests/test_storage_backend.py`, `test_acceptance_cli.py` |
| CAND-M01 | capture → evaluate → diff → approve | `tests/test_bridge_api.py`, `tests/test_acceptance_cli.py` |
| CAND-M02 | Critical approve 拒否 | `tests/test_critical_merge.py`, `test_acceptance_cli.py`, `test_bridge_api.py` |
| CAND-M03 | lineage | `tests/test_acceptance_cli.py`（任意） |
| BRG-M01 | `/health` | `tests/test_bridge_api.py` |
| BRG-M02 | 401 without token | `tests/test_bridge_api.py` |
| BRG-M03 | capture → approve 一連 | `tests/test_bridge_api.py` |
| MCP-M01 | mcp list-profiles / inspect | `tests/test_mcp_cli.py`, `tests/test_acceptance_cli.py` |
| SEC-M01 | 誤 token → 401 | `tests/test_bridge_api.py` |
| SEC-M02 | approve 前に merge されない | `tests/test_acceptance_cli.py` |
| INS-CG-02 / INS-CL-02（DOM 挿入） | Insert ロジック | `extension/e2e/`（モック DOM）· [extension-e2e.md](extension-e2e.md) |

`cli-acceptance-test.md` の ERR / CAND / STOR / MCP / PLG 多くは同様に L1 化済み（§1.4 参照）。

---

## 3. L2 Core 手動が必要なもの（[#88](https://github.com/zyx-corporation/sayane/issues/88)）

| 優先 | ID | 理由 | 備考 |
|:----:|-----|------|------|
| P0 | **PRE-M01** | リリース担当者が L1 green を確認 | CI と同じ `pytest -q`（専用 venv 推奨） |
| P1 | **SERVE-M01** | `sayane serve` 常駐 + 実 token で smoke | 下記 §3.1 |
| P2 | **STOR-M02** | 実ファイル追加後の **メッセージ**目視 | entries 件数は L1 |
| P2 | **記録シート** | [acceptance-spec.md §4.0](acceptance-spec.md) の P/F 記入 | サインオフ証跡 |

### 3.1 SERVE-M01（新規・L2 最小 smoke）

| 手順 | 期待結果 |
|------|----------|
| ターミナル A: `sayane serve` | `http://127.0.0.1:38741` で待ち受け |
| `curl -s http://127.0.0.1:38741/health` | `{"status":"ok"}` |
| `curl -s -H "Authorization: Bearer $(cat ~/.sayane/bridge.token)" http://127.0.0.1:38741/profiles` | Profile 配列 |

TestClient では uvicorn プロセス起動は検証しないため L2 に残す。

---

## 4. L2-CLI 詳細で手動が必要なもの

[cli-acceptance-test.md](cli-acceptance-test.md) — **必須 L2 列が空の項目**は L1 のみ。次は手動レビュー推奨。

| ID | 理由 |
|----|------|
| EXP-01 | Markdown 出力の読みやすさ |
| I18N-01 | 日本語ヘルプの自然さ（キー存在は L1） |
| STOR-04〜05 | 実 vault import / `git log` 目視 |
| COMP-03 | `instruction` 反映の**内容**確認 |

---

## 5. L3 Extension 手動が必要なもの（[#89](https://github.com/zyx-corporation/sayane/issues/89)）

[extension-acceptance-test.md](extension-acceptance-test.md) の **必須 ID** が対象。

| 区分 | 代表 ID | 手動が必要な理由 | #91 との分担 |
|------|---------|-----------------|-------------|
| Options | OPT-02〜04 | ブラウザ UI、token 保存 | — |
| Popup | POP-01〜03 | 接続ステータス | — |
| Capture | CAP-01〜02 | `activeTab` + 実ページ | — |
| Insert | INS-CG-02, INS-CL-02 | **本番 DOM** | Playwright はモック DOM のみ |
| Security | SEC-01〜02 | popup に token 欄が無いことの目視 | — |

Extension 変更がある PR / タグでは L3 必須 Pass。

---

## 6. リリース時の最小手動セット

| 条件 | 最低限 |
|------|--------|
| **常時** | L1 green（CI + 必要ならローカル `pytest -q`） |
| **Core のみ変更** | §3 の P0 + P1（SERVE-M01）+ 記録 |
| **Extension 変更あり** | 上記 + L3 必須（#89） |
| **scheduled** | `extension-e2e.yml`（週次 / PR） |

---

## 7. 非目標

- 手動 UAT の完全廃止
- 実サイト Insert の PR 必須 Playwright 化（flake のため [#91](https://github.com/zyx-corporation/sayane/issues/91) はモック DOM + scheduled）
