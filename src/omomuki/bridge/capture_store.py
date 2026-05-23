"""Persist capture payloads as candidate updates (not profile merge)."""

import json
from datetime import UTC, datetime
from uuid import uuid4

from omomuki.bridge.config import BridgeConfig
from omomuki.bridge.models import CaptureRequest, CaptureResponse


def save_capture(config: BridgeConfig, request: CaptureRequest) -> CaptureResponse:
    config.candidates_dir.mkdir(parents=True, exist_ok=True)
    capture_id = uuid4().hex
    record = {
        "id": capture_id,
        "status": "candidate",
        "content": request.content,
        "source": request.source,
        "source_url": request.source_url,
        "captured_at": datetime.now(UTC).isoformat(),
    }
    path = config.candidates_dir / f"{capture_id}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return CaptureResponse(id=capture_id, path=str(path))
