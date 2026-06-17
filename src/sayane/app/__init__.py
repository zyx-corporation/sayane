"""Resident app service boundary for ADR 0007 Phase 4."""

from sayane.app.capabilities import (
    CapabilityIssuer,
    CapabilityIssuerPolicy,
    CapabilityToken,
    create_capability_issuer_for_surface,
    create_local_capability_token,
    create_surface_capability_tokens,
)
from sayane.app.daemon_identity import (
    ResidentDaemonIdentity,
    validate_runtime_local_path,
)
from sayane.app.daemon_lifecycle import (
    ResidentDaemonLifecycle,
    ResidentDaemonMode,
    ResidentDaemonState,
    is_local_bind_host,
    validate_local_bind_host,
)
from sayane.app.daemon_runtime_layout import (
    ResidentDaemonRuntimeLayout,
    validate_runtime_child_path,
)
from sayane.app.runtime import (
    ResidentRepositoryBackend,
    ResidentRepositorySelection,
    ResidentRuntime,
    build_resident_runtime,
    select_resident_repositories,
)
from sayane.app.service import ResidentAppService
from sayane.app.ui import build_mcp_preview, build_review_queue

__all__ = [
    "CapabilityIssuer",
    "CapabilityIssuerPolicy",
    "CapabilityToken",
    "ResidentAppService",
    "ResidentDaemonIdentity",
    "ResidentDaemonLifecycle",
    "ResidentDaemonMode",
    "ResidentDaemonRuntimeLayout",
    "ResidentDaemonState",
    "ResidentRepositoryBackend",
    "ResidentRepositorySelection",
    "ResidentRuntime",
    "build_mcp_preview",
    "build_resident_runtime",
    "build_review_queue",
    "create_capability_issuer_for_surface",
    "create_local_capability_token",
    "create_surface_capability_tokens",
    "is_local_bind_host",
    "select_resident_repositories",
    "validate_local_bind_host",
    "validate_runtime_child_path",
    "validate_runtime_local_path",
]
