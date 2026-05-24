"""FileSystem-backed Profile and Context repositories."""

from pathlib import Path

from sayane.core.loader import load_profile, save_profile
from sayane.core.models import SayaneProfile
from sayane.storage.markdown import normalize_markdown


class FileSystemProfileStore:
    """Profile store rooted at a directory containing sayane.profile.yaml."""

    def __init__(self, profile_dir: Path, profile_filename: str = "sayane.profile.yaml") -> None:
        self._profile_dir = profile_dir.resolve()
        self._profile_path = self._profile_dir / profile_filename

    @property
    def profile_dir(self) -> Path:
        return self._profile_dir

    @property
    def profile_path(self) -> Path:
        return self._profile_path

    def load(self) -> SayaneProfile:
        return load_profile(self._profile_path)

    def save(self, profile: SayaneProfile) -> None:
        save_profile(self._profile_path, profile)


class FileSystemContextStore:
    """Context markdown files under profile_dir/context/."""

    def __init__(self, profile_dir: Path, context_subdir: str = "context") -> None:
        self._profile_dir = profile_dir.resolve()
        self._context_dir = self._profile_dir / context_subdir

    @property
    def profile_dir(self) -> Path:
        return self._profile_dir

    @property
    def context_dir(self) -> Path:
        return self._context_dir

    def list_markdown(self) -> list[Path]:
        if not self._context_dir.exists():
            return []
        files: list[Path] = []
        for path in sorted(self._context_dir.rglob("*.md")):
            if path.is_file():
                files.append(path)
        return files

    def relative_path(self, absolute: Path) -> str:
        return absolute.relative_to(self._context_dir).as_posix()

    def read_text(self, relative_path: str) -> str | None:
        path = self._safe_path(relative_path)
        if path is None or not path.is_file():
            return None
        return normalize_markdown(path.read_text(encoding="utf-8"))

    def write_text(self, relative_path: str, content: str) -> Path:
        path = self._safe_path(relative_path)
        if path is None:
            raise ValueError(f"Invalid context path: {relative_path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        normalized = normalize_markdown(content)
        path.write_text(normalized, encoding="utf-8")
        return path

    def _safe_path(self, relative_path: str) -> Path | None:
        rel = Path(relative_path)
        if rel.is_absolute() or ".." in rel.parts:
            return None
        candidate = (self._context_dir / rel).resolve()
        try:
            candidate.relative_to(self._context_dir.resolve())
        except ValueError:
            return None
        return candidate
