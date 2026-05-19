# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion O1 (QM): Layer A roundtrip for OSLC-QM core constructs."""

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


def _layer_a_roundtrip(fixture: str) -> tuple[bytes, bytes]:
    turtle = (CANONICAL_DIR / fixture).read_text()
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


def test_qm_test_case_layer_a_roundtrip() -> None:
    before, after = _layer_a_roundtrip("qm-test-case.ttl")
    assert before == after


def test_qm_test_execution_and_result_layer_a_roundtrip() -> None:
    before, after = _layer_a_roundtrip("qm-test-execution-and-result.ttl")
    assert before == after
