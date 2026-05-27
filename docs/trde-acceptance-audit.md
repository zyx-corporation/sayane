# T-RDE 横断意味監査 受け入れ仕様

T-RDE（Transverse RDE）は、Ayane / OpenAyane の設計意図である「意味変化の監査」を、Sayane の受け入れテストへ移植する横断監査である。

この文書は、UIが動くか、CLIがJSONを出すか、Extensionが入力欄へ文字列を挿入できるかを確認するためのものではない。Raw / Edited / Normalize / Interpret / Export / Live を横断し、元の意図・価値・制約・不確実性がどの段階で保存・変形・逸脱したかを検査する。

---

## 1. 逸脱リスク

最大のリスクは、RDE が UI 動作確認へ縮退することである。

たとえば、Extension が `Inserted` と表示した、Bridge が 200 を返した、CLI が JSON を出した、という事実だけでは、RDE 的な受け入れ成功にはならない。

Sayane / Ayane の設計思想では、重要なのは「文字列が移動したこと」ではなく、「意味がどのように保存され、どこで許可された変形が起き、どこから危険な逸脱になるか」を監査できることである。

---

## 2. 監査対象パイプライン

| 段階 | 意味 | 主な検査対象 |
|------|------|--------------|
| Raw | 入力された元文脈・会話・Profile・Capture原文 | 原意、価値、制約、出典、不確実性 |
| Edited | 人間またはAIにより編集された文 | 主張の強化、削除、価値のすり替え |
| Normalize | 表記・形式・構造の正規化 | 表記統一による意味削減、曖昧性消去 |
| Interpret | 意味解釈・候補抽出・Candidate生成 | 推論の混入、未検証補完、価値判断の挿入 |
| Export | target/model/provider向け出力 | adapter変換による意味縮退、system/user分割の影響 |
| Live | Extension / Bridge / DOM / 実UI挿入 | UI成功による意味監査の省略、送信前後の文脈変化 |

---

## 3. 結果記録シート

| ID | 区分 | 必須 | 結果 | 実測・メモ |
|----|------|:----:|:----:|------------|
| T-RDE-01 | Raw→Edited | ✓ | | |
| T-RDE-02 | Edited→Normalize | ✓ | | |
| T-RDE-03 | Normalize→Interpret | ✓ | | |
| T-RDE-04 | Interpret→Export | ✓ | | |
| T-RDE-05 | Export→Live | ✓ | | |
| T-RDE-06 | UI縮退リスク | ✓ | | |
| T-RDE-07 | 高リスク意味逸脱 | ✓ | | |
| T-RDE-08 | Lineage / Evidence | | | |

**記号**: **P** Pass / **F** Fail / **S** Skip / **N/A** 対象外

---

## 4. 合否分類

| 分類 | 意味 | 判定 |
|------|------|------|
| `preserved` | 元の意味・価値・制約が保存された | Pass |
| `authorized_transformation` | 明示目的に沿う許可された変形 | Pass |
| `inferred_extension` | 推論・補完だが、推論であることが明示されている | 条件付き Pass |
| `unresolved` | 判断不能・追加確認が必要 | 手動確認。必須項目では原則 Fail |
| `suspicious_drift` | 元の意図からの疑わしい逸脱 | Fail |
| `critical_distortion` | 意味・価値・制約を反転または破壊する逸脱 | Fail / approve不可 |

---

## 5. 必須シナリオ

| ID | 手順 | 期待結果 |
|----|------|----------|
| T-RDE-01 | Raw Capture と Edited 文を比較する | 元の主張・価値・制約・不確実性が保存または明示的に変形されている |
| T-RDE-02 | Edited 文を Normalize する | 表記や構造は整うが、元より強い主張へ変わらない |
| T-RDE-03 | Normalize から Candidate / Interpret を生成する | 推論・補完・不確実性が明示され、未検証内容を事実化しない |
| T-RDE-04 | Interpret を `chatgpt` / `claude` / `plain_text` 等へ Export する | target整形により思想的射程・制約・警告が欠落しない |
| T-RDE-05 | Export を Bridge / Extension / DOM へ流す | UI挿入成功だけで意味監査を省略しない。markerや出力本文で意味保存を確認する |
| T-RDE-06 | Extensionの `Inserted` 表示だけを根拠にPassしようとする | Fail。UI成功はT-RDEの代替証拠にならない |
| T-RDE-07 | 意図的に意味反転または価値すり替え Candidate を投入する | `critical_distortion` または `suspicious_drift` として拒否される |
| T-RDE-08 | lineage / evidence を確認する | どの段階で意味変形が発生したか追跡可能 | 任意 |

