# コンテキスト層設計 — Tone / Identity / Theory / PII の分離

Dogfooding Iteration 2（2026-05）で観察された **Tone 汚染・部分注入・PII 露出** を受け、Sayane Profile と `context/` ファイルへの **配置ルール** を定義する。

追跡 Issue: [#102](https://github.com/zyx-corporation/sayane/issues/102)

関連:

- [Sayane Profile と Prompt IR](profile-ir.md)
- [Dogfood 手順書](dogfood-walkthrough.md)
- [RDE / Candidate 評価マニュアル](evaluation-manual.md)
- [Confidentiality Policy スキーマ契約](confidentiality-policy-schema.md)
- 実装: `src/sayane/core/builder.py`（compile 時の system / context / constraints 分割）

---

## 1. 背景（Dogfood Iteration 2）

### 1.1 観察サマリー

| 現象 | 原因（技術） | 設計上の問題 |
|------|----------------|--------------|
| **Tone 汚染** | ペルソナ先頭が `voice.tone` に merge され、compile で `Tone: …` 行になる | Tone は応答スタイル用であり、アイデンティティ格納場所ではない |
| **部分注入** | Capture → proposal は先頭数行・最大 5 項目。Insert は Profile 全体を compile するが system 行は要約 | 長文ペルソナの「深層」が LLM に届かない |
| **PII 露出** | email・本名が `knowledge.concepts` にフラット列挙 | cross-LLM ハンドオフ時の機密区分が未定義 |
| **context 空** | `MyContext.md` がスケルトンのまま | `context_index` はあるが中身運用ルールが無い |

### 1.2 なぜ「dogfood」か

開発者が **自分の Sayane を自分の跨 LLM 作業で使う** 実践。自動テストでは見えない「意味論的に正しい配置」を検証する。

---

## 2. 設計原則

1. **短い・安定・LLM 向け制御** → Profile YAML の該当セクション（system / constraints に近い）
2. **長い・更新頻度低・参照用** → `context/*.md`（Prompt IR の `context` 本文）
3. **PII・機密** → `identity` の最小化 + Confidentiality Policy +（Commercial）暗号化レイヤー
4. **未確認・推測** → `context/notes/unverified.md`（断定しない）
5. **Capture は候補** → 全文ペルソナの一次投入手段にしない

```text
外部ペルソナ YAML / チャット出力
        ↓ 手動整理 or 分割キャプチャ
Profile（構造化） + context/（長文）
        ↓ build_prompt_ir
Prompt IR: system | context | constraints
        ↓ Adapter
ChatGPT / Claude context packet → Extension Insert
```

---

## 3. 意味層と配置マッピング

### 3.1 層定義

| 層 | 意味 | 典型コンテンツ | コンパイル先（現行） |
|----|------|------------------|----------------------|
| **PII** | 個人識別・連絡先 | 本名、email、ORCID | `identity.*`（**自動 merge 不可**） |
| **Identity** | 役割・組織・呼称（非 PII 中心） | handle、roles、AI 呼称 | `identity` + `context/identity.md` |
| **Tone** | 応答スタイルのみ | 簡潔、批判歓迎、詩的×厳密 | `voice.tone`（**短いフレーズのみ**） |
| **Values** | 倫理・判断基準 | 尊厳、共鳴、不確実性の明示 | `values.core` |
| **Policy** | 実行時制約 | avoid / prefer | `policy.response.*` |
| **Theory** | 理論体系・造語・論文 | Resonanceverse、ΔM、RDE | `context/theory.md` + `knowledge.concepts`（索引） |
| **Projects** | プロジェクト一覧 | 各プロジェクト名 | `context/projects.md` + concepts ラベル |
| **Formation / Health** | 形成史・健康（センシティブ） | 病歴、原体験 | `context/private/`（任意・区分付き） |
| **Interaction** | 対話・開発スタイル | TDD、反論歓迎 | `voice.tone` + `policy.response.prefer` |
| **Unverified** | 未確認メタ | 推定のみの学歴等 | `context/notes/unverified.md` |

### 3.2 外部ペルソナ YAML → Sayane マッピング（例）

| ソースキー（例） | 置き場所 | Capture 可否 |
|------------------|----------|----------------|
| `person.name.*` | `identity`（PII は手動・最小） | ❌ 自動 merge 不可 |
| `person.contact.*` | **手動** / Confidentiality Policy | ❌ |
| `organization.roles` | `identity.roles` | △ 短いリストのみ、要 `--force-critical` |
| `relationships.ai_naming` | `context/identity.md` | ❌ 長文はファイル |
| `interaction_style.*` | `voice.tone` + `policy.response.prefer` | △ 箇条書き単位で分割キャプチャ |
| `philosophy.*` | `context/theory.md` | ❌ ファイル編集 |
| `theory.*` | `context/theory.md` | ❌ |
| `projects.*` | `context/projects.md` | ❌（例: `Melotone:` が `tone:` に誤爆しうる） |
| `health.*` | `context/private/health.md` | ❌ |
| `unverified.*` | `context/notes/unverified.md` | ❌ |

**構造化ペルソナ（`person:` + `projects:` + … 複数ルート）** は Level 1 ヒューリスティックで `knowledge.concepts` に落ちるが、**中身は concepts リストに載せず** `context/` へ移すのが本設計の運用。

---

## 4. 推奨ディレクトリレイアウト

```text
~/.sayane/profiles/default/
  sayane.profile.yaml      # 短い制御面のみ
  context/
    MyContext.md          # エントリポイント（要約 + 索引）
    AI_HANDOFF.md         # merge 方針・RDE 要約（既存）
    identity.md           # 呼称・関係・役割（PII 以外）
    theory.md             # 哲学・理論体系
    projects.md           # プロジェクト群
    interaction.md        # 対話スタイル・開発原則
    notes/
      unverified.md       # 断定しない事項
      rde-heuristic.md    # RDE 定義本体（ラベルだけを concepts に置かない）
    private/              # 任意: センシティブ（Confidentiality 区分を上げる）
      health.md
      formation.md
```

### 4.1 `sayane.profile.yaml` の理想形（要約）

```yaml
identity:
  name: "…"              # 表示名最小
  preferred_name: "example"
  roles: ["developer"]
voice:
  default_language: "ja"
  tone:
    - "批判的検討を歓迎"
    - "詩的表現と技術的厳密性の両立"
values:
  core:
    - "共鳴する存在としての AGI"
    - "明示的不確実性"
knowledge:
  concepts:
    - "RDE"
    - "Resonanceverse"
    # email・長文ペルソナ見出しは載せない
policy:
  response:
    prefer:
      - "具体的実装へ言及"
    avoid:
      - "同調・称賛の連発"
context_index:
  entrypoint: "context/MyContext.md"
  handoff: "context/AI_HANDOFF.md"
  entries:
    - "context/theory.md"
    - "context/projects.md"
    - "context/interaction.md"
    - "context/notes/unverified.md"
```

`storage index` で `entries` を `context/` から再生成できる（[Storage マニュアル](storage-manual.md)）。**`context/private/` 以下は自動 index から除外**（PII・センシティブ）。含める場合のみ `entries` へ手動追加。

---

## 5. Compile / Insert 時の出力対応（現行実装）

`build_prompt_ir`（`builder.py`）の対応:

| Prompt IR | 内容 | 含めてはいけないもの |
|-----------|------|----------------------|
| **system** | identity 要約、language、**Tone**、values 要約、concepts ラベル | ペルソナ全文、email、YAML 見出し |
| **context** | `context_index` パス + **Markdown 本文** | — |
| **constraints** | policy avoid / prefer | — |

**Insert（文脈を挿入）** はこの IR を LLM 向けに整形したテキストを入力欄に入れるだけ。配置を直さない限り Tone 汚染は再発する。

---

## 6. Capture / Candidate 運用ルール

| ルール | 理由 |
|--------|------|
| 全文ペルソナ YAML を一度に Capture しない | proposal 5 行制限・誤セクション化 |
| Capture は **1 セクション相当の短文**（1〜3 箇条書き） | `voice.tone` / `values.core` 等へ意図的に入れる |
| Approve 前に **Show diff** で `section` と `add` を確認 | Tone / concepts 汚染の検知 |
| 長文は **Reject** → `context/*.md` を手編集 → `storage index` | ポータビリティの本体 |
| PII は Capture しない（手動 + Policy） | cross-LLM 露出 |

Level 1 ヒューリスティックは **境界付きマッチ**（`heuristic_match.py`）だが、**意味論的に正しい配置の保証はしない**。

---

## 7. PII と Confidentiality

| 手段 | 適用 |
|------|------|
| `identity.name` / `preferred_name` | 自動 merge **不可**（[評価マニュアル](evaluation-manual.md) §7） |
| `~/.sayane/confidentiality/default.policy.yaml` | email・パターンの reject / warn（[Confidentiality Policy](confidentiality-policy-schema.md)） |
| Commercial `encrypted-sqlite` | 保存時暗号化（別製品） |
| compile 時 redaction | **未実装**（バックログ B4） |

Dogfood では **concepts に email を入れない** を即時運用ルールとする。

---

## 8. Dogfood クリーンアップ手順（Iteration 2 後）

1. `sayane.profile.yaml` の `voice.tone` からペルソナ見出し・`name:` 行を **削除**
2. `knowledge.concepts` から email・長文断片を **削除**
3. `context/theory.md` 等にペルソナ本体を **移動**
4. `MyContext.md` に 5〜10 行の **索引要約** を書く
5. `sayane storage index` → `sayane compile --target claude` で context 本文が載ることを確認
6. Extension **文脈を挿入** で system / user 塊を確認

---

## 9. 実装バックログ（製品）

| ID | 内容 | 優先度 |
|----|------|--------|
| B1 | compile / inspect 前に `voice.tone`・`concepts` を検証（warn）— `profile_quality.py`, `sayane profile validate` | P1 **実装済** |
| B2 | 全文ペルソナ Capture 時にガイダンス— `CaptureResponse.warnings` + Extension popup | P1 **実装済** |
| B3 | `CaptureRequest.section` 明示（ヒューリスティック override） | P2 **実装済** |
| B4 | Confidentiality Policy 連携 compile redaction | P2 |
| B5 | Persona → `context/` 分割インポート CLI（`sayane profile import-persona`） | P3 |
| B6 | Prompt IR に `persona_body` 層を追加し Adapter が system と分離 | P3 |

---

## 10. 受け入れ（この設計の Done）

Dogfood Iteration 3（2026-05-28）で以下を確認済みとする例:

- [x] `voice.tone` に 80 文字超の行が無い（または 0 件）
- [x] `knowledge.concepts` に email / `@` を含む行が無い
- [x] `context/theory.md` が空でない（理論の一次ソース）
- [x] `compile` 出力の `Tone:` にペルソナ見出しが無い
- [x] Insert 後、Claude/ChatGPT で theory / interaction が **context 本文** から読める
- [x] `context/notes/unverified.md` に未確認事項のみが集約されている

---

## 11. 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-05-28 | 初版（Dogfood Iteration 2 反映） |
