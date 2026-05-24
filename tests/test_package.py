import sayane
from sayane import (
    adapters,
    bridge,
    cli,
    core,
    evaluators,
    mcp,
    storage,
    strategies,
)


def test_version() -> None:
    assert sayane.__version__ == "0.5.9"


def test_subpackages_importable() -> None:
    for module in (core, cli, bridge, adapters, strategies, evaluators, storage, mcp):
        assert module.__doc__ is not None
