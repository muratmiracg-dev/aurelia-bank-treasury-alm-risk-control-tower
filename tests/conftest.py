from pathlib import Path

import pytest

from aurelia_alm.config import load_project_config
from aurelia_alm.generator import build_demo_data


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def config(project_root: Path):
    return load_project_config(project_root)


@pytest.fixture(scope="session")
def demo(config):
    return build_demo_data(config)
