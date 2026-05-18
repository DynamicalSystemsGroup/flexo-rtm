# SPDX-License-Identifier: Apache-2.0
"""Acceptance criterion X1 (partial): canonicalization is byte-identical across runs.

Slice 1 proves this for a toy graph in-process; slice 2 lifts it to full audit transcripts.
"""

from __future__ import annotations

from oracle.canonicalize import canonicalize_graph
from rdflib import Graph

TURTLE = """
@prefix ex: <https://rtm.example/> .
@prefix rtm: <https://rtm.example/ontology#> .
ex:r1 a rtm:Requirement .
ex:r2 a rtm:Requirement .
ex:r3 a rtm:Requirement .
ex:a1 a rtm:Artifact ; rtm:addresses ex:r1 .
ex:a2 a rtm:Artifact ; rtm:addresses ex:r2 .
"""


def _parse() -> Graph:
    g = Graph()
    g.parse(data=TURTLE, format="turtle")
    return g


def test_canonicalize_is_repeatable() -> None:
    first = canonicalize_graph(_parse())
    second = canonicalize_graph(_parse())
    assert first.canonical_bytes == second.canonical_bytes
    assert first.sha256_hex == second.sha256_hex


def test_canonicalize_is_fixed_point_under_reparse() -> None:
    first = canonicalize_graph(_parse())
    reparsed = Graph()
    reparsed.parse(data=first.canonical_bytes.decode("utf-8"), format="nt")
    second = canonicalize_graph(reparsed)
    assert first.canonical_bytes == second.canonical_bytes
    assert first.sha256_hex == second.sha256_hex
