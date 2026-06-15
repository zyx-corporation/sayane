"""Local capability tokens for resident app preparation.

These tokens are intentionally simple. They model the capability boundary before
Sayane grows a resident local daemon with multiple local callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ResidentCapability = Literal[
    "ui",
    "capture",
    "review",
    "export",
    "mcp",
    "bridge",
    "admin",
]
ResidentCapabilityScopes = (
    list[ResidentCapability] | tuple[ResidentCapability, ...] | set[ResidentCapability]
)


class CapabilityError(PermissionError):
    """Raised when a resident app operation lacks a required capability."""


@dataclass(frozen=True)
class CapabilityToken:
    """Explicit local capability token for resident app operations."""

    scopes: frozenset[ResidentCapability]
    subject: str = "local_user"

    def has(self, capability: ResidentCapability) -> bool:
        """Return True when this token grants the requested capability."""
        return "admin" in self.scopes or capability in self.scopes

    def require(self, capability: ResidentCapability) -> None:
        """Raise when this token does not grant the requested capability."""
        if not self.has(capability):
            raise CapabilityError(f"missing resident app capability: {capability}")


def create_local_capability_token(
    scopes: ResidentCapabilityScopes,
    *,
    subject: str = "local_user",
) -> CapabilityToken:
    """Create a local resident app capability token."""
    return CapabilityToken(scopes=frozenset(scopes), subject=subject)
