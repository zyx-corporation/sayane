# インストール

Omomuki CLI のプラットフォーム別インストーラー。Extension ビルドは別途 [Extension マニュアル](extension-manual.md) を参照。

| OS | 方式 | スクリプト / パッケージ |
|----|------|------------------------|
| **macOS** | curl + bash | `scripts/install.sh` |
| **Linux** | curl + bash | `scripts/install.sh` |
| **Windows（Community）** | PowerShell (`irm` + `iex`) | `scripts/install.ps1` |
| **Windows（Commercial）** | **署名付き MSI** | [omomuki-pro](https://github.com/zyx-corporation/omomuki-pro) |

## 前提

- **Python 3.11+**
- **git**（GitHub から pip インストールする場合）
- ネットワーク（初回 install 時）

インストール先（既定）:

| OS | パス |
|----|------|
| macOS / Linux | `~/.local/share/omomuki/venv` |
| Windows | `%LOCALAPPDATA%\Omomuki\venv` |

CLI ラッパー:

| OS | パス |
|----|------|
| macOS / Linux | `~/.local/bin/omomuki` |
| Windows | `%LOCALAPPDATA%\Omomuki\bin\omomuki.cmd`（ユーザー PATH に追加） |

---

## macOS

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/omomuki/main/scripts/install.sh | bash
```

特定バージョン（タグ）:

```bash
OMOMUKI_REF=v0.5.9 curl -fsSL .../install.sh | bash
```

`~/.local/bin` が PATH に無い場合、シェルプロファイルに追加:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### 開発者（リポジトリ clone 済み）

```bash
OMOMUKI_SOURCE_DIR=/path/to/omomuki OMOMUKI_DEV=1 bash scripts/install.sh
```

---

## Linux

macOS と同じ one-liner:

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/omomuki/main/scripts/install.sh | bash
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
irm https://raw.githubusercontent.com/zyx-corporation/omomuki/main/scripts/install.ps1 | iex
```

実行ポリシーで拒否される場合:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
# または
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

インストーラーは **ユーザー PATH** に `%LOCALAPPDATA%\Omomuki\bin` を追加する。新しいターミナルで:

```powershell
omomuki --version
omomuki init
```

### Windows で curl+bash を使わない理由

- 既定シェルが cmd / PowerShell で、`bash` が無い環境が多い
- Python / PATH の扱いが PowerShell の方が安定
- **Chrome Extension + Bridge** は **Windows ネイティブ Python** 上の Bridge を推奨（WSL 内 Bridge は localhost 連携が届かない場合がある）

### Commercial Edition: MSI インストーラ

**Commercial Edition**（[omomuki-pro](https://github.com/zyx-corporation/omomuki-pro)）の Windows 向け第一配布方式は **署名付き MSI** である。詳細は [商用版ドキュメント §5](https://github.com/zyx-corporation/omomuki-pro/blob/main/docs/commercial-edition.md) を参照。

| 項目 | 内容 |
|------|------|
| 形式 | x64 MSI（Authenticode 署名） |
| インストール | ユーザー単位（管理者不要） |
| データ | アンインストール時も `~/.omomuki/` は保持 |

Community Edition（本リポジトリ OSS）は引き続き **PowerShell スクリプト** を第一選択とする。

### 将来の配布案（Community / 未実装）

| 方式 | 用途 |
|------|------|
| **WinGet** マニフェスト | 企業・再現性重視 |
| **Scoop** bucket | 開発者向け |

---

## 環境変数（共通）

| 変数 | 説明 |
|------|------|
| `OMOMUKI_REPO` | GitHub リポジトリ（既定 `zyx-corporation/omomuki`） |
| `OMOMUKI_REF` | ブランチ / タグ / SHA（既定 `main`） |
| `OMOMUKI_INSTALL_DIR` | インストールルート |
| `OMOMUKI_BIN_DIR` | ラッパー配置（Unix のみ。既定 `~/.local/bin`） |
| `OMOMUKI_SOURCE_DIR` | ローカル checkout から editable install |
| `OMOMUKI_DEV` | `1` で `[dev]` 依存を含める |
| `OMOMUKI_SKIP_INIT` | `1` で `omomuki init` をスキップ |
| `OMOMUKI_YES` | `1` で確認プロンプトをスキップ |

---

## インストール後

```bash
omomuki --version
omomuki help
omomuki init                    # スキップした場合
omomuki serve                   # Bridge（Extension 用）
```

→ [はじめに](getting-started.md) / [CLI マニュアル](cli-manual.md)

---

## Bridge 常駐化（任意）

Bridge をログイン時に自動起動する方法（LaunchAgent / systemd user / タスク スケジューラ）は Phase 6 で `omomuki serve --install-daemon` として提供予定。現状は手動で `omomuki serve` を実行する。

---

## アンインストール

```bash
# macOS / Linux
rm -rf ~/.local/share/omomuki ~/.local/bin/omomuki
# Profile データを残す場合は ~/.omomuki は削除しない
```

```powershell
# Windows
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Omomuki"
# PATH から ...\Omomuki\bin を手動削除（設定 → 環境変数）
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
