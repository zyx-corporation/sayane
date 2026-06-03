# RDE 評価 UI リデザイン指示書

## 背景と課題

Chrome Extension popup の Candidate 評価 UI が最低限未満であり、人間の取捨選択・修正・追加に過大な認知負荷をかけている。

### 現状の問題点

1. **取捨選択が困難**: ドロップダウンに `8文字ID · status · rde_class` だけ。content_preview, section, source が不可視で、どの候補を先に見るべきか判断できない
2. **評価結果が不可視**: RDEクラス・UIB 6軸スコア・notes がステータスバーに1行表示されるだけ。diff は JSON 生ダンプ（`JSON.stringify(diff, null, 2)`）
3. **修正手段がゼロ**: reject reason 入力なし、force-critical の UI 公開なし。approve/reject の2択のみ
4. **文脈の断絶**: source_url、対象セクション、content_preview がどこにも表示されない

## 設計方針

- popup のサイズ制約（幅 ~350px, 高さ ~600px）内で収める
- **リスト画面 → 詳細画面**の 2 ステップ遷移で情報密度と可読性を両立
- 既存の message passing アーキテクチャ（popup → background → bridge-client → Bridge API）を維持
- i18n 対応を維持（`data-i18n` 属性 + `t()` 関数）

---

## アーキテクチャ概要

```
popup.html
├── #view-list    ← Candidate リスト画面（初期表示）
│   ├── Profile select, Capture buttons, Insert buttons（既存）
│   └── Candidate カードリスト（新規）
│
└── #view-detail  ← Candidate 詳細画面（カード選択で遷移）
    ├── ← 戻るボタン
    ├── Candidate ヘッダー（ID, status, RDE バッジ）
    ├── メタ情報（section, source, captured_at）
    ├── Content preview
    ├── 評価パネル（RDE + UIB + notes）
    ├── Diff パネル
    └── アクションバー（Evaluate, Approve, Reject + オプション）
```

---

## 変更対象ファイル一覧

| ファイル | 変更内容 |
|----------|----------|
| `extension/popup.html` | 2画面構造へ書き換え、CSS 追加 |
| `extension/src/popup.ts` | 画面遷移ロジック、詳細表示、新 UI イベント |
| `extension/src/types.ts` | `BRIDGE_GET_CANDIDATE` メッセージ型追加、`CandidateDetail` 型追加 |
| `extension/src/bridge-client.ts` | `getCandidate()` 関数追加 |
| `extension/src/background.ts` | `BRIDGE_GET_CANDIDATE` ハンドラ追加 |
| `extension/locale/en.json` | 新 UI キー追加 |
| `extension/locale/ja.json` | 新 UI キー追加 |

バックエンド（Python）変更は不要。`GET /candidates/{id}` エンドポイントは既存（`candidate_api.py:get_candidate`）で、完全な `CandidateUpdate` JSON を返す。

---

## 1. 型定義の追加（`types.ts`）

### 1.1 `CandidateDetail` インターフェース追加

Bridge の `GET /candidates/{id}` が返す完全な CandidateUpdate に対応する型を追加する。

```typescript
export interface CandidateDetail {
  id: string;
  version: string;
  kind: "CandidateUpdate";
  status: "pending" | "evaluated" | "approved" | "rejected";
  target_profile_id: string;
  content: string;
  source: {
    type: string;
    uri: string | null;
    captured_at: string;
  };
  proposal: {
    section: string;
    add: string[];
    summary: string | null;
  };
  evaluation: {
    level: number;
    rde_class: string;
    notes: string[];
    uib: {
      UD: number;
      MI: number;
      CH: number;
      DT: number;
      VP: number;
      FG: number;
    };
    evaluated_at: string;
    llm_review: {
      model: string;
      level: number;
      rde_class: string | null;
      notes: string[];
      uib: Record<string, number> | null;
    } | null;
  } | null;
}
```

### 1.2 `CandidateDiff` インターフェース修正

実際の diff レスポンス構造に合わせて明確化する。

```typescript
export interface CandidateDiff {
  profile_id: string;
  candidate_id: string;
  section: string;
  add: string[];
  already_present: string[];
  note?: string;
  proposed_add?: string[];
}
```

