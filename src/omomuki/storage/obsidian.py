"""Import and export context markdown with Obsidian vaults."""

import os
from pathlib import Path

from omomuki.storage.markdown import normalize_markdown

OMOMUKI_OBSIDIAN_VAULT_ENV = "OMOMUKI_OBSIDIAN_VAULT"

_SKIP_DIR_NAMES = frozenset({".obsidian", ".trash", ".git", "node_modules", ".cursor"})


def resolve_default_obsidian_vault() -> Path | None:
    """Return vault path from OMOMUKI_OBSIDIAN_VAULT when set and the directory exists."""
    raw = os.environ.get(OMOMUKI_OBSIDIAN_VAULT_ENV, "").strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    if path.is_dir():
        return path.resolve()
    return None


def resolve_obsidian_vault(vault: Path | None) -> Path:
    """CLI vault argument, or default from OMOMUKI_OBSIDIAN_VAULT when available."""
    if vault is not None:
        return vault
    default = resolve_default_obsidian_vault()
    if default is not None:
        return default
    raise FileNotFoundError(
        "Obsidian vault path required. Pass <vault> or set "
        f"{OMOMUKI_OBSIDIAN_VAULT_ENV} to an existing directory."
    )


def iter_vault_markdown(vault: Path) -> list[Path]:
    """List markdown files in a vault, skipping Obsidian metadata dirs."""
    vault = vault.resolve()
    if not vault.is_dir():
        raise FileNotFoundError(f"Vault not found: {vault}")

    results: list[Path] = []
    for path in sorted(vault.rglob("*.md")):
        if not path.is_file():
            continue
        if _is_under_skipped_dir(vault, path):
            continue
        results.append(path)
    return results


def import_from_vault(vault: Path, context_dir: Path) -> list[str]:
    """Copy normalized markdown from vault into context_dir. Returns relative paths."""
    vault = vault.resolve()
    context_dir = context_dir.resolve()
    context_dir.mkdir(parents=True, exist_ok=True)

    imported: list[str] = []
    for src in iter_vault_markdown(vault):
        rel = src.relative_to(vault).as_posix()
        dest = context_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        text = normalize_markdown(src.read_text(encoding="utf-8"))
        dest.write_text(text, encoding="utf-8")
        imported.append(rel)
    return imported


def export_to_vault(
    context_dir: Path,
    vault: Path,
    *,
    subdir: str = "omomuki",
) -> list[str]:
    """Export context_dir into vault/subdir (avoids overwriting vault root)."""
    context_dir = context_dir.resolve()
    vault = vault.resolve()
    if not context_dir.is_dir():
        raise FileNotFoundError(f"Context dir not found: {context_dir}")
    vault.mkdir(parents=True, exist_ok=True)

    target_root = vault / subdir
    exported: list[str] = []
    for src in sorted(context_dir.rglob("*.md")):
        if not src.is_file():
            continue
        rel = src.relative_to(context_dir).as_posix()
        dest = target_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        text = normalize_markdown(src.read_text(encoding="utf-8"))
        dest.write_text(text, encoding="utf-8")
        exported.append(f"{subdir}/{rel}")
    return exported


def _is_under_skipped_dir(vault: Path, path: Path) -> bool:
    try:
        rel = path.relative_to(vault)
    except ValueError:
        return True
    return any(part in _SKIP_DIR_NAMES or part.startswith(".") for part in rel.parts[:-1])
