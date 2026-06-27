from pathlib import Path

import json

from sayane.storage.obsidian import (
    ExternalTargetPathError,
    EXPORT_METADATA_FILENAME,
    EXPORT_NOTICE_FILENAME,
    export_to_vault,
    import_from_vault,
    iter_vault_markdown,
    normalize_export_subdir,
)


def test_import_skips_obsidian_dir(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note.md").write_text("# Note\n", encoding="utf-8")
    (vault / ".obsidian").mkdir()
    (vault / ".obsidian" / "hidden.md").write_text("# Hidden\n", encoding="utf-8")

    context_dir = tmp_path / "context"
    imported = import_from_vault(vault, context_dir)

    assert imported == ["note.md"]
    assert (context_dir / "note.md").exists()
    assert not (context_dir / ".obsidian").exists()


def test_export_to_subdirectory(tmp_path: Path) -> None:
    context_dir = tmp_path / "context"
    context_dir.mkdir()
    (context_dir / "a.md").write_text("# A\n", encoding="utf-8")
    vault = tmp_path / "vault"

    exported = export_to_vault(context_dir, vault, subdir="sayane")

    assert exported == ["sayane/a.md"]
    assert (vault / "sayane" / "a.md").read_text(encoding="utf-8").startswith("# A")
    metadata = json.loads((vault / "sayane" / EXPORT_METADATA_FILENAME).read_text(encoding="utf-8"))
    assert metadata["schema_version"] == "sayane-legacy-external-export-v1"
    assert metadata["is_canonical_profile"] is False
    assert metadata["requires_legacy_compatible_confirmation"] is True
    assert metadata["retention"]["recommended_max_age"] == "30d"
    assert metadata["redaction"]["local_paths_redacted"] is True
    assert metadata["source"]["context_dir"] == "<redacted:path>"
    assert metadata["source"]["vault_root"] == "<redacted:path>"
    assert (vault / "sayane" / EXPORT_NOTICE_FILENAME).exists()


def test_iter_vault_markdown_lists_files(tmp_path: Path) -> None:
    vault = tmp_path / "v"
    vault.mkdir()
    (vault / "a.md").write_text("x", encoding="utf-8")
    paths = iter_vault_markdown(vault)
    assert len(paths) == 1


def test_iter_vault_markdown_can_scope_to_safe_subdir(tmp_path: Path) -> None:
    vault = tmp_path / "v"
    (vault / "safe").mkdir(parents=True)
    (vault / "safe" / "a.md").write_text("x", encoding="utf-8")
    (vault / "other").mkdir()
    (vault / "other" / "b.md").write_text("y", encoding="utf-8")
    paths = iter_vault_markdown(vault, subdir="safe")
    assert [p.name for p in paths] == ["a.md"]


def test_import_from_vault_can_scope_to_safe_subdir(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / "safe").mkdir(parents=True)
    (vault / "safe" / "note.md").write_text("# Note\n", encoding="utf-8")
    (vault / "other").mkdir()
    (vault / "other" / "skip.md").write_text("# Skip\n", encoding="utf-8")
    context_dir = tmp_path / "context"
    imported = import_from_vault(vault, context_dir, subdir="safe")
    assert imported == ["note.md"]
    assert (context_dir / "note.md").exists()
    assert not (context_dir / "skip.md").exists()


def test_normalize_export_subdir_rejects_forbidden_segments() -> None:
    for bad in ("", ".", "..", ".obsidian", ".hidden", "/abs", "../escape", "a/../b", "node_modules"):
        try:
            normalize_export_subdir(bad)
        except ExternalTargetPathError:
            continue
        raise AssertionError(f"expected failure for {bad!r}")


def test_normalize_export_subdir_allows_safe_nested_path() -> None:
    assert normalize_export_subdir("exports/sayane") == "exports/sayane"