### 1.3 `BackgroundMessage` に追加

```typescript
| { type: "BRIDGE_GET_CANDIDATE"; candidateId: string }
```

---

## 2. Bridge Client 追加（`bridge-client.ts`）

### 2.1 `getCandidate()` 関数追加

```typescript
export async function getCandidate(candidateId: string): Promise<CandidateDetail> {
  const res = await bridgeFetch(`/candidates/${encodeURIComponent(candidateId)}`);
  return (await res.json()) as CandidateDetail;
}
```

import に `CandidateDetail` を追加。

---

## 3. Background 追加（`background.ts`）

### 3.1 import に `getCandidate` を追加

### 3.2 switch に case 追加

```typescript
case "BRIDGE_GET_CANDIDATE":
  return { ok: true, data: await getCandidate(message.candidateId) };
```

---

## 4. HTML 構造（`popup.html`）

既存の `<body>` 内を `#view-list` と `#view-detail` の 2 つの `<div>` に分割する。

### 4.1 リスト画面（`#view-list`）

既存の Profile select, Capture, Insert セクションはそのまま残す。Candidate セクションのみ以下に置き換え。

```html
<div class="section" id="candidate-section">
  <div class="row" style="align-items: center;">
    <label data-i18n="candidate.label" style="margin:0; flex:1;">Candidate</label>
    <button type="button" id="btn-refresh-candidates"
            class="btn-icon" data-i18n-title="candidate.refresh">↻</button>
  </div>
  <div id="candidate-list" class="candidate-list">
    <!-- JS で動的生成 -->
  </div>
</div>
```

ドロップダウン (`<select id="candidate-select">`) を削除し、カードリストに置き換える。

### 4.2 詳細画面（`#view-detail`）

```html
<div id="view-detail" hidden>
  <!-- ヘッダー -->
  <div class="detail-header">
    <button type="button" id="btn-back" class="btn-icon">←</button>
    <span id="detail-id" class="detail-id"></span>
    <span id="detail-rde-badge" class="rde-badge"></span>
  </div>

  <!-- メタ情報 -->
  <dl class="detail-meta">
    <div class="meta-row">
      <dt data-i18n="detail.section">Section</dt>
      <dd id="detail-section"></dd>
    </div>
    <div class="meta-row">
      <dt data-i18n="detail.source">Source</dt>
      <dd id="detail-source"></dd>
    </div>
    <div class="meta-row">
      <dt data-i18n="detail.captured_at">Captured</dt>
      <dd id="detail-captured-at"></dd>
    </div>
    <div class="meta-row">
      <dt data-i18n="detail.status">Status</dt>
      <dd id="detail-status"></dd>
    </div>
  </dl>

  <!-- Content preview -->
  <details class="detail-section" id="content-details">
    <summary data-i18n="detail.content">Content</summary>
    <pre id="detail-content" class="content-preview"></pre>
  </details>

  <!-- Proposal -->
  <details class="detail-section" open id="proposal-details">
    <summary data-i18n="detail.proposal">Proposal</summary>
    <ul id="detail-proposal-items" class="proposal-list"></ul>
    <p id="detail-proposal-summary" class="proposal-summary"></p>
  </details>

  <!-- 評価結果（評価済みの場合のみ表示） -->
  <div id="evaluation-panel" hidden>
    <details class="detail-section" open>
      <summary data-i18n="detail.evaluation">Evaluation</summary>

      <!-- RDE クラス + レベル -->
      <div class="eval-header">
        <span id="eval-rde-class" class="rde-badge"></span>
        <span id="eval-level" class="eval-level"></span>
      </div>

      <!-- UIB 6軸バー -->
      <div id="uib-chart" class="uib-chart">
        <!-- 各軸: UD, MI, CH, DT, VP, FG -->
      </div>

      <!-- Notes -->
      <ul id="eval-notes" class="eval-notes"></ul>

      <!-- LLM Review（あれば） -->
      <div id="llm-review-panel" hidden>
        <p class="llm-review-header">
          <span data-i18n="detail.llm_review">LLM Review</span>:
          <span id="llm-model"></span>
        </p>
        <ul id="llm-notes" class="eval-notes"></ul>
      </div>
    </details>
  </div>

  <!-- Diff -->
  <details class="detail-section" id="diff-details">
    <summary data-i18n="detail.diff">Diff</summary>
    <div id="detail-diff" class="diff-panel"></div>
  </details>

  <!-- アクションバー -->
  <div class="action-bar">
    <div class="row">
      <select id="detail-eval-level">
        <option value="1" data-i18n="candidate.level1">Level 1</option>
        <option value="2" data-i18n="candidate.level2">Level 2</option>
      </select>
      <button type="button" id="btn-detail-evaluate"
              class="btn-primary" data-i18n="candidate.evaluate">Evaluate</button>
    </div>

    <!-- Reject reason -->
    <input type="text" id="reject-reason"
           data-i18n-placeholder="detail.reject_reason_placeholder"
           placeholder="Rejection reason (optional)" />

    <!-- Force-critical チェックボックス -->
    <label class="force-critical-label" id="force-critical-row" hidden>
      <input type="checkbox" id="force-critical-check" />
      <span data-i18n="detail.force_critical">Force approve (critical)</span>
    </label>

    <div class="row">
      <button type="button" id="btn-detail-approve"
              class="btn-approve" data-i18n="candidate.approve">Approve</button>
      <button type="button" id="btn-detail-reject"
              class="btn-reject" data-i18n="candidate.reject">Reject</button>
    </div>
  </div>

  <p id="detail-status-msg" class="status"></p>
</div>
```

