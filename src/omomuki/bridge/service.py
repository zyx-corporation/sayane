"""Bridge business logic delegating to Omomuki core."""

from pathlib import Path

from omomuki.adapters.factory import get_adapter
from omomuki.bridge.config import BridgeConfig
from omomuki.bridge.models import (
    CompileRequest,
    ContextPacketResponse,
    ProfileSummary,
)
from omomuki.core.builder import build_prompt_ir
from omomuki.core.loader import load_profile


def list_profiles(config: BridgeConfig) -> list[ProfileSummary]:
    base = config.profiles_dir
    if not base.exists():
        return []
    summaries: list[ProfileSummary] = []
    for entry in sorted(base.iterdir()):
        if not entry.is_dir():
            continue
        profile_path = entry / "omomuki.profile.yaml"
        if not profile_path.exists():
            continue
        name: str | None = None
        try:
            profile = load_profile(profile_path)
            name = profile.identity.name
        except Exception:
            name = None
        summaries.append(
            ProfileSummary(id=entry.name, path=str(profile_path), name=name),
        )
    return summaries


def resolve_profile_path(config: BridgeConfig, profile_id: str) -> Path:
    path = config.profiles_dir / profile_id / "omomuki.profile.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_id}")
    return path


def compile_prompt(
    config: BridgeConfig,
    request: CompileRequest,
) -> ContextPacketResponse:
    profile_path = resolve_profile_path(config, request.profile_id)
    profile = load_profile(profile_path)
    ir = build_prompt_ir(profile, instruction=request.instruction)
    compiled = get_adapter(request.target).compile(ir)
    return ContextPacketResponse(
        target=compiled.target,
        format=compiled.format,
        payload=compiled.payload,
        profile_id=request.profile_id,
    )
