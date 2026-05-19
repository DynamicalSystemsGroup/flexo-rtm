# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion O2: Layer C carry-through. Vendor-extension triples
(predicates outside the OSLC core namespaces) are stored verbatim in source
graphs and re-emitted unchanged."""

from __future__ import annotations

from pathlib import Path

from oracle.adapters.oslc import (
    canonical_triple_set,
    emit_oslc,
    extract_carry_through_triples,
    parse_oslc,
)
from rdflib import Graph

from tests.conftest import REPO_ROOT

VENDOR_DIR: Path = REPO_ROOT / "examples" / "oslc-fixtures" / "vendor"


def _layer_c_roundtrip(turtle: str) -> tuple[bytes, bytes, int, int]:
    ingest = Graph()
    ingest.parse(data=turtle, format="turtle")
    ds = parse_oslc(turtle, format="turtle")
    emitted = emit_oslc(ds, format="turtle")
    reparsed = Graph()
    reparsed.parse(data=emitted, format="turtle")
    before = extract_carry_through_triples(ingest)
    after = extract_carry_through_triples(reparsed)
    return (
        canonical_triple_set(before),
        canonical_triple_set(after),
        len(before),
        len(after),
    )


def test_doors_extensions_carry_through_unchanged() -> None:
    turtle = (VENDOR_DIR / "doors-next-requirement.ttl").read_text()
    before, after, n_before, n_after = _layer_c_roundtrip(turtle)
    assert n_before > 0  # the fixture has at least one vendor extension
    assert n_before == n_after
    assert before == after


def test_jama_extensions_carry_through_unchanged() -> None:
    turtle = (VENDOR_DIR / "jama-connect-requirement.ttl").read_text()
    before, after, n_before, n_after = _layer_c_roundtrip(turtle)
    assert n_before > 0
    assert n_before == n_after
    assert before == after


def test_polarion_extensions_carry_through_unchanged() -> None:
    turtle = (VENDOR_DIR / "polarion-requirement.ttl").read_text()
    before, after, n_before, n_after = _layer_c_roundtrip(turtle)
    assert n_before > 0
    assert n_before == n_after
    assert before == after
