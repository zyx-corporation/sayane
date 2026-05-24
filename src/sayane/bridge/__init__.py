"""Local Bridge — localhost API for Extension and local clients."""

from sayane.bridge.app import create_app
from sayane.bridge.config import BridgeConfig

__all__ = ["BridgeConfig", "create_app"]
