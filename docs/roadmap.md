# Sayane 実装ロードマップ

## 1. 方針

Sayane は、CLI で最小価値を実証した後、Local Bridge、MCP Server、保存先セキュリティ基盤、RDE / Candidate Review、常駐ローカルアプリ、Local Vault、UI 統合へ進む。

初期ロードマップでは Chrome Extension を主要な入出力面として扱っていた。しかし、ページ全体キャプチャはノイズが多く、文脈候補（Candidate）の品質とプライバシー境界を悪化させることが分かった。今後の標準入口は、常駐アプリによる明示的な clipboard capture / selected-text capture とする。

Chrome Extension は freeze / deprecated とし、新機能追加は行わない。既存利用者向けの移行期間を設けたうえで、次リリース以降は primary release / primary docs から外す。

MCP Server は、AI エディタへ文脈を渡す安定接続面として維持する。ただし MCP は bulk export channel ではなく、MCP Context Exposure Policy に従い、承認済み文脈だけを渡す境界装置として扱う。

RDE / Candidate Review は、Candidate、ReviewDecision、Lineage という高感度データを発生させる。そのため、RDE / Candidate Review を拡張する前に、保存先の安全境界を先に確立する。Phase 4 は FileSystem storage の最小維持と外部連携保留を扱い、Phase 5 で RDE / Candidate Review の意味モデルと操作フローを扱う。

常駐アプリ化に伴い、local storage は単なるローカルDBではなく Local Vault として扱う。Local-first は plaintext-local を意味しない。保存時暗号化、OS Keychain 抽象、時間制限付き unlock session、分類別 envelope encryption、Deep Private / Layer 3 の明示 unlock を設計前提とする。

Obsidian import/export、Git 自動コミット、外部同期前提の長期保存導線は、Local Vault / 暗号化 / 鍵管理 / retention policy が固まるまで保留する。

関連 ADR / 方針文書:

- [`docs/adr/0001-local-vault-key-management.md`](adr/0001-local-vault-key-management.md)
- [`docs/mcp/context-exposure-policy.md`](mcp/context-exposure-policy.md)

実装言語は以下を基本とする。

```text
Core / CLI / Bridge : Python
MCP Server          : Python
App / UI            : native macOS app（MVP primary path）+ debug Web UI compatibility surface
Schema / IR         : JSON Schema + Pydantic
Local Vault         : SQLite + encryption-ready abstraction
将来の高速化部分     : Rust
Chrome Extension    : TypeScript（freeze / deprecated）
```

## 2. Phase 0: Repository Foundation

目的は、設計文書と最低限の開発基盤を整えることである。

作業項目:

- README整備
- Apache-2.0 LICENSE確認
- docs整備
- pyproject.toml追加
- extension/package.json追加（freeze対象）
- 基本ディレクトリ作成
- CI方針検討（[`ci.md`](ci.md)、`.github/workflows/ci.yml`）
- security方針の明文化（[`security.md`](security.md)）
- MVP範囲の明文化（[`mvp-scope.md`](mvp-scope.md)）

Phase 0 完了時点で整備済み:

- `schemas/` — Sayane Profile / Prompt IR の JSON Schema
- `src/sayane/` — core, cli, bridge, adapters, strategies, evaluators, storage, mcp
- `examples/profiles/minimal.yaml`
- `tests/` — パッケージ import と schema 検証
- `extension/` — Manifest V3 スケルトン（freeze / deprecated）

想定ディレクトリ:

```text
sayane/
  README.md
  README_ja.md
  LICENSE
  docs/
    adr/
    mcp/
  schemas/
  src/
    sayane/
      core/
      cli/
      bridge/
      adapters/
      strategies/
      evaluators/
      storage/
      mcp/
      app/          # future resident app service / UI boundary
      vault/        # future Local Vault / key abstraction
  extension/        # frozen / deprecated
  examples/
  tests/
```

