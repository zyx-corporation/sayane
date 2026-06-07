# Sidepanel Review Display (F-3)

The sidepanel is the primary review surface for candidates in the Chrome Extension.
It must make scoped context boundaries visible to human reviewers.

## Design Principles

1. Sidepanel is a review surface, not a storage surface.
2. Scoped accept must be visually distinct from normal approval.
3. Conditions, negative constraints, and promotion risks must not be hidden.
4. Missing metadata is displayed as "未指定", never invented.

## Display Sections

### Candidate Card

| Field | Source | Display |
|---|---|---|
| status | `scoped_accept` | 「範囲付き許容」badge |
| scope | `accepted_scope` | project:zenn/article-02-intro |
| promotion risk | `promotion_policy.can_promote=False` | 「昇格注意」badge |

### Detail Panel

| Section | Japanese Label | Content |
|---|---|---|
| Scope | 有効範囲 | `accepted_scope.level` / `target` / `sub_scope` |
| Conditions | 条件 | `conditions[]` |
| Negative Constraints | 扱ってはいけない解釈 | `negative_constraints[]` |
| Promotion Policy | 昇格制約 | `can_promote` + `requires_review_for[]` |
| Reuse Policy | 再利用方針 | `review_on_reuse` |

### Filters

| Filter | Label | Default |
|---|---|---|
| all | すべて | |
| review_required | 要判断 | ✅ default |
| scoped_accept | 範囲付き許容 | |
| promotion_risk | 昇格注意 | |

## Boundary

- Sidepanel is the primary review surface. Popup is the entry point only.
- Scoped accept must not look like ordinary approval.
- Warnings must not be collapsed out of visibility.
- Missing scope fields must show "未指定", not invented values.
