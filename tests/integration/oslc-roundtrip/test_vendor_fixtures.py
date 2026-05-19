# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion O5: vendor sample fixtures roundtrip Layer A on core +
Layer C on extensions."""

from __future__ import annotations

from oracle.adapters.oslc import (
    canonical_triple_set,
    emit_oslc,
    extract_carry_through_triples,
    extract_core_triples,
    parse_oslc,
)
from rdflib import Graph

from tests.conftest import REPO_ROOT

VENDOR_DIR = REPO_ROOT / "examples" / "oslc-fixtures" / "vendor"


def test_every_vendor_fixture_roundtrips_core_and_extensions() -> None:
    fixtures = sorted(VENDOR_DIR.glob("*.ttl"))
    assert fixtures, "no vendor fixtures present"

    for fixture in fixtures:
        turtle = fixture.read_text()
        ingest = Graph()
        ingest.parse(data=turtle, format="turtle")
        ds = parse_oslc(turtle, format="turtle")
        emitted = emit_oslc(ds, format="turtle")
        reparsed = Graph()
        reparsed.parse(data=emitted, format="turtle")

        core_before = canonical_triple_set(extract_core_triples(ingest))
        core_after = canonical_triple_set(extract_core_triples(reparsed))
        assert core_before == core_after, f"core roundtrip failed for {fixture.name}"

        ext_before = extract_carry_through_triples(ingest)
        ext_after = extract_carry_through_triples(reparsed)
        assert len(ext_before) > 0, (
            f"vendor fixture {fixture.name} has no extension triples; check the fixture"
        )
        assert len(ext_before) == len(ext_after), (
            f"vendor extension count changed for {fixture.name}: "
            f"{len(ext_before)} → {len(ext_after)}"
        )
        assert canonical_triple_set(ext_before) == canonical_triple_set(ext_after), (
            f"vendor extension content changed for {fixture.name}"
        )
