# インストール

Sayane CLI のプラットフォーム別インストーラー。Extension ビルドは別途 [Extension マニュアル](extension-manual.md) を参照。

| OS | 方式 | スクリプト / パッケージ |
|----|------|------------------------|
| **macOS** | curl + bash | `scripts/install.sh` |
| **Linux** | curl + bash | `scripts/install.sh` |
| **Windows（Community）** | PowerShell (`irm` + `iex`) | `scripts/install.ps1` |

## 前提

- **Python 3.11+**
- **git**（GitHub から pip インストールする場合）
- ネットワーク（初回 install 時）

インストール先（既定）:

| OS | パス |
|----|------|
| macOS / Linux | `~/.local/share/sayane/venv` |
| Windows | `%LOCALAPPDATA%\Sayane\venv` |

CLI ラッパー:

| OS | パス |
|----|------|
| macOS / Linux | `~/.local/bin/sayane` |
| Windows | `%LOCALAPPDATA%\Sayane\bin\sayane.cmd`（ユーザー PATH に追加） |

---

## macOS

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
```

特定バージョン（タグ）:

```bash
SAYANE_REF=v1.0.0 curl -fsSL .../install.sh | bash
```

`~/.local/bin` が PATH に無い場合、シェルプロファイルに追加:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### 開発者（リポジトリ clone 済み）

```bash
SAYANE_SOURCE_DIR=/path/to/sayane SAYANE_DEV=1 bash scripts/install.sh
```

---

## Linux

macOS と同じ one-liner:

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
```

**Debian / Ubuntu** で venv が無い場合:

```bash
sudo apt install python3-venv git
```

**Fedora**:

```bash
sudo dnf install python3.11 git
```

---

## Windows

### 推奨: PowerShell ワンライナー

PowerShell（**管理者不要**）:

```powershell
irm https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.ps1 | iex
```

実行ポリシーで拒否される場合:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
# または
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

インストーラーは **ユーザー PATH** に `%LOCALAPPDATA%\Sayane\bin` を追加する。新しいターミナルで:

```powershell
sayane --version
sayane init
```

### Windows で curl+bash を使わない理由

- 既定シェルが cmd / PowerShell で、`bash` が無い環境が多い
- Python / PATH の扱いが PowerShell の方が安定
- **Chrome Extension + Bridge** は **Windows ネイティブ Python** 上の Bridge を推奨（WSL 内 Bridge は localhost 連携が届かない場合がある）

Community Edition（本リポジトリ OSS）は **PowerShell スクリプト** を第一選択とする。Commercial Edition の Windows MSI インストールは sayane-pro 側マニュアルを参照。

### 将来の配布案（Community / 未実装）

| 方式 | 用途 |
|------|------|
| **WinGet** マニフェスト | 企業・再現性重視 |
| **Scoop** bucket | 開発者向け |

---

## 環境変数（共通）

| 変数 | 説明 |
|------|------|
| `SAYANE_REPO` | GitHub リポジトリ（既定 `zyx-corporation/sayane`） |
| `SAYANE_REF` | ブランチ / タグ / SHA（既定 `main`） |
| `SAYANE_INSTALL_DIR` | インストールルート |
| `SAYANE_BIN_DIR` | ラッパー配置（Unix のみ。既定 `~/.local/bin`） |
| `SAYANE_SOURCE_DIR` | ローカル checkout から editable install |
| `SAYANE_DEV` | `1` で `[dev]` 依存を含める |
| `SAYANE_SKIP_INIT` | `1` で `sayane init` をスキップ |
| `SAYANE_YES` | `1` で確認プロンプトをスキップ |

---

## インストール後

```bash
sayane --version
sayane help
sayane init                    # スキップした場合
sayane serve                   # Bridge（Extension 用）
```

→ [はじめに](getting-started.md) / [CLI マニュアル](cli-manual.md)

---

## PyPI

**PyPI パッケージ `sayane` は未公開**（2026-05 時点）。インストールは本書のスクリプト、または:

```bash
pip install "sayane @ git+https://github.com/zyx-corporation/sayane.git@v1.0.0"
```

公開時は [CHANGELOG](../CHANGELOG.md) を参照。

---

## Bridge 常駐化（任意）

Bridge をログイン時に自動起動する方法（LaunchAgent / systemd user / タスク スケジューラ）は Phase 6 で `sayane serve --install-daemon` として提供予定。現状は手動で `sayane serve` を実行する。

---

## アンインストール

```bash
# macOS / Linux
rm -rf ~/.local/share/sayane ~/.local/bin/sayane
# Profile データを残す場合は ~/.sayane は削除しない
```

```powershell
# Windows
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Sayane"
# PATH から ...\Sayane\bin を手動削除（設定 → 環境変数）
```

---

## セキュリティ

`curl | bash` および `irm | iex` は、実行前にスクリプト内容を確認すること:

```bash
curl -fsSL .../install.sh -o install.sh
less install.sh
bash install.sh
```

関連: [Security Design](security.md)（Bridge は `127.0.0.1` のみ）