---

## 5. CSS スタイル

`popup.html` の `<style>` に追加。既存スタイルとの統一感を維持する（system-ui, #333 テキスト, #b00020 エラー, #f5f5f5 背景）。

### 5.1 RDE クラスバッジの色定義

```css
.rde-badge {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
}
.rde-preserved          { background: #e0e0e0; color: #333; }
.rde-authorized         { background: #fff3e0; color: #e65100; }
.rde-inferred           { background: #e8f5e9; color: #2e7d32; }
.rde-unresolved         { background: #fff8e1; color: #f9a825; }
.rde-suspicious         { background: #fff3e0; color: #bf360c; }
.rde-critical           { background: #ffebee; color: #b71c1c; }
```

色の意味:
- 緑系 = 安全（Inferred Extension）
- 黄系 = 注意（Unresolved Gap）
- オレンジ系 = 要確認（Authorized Transformation, Suspicious Drift）
- 赤系 = 危険（Critical Distortion）
- グレー = 変更なし（Preserved）

### 5.2 Candidate カード

```css
.candidate-list {
  max-height: 240px;
  overflow-y: auto;
}

.candidate-card {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 8px;
  margin-bottom: 6px;
  cursor: pointer;
  transition: border-color 0.15s;
}
.candidate-card:hover {
  border-color: #999;
}

.candidate-card .card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.candidate-card .card-id {
  font-family: monospace;
  font-size: 0.75rem;
  color: #666;
}
.candidate-card .card-section {
  font-size: 0.7rem;
  color: #888;
  margin-left: auto;
}
.candidate-card .card-preview {
  font-size: 0.75rem;
  color: #555;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.candidate-card .card-meta {
  font-size: 0.65rem;
  color: #999;
  margin-top: 4px;
}
```

### 5.3 詳細画面

```css
#view-detail {
  /* popup.html の body margin は既存の 12px を流用 */
}
.detail-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.detail-id {
  font-family: monospace;
  font-size: 0.8rem;
  color: #555;
}
.btn-icon {
  background: none;
  border: 1px solid #ccc;
  border-radius: 3px;
  width: auto;
  padding: 4px 8px;
  cursor: pointer;
  font-size: 0.85rem;
}

.detail-meta {
  margin: 0 0 8px;
}
.meta-row {
  display: flex;
  gap: 8px;
  font-size: 0.75rem;
  padding: 2px 0;
}
.meta-row dt {
  color: #888;
  min-width: 60px;
  flex-shrink: 0;
}
.meta-row dd {
  margin: 0;
  color: #333;
  word-break: break-all;
}

.detail-section {
  margin-bottom: 6px;
}
.detail-section summary {
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 0;
}

.content-preview {
  font-size: 0.7rem;
  max-height: 100px;
  overflow: auto;
  background: #f5f5f5;
  padding: 6px;
  margin: 4px 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.proposal-list {
  font-size: 0.75rem;
  margin: 4px 0 4px 1.2em;
  padding: 0;
}
.proposal-list li {
  margin-bottom: 2px;
}
.proposal-summary {
  font-size: 0.7rem;
  color: #666;
  margin: 2px 0;
}
```

