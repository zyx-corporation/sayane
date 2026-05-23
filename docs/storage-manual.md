# Storage / Obsidian / Git マニュアル

Phase 5 で提供される、Profile Store のファイルシステム運用・Obsidian vault 連携・Git 履歴化の利用者向けマニュアルである。

**SQLite 実装までは Git 連携が既定動作**である。Profile Store を変更する操作（`init`、`storage import` / `index`、`candidate approve` など）のあと、プロファイルディレクトリで Git リポジトリを自動初期化し、変更があればコミットする。手動の `storage commit` も利用できる。

## 1. 概要

| コマンド | 概要 |
|---------|------|
| `omomuki storage import [<vault>]` | Obsidian vault の `.md` を `context/` へ取り込む |
| `omomuki storage export [<vault>]` | `context/` を vault 内 `omomuki/` へ書き出す |
| `omomuki storage index` | `context/` を走査し `context_index.entries` を再生成する |
| `omomuki storage commit -m "..."` | Profile と context を Git コミットする |

`<vault>` は省略可。環境変数 **`OMOMUKI_OBSIDIAN_VAULT`** に存在するディレクトリを設定している場合、そのパスが既定 vault になる。

`compile` / `export` / Bridge の `compile` は、プロファイルディレクトリ内に文脈ファイルがあれば **本文を Prompt IR の context に含める**（Phase 5 以降）。

## 2. Profile Store レイアウト

```text
~/.omomuki/profiles/default/
  omomuki.profile.yaml
  context/
    MyContext.md
    AI_HANDOFF.md
    …
```

`context_index` は entrypoint / handoff に加え、任意で `entries`（`context/` 配下の相対パス一覧）を持つ。

## 3. Obsidian 取り込み

```bash
omomuki init
omomuki storage import /path/to/your-vault
```

環境変数 **`OMOMUKI_OBSIDIAN_VAULT`** に vault のパスを設定し、そのディレクトリが存在する場合、`<vault>` 引数を省略できる。

```bash
export OMOMUKI_OBSIDIAN_VAULT="$HOME/Documents/MyVault"
omomuki storage import
omomuki storage export   # 同じ vault を既定に使用
```

- `.obsidian`、`.git`、`node_modules` 配下はスキップする
- 取り込み時に markdown を正規化（改行・BOM・行末空白）
- 取り込み後に `context_index` を自動更新する
- 取り込み後に **Git へ自動コミット**（リポジトリ未作成なら `git init`）

ドライラン:

```bash
omomuki storage import /path/to/vault --dry-run
```

## 4. Obsidian への書き出し

```bash
omomuki storage export /path/to/your-vault
```

既定では vault 直下の **`omomuki/`** サブディレクトリへ出力する（vault ルートの既存ノートを上書きしない）。

別名:

```bash
omomuki storage export /path/to/vault --subdir export
```

## 5. context_index の再生成

`context/` にファイルを手動追加したあと:

```bash
omomuki storage index
```

`context_index` 更新後、変更があれば **Git へ自動コミット**される。

## 6. Git 連携

### 6.1 既定動作（SQLite 実装まで）

| 操作 | Git 動作 |
|------|---------|
| `omomuki init` | リポジトリ初期化 + 初回コミット |
| `storage import` / `index` | 変更があれば自動コミット |
| `candidate approve` | Profile 更新後に自動コミット |
| `storage commit -m "..."` | 任意メッセージで手動コミット |

プロファイルディレクトリ（例: `~/.omomuki/profiles/default/`）が Git リポジトリでない場合、初回の自動コミット時に `git init` する。コミット対象は `omomuki.profile.yaml` と `context/` のみ。

### 6.2 手動コミット

任意メッセージでコミットしたい場合:

```bash
omomuki storage commit -m "omomuki: add handoff notes"
```

初回のみ `--init` を付けることもできる（自動初期化後は通常不要）:

```bash
omomuki storage commit -m "omomuki: initial context" --init
```

## 7. 制限（Phase 5 MVP）

- vault ルートへの直接 export はしない（`--subdir` 必須の安全側）
- 双方向同期・競合解決は未実装
- 暗号化ストア・SQLite は Phase 6 以降（SQLite 導入後は Git 自動コミット方針を見直す）

関連: [はじめに](getting-started.md)、[実装ロードマップ](roadmap.md)
