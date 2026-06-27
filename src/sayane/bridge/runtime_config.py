"""Bridge route helpers for vault-aware runtime-backed config resolution."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException

from sayane.bridge.config import BridgeConfig

if TYPE_CHECKING:
    from sayane.app.runtime import ResidentRuntime


def resolve_runtime_backed_bridge_config(
    cfg: BridgeConfig,
    *,
    profile_id: str = "default",
    required_scope: str | None = None,
    error_message: str | None = None,
) -> tuple[BridgeConfig, "ResidentRuntime | None", dict[str, Any]]:
    """Return a BridgeConfig backed by resident repositories when available.

    When the resident runtime is connected to a Local Vault backend, callers may
    require a scope so the returned config carries the matching process-local
    unlock session for repository reads or writes.
    """
    from sayane.app.runtime import build_resident_runtime

    runtime = build_resident_runtime(
        home=cfg.home,
        host=cfg.host,
        port=cfg.port,
        profile_id=profile_id,
    )
    if runtime.service.repositories is None:
        return cfg, runtime, {}

    repository_session: Any | None = None
    repository_kwargs: dict[str, Any] = {}
    if runtime.vault_runtime is not None and required_scope is not None:
        repository_session = runtime.first_vault_session_for_scope(required_scope)
        if repository_session is None:
            raise HTTPException(
                status_code=409,
                detail=error_message or "Local Vault access requires an active unlock session",
            )
        repository_kwargs = {"session": repository_session}

    route_cfg = replace(
        cfg,
        repositories=runtime.service.repositories,
        repository_session=repository_session,
    )
    return route_cfg, runtime, repository_kwargs
