"""Load T-RDE semantic maps from YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sayane.trde.models import SemanticMap


def load_semantic_map(path: Path | str) -> SemanticMap:
    """Load a SemanticMap from YAML.

    The YAML schema intentionally mirrors the pydantic model field names so the
    file can remain human-readable and diffable.
    """
    source = Path(path)
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"T-RDE semantic map must be a mapping: {source}")
    return SemanticMap.model_validate(data)


def semantic_map_from_dict(data: dict[str, Any]) -> SemanticMap:
    """Create a SemanticMap from an already-parsed mapping."""
    return SemanticMap.model_validate(data)
