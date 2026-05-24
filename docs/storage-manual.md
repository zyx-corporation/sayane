# Storage / Obsidian / Git マニュアル

Phase 5 で提供される、Profile Store のファイルシステム運用・Obsidian vault 連携・Git 履歴化の利用者向けマニュアルである。

**SQLite 実装までは Git 連携が既定動作**である。Profile Store を変更する操作（`init`、`storage import` / `index`、`candidate approve` など）のあと、プロファイルディレクトリで Git リポジトリを自動初期化し、変更があればコミットする。手動の `storage commit` も利用できる。

## 1. 概要

| コマンド | 概要 |
|---------|------|
| `sayane storage import [<vault>]` | Obsidian vault の `.md` を `context/` へ取り込む |
| `sayane storage export [<vault>]` | `context/` を vault 内 `sayane/` へ書き出す |
| `sayane storage index` | `context/` を走査し `context_index.entries` を再生成する |
| `sayane storage commit -m "..."` | Profile と context を Git コミットする |

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
- Git 履歴に残すには `sayane storage commit -m "..."` を実行する（`storage index` を実行しても `context/` の変更は自動コミットされる）

**`context/` に新しい `.md` を追加した場合**

```bash
sayane storage index          # context_index.entries を再生成
sayane compile --target chatgpt
```

`storage index` 実行後、変更があれば **Git へ自動コミット**される（0.5.9 以降）。

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
sayane storage import /path/to/your-vault
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
- 取り込み後に **Git へ自動コミット**（リポジトリ未作成なら `git init`）

ドライラン:

```bash
sayane storage import /path/to/vault --dry-run
```

## 5. Obsidian への書き出し

```bash
sayane storage export /path/to/your-vault
```

既定では vault 直下の **`sayane/`** サブディレクトリへ出力する（vault ルートの既存ノートを上書きしない）。

別名:

```bash
sayane storage export /path/to/vault --subdir export
```

## 6. context_index の再生成

`context/` にファイルを手動追加したあと:

```bash
sayane storage index
```

`context_index` 更新後、変更があれば **Git へ自動コミット**される。

## 7. Git 連携

### 7.1 既定動作（SQLite 実装まで）

| 操作 | Git 動作 |
|------|---------|
| `sayane init` | リポジトリ初期化 + 初回コミット |
| `storage import` / `index` | 変更があれば自動コミット |
| `candidate approve` | Profile 更新後に自動コミット |
| `storage commit -m "..."` | 任意メッセージで手動コミット |

プロファイルディレクトリ（例: `~/.sayane/profiles/default/`）が Git リポジトリでない場合、初回の自動コミット時に `git init` する。コミット対象は `sayane.profile.yaml` と `context/` のみ。

### 7.2 手動コミット

任意メッセージでコミットしたい場合:

```bash
sayane storage commit -m "sayane: add handoff notes"
```

初回のみ `--init` を付けることもできる（自動初期化後は通常不要）:

```bash
sayane storage commit -m "sayane: initial context" --init
```

## 8. 制限（Phase 5 MVP）

- vault ルートへの直接 export はしない（`--subdir` 必須の安全側）
- 双方向同期・競合解決は未実装
- 暗号化 SQLite ストア・移行 CLI は **[商用版（sayane-pro）](https://github.com/zyx-corporation/sayane-pro/blob/main/docs/commercial-edition.md)**（Phase 6）。Community 版は FileSystem + Git を継続
- 商用版でも `storage backend filesystem` により本マニュアルの操作をそのまま利用可能

関連: [はじめに](getting-started.md)、[実装ロードマップ](roadmap.md)
