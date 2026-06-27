# Storage / Obsidian / Git マニュアル

Phase 5 で提供される、Profile Store のファイルシステム運用・Obsidian vault 連携・Git 履歴化の利用者向けマニュアルである。

> 現行方針: Storage の主経路は **local Markdown / filesystem-first** である。Obsidian / Git 連携は既存ワークフローとの互換導線として残るが、新規セットアップの primary path ではない。mutating な外部連携は `--legacy-compatible` が必要である。

既存実装では Git 連携や Obsidian 補助コマンドも利用できる。必要に応じて既存運用との互換のため使えるが、ロードマップ上は将来の Local Vault 境界を優先している。

## 1. 概要

| コマンド | 概要 |
|---------|------|
| `sayane storage import [<vault>] --legacy-compatible` | Obsidian vault の `.md` を `context/` へ取り込む |
| `sayane storage export [<vault>] --legacy-compatible` | `context/` を vault 内 `sayane/` へ書き出す |
| `sayane storage export-package -o <dir>` | vault-aware external package を書き出す |
| `sayane storage import-package <dir>` | vault-aware external package を preview import する |
| `sayane storage queue-package <dir>` | vault-aware external package を pending review queue へ投入する |
| `sayane storage index` | `context/` を走査し `context_index.entries` を再生成する |
| `sayane storage commit -m "..." --legacy-compatible` | Profile と context を Git コミットする |

`<vault>` は省略可。環境変数 **`SAYANE_OBSIDIAN_VAULT`** に存在するディレクトリを設定している場合、そのパスが既定 vault になる。

`compile` / `export` / Bridge の `compile` は、プロファイルディレクトリ内に文脈ファイルがあれば **本文を Prompt IR の context に含める**（Phase 5 以降）。

## 2. Profile Store レイアウト

```text
~/.sayane/profiles/default/
  sayane.profile.yaml
  context/
    MyContext.md
    AI_HANDOFF.md
    …
```

`context_index` は entrypoint / handoff に加え、任意で `entries`（`context/` 配下の相対パス一覧）を持つ。

## 3. ファイル形式と直接編集

SQLite 実装までは、storage の本体は **ローカル上のプレーンファイル** である。エディタや Obsidian から直接編集してよい。

### 3.1 書式

| 種類 | パス | 形式 | 内容 |
|------|------|------|------|
| **Profile** | `sayane.profile.yaml` | **YAML**（UTF-8） | `identity`, `voice`, `values`, `context_index` など構造化メタデータ |
| **文脈** | `context/*.md` | **Markdown**（UTF-8） | 自由記述のノート（Obsidian と同じ `.md` でよい） |

**Profile YAML**

- `kind: SayaneProfile` が必須
- [Sayane Profile と Prompt IR](profile-ir.md) および `schemas/sayane-profile.schema.json` に従う
- スキーマ不整合の YAML は `profile inspect` / `compile` 時にエラーになる

**文脈 Markdown**

- 決まった front matter や専用 DSL は **ない**（通常の Markdown テキスト）
- `storage import` / `export` 時のみ次を正規化する: BOM 除去、改行を LF、行末空白のトリム
- エディタで直接保存したファイルは、そのままの内容が使われる（正規化は import/export 経由時のみ）

Obsidian から `storage import` した内容も、最終的には `context/` 配下の Markdown として保持される。

### 3.2 編集後の手順

**`context/` の既存 `.md` の中身だけを変えた場合**

- `context_index` に載っているファイルであれば、追加コマンドなしで `sayane compile` の Prompt IR に反映される
- Git 履歴に残すには `sayane storage commit -m "..." --legacy-compatible` を実行する

**`context/` に新しい `.md` を追加した場合**

```bash
sayane storage index          # context_index.entries を再生成
sayane compile --target chatgpt
```

`storage index` は Git repository 作成や自動コミットを暗黙実行しない。

**`sayane.profile.yaml` を直接編集した場合**

```bash
sayane profile inspect        # 読み込み・要約の確認
sayane storage commit -m "sayane: edit profile"   # 任意: Git に記録
```

YAML の直接編集は **自動 Git コミットの対象外**である。履歴に残す場合は `storage commit` を明示的に実行する。

**Candidate（`~/.sayane/candidates/`）**

- storage とは別ディレクトリ。Profile へ反映するには [評価マニュアル](evaluation-manual.md) の evaluate → approve フローを使う

### 3.3 おすすめの編集フロー

| 編集したい内容 | 手段 |
|---------------|------|
| 長文メモ・文脈ノート | `context/*.md` をエディタ / Obsidian で編集（または `storage import`） |
| 人格・方針の構造化フィールド | `sayane.profile.yaml`、または Candidate → approve |
| 新規 Markdown の取り込み | ファイル追加後に `storage index` |
| 動作確認 | `profile inspect` / `compile` |

### 3.4 制限

- `compile` が読む本文は **プロファイルディレクトリ内**のファイルに限定される
- `context_index` に載っていないファイルは `compile` では読まれない
- 1 ファイルあたり最大 **約 32KB**（超過分は切り詰めて `…(truncated)` を付与）
- Obsidian vault との **リアルタイム双方向同期は未実装**（`import` / `export` は CLI 経由）

## 4. Obsidian 取り込み

```bash
sayane init
sayane storage import /path/to/your-vault --legacy-compatible
sayane storage import /path/to/your-vault --legacy-compatible --source-subdir sayane
```

環境変数 **`SAYANE_OBSIDIAN_VAULT`** に vault のパスを設定し、そのディレクトリが存在する場合、`<vault>` 引数を省略できる。

