# Sayane はじめに（利用者ガイド）

Sayane **1.0.13 package line** 時点で、Phase 0〜5 の成果物に加え resident app / daemon proof / operator packaging フェーズのプレビュー/方針文書が追加されている。本書は「何ができて」「どこから始めるか」をまとめる。

設計の詳細は [設計概要](architecture.md)、開発者向けは [開発原則](development-principles.md) を参照。

## 1. Sayane とは

LLM 間で、ユーザーの人格的文脈・価値観・応答様式を **local-first** に保持し、各 LLM 向けプロンプトへ変換するツールである。

```text
人格と実行を分離する
```

```text
Sayane Profile  →  Prompt IR  →  Adapter  →  LLM 向け出力
```

LLM は人格の所有者ではない。Profile と Prompt IR は LLM 非依存の中間表現である。

## 2. 現在利用できる構成（Phase 0〜5）

| Phase | 成果物 | 主な用途 |
|-------|--------|----------|
| 0 | スキーマ・CI・パッケージ骨格 | 開発基盤 |
| 1 | **CLI** (`init`, `compile`, `export` …) | ターミナルから Profile → プロンプト |
| 2 | **Local Bridge** (`sayane serve`) | HTTP API・Extension 連携 |
| 2.5 | **MCP Server** (`sayane mcp serve`) | Cursor / Claude Desktop 等 |
| 3 | **Chrome Extension** | ブラウザ capture・LLM 挿入・Candidate popup（ja/en、現行方針では freeze / deprecated） |
| 4 | **RDE / Candidate 評価** | ヒューリスティック評価・approve/reject・lineage |
| 5 | **Storage / Obsidian / Git** | local Markdown / context_index。Obsidian / Git は互換運用 |

**未実装（Phase 6 / Commercial Edition）**: 概要は [roadmap.md §9](roadmap.md)。商用版 CLI・MSI 等のマニュアルは sayane-pro 側。

## 3. 接続面の選び方

```text
                    ┌─────────────────┐
                    │  Core Library   │
                    │ Profile / IR    │
                    └────────┬────────┘
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
      ┌─────────┐     ┌───────────┐    ┌────────────┐
      │   CLI   │     │  Bridge   │    │ MCP Server │
      │ 直接操作 │     │ HTTP:38741│    │ stdio MCP  │
      └─────────┘     └─────┬─────┘    └──────┬─────┘
                            │                  │
                            ▼                  ▼
                     Chrome Extension    Cursor / Cline
```

| やりたいこと | 推奨 |
|-------------|------|
| 手元でプロンプト JSON を得る | [CLI マニュアル](cli-manual.md) |
| ローカル browser shell で queue / daemon / diagnostics を使う | [Bridge マニュアル](bridge-manual.md) の resident app 導線 |
| Cursor から Profile を参照・compile | [MCP マニュアル](mcp-manual.md) |
| ブラウザで文脈を capture / LLM 欄に挿入 | [Extension マニュアル](extension-manual.md) + Bridge |
| スクリプトから HTTP で呼ぶ | [Bridge マニュアル](bridge-manual.md) |

## 4. インストール

**PyPI**（Python 3.11+）:

```bash
pip install "sayane==1.0.14.post1"
```

**macOS / Linux**（curl + bash）:

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
```

**Windows**（PowerShell）:

```powershell
irm https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.ps1 | iex
```

詳細: [インストール](install.md)

### 開発者向け（clone 済み）

```bash
git clone https://github.com/zyx-corporation/sayane.git
cd sayane
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

または `SAYANE_SOURCE_DIR=$PWD bash scripts/install.sh`

Profile Store の初期化:

```bash
sayane init
# ~/.sayane/profiles/default/sayane.profile.yaml を編集
sayane profile inspect
```

サンプルだけ試す場合:

```bash
sayane compile --target chatgpt --profile examples/profiles/minimal.yaml
```

## 5. シナリオ別クイックスタート

### 5.1 CLI のみ（Phase 1）

