"""Configuration for optional LLM-as-a-Judge (Level 2+)."""

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

_DEFAULT_LOCAL_BASE = "http://127.0.0.1:11434/v1"
_DEFAULT_MODEL = "llama3.2"


@dataclass(frozen=True)
class JudgeConfig:
    base_url: str
    api_key: str | None
    model: str
    timeout_sec: float = 60.0

    @property
    def is_local(self) -> bool:
        host = self.base_url.lower()
        return "127.0.0.1" in host or "localhost" in host


def load_judge_config(level: int) -> JudgeConfig | None:
    """Load judge settings from ~/.sayane/judge.yaml and environment."""
    if level < 2:
        return None

    home = Path.home() / ".sayane"
    file_data: dict = {}
    judge_path = home / "judge.yaml"
    if judge_path.is_file():
        with judge_path.open(encoding="utf-8") as f:
            raw = yaml.safe_load(f)
            if isinstance(raw, dict):
                file_data = raw

    base_url = os.environ.get("SAYANE_JUDGE_BASE_URL") or file_data.get("base_url")
    api_key = os.environ.get("SAYANE_JUDGE_API_KEY") or file_data.get("api_key")
    model = os.environ.get("SAYANE_JUDGE_MODEL") or file_data.get("model") or _DEFAULT_MODEL
    timeout = file_data.get("timeout_sec", 60.0)

    if level == 2 and not base_url:
        base_url = _DEFAULT_LOCAL_BASE
    if level == 3 and not base_url:
        return None
    if level == 3 and not api_key:
        return None

    return JudgeConfig(
        base_url=str(base_url).rstrip("/"),
        api_key=str(api_key) if api_key else None,
        model=str(model),
        timeout_sec=float(timeout),
    )
