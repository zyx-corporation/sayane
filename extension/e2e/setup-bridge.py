#!/usr/bin/env python3
"""Prepare ~/.sayane profile + bridge token for Extension Playwright E2E."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from sayane.bridge.auth import load_or_create_token
from sayane.bridge.config import BridgeConfig

SAYANE_ROOT = Path(__file__).resolve().parents[2]
MINIMAL_PROFILE = SAYANE_ROOT / "examples" / "profiles" / "minimal.yaml"


def main() -> None:
    home = Path(os.environ["HOME"])
    sayane_home = home / ".sayane"
    profile_dir = sayane_home / "profiles" / "default"
    profile_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(MINIMAL_PROFILE, profile_dir / "sayane.profile.yaml")

    config = BridgeConfig(home=sayane_home)
    token, _ = load_or_create_token(config)

    env_file = Path(os.environ["SAYANE_E2E_ENV_FILE"])
    env_file.write_text(
        json.dumps(
            {
                "bridgeUrl": f"http://{config.host}:{config.port}",
                "token": token,
                "home": str(home),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