```bash
sayane compile --target claude --profile examples/profiles/minimal.yaml
sayane export --format markdown --target chatgpt \
  --profile examples/profiles/minimal.yaml
```

→ [CLI マニュアル](cli-manual.md)

### 5.2 MCP クライアント（Phase 2.5）

```bash
sayane mcp serve   # stdio — クライアントが子プロセス起動
# またはデバッグ用:
sayane mcp list-profiles
sayane mcp compile --target chatgpt --profile-id default
```

→ [MCP マニュアル](mcp-manual.md)

### 5.3 Chrome Extension + Bridge（Phase 2 + 3 / legacy）

Chrome Extension は既存利用者向けには利用可能だが、現行方針では **freeze / deprecated** であり、新規の主経路は CLI / MCP / Local Bridge である。

ターミナル 1:

```bash
sayane serve
# Bearer token: ~/.sayane/bridge.token
# Dedicated local UI session artifact: ~/.sayane/bridge.ui-session.json
# Resident app bootstrap: http://127.0.0.1:38741/app/ui
```

ターミナル 2:

```bash
cd extension && npm install && npm run build
# Chrome で extension/ を読み込み、Options に token を設定
```

→ [Bridge マニュアル](bridge-manual.md) / [Extension マニュアル](extension-manual.md)

### 5.4 native macOS app（current primary UI path）

現行の primary operator-facing growth path は、Bridge-hosted local shell ではなく
**native macOS app** である。`/app/ui` は debug-only compatibility surface として残っている。

```bash
./scripts/run-macos-app-preview.sh
# 必要なら:
# ./scripts/run-macos-app-preview.sh --foreground
# ./scripts/run-macos-app-preview.sh --no-build
swift build --package-path macos/SayaneApp
swift test --package-path macos/SayaneApp
# Python 側の関連確認は:
# uv run --extra dev pytest -q tests/test_bridge_api.py tests/test_resident_app_html.py
```

これらの launcher / smoke script は、`>=3.11` かつ Sayane 依存込みの Python を前提にする。
`uv run --extra dev ...` を一度通すか、`.venv` を作って `pip install -e ".[dev]"` しておく。

native app は bearer-backed app-facing resident surfaces を直接利用する。

native app 上では、`Home` / `Bridge Status` / `Daemon` / fallback `Error` view から同じ
起動導線を辿れる。local script path が見えている面では `Open Launcher` と
`Copy Startup Command`、debug compatibility path が見えている面では
`Open Debug Shell` と `Copy Debug Shell URL` を使う。

### 5.5 resident app debug shell（debug-only compatibility path）

Bridge-hosted local shell は、debug / fallback / handoff / browser-local smoke 向けに維持する。

```bash
./scripts/run-app-local.sh
# 必要なら:
# ./scripts/run-app-local.sh --foreground
# ./scripts/run-app-local.sh --no-open
# Google Chrome があれば bootstrap URL を Chrome で優先的に開く
# 初回ブラウザ導線は /app/ui?bootstrap_token=... を 1 回だけ踏み、
# 以後は dedicated local UI session cookie で /app/ui を継続利用する
sayane app overview --json
sayane app daemon-overview --json
sayane app daemon-packaging-status --json
sayane app daemon-service-targets-status --json
sayane app daemon-service-control-boundary --json
sayane app daemon-supervision-status --json
sayane app daemon-recovery-consent-status --json
sayane app daemon-operator-phase-status --json
sayane app daemon-preflight --json
sayane app daemon-proof-diagnostics --operation-class bridge_health --json
```

`run-app-local.sh` も同じ前提で動く。互換 Python が見つからない場合は fail-closed で止まるため、
その場合は `uv run --extra dev pytest -q` か `.venv` 構築を先に行う。

Bridge-hosted daemon shell では、UI session 確立後に次の read surface へそのまま drill-down できる:

```text
/app/ui-state/operator-phase-status
/app/ui-state/daemon-packaging-status
/app/ui-state/daemon-service-targets-status
/app/ui-state/daemon-service-control-boundary
/app/ui-state/daemon-supervision-status
/app/ui-state/daemon-recovery-consent-status
```

