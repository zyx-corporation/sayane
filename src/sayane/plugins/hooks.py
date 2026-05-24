"""Hook registry loaded via ``sayane.hooks`` entry points."""

from __future__ import annotations

from collections.abc import Callable
from importlib.metadata import entry_points
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sayane.bridge.config import BridgeConfig
    from sayane.core.candidate import CandidateUpdate

BeforeCandidateApproveHook = Callable[["BridgeConfig", "CandidateUpdate"], None]

_BEFORE_CANDIDATE_APPROVE: list[BeforeCandidateApproveHook] = []
_hooks_loaded = False


def register_before_candidate_approve(hook: BeforeCandidateApproveHook) -> None:
    _BEFORE_CANDIDATE_APPROVE.append(hook)


def run_before_candidate_approve(config: BridgeConfig, candidate: CandidateUpdate) -> None:
    ensure_hooks_loaded()
    for hook in _BEFORE_CANDIDATE_APPROVE:
        hook(config, candidate)


def ensure_hooks_loaded() -> None:
    global _hooks_loaded
    if _hooks_loaded:
        return
    try:
        eps = entry_points(group="sayane.hooks")
    except TypeError:
        eps = entry_points().get("sayane.hooks", ())
    for ep in eps:
        installer = ep.load()
        installer()
    _hooks_loaded = True


def reset_hooks() -> None:
    """Clear hooks and reload state (tests only)."""
    global _hooks_loaded
    _hooks_loaded = False
    _BEFORE_CANDIDATE_APPROVE.clear()
