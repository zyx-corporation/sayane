# Storage Backend プラグイン契約

Commercial Edition（[omomuki-pro](https://github.com/zyx-corporation/omomuki-pro)）が `encrypted-sqlite` backend を提供するための **OSS 側インターフェース契約**。

## リポジトリ抽象

| Protocol | 別名 | 役割 |
|----------|------|------|
| `ProfileRepository` | `ProfileStore` | Profile YAML の load / save |
| `ContextRepository` | `ContextStore` | context Markdown の CRUD |
| `LineageRepository` | `LineageStore` | lineage / 監査イベント |

定義: `src/omomuki/storage/base.py`

`StorageBundle` は backend 名と 3 リポジトリを束ねる:

```python
from omomuki.storage import open_storage

bundle = open_storage()
profile = bundle.profile.load()
bundle.context.write_text("notes.md", "# Notes")
bundle.lineage.append("event", {"key": "value"})
```

## 設定

`~/.omomuki/config.yaml`:

```yaml
storage:
  backend: filesystem
  profile: default
```

CLI:

```bash
omomuki storage backend status
omomuki storage backend list
omomuki storage backend set filesystem
```

## プラグイン登録（omomuki-pro）

`pyproject.toml` の entry point グループ `omomuki.storage_backends` に factory を登録する:

```toml
[project.entry-points."omomuki.storage_backends"]
encrypted-sqlite = "omomuki_pro.storage:create_backend"
```

Factory シグネチャ:

```python
def create_backend(
    storage_config: StorageConfig,
    *,
    home: Path | None = None,
    profile_dir: Path | None = None,
) -> StorageBundle: ...
```

## 組み込み backend

| backend | 提供 | Git 自動コミット |
|---------|------|-----------------|
| `filesystem` | OSS（Community） | あり |
| `encrypted-sqlite` | omomuki-pro | なし |

## 契約テスト

`tests/test_storage_backend.py` に mock backend 登録テストあり。omomuki-pro は同一 factory シグネチャで CI 契約テストを追加可能。

## 関連

- [Storage マニュアル](storage-manual.md)
- [商用版（omomuki-pro）](https://github.com/zyx-corporation/omomuki-pro/blob/main/docs/commercial-edition.md)
- [development-principles.md §8.7](development-principles.md)
- Issue: [#65](https://github.com/zyx-corporation/omomuki/issues/65)