同じ daemon shell には decision assist も追加されており、service control / recovery /
supervision / LaunchAgent の各判断について、次に確認すべき command と read surface を
ブラウザ上からそのまま辿れる。
さらに phase-closure gate guide も追加されており、未完了の gate ごとにどの read surface を
先に確認すべきかを同じ daemon shell 上で辿れる。
加えて implementation gate preflight も同じ drill-down stack に統合され、daemon 実装前の
schema-only gate 状態を browser 上から直接確認できる。
さらに current gate / next command / next read surface を 1 つにまとめた operator summary rail が
native app 側にも mirrored されており、同じ startup/debug shortcut を保ったまま deeper daemon
workspace に入れる。
bridge-hosted shell に追加され、長い panel を読む前に優先確認ポイントを先に揃えられる。

package line を local で release 確認したい場合は、長寿命の開発用 `.venv` に依存せず
短命な metadata-check 用 venv を内部で作る次のコマンドを使う:

```bash
bash scripts/build-wheel.sh
```

この local shell は preview / review / operator guidance surface であり、直接 profile patch や
OS service activation を行うものではない。

現在の resident app entrypoint は:

```text
http://127.0.0.1:38741/app/ui
```

`http://127.0.0.1:8008/index.html` のような別 static-site URL は使わない。

→ [Bridge マニュアル](bridge-manual.md) / [CLI コマンドリファレンス](reference/cli-command-reference.md)

### 5.5 macOS native app preview

macOS では、Bridge-hosted web shell に加えて native app preview も開発中です。

```bash
swift build --package-path macos/SayaneApp
./scripts/run-macos-app-preview.sh
./scripts/check-macos-app-preview.sh
```

Swift package を Xcode で開き、`SayaneApp` executable target を起動する。
現在は `./scripts/run-macos-app-preview.sh` だけで、Bridge を整えてから
`macos/SayaneApp/.build/arm64-apple-macosx/debug/SayaneApp` を直接起動できる。
IDE で確認したい場合だけ `./scripts/run-macos-app-preview.sh --xcode` を使う。
Bridge 切断時は native error view の `Start Bridge` / `Reconnect` を使う。
`./scripts/check-macos-app-preview.sh` は local Bridge shell の準備、Swift package build/test、
`/app/ui` bootstrap と screen-state surface の smoke check をまとめて実行する。
現状の smoke test は既定で full `swift test --package-path macos/SayaneApp --disable-xctest` を実行し、
native app 導線の回帰をそのまま確認する。
この native smoke は current resident app shell と同じ `./scripts/run-app-local.sh`
経由で Bridge を起動し、stale な detached `serve` process が残っていても
起動前に整理する。
Bridge-hosted local shell の UI session だけを軽く確認したい場合は
`./scripts/check-resident-app-ui-session.sh` を使う。
bearer-backed resident app JSON read surface だけを軽く確認したい場合は
`./scripts/check-resident-app-api-surfaces.sh` を使う。
release 向けに API surface smoke と UI session smoke をまとめて流したい場合は
`./scripts/check-resident-app-release-smoke.sh --start` を使う。
native macOS preview も含めて current app shell 全体を 1 回で確認したい場合は
`./scripts/check-resident-app-release-smoke.sh --start --with-native` を使う。
現在の local launcher / smoke scripts は、port だけを掴んでいない stale `serve`
process も起動前に掃除する。
また `sayane serve` は、通常の Bridge 起動では optional reload watcher
(`watchfiles`) に依存しない保護付きになっているため、開発環境の native wheel が
壊れていても resident app local shell の通常起動は継続できる。
既存の手動起動 Bridge をそのまま使いたい場合は `--no-start`、Bridge/session 切り分けだけを
したい場合は `--no-build --no-tests`、
失敗時のレスポンス本文まで見たい場合は `--verbose` を使う。

