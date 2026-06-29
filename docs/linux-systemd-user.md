# Linux systemd --user — `sayane serve` の unit 化

Linux 上で `sayane serve` を user-scoped の `systemd --user` unit として
明示的に preview / write / verify する手順。

この手順は unit file の preview / apply / status までを対象とし、
desktop packaging や自動 update、広い lifecycle 自動化までは扱わない。

## 1. Preview

```bash
sayane app daemon-systemd-user-preview --json
```

確認ポイント:

- `unit_path`
- `program_arguments`
- `systemctl_commands`
- `stdout_path` / `stderr_path`

## 2. Apply

まず preview の `operation_id` と `preview_hash` を確認し、その値で apply する。

```bash
sayane app daemon-systemd-user-apply \
  --operation-id systemd-user-... \
  --confirm-operation-id systemd-user-... \
  --confirm-preview-hash ... \
  --json
```

これにより `~/.config/systemd/user/sayane-resident-bridge.service` が書き込まれる。

## 3. Reload / enable

unit file 書込後は CLI surface か `systemctl` を operator が明示的に実行する。

```bash
sayane app daemon-systemd-user-daemon-reload --json
sayane app daemon-systemd-user-enable-now --json
sayane app daemon-systemd-user-disable-now --json
```

同等の raw command は次のとおり。

```bash
systemctl --user daemon-reload
systemctl --user enable --now sayane-resident-bridge.service
```

## 4. Status

```bash
sayane app daemon-systemd-user-status --json
systemctl --user status sayane-resident-bridge.service --no-pager --full
```

## 5. Boundaries

- Community line では local-only の `sayane serve` 実行線を維持する
- unit file apply は explicit confirmation 必須
- `systemctl --user update/remove` の完全自動化はまだ閉じていない
- desktop packaging / installer / tray integration は別フェーズ

## Related

- [CLI Command Reference](reference/cli-command-reference.md)
- [Roadmap](roadmap.md)
- [macOS LaunchAgent 常駐化](macos-launchagent.md)