```bash
export SAYANE_OBSIDIAN_VAULT="$HOME/Documents/MyVault"
sayane storage import
sayane storage export   # 同じ vault を既定に使用
```

- `.obsidian`、`.git`、`node_modules` 配下はスキップする
- 取り込み時に markdown を正規化（改行・BOM・行末空白）
- 取り込み後に `context_index` を自動更新する
- 取り込み後に Git は自動コミットされない
- `--source-subdir` を付けると、その safe subdirectory だけを取り込む
- `--source-subdir` には `.obsidian`, `.git`, `node_modules`, `.hidden`, `..` などは禁止

ドライラン:

```bash
sayane storage import /path/to/vault --dry-run
```

## 5. Obsidian への書き出し

```bash
sayane storage export /path/to/your-vault --legacy-compatible
```

既定では vault 直下の **`sayane/`** サブディレクトリへ出力する（vault ルートの既存ノートを上書きしない）。

許可される export target の考え方:

- vault root 配下の **明示 subdir**
- hidden / reserved dir ではない path
- `.` / `..` を含まない relative path

禁止される例:

- vault root そのもの
- `.obsidian`
- `.git`
- `node_modules`
- `.hidden`
- `../escape`

書き出し先には次も同梱される:

- `sayane-export-metadata.json` — 非正本・derived・review-required を示す機械可読 metadata
- `SAYANE_EXPORT_NOTICE.txt` — operator 向けの短い boundary notice

metadata には少なくとも次が入る:

- local path redaction (`<redacted:path>`)
- `recommended_max_age: 30d`
- `delete_after_import_or_review: true`
- raw capture / review history / lineage history を含めないという redaction posture

別名:

```bash
sayane storage export /path/to/vault --subdir export
```

## 6. vault-aware external package

legacy Obsidian / Git compatibility path とは別に、P3 では reviewable external
exchange format として **vault-aware external package** を導入した。

```bash
sayane storage export-package --output ./sayane-external-package
sayane storage import-package ./sayane-external-package
sayane storage queue-package ./sayane-external-package
```

この package は少なくとも次を持つ:

- `manifest.json`
- `artifacts/bundle.yml`
- （任意）`artifacts/audit-export.json`

boundary:

- canonical profile state ではない
- review before merge が必要
- preview / verify は acceptance を意味しない
- legacy compatibility path ではない
- `import-package` は preview-only 契約であり、profile を変更しない

retention class:

- `reviewable_context_bundle` — 推奨 `30d`
- `redacted_audit_export` — 推奨 `14d`
- retention expiry は現行 contract では `warning_only`

supported operator actions:

- `offline_review`
- `candidate_generation_preview`
- `manual_redacted_handoff`

forbidden workflows:

- `canonical_working_store`
- `automatic_external_sync_promotion`
- `automatic_bidirectional_sync`
- `implicit_filesystem_git_auto_commit_as_primary_sync`
- `direct_profile_merge_without_review`
- `long_lived_unreviewed_archive`

`bundle.yml` には provenance metadata と content hash が付く。
`import-package` はこの slice では **preview-only** であり、profile は変更せず、
reviewable candidate を表示するだけで永続化しない。
将来もし mutating な package intake を導入する場合も、それは別の explicit workflow とし、
`import-package` 自体の意味は変えない。
pending candidate を review queue に入れる明示コマンドは `queue-package` である。
これは Candidate を永続化するが、Profile 自体は変更しない。
preview では package age が推奨 review window を超えると warning を表示する。

恒久 legacy compatibility workflow:

- `sayane storage import --legacy-compatible`
- `sayane storage export --legacy-compatible`
- `sayane storage commit --legacy-compatible`

## 7. context_index の再生成

`context/` にファイルを手動追加したあと:

```bash
sayane storage index
```

`context_index` 更新後も Git は自動コミットされない。

## 8. Git 連携（互換運用）

### 8.1 既存実装の動作

| 操作 | Git 動作 |
|------|---------|
| `sayane init` | Git 変更なし |
| `storage import` / `index` | 自動コミットしない |
| `candidate approve` | Git 自動コミットしない |
| `storage commit -m "..." --legacy-compatible` | 任意メッセージで手動コミット |

プロファイルディレクトリ（例: `~/.sayane/profiles/default/`）が Git リポジトリでない場合、`storage commit --init --legacy-compatible` により初回だけ `git init` できる。コミット対象は `sayane.profile.yaml` と `context/` のみ。

### 8.2 手動コミット

任意メッセージでコミットしたい場合:

```bash
sayane storage commit -m "sayane: add handoff notes" --legacy-compatible
```

初回のみ `--init` を付けることもできる（自動初期化後は通常不要）:

```bash
sayane storage commit -m "sayane: initial context" --init --legacy-compatible
```

## 9. 制限（Phase 5 MVP）

- vault ルートへの直接 export はしない（`--subdir` 必須の安全側）
- hidden / reserved / escaping subdir への export は拒否される
- 双方向同期・競合解決は未実装
- 暗号化 SQLite ストア・移行 CLI・ライセンスは **Commercial Edition**（Phase 6、sayane-pro 側マニュアル）
- Local Vault / 保存時暗号化方針が固まるまで、Obsidian / Git 連携は互換導線として扱う
- export 先の metadata / notice は「この書き出し物は canonical profile state ではない」ことを明示する
- export metadata では local source path をそのまま書かず redaction する

関連: [はじめに](getting-started.md)、[実装ロードマップ](roadmap.md)
