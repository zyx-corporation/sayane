"""Local capability tokens for resident app preparation.

These tokens are intentionally simple. They model the capability boundary before
Sayane grows a resident local daemon with multiple local callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
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
    issuer: str = "local"
    purpose: str = "resident_app"
    issued_at: datetime | None = None
    expires_at: datetime | None = None

    def is_expired(self, *, now: datetime | None = None) -> bool:
        """Return True when the token is no longer valid."""
        if self.expires_at is None:
            return False
        current = now or datetime.now(UTC)
        expiry = self.expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)
        return current >= expiry

    def has(self, capability: ResidentCapability) -> bool:
        """Return True when this token grants the requested capability."""
        if self.is_expired():
            return False
        return "admin" in self.scopes or capability in self.scopes

    def require(self, capability: ResidentCapability) -> None:
        """Raise when this token does not grant the requested capability."""
        if self.is_expired():
            raise CapabilityError("resident app capability token expired")
        if not self.has(capability):
            raise CapabilityError(f"missing resident app capability: {capability}")

    def public_metadata(self) -> dict[str, object]:
        """Return non-sensitive capability metadata for diagnostics."""
        return {
            "subject": self.subject,
            "issuer": self.issuer,
            "purpose": self.purpose,
            "scopes": sorted(self.scopes),
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired(),
        }


@dataclass(frozen=True)
class CapabilityIssuer:
    """Local-only capability issuer boundary for resident app operations."""

    issuer: str = "local"
    default_ttl_seconds: int | None = 3600

    def issue(
        self,
        scopes: ResidentCapabilityScopes,
        *,
        subject: str = "local_user",
        purpose: str = "resident_app",
        ttl_seconds: int | None = None,
        issued_at: datetime | None = None,
    ) -> CapabilityToken:
        """Issue a local capability token with explicit metadata."""
        issued = issued_at or datetime.now(UTC)
        ttl = self.default_ttl_seconds if ttl_seconds is None else ttl_seconds
        expires_at = issued + timedelta(seconds=ttl) if ttl is not None else None
        return CapabilityToken(
            scopes=frozenset(scopes),
            subject=subject,
            issuer=self.issuer,
            purpose=purpose,
            issued_at=issued,
            expires_at=expires_at,
        )


def create_local_capability_token(
    scopes: ResidentCapabilityScopes,
    *,
    subject: str = "local_user",
    purpose: str = "resident_app",
    ttl_seconds: int | None = 3600,
    issuer: str = "local",
    issued_at: datetime | None = None,
) -> CapabilityToken:
    """Create a local resident app capability token."""
    return CapabilityIssuer(issuer=issuer, default_ttl_seconds=ttl_seconds).issue(
        scopes,
        subject=subject,
        purpose=purpose,
        issued_at=issued_at,
    )