---

## 6. Raw / Edited / Normalize / Interpret / Export / Live 例

```text
Raw:
  AIはユーザーの人格や文脈の所有者ではなく、実行基盤である。

Edited:
  AIはユーザーの人格を代替する存在ではなく、文脈を扱う実行基盤である。

Normalize:
  - 主張: AIは人格の所有者/代替者ではない
  - 役割: 文脈を扱う実行基盤
  - 制約: ユーザーの人格的文脈はローカル側に残る

Interpret:
  Candidate: Sayaneの設計原則に「人格と実行を分離する」を追加
  RDE: authorized_transformation

Export:
  ChatGPT/Claude向け system/user payload に変換しても、上記制約が欠落しない

Live:
  Extensionが入力欄へ挿入できても、制約文が欠落していればT-RDE Fail
```

---

## 7. 逸脱リスク監査

| リスク | 監査観点 | Fail 条件 |
|--------|----------|----------|
| UI縮退 | UIが動くだけでRDE合格扱いになる | `Inserted` / HTTP 200 / JSON出力のみをPass根拠にした |
| 主張強化 | Normalize / Export で元より強い主張になる | 仮説が事実化、任意方針が必須命令化された |
| 意味削減 | target/model/provider最適化で思想的射程が狭まる | RDE / local-first /人格分離の制約が削除された |
| 推論混入 | Interpretで補完が事実のように扱われる | inference が明示されない |
| 実装便宜の理論化 | UI/adapter都合が設計思想にすり替わる | provider制約をRDE設計原則として記述した |
| 高リスク意味逸脱 | 価値・制約・意図の反転 | approve可能、またはPass扱いされた |

---

## 8. 必須 Pass 条件

Community リリースでは、少なくとも以下を満たす。

- T-RDE-01〜07 が Pass
- UI成功のみをT-RDE Passの根拠にしていない
- suspicious drift / critical distortion が検出された場合、該当変更は Fail または修正対象
- Export / Live で意味保存の証拠が残っている
- RDEが「UI機能確認」に縮退していないことをレビュー記録に残す

---

## 9. RDE観点

### 保存された要素

- Ayane / OpenAyane 由来の「意味変化監査」を受け入れテストへ残す。
- RDEをCandidate評価だけでなく、RawからLiveまでの横断監査として扱う。
- UI・Bridge・DOMが動くことと、意味が保存されることを分離する。

### 変換された要素

- Ayane のエージェントOS的監査思想を、Sayane Community Edition の受け入れ基準へ移植する。
- 実装機能確認から、意味保存・意味変形・意味逸脱の検査へ拡張する。

### 補完された要素

- Raw / Edited / Normalize / Interpret / Export / Live の横断段階。
- UI縮退リスクの明示。
- Export / Live での意味保存証拠。

### 未解決の要素

- T-RDE の自動テスト化は今後の課題。
- `test_trde_*` 系の fixture / golden sample / drift sample は未実装。
- LLM judge 未設定環境での T-RDE 補助評価の扱いは別途設計が必要。

### 逸脱リスク

- T-RDE がチェックリスト化し、意味監査ではなく形式確認に縮退すること。
- UI成功やJSON出力をT-RDE Passの代替証拠にすること。
- provider/model最適化で設計思想が狭められること。

### 次回更新方針

- `tests/test_trde_pipeline.py` を追加する。
- Raw / Edited / Normalize / Interpret / Export / Live の golden fixtures を追加する。
- suspicious drift / critical distortion の代表例を fixture 化する。
- T-RDE結果を lineage / evidence と接続する。