この native app preview は resident app contract / screen-state / action surfaces を使う。
native app 自体は `~/.sayane/bridge.token` を使って bearer-backed app-facing surface を直接読む。
Browser bootstrap と resident app UI session は Bridge-hosted debug shell 側の話として切り分ける。
Home と error view には共通の connection diagnostics card があり、Bridge URL / health endpoint /
debug shell URL / token path / log path と、Reconnect / Start Bridge / Open Logs などの復旧操作を
同じ場所から使える。
さらに Home 最上部には Bridge status panel があり、未接続 / 起動中 / 利用可能 を先に判断してから
次の操作へ進める。
同じ status rail は Queue / Daemon にも compact 表示されるため、作業中の画面から戻らずに
Bridge の再接続やログ確認へ進める。
また capture / review / copy の結果は共通の feedback banner に集約され、mutation 失敗時は
sheet が閉じずに入力内容を保ったまま再試行できる。
Queue detail では、現在選択中の候補に関係する直近アクション結果だけを candidate result strip として
残すため、approve / revise 後の文脈を見失いにくい。
同じ detail 面から candidate detail / diff / lineage をそのままコピーできるため、
レビュー内容を外部メモやチャットへ移すときに手動選択が要らない。
さらに Queue detail の review command deck に readiness / 実行ボタン / shortcut をまとめ、
判断と操作を 1 箇所で完結できるようにしている。
Home では review / quick link / daemon action の先頭項目を start-here section に集約し、
起動直後の最初の一手を選びやすくしている。
Daemon でも next action / LaunchAgent status / runbook を focus section にまとめ、
さらに current gate / next command / next read surface を operator summary rail にまとめてから、
長い運用情報に入る前の優先確認ポイントを先に見せる。
同じ `Start Here` カード自体から、そのまま該当 daemon section へ移動できるため、
「何を見るべきか」と「どこを開くか」を分けずに辿れる。
さらに section navigator も priority sections と other sections に分かれ、
直前の `Start Here` / operator summary rail で触れた判断面を先に辿りやすくしている。
そのため next-epic workspace 側は、同じ優先導線で既に触れた判断面を重ねず、
残りの判断面だけを deeper review 用に残す構成になっている。
さらに phase-closure gates / decision assist / evidence drill-down / remaining workstreams も
同じ priority path に沿った順で並ぶため、深掘りに入っても読み順が急に変わらない。
macOS の LaunchAgent 面では、compact な `LaunchAgent Focus` を先頭に置きつつ、
下段の `Current State Details` / `Recovery Preview Details` で要約の根拠と診断内訳を追える。
同じ detail groups から current state / recovery preview の内容をそのままコピーできるため、
handoff や troubleshooting の転記も native app だけで進めやすい。
さらに operator summary rail / phase closure gates / decision assist / evidence drill-down にも
copy action が入り、現在の運用判断・次コマンド・参照先を daemon 画面からそのまま共有できる。
同じ daemon header からは、それらを LaunchAgent current state / recovery preview と合わせた
handoff note として `.txt` に書き出せるため、セッション終端時の引き継ぎも native app 内で完結する。
書き出し内容には生成日時・Profile・Bridge URL・Health Endpoint・現在の Bridge 状態も含まれるため、
あとから見返したときにも「どの接続状態で保存したメモか」を追いやすい。
さらにファイル名自体にも timestamp が入り、Bridge Version / Source Updated も記録されるため、
同日に複数回 handoff を残しても衝突しにくく、どの build / source freshness だったかを追いやすい。
加えて Component / Token File / Log File も入るため、引き継ぎ相手が app を開き直さなくても
まずどの bridge 実体を見て、どの token / log を辿ればよいかを exported note だけで把握しやすい。
さらに Debug Shell と最初の Next Command / Reason も冒頭に入るため、ブラウザ側の fallback 確認と
daemon 側の初手判断を同じ exported note からすぐ始められる。
加えて launchctl print / stdout tail / stderr tail も入るため、CLI ベースの一次診断へも
そのまま接続でき、handoff 先でコマンドを再発見し直す手間が減る。
さらに Preflight Checks / Proof Diagnostics の代表コマンドも含まれるため、準備確認と
proof-oriented な深掘りのどちらから入る場合でも exported note を起点に進めやすい。
加えて command 群自体も `Status Diagnostics` / `Tail Commands` / `Preflight Checks` /
`Proof Diagnostics` に分かれているため、handoff 相手が今どの診断モードに入るかを選びやすい。
さらに後半の `Operator Summary` / `Phase Gates` / `Suggested Action` / `Read Surfaces` /
`Current State` / `Recovery Preview` も同じ見出し付きになったため、長めの exported note でも
目当ての塊へ素早く飛びやすい。
加えて並び順自体も `Operator Summary → Suggested Action → Phase Gates → Read Surfaces →
Current State → Recovery Preview` に寄せたため、handoff の読み手が実際の判断順に沿って追いやすい。
さらに先頭の metadata も `Bridge Context` でまとまったため、接続前提・診断入口・運用判断の境界が
exported note 上でよりはっきり分かれる。
加えてその見出し自体も i18n 文言に移したため、日本語環境では hard-coded な英語見出しが残らず、
他の native app 文言と同じ調整経路で将来の表現変更にも追従できる。
さらに bridge metadata や diagnostic section 周りのラベルも日本語側へ寄せたため、
handoff note 全体の見出しが日本語環境でより一貫して読めるようになっている。
加えて `コンポーネント` や `ログ追跡コマンド` など CLI に近いラベルも i18n 管理に入ったため、
後続の文言調整でも exported note だけ別管理になる状態を避けやすい。
さらに LaunchAgent Runbook も、preflight / verification / proof diagnostics を先に並べ、
その後に log / preview detail を続ける順になっているため、確認系から深掘り系へ自然に進める。
同じ LaunchAgent section 内の command deck も inspect / recover / start / log の順に並び、
状態確認と復旧判断のあとで起動系コマンドへ進む読み順に揃えている。
さらに inspect は非破壊の status / health 確認だけに絞られ、recover では cleanup / repair /
bootout をその順で出すため、確認・復旧・再起動の境界がより明確になっている。
各グループには短い summary も付いているため、command deck を開いた直後に
「この段では何をするか」をコマンド列より先に掴める。
さらに LaunchAgent section の先頭には compact な focus ブロックがあり、
current state / recovery preview / next command を先にひとまとめで確認したあと、
下段の detail groups で重複なしに確認を続けられる。
次のEpic向けには packaging / service / supervision / recovery を 1 画面で見比べる
next-epic workspace も追加されており、各判断面の read surface コマンドをその場でコピーできる。
同じ next-epic workspace には unresolved な phase closure gate ごとのカードもあり、
packaging / service / supervision / recovery のどの read surface を先に見るべきかを
その場で開き分けられる。
同じ場所で recommended implementation order と phase closure checklist の要約も見えるため、
どの判断から先に着手すべきかと、何が未解決ブロッカーかを native app 上で先に揃えられる。
さらに evidence drill-down から operator phase / packaging / service targets / service control /
supervision / recovery consent の JSON read surface へ即座に降りられる。
各 evidence card 自体にも current snapshot が出るため、command をコピーする前に比較の起点を揃えやすい。
さらに decision assist が service control / recovery / supervision の次の確認コマンドを先に提案する。
LaunchAgent 系では runtime-init / cleanup-preview / repair-preview の確認経路も同じ assist 面から辿れる。
proof line では `daemon-identity-proof` / `daemon-readiness-proof` / `daemon-api-readiness-proof` /
`daemon-proof-diagnostics` に加え、implementation gate 確認用の `daemon-preflight` も
LaunchAgent Runbook から copyable な read command として辿れる。
daemon 画面では copyable な CLI / `launchctl` コマンド、LaunchAgent plist 確認、
runtime-init / cleanup / repair の conservative preview 要約を確認できる。
さらに current operator packaging / supervision / recovery contract を read-first で表示し、
packaging model 候補、background supervision 候補、guardrails、推奨 recovery flow を
native app 内で参照できる。加えて startup command / bootstrap UI / phase closure checklist
も native 側で可視化する。handoff 向けに workstream 状態と recommended implementation order
も同じ画面で確認できる。service lifecycle operation / policy gate / app-UI exposure limit /
governing rule も同じ daemon 画面で read-first に確認できる。macOS では LaunchAgent 向けの
preflight / verification / log path / security boundary / troubleshooting に加えて、
plist preview / program arguments / environment assumptions も native 画面で参照できる。
さらに operation id / preview hash も native 画面で確認でき、handoff 時の照合に使える。
stdout/stderr の tail コマンドと preview/apply boundary も同画面で確認できる。
loaded status / return code / stderr summary も先に確認できる。
主要セクションは折りたたみ表示になっており、要点だけ先に確認しやすい。