## 3. Phase 1: CLI MVP

目的は、Sayane Profileを読み込み、Prompt IRへ変換し、ChatGPT / Claude向けpromptへcompileできることを実証することである。

このPhaseでは、Local Bridge、MCP Server、RDE/UIB自動評価、Local Vault、常駐アプリは実装しない。Sayaneの最小価値である `Profile → Prompt IR → Adapter` を動かすことに集中する。

実装対象:

- `sayane init`
- `sayane profile inspect`
- `sayane compile --target chatgpt`
- `sayane compile --target claude`
- `sayane export --format markdown`

Core model:

- SayaneProfile
- PromptIR
- Policy
- ContextIndex
- Adapter base class
- ChatGPTAdapter
- ClaudeAdapter

完了条件:

- sample Sayane Profile を読み込める
- schema validation が通る
- Prompt IR を生成できる
- ChatGPT向けpromptを生成できる
- Claude向けpromptを生成できる
- pytestで基本modelとadapterが検証されている
- examplesに最小profileが存在する
- READMEまたはdocsにCLI実行例がある

**マニュアル**: [CLI マニュアル](cli-manual.md) / [はじめに](getting-started.md)

## 4. Phase 2: Local Bridge MVP

目的は、外部UIや将来の常駐アプリからCore Libraryを利用できるlocalhost APIを提供することである。

実装前に `docs/security.md` の要件を満たすことを確認する。

実装対象:

- `sayane serve`
- `GET /health`
- `GET /profiles`
- `POST /capture`
- `POST /compile`
- `GET /context-packet`

完了条件:

- curlでcapture/compileが動作する
- pairing tokenの初期設計がある
- ExtensionなしでもBridge APIの動作確認ができる
- CORS deny by default
- localhost bind限定
- profile merge endpointを持たない、または明示承認を必須にする

**マニュアル**: [Bridge マニュアル](bridge-manual.md) / [CLI マニュアル](cli-manual.md)（`sayane serve`）

## 5. Phase 2.5: MCP Server MVP / Context Exposure Boundary

目的は、DOM注入に依存しない安定接続面として、MCP対応クライアントからSayane Coreを利用できるようにすることである。

MCP Serverは、Cursor、Claude Desktop、その他MCP対応クライアントからSayaneのProfile / Context / Prompt IR生成機能を呼び出すための接続面となる。ただし、MCP は AI エディタへ文脈を渡す境界であり、保存済みデータの一括公開口ではない。

実装対象:

- Sayane MCP server skeleton
- profile list tool
- compile prompt tool
- context packet tool
- candidate update list tool
- `compiled_context` tool
- MCP Context Exposure Policy guard
- read-only / review-only tool boundary

完了条件:

- MCPクライアントからprofile一覧を取得できる
- MCPクライアントからChatGPT/Claude向けcontext packetを生成できる
- MCPクライアントから安全な compiled context を取得できる
- read-only modeでProfile本体を変更しない
- pending / rejected / deferred Candidate content が通常context endpointから漏れない
- approved / scoped_accept Candidate のみが scope metadata 付きで露出する
- Local Bridgeと同等以上のsecurity境界を持つ
- Extensionなしで安定した接続面として動作する

**マニュアル**: [MCP マニュアル](mcp-manual.md) / [CLI マニュアル](cli-manual.md)（`sayane mcp`）

## 6. Phase 3: Chrome Extension Freeze / App Clipboard Capture Transition

目的は、ブラウザ拡張中心の導線を凍結し、常駐アプリ側の明示的な clipboard capture / selected-text capture へ移行することである。

Chrome Extension は補助UIとして実装されたが、ページ全体キャプチャはノイズが多く、Candidate Review の品質とプライバシー境界を悪化させる。残る有用な導線が clipboard / selected-text capture であるなら、常駐アプリ側に統合する方が適切である。

実装対象:

- Chrome Extension の freeze / deprecated 表示
- full-page capture の削除または無効化
- App clipboard capture の設計
- clipboard capture → Candidate 作成
- Extension 利用者向け migration note
- release artifact / docs から Extension を段階的に除外

完了条件:

- Extension は新機能追加対象ではないと明記されている
- ページ全体キャプチャが通常ユーザーフローから外れている
- clipboard / selected-text capture は常駐アプリ側で実現される
- capture は直接 Profile 更新ではなく Candidate 作成に入る
- Candidate review、approve / reject / defer / scoped_accept、lineage は維持される
- 次リリースで Extension が primary entrypoint として扱われない

**関連Issue**: #169 Freeze Chrome Extension and move capture flow to App clipboard capture

## 7. Phase 4: FileSystem Storage Security Foundation / External Storage Hold

目的は、RDE / Candidate Review が高感度データを発生させる前に、保存先の最小安全境界を確立することである。

このPhaseでは、FileSystem storage の最小維持に限定する。Obsidian vault import/export、Git commit integration、Git 自動コミット、外部同期前提の運用は保留する。理由は、local storage の暗号化、鍵管理、retention policy、Deep Private / Layer 3 の扱い、外部同期時の漏洩リスクがまだ解決されていないためである。

実装対象:

- FileSystem storage の最小維持
- context_index generation の最小維持
- markdown normalization の最小維持
- 外部 storage / sync / Git 連携に依存しない Candidate / Profile 基本操作
- Phase 5 の Candidate / ReviewDecision / Lineage が保存される暫定 local working store の境界定義
- 外部同期フォルダ・Git・Obsidian へ Candidate / ReviewDecision / Lineage を流さないルール

保留対象:

- Obsidian vault import/export
- Git commit integration
- Profile Store 変更時の Git 自動コミット
- 外部同期フォルダを正本 storage とする設計
- vault 間の自動同期 / 自動反映

完了条件:

- FileSystem storage だけで Community の基本 workflow が動作する
- Obsidian / Git なしで init / compile / candidate review の基本操作が可能
- 外部 storage 連携が primary path として推奨されていない
- Candidate / ReviewDecision / Lineage の暫定保存先が external sync / Git から分離されている
- 外部同期や Git 連携は Local Vault security model 完了後の再評価対象として明記されている

**マニュアル**: [Storage / Obsidian / Git マニュアル](storage-manual.md) は更新が必要。現状の Obsidian / Git 記述は legacy / hold 扱いへ移す。

Phase 5 拡張（0.5.8）と Phase 5 拡張（0.5.9）は、Local Vault / security model の完了まで保留する。

**マイルストーン注記（Community 1.0）**: Phase 0〜4 の成果物は、FileSystem storage を前提とした最小 Community workflow の基準とする。Obsidian / Git integration は Community 1.0 の必須条件から外す。

## 8. Phase 5: RDE / UIB Evaluation MVP

目的は、Profile更新候補を即時mergeせず、意味変化評価を挟めること。

Phase 5 は、Phase 4 で定義された FileSystem local working store 境界の上に実装する。Candidate / ReviewDecision / Lineage は高感度データとして扱い、Obsidian / Git / 外部同期フォルダへは出さない。

初期段階ではLLM-as-a-Judgeへ依存しすぎない。まずは schema validation、rule-based diff、heuristic RDE classification を中心にする。

評価階層:

```text
Level 0: schema validation + rule-based diff
Level 1: heuristic RDE classification
Level 2: local LLM assisted review
Level 3: external LLM assisted review
```

実装対象:

- Candidate Update model
- schema validation
- rule-based diff
- heuristic RDE classification
- UIB simple checklist
- approve / reject flow
- defer / modify / scoped_accept flow
- lineage record
- profile diff
- Candidate / ReviewDecision / Lineage の暫定 local working store 書き込み

完了条件:

