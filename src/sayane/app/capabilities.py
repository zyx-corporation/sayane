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
ResidentCapabilitySurface = Literal["capture", "ui", "mcp", "bridge", "admin"]


class CapabilityError(PermissionError):
    """Raised when a resident app operation lacks a required capability."""


@dataclass(frozen=True)
class CapabilityIssuerPolicy:
    """Non-secret policy metadata for local resident capability issuance.

    This is not production authentication. It makes the local/development token
    assumptions explicit before daemon lifecycle and durable credentials exist.
    """

    name: str = "local_development"
    token_persistence: Literal["non_persistent", "persistent"] = "non_persistent"
    unlock_session_binding: Literal["unbound", "bound"] = "unbound"
    network_auth: Literal["not_supported", "required"] = "not_supported"
    cryptographic_signing: Literal["not_supported", "required"] = "not_supported"
    production_ready: bool = False

    def require_non_persistent(self) -> None:
        """Reject policies that would silently persist local tokens."""
        if self.token_persistence != "non_persistent":
            raise CapabilityError("persistent capability tokens are not supported yet")

    def public_metadata(self) -> dict[str, object]:
        """Return safe capability issuer policy diagnostics."""
        return {
            "name": self.name,
            "token_persistence": self.token_persistence,
            "unlock_session_binding": self.unlock_session_binding,
            "network_auth": self.network_auth,
            "cryptographic_signing": self.cryptographic_signing,
            "production_ready": self.production_ready,
        }


@dataclass(frozen=True)
class CapabilityToken:
    """Explicit local capability token for resident app operations."""

    scopes: frozenset[ResidentCapability]
    subject: str = "local_user"
    issuer: str = "local"
    purpose: str = "resident_app"
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    policy: CapabilityIssuerPolicy = CapabilityIssuerPolicy()
    surface: ResidentCapabilitySurface | None = None

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
            "surface": self.surface,
            "scopes": sorted(self.scopes),
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired(),
            "policy": self.policy.public_metadata(),
        }


@dataclass(frozen=True)
class CapabilityIssuer:
    """Local-only capability issuer boundary for resident app operations."""

    issuer: str = "local"
    default_ttl_seconds: int | None = 3600
    policy: CapabilityIssuerPolicy = CapabilityIssuerPolicy()
    surface: ResidentCapabilitySurface | None = None

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
        self.policy.require_non_persistent()
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
            policy=self.policy,
            surface=self.surface,
        )

    def public_metadata(self) -> dict[str, object]:
        """Return non-secret issuer metadata for diagnostics."""
        return {
            "issuer": self.issuer,
            "surface": self.surface,
            "default_ttl_seconds": self.default_ttl_seconds,
            "policy": self.policy.public_metadata(),
        }


def create_capability_issuer_for_surface(
    surface: ResidentCapabilitySurface,
    *,
    issuer: str = "local",
    default_ttl_seconds: int | None = 3600,
    policy: CapabilityIssuerPolicy | None = None,
) -> CapabilityIssuer:
    """Create a local issuer dedicated to one resident capability surface."""
    return CapabilityIssuer(
        issuer=f"{issuer}:{surface}",
        default_ttl_seconds=default_ttl_seconds,
        policy=policy or CapabilityIssuerPolicy(),
        surface=surface,
    )


def create_local_capability_token(
    scopes: ResidentCapabilityScopes,
    *,
    subject: str = "local_user",
    purpose: str = "resident_app",
    ttl_seconds: int | None = 3600,
    issuer: str = "local",
    issued_at: datetime | None = None,
    policy: CapabilityIssuerPolicy | None = None,
    surface: ResidentCapabilitySurface | None = None,
) -> CapabilityToken:
    """Create a local resident app capability token."""
    if surface is not None:
        capability_issuer = create_capability_issuer_for_surface(
            surface,
            issuer=issuer,
            default_ttl_seconds=ttl_seconds,
            policy=policy,
        )
    else:
        capability_issuer = CapabilityIssuer(
            issuer=issuer,
            default_ttl_seconds=ttl_seconds,
            policy=policy or CapabilityIssuerPolicy(),
        )
    return capability_issuer.issue(
        scopes,
        subject=subject,
        purpose=purpose,
        issued_at=issued_at,
    )


def create_surface_capability_tokens(
    *,
    issuer: str = "local",
    policy: CapabilityIssuerPolicy | None = None,
) -> dict[ResidentCapabilitySurface, CapabilityToken]:
    """Create separate local capability tokens for resident app surfaces."""
    issuer_policy = policy or CapabilityIssuerPolicy()
    return {
        "capture": create_local_capability_token(
            ["capture"],
            issuer=issuer,
            policy=issuer_policy,
            surface="capture",
        ),
        "ui": create_local_capability_token(
            ["ui"],
            issuer=issuer,
            policy=issuer_policy,
            surface="ui",
        ),
        "mcp": create_local_capability_token(
            ["mcp"],
            issuer=issuer,
            policy=issuer_policy,
            surface="mcp",
        ),
        "bridge": create_local_capability_token(
            ["bridge"],
            issuer=issuer,
            policy=issuer_policy,
            surface="bridge",
        ),
        "admin": create_local_capability_token(
            ["admin"],
            issuer=issuer,
            policy=issuer_policy,
            surface="admin",
        ),
    }
