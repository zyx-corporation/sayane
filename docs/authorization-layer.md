# Authorization Layer（候補更新・記憶書き込み）

## 位置づけ

Authorization Layer は、Candidate の評価結果と利用者許可を、Profile への不可逆 merge の前に検証する層である。

**完全実装ではない。** RDE vNext 全体の規則ではなく、次の逸脱を防ぐための**最小ガード**として導入する。

> この実装は RDE vNext の全規則を実装するものではない。ただし、RDE 出力の事実化、利用者許可の免罪符化、制度 scope の自己拡大、説明責任ログのプロファイリング転用、PoP-UID との不可逆的結合は、現時点でも禁止される逸脱として扱う。

## 原則（英語要約）

| 原則 | 説明 |
|------|------|
| RDE output is not objective fact | 評価は仮説；`confirmed` ≠ 事実 |
| Evaluation requires positional disclosure | `evaluator.position` 必須（欠落は provisional） |
| User authorization is necessary but not sufficient | Approve 前に `user_authorization_audit` が必要 |
| Self-evaluation is advisory only | `generator_id == evaluator_id` → advisory |
| Mirror is not veto | `disposition: mirror` は却下権ではない |
| Institutional scope must not self-expand | `in_scope: false` では記録しない |
| Accountability logs must not become profiling | 禁止 purpose_binding |
| PoP-UID linkage is explicitly deferred | 既定 `pop_uid_linkage_enabled: false` |

## フロー

```text
Capture → CandidateUpdate (generator_id)
       → evaluate_candidate()
            → heuristic (self_agent, advisory)
            → optional LLM (independent_rde)
            → disposition_status (provisional | confirmed)
       → approve_candidate()
            → user_authorization_audit (mirror)
            → user evaluator supplemental (final, merge jurisdiction)
            → assert_memory_write_allowed()
            → profile merge
```

## Feature flags

`AuthorizationFeatureFlags`（`core/authorization.py`）:

| フラグ | 既定 | 意味 |
|--------|------|------|
| `pop_uid_linkage_enabled` | `false` | PoP-UID 結合（保留） |
| `enforce_authorization_guards` | `true` | merge 前ガード |
| `legacy_approve_compat` | `true` | evaluator 欠落の旧 Candidate を許容 |

## 後方互換

- 既存 `CandidateEvaluation` に `evaluator` が無い場合 → `disposition_status: provisional`
- `legacy_approve_compat: true` 時は merge 可能（監査 trail は approve 時に付与）

## 参照

- [rde-audit-policy.md](./rde-audit-policy.md)
- [architecture.md](./architecture.md) §3.5 Evaluator
- [evaluation-lineage.md](./evaluation-lineage.md)
