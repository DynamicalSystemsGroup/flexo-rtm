# SPDX-License-Identifier: Apache-2.0
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY_DIR = REPO_ROOT / "ontology"
EXAMPLES_DIR = REPO_ROOT / "examples"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-skip integration tests that need external services.

    - ``@pytest.mark.network`` — skipped unless ``FLEXO_RTM_NETWORK_TESTS=1``.
    - ``@pytest.mark.live`` — skipped unless ``FLEXO_TOKEN`` is set (Flexo REST
      Binding §8 / acceptance criterion F7).
    """
    skip_network = (
        None
        if os.environ.get("FLEXO_RTM_NETWORK_TESTS")
        else pytest.mark.skip(reason="set FLEXO_RTM_NETWORK_TESTS=1 to enable network tests")
    )
    skip_live = (
        None
        if os.environ.get("FLEXO_TOKEN")
        else pytest.mark.skip(reason="FLEXO_TOKEN not set; live Flexo tests skipped (F7)")
    )
    for item in items:
        if skip_network is not None and "network" in item.keywords:
            item.add_marker(skip_network)
        if skip_live is not None and "live" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture()
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture()
def ontology_dir() -> Path:
    return ONTOLOGY_DIR


@pytest.fixture()
def assembled_ontology_path() -> Path:
    return ONTOLOGY_DIR / "rtm.ttl"