失敗時の基本切り分け:

```bash
curl -s http://127.0.0.1:38741/health
open -a "Google Chrome" "http://127.0.0.1:38741/app/ui?bootstrap_token=$(cat ~/.sayane/bridge.token)"
tail -n 40 ~/.sayane/macos-app-smoke.log
```

- `ERR_CONNECTION_REFUSED`: Bridge 未起動または listen 失敗
- `Missing bootstrap bearer or valid resident app UI session`: bootstrap URL を踏まずに `/app/ui` を開いている
- `Missing or invalid resident app UI session`: cookie が stale。bootstrap URL を開き直すか smoke script を再実行する

→ [macOS app preview](../macos/SayaneApp/README.md)

### 5.6 Obsidian / Git（Phase 5 / compatibility）

```bash
export SAYANE_OBSIDIAN_VAULT="$HOME/Documents/MyVault"   # 任意: 存在する vault
sayane storage import          # または sayane storage import /path/to/vault
sayane storage index
sayane compile --target chatgpt   # context 本文を Prompt IR に含める
# Git / Obsidian は互換導線として残るが、現行方針では primary path ではない
```

→ [Storage マニュアル](storage-manual.md)

## 6. ローカルデータの場所

```text
~/.sayane/
  bridge.token              # Bridge 認証（Phase 2）
  bridge.ui-session.json    # resident app の dedicated local UI session artifact
  profiles/
    default/
      sayane.profile.yaml  # メイン Profile
      context/              # 文脈 Markdown（参照用）
  candidates/               # capture された Candidate（merge 前）
```