### 5.4 評価パネル

```css
.eval-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 6px 0;
}
.eval-level {
  font-size: 0.7rem;
  color: #888;
}
.eval-notes {
  font-size: 0.7rem;
  color: #555;
  margin: 4px 0 4px 1.2em;
  padding: 0;
}
.eval-notes li {
  margin-bottom: 2px;
}
.llm-review-header {
  font-size: 0.7rem;
  color: #666;
  margin: 6px 0 2px;
}
```

### 5.5 UIB 6軸バーチャート

```css
.uib-chart {
  display: grid;
  grid-template-columns: 28px 1fr 32px;
  gap: 2px 6px;
  align-items: center;
  margin: 6px 0;
  font-size: 0.65rem;
}
.uib-chart .uib-label {
  color: #888;
  text-align: right;
  font-weight: 600;
}
.uib-chart .uib-bar-bg {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
}
.uib-chart .uib-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}
.uib-chart .uib-value {
  color: #666;
  text-align: right;
}

/* UIB バーの色: 値に応じて JS で設定（下記参照） */
```

### 5.6 Diff パネル

```css
.diff-panel {
  font-size: 0.7rem;
  padding: 6px;
  background: #f5f5f5;
  border-radius: 3px;
  margin: 4px 0;
}
.diff-panel .diff-add {
  color: #2e7d32;
}
.diff-panel .diff-add::before {
  content: "+ ";
  font-weight: 600;
}
.diff-panel .diff-present {
  color: #888;
  text-decoration: line-through;
}
.diff-panel .diff-present::before {
  content: "= ";
}
.diff-panel .diff-note {
  color: #e65100;
  font-style: italic;
}
```

### 5.7 アクションバー

```css
.action-bar {
  border-top: 1px solid #ddd;
  padding-top: 8px;
  margin-top: 8px;
}
.action-bar input[type="text"] {
  width: 100%;
  box-sizing: border-box;
  padding: 6px 8px;
  font-size: 0.75rem;
  margin-bottom: 6px;
  border: 1px solid #ccc;
  border-radius: 3px;
}
.force-critical-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.7rem;
  color: #b71c1c;
  margin-bottom: 6px;
  cursor: pointer;
}
.btn-primary {
  background: #1976d2;
  color: #fff;
  border: none;
  border-radius: 3px;
}
.btn-approve {
  background: #2e7d32;
  color: #fff;
  border: none;
  border-radius: 3px;
}
.btn-reject {
  background: #c62828;
  color: #fff;
  border: none;
  border-radius: 3px;
}
```

### 5.8 ステータスバッジ（カード内用）

```css
.status-badge {
  font-size: 0.6rem;
  padding: 1px 4px;
  border-radius: 2px;
}
.status-pending   { background: #e3f2fd; color: #1565c0; }
.status-evaluated { background: #f3e5f5; color: #7b1fa2; }
.status-approved  { background: #e8f5e9; color: #2e7d32; }
.status-rejected  { background: #fce4ec; color: #c62828; }
```

---

## 6. ロジック（`popup.ts`）

### 6.1 画面遷移

```typescript
function showListView(): void {
  $("view-list").hidden = false;
  $("view-detail").hidden = true;
}

function showDetailView(): void {
  $("view-list").hidden = true;
  $("view-detail").hidden = false;
}
```

`#btn-back` のクリックで `showListView()` を呼ぶ。

### 6.2 Candidate カードリスト描画

`loadCandidates()` を書き換え。`<select>` への option 追加ではなく、カード DOM を生成する。