- captureした情報がCandidate Updateとして保存される
- RDE分類が付与される
- ユーザー承認後にProfileへmergeされる
- reject / defer / scoped_accept の判断が lineage に残る
- LLM評価なしでも最小評価が動作する
- LLM Judge は最終判断ではなく補助情報として扱われる
- Candidate / ReviewDecision / Lineage が外部同期・Git・Obsidianへ自動流出しない

**マニュアル**: [RDE / Candidate 評価マニュアル](evaluation-manual.md)

Phase 5 拡張（旧 Phase 4 拡張 0.5.1）: Level 2/3 LLM-as-a-Judge、`--force-critical` による values/voice/policy/roles の merge。

## 9. Phase 6: Resident App / Local Vault Foundation

Phase 6 は、Sayane を CLI / Bridge / MCP の集合から、常駐する local-first application へ進化させる基盤である。

目的:

- 常駐 App Service / daemon による CLI・Bridge・MCP・UI の状態統合
- Local Vault による Candidate / ReviewDecision / Lineage / Profile / Project Context の永続化
- OS Keychain abstraction による cross-platform secret handling
- DB全体暗号化 + 高感度カラム / レコードの分類別 envelope encryption
- unlock session の導入（normal / sensitive / deep_private）
- Deep Private / Layer 3 の明示 unlock
- App clipboard capture と Candidate Review Queue の統合
- MCP Context Preview UI

実装対象:

- `PlatformKeychainProvider` 抽象
- `KeyManager` / `CryptoProvider` 抽象
- SQLite keyring / encrypted record schema
- unlock session manager
- capability-based local access control
- `load_review_decisions()` persistent implementation
- Candidate / ReviewDecision / Lineage repository abstraction
- App clipboard capture
- Candidate Review Queue UI
- MCP compiled_context preview UI

完了条件:

- local storage が encrypted-by-default の設計になっている
- plaintext SQLite が production default ではない
- master key は直接データ暗号化に使われず、分類別 DEK を wrap する
- Raw Capture / Profile / Lineage / Cloud Transfer Log / Deep Private が別暗号境界を持つ
- unlock session は scope と timeout を持つ
- UI unlock は MCP / Bridge / Extension token に自動継承されない
- App clipboard capture から Candidate を作成できる
- UI で Candidate Review Queue を操作できる
- MCP に渡る compiled context を UI で preview できる

**ADR**: [ADR 0001: Local Vault Key Management](adr/0001-local-vault-key-management.md)

### 本番完成向け Issue 分解

Resident App MVP 完了後の production-completion line は、extension ではなく app / Local Vault を優先して進める。

| Issue | 状態 | 概要 |
|------|------|------|
| P1 | 完了 | Local Vault foundation — 保存時暗号化、OS keychain 抽象、unlock session 導入、resident app/native app からの unlock/lock/gated action 連携 |
| P2 | 完了 | Sensitive working-store migration — `Candidate` / `ReviewDecision` / `Lineage` を vault-aware storage へ全面移行 |
| P3 | 完了 | External integration re-design — Obsidian / Git / external sync を security model 後の正式仕様へ更新 |
| P4 | 保留 | Linux operator packaging — Linux systemd --user preview/apply shipped slice までは記録済みとし、残る lifecycle / desktop packaging は macOS 完了後に再開する |
| P5 | 保留 | Windows operator packaging — Windows service / installer / operator path は contract 記録のみ維持し、macOS 完了後に再開する |
| P6 | 進行中 | `/app/ui*` legacy retirement — debug-only compatibility surface を通常の macOS operator flow から段階的に退避する |
| P7 | 未着手 | Extension release/doc retirement — primary docs / release artifact から extension を外し切る |

現時点の優先順位メモ:

- Linux / Windows の追加実装はここで保留し、現状 contract / shipped slice を記録済み状態として維持する
- 直近は native macOS app の完成と `/app/ui*` debug-only compatibility surface の縮退を優先する

