# Dogfood 手順書（エンドツーエンド）

Sayane **0.5.8** 時点で、ローカル環境で一通り動作確認する手順である。  
前提: `pip install -e ".[dev]"` 済み。

## 1. 初期化と文脈の準備

```bash
export SAYANE_LANG=ja   # 任意: CLI メッセージを日本語に

sayane init
sayane profile inspect

# Obsidian vault がある場合
export SAYANE_OBSIDIAN_VAULT="$HOME/Documents/MyVault"   # 任意
sayane storage import          # または sayane storage import /path/to/vault
sayane storage index

sayane compile --target chatgpt
```

## 2. Local Bridge の起動

**ターミナル A**（常駐）:

```bash
sayane serve
# ~/.sayane/bridge.token を Extension Options にコピー
```

## 3. Capture → 評価 → merge（HTTP）

**ターミナル B**:

```bash
TOKEN=$(cat ~/.sayane/bridge.token)
AUTH="Authorization: Bearer $TOKEN"

# 意味のある文面で capture（プレースホルダーは避ける）
CAP=$(curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"content":"Explicit uncertainty and local-first context portability for cross-LLM work.","source":"dogfood"}' \
  http://127.0.0.1:38741/capture)
CID=$(echo "$CAP" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "CID=$CID"

# Level 1 評価
curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"level":1}' "http://127.0.0.1:38741/candidates/$CID/evaluate" | jq .evaluation.rde_class

# diff（add が空なら既に Profile に同名概念がある）
curl -s -H "$AUTH" "http://127.0.0.1:38741/candidates/$CID/diff" | jq .

# 問題なければ approve
curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"force_critical":false}' "http://127.0.0.1:38741/candidates/$CID/approve" | jq .status
```

## 4. Level 2（Ollama / 任意）

```bash
ollama list
export SAYANE_JUDGE_MODEL=llama3.2:1b   # 環境のモデル名に合わせる

sayane candidate evaluate "$CID" --level 2
sayane candidate show "$CID"
```

`llm_review` が入れば成功。`Suspicious Drift` / `Unresolved Gap` のときは diff を確認してから approve。

## 5. CLI でも同じフロー

```bash
sayane candidate list
sayane candidate evaluate "$CID" --level 1
sayane candidate diff "$CID"
sayane candidate approve "$CID"
sayane candidate lineage --profile-id default
```

## 6. Git と再 compile

```bash
sayane storage commit -m "dogfood: context sync" --init   # 初回のみ --init
sayane compile --target claude
```

## 7. チェックリスト

| # | 項目 | OK |
|---|------|-----|
| 1 | `sayane init` / `profile inspect` | ☐ |
| 2 | `storage import` + `index`（任意） | ☐ |
| 3 | `compile` に context 本文が含まれる | ☐ |
| 4 | Bridge `capture` → `evaluate` → `approve` | ☐ |
| 5 | `candidate lineage` に記録 | ☐ |
| 6 | Level 2 judge（任意） | ☐ |
| 7 | Extension capture / insert（[受け入れテスト](extension-acceptance-test.md) §5, §7） | ☐ |
| 8 | Extension evaluate / approve（[受け入れテスト](extension-acceptance-test.md) §6） | ☐ |

## 8. よくある状態

| 症状 | 意味 |
|------|------|
| `diff.add` が空 / `already_present` | 同じ文言が既に `knowledge.concepts` にある |
| `llm_review: null` + UIB validation | 旧版。0.5.3+ で UIB 欠損軸を補完 |
| Ollama 404 | `SAYANE_JUDGE_MODEL` を `ollama list` の名前に合わせる |

## 9. Iteration 2 以降（配置設計）

Tone 汚染・部分注入・PII 露出などを観察した場合は、[コンテキスト層設計](context-layering-design.md) のマッピングルールとクリーンアップ手順に従う。

```bash
sayane profile validate          # tone / concepts 配置の警告
sayane compile --target claude   # compile 時にも警告を stderr へ
```

構造化ペルソナを Capture した場合、Bridge は `warnings` を返す（Extension popup に表示）。

## 10. Iteration 3（context/ 長文移行）

1. `context/theory.md`, `projects.md`, `interaction.md`, `identity.md`, `notes/unverified.md` を作成（[レイアウト](context-layering-design.md#4-推奨ディレクトリレイアウト)）
2. `sayane storage index` — `context/private/` は自動除外
3. `sayane profile validate` → `Profile layout: OK`
4. Extension **文脈を挿入** — [user] に theory / projects / unverified 本文が含まれること
5. [system] の `Tone:` にペルソナ見出し・email が **無い** こと

| # | 項目 | OK |
|---|------|-----|
| I3-1 | context 長文ファイル作成 | ☐ |
| I3-2 | `profile validate` OK | ☐ |
| I3-3 | Insert に theory/projects 本文 | ☐ |
| I3-4 | PII が Insert に無い（private 未 index） | ☐ |

観察メモは `~/.sayane/profiles/default/context/notes/context.md` へ追記可。

関連: [はじめに](getting-started.md) / [評価マニュアル](evaluation-manual.md) / [Bridge マニュアル](bridge-manual.md) / [コンテキスト層設計](context-layering-design.md) / [#102](https://github.com/zyx-corporation/sayane/issues/102)
