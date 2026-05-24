from pathlib import Path

from sayane.storage.obsidian import export_to_vault, import_from_vault, iter_vault_markdown


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


def test_iter_vault_markdown_lists_files(tmp_path: Path) -> None:
    vault = tmp_path / "v"
    vault.mkdir()
    (vault / "a.md").write_text("x", encoding="utf-8")
    paths = iter_vault_markdown(vault)
    assert len(paths) == 1
