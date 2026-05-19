# SPDX-License-Identifier: Apache-2.0
"""X1 + X3 in the property setting: arbitrary valid graph → record transcript →
replay → byte-identical hashes.
"""

from __future__ import annotations

from uuid import UUID

from hypothesis import given
from hypothesis import strategies as st
from oracle.analysis.emit.transcript import (
    TranscriptRecorder,
    replay_transcript,
    transcript_canonical_bytes,
)
from rdflib import RDF, Graph, Namespace, URIRef

RTM = Namespace("https://flexo-rtm.dev/ontology#")
EX = Namespace("https://rtm.example/")

QUERY = "PREFIX rtm: <https://flexo-rtm.dev/ontology#> SELECT ?r WHERE { ?r a rtm:Requirement }"


@st.composite
def small_rtm_graph(draw: st.DrawFn) -> Graph:
    n_reqs = draw(st.integers(min_value=0, max_value=6))
    n_arts = draw(st.integers(min_value=0, max_value=6))
    g = Graph()
    for i in range(n_reqs):
        g.add((URIRef(f"{EX}r{i}"), RDF.type, RTM.Requirement))
    for j in range(n_arts):
        g.add((URIRef(f"{EX}a{j}"), RDF.type, RTM.Artifact))
    if n_reqs > 0 and n_arts > 0:
        edges = draw(
            st.lists(
                st.tuples(
                    st.integers(min_value=0, max_value=n_arts - 1),
                    st.integers(min_value=0, max_value=n_reqs - 1),
                ),
                max_size=12,
                unique=True,
            )
        )
        for a, r in edges:
            g.add((URIRef(f"{EX}a{a}"), RTM.addresses, URIRef(f"{EX}r{r}")))
    return g


FIXED_RUN_ID = UUID("00000000-0000-4000-8000-0000000abcde")


@given(g=small_rtm_graph())
def test_record_then_replay_always_passes(g: Graph) -> None:
    recorder = TranscriptRecorder(run_id=FIXED_RUN_ID, input_graph=g)
    recorder.record_sparql(query_text=QUERY)
    recorder.record_canonicalize()
    result = replay_transcript(recorder.transcript(), input_graph=g)
    assert result.passed, f"replay failed at seq {result.diverged_at_seq}: {result.diverged_field}"


@given(g=small_rtm_graph())
def test_transcript_canonical_bytes_are_byte_identical_across_runs(g: Graph) -> None:
    """X1 in the property setting: same input → byte-identical transcript bytes."""

    def _build() -> bytes:
        r = TranscriptRecorder(run_id=FIXED_RUN_ID, input_graph=g)
        r.record_sparql(query_text=QUERY)
        r.record_canonicalize()
        return transcript_canonical_bytes(r.transcript())

    assert _build() == _build()