macOS 完成に向けた追加 Issue 分解:

| Issue | 状態 | 概要 |
|------|------|------|
| M8 | 進行中 | Native-first operator launch — 通常の macOS operator 起動を repo-local script 前提から外し、native app 起点の起動導線へ寄せる |
| M9 | 進行中 | Bundled Bridge/helper runtime — native app から Local Bridge を内部 helper として起動・warmup・再接続できる shipped runtime を整える |
| M10 | 進行中 | Native diagnostics closure — browser fallback なしで bridge 状態・token/log・再接続・起動失敗理由を native app 内で把握できるようにする |
| M11 | 進行中 | macOS install/runtime closure — install / upgrade / reinstall / launch の通常導線を native app 中心に閉じ、curl+bash 配布導線と噛み合わせる |
| M12 | 進行中 | `/app/ui*` retirement on macOS path — native parity が満たされた範囲から browser compatibility surface を routine flow から外す |

M8–M12 の方針:

- ユーザー体験としては「1つの macOS app を起動すれば使える」状態を先に作る
- backend は当面 Local Bridge を維持し、helper/backend として app の背後に隠す
- backend 置換は別判断とし、まずは UX 統合を完了させる

**ADR**:

- [ADR 0027: macOS Native App Owns the Operator Launch Experience While Bridge Remains the Local Backend](adr/0027-macos-native-app-owns-the-operator-launch-experience-while-bridge-remains-the-local-backend.md)

P1 完了時点の到達点:

- `PlatformKeychainProvider` / `KeyManager` / `CryptoProvider` 抽象が実装済み
- explicit development runtime と explicit macOS keychain runtime が実装済み
- unlock policy / unlock session manager / scoped session metadata が実装済み
- resident app API / compatibility shell / native macOS app から Local Vault status と session 状態が可視化済み
- Local Vault backend 有効時の clipboard capture / review action / revise が active unlock session 必須で fail-closed 化済み

P1 の次は、app-facing 操作が現在の FileSystem working store に残している高感度実体を、vault-aware repository へ移す P2 を優先する。

P2 の現時点での進捗:

- resident app / native macOS app 経由の capture・review・revision・lineage read は `BridgeConfig.repositories` / `repository_session` を通じて vault-aware repository を利用
- generic legacy bridge `/capture` / `/candidates*` / `/captures/*/lineage` も同じ vault-aware repository と active unlock session 境界へ収束済み
- Local Vault backend 有効時、resident app の candidate queue / detail / diff / lineage read も active unlock session 前提で vault-backed record を読む
- resident app 経由で作成した Candidate は FileSystem `~/.sayane/candidates/*.json` に落とさず、vault-backed repository に保存される
- CLI `capture` / `candidate` も explicit `--vault-mode` で同じ vault-aware repository を使える
- CLI `review` / `context-compile` / `audit` も explicit `--vault-mode` で vault-backed ReviewDecision を read/write できる

P2 の完了境界:

- transitional FileSystem working store は debug / import / legacy compatibility path に限定して残す
- 新しい高感度 app-facing 機能は FileSystem working store を増やさず、repository / Local Vault path を拡張する
- 詳細は `docs/adr/0017-transitional-filesystem-working-store-boundary-after-p2.md`

P3 の現時点での進捗:

