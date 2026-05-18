# SPDX-License-Identifier: Apache-2.0
"""RDFC-1.0 + sha256 wrapper (Design Spec §4.7, X1; ADR-026 suite-derived)."""

from __future__ import annotations

from oracle.canonicalize import canonicalize_graph
from rdflib import Graph

TURTLE_A = """
@prefix ex: <https://rtm.example/> .
@prefix rtm: <https://rtm.example/ontology#> .
ex:r1 a rtm:Requirement ; rtm:label "r1" .
ex:a1 a rtm:Artifact ; rtm:addresses ex:r1 .
"""

# Semantically identical: reordered prefixes, reordered statements, different whitespace.
TURTLE_B = """
@prefix rtm: <https://rtm.example/ontology#> .
@prefix ex:  <https://rtm.example/> .

ex:a1
    a rtm:Artifact ;
    rtm:addresses ex:r1 .

ex:r1   a   rtm:Requirement ;   rtm:label "r1" .
"""


def _parse(turtle: str) -> Graph:
    g = Graph()
    g.parse(data=turtle, format="turtle")
    return g


def test_canonicalize_returns_three_fields() -> None:
    g = _parse(TURTLE_A)
    result = canonicalize_graph(g)
    assert result.canonical_bytes
    assert len(result.sha256_hex) == 64
    assert result.suite_id == "urn:rtm:suite/rdfc-1.0+sha256"


def test_canonicalize_semantically_equivalent_graphs_have_same_hash() -> None:
    a = canonicalize_graph(_parse(TURTLE_A))
    b = canonicalize_graph(_parse(TURTLE_B))
    assert a.sha256_hex == b.sha256_hex
    assert a.canonical_bytes == b.canonical_bytes


def test_canonicalize_differing_graphs_have_different_hash() -> None:
    a = canonicalize_graph(_parse(TURTLE_A))
    different = TURTLE_A + "\nex:r2 a <https://rtm.example/ontology#Requirement> .\n"
    b = canonicalize_graph(_parse(different))
    assert a.sha256_hex != b.sha256_hex
