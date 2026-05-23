"""Generate context_index from scanned context markdown files."""

from pathlib import Path

from omomuki.core.models import ContextIndex, OmomukiProfile
from omomuki.storage.filesystem import FileSystemContextStore

_DEFAULT_ENTRYPOINT = "MyContext.md"
_DEFAULT_HANDOFF = "AI_HANDOFF.md"


def generate_context_index(profile_dir: Path, profile: OmomukiProfile) -> ContextIndex:
    """Scan context/ and build entries plus entrypoint/handoff hints."""
    store = FileSystemContextStore(profile_dir)
    entries = [store.relative_path(p) for p in store.list_markdown()]

    entrypoint = profile.context_index.entrypoint
    handoff = profile.context_index.handoff

    prefixed = [f"context/{e}" for e in entries]

    if entrypoint and _entry_exists(profile_dir, entrypoint):
        pass
    elif _DEFAULT_ENTRYPOINT in entries:
        entrypoint = f"context/{_DEFAULT_ENTRYPOINT}"
    elif entries:
        entrypoint = f"context/{entries[0]}"
    else:
        entrypoint = profile.context_index.entrypoint or f"context/{_DEFAULT_ENTRYPOINT}"

    handoff_name = _DEFAULT_HANDOFF
    if handoff and _entry_exists(profile_dir, handoff):
        pass
    elif handoff_name in entries:
        handoff = f"context/{handoff_name}"
    else:
        handoff = profile.context_index.handoff

    return ContextIndex(entrypoint=entrypoint, handoff=handoff, entries=prefixed)


def apply_context_index(profile: OmomukiProfile, profile_dir: Path) -> OmomukiProfile:
    """Return profile copy with regenerated context_index."""
    idx = generate_context_index(profile_dir, profile)
    return profile.model_copy(update={"context_index": idx})


def _entry_exists(profile_dir: Path, rel: str) -> bool:
    path = (profile_dir / rel).resolve()
    root = profile_dir.resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return path.is_file()
