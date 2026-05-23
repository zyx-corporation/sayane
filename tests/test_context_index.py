from pathlib import Path

from omomuki.core.loader import load_profile
from omomuki.storage.context_index import apply_context_index, generate_context_index


def test_generate_context_index_from_context_dir(tmp_path: Path, examples_dir: Path) -> None:
    profile_dir = tmp_path / "store"
    profile_dir.mkdir()
    ctx = profile_dir / "context"
    ctx.mkdir()
    (ctx / "NoteA.md").write_text("# A\n", encoding="utf-8")
    (ctx / "NoteB.md").write_text("# B\n", encoding="utf-8")

    profile = load_profile(examples_dir / "profiles" / "minimal.yaml")
    idx = generate_context_index(profile_dir, profile)

    assert "context/NoteA.md" in idx.entries
    assert "context/NoteB.md" in idx.entries
    assert idx.entrypoint is not None


def test_apply_context_index_persists_entries(tmp_path: Path, examples_dir: Path) -> None:
    profile_dir = tmp_path / "store"
    (profile_dir / "context").mkdir(parents=True)
    (profile_dir / "context" / "X.md").write_text("# X\n", encoding="utf-8")

    profile = load_profile(examples_dir / "profiles" / "minimal.yaml")
    updated = apply_context_index(profile, profile_dir)
    assert any("context/X.md" in e for e in updated.context_index.entries)
