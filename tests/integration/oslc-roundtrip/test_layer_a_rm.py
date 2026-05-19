# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion O1 (RM): Layer A roundtrip — RDFC-1.0 triple-set
equivalence over OSLC-RM core constructs after parse→emit→parse."""

from __future__ import annotations

from oracle.adapters.oslc import (
    canonical_triple_set,
    emit_oslc,
    extract_core_triples,
    parse_oslc,
)
from rdflib import Graph

from tests.conftest import REPO_ROOT

CANONICAL_DIR = REPO_ROOT / "examples" / "oslc-fixtures" / "canonical"


def _read(fixture: str) -> str:
    return (CANONICAL_DIR / fixture).read_text()


def _layer_a_roundtrip(turtle: str) -> tuple[bytes, bytes]:
    ingest = Graph()
    ingest.parse(data=turtle, format="turtle")
    ds = parse_oslc(turtle, format="turtle")
    emitted = emit_oslc(ds, format="turtle")
    reparsed = Graph()
    reparsed.parse(data=emitted, format="turtle")
    return (
        canonical_triple_set(extract_core_triples(ingest)),
        canonical_triple_set(extract_core_triples(reparsed)),
    )


def test_rm_requirement_layer_a_roundtrip() -> None:
    before, after = _layer_a_roundtrip(_read("rm-requirement.ttl"))
    assert before == after


def test_rm_requirement_collection_layer_a_roundtrip() -> None:
    before, after = _layer_a_roundtrip(_read("rm-requirement-collection.ttl"))
    assert before == after