```typescript
async function loadCandidates(): Promise<void> {
  const container = $("candidate-list");
  const res = await send({ type: "BRIDGE_LIST_CANDIDATES" });
  if (!res.ok) { setStatus(localizeError(res.error), true); return; }

  const items = res.data as CandidateSummary[];
  container.innerHTML = "";

  if (items.length === 0) {
    container.innerHTML = `<p class="no-candidates">${t("candidate.none")}</p>`;
    return;
  }

  // ソート: Critical Distortion → Suspicious Drift → ... → approved/rejected を末尾
  const sorted = sortCandidates(items);

  for (const c of sorted) {
    const card = document.createElement("div");
    card.className = "candidate-card";
    card.dataset.candidateId = c.id;

    const rdeClass = rdeClassToCssClass(c.rde_class);
    const rdeBadge = c.rde_class
      ? `<span class="rde-badge ${rdeClass}">${c.rde_class}</span>`
      : "";
    const statusBadge = `<span class="status-badge status-${c.status}">${c.status}</span>`;

    card.innerHTML = `
      <div class="card-header">
        ${statusBadge}
        ${rdeBadge}
        <span class="card-section">${c.target_profile_id}:${sectionShortName(c)}</span>
      </div>
      <div class="card-preview">${escapeHtml(c.content_preview)}</div>
      <div class="card-meta">
        <span class="card-id">${c.id.slice(0, 12)}</span>
        · ${formatRelativeTime(c.captured_at)}
      </div>
    `;

    card.addEventListener("click", () => openCandidateDetail(c.id));
    container.appendChild(card);
  }
}
```

注: `CandidateSummary` には `proposal.section` がないが `content_preview` はある。セクション情報を表示するためには以下の選択肢がある:
- **案 A**: `_candidate_summary()` (Python) に `section` フィールドを追加し、`CandidateSummary` 型にも追加（推奨。1行の変更）
- **案 B**: カードクリック時に `GET /candidates/{id}` で取得するまでセクション非表示

→ **案 A を採用**。`candidate_api.py` の `_candidate_summary()` に以下を追加:

```python
"section": c.proposal.section,
```

`CandidateSummary`（TypeScript）にも:

```typescript
section: string;
```

### 6.3 ソート関数

```typescript
const RDE_SEVERITY: Record<string, number> = {
  "Critical Distortion": 5,
  "Suspicious Drift": 4,
  "Authorized Transformation": 3,
  "Unresolved Gap": 2,
  "Inferred Extension": 1,
  "Preserved": 0,
};

const STATUS_PRIORITY: Record<string, number> = {
  pending: 0,
  evaluated: 1,
  approved: 2,
  rejected: 3,
};

function sortCandidates(items: CandidateSummary[]): CandidateSummary[] {
  return [...items].sort((a, b) => {
    const sa = STATUS_PRIORITY[a.status] ?? 9;
    const sb = STATUS_PRIORITY[b.status] ?? 9;
    if (sa !== sb) return sa - sb;
    const ra = RDE_SEVERITY[a.rde_class ?? ""] ?? -1;
    const rb = RDE_SEVERITY[b.rde_class ?? ""] ?? -1;
    return rb - ra; // 重篤度降順
  });
}
```

### 6.4 詳細画面表示

```typescript
async function openCandidateDetail(candidateId: string): Promise<void> {
  showDetailView();
  setDetailStatus(t("status.loading"));

  // 完全な Candidate データを取得
  const res = await send({ type: "BRIDGE_GET_CANDIDATE", candidateId });
  if (!res.ok) {
    setDetailStatus(localizeError(res.error), true);
    return;
  }

  const c = res.data as CandidateDetail;
  currentCandidateId = c.id;

  // ヘッダー
  ($("detail-id") as HTMLSpanElement).textContent = c.id;
  renderRdeBadge($("detail-rde-badge"), c.evaluation?.rde_class ?? null);
  ($("detail-status") as HTMLElement).textContent = c.status;

  // メタ情報
  ($("detail-section") as HTMLElement).textContent = c.proposal.section;
  ($("detail-source") as HTMLElement).textContent = c.source.uri
    ? `${c.source.type} — ${c.source.uri}`
    : c.source.type;
  ($("detail-captured-at") as HTMLElement).textContent =
    formatRelativeTime(c.source.captured_at);

  // Content
  ($("detail-content") as HTMLPreElement).textContent = c.content;

  // Proposal
  renderProposal(c.proposal);

  // Evaluation（あれば）
  if (c.evaluation) {
    renderEvaluation(c.evaluation);
    $("evaluation-panel").hidden = false;
  } else {
    $("evaluation-panel").hidden = true;
  }

  // Diff は別途取得（details の open 時、または自動）
  renderDiff(candidateId);

  // force-critical 行の表示制御
  const needsForce =
    c.evaluation?.rde_class === "Critical Distortion" ||
    (c.proposal.section !== "knowledge.concepts");
  $("force-critical-row").hidden = !needsForce;

  setDetailStatus("");
}
```

