# SPDX-License-Identifier: Apache-2.0
"""SysMLv2 write-back roundtrip — pulled into v0.1 scope to prove the read step.

A same-format roundtrip (parse → emit → parse → canonical-form equality) is the
only way to be confident the parse path didn't lose or normalise anything. Test
both single-file and multi-file ingestion paths, then verify the emitted RDF
still passes the sysmlv2-anchored profile (so re-ingest stays clean).
"""

from __future__ import annotations

from pathlib import Path

import pyshacl
from oracle.adapters.sysmlv2 import (
    canonical_triple_set,
    emit_sysmlv2,
    list_source_files,
    parse_sysmlv2,
    source_graph_iri_for_path,
)
from rdflib import Graph

from tests.conftest import ONTOLOGY_DIR, REPO_ROOT

CANONICAL_DIR = REPO_ROOT / "examples" / "sysmlv2" / "canonical"
SYSMLV2_PROFILE: Path = ONTOLOGY_DIR / "profiles" / "sysmlv2-anchored.shacl.ttl"
ASSEMBLED: Path = ONTOLOGY_DIR / "rtm.ttl"


def _canon(turtle: str) -> bytes:
    g = Graph()
    g.parse(data=turtle, format="turtle")
    return canonical_triple_set(g)


def _profile_passes(turtle: str) -> tuple[bool, str]:
    data = Graph()
    data.parse(data=turtle, format="turtle")
    shapes = Graph()
    shapes.parse(SYSMLV2_PROFILE, format="turtle")
    ont = Graph()
    ont.parse(ASSEMBLED, format="turtle")
    conforms, _, text = pyshacl.validate(
        data_graph=data, shacl_graph=shapes, ont_graph=ont, inference="none", advanced=False
    )
    return conforms, text


def test_single_file_emit_by_path_matches_emit_by_source_graph() -> None:
    turtle = (CANONICAL_DIR / "minimal-requirement.ttl").read_text()
    ds = parse_sysmlv2(turtle, path="minimal-requirement.ttl", format="turtle")
    by_path = emit_sysmlv2(ds, path="minimal-requirement.ttl", format="turtle")
    by_iri = emit_sysmlv2(
        ds, source_graph=source_graph_iri_for_path("minimal-requirement.ttl"), format="turtle"
    )
    assert _canon(by_path) == _canon(by_iri)


def test_multi_file_ingest_preserves_per_file_separation() -> None:
    a_turtle = (CANONICAL_DIR / "minimal-requirement.ttl").read_text()
    b_turtle = (CANONICAL_DIR / "verification-case.ttl").read_text()

    ds = parse_sysmlv2(a_turtle, path="a.ttl", format="turtle")
    parse_sysmlv2(b_turtle, path="b.ttl", format="turtle", into=ds)

    iris = list_source_files(ds)
    assert len(iris) == 2

    a_emitted = emit_sysmlv2(ds, path="a.ttl", format="turtle")
    b_emitted = emit_sysmlv2(ds, path="b.ttl", format="turtle")

    assert _canon(a_emitted) == _canon(a_turtle)
    assert _canon(b_emitted) == _canon(b_turtle)


def test_multi_file_default_emit_unions_every_source_graph() -> None:
    a_turtle = (CANONICAL_DIR / "minimal-requirement.ttl").read_text()
    b_turtle = (CANONICAL_DIR / "verification-case.ttl").read_text()

    ds = parse_sysmlv2(a_turtle, path="a.ttl", format="turtle")
    parse_sysmlv2(b_turtle, path="b.ttl", format="turtle", into=ds)
    union_emitted = emit_sysmlv2(ds, format="turtle")

    union_input = Graph()
    union_input.parse(data=a_turtle, format="turtle")
    union_input.parse(data=b_turtle, format="turtle")

    assert _canon(union_emitted) == canonical_triple_set(union_input)


def test_emitted_rdf_still_passes_sysmlv2_anchored_profile() -> None:
    """If the emitted RDF dropped elementId / qualifiedName / owner, re-ingest
    would fail the SHACL profile. This is the strongest 'read didn't lose
    anything' check we have without round-tripping through openCAESAR."""
    turtle = (CANONICAL_DIR / "minimal-requirement.ttl").read_text()
    ds = parse_sysmlv2(turtle, path="minimal-requirement.ttl", format="turtle")
    emitted = emit_sysmlv2(ds, path="minimal-requirement.ttl", format="turtle")
    conforms, report = _profile_passes(emitted)
    assert conforms, report
