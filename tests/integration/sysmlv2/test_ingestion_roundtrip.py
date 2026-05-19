# SPDX-License-Identifier: Apache-2.0
"""Source-preserving SysMLv2 ingestion — SysMLv2 Ingestion Contract §6.

The source graph for a SysMLv2 file is byte-identical to the input RDF (after
RDFC-1.0 canonicalization). Internal augmentations do NOT contaminate the
source. This makes write-back (v0.2) clean.
"""

from __future__ import annotations

from oracle.adapters.sysmlv2 import (
    SOURCE_GRAPH_PREFIX,
    canonical_triple_set,
    emit_sysmlv2,
    parse_sysmlv2,
    source_graph_iri_for_path,
)
from rdflib import Graph

from tests.conftest import REPO_ROOT

CANONICAL_DIR = REPO_ROOT / "examples" / "sysmlv2" / "canonical"


def _ingest(fixture: str) -> tuple[bytes, bytes]:
    turtle = (CANONICAL_DIR / fixture).read_text()
    ingest = Graph()
    ingest.parse(data=turtle, format="turtle")
    ds = parse_sysmlv2(turtle, path=fixture, format="turtle")
    emitted = emit_sysmlv2(ds, format="turtle")
    reparsed = Graph()
    reparsed.parse(data=emitted, format="turtle")
    return canonical_triple_set(ingest), canonical_triple_set(reparsed)


def test_minimal_requirement_roundtrip() -> None:
    before, after = _ingest("minimal-requirement.ttl")
    assert before == after


def test_verification_case_roundtrip() -> None:
    before, after = _ingest("verification-case.ttl")
    assert before == after


def test_source_graph_iri_is_deterministic_per_path() -> None:
    assert source_graph_iri_for_path("a.ttl") == source_graph_iri_for_path("a.ttl")
    assert source_graph_iri_for_path("a.ttl") != source_graph_iri_for_path("b.ttl")
    assert str(source_graph_iri_for_path("a.ttl")).startswith(SOURCE_GRAPH_PREFIX)


def test_ingestion_lands_in_a_single_named_graph_per_file() -> None:
    turtle = (CANONICAL_DIR / "minimal-requirement.ttl").read_text()
    ds = parse_sysmlv2(turtle, path="minimal-requirement.ttl", format="turtle")
    source_contexts = [
        ctx for ctx in ds.contexts() if str(ctx.identifier).startswith(SOURCE_GRAPH_PREFIX)
    ]
    assert len(source_contexts) == 1
    assert len(source_contexts[0]) > 0
