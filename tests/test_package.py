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
    assert sayane.__version__ == "1.0.4"


def test_subpackages_importable() -> None:
    modules = (
        core,
        cli,
        bridge,
        adapters,
        strategies,
        evaluators,
        storage,
        mcp,
    )
    for module in modules:
        assert module.__doc__ is not None
