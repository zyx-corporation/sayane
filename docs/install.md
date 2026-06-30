# インストール

現状の **主導線は `curl | bash` による CLI / Bridge install** である。  
macOS native app はその後段に必要な場合だけ追加する補助導線として扱う。Extension ビルドは別途 [Extension マニュアル](extension-manual.md) を参照。

| OS | 方式 | スクリプト / パッケージ |
|----|------|------------------------|
| **macOS** | curl + bash | `scripts/install.sh` |
| **Linux** | curl + bash | `scripts/install.sh` |
| **Windows（Community）** | PowerShell (`irm` + `iex`) | `scripts/install.ps1` |

## 前提

- **Python 3.11+**
- **git**（git fallback / custom ref / local source install を使う場合）
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

### 推奨導線

まずはこれだけでよい:

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
sayane --version
sayane serve
```

この `curl | bash` 導線で CLI / Bridge runtime まで整う。  
native macOS app は **必要になったときだけ** 後から追加する。

最短の operator handoff は:

- [v1.0.76 curl+bash Operator Quickstart](release/v1.0.76-curl-bash-operator-quickstart.md)

ローカルで installer 自体を確認したい場合:

```bash
bash scripts/check-install-local.sh
```

### CLI / Bridge

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install.sh | bash
```

現行 installer は通常 install で **PyPI を先に試し、必要時だけ git fallback** する。  
そのため `curl | bash` 主導線では、常に git を前提にしなくてよい。

特定バージョン（タグ）:

```bash
SAYANE_REF=v1.0.13 curl -fsSL .../install.sh | bash
```

`~/.local/bin` が PATH に無い場合、シェルプロファイルに追加:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### 開発者（リポジトリ clone 済み）

```bash
SAYANE_SOURCE_DIR=/path/to/sayane SAYANE_DEV=1 bash scripts/install.sh
```

インストール元を固定したい場合:

```bash
# PyPI のみ
SAYANE_INSTALL_SOURCE=pypi bash scripts/install.sh

# git のみ
SAYANE_INSTALL_SOURCE=git SAYANE_REF=main bash scripts/install.sh
```

### native macOS app（補助導線）

native macOS app は現時点では **repo-local build から `.app` bundle を作り、`~/Applications` へ入れる補助導線** を採る。  
Bridge / CLI runtime は引き続きローカル Python 環境に依存するため、まず上の `curl | bash` 主導線を通しておく。  
通常起動は native app から行い、app 側が installed `sayane` CLI を見つけて Local Bridge を内部 backend として起動する前提へ寄せている。
生成される `.app` bundle には `Contents/Resources/run-bridge-helper.sh` も同梱され、installed app は repo-local launcher ではなくこの helper を優先して使う。

repo checkout を前提にしない install 導線として、GitHub release zip から直接 `~/Applications` へ入れる補助スクリプトも使える:

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install-macos-app-release.sh | bash
```

特定バージョンを入れたい場合:

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/sayane/main/scripts/install-macos-app-release.sh | bash -s -- --version 1.0.14.post1
```

この release zip install も、前提は変わらない:

- 先に `curl | bash` で CLI / Bridge runtime を入れておく
- native app 自体は `~/Applications/SayaneApp.app` に入る薄い shell である
- backend は native app 側が installed `sayane` CLI または bundled helper から起動する
- self-contained Python runtime や notarized dmg を意味しない

bundle 作成:

```bash
bash scripts/build-macos-app-bundle.sh
# zip も必要なら:
bash scripts/build-macos-app-bundle.sh --zip
```

生成物:

- `dist/macos/SayaneApp.app`
- `dist/macos/SayaneApp-<version>-macos-release.zip`
- `dist/macos/SayaneApp-latest-macos-release.zip`
- `dist/macos/SayaneApp-<version>-macos-release.sha256`
- `dist/macos/SayaneApp-<version>-macos-release.manifest.txt`

ローカル install:

```bash
bash scripts/install-macos-app.sh
bash scripts/refresh-macos-app.sh
```

削除:

```bash
bash scripts/uninstall-macos-app.sh
```

既定の配置先:

| 種別 | パス |
|------|------|
| build artifact | `dist/macos/SayaneApp.app` |
| local install | `~/Applications/SayaneApp.app` |

主なオプション:

```bash
# 既存 build を再利用
bash scripts/install-macos-app.sh --no-build

# 停止 → 再 install → verify → open をまとめて実行
bash scripts/refresh-macos-app.sh

# debug bundle を install
bash scripts/install-macos-app.sh --debug

# 別ディレクトリへ install
bash scripts/install-macos-app.sh --applications /tmp/SayaneApps

# local ad-hoc sign を付けずに install
bash scripts/install-macos-app.sh --no-adhoc-sign
```

通常の更新導線:

```bash
bash scripts/refresh-macos-app.sh --no-build
```

release zip から更新したい場合:

```bash
bash scripts/install-macos-app-release.sh
# または特定バージョン:
bash scripts/install-macos-app-release.sh --version 1.0.14.post1
```

起動:

```bash
open ~/Applications/SayaneApp.app
```

確認:

```bash
bash scripts/verify-macos-app-install.sh
plutil -lint ~/Applications/SayaneApp.app/Contents/Info.plist
file ~/Applications/SayaneApp.app/Contents/MacOS/SayaneApp
open ~/Applications/SayaneApp.app
```

注意:

- 主導線はあくまで `curl | bash` による CLI / Bridge install
- 現行 macOS app は **self-contained Python bundle / signed pkg / notarized dmg** ではない
- 現行 macOS app は installed `sayane` CLI（`~/.local/bin/sayane`、`PATH`、`SAYANE_CLI_BIN`）を優先して Local Bridge を起動する
- installed `.app` bundle には bridge 起動 helper が同梱され、repo checkout が無くても native app 側の起動導線は成立する
- local install では `open ~/Applications/SayaneApp.app` を通しやすくするため ad-hoc sign を付与する
- local Bridge と `~/.sayane/bridge.token` を使う現行 operator model のまま動く
- そのため現段階の配布単位は「native app bundle + local CLI/Bridge runtime」である
- Linux / Windows の追加 packaging は保留中

署名 / 公証準備:

```bash
# まず plan を確認
bash scripts/sign-macos-app.sh --dry-run --identity "Developer ID Application: Example"
bash scripts/notarize-macos-app.sh --dry-run --profile sayane-notary
bash scripts/prepare-macos-release-artifacts.sh
```

実行時の想定:

- 署名: `SAYANE_MACOS_CODESIGN_IDENTITY`
- 公証: `SAYANE_MACOS_NOTARY_PROFILE`
- 任意メモ: `SAYANE_MACOS_TEAM_ID`, `SAYANE_MACOS_APPLE_ID`
- installer 終了時に最短コマンドも見たい場合: `SAYANE_PRINT_QUICKSTART=1`

現時点では **署名 / 公証の補助スクリプトと手順を先に整備** しており、実際の `Developer ID`
証明書・`notarytool` プロファイル投入は maintainers 側の秘密情報が揃ってから行う。

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

### WinGet / Scoop（Community / プレビュー）

| 方式 | 用途 | リポジトリ内 |
|------|------|--------------|
| **WinGet** マニフェスト | 企業・再現性重視 | [`packaging/winget/`](../packaging/winget/)（draft、未公開） |
| **Scoop** bucket | 開発者向け | [`packaging/scoop/`](../packaging/scoop/)（draft、未公開） |

**現状の推奨インストール**は上記 PowerShell ワンライナー。WinGet / Scoop は #83 のマニフェスト雛形のみ — `microsoft/winget-pkgs` または公開 bucket への PR は未実施。

WinGet 検証（マニフェストを有効化した後）:

```powershell
winget validate .\packaging\winget\zyx-corporation.sayane.yaml
```

Scoop（カスタム bucket に `sayane.json` を配置した場合）:

```powershell
scoop install sayane
```

詳細: [`packaging/winget/README.md`](../packaging/winget/README.md) / [`packaging/scoop/README.md`](../packaging/scoop/README.md)

### その他（未実装）

| 方式 | 用途 |
|------|------|
| PyPI `pip install sayane` | **利用可能**（現行 docs 基準: v1.0.13） |

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
sayane serve                   # Bridge（MCP 以外のローカル連携や legacy Extension 用）
bash scripts/install-macos-app.sh --no-build   # macOS native app を入れる場合
```

→ [はじめに](getting-started.md) / [CLI マニュアル](cli-manual.md)

---

## PyPI

**公開済み:** https://pypi.org/project/sayane/ （現行 docs 基準: v1.0.13）

```bash
pip install sayane
# または特定版（zsh ではクォート推奨）:
pip install "sayane==1.0.13"
```

> **zsh ユーザー:** `sayane==1.0.13` をクォートしないと `zsh: no matches found` になることがあります。

PyPI には **CLI + Bridge + MCP** のみ含まれます。Chrome Extension は別途 [Extension マニュアル](extension-manual.md) を参照。なお Extension は現行方針では **freeze / deprecated** であり、主な導線は CLI / Bridge / MCP である。

初回公開: **2026-05-30**。現行リポジトリ版は `1.0.13`。

Maintainer 手順（再公開時）: 以下チェックリスト。

Git タグから直接:

```bash
pip install "sayane @ git+https://github.com/zyx-corporation/sayane.git@v1.0.13"
```

公開履歴は [CHANGELOG](../CHANGELOG.md) を参照。

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
