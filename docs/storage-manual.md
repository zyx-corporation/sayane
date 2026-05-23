# Storage / Obsidian / Git マニュアル

Phase 5 で提供される、Profile Store のファイルシステム運用・Obsidian vault 連携・Git 履歴化の利用者向けマニュアルである。

## 1. 概要

| コマンド | 概要 |
|---------|------|
| `omomuki storage import <vault>` | Obsidian vault の `.md` を `context/` へ取り込む |
| `omomuki storage export <vault>` | `context/` を vault 内 `omomuki/` へ書き出す |
| `omomuki storage index` | `context/` を走査し `context_index.entries` を再生成する |
| `omomuki storage commit -m "..."` | Profile と context を Git コミットする |

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

- `.obsidian`、`.git`、`node_modules` 配下はスキップする
- 取り込み時に markdown を正規化（改行・BOM・行末空白）
- 取り込み後に `context_index` を自動更新する

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

## 6. Git 連携

プロファイルディレクトリで初回:

```bash
cd ~/.omomuki/profiles/default
omomuki storage commit -m "omomuki: initial context" --init
```

以降:

```bash
omomuki storage commit -m "omomuki: add handoff notes"
```

`omomuki.profile.yaml` と `context/` のみステージする。

## 7. 制限（Phase 5 MVP）

- vault ルートへの直接 export はしない（`--subdir` 必須の安全側）
- 双方向同期・競合解決は未実装
- 暗号化ストア・SQLite は Phase 6 以降

関連: [はじめに](getting-started.md)、[実装ロードマップ](roadmap.md)
