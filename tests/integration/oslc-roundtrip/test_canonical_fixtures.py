# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion O4: canonical fixtures in examples/oslc-fixtures/canonical/
roundtrip losslessly (Layer A)."""

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


def test_every_canonical_fixture_roundtrips_layer_a() -> None:
    fixtures = sorted(CANONICAL_DIR.glob("*.ttl"))
    assert fixtures, "no canonical fixtures present"

    for fixture in fixtures:
        turtle = fixture.read_text()
        ingest = Graph()
        ingest.parse(data=turtle, format="turtle")
        ds = parse_oslc(turtle, format="turtle")
        emitted = emit_oslc(ds, format="turtle")
        reparsed = Graph()
        reparsed.parse(data=emitted, format="turtle")
        before = canonical_triple_set(extract_core_triples(ingest))
        after = canonical_triple_set(extract_core_triples(reparsed))
        assert before == after, f"layer A roundtrip failed for {fixture.name}"
