# SPDX-License-Identifier: Apache-2.0
"""Hypothesis property tests for the coverage helpers — addresses coverage is
a pure function of the graph; percentages are in [0, 100]; counts are consistent.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st
from oracle.analysis.coverage import compute_coverage
from rdflib import RDF, Graph, Namespace, URIRef

RTM = Namespace("https://flexo-rtm.dev/ontology#")
EX = Namespace("https://rtm.example/")


@st.composite
def rtm_graph(draw: st.DrawFn) -> Graph:
    n_reqs = draw(st.integers(min_value=0, max_value=10))
    n_arts = draw(st.integers(min_value=0, max_value=10))
    edges = draw(
        st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=max(0, n_arts - 1)),
                st.integers(min_value=0, max_value=max(0, n_reqs - 1)),
            ),
            max_size=20,
            unique=True,
        )
    )

    g = Graph()
    for i in range(n_reqs):
        g.add((URIRef(f"{EX}r{i}"), RDF.type, RTM.Requirement))
    for j in range(n_arts):
        g.add((URIRef(f"{EX}a{j}"), RDF.type, RTM.Artifact))
    if n_reqs > 0 and n_arts > 0:
        for a, r in edges:
            g.add((URIRef(f"{EX}a{a}"), RTM.addresses, URIRef(f"{EX}r{r}")))
    return g


@given(g=rtm_graph())
def test_coverage_is_a_pure_function_of_the_graph(g: Graph) -> None:
    a = compute_coverage(g)
    b = compute_coverage(g)
    assert a == b


@given(g=rtm_graph())
def test_coverage_percentages_in_bounds(g: Graph) -> None:
    stats = compute_coverage(g)
    assert 0.0 <= stats.forward_percent <= 100.0
    assert 0.0 <= stats.backward_percent <= 100.0


@given(g=rtm_graph())
def test_empty_populations_report_vacuous_100(g: Graph) -> None:
    n_reqs = len(list(g.subjects(RDF.type, RTM.Requirement)))
    n_arts = len(list(g.subjects(RDF.type, RTM.Artifact)))
    stats = compute_coverage(g)
    if n_reqs == 0:
        assert stats.forward_percent == 100.0
    if n_arts == 0:
        assert stats.backward_percent == 100.0


@given(g=rtm_graph())
def test_adding_unaddressed_artifact_cannot_increase_backward_coverage(g: Graph) -> None:
    before = compute_coverage(g).backward_percent
    augmented = Graph()
    for triple in g:
        augmented.add(triple)
    augmented.add((URIRef(f"{EX}unaddressed-{id(g)}"), RDF.type, RTM.Artifact))
    after = compute_coverage(augmented).backward_percent
    assert after <= before
