# CLI 受け入れテスト — 考察と手順書

Sayane **Community Edition** の `sayane` CLI について、受け入れテストの**考察**（何をどの層で担保するか）と**手動 UAT 手順**を定義する。

| 項目 | 値 |
|------|-----|
| **Sayane** | **0.6.0+**（`sayane --version`） |
| **対象** | Community Edition（`filesystem` backend、sayane-pro 未インストール） |
| **所要時間** | 60〜90 分（Candidate フルフロー + Storage Git 含む） |
| **上位仕様** | [acceptance-spec.md](acceptance-spec.md) L2 の CLI 部分 |
| **関連 Issue** | [#88](https://github.com/zyx-corporation/sayane/issues/88) L2 Core 手動受け入れ |

関連: [CLI マニュアル](cli-manual.md) / [評価マニュアル](evaluation-manual.md) / [Storage マニュアル](storage-manual.md) / [Dogfood 手順書](dogfood-walkthrough.md)

---

## 1. 考察 — CLI 受け入れテストの位置づけ

### 1.1 CLI が担う責務

CLI は Sayane の**制御面**である。次をローカル完結で行う。

```text
Profile Store  →  Prompt IR  →  Adapter  →  stdout（JSON / Markdown）
                ↘  Candidate 評価・merge
                ↘  Storage（import / index / commit）
                ↘  Bridge 起動（`sayane serve`）
                ↘  MCP 操作の CLI ラッパー
```

Extension は Bridge HTTP 経由、MCP クライアントは stdio 経由であり、**CLI 単体では検証できない経路**がある。逆に CLI だけが検証できるのは次のとおり。

| CLI 固有の検証価値 | 理由 |
|-------------------|------|
| **stdout 形式**（JSON indent、Markdown 見出し） | HTTP レスポンスとは別経路 |
| **Typer 引数・終了コード** | 利用者がコピペするコマンドライン |
| **i18n メッセージ**（`SAYANE_LANG`） | Bridge/Extension とは独立 |
| **`sayane init` / Profile Store レイアウト** | 初回体験の入口 |
| **Storage CLI + Git 自動コミット** | ファイルシステム副作用 |
| **エラー文言**（`BadParameter`、未知 target） | UX 契約 |

### 1.2 三層モデル（CLI 視点）

| 層 | 手段 | CLI でのカバー |
|----|------|----------------|
| **L1 自動** | `pytest` + `CliRunner` | コマンド単位の exit code・stdout 断片 |
| **L2-CLI 手動** | 本書 §4 | フルフロー・副作用・人間可読出力の確認 |
| **L2-Bridge** | [acceptance-spec.md §4.5](acceptance-spec.md) / Dogfood §3 | `sayane serve` 起動後の HTTP（CLI からは起動のみ） |
| **L3 Extension** | [extension-acceptance-test.md](extension-acceptance-test.md) | capture は Bridge 経由（CLI `capture` 未実装） |

**リリース判定（CLI 部分）**: L1 green + 本書 **必須 ID すべて P**。Bridge / Extension は上位仕様に従う。

### 1.3 L1（pytest）で担保していること / ギャップ

| コマンド群 | L1 テスト | L2-CLI で追加確認すべきギャップ |
|-----------|----------|-------------------------------|
| `--version`, `init` | `test_cli.py` | 実ホーム `~/.sayane` での初回体験 |
| `profile inspect` | `test_cli.py` | 編集後の再 inspect |
| `compile` / `export` | `test_cli.py` | `gemini`、未知 target、リダイレクト先ファイル |
| `help` | `test_cli_help.py` | ネスト topic の網羅目視 |
| `candidate list|evaluate` | `test_candidate_cli.py` | **approve / reject / diff / show / lineage** 一連 |
| `storage index|import` | `test_storage_cli.py` | **export / commit / backend set**、Git log |
| `mcp *` | `test_mcp_cli.py` | `mcp serve` 起動スモーク（任意） |
| i18n | `test_cli_i18n.py` | `--lang ja` と `SAYANE_LANG` の優先順位 |
| Critical merge | `test_critical_merge.py`（サービス層） | CLI `approve` での **拒否メッセージ** |
| plugins | `test_cli_plugins.py` | sayane-pro 無しで拡張コマンドが出ないこと |

**考察の結論**: pytest は**回帰の安全網**であり、CLI 受け入れの**代替ではない**。特に Candidate approve 拒否・Storage Git・i18n の「読める出力」は L2-CLI で記録する。

### 1.4 コマンド一覧と要件 ID（仕様マトリクス）

| 要件 ID | コマンド | 必須 L2 | L1 根拠 |
|---------|---------|:-------:|---------|
| CLI-01 | `sayane --version` | ✓ | `test_version_flag` |
| CLI-02 | `sayane init` | ✓ | `test_init_creates_profile_store` |
| CLI-03 | `sayane help` / `help <topic>` | ✓ | `test_cli_help.py` |
| CLI-04 | `profile inspect` | ✓ | `test_profile_inspect` |
| CLI-05 | `compile --target chatgpt\|claude` | ✓ | `test_compile_*` |
| CLI-06 | `export --format markdown` | | `test_export_markdown` |
| CLI-07 | `candidate list\|show\|evaluate\|diff\|approve\|reject\|lineage` | ✓ | `test_acceptance_cli.py` |
| CLI-08 | `storage backend status\|list\|set filesystem` | ✓ | `test_storage_backend.py`, `test_acceptance_cli.py` |
| CLI-09 | `storage import` / `index` | ✓ | `test_storage_cli.py` |
| CLI-10 | `storage export` / `commit` | | `test_acceptance_cli.py` |
| CLI-11 | `mcp list-profiles\|inspect-profile\|compile` | ✓ | `test_mcp_cli.py`, `test_acceptance_cli.py` |
| CLI-12 | `--lang ja` / `SAYANE_LANG` | | `test_acceptance_cli.py` |
| CLI-13 | 未知 `--target` / Profile 不在 | ✓ | `test_acceptance_cli.py` |
| CLI-14 | `sayane serve`（起動のみ） | | BRG と併用 |

---

## 2. 結果記録シート（全項目）

実施後にこの表を埋める。詳細手順は §4。

| ID | 区分 | 必須 | 結果 | 実測・メモ |
|----|------|:----:|:----:|------------|
| PRE-C01 | 前提 | ✓ | | |
| PRE-C02 | 前提 | ✓ | | |
| PRE-C03 | 前提 | ✓ | | |
| VER-01 | 版 | ✓ | | |
| HLP-01 | ヘルプ | ✓ | | |
| HLP-02 | ヘルプ | ✓ | | |
| INIT-01 | init | ✓ | | |
| PROF-01 | profile | ✓ | | |
| COMP-01 | compile | ✓ | | |
| COMP-02 | compile | ✓ | | |
| COMP-03 | compile | | | |
| EXP-01 | export | | | |
| CAND-01 | candidate | ✓ | | |
| CAND-02 | candidate | ✓ | | |
| CAND-03 | candidate | ✓ | | |
| CAND-04 | candidate | ✓ | | |
| CAND-05 | candidate | ✓ | | |
| CAND-06 | candidate | ✓ | | |
| CAND-07 | candidate | ✓ | | |
| CAND-08 | candidate | | | |
| STOR-01 | storage | ✓ | | |
| STOR-02 | storage | ✓ | | |
| STOR-03 | storage | ✓ | | |
| STOR-04 | storage | | | |
| STOR-05 | storage | | | |
| MCP-01 | mcp | ✓ | | |
| MCP-02 | mcp | ✓ | | |
| I18N-01 | i18n | | | |
| ERR-01 | エラー | ✓ | | |
| ERR-02 | エラー | ✓ | | |
| PLG-01 | plugin | ✓ | | |

**記号**: **P** Pass / **F** Fail / **S** Skip / **N/A** 対象外

**合計判定**: ☐ Pass（必須がすべて P） / ☐ Fail

---

## 3. テスト環境

| 項目 | 推奨 |
|------|------|
| OS | macOS / Linux / Windows のいずれか |
| Python | 3.11+ |
| インストール | `pip install -e ".[dev]"` |
| sayane-pro | **未インストール**（Community のみ） |
| 作業ディレクトリ | sayane リポジトリ clone 先 |

### 3.1 事前セットアップ

```bash
cd /path/to/sayane
git pull
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
sayane --version          # 0.6.0+
pytest -q                 # PRE-C01
```

**検証用 Profile**（`init` 後に編集するか、examples を参照）:

```bash
sayane init
sayane profile inspect
# または
sayane profile inspect --profile examples/profiles/minimal.yaml
```

### 3.2 実施メタデータ

| 項目 | 記入 |
|------|------|
| 実施日 | |
| 実施者 | |
| sayane 版 | |
| OS / Python | |
| git commit / PR | |
| 総合判定 | ☐ Pass / ☐ Fail |

---

## 4. 手順（シナリオ）

### 4.1 前提（PRE-C）

| ID | 手順 | 期待結果 |
|----|------|----------|
| PRE-C01 | `pytest -q` | 全 pass（skip のみ許容） |
| PRE-C02 | `sayane --version` | `sayane 0.6.0` 以上 |
| PRE-C03 | 新規ホームで `sayane init`（または既存 `~/.sayane` をバックアップ後 init） | `profiles/default/sayane.profile.yaml` 存在 |

### 4.2 版・ヘルプ（VER / HLP）

| ID | 手順 | 期待結果 |
|----|------|----------|
| VER-01 | `sayane --version` と `sayane -V` | 同一バージョン文字列 |
| HLP-01 | `sayane help` | グループ一覧（`candidate`, `storage`, `mcp` 等） |
| HLP-02 | `sayane help candidate evaluate` | `--level` 等のオプション説明 |

### 4.3 初期化・Profile（INIT / PROF）

| ID | 手順 | 期待結果 |
|----|------|----------|
| INIT-01 | 空の `~/.sayane` で `sayane init` | `context/MyContext.md` 等が作成される |
| PROF-01 | `sayane profile inspect` | `SayaneProfile`、identity 名が表示 |

### 4.4 Compile / Export（COMP / EXP）

| ID | 手順 | 期待結果 |
|----|------|----------|
| COMP-01 | `sayane compile --target chatgpt` | exit 0、stdout が JSON、`messages` 配列 |
| COMP-02 | `sayane compile --target claude` | exit 0、`system` または Anthropic 形式 |
| COMP-03 | `sayane compile --target chatgpt --instruction "週次レビュー"` | `instruction` が user 側に反映 | 任意 |
| EXP-01 | `sayane export --format markdown --target chatgpt` | `# Sayane Compiled Prompt`、`## Prompt IR` | 任意 |

**CLI 照合（任意）**:

```bash
sayane compile --target chatgpt --profile examples/profiles/minimal.yaml | python3 -m json.tool | head
```

### 4.5 Candidate フロー（CAND）— CLI 完結

Bridge を使わず CLI のみで実施する。capture 相当は **テスト用 JSON を配置**するか、次のワンライナーで作成する。

```bash
# 例: Python から capture 相当（~/.sayane が init 済み）
python3 -c "
from sayane.bridge.config import BridgeConfig
from sayane.storage.candidates import create_from_capture
cfg = BridgeConfig()
print(create_from_capture(cfg, 'CLI acceptance: explicit uncertainty and local-first.', 'cli-uat').id)
"
CID=<上記の id>
```

| ID | 手順 | 期待結果 |
|----|------|----------|
| CAND-01 | `sayane candidate list` | 上記 ID が `pending` 等で表示 |
| CAND-02 | `sayane candidate show $CID` | YAML に `proposal` / `content` |
| CAND-03 | `sayane candidate evaluate $CID --level 1` | `rde_class` が YAML に出力 |
| CAND-04 | `sayane candidate diff $CID` | JSON に `add` / `already_present` |
| CAND-05 | `sayane candidate approve $CID` | 成功メッセージ、`sayane profile inspect` で概念増加 |
| CAND-06 | `sayane candidate lineage --profile-id default` | approve イベント | 任意 |
| CAND-07 | Critical candidate を `--force-critical` なし `approve` | **拒否**（exit ≠ 0、force を促す文言） |

**Critical 拒否の用意（CAND-07）**:

```bash
# voice.tone 等 — evaluate 済み・Critical 相当の candidate を保存したうえで:
sayane candidate approve <critical-cid>
# → 非ゼロ終了、--force-critical を促すメッセージ
```

**Reject（任意・CAND-08）**:

```bash
sayane candidate reject <other-cid> --reason "uat reject"
```

### 4.6 Storage（STOR）

一時 vault:

```bash
VAULT=/tmp/sayane-uat-vault
mkdir -p "$VAULT" && echo "# UAT Note" > "$VAULT/note.md"
export SAYANE_OBSIDIAN_VAULT="$VAULT"
```

| ID | 手順 | 期待結果 |
|----|------|----------|
| STOR-01 | `sayane storage backend status` | `filesystem` |
| STOR-02 | `sayane storage backend list` | `filesystem` を含む |
| STOR-03 | `sayane storage import --dry-run` | `note.md` が一覧に出る |
| STOR-04 | `sayane storage import` → `sayane storage index` | context に取り込み、entries 増加 | 任意 |
| STOR-05 | `sayane storage commit -m "uat: cli acceptance" --init` | コミット hash 表示、または nothing to commit | 任意 |

### 4.7 MCP CLI ラッパー（MCP）

| ID | 手順 | 期待結果 |
|----|------|----------|
| MCP-01 | `sayane mcp list-profiles` | JSON 配列、`default` |
| MCP-02 | `sayane mcp compile --target chatgpt --profile-id default` | JSON、`format`: `openai_chat` |

`mcp serve` の常駐確認は [MCP マニュアル](mcp-manual.md) 参照（任意・Skip 可）。

### 4.8 国際化（I18N）— 任意

| ID | 手順 | 期待結果 |
|----|------|----------|
| I18N-01 | `export SAYANE_LANG=ja` → `sayane help` | 日本語見出し（「使い方」等） |
| I18N-02 | `sayane --lang ja candidate list`（Candidate 0 件時） | 日本語メッセージ | 任意 |

### 4.9 エラー経路（ERR）— 必須

| ID | 手順 | 期待結果 |
|----|------|----------|
| ERR-01 | `sayane compile --target not-a-llm` | 非ゼロ終了、`Unknown target` 等 |
| ERR-02 | `sayane compile --profile /no/such/file.yaml` | 非ゼロ終了、Profile 不在 |

### 4.10 プラグイン境界（PLG）— 必須

| ID | 手順 | 期待結果 |
|----|------|----------|
| PLG-01 | sayane-pro **未インストール**で `sayane --help` | `license` / `confidentiality` 等の商用サブコマンドが**出ない** |

sayane-pro インストール環境では本項目は **N/A**（商用マニュアル側で検証）。

---

## 5. L1 自動テストとの対応（証拠表）

リリース担当者が L1 green を確認する際の参照。

| pytest モジュール | 主な CLI 要件 |
|------------------|--------------|
| `tests/test_cli.py` | CLI-01, 02, 04, 05, 06 |
| `tests/test_cli_help.py` | CLI-03 |
| `tests/test_cli_i18n.py` | CLI-12 |
| `tests/test_cli_locale_resolve.py` | ロケール解決 |
| `tests/test_candidate_cli.py` | CAND 一部 |
| `tests/test_critical_merge.py` | Critical approve（サービス層） |
| `tests/test_storage_cli.py` | STOR-03, 09 一部 |
| `tests/test_storage_backend.py` | CLI-08 |
| `tests/test_mcp_cli.py` | CLI-11 |
| `tests/test_acceptance_cli.py` | CLI-07〜13, ERR, CAND, STOR-10, MCP context-packet, PLG-01 |
| `tests/test_acceptance_coverage.py` | #92 シナリオ ID レジストリ |
| `tests/test_bridge_api.py` | BRG reject / Critical 400 |

```bash
pytest -q tests/test_cli.py tests/test_cli_help.py tests/test_candidate_cli.py \
  tests/test_storage_cli.py tests/test_mcp_cli.py tests/test_cli_plugins.py
```

---

## 6. リグレッション（CLI 変更後）

| 変更箇所 | 最低限再実施 |
|----------|--------------|
| `src/sayane/cli/app.py`（candidate） | CAND-01〜07 |
| `src/sayane/cli/app.py`（storage） | STOR-01〜03 |
| `src/sayane/cli/app.py`（compile/export） | COMP-01〜02, ERR-01 |
| `src/sayane/cli/i18n.py` / `locale/*` | I18N-01 |
| `src/sayane/evaluators/` | CAND-03〜05, Critical 拒否 |
| Typer グループ追加 | HLP-01, PLG-01 |

---

## 7. 合否判定

| 区分 | ID |
|------|-----|
| **必須 Pass** | PRE-C01〜03, VER-01, HLP-01〜02, INIT-01, PROF-01, COMP-01〜02, CAND-01〜07, STOR-01〜03, MCP-01〜02, ERR-01〜02, PLG-01 |
| **任意** | COMP-03, EXP-01, CAND-08, STOR-04〜05, I18N-*, `--force-critical` 成功確認 |
| **Fail** | 必須 NG → Issue 起票 → 修正 → 本書再実施 |

[acceptance-spec.md](acceptance-spec.md) の L2 記録（CLI-M01〜03）は、本書の **COMP-01 / COMP-02 / PROF-01** を実施すれば満たせる。

---

## 8. 既知の許容事項

| 現象 | 判定 |
|------|------|
| `diff.add` が空 | **Pass** |
| `sayane candidate capture` 未実装 | capture は Bridge / Extension — **N/A** |
| Level 2 judge 未設定 | `evaluate --level 2` は **Skip** |
| `storage backend encrypted-sqlite` が list に無い | Community では **Pass** |

---

## 9. 関連ドキュメント

- [acceptance-spec.md](acceptance-spec.md) — OSS 全体の L1/L2/L3
- [cli-acceptance-test.md](cli-acceptance-test.md) — 本書（L2-CLI）
- [extension-acceptance-test.md](extension-acceptance-test.md) — L3
- [development-principles.md §7.5](development-principles.md)
- [ci.md](ci.md)

---

## 10. 変更履歴

| 日付 | 版 | 内容 |
|------|-----|------|
| 2026-05-24 | 0.6.0 | 初版 — CLI 受け入れの考察・記録シート・L1 対応表 |
