"""Import bundle route registration."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Callable
from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, HTTPException

from sayane.bridge.config import BridgeConfig

AuthDependency = Callable[..., None]


def register_import_routes(
    app: FastAPI,
    cfg: BridgeConfig,
    require_bearer: AuthDependency,
) -> None:
    """Register import endpoints."""
    router = APIRouter()

    @router.post("/import")
    def post_import(
        body: dict,
        _: Annotated[None, Depends(require_bearer)] = None,
    ) -> dict:
        from sayane.bridge.service import resolve_profile_path
        from sayane.core.import_bundle import ImportMetadata, create_import_candidates, parse_bundle
        from sayane.core.loader import load_profile
        from sayane.storage.candidates import save_candidate

        bundle_path = body.get("path")
        if not bundle_path or not Path(bundle_path).is_file():
            raise HTTPException(status_code=400, detail="Invalid or missing bundle path")

        profile_id = body.get("profile_id", "default")
        profile = load_profile(resolve_profile_path(cfg, profile_id))
        parsed = parse_bundle(Path(bundle_path))
        if parsed is None:
            raise HTTPException(status_code=400, detail="Could not parse bundle")

        import_id = uuid4().hex
        import_meta = ImportMetadata(
            import_id=import_id,
            source_path=bundle_path,
            source_format=body.get("source_format", "yaml"),
            source_target=body.get("source_target"),
            source_scopes=body.get("source_scopes", []),
        )
        candidates = create_import_candidates(parsed, profile, import_meta=import_meta, target_profile_id=profile_id)
        saved_ids = []
        for c in candidates:
            save_candidate(cfg, c)
            saved_ids.append(c.id)

        return {"import_id": import_id, "candidate_count": len(saved_ids), "candidate_ids": saved_ids}

    app.include_router(router)
