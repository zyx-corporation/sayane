# Omomuki から Sayane への移行

2026-05 以降、プロジェクト名・リポジトリ名・CLI を **Sayane（紗綾音）** に統一した。Community Edition **0.6.0** 以降は新名称のみをサポートする。

## 対象者

- 以前 `omomuki` CLI と `~/.omomuki/` を使っていたユーザー
- リポジトリ `zyx-corporation/omomuki` を clone していた開発者

新規インストールは [インストール](install.md) のみでよい。

## 名称対応表

| 旧 (Omomuki) | 新 (Sayane) |
|--------------|-------------|
| CLI `omomuki` | `sayane` |
| 設定ディレクトリ `~/.omomuki/` | `~/.sayane/` |
| プロファイル `omomuki.profile.yaml` | `sayane.profile.yaml` |
| 環境変数 `OMOMUKI_*` | `SAYANE_*`（例: `SAYANE_LANG`, `SAYANE_OBSIDIAN_VAULT`） |
| Python パッケージ `omomuki` | `sayane` |
| リポジトリ `zyx-corporation/omomuki` | [zyx-corporation/sayane](https://github.com/zyx-corporation/sayane) |
| 商用版 `omomuki-pro` | Commercial Edition（別途ライセンス提供） |
| Profile kind `OmomukiProfile` | `SayaneProfile` |

## 1. CLI の再インストール

旧ラッパーを削除し、新インストーラで入れ直す。

### macOS / Linux

```bash
# 旧 CLI（存在する場合）
rm -f ~/.local/bin/omomuki
rm -rf ~/.local/share/omomuki

# 新規インストール
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash

sayane --version
```

### Windows (PowerShell)

```powershell
Remove-Item -Force "$env:LOCALAPPDATA\Omomuki\bin\omomuki.cmd" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Omomuki" -ErrorAction SilentlyContinue

irm https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.ps1 | iex

sayane --version
```

`SAYANE_SKIP_INIT=1` を付けると、既存プロファイルがある場合は `sayane init` をスキップできる（下記データ移行後に実行推奨）。

## 2. プロファイルストアの移行

`~/.omomuki/` にデータがある場合、ディレクトリごとコピーし、ファイル名を更新する。

```bash
# バックアップ（推奨）
cp -a ~/.omomuki ~/.omomuki.bak.$(date +%Y%m%d)

# 新ストアへコピー
mkdir -p ~/.sayane
cp -a ~/.omomuki/. ~/.sayane/

# プロファイルファイル名の変更（各 profile ディレクトリ）
find ~/.sayane/profiles -name 'omomuki.profile.yaml' | while read -r f; do
  mv "$f" "$(dirname "$f")/sayane.profile.yaml"
done

# kind フィールドの更新（YAML）
# macOS (BSD sed)
find ~/.sayane/profiles -name 'sayane.profile.yaml' -exec \
  sed -i '' 's/kind: OmomukiProfile/kind: SayaneProfile/g' {} +

# Linux (GNU sed) の場合は sed -i 's/.../g' を使用
```

`config.yaml` が `~/.omomuki/` にある場合も `~/.sayane/config.yaml` にコピーされる。storage backend 名は `filesystem` のまま利用可能。

### 動作確認

```bash
sayane profile inspect
sayane storage backend status
```

問題なければ、十分な期間後にバックアップを削除できる。

```bash
# 任意: 旧ディレクトリを残すか削除
# rm -rf ~/.omomuki
```

## 3. 環境変数

シェルプロファイルや CI で旧変数を使っている場合は置き換える。

| 旧 | 新 |
|----|-----|
| `OMOMUKI_LANG` | `SAYANE_LANG` |
| `OMOMUKI_OBSIDIAN_VAULT` | `SAYANE_OBSIDIAN_VAULT` |
| `OMOMUKI_REPO` / `OMOMUKI_REF`（install.sh） | `SAYANE_REPO` / `SAYANE_REF` |

## 4. 開発者向け（editable install）

```bash
git remote set-url origin git@github.com:zyx-corporation/sayane.git
cd sayane   # リポジトリ clone 先
pip install -e ".[dev]"
pytest
```

Import は `from sayane.core.models import SayaneProfile` などに変更済み。

## 5. Chrome Extension

Extension を再ビルド・再読み込みする。Bridge の URL は従来どおり `http://127.0.0.1:38741`（変更なし）。

## 6. PyPI

現時点では **PyPI 公開パッケージ名 `sayane` は未提供**。インストールは [install.sh](../scripts/install.sh) / [install.ps1](../scripts/install.ps1) または `pip install git+https://github.com/zyx-corporation/sayane.git@v0.6.0` を利用する。

## 関連

- [CHANGELOG](../CHANGELOG.md) — 0.6.0 リネーム内容
- [はじめに](getting-started.md)
- [roadmap.md §9（Phase 6 概要）](roadmap.md)
