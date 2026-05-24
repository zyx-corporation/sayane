"""Plugin hook registry for Commercial Edition extensions."""

from sayane.plugins.hooks import (
    ensure_hooks_loaded,
    register_before_candidate_approve,
    run_before_candidate_approve,
)

__all__ = [
    "ensure_hooks_loaded",
    "register_before_candidate_approve",
    "run_before_candidate_approve",
]
