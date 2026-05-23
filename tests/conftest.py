from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = REPO_ROOT / "schemas"
EXAMPLES_DIR = REPO_ROOT / "examples"


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def schemas_dir() -> Path:
    return SCHEMAS_DIR


@pytest.fixture
def examples_dir() -> Path:
    return EXAMPLES_DIR
