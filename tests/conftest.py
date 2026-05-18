# SPDX-License-Identifier: Apache-2.0
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY_DIR = REPO_ROOT / "ontology"
EXAMPLES_DIR = REPO_ROOT / "examples"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-skip @pytest.mark.network tests unless FLEXO_RTM_NETWORK_TESTS is set."""
    if os.environ.get("FLEXO_RTM_NETWORK_TESTS"):
        return
    skip_marker = pytest.mark.skip(reason="set FLEXO_RTM_NETWORK_TESTS=1 to enable network tests")
    for item in items:
        if "network" in item.keywords:
            item.add_marker(skip_marker)


@pytest.fixture()
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture()
def ontology_dir() -> Path:
    return ONTOLOGY_DIR


@pytest.fixture()
def assembled_ontology_path() -> Path:
    return ONTOLOGY_DIR / "rtm.ttl"
