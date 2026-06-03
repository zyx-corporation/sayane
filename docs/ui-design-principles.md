# UI 設計の基本コンセプト

Sayane の **Chrome Extension** および将来の対話面（Web UI、デスクトップシェル等）に共通する、人間とのインタラクション設計の基本方針である。

## 0. UI は実行基盤の実行要素である

Sayane において UI は、CLI・Local Bridge・Adapter・Storage と並ぶ **実行基盤の実行要素** である。装飾や付属品ではない。

LLM とのチャット画面と**同格**である。チャットがモデルへの入力と応答の境界を担うように、Sayane の UI は **人格的文脈の入口（Capture）と出口（Insert）**、および **候補の確認・評価・承認** という人間側の実行境界を担う。

```text
[人間] ←—— UI（Capture / 確認 / 判断 / Insert）——→ [Sayane Core / Bridge]
              ↕
         LLM チャット UI（compile 結果の消費・対話）
```

ここをおろそかにすると、入出力の意味が失われる。

| おろそかにしたときに起きること | 例 |
|-------------------------------|-----|
| **入力の意味喪失** | 何を選んで Capture したか分からない、ページノイズと意図した文脈の区別がつかない |
| **中間状態の意味喪失** | 評価中か失敗か不明、provisional と確定の違いが UI に現れない |
| **出力の意味喪失** | Insert 前に何が渡るか不明、Approve が「保存したつもり」だけで差分を見ていない |

Core・RDE・Authorization が正しくても、**UI が状態と意図を伝えられなければ**、利用者は文脈更新の主体として機能できず、監査可能なパイプラインは途切れる。

T-RDE の観点からも、UI は「操作を塞ぐ壁」ではなく、**今アプリで何が起きているか**を利用者に伝える媒体である。カーソル・ラベル・無効化の理由は、その媒体の最低限の誠実さである。

## 1. 基本原則：状態を伝える

人間とのインタラクションにおいて、アプリで今何が起きているかを伝えることは UI 設計の基本である。

利用者は次を瞬時に区別できる必要がある。

| 利用者が知りたいこと | UI が伝えるべきこと |
|---------------------|---------------------|
| 処理が進行中か | **待機中** — しばらくすると進む |
| この操作は今使えないか | **不可** — 条件が満たされていない（終了後も同様） |
| 操作できるか | **通常** — クリック・入力が有効 |

**禁止**: 処理中と「今は使えない」を同じ見た目（同じカーソル・同じ無言の `disabled`）で混同すること。

## 2. カーソルと無効化の対応

### 2.1 処理中（busy）

**意味**: Bridge 通信、評価、Capture、差分読み込みなど、**非同期処理が進行中**で、他操作を並行させない／させない方がよい状態。

| 表現 | 実装 |
|------|------|
| カーソル | `wait`（砂時計系） |
| 対象 | `body.is-busy` および `#app-root`、処理待ちで無効化したボタン |
| 属性 | `data-cursor-hint="busy"` |

ラベルは可能なら進行を示す（例: 「評価中…」「Capture中…」）。`aria-busy="true"` を併用する。

### 2.2 操作不可（unavailable）

**意味**: 処理は**終了している**（またはその操作には busy が関与しない）が、**業務条件**によりまだ使えない状態。

例:

- 選択範囲が空のため Capture できない
- Bridge 未接続
- Candidate 未選択のため Evaluate / Approve できない
- RDE 分類上、そのまま Approve できない

| 表現 | 実装 |
|------|------|
| カーソル | `not-allowed` |
| 属性 | `data-cursor-hint="unavailable"` |

**補助**: ボタン近傍のヒント文、ステータス行、Bridge / ページ診断の説明で**理由**を書く（「なぜ今できないか」）。

### 2.3 判定の優先順位

ボタンを `disabled` にするとき、hint は次の順で決める。

```text
1. そのボタン自身の busy 操作が走っている → busy
2. 別操作の busy によりグローバルに待機している → busy
3. 上記以外で disabled → unavailable
```

実装: `extension/src/busy-ui.ts` の `resolveDisabledHint` / `applyExternalDisabled`。

## 3. CSS 方針（Extension）

`body.is-busy * { cursor: wait !important }` のような**全要素一括**指定は使わない。  
`button:disabled { cursor: not-allowed }` のような**一括 not-allowed** も使わない。

代わりに hint 別ルールを使う（`popup.html` / `diff.html` / `options.html` と同型）。

```css
body.is-busy,
body.is-busy #app-root {
  cursor: wait;
}
button:disabled[data-cursor-hint="busy"] {
  cursor: wait !important;
}
button:disabled[data-cursor-hint="unavailable"] {
  cursor: not-allowed !important;
}
```

参照: `extension/src/busy-ui-cursor.css.ts`（コメント用の CSS 断片）。

## 4. Busy UI コントローラ

`BusyUiController`（`busy-ui.ts`）は操作種別ごとの busy フラグを持つ。

- **busy 中**: 該当ボタンは busy ラベル + `disabled` + `data-cursor-hint="busy"`
- **busy 終了後**: `applyExternalDisabled` で業務条件に応じた `unavailable` または有効化を再適用
- **候補処理の連鎖**: `blockDuringCandidateMutation` — 評価・採用・棄却・差分読み込み中は関連ボタンを busy 扱い（他操作が進行中であることを示す）

新しいボタンや非同期処理を追加するときは、必ず `registerButton` / `applyExternalDisabled` / `applyDisabledWithCursorHint` のいずれか経由で無効化し、hint を付ける。

## 5. T-RDE / RDE との関係

| RDE・監査の考え方 | UI への落とし込み |
|------------------|-------------------|
| 評価結果は客観的事実ではない | ステータス・警告文で「仮説」「要確認」を示す（[rde-audit-policy.md](rde-audit-policy.md)） |
| 利用者許可は必要だが十分ではない | Approve は可能でも、差分・警告を読んだ上での判断を促す |
| 処理の透明性 | busy 中は `wait` で「システムが仕事中」と明示 |
| Mirror は veto ではない | 警告表示は却下 UI にしない |

UI が「黙って塞ぐ」のではなく、**進行中**と**条件不足**を区別して伝えることは、非懲罰的監査・説明責任の前提にも合致する。

## 6. 受け入れ・レビュー時の確認

Extension や対話 UI の PR では、次を確認する。

- [ ] 新規の `disabled` に `data-cursor-hint` が付いているか
- [ ] グローバル busy 中に、理由なく `not-allowed` だけが出ていないか
- [ ] 処理完了後、条件不足の操作が `unavailable`（＋理由テキスト）になっているか
- [ ] `busy-ui.test.ts` または同等のテストで hint が検証されているか

手動 UAT: [extension-acceptance-test.md](extension-acceptance-test.md) に併記してもよい。

## 7. 適用範囲

| 対象 | 適用 |
|------|------|
| Chrome Extension（popup / diff / options） | **必須**（本ドキュメントの参照実装） |
| CLI | 該当なし（TTY はスピナー・メッセージで同趣旨） |
| 将来の Web UI / Tauri | 本ドキュメントを継承 |

## 8. 関連ドキュメント

- [Chrome Extension マニュアル](extension-manual.md)
- [開発原則](development-principles.md) § UI 設計
- [CLI / Extension 設計](cli-chrome-extension.md)
- [RDE 監査ポリシー（逸脱防止）](rde-audit-policy.md)
- [Authorization Layer](authorization-layer.md)

## 変更履歴の意図

2026-06: ビジー状態で `not-allowed` が一貫して出る問題を修正し、本ドキュメントとして基本コンセプトを明文化した。
