# RDE 監査ポリシー（逸脱防止基準）

この文書は **RDE vNext の全規則を実装するものではない**。ただし、次の逸脱は現時点でも禁止される。

- RDE 出力の**事実化**
- 利用者許可の**免罪符化**
- 制度 **scope の自己拡大**
- 説明責任ログの**プロファイリング転用**
- PoP-UID と authorization / accountability log の**不可逆的結合**

## 1. RDE 出力は客観的事実ではない

RDE（Resonant Deviation Evaluator）は意味変化 ΔM の**監査構造**であり、無謬の判定者ではない。

- 評価結果は「特定の評価主体・立場・権限・管轄からの**仮説**」として記録する。
- `disposition_status: confirmed` は「事実が確定した」ことを意味しない。
- 現行規則系において**確認済みの仮説**であることを示すに留める。
- evaluator 情報が欠落する既存レコードは `provisional` として扱う。

## 2. 評価スキーマ（CandidateEvaluation 拡張）

```yaml
evaluation:
  evaluator:
    type: self_agent | independent_rde | user | policy | council
    identity: string
    position:
      stake: self_interest | neutral | third_party_advocate
      authority: advisory | primary | final | veto
      jurisdiction: string[]
    conflict_of_interest: none | low | high
  separation:
    generator_id: string
    evaluator_id: string
    is_separated: boolean
  policy_provenance:
    legislator: string
    revisable: boolean
    last_revised: string | null
  disposition_status: provisional | confirmed
```

実装: `sayane.core.authorization`, `sayane.core.candidate.CandidateEvaluation`。

## 3. R1 — 生成と評価の分離

`generator_id == evaluator_id` の場合、authority は **advisory** に降格する。

- self-agent は自分の生成物について**最終承認できない**。
- advisory のみでは memory write（profile merge）・confirmed authorization・不可逆操作に進めない。

## 4. R4/R5 — 立場の必記録

- `evaluator.position` 欠落 → `provisional`
- 単一評価で `stake: self_interest` または `conflict_of_interest: high` → `provisional`
- `confirmed` には neutral な `independent_rde` / `user` / `policy` / `council` 等の再評価が必要

## 5. R6 — 利用者許可の監査（mirror は veto ではない）

`user_authorization_audit` は利用者の「保存してよい」意思を記録する。

- `disposition: mirror` 固定（警告・自己確認の映し出し）
- AGI / system が人間を**後見拒否**する機能ではない
- 許可は**必要条件**であり**十分条件ではない**

## 6. R7 — accountability log の scope

制度は自ら scope を拡大しない。

- `in_scope: false` → 制度は記録・介入しない（`human_mediation` へ委譲）
- `purpose_binding` に `judgment` / `profiling` / `prediction` / `scoring` 等を含めない
- 開示は `need_to_know` + `procedure_required`

## 7. PoP-UID 接続の保留

PoP-UID / DID / VC と authorization history / accountability log の**直接結合は既定で無効**。

- `AuthorizationFeatureFlags.pop_uid_linkage_enabled` 既定値: `false`
- 将来も `proof_of_existence` / `selective_disclosure` の設計同型の示唆に留める

## 8. 関連コード

| モジュール | 役割 |
|-----------|------|
| `core/authorization.py` | 型定義 |
| `evaluators/authorization_guards.py` | R1/R4–R7 ガード |
| `evaluators/service.py` | evaluate / approve への適用 |
| `core/pop_uid.py` | PoP-UID 結合拒否 |

## 9. テスト

`tests/test_authorization_layer.py` が上記ガードを検証する。
