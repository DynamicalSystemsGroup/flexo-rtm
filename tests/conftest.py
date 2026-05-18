# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY_DIR = REPO_ROOT / "ontology"
EXAMPLES_DIR = REPO_ROOT / "examples"


@pytest.fixture()
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture()
def ontology_dir() -> Path:
    return ONTOLOGY_DIR


@pytest.fixture()
def assembled_ontology_path() -> Path:
    return ONTOLOGY_DIR / "rtm.ttl"