### 6.5 UIB バーチャート描画

```typescript
const UIB_LABELS: Record<string, string> = {
  UD: "UD",  // Uncertainty Detection
  MI: "MI",  // Material Integrity
  CH: "CH",  // Coherence
  DT: "DT",  // Diegetic Truthfulness
  VP: "VP",  // Value Preservation
  FG: "FG",  // Factual Grounding
};

function uibBarColor(value: number): string {
  if (value >= 0.7) return "#4caf50";
  if (value >= 0.4) return "#ff9800";
  return "#f44336";
}

function renderUIBChart(uib: Record<string, number>): void {
  const container = $("uib-chart");
  container.innerHTML = "";
  for (const [key, label] of Object.entries(UIB_LABELS)) {
    const value = uib[key] ?? 0;
    const pct = Math.round(value * 100);

    const labelEl = document.createElement("span");
    labelEl.className = "uib-label";
    labelEl.textContent = label;

    const barBg = document.createElement("div");
    barBg.className = "uib-bar-bg";
    const barFill = document.createElement("div");
    barFill.className = "uib-bar-fill";
    barFill.style.width = `${pct}%`;
    barFill.style.background = uibBarColor(value);
    barBg.appendChild(barFill);

    const valueEl = document.createElement("span");
    valueEl.className = "uib-value";
    valueEl.textContent = value.toFixed(2);

    container.appendChild(labelEl);
    container.appendChild(barBg);
    container.appendChild(valueEl);
  }
}
```

### 6.6 RDE バッジ描画

```typescript
function rdeClassToCssClass(rdeClass: string | null): string {
  if (!rdeClass) return "";
  const map: Record<string, string> = {
    "Preserved": "rde-preserved",
    "Authorized Transformation": "rde-authorized",
    "Inferred Extension": "rde-inferred",
    "Unresolved Gap": "rde-unresolved",
    "Suspicious Drift": "rde-suspicious",
    "Critical Distortion": "rde-critical",
  };
  return map[rdeClass] ?? "";
}

function renderRdeBadge(el: HTMLElement, rdeClass: string | null): void {
  if (!rdeClass) {
    el.hidden = true;
    return;
  }
  el.hidden = false;
  el.textContent = rdeClass;
  el.className = `rde-badge ${rdeClassToCssClass(rdeClass)}`;
}
```

### 6.7 Diff 描画（人間に読める形式）

```typescript
async function renderDiff(candidateId: string): Promise<void> {
  const container = $("detail-diff");
  const res = await send({ type: "BRIDGE_DIFF_CANDIDATE", candidateId });
  if (!res.ok) {
    container.innerHTML = `<p class="diff-note">${escapeHtml(res.error)}</p>`;
    return;
  }

  const diff = res.data as CandidateDiff;
  container.innerHTML = "";

  if (diff.note) {
    const noteEl = document.createElement("p");
    noteEl.className = "diff-note";
    noteEl.textContent = diff.note;
    container.appendChild(noteEl);
  }

  const addItems = diff.add ?? diff.proposed_add ?? [];
  for (const item of addItems) {
    const line = document.createElement("div");
    line.className = "diff-add";
    line.textContent = item;
    container.appendChild(line);
  }

  for (const item of diff.already_present ?? []) {
    const line = document.createElement("div");
    line.className = "diff-present";
    line.textContent = item;
    container.appendChild(line);
  }

  if (addItems.length === 0 && (diff.already_present ?? []).length === 0 && !diff.note) {
    container.textContent = t("detail.diff_empty");
  }
}
```

### 6.8 Evaluation 描画

