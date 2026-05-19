# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion O7: vendor-extension registry schema. Adding a new
vendor requires only a YAML entry — no code changes."""

from __future__ import annotations

from pathlib import Path

import yaml

from tests.conftest import REPO_ROOT

REGISTRY_PATH: Path = REPO_ROOT / "examples" / "oslc-fixtures" / "vendor-registry.yaml"
REQUIRED_FIELDS = {"name", "namespace_prefix", "namespace_uri", "handling"}


def test_registry_loads_and_each_entry_carries_required_fields() -> None:
    data = yaml.safe_load(REGISTRY_PATH.read_text())
    assert "vendors" in data
    assert len(data["vendors"]) >= 3
    for entry in data["vendors"]:
        missing = REQUIRED_FIELDS - set(entry.keys())
        assert not missing, f"vendor {entry.get('name')!r} missing fields: {missing}"
        assert entry["handling"] == "carry-through"


def test_registry_includes_doors_jama_polarion() -> None:
    data = yaml.safe_load(REGISTRY_PATH.read_text())
    names = {entry["name"] for entry in data["vendors"]}
    assert {"IBM-Doors-Next", "Jama-Connect", "Polarion"}.issubset(names)


def test_each_registered_vendor_has_a_fixture() -> None:
    data = yaml.safe_load(REGISTRY_PATH.read_text())
    vendor_dir = REPO_ROOT / "examples" / "oslc-fixtures" / "vendor"
    fixtures = list(vendor_dir.glob("*.ttl"))
    assert fixtures, "no vendor fixtures present"

    fixture_contents = " ".join(p.read_text() for p in fixtures)
    for entry in data["vendors"]:
        namespace = entry["namespace_uri"]
        assert namespace in fixture_contents, (
            f"vendor {entry['name']!r} (namespace {namespace}) has no fixture"
        )
