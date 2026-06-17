from importlib import metadata

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


def test_version_matches_package_metadata() -> None:
    assert sayane.__version__ == metadata.version("sayane")


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