capture は **Profile へ即 merge しない**。評価・承認は CLI / Bridge / Extension / MCP から行う（[評価マニュアル](evaluation-manual.md)）。

## 7. マニュアル一覧

| ドキュメント | 内容 |
|-------------|------|
| [CLI マニュアル](cli-manual.md) | `init`, `profile`, `compile`, `export`, `serve`, `mcp` 概要 |
| [Bridge マニュアル](bridge-manual.md) | HTTP API・認証・curl |
| [MCP Server マニュアル](mcp-manual.md) | Tools・Cursor 設定 |
| [Chrome Extension マニュアル](extension-manual.md) | ビルド・popup・i18n・site adapter |
| [Chrome Extension 受け入れテスト](extension-acceptance-test.md) | 手動 UAT 手順 |
| [RDE / Candidate 評価マニュアル](evaluation-manual.md) | evaluate・approve・lineage |
| [Storage マニュアル](storage-manual.md) | Obsidian import/export・Git・直接編集 |
| [Sayane Profile と Prompt IR](profile-ir.md) | データ構造 |
| [Security Design](security.md) | 脅威モデル・read-only 方針 |

## 8. 制限事項（現バージョン）

- `compile` の context 本文読み込みはプロファイルディレクトリ内のファイルに限定（最大約 32KB/ファイル）
- Adapter は **chatgpt / claude** のみ
- Obsidian: `SAYANE_OBSIDIAN_VAULT` 設定時は `storage import` / `export` で vault 引数を省略可
- Obsidian export は vault 内サブディレクトリ（既定 `sayane/`）のみ
- Level 3 judge は API key とネットワークが必要（任意機能）

## 9. 次のロードマップ

[実装ロードマップ](roadmap.md) — Phase 6: Rust 抽出（diff engine、vault indexer 等）。
