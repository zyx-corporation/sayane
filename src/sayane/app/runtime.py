"""Resident runtime builder for local app command wiring.

This module keeps resident command assembly separate from CLI, Bridge routes,
and concrete storage adapters. It is intentionally thin until production
runtime selection is decided.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sayane.app.capabilities import CapabilityToken, create_local_capability_token
from sayane.app.service import ResidentAppService
from sayane.bridge.config import BridgeConfig
from sayane.storage.repositories import RepositoryBundle


@dataclass(frozen=True)
class ResidentRuntime:
    """Assembled resident runtime boundary for local commands."""

    service: ResidentAppService
    bridge_config: BridgeConfig
    capabilities: dict[str, CapabilityToken] = field(default_factory=dict)

    def describe(self) -> dict[str, Any]:
        """Return non-sensitive runtime diagnostics."""
        payload = self.service.describe()
        payload["bridge_host"] = self.bridge_config.host
        payload["bridge_port"] = self.bridge_config.port
        payload["capabilities"] = sorted(self.capabilities)
        return payload


def build_resident_runtime(
    *,
    home: Path | None = None,
    host: str = "127.0.0.1",
    port: int = 38741,
    profile_id: str = "default",
    repositories: RepositoryBundle | None = None,
) -> ResidentRuntime:
    """Build a local resident runtime boundary.

    This does not select production storage by itself. Callers may inject a
    repository bundle when a persistent runtime has been explicitly selected.
    """
    bridge_config = BridgeConfig(host=host, port=port, home=home or BridgeConfig().home)
    service = ResidentAppService(profile_id=profile_id, repositories=repositories)
    capabilities = {
        "capture": create_local_capability_token(["capture"]),
        "admin": create_local_capability_token(["admin"]),
    }
    return ResidentRuntime(
        service=service,
        bridge_config=bridge_config,
        capabilities=capabilities,
    )