```typescript
function renderEvaluation(ev: CandidateDetail["evaluation"]): void {
  if (!ev) return;

  renderRdeBadge($("eval-rde-class"), ev.rde_class);
  ($("eval-level") as HTMLElement).textContent = `Level ${ev.level}`;

  // UIB
  renderUIBChart(ev.uib as unknown as Record<string, number>);

  // Notes
  const notesList = $("eval-notes");
  notesList.innerHTML = "";
  for (const note of ev.notes) {
    const li = document.createElement("li");
    li.textContent = note;
    notesList.appendChild(li);
  }

  // LLM Review
  if (ev.llm_review) {
    $("llm-review-panel").hidden = false;
    ($("llm-model") as HTMLElement).textContent =
      `${ev.llm_review.model} (L${ev.llm_review.level})`;
    const llmNotes = $("llm-notes");
    llmNotes.innerHTML = "";
    for (const note of ev.llm_review.notes) {
      const li = document.createElement("li");
      li.textContent = note;
      llmNotes.appendChild(li);
    }
  } else {
    $("llm-review-panel").hidden = true;
  }
}
```

### 6.9 アクションイベント（詳細画面）

既存の `#btn-evaluate`, `#btn-approve`, `#btn-reject` イベントを詳細画面のボタンに移行する。

```typescript
$("btn-detail-evaluate").addEventListener("click", async () => {
  if (!currentCandidateId) return;
  const level = Number(($("detail-eval-level") as HTMLSelectElement).value) || 1;
  setDetailStatus(t("status.loading"));
  const res = await send({
    type: "BRIDGE_EVALUATE_CANDIDATE",
    candidateId: currentCandidateId,
    level,
  });
  if (!res.ok) { setDetailStatus(localizeError(res.error), true); return; }
  setDetailStatus(t("status.evaluated", {
    summary: evaluationSummary(res.data as Record<string, unknown>),
  }));
  // 詳細を再読み込み
  await openCandidateDetail(currentCandidateId);
});

$("btn-detail-approve").addEventListener("click", async () => {
  if (!currentCandidateId) return;
  const forceCritical = ($("force-critical-check") as HTMLInputElement).checked;
  const res = await send({
    type: "BRIDGE_APPROVE_CANDIDATE",
    candidateId: currentCandidateId,
    forceCritical,
  });
  if (!res.ok) { setDetailStatus(localizeError(res.error), true); return; }
  setDetailStatus(t("status.approved", { id: currentCandidateId.slice(0, 8) }));
  await openCandidateDetail(currentCandidateId);
});

$("btn-detail-reject").addEventListener("click", async () => {
  if (!currentCandidateId) return;
  const reason = ($("reject-reason") as HTMLInputElement).value.trim() || undefined;
  const res = await send({
    type: "BRIDGE_REJECT_CANDIDATE",
    candidateId: currentCandidateId,
    reason,
  });
  if (!res.ok) { setDetailStatus(localizeError(res.error), true); return; }
  setDetailStatus(t("status.rejected", { id: currentCandidateId.slice(0, 8) }));
  await openCandidateDetail(currentCandidateId);
});
```

### 6.10 ユーティリティ

```typescript
let currentCandidateId: string | null = null;

function setDetailStatus(text: string, isError = false): void {
  const el = $("detail-status-msg");
  el.textContent = text;
  el.className = isError ? "status error" : "status";
}

function escapeHtml(text: string): string {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function formatRelativeTime(isoDate: string): string {
  const d = new Date(isoDate);
  const now = Date.now();
  const diffMs = now - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return t("time.just_now");
  if (diffMin < 60) return t("time.minutes_ago", { n: diffMin });
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return t("time.hours_ago", { n: diffH });
  const diffD = Math.floor(diffH / 24);
  return t("time.days_ago", { n: diffD });
}

function renderProposal(proposal: CandidateDetail["proposal"]): void {
  const list = $("detail-proposal-items");
  list.innerHTML = "";
  for (const item of proposal.add) {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  }
  const summary = $("detail-proposal-summary");
  summary.textContent = proposal.summary ?? "";
  summary.hidden = !proposal.summary;
}
```

---

## 7. i18n キー追加

### `locale/en.json` に追加

