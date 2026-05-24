"""Persist capture payloads as candidate updates (not profile merge)."""

from sayane.bridge.config import BridgeConfig
from sayane.bridge.models import CaptureRequest, CaptureResponse
from sayane.storage.candidates import create_from_capture, save_candidate


def save_capture(config: BridgeConfig, request: CaptureRequest) -> CaptureResponse:
    candidate = create_from_capture(
        config,
        content=request.content,
        source_type=request.source or "capture",
        source_url=request.source_url,
    )
    path = save_candidate(config, candidate)
    return CaptureResponse(id=candidate.id, path=str(path))
