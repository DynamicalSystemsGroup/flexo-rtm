# SPDX-License-Identifier: Apache-2.0
"""ADCS regression: flexo-rtm v0.1 produces the same §4.1 structural verdict
the prototype produces against its own data.

Per ADCS Prototype Lessons §6: certification of this corpus is a regression test
— drift here is an ontology bug. The frozen fixture at examples/adcs-corpus/rtm.ttl
is the output of scripts/translate_adcs_corpus.py against the prototype's TTLs
(verbatim source kept in examples/adcs-corpus/source/ for provenance).

Slice 3 scope: addresses coverage only (§4.1 + X7 partial). Attestation profiles
(satisfaction / adequacy / sufficiency) land with slice 9; the deliberately-
unattested REQ-001 case the wiki names becomes a T3 gap when attested-satisfies
is active, not a §4.1 fail.
"""

from __future__ import annotations

from pathlib import Path

from oracle.analysis.coverage import compute_coverage
from rdflib import Graph

CORPUS_TTL = (
    Path(__file__).resolve().parent.parent.parent.parent / "examples" / "adcs-corpus" / "rtm.ttl"
)


def _load_corpus() -> Graph:
    g = Graph()
    g.parse(CORPUS_TTL, format="turtle")
    return g


def test_corpus_loads_with_expected_population() -> None:
    g = _load_corpus()
    from rdflib import RDF, URIRef

    RTM = URIRef("https://flexo-rtm.dev/ontology#")
    reqs = list(g.subjects(RDF.type, URIRef("https://flexo-rtm.dev/ontology#Requirement")))
    arts = list(g.subjects(RDF.type, URIRef("https://flexo-rtm.dev/ontology#Artifact")))
    edges = list(g.triples((None, URIRef("https://flexo-rtm.dev/ontology#addresses"), None)))
    assert len(reqs) == 4, f"expected 4 ADCS-team requirements, got {len(reqs)}"
    assert len(arts) == 7, f"expected 7 evidence artifacts, got {len(arts)}"
    assert len(edges) == 7, f"expected 7 addresses edges, got {len(edges)}"
    assert RTM  # silence unused-import lint


def test_forward_addresses_coverage_is_100_percent() -> None:
    stats = compute_coverage(_load_corpus())
    assert stats.forward_percent == 100.0, (
        "Each of the 4 ADCS-team requirements has at least one addressing artifact"
    )


def test_backward_addresses_coverage_is_100_percent() -> None:
    stats = compute_coverage(_load_corpus())
    assert stats.backward_percent == 100.0, (
        "Each of the 7 evidence artifacts addresses at least one requirement"
    )


def test_every_adcs_requirement_has_at_least_one_addressing_artifact() -> None:
    from rdflib import RDF, URIRef

    g = _load_corpus()
    addresses = URIRef("https://flexo-rtm.dev/ontology#addresses")
    requirement = URIRef("https://flexo-rtm.dev/ontology#Requirement")
    for req in g.subjects(RDF.type, requirement):
        incoming = list(g.subjects(predicate=addresses, object=req))
        assert incoming, f"requirement {req} has no addressing evidence"
