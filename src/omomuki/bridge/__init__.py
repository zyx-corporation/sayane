"""Local Bridge — localhost API for Extension and local clients."""

from omomuki.bridge.app import create_app
from omomuki.bridge.config import BridgeConfig

__all__ = ["BridgeConfig", "create_app"]