```json
"detail.section": "Section",
"detail.source": "Source",
"detail.captured_at": "Captured",
"detail.status": "Status",
"detail.content": "Content",
"detail.proposal": "Proposal",
"detail.evaluation": "Evaluation",
"detail.llm_review": "LLM Review",
"detail.diff": "Diff",
"detail.diff_empty": "No changes",
"detail.force_critical": "Force approve (critical section)",
"detail.reject_reason_placeholder": "Rejection reason (optional)",
"time.just_now": "just now",
"time.minutes_ago": "{n}m ago",
"time.hours_ago": "{n}h ago",
"time.days_ago": "{n}d ago"
```

### `locale/ja.json` に追加

```json
"detail.section": "セクション",
"detail.source": "ソース",
"detail.captured_at": "キャプチャ日時",
"detail.status": "ステータス",
"detail.content": "本文",
"detail.proposal": "提案",
"detail.evaluation": "評価",
"detail.llm_review": "LLM レビュー",
"detail.diff": "差分",
"detail.diff_empty": "変更なし",
"detail.force_critical": "強制承認（重要セクション）",
"detail.reject_reason_placeholder": "却下理由（任意）",
"time.just_now": "たった今",
"time.minutes_ago": "{n}分前",
"time.hours_ago": "{n}時間前",
"time.days_ago": "{n}日前"
```

---

## 8. Python 側の軽微変更

### 8.1 `candidate_api.py` — `_candidate_summary()` にセクション追加

```python
def _candidate_summary(c: CandidateUpdate) -> dict[str, Any]:
    preview = c.content if len(c.content) <= 200 else c.content[:200] + "..."
    return {
        "id": c.id,
        "status": c.status,
        "target_profile_id": c.target_profile_id,
        "source": c.source.type,
        "source_url": c.source.uri,
        "captured_at": c.source.captured_at.isoformat(),
        "rde_class": c.evaluation.rde_class if c.evaluation else None,
        "evaluation_level": c.evaluation.level if c.evaluation else None,
        "section": c.proposal.section,               # ← 追加
        "content_preview": preview,
    }
```

TypeScript の `CandidateSummary` にも `section: string;` を追加。

---

## 9. 削除する既存要素

- `<select id="candidate-select">` — カードリストに置換
- `<select id="eval-level">` + `<button id="btn-refresh-candidates">` の `.row` — リスト画面のリフレッシュボタンのみ残す
- `<button id="btn-evaluate">`, `<button id="btn-diff">`, `<pre id="diff-preview">` — 詳細画面に移動
- `<button id="btn-approve">`, `<button id="btn-reject">` の `.row` — 詳細画面に移動

リスト画面に残るのは: Profile, Capture, Insert, Candidate カードリスト（+ Refresh ボタン）, Options。

---

## 10. テスト確認事項

- [ ] カードリストが正しくソートされる（pending > evaluated, 重篤度降順）
- [ ] カードクリック→詳細画面遷移→戻るボタンで元に戻る
- [ ] 未評価 Candidate: evaluation パネルが非表示、Evaluate ボタンのみ有効
- [ ] 評価済み Candidate: RDE バッジ色、UIB バーチャート、notes 表示
- [ ] Critical Distortion / 非 knowledge.concepts セクション → force-critical チェックボックス表示
- [ ] Approve (force-critical) が正しく `forceCritical: true` を送信
- [ ] Reject reason が正しく送信される
- [ ] Diff パネルに add は緑、already_present は取り消し線グレーで表示
- [ ] i18n: en / ja 切り替えで全テキストが正しく翻訳
- [ ] LLM Review パネル: Level 2+ で llm_review がある場合にモデル名と notes 表示
- [ ] 空の Candidate リスト時の表示
- [ ] source_url がある場合/ない場合のメタ情報表示

---

## 11. 実装順序（推奨）

1. **型定義**: `types.ts` に `CandidateDetail`, `BackgroundMessage` 追加, `CandidateSummary` に `section` 追加
2. **Python**: `_candidate_summary()` に `section` 追加
3. **Bridge client**: `getCandidate()` 追加
4. **Background**: `BRIDGE_GET_CANDIDATE` ハンドラ追加
5. **HTML**: `popup.html` を 2 画面構造に書き換え、CSS 追加
6. **ロジック**: `popup.ts` を書き換え（リスト描画、詳細表示、アクション）
7. **i18n**: locale ファイルにキー追加
8. **動作確認**: `sayane serve` + Extension リロードで確認
