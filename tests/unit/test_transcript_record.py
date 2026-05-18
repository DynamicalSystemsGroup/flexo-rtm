# SPDX-License-Identifier: Apache-2.0
"""Transcript record path — Transcript Replay Semantics §1, §2, §5 (Merkle chain)."""

from __future__ import annotations

from uuid import UUID

from oracle.analysis.emit.transcript import TranscriptRecorder
from oracle.canonicalize import SUITE_RDFC_1_0_SHA256
from rdflib import Graph

RUN_ID = UUID("00000000-0000-4000-8000-000000000001")


def _input_graph() -> Graph:
    g = Graph()
    g.parse(
        data="""
        @prefix rtm: <https://flexo-rtm.dev/ontology#> .
        @prefix ex:  <https://rtm.example/> .
        ex:r1 a rtm:Requirement .
        ex:a1 a rtm:Artifact ; rtm:satisfies ex:r1 .
        """,
        format="turtle",
    )
    return g


def test_record_single_sparql_step_populates_required_fields() -> None:
    recorder = TranscriptRecorder(run_id=RUN_ID, input_graph=_input_graph())
    query = "PREFIX rtm: <https://flexo-rtm.dev/ontology#> SELECT ?r WHERE { ?r a rtm:Requirement }"
    step = recorder.record_sparql(query_text=query)

    assert step.seq == 1
    assert step.step_kind == "sparql"
    assert step.query_text == query
    assert step.inputs_hash == recorder.genesis_inputs_hash
    assert len(step.result_hash) == 64
    assert step.was_informed_by is None
    assert step.cryptosuite == SUITE_RDFC_1_0_SHA256


def test_record_chain_links_via_was_informed_by() -> None:
    recorder = TranscriptRecorder(run_id=RUN_ID, input_graph=_input_graph())
    step1 = recorder.record_sparql(
        query_text="SELECT ?r WHERE { ?r ?p ?o }",
    )
    step2 = recorder.record_canonicalize()
    transcript = recorder.transcript()

    assert step2.seq == 2
    assert step2.was_informed_by == step1.prov_activity
    assert step2.inputs_hash == step1.result_hash
    assert len(transcript.steps) == 2
    assert transcript.run_id == RUN_ID
    assert transcript.cryptosuite == SUITE_RDFC_1_0_SHA256
