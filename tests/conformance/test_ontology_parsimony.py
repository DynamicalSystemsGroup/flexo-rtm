# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion X6: assembled rtm.ttl ≤ 2000 triples; manifest is the audit trail."""

from __future__ import annotations

from pathlib import Path

import yaml
from rdflib import Graph

from tests.conftest import ONTOLOGY_DIR

ASSEMBLED_RTM_TTL: Path = ONTOLOGY_DIR / "rtm.ttl"
MANIFEST_PATH: Path = ONTOLOGY_DIR / "parsimony" / "manifest.yaml"

TRIPLE_BUDGET = 2000


def test_assembled_ontology_exists() -> None:
    assert ASSEMBLED_RTM_TTL.exists(), (
        "ontology/rtm.ttl is missing — run `make parsimony` (or `uv run python "
        "ontology/parsimony/build.py`) before tests"
    )


def test_assembled_ontology_under_budget() -> None:
    g = Graph()
    g.parse(ASSEMBLED_RTM_TTL, format="turtle")
    count = len(g)
    assert count <= TRIPLE_BUDGET, (
        f"rtm.ttl has {count} triples (budget {TRIPLE_BUDGET}). "
        "See Parsimony Manifest §4 for the per-vocabulary allocation."
    )


def test_manifest_declares_budget() -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text())
    assert manifest["target_triple_budget"] == TRIPLE_BUDGET
    assert isinstance(manifest["vocabularies"], list)
    assert len(manifest["vocabularies"]) >= 1


def test_manifest_extracts_present_when_declared() -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text())
    for vocab in manifest["vocabularies"]:
        terms = (
            vocab.get("extracted_classes", [])
            + vocab.get("extracted_properties", [])
            + vocab.get("extracted_individuals", [])
        )
        target = vocab.get("target_extract_file")
        if terms:
            assert target, f"vocabulary {vocab['name']!r} has terms but no target_extract_file"
            extract_path = ONTOLOGY_DIR / target if not Path(target).is_absolute() else Path(target)
            if not extract_path.is_absolute():
                extract_path = (ONTOLOGY_DIR.parent / target).resolve()
            assert extract_path.exists(), (
                f"manifest declares terms for {vocab['name']!r} but extract file "
                f"{extract_path} is missing"
            )
