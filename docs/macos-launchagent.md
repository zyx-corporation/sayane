# macOS LaunchAgent — sayane serve 常駐化

`sayane serve` を macOS 上でログイン時に自動起動し、常駐させる手順。

LaunchDaemon（root）ではなく、ユーザー単位の **LaunchAgent** を使う。

## 1. 事前確認

```bash
# Profile Store が初期化されていること
sayane init

# 手動で起動できること
sayane serve
# → Local Bridge: http://127.0.0.1:38741 で待ち受け中

# 別のターミナルで health check
curl -s http://127.0.0.1:38741/health
# → {"status":"ok"}

# sayane の絶対パスを確認（plist に使う）
which sayane
# → /Users/tomyuk/.local/bin/sayane
```

`which sayane` の出力を控えておく。以降の例では `/Users/tomyuk/.local/bin/sayane` とする。

## 2. LaunchAgent plist 作成

```bash
mkdir -p ~/Library/LaunchAgents
```

`~/Library/LaunchAgents/jp.zyxcorp.sayane.serve.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>jp.zyxcorp.sayane.serve</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/tomyuk/.local/bin/sayane</string>
        <string>serve</string>
        <string>--host</string>
        <string>127.0.0.1</string>
        <string>--port</string>
        <string>38741</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/tomyuk/.sayane/logs/serve-stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/tomyuk/.sayane/logs/serve-stderr.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Users/tomyuk/.local/bin</string>
        <key>HOME</key>
        <string>/Users/tomyuk</string>
    </dict>
</dict>
</plist>
```

**ポイント:**

- `sayane` のパスは `which sayane` の結果に置き換える
- `--host 127.0.0.1` を明示（localhost のみ）
- `--allow-all-interfaces` は常駐化手順では使わない
- ログディレクトリは事前に作成しておく

```bash
mkdir -p ~/.sayane/logs
```

## 3. 登録・起動

```bash
# GUI セッションに登録（ユーザー単位）
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/jp.zyxcorp.sayane.serve.plist

# 有効化
launchctl enable gui/$(id -u)/jp.zyxcorp.sayane.serve

# 即時起動（すでに起動していれば再起動）
launchctl kickstart -k gui/$(id -u)/jp.zyxcorp.sayane.serve
```

## 4. 動作確認

```bash
# LaunchAgent の状態確認
launchctl print gui/$(id -u)/jp.zyxcorp.sayane.serve

# health check
curl -s http://127.0.0.1:38741/health
# → {"status":"ok"}

# ログ確認
tail -f ~/.sayane/logs/serve-stdout.log
tail -f ~/.sayane/logs/serve-stderr.log
```

## 5. 停止・解除

```bash
# 停止
launchctl bootout gui/$(id -u)/jp.zyxcorp.sayane.serve

# 完全に削除する場合
rm ~/Library/LaunchAgents/jp.zyxcorp.sayane.serve.plist
```

## 6. venv 利用時の注意

venv 内の `sayane` を使う場合は、絶対パスを venv の bin に向ける。

```xml
<string>/Users/tomyuk/projects/sayane/.venv/bin/sayane</string>
```

venv を削除・再作成するとパスが変わるため、その場合は plist を更新して再登録する。

## 7. セキュリティ境界

- **既定は `127.0.0.1`**。localhost 以外からアクセスできない。
- `--allow-all-interfaces` や `0.0.0.0` bind は **この常駐化手順では扱わない**。
- LAN 公開・VPN 越し公開が必要な場合は [Serve Network Policy](serve-network-policy.md) を参照。
- `~/.sayane/bridge.token` は `0600` パーミッションを維持すること。

## 8. トラブルシューティング

| 症状 | 対処 |
|------|------|
| `launchctl bootstrap` で `Already bootstrapped` | 先に `bootout` → `bootstrap` |
| `curl /health` が通らない | `tail ~/.sayane/logs/serve-stderr.log` で起動エラー確認 |
| `sayane: command not found` | plist の絶対パスが正しいか `which sayane` で再確認 |
| ログファイルが空 | `launchctl kickstart -k` で強制再起動 |
| ログイン後すぐに落ちる | `KeepAlive` が `true` か確認 |

## 関連

- [Serve Network Policy](serve-network-policy.md) — ネットワーク公開方針、SSH トンネル、systemd 例
- [インストール](install.md)
- [はじめに（利用者ガイド）](getting-started.md)