- Obsidian import / export と Git commit は `--legacy-compatible` を要求する explicit legacy compatibility path になった
- `sayane init` は Git repository 作成や初回 commit を暗黙実行しない
- dry-run inspection は非破壊のため従来どおり確認用途に残す
- `storage export` は外部書き出し先に non-canonical / derived / review-required を示す metadata と notice を同梱する
- `storage export` metadata では local path を redaction し、互換 export の retention guidance を同梱する
- `storage export` は hidden / reserved / escaping subdir を拒否し、bounded subdirectory のみを許可する
- `storage import` も `--source-subdir` で safe bounded subtree に限定できる
- `storage export-package` / `storage import-package` により、vault-aware external package を reviewable exchange format として定義した
- vault-aware package の `bundle.yml` は provenance metadata と content hash を持ち、package manifest も non-canonical / review-required boundary を持つ
- vault-aware package は artifact ごとの retention class（現行は `reviewable_context_bundle=30d`, `redacted_audit_export=14d`）を持つ
- vault-aware package manifest は supported operator actions と forbidden workflows を明示する
- `storage import-package` は preview-only 契約で、profile と review queue を変更せず candidate-style review 出力だけを返す
- Obsidian import / export / filesystem Git commit は恒久 legacy compatibility workflow として固定した
- retention expiry は現行 contract では warning-only とし、automatic sync automation は supported path から除外した
- `storage queue-package` により、preview-only import を壊さず explicit review queue intake を追加した

P3 完了境界:

- legacy compatibility path、supported package path、preview-only path、explicit review-queue intake path が分離された
- automatic external sync promotion / bidirectional sync / implicit filesystem Git auto-commit primary path は supported path から除外された
- package から profile merge までは preview → queue → review → approve の明示段階になった

## 10. Phase 7: Commercial / Pro Extensions

Commercial / Pro Edition は、Community で確立された Local Vault / App Service / UI 境界を前提に、配布・性能・運用機能を拡張する。

候補:

| 候補 | エディション |
|------|-------------|
| 高性能 encrypted SQLite engine / Rust backend | Commercial / Pro |
| `storage migrate to encrypted-sqlite` 強化 | Commercial / Pro |
| Windows MSI / macOS signed app / auto update | Commercial / Pro |
| local daemon production installer | Commercial / Pro |
| 大規模 semantic diff engine | Commercial / Pro |
| 大規模 markdown vault indexer | Commercial / Pro |
| enterprise policy / team vault / managed keys | Commercial / Pro |
| provider trust profile / cloud-send risk dashboard | Commercial / Pro |

Community Edition（Apache 2.0）は FileSystem + Python Core + security abstraction contracts を継続メンテする。Obsidian / Git integration は、Local Vault / security model の完了後に再評価する。Rust/SQLite backend・MSI・商用UI拡張の実装本体は Commercial / Pro 側とし、Storage / Vault / Keychain 抽象の契約は OSS に残す。

Rust化は、Python実装で仕様とボトルネックが明確になってから行う。

## 11. 優先順位

現時点の優先順位は以下である。

```text
1. MCP Context Exposure Policy の実配線維持
2. Chrome Extension freeze / App clipboard capture 移行
3. Phase 4: FileSystem storage security foundation
4. Phase 5: RDE / Candidate Review MVP
5. Local Vault key management ADR の実装準備
6. PlatformKeychainProvider 抽象
7. SQLite persistent store abstraction
8. load_review_decisions() persistent implementation
9. Resident App Service / daemon
10. Candidate Review Queue UI
11. MCP compiled_context preview UI
12. Obsidian / Git integration の再評価
13. Commercial / Pro packaging and performance work
```

## 12. 非目標

初期段階では以下を目標にしない。

- 完全自動人格更新
- 全LLM API対応
- 完全な意味理解
- 意識や人格保存の主張
- クラウドSaaS化
- Chrome Extension中心の安定接続設計
- ページ全体キャプチャの復活
- Obsidian / Git integration を security model 完了前に primary path とする設計
- 外部同期フォルダを保護なしに正本 storage とする設計
- Candidate / ReviewDecision / Lineage を外部同期・Git・Obsidianへ自動保存する設計
- RDE/UIB評価の完全自動化
- 同一人格の完全再現という主張
- UI unlock を外部ツールアクセスへ自動継承する設計
- plaintext local storage を production default とする設計

Sayaneはまず、local-firstなPersona / Context IR基盤から、保護された Local Vault と人間のレビューを中心にした常駐文脈受容基盤へ進む。
