"""Import and export context markdown with Obsidian vaults."""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from sayane.storage.markdown import normalize_markdown

SAYANE_OBSIDIAN_VAULT_ENV = "SAYANE_OBSIDIAN_VAULT"
EXPORT_METADATA_FILENAME = "sayane-export-metadata.json"
EXPORT_NOTICE_FILENAME = "SAYANE_EXPORT_NOTICE.txt"
EXPORT_METADATA_SCHEMA = "sayane-legacy-external-export-v1"
REDACTED_PATH = "<redacted:path>"

_SKIP_DIR_NAMES = frozenset({".obsidian", ".trash", ".git", "node_modules", ".cursor"})


class ExternalTargetPathError(ValueError):
    """Raised when an external export target path violates P3 boundary rules."""


def resolve_default_obsidian_vault() -> Path | None:
    """Return vault path from SAYANE_OBSIDIAN_VAULT when set and the directory exists."""
    raw = os.environ.get(SAYANE_OBSIDIAN_VAULT_ENV, "").strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    if path.is_dir():
        return path.resolve()
    return None


def resolve_obsidian_vault(vault: Path | None) -> Path:
    """CLI vault argument, or default from SAYANE_OBSIDIAN_VAULT when available."""
    if vault is not None:
        return vault
    default = resolve_default_obsidian_vault()
    if default is not None:
        return default
    raise FileNotFoundError(
        "Obsidian vault path required. Pass <vault> or set "
        f"{SAYANE_OBSIDIAN_VAULT_ENV} to an existing directory."
    )


def iter_vault_markdown(vault: Path, *, subdir: str | None = None) -> list[Path]:
    """List markdown files in a vault, skipping Obsidian metadata dirs."""
    vault = vault.resolve()
    if not vault.is_dir():
        raise FileNotFoundError(f"Vault not found: {vault}")
    scan_root = vault
    if subdir is not None:
        normalized_subdir = normalize_export_subdir(subdir)
        scan_root = (vault / normalized_subdir).resolve()
        try:
            scan_root.relative_to(vault)
        except ValueError as exc:
            raise ExternalTargetPathError(
                f"Import subdir escapes vault boundary: {subdir}"
            ) from exc
        if not scan_root.is_dir():
            raise FileNotFoundError(f"Vault subdir not found: {scan_root}")

    results: list[Path] = []
    for path in sorted(scan_root.rglob("*.md")):
        if not path.is_file():
            continue
        if _is_under_skipped_dir(vault, path):
            continue
        results.append(path)
    return results


def import_from_vault(vault: Path, context_dir: Path, *, subdir: str | None = None) -> list[str]:
    """Copy normalized markdown from vault into context_dir. Returns relative paths."""
    vault = vault.resolve()
    context_dir = context_dir.resolve()
    context_dir.mkdir(parents=True, exist_ok=True)

    imported: list[str] = []
    for src in iter_vault_markdown(vault, subdir=subdir):
        rel = src.relative_to(vault if subdir is None else (vault / normalize_export_subdir(subdir))).as_posix()
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
    subdir: str = "sayane",
) -> list[str]:
    """Export context_dir into vault/subdir (avoids overwriting vault root)."""
    context_dir = context_dir.resolve()
    vault = vault.resolve()
    if not context_dir.is_dir():
        raise FileNotFoundError(f"Context dir not found: {context_dir}")
    vault.mkdir(parents=True, exist_ok=True)

    normalized_subdir = normalize_export_subdir(subdir)
    target_root = (vault / normalized_subdir).resolve()
    try:
        target_root.relative_to(vault)
    except ValueError as exc:
        raise ExternalTargetPathError(
            f"Export subdir escapes vault boundary: {subdir}"
        ) from exc
    exported: list[str] = []
    for src in sorted(context_dir.rglob("*.md")):
        if not src.is_file():
            continue
        rel = src.relative_to(context_dir).as_posix()
        dest = target_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        text = normalize_markdown(src.read_text(encoding="utf-8"))
        dest.write_text(text, encoding="utf-8")
        exported.append(f"{normalized_subdir}/{rel}")
    _write_export_metadata(
        target_root,
        context_dir=context_dir,
        vault=vault,
        subdir=normalized_subdir,
        exported=exported,
    )
    return exported


def normalize_export_subdir(subdir: str) -> str:
    """Validate and normalize export subdir under the external vault root."""
    raw = subdir.strip()
    if not raw:
        raise ExternalTargetPathError("Export subdir must not be empty.")
    path = Path(raw)
    if path.is_absolute():
        raise ExternalTargetPathError("Export subdir must be relative to the vault root.")
    normalized_parts: list[str] = []
    for part in path.parts:
        if part in {"", ".", ".."}:
            raise ExternalTargetPathError(f"Unsupported export subdir segment: {part or '<empty>'}")
        if part in _SKIP_DIR_NAMES or part.startswith("."):
            raise ExternalTargetPathError(f"Forbidden export subdir segment: {part}")
        normalized_parts.append(part)
    if not normalized_parts:
        raise ExternalTargetPathError("Export subdir must not resolve to the vault root.")
    return "/".join(normalized_parts)


def _write_export_metadata(
    target_root: Path,
    *,
    context_dir: Path,
    vault: Path,
    subdir: str,
    exported: list[str],
) -> None:
    target_root.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema_version": EXPORT_METADATA_SCHEMA,
        "export_kind": "legacy_external_compatibility",
        "generated_at": datetime.now(UTC).isoformat(),
        "is_canonical_profile": False,
        "is_derived_context": True,
        "requires_candidate_review_for_merge": True,
        "requires_legacy_compatible_confirmation": True,
        "retention": {
            "recommended_max_age": "30d",
            "delete_after_import_or_review": True,
            "canonical_promotion_requires_candidate_review": True,
        },
        "redaction": {
            "local_paths_redacted": True,
            "raw_capture_excluded": True,
            "candidate_review_history_excluded": True,
            "lineage_history_excluded": True,
        },
        "source": {
            "context_dir": REDACTED_PATH,
            "vault_root": REDACTED_PATH,
            "subdir": subdir,
        },
        "summary": {
            "markdown_file_count": len(exported),
        },
        "warnings": [
            "This export is a compatibility artifact, not canonical Sayane profile state.",
            "Imported or edited content must pass through Candidate Review before canonical merge.",
        ],
    }
    (target_root / EXPORT_METADATA_FILENAME).write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (target_root / EXPORT_NOTICE_FILENAME).write_text(
        "This directory is a Sayane legacy compatibility export.\n"
        "It is derived context, not canonical profile state.\n"
        "Local source paths are redacted in export metadata.\n"
        "Delete this export after import or review unless a separate retention decision exists.\n"
        "Any re-imported or edited content still requires Candidate Review before canonical merge.\n",
        encoding="utf-8",
    )


def _is_under_skipped_dir(vault: Path, path: Path) -> bool:
    try:
        rel = path.relative_to(vault)
    except ValueError:
        return True
    return any(part in _SKIP_DIR_NAMES or part.startswith(".") for part in rel.parts[:-1])
