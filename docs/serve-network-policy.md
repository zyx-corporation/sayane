# Sayane Serve Network Policy

## 方針

`sayane serve` はデフォルトで `127.0.0.1`（localhost）にのみバインドする。

Sayane は文脈履歴、思考ログ、RDE 差分、Chronicle Stack 連携、個人知識基盤を扱うため、public internet への未認証公開は禁止する。

一方で、`noor` のような private lab node 上で常時稼働させ、LAN / VPN / Tailscale / ZeroTier / WireGuard 経由で他端末から利用するユースケースは正当である。

## デフォルト動作

```bash
sayane serve
```

- host: `127.0.0.1`
- port: `38741`
- 外部端末からはアクセス不可。localhost のみ。

## プライベートネットワーク公開

```bash
sayane serve --host 192.168.33.32 --port 38741
```

起動時に以下の warning が表示される。

```text
WARNING: localhost 以外のアドレスで待ち受けています (192.168.33.32:38741).
Sayane は信頼できるプライベートネットワーク（LAN / VPN / Tailscale / ZeroTier / WireGuard / SSH tunnel）上でのみ公開してください。
インターネットへ直接公開しないでください。
```

VPN インターフェース（Tailscale / ZeroTier など）の IP も同様に許可される。

## SSH トンネル経由の利用

リモート端末から安全にアクセスする場合は SSH トンネルを推奨する。

```bash
# noor 上で sayane serve を起動（localhost only）
ssh tomyuk@noor "sayane serve"

# ローカル端末から SSH トンネルを張る
ssh -L 38741:127.0.0.1:38741 tomyuk@noor

# ローカル端末のブラウザからアクセス
# http://127.0.0.1:38741
```

## 全インターフェースへのバインド（非推奨）

`0.0.0.0` または `::` へのバインドはデフォルトで拒否される。

```bash
sayane serve --host 0.0.0.0
# ERROR: 0.0.0.0 へのバインドには --allow-all-interfaces が必要です。
```

明示的に許可する場合は `--allow-all-interfaces` を付与する。

```bash
sayane serve --host 0.0.0.0 --port 38741 --allow-all-interfaces
```

起動時に強い warning が表示される。

```text
WARNING: すべてのインターフェースで待ち受けています (0.0.0.0:38741).
プライベートな文脈データが localhost 外に露出する可能性があります。
firewall / VPN / 認証付きリバースプロキシで保護してください。
未認証でのインターネット直接公開はサポート対象外です。
```

**注意:** `--allow-all-interfaces` は firewall / VPN / 認証付きリバースプロキシで保護されている場合のみ使用すること。public internet への未認証公開はサポート対象外。

## PostgreSQL の公開について

Sayane Core / Bridge に加えて、PostgreSQL を storage backend として使用する場合も、public internet へ直接公開しないこと。

PostgreSQL は常に localhost または private network 内に留め、必要に応じて SSH トンネルまたは VPN 経由でアクセスする。

## systemd service 例

### localhost only（デフォルト）

```ini
[Unit]
Description=Sayane local serve
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=tomyuk
WorkingDirectory=/home/tomyuk/projects/sayane
ExecStart=/usr/local/bin/sayane serve --host 127.0.0.1 --port 38741
Restart=on-failure
RestartSec=5
Environment=RUST_LOG=info

[Install]
WantedBy=multi-user.target
```

### private LAN 公開

```ini
[Unit]
Description=Sayane private network serve
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=tomyuk
WorkingDirectory=/home/tomyuk/projects/sayane
ExecStart=/usr/local/bin/sayane serve --host 192.168.33.32 --port 38741
Restart=on-failure
RestartSec=5
Environment=RUST_LOG=info

[Install]
WantedBy=multi-user.target
```

## 確認コマンド

```bash
ss -ltnp | grep 38741
```

期待される出力:

```text
127.0.0.1:38741       # localhost only（デフォルト）
192.168.33.32:38741   # private network 公開
0.0.0.0:38741         # 全インターフェース（--allow-all-interfaces 必須）
```

## 制限事項

- 現時点では HTTPS / TLS は未対応。信頼できるネットワーク内でのみ使用すること。
- 認証は Bearer token による。token は `~/.sayane/bridge.token` に保存される。
- public internet への安全な公開が必要な場合は、認証付きリバースプロキシ（nginx / Caddy 等）の背後に配置することを推奨する。
